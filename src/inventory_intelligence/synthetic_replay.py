"""Explicit local synthetic admission; immutable sources and real kernel replay."""
from datetime import date, timedelta
import gzip
import json
import os
from pathlib import Path
import re
import tempfile

from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .demand import BUSINESS_TIMEZONE, midnight
from .planning_runs import exact_json, run_forecast
from .copilot_planning import load_planning_run
from .copilot import load_run
from .reliability import run_checks
from .replenishment import run_plan
from .product import archive_digest, normalize_report, _instant, _require, BOUNDS

INPUT_BYTES = 2 * 1024 * 1024


def parse_input(text):
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result: raise ValueError('duplicate JSON field')
            result[key]=value
        return result
    _require(isinstance(text,str) and len(text.encode())<=12*INPUT_BYTES)
    return json.loads(text,object_pairs_hook=unique)


def _piece(value):
    _require(type(value) is int and 0 <= value <= 9223372036854775807)


def validate_sources(sources):
    """One fixed scope, chronological versions; gaps in demand stay explicit."""
    _require(type(sources) is list and 1 <= len(sources) <= 12)
    ids, cutoffs = set(), []
    for source in sources:
        _require(set(source) == {'contract_version','synthetic','dataset_id','version_id',
                                'cutoff','known_at','dimensions','keys'})
        _require(source['contract_version'] == 'synthetic-intake-v1' and source['synthetic'] is True)
        _require(len(json.dumps(source, allow_nan=False).encode()) <= INPUT_BYTES)
        for field in ('dataset_id','version_id'):
            _require(isinstance(source[field], str) and re.fullmatch(r'[A-Za-z0-9_-]{1,64}', source[field]))
        _require(source['dataset_id'] == sources[0]['dataset_id'])
        _require(source['version_id'] not in ids); ids.add(source['version_id'])
        day = date.fromisoformat(source['cutoff']); cutoffs.append(day)
        _require(_instant(source['known_at']) == midnight(day))
        dims = source['dimensions']
        _require(dims == sources[0]['dimensions'] and set(dims) == {'styles','skus','warehouses'})
        _require(1 <= len(dims['skus']) <= 50 and 1 <= len(dims['warehouses']) <= 2 and 1 <= len(dims['styles']) <= 50)
        for table, fields, identity in (
            ('styles', {'style_id','style_code','name'}, 'style_id'),
            ('skus', {'sku_id','style_id','sku_code','color','size','base_uom'}, 'sku_id'),
            ('warehouses', {'warehouse_id','warehouse_code','name'}, 'warehouse_id')):
            _require(all(set(row) == fields and all(isinstance(v,str) and 0 < len(v) <= 100 and v.strip() for v in row.values()) for row in dims[table]))
            _require(len({r[identity] for r in dims[table]}) == len(dims[table]))
            _require(all(r[identity].startswith('product') for r in dims[table]))
        _require(all(s['base_uom'] == 'each' and s['style_id'] in {r['style_id'] for r in dims['styles']} for s in dims['skus']))
        expected = {(s['sku_id'], w['warehouse_id']) for s in dims['skus'] for w in dims['warehouses']}
        _require(len(source['keys']) == len(expected) and {(k['sku_id'],k['warehouse_id']) for k in source['keys']} == expected)
        for key in source['keys']:
            _require(set(key) == {'sku_id','warehouse_id','stock','demand','supply_complete',
                                  'policy','reservations','inbound','future_demand'})
            _piece(key['stock']); _require(type(key['supply_complete']) is bool)
            _require(len(key['demand']) == len(key['future_demand']) == 28)
            for q in key['demand']:
                if q is not None: _piece(q)
            for q in key['future_demand']: _piece(q)
            _require(set(key['policy']) == {'lead_days','review_days','safety_qty','pack_size','moq'})
            for field, value in key['policy'].items():
                _, low, high = BOUNDS[field]
                _require(type(value) is int and low <= value <= high)
            _require(key['policy']['lead_days'] + key['policy']['review_days'] <= 28)
            for table, statuses in (('reservations',('open','fulfilled','cancelled')), ('inbound',('confirmed','pending','cancelled'))):
                rows = key[table]; _require(type(rows) is list and len(rows) <= 16)
                _require(len({r['id'] for r in rows}) == len(rows))
                for row in rows:
                    _require(set(row) == {'id','quantity','day','status'} and isinstance(row['id'],str) and re.fullmatch(r'[A-Za-z0-9_-]{1,64}', row['id']))
                    _piece(row['quantity']); _require(row['status'] in statuses)
                    _require(date.fromisoformat(row['day']) >= day)
    _require(cutoffs == sorted(set(cutoffs)))
    return sources


