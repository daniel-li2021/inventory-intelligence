"""Export immutable saved synthetic product reports from a fresh database."""
import argparse
from datetime import timedelta
import gzip
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import psycopg
from inventory_intelligence.demand import midnight
from inventory_intelligence.planning_runs import exact_json, run_forecast
from inventory_intelligence.reliability import run_checks
from inventory_intelligence.replenishment import run_plan
from inventory_intelligence.product import archive_digest, normalize_report, validate_catalog
from synthetic.product_demo import load_inputs


def export(owner,runner,sku_count=50,prefix='product'):
    fixture=load_inputs(owner,sku_count,prefix)
    dimensions={}
    for table in ('styles','skus','warehouses'):
        with owner.cursor(row_factory=psycopg.rows.dict_row) as cur:
            dimensions[table]=cur.execute('SELECT * FROM operational_fixture.'+table+' ORDER BY 1').fetchall()
    archive=dict(contract_version='inventory-product-evidence-v1',synthetic=True,
        business_data='synthetic only',rules_version='inventory-insights-v1',dimensions=dimensions,
        objects={},reports={},cutoffs=[],controls={},runtime=f'PostgreSQL server_version={runner.info.server_version}; restricted ii_runner')
    def save(report):
        report=exact_json(report)
        archive['reports'][report['run_id']]={'digest':archive_digest(report,exclude_digest=False),
            'report':normalize_report(report,archive['objects'])}
        return report['run_id']
    for day in fixture['cutoffs']:
        origin,stem=midnight(day),f'{prefix}:{day}'
        reliability=run_checks(runner,ledger_batch_id=stem+':ledger',snapshot_batch_id=stem+':snapshot',
            as_of=origin,evaluated_at=origin,code_version='product-export-v1')
        if reliability['overall_status']!='pass':
            raise ValueError('normal inventory fixture must pass')
        binding=dict(cutoff=day.isoformat(),reliability_run_id=save(reliability),keys=[])
        for ki,key in enumerate(fixture['keys']):
            options=dict(batch_id=f'{stem}:key-{ki}:demand',sku_id=key['sku_id'],warehouse_id=key['warehouse_id'],
                start_day=day-timedelta(days=28),origin_day=day,method='mean',code_version='product-export-v1')
            saved_forecast=run_forecast(runner,**options,horizon=28)
            plan=run_plan(runner,**options,reliability_run_id=reliability['run_id'],supply_batch_id=f'{stem}:key-{ki}:supply')
            binding['keys'].append(dict(sku_id=key['sku_id'],warehouse_id=key['warehouse_id'],
                forecast_run_id=save(saved_forecast),plan_run_id=save(plan),
                future_demand=dict(id=f'{stem}:key-{ki}:declared-future',quantities=[0 if ki%8==3 else 4]*28,
                    source='declared synthetic constant demand; not a future observation')))
        archive['cutoffs'].append(binding)
    # Isolated defect uses new batches, never edits any normal source or prior report.
    day=fixture['cutoffs'][-1]; origin=midnight(day); stem=f'{prefix}:{day}'
    with owner.transaction():
        owner.execute("INSERT INTO operational_fixture.batches SELECT batch_id || ':duplicate-control',kind,status,baseline_at,as_of,watermark,observed_at,expected_row_count+CASE WHEN kind='snapshot' THEN 1 ELSE 0 END FROM operational_fixture.batches WHERE batch_id IN (%s,%s)",(stem+':ledger',stem+':snapshot'))
        for table in ('coverage','opening_balances','snapshots'):
            columns=[r[0] for r in owner.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='operational_fixture' AND table_name=%s ORDER BY ordinal_position",(table,))]
            expressions=["row_id || ':duplicate-control'" if c=='row_id' else "batch_id || ':duplicate-control'" if c=='batch_id' else c for c in columns]
            owner.execute('INSERT INTO operational_fixture.'+table+' SELECT '+','.join(expressions)+' FROM operational_fixture.'+table+' WHERE batch_id IN (%s,%s)',(stem+':ledger',stem+':snapshot'))
        owner.execute("INSERT INTO operational_fixture.snapshots SELECT row_id || ':extra',batch_id,sku_id,warehouse_id,on_hand_qty,as_of,watermark,observed_at FROM operational_fixture.snapshots WHERE batch_id=%s ORDER BY row_id LIMIT 1",(stem+':snapshot:duplicate-control',))
    defect=run_checks(runner,ledger_batch_id=stem+':ledger:duplicate-control',snapshot_batch_id=stem+':snapshot:duplicate-control',as_of=origin,evaluated_at=origin,code_version='product-export-v1')
    control_plan=run_plan(runner,**dict(batch_id=stem+':key-0:demand',sku_id=fixture['keys'][0]['sku_id'],warehouse_id=fixture['keys'][0]['warehouse_id'],start_day=day-timedelta(days=28),origin_day=day,method='mean',code_version='product-export-v1'),reliability_run_id=defect['run_id'],supply_batch_id=stem+':key-0:supply')
    archive['controls']['duplicate_inventory']=dict(reliability_run_id=save(defect),plan_run_id=save(control_plan),scope='global nonpassing inventory suppresses every selected-key plan')
    archive=exact_json(archive)
    archive['digest']=archive_digest(archive)
    validate_catalog(archive)
    return archive


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('src/inventory_intelligence/product_evidence.json.gz'))
    parser.add_argument('--sku-count',type=int,choices=(4,50),default=50)
    parser.add_argument('--prefix',default='product')
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError('refuse to overwrite retained evidence; use a new output path')
    with psycopg.connect(os.environ['FIXTURE_DATABASE_URL'],autocommit=True) as owner,psycopg.connect(os.environ['DATABASE_URL'],autocommit=True) as runner:
        archive=export(owner,runner,args.sku_count,args.prefix)
    raw=json.dumps(archive,sort_keys=True,separators=(',',':')).encode()
    if args.output.exists():
        raise ValueError('refuse to overwrite retained evidence; use a new output path')
    args.output.write_bytes(gzip.compress(raw,mtime=0) if args.output.suffix=='.gz' else raw)
    print(json.dumps(dict(output=str(args.output),digest=archive['digest'],keys=args.sku_count*2,cutoffs=3,saved_reports=len(archive['reports']),raw_bytes=len(raw))))

if __name__=='__main__':
    main()
