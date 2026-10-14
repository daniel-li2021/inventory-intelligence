"""Fresh bounded restricted-runner replay; frozen hand controls, no policy efficacy claim."""
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
import argparse
import hashlib
import json
import os
import resource
import subprocess
import time

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from inventory_intelligence.insights import discover
from inventory_intelligence.planning_runs import exact_json
from inventory_intelligence.product import _report, archive_digest, load_catalog
from inventory_intelligence.synthetic_replay import admit, replay, publish, validate_sources

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / 'docs/examples/generalization-protocol-v1.json'


def audit(catalog, sources, expected):
    checked = []
    for source, binding, golden in zip(sources, catalog['cutoffs'], expected):
        finding_set = sorted((f['rule_id'], f['sku_id'], f['warehouse_id']) for f in discover(catalog, source['cutoff'])['findings'])
        wanted = sorted((g['rule'], source['dimensions']['skus'][g['sku']]['sku_id'], source['dimensions']['warehouses'][g['site']]['warehouse_id']) for g in golden['rule_keys'])
        if finding_set != wanted:
            raise AssertionError(dict(cutoff=source['cutoff'], expected=wanted, actual=finding_set))
        discovery = discover(catalog, source['cutoff'])
        if len(discovery['unknown']) != golden['unknown']:
            raise AssertionError(dict(cutoff=source['cutoff'], expected_unknown=golden['unknown'], actual_unknown=discovery['unknown']))
        for key, order, balances in zip(binding['keys'], golden['orders'], golden['balances']):
            report = _report(catalog, key['plan_run_id']); result = report['result']
            if result['proposed_order_qty'] != order:
                raise AssertionError(dict(key=key['sku_id'], expected=order, actual=result['proposed_order_qty']))
            actual = [Fraction(day['balance_without_order']) for day in result['projection']] if result['projection'] is not None else None
            wanted_balances = [Fraction(v) for v in balances] if balances is not None else None
            if actual != wanted_balances:
                raise AssertionError(dict(key=key['sku_id'], expected=balances, actual=str(actual)))
            checked.append(dict(cutoff=source['cutoff'], sku_id=key['sku_id'], warehouse_id=key['warehouse_id'], status=report['status'],
                                order=order, balances=exact_json(actual), reasons=result['reasons']))
    return checked


def semantic(catalog, cutoff):
    binding = next(b for b in catalog['cutoffs'] if b['cutoff'] == cutoff)
    return [dict(status=_report(catalog,k['plan_run_id'])['status'],
                 proposal=_report(catalog,k['plan_run_id'])['result']['proposed_order_qty'],
                 projection=_report(catalog,k['plan_run_id'])['result']['projection'],
                 supply=_report(catalog,k['plan_run_id'])['result']['supply'],
                 training=_report(catalog,k['plan_run_id'])['result']['training']) for k in binding['keys']]