def source_tables(source):
    """Deterministic source adapter, with no repair or inferred missing quantities."""
    stem = 'replay:' + archive_digest(source, False)
    day = date.fromisoformat(source['cutoff']); origin = midnight(day)
    tables = {t: [] for t in ('batches','coverage','opening_balances','movements','snapshots',
              'demand_batches','order_versions','day_observations','supply_batches','policies','reservations','inbound')}
    for kind in ('ledger','snapshot'):
        batch = stem + ':' + kind
        tables['batches'].append(dict(batch_id=batch, kind=kind, status='complete', baseline_at=midnight(day-timedelta(days=1)) if kind=='ledger' else None,
            as_of=origin, watermark=0, observed_at=origin, expected_row_count=0 if kind=='ledger' else len(source['keys'])))
        for i, key in enumerate(source['keys']):
            fields = {f:key[f] for f in ('sku_id','warehouse_id')}
            tables['coverage'].append(dict(row_id=f'{batch}:coverage:{i:03}',batch_id=batch,**fields))
            if kind == 'ledger':
                tables['opening_balances'].append(dict(row_id=f'{batch}:opening:{i:03}',batch_id=batch,**fields,quantity=key['stock'],as_of=midnight(day-timedelta(days=1)),baseline_ref='declared-independent-synthetic-count'))
            else:
                tables['snapshots'].append(dict(row_id=f'{batch}:snapshot:{i:03}',batch_id=batch,**fields,on_hand_qty=key['stock'],as_of=origin,watermark=0,observed_at=origin))
    for i, key in enumerate(source['keys']):
        fields = {f:key[f] for f in ('sku_id','warehouse_id')}
        batch = f'{stem}:key-{i}:demand'; start = day-timedelta(days=28)
        days, orders = [], []
        for j, qty in enumerate(key['demand']):
            if qty is None: continue
            business = start+timedelta(days=j); known = midnight(business+timedelta(days=1))
            days.append(dict(row_id=f'{batch}:day:{j:02}',batch_id=batch,**fields,business_day=business,revision=1,source_recorded_at=known,observed_at=known,coverage='complete',availability='available',expected_lines=int(qty>0)))
            if qty:
                orders.append(dict(row_id=f'{batch}:order:{j:02}',batch_id=batch,**fields,source_system='synthetic-replay',order_id=f"{source['dataset_id']}:{fields['sku_id']}:{fields['warehouse_id']}:{business}",line_id='1',revision=1,accepted_at=midnight(business)+timedelta(hours=12),source_recorded_at=known,observed_at=known,accepted_qty=qty,status='accepted'))
        tables['demand_batches'].append(dict(batch_id=batch,version_id=source['version_id'],business_timezone=BUSINESS_TIMEZONE,start_day=start,end_day=day,assembled_at=origin,status='complete',expected_orders=len(orders),expected_days=len(days)))
        tables['order_versions'].extend(orders); tables['day_observations'].extend(days)
        supply = f'{stem}:key-{i}:supply'
        tables['supply_batches'].append(dict(batch_id=supply,version_id=source['version_id'],**fields,as_of=origin,observed_at=origin,status='complete',reservations_complete=key['supply_complete'],inbound_complete=key['supply_complete'],expected_reservations=len(key['reservations']),expected_inbound=len(key['inbound'])))
        tables['policies'].append(dict(row_id=supply+':policy',batch_id=supply,**key['policy'],source_recorded_at=origin,observed_at=origin))
        for table, natural, clock in (('reservations','reservation_id','due_day'),('inbound','inbound_id','arrival_day')):
            tables[table].extend(dict(row_id=f"{supply}:{table}:{r['id']}",batch_id=supply,source_system='synthetic-replay',**{natural:r['id'],clock:date.fromisoformat(r['day'])},remaining_qty=r['quantity'],status=r['status'],source_recorded_at=origin,observed_at=origin) for r in key[table])
    return stem, exact_json(tables)


def _insert(conn, schema, table, rows):
    if not rows: return
    keys = list(rows[0])
    query = sql.SQL('INSERT INTO {}.{} ({}) VALUES ({})').format(sql.Identifier(schema),sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,keys)),sql.SQL(',').join(sql.Placeholder() for _ in keys))
    with conn.cursor() as cur: cur.executemany(query, [[r[k] for k in keys] for r in rows])


