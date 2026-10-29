"""Smoke-test an installed product wheel from outside the source checkout."""
import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from inventory_intelligence import product
from inventory_intelligence.lab_api import create_app
from inventory_intelligence.lab_hosted import HostedLab


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    module = Path(product.__file__).resolve()
    if 'site-packages' not in module.parts:
        raise ValueError('This check requires an installed wheel, not PYTHONPATH=src')
    with patch('psycopg.connect', side_effect=AssertionError('Offline demo must not connect to a database')):
        client = TestClient(HostedLab(burst=100))
        for path in ('/', '/lab', '/api/lab', '/health/live', '/health/ready'):
            response = client.get(path)
            assert response.status_code == 200, (path, response.status_code)
        overview = client.get('/api/product/overview').json()
        assert overview['summary'] == dict(risk=37, opportunity=25, evidence=12, none=26,
                                           keys=100, assessable=88, blocked=12)
        assert client.get('/api/lab').json()['baseline']['plan']['proposed_order_qty'] == 12
        execution=client.get('/api/execution').json()
        assert len(execution['manual'])==7 and len(execution['comparisons'])==12
        assert execution['journal_enabled'] is False
        assert client.post('/api/execution/admit',json={}).status_code==404
        cold=client.get('/api/execution/detail?name=cold-shortage').json()
        assert cold['summary']['total_cost']=='776' and cold['summary']['proposals']==['18',None,None]
        selected = dict(cutoff='2026-01-05', sku_id='product:sku-00', warehouse_id='product:harbor',
                        archive_digest=overview['archive_digest'])
        demand = client.get('/api/product/demand', params=selected | dict(horizon=28)).json()
        assert demand['contract_version'] == 'demand-planning-v1'
        assert demand['totals']['baseline'] == dict(numerator='112', denominator='1')
        planned = client.post('/api/product/demand-scenario', json=selected | dict(
            adjustment=dict(kind='percent', value=25, start_day='2026-01-05', end_day='2026-02-01'))).json()
        assert planned['totals']['adjusted'] == dict(numerator='140', denominator='1')
        assert planned['impact']['adjusted']['proposed_order_qty'] == '18'
        assert planned['daily'][:28] == demand['daily'][:28]
        detail = client.get('/api/product/detail', params=selected)
        assert detail.status_code == 200 and detail.json()['proposed_order_qty'] == '12'
        scenario = client.post('/api/product/scenario', json=selected | {'overrides': {'demand_percent': 125}})
        assert scenario.status_code == 200 and scenario.json()['scenario']['plan']['proposed_order_qty'] == '18'
        blocked = client.post('/api/product/scenario', json=selected | {'overrides': {'evidence_case': 'incomplete_supply'}})
        assert blocked.status_code == 200 and blocked.json()['scenario']['plan'] is None
        assets = module.with_name('product_static')
        names = []
        for asset in sorted(assets.iterdir()):
            if asset.name == 'index.html':
                continue
            response = client.get('/product-static/'+asset.name)
            assert response.status_code == 200 and response.content == asset.read_bytes(), asset.name
            names.append(asset.name)
        evidence = module.with_name('product_evidence.json.gz')
        result = dict(status='pass', installed_module=str(module), no_database=True, no_node_runtime=True,
                      archive_digest=overview['archive_digest'], packaged_evidence_sha256=hashlib.sha256(evidence.read_bytes()).hexdigest(),
                      served_assets=names, independently_expected_proposals=['12', '18', None])
        feedback=client.get('/api/product/feedback-example').json()
        assert feedback['reports']['overdue_partial']['result']['proposed_order_qty'] is None
        assert feedback['reports']['revised_eta']['result']['proposed_order_qty']==0
        evaluation=client.get('/api/product/evaluation').json()
        assert evaluation['reviews']==144 and evaluation['decision_gate_passes']==2 and evaluation['global_winner'] is None
        terms=client.get('/api/product/decision-context',params=selected).json()
        feasible=client.post('/api/product/supplier-contrast',json=selected|dict(quantity=18,supplier=terms['supplier'])).json()
        assert feasible['arms']['actual_proposal']['feasibility']['promised_day']=='2026-01-07'
        assert feasible['arms']['alternative']['total_cost'] is None
        assert client.post('/api/product/supplier-admit',json={}).status_code==404
        assert client.post('/api/product/transfer-reserve',json={}).status_code==404
        result.update(evaluation_reviews=144, evaluation_summary_sha256=hashlib.sha256(module.with_name('forecast_decision_summary.json').read_bytes()).hexdigest(),
                      feasible_supplier_calendar=True,blocked_capacity_arm=True)
        result.update(execution_archive_digest=execution['archive_digest'],execution_controls=7,paired_policy_cells=36,
                      default_journal_disabled=True, demand_planning=True,
                      demand_expected_totals=['112', '140'], demand_expected_orders=['12', '18'])
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