def run(output):
    started = time.monotonic()
    protocol = json.loads(PROTOCOL.read_text())
    protocol_hash = hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
    for name, expected in protocol['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen source input changed')
    if output.exists():
        raise ValueError('Refuse to overwrite evidence directory')
    owner_options = conninfo_to_dict(os.environ['TEST_DATABASE_URL'])
    runner_options = conninfo_to_dict(os.environ['DATABASE_URL'])
    datasets = []
    with psycopg.connect(make_conninfo(**(owner_options | dict(dbname='postgres'))), autocommit=True) as admin:
        for entry in protocol['datasets']:
            name = 'ii_generalization_' + uuid4().hex[:12]
            admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
            try:
                with psycopg.connect(make_conninfo(**(owner_options | dict(dbname=name))), autocommit=True) as owner, psycopg.connect(make_conninfo(**(runner_options | dict(dbname=name))), autocommit=True) as runner:
                    if not 170000 <= runner.info.server_version < 180000:
                        raise ValueError('This reference execution requires PostgreSQL17')
                    for filename in ('schema.sql','planning_schema.sql'):
                        owner.execute((ROOT/'sql'/filename).read_text())
                    text = (ROOT/entry['input']).read_text(); sources = json.loads(text)
                    first = replay(owner, runner, sources[:1])
                    first_semantic = semantic(first, sources[0]['cutoff'])
                    t = time.perf_counter(); catalog = replay(owner, runner, sources, text)
                    replay_seconds = time.perf_counter()-t
                    cells = audit(catalog, sources, entry['expected'])
                    if semantic(catalog, sources[0]['cutoff']) != first_semantic:
                        raise AssertionError('New source versions changed historical semantic result')
                    counts = owner.execute('SELECT count(*) FROM synthetic_replay.sources').fetchone()[0]
                    batches = owner.execute('SELECT count(*) FROM operational_fixture.batches').fetchone()[0]
                    admit(owner, sources)
                    if owner.execute('SELECT count(*) FROM operational_fixture.batches').fetchone()[0] != batches:
                        raise AssertionError('Retry duplicated source rows')
                    changed = deepcopy(sources[:2]); changed[0]['version_id']='rollback-candidate'; changed[1]['keys'][0]['stock']+=1
                    try: admit(owner, changed)
                    except ValueError: pass
                    else: raise AssertionError('Conflicting immutable version admitted')
                    if owner.execute("SELECT count(*) FROM synthetic_replay.sources WHERE version_id='rollback-candidate'").fetchone()[0]:
                        raise AssertionError('Earlier version did not roll back')
                    owner.execute("""CREATE FUNCTION synthetic_replay.reject_late() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.version_id='late-failure' THEN RAISE EXCEPTION 'late probe'; END IF; RETURN NEW; END $$""")
                    owner.execute('CREATE TRIGGER late_probe BEFORE INSERT ON synthetic_replay.sources FOR EACH ROW EXECUTE FUNCTION synthetic_replay.reject_late()')
                    failed = deepcopy(sources[:2]); failed[0]['version_id']='late-before'; failed[1]['version_id']='late-failure'
                    try: admit(owner, failed)
                    except psycopg.Error: pass
                    else: raise AssertionError('Late failure was not exercised')
                    if owner.execute('SELECT count(*) FROM synthetic_replay.sources').fetchone()[0] != counts or owner.execute('SELECT count(*) FROM operational_fixture.batches').fetchone()[0] != batches:
                        raise AssertionError('Late failure left partial source rows')
                    for change in ('duplicate_version','null_stock','future_knowledge'):
                        invalid = deepcopy(sources)
                        if change=='duplicate_version': invalid[1]['version_id']=invalid[0]['version_id']
                        elif change=='null_stock': invalid[0]['keys'][0]['stock']=None
                        else: invalid[0]['known_at']='2030-01-01T00:00:00+00:00'
                        try: validate_sources(invalid)
                        except (ValueError,TypeError): pass
                        else: raise AssertionError(change+' accepted')
                    for conn, query in ((runner,'DELETE FROM operational_fixture.snapshots'),(owner,'UPDATE operational_fixture.snapshots SET on_hand_qty=0')):
                        try: conn.execute(query)
                        except psycopg.Error: pass
                        else: raise AssertionError('Source write boundary failed')
                    fresh = replay(owner, runner, sources[:1])
                    if semantic(fresh, sources[0]['cutoff']) != first_semantic or set(fresh['reports']) & set(first['reports']):
                        raise AssertionError('Historical rerun lost semantic reproducibility or fresh identity')
                    with TemporaryDirectory() as directory:
                        published = publish(catalog, directory); good_bytes=published.read_bytes()
                        broken=deepcopy(catalog); broken['source_versions'][0]['keys'][0]['stock']+=1
                        try: publish(broken,directory)
                        except ValueError: pass
                        else: raise AssertionError('Invalid catalog published')
                        try: publish(catalog,directory)
                        except FileExistsError: pass
                        else: raise AssertionError('Existing publication overwritten')
                        if published.read_bytes()!=good_bytes or len(list(Path(directory).iterdir()))!=1:
                            raise AssertionError('Failed publication damaged last-good catalog')
                        load_catalog(published)
                        datasets.append(dict(input=entry['input'], runtime=f'PostgreSQL {runner.info.server_version}; restricted {runner.info.user}',
                            input_sha256=protocol['source_sha256'][entry['input']],archive_digest=catalog['digest'],
                            keys_per_version=len(sources[0]['keys']),cutoffs=len(sources),saved_reports=len(catalog['reports']),
                            checked_cells=cells, exact_rule_triggers=sum(len(e['rule_keys']) for e in entry['expected']),
                            replay_seconds_single_sample=replay_seconds,compressed_bytes=len(good_bytes),raw_bytes=len(json.dumps(catalog,separators=(',',':')).encode()),
                            archive_name=Path(entry['input']).stem+'.json.gz',archive_bytes=good_bytes,
                            controls=dict(idempotent=True,version_conflict_rollback=True,late_transaction_rollback=True,invalid_sources=True,source_write_denied=True,historical_fresh_rerun=True,last_good_publication=True)))
            finally:
                admin.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(name)))
            if time.monotonic()-started > protocol['budget_seconds']:
                raise TimeoutError('Study exceeded frozen budget')
    output.mkdir(parents=True)
    for dataset in datasets:
        (output/dataset['archive_name']).write_bytes(dataset.pop('archive_bytes'))
    receipt=dict(protocol_version=protocol['protocol_version'],synthetic=True,protocol_sha256=protocol_hash,
                 code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                 source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('scripts/generalization_study.py','src/inventory_intelligence/insights.py','src/inventory_intelligence/synthetic_replay.py','src/inventory_intelligence/exception_review.py')},
                 datasets=datasets,total_seconds=time.monotonic()-started,max_rss_platform_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                 boundary='Fresh independent arithmetic/discovery/rollback controls. No unseen detection accuracy, policy promotion, maximum-scale, network or production claim.')
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    receipt=run(args.output_dir)
    print(json.dumps(dict(datasets=len(receipt['datasets']),cells=sum(len(d['checked_cells']) for d in receipt['datasets']),triggers=sum(d['exact_rule_triggers'] for d in receipt['datasets']),seconds=receipt['total_seconds'])))