def _local(conn):
    _require(conn.info.host in ('127.0.0.1','localhost','::1') or conn.info.host.startswith('/'))
    _require(conn.autocommit and conn.info.transaction_status.name == 'IDLE')


def admit(owner, sources):
    _local(owner); validate_sources(sources)
    with owner.transaction():
        # Serialize retries and conflicting producers before looking up identities.
        owner.execute("SELECT pg_advisory_xact_lock(712934021)")
        if owner.execute("SELECT to_regclass('synthetic_replay.sources')").fetchone()[0] is None:
            occupied=owner.execute('''SELECT EXISTS (
                SELECT 1 FROM operational_fixture.styles UNION ALL
                SELECT 1 FROM operational_fixture.skus UNION ALL
                SELECT 1 FROM operational_fixture.warehouses UNION ALL
                SELECT 1 FROM operational_fixture.batches UNION ALL
                SELECT 1 FROM planning.runs UNION ALL SELECT 1 FROM reliability.runs)''').fetchone()[0]
            _require(not occupied)  # First admission requires a dedicated empty synthetic DB.
        owner.execute('CREATE SCHEMA IF NOT EXISTS synthetic_replay')
        owner.execute('CREATE TABLE IF NOT EXISTS synthetic_replay.sources (dataset_id text NOT NULL, version_id text NOT NULL, digest text NOT NULL, payload jsonb NOT NULL, PRIMARY KEY(dataset_id,version_id))')
        owner.execute("""CREATE OR REPLACE FUNCTION synthetic_replay.immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'immutable synthetic source'; END $$""")
        for schema, tables in (('operational_fixture', ('styles','skus','warehouses','batches','coverage','opening_balances','movements','snapshots')), ('planning_input', ('demand_batches','order_versions','day_observations','supply_batches','policies','reservations','inbound')), ('synthetic_replay', ('sources',))):
            for table in tables:
                owner.execute(sql.SQL('CREATE OR REPLACE TRIGGER synthetic_immutable BEFORE UPDATE OR DELETE ON {}.{} FOR EACH ROW EXECUTE FUNCTION synthetic_replay.immutable()').format(sql.Identifier(schema),sql.Identifier(table)))
        for source in sources:
            identity = archive_digest(source, False)
            prior = owner.execute('SELECT digest,payload FROM synthetic_replay.sources WHERE dataset_id=%s AND version_id=%s',(source['dataset_id'],source['version_id'])).fetchone()
            if prior:
                _require(prior == (identity, source)); continue
            for table, rows in source['dimensions'].items():
                field = {'styles':'style_id','skus':'sku_id','warehouses':'warehouse_id'}[table]
                for row in rows:
                    with owner.cursor(row_factory=dict_row) as cur:
                        old = cur.execute(sql.SQL('SELECT * FROM operational_fixture.{} WHERE {}=%s').format(sql.Identifier(table),sql.Identifier(field)),(row[field],)).fetchone()
                    if old: _require(old == row)
                    else: _insert(owner, 'operational_fixture', table, [row])
            _, tables = source_tables(source)
            for table, rows in tables.items():
                schema = 'operational_fixture' if table in ('batches','coverage','opening_balances','movements','snapshots') else 'planning_input'
                _insert(owner,schema,table,rows)
            owner.execute('INSERT INTO synthetic_replay.sources VALUES (%s,%s,%s,%s)',(source['dataset_id'],source['version_id'],identity,Jsonb(source)))


def replay(owner, runner, sources, original_text=None):
    from .product import validate_catalog
    _local(runner)
    _require(owner.info.dbname == runner.info.dbname and owner.info.port == runner.info.port and owner.info.host == runner.info.host and runner.info.user == 'ii_runner')
    validate_sources(sources)
    original_text = original_text or json.dumps(sources,sort_keys=True,separators=(',',':'))
    _require(parse_input(original_text) == sources)
    admit(owner,sources)
    archive = dict(contract_version='inventory-product-evidence-v2',synthetic=True,business_data='synthetic only',rules_version='inventory-insights-v1',
        dimensions=sources[0]['dimensions'],source_versions=sources,original_input_text=original_text,
        objects={},reports={},cutoffs=[],controls={},runtime=f'PostgreSQL server_version={runner.info.server_version}; restricted ii_runner')
    def save(report):
        report = exact_json(report)
        if 'kind' in report: _require(load_planning_run(runner,report['run_id']) == report)
        archive['reports'][report['run_id']] = dict(digest=archive_digest(report,False),report=normalize_report(report,archive['objects']))
        return report['run_id']
    for source in sources:
        day = date.fromisoformat(source['cutoff']); stem,_ = source_tables(source)
        reliability = run_checks(runner,ledger_batch_id=stem+':ledger',snapshot_batch_id=stem+':snapshot',as_of=midnight(day),evaluated_at=midnight(day),code_version='synthetic-replay-v1')
        _require(reliability['overall_status']=='pass')
        _require(exact_json(load_run(runner,reliability['run_id'])) == exact_json(reliability))
        binding = dict(cutoff=source['cutoff'],source_digest=archive_digest(source,False),reliability_run_id=save(reliability),keys=[])
        for i,key in enumerate(source['keys']):
            options = dict(batch_id=f'{stem}:key-{i}:demand',sku_id=key['sku_id'],warehouse_id=key['warehouse_id'],start_day=day-timedelta(days=28),origin_day=day,method='mean',code_version='synthetic-replay-v1')
            fc = run_forecast(runner,**options,horizon=28)
            plan = run_plan(runner,**options,reliability_run_id=reliability['run_id'],supply_batch_id=f'{stem}:key-{i}:supply')
            binding['keys'].append(dict(sku_id=key['sku_id'],warehouse_id=key['warehouse_id'],forecast_run_id=save(fc),plan_run_id=save(plan),future_demand=dict(id=f'{stem}:key-{i}:declared-future',quantities=key['future_demand'],source='declared synthetic demand; not observations')))
        archive['cutoffs'].append(binding)
    archive['digest'] = archive_digest(archive)
    return validate_catalog(archive)


def publish(archive, directory):
    """Publish only complete evidence; no overwrite, pointer switch or source write."""
    from .product import validate_catalog
    validate_catalog(archive)
    directory = Path(directory); directory.mkdir(parents=True,exist_ok=True)
    raw = json.dumps(archive,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    path = directory/(archive['digest']+'.json.gz')
    with tempfile.NamedTemporaryFile(dir=directory,delete=False) as stream:
        temp = Path(stream.name); stream.write(gzip.compress(raw,mtime=0)); stream.flush(); os.fsync(stream.fileno())
    try:
        os.link(temp,path)
    finally: temp.unlink()
    return path


def validate_bindings(catalog, expanded):
    """Reconstruct every retained input from immutable source versions, offline."""
    sources = validate_sources(catalog['source_versions'])
    _require(parse_input(catalog['original_input_text']) == sources and catalog['dimensions'] == sources[0]['dimensions'])
    _require(len(sources) == len(catalog['cutoffs']) and not catalog['controls'])
    expected_runs = set()
    for source, binding in zip(sources,catalog['cutoffs']):
        stem,tables = source_tables(source)
        _require(binding['cutoff'] == source['cutoff'] and binding['source_digest'] == archive_digest(source,False))
        expected_runs.add(binding['reliability_run_id'])
        _require(len(binding['keys']) == len(source['keys']))
        for i,(key,saved) in enumerate(zip(source['keys'],binding['keys'])):
            _require(all(saved[f] == key[f] for f in ('sku_id','warehouse_id')))
            plan = expanded[saved['plan_run_id']]; fc = expanded[saved['forecast_run_id']]
            expected_runs.update((saved['plan_run_id'],saved['forecast_run_id']))
            result = plan['result']; supply = result['supply']; series = result['training']
            _require(plan['context']['batch_id'] == f'{stem}:key-{i}:demand' and plan['context']['supply_batch_id'] == f'{stem}:key-{i}:supply')
            _require(result['inventory']['source'] == {t:sorted(tables[t],key=lambda r:r.get('row_id',r.get('batch_id'))) for t in ('batches','coverage','opening_balances','movements','snapshots')})
            def rows(table, batch): return sorted([r for r in tables[table] if r['batch_id']==batch],key=lambda r:r['row_id'])
            batch = plan['context']['batch_id']; sb = plan['context']['supply_batch_id']
            _require(series['batch'] == next(r for r in tables['demand_batches'] if r['batch_id']==batch))
            _require(series['order_versions'] == rows('order_versions',batch) and series['day_versions'] == sorted(rows('day_observations',batch),key=lambda r:(r['business_day'],r['revision'],r['row_id'])))
            _require(supply['batch'] == next(r for r in tables['supply_batches'] if r['batch_id']==sb))
            _require(all(supply[t] == rows(t,sb) for t in ('reservations','inbound','policies')))
            _require(saved['future_demand']['quantities'] == key['future_demand'])
            _require(fc['result']['training'] == series)
    _require(set(catalog['reports']) == expected_runs)
