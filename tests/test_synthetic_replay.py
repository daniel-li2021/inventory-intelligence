"""Independent exact controls over retained real PostgreSQL replay evidence."""
from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest
from fastapi.testclient import TestClient

from inventory_intelligence.product import load_catalog, validate_catalog, archive_digest, _report, detail, history, scenario
from inventory_intelligence.synthetic_replay import validate_sources, publish, source_tables, parse_input
from inventory_intelligence.insights import discover
from inventory_intelligence.lab_api import create_app
from inventory_intelligence.lab_hosted import HostedLab

ROOT = Path(__file__).resolve().parents[1]
SAVED = ROOT/'docs/review/dynamic-replay-v1.json.gz'
KEY = ('product-dynamic:a','product-dynamic:harbor')


class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources=json.loads((ROOT/'docs/examples/dynamic-controls-v1.json').read_text())
        cls.catalog=load_catalog(SAVED)

    def test_predeclared_exact_planner_controls_and_nulls(self):
        for day,proposal,balances in [('2026-04-06',6,[4,6,3,0,-3]),('2026-04-13',18,[-3,-7,-11,-12,-16]),('2026-04-20',18,[-3,-7,-11,-12,-16])]:
            result=detail(self.catalog,day,*KEY)
            self.assertEqual(result['proposed_order_qty'],str(proposal))
            binding=next(b for b in self.catalog['cutoffs'] if b['cutoff']==day)
            key=next(k for k in binding['keys'] if (k['sku_id'],k['warehouse_id'])==KEY)
            self.assertEqual([r['balance_without_order'] for r in _report(self.catalog,key['plan_run_id'])['result']['projection']],list(map(str,balances)))
        missing=detail(self.catalog,'2026-04-06','product-dynamic:b','product-dynamic:upland')
        self.assertIsNone(missing['proposed_order_qty'])
        self.assertEqual(missing['on_hand'],'10')
        self.assertIsNone(scenario(self.catalog,'2026-04-20','product-dynamic:b','product-dynamic:upland')['baseline']['plan'])
        restored=history(self.catalog,'product-dynamic:b','product-dynamic:upland')['points'][1]
        self.assertFalse(restored['comparable']);self.assertIsNone(restored['stock_delta'])

    def test_predeclared_exact_discovery_sets_no_extra_findings(self):
        expected=[{'I201':2,'I206':1},{'I202':2,'I203':2,'I204':2,'I205':1,'I206':1},{'I204':2,'I205':1,'I206':1}]
        from collections import Counter
        for binding, oracle in zip(self.catalog['cutoffs'],expected):
            result=discover(self.catalog,binding['cutoff'])
            self.assertEqual(Counter(r['rule_id'] for r in result['findings']),oracle)
            self.assertTrue(all(r['sku_id']=='product-dynamic:a' for r in result['findings']))
            self.assertEqual(len({f['id'] for f in result['findings']}),len(result['findings']))
            self.assertTrue(all(f['references'] and f['missing_evidence'] and f['next_step'] for f in result['findings']))

    def test_exact_demand_supply_and_imbalance_facts(self):
        first=discover(self.catalog,'2026-04-06')['findings']
        demand=next(f for f in first if f['rule_id']=='I201')
        self.assertEqual(demand['values'],dict(older_daily=dict(numerator='2',denominator='1'),recent_daily=dict(numerator='4',denominator='1'),delta_daily=dict(numerator='2',denominator='1'),change_ratio=dict(numerator='1',denominator='1')))
        imbalance=next(f for f in first if f['rule_id']=='I206')
        self.assertEqual(imbalance['values']['surplus_exposure'],dict(numerator='65',denominator='1'))
        self.assertEqual(len(imbalance['members']),2)
        later=discover(self.catalog,'2026-04-13')['findings']
        reduced=next(f for f in later if f['rule_id']=='I203')
        self.assertEqual(reduced['values'],dict(previous_pieces='5',current_pieces='3',delta_pieces='-2'))
        risk=next(f for f in later if f['rule_id']=='I205')
        self.assertEqual(risk['values'],dict(previous_proposal='6',current_proposal='18',previous_shortage_days='0',current_shortage_days='2'))

    def test_source_validation_integer_dimensions_scope_and_clocks(self):
        faults=[lambda s:s[0]['keys'][0].update(stock=None),lambda s:s[0]['keys'][0].update(stock=True),lambda s:s[0]['keys'][0].update(stock=1.5),lambda s:s[0]['keys'][0].update(stock=-1),lambda s:s[0]['keys'][0]['demand'].pop(),lambda s:s[0]['keys'].pop(),lambda s:s[0].update(known_at='2026-04-07T07:00:00+00:00'),lambda s:s[1].update(version_id='v1'),lambda s:s[0]['keys'][0]['inbound'].append(deepcopy(s[0]['keys'][0]['inbound'][0])),lambda s:s[1]['dimensions']['skus'][0].update(base_uom='case'),lambda s:s[0]['keys'][0].update(supply_complete=1),lambda s:s[0]['keys'][0]['policy'].update(review_days=60)]
        for fault in faults:
            sources=deepcopy(self.sources);fault(sources)
            with self.assertRaises(ValueError):validate_sources(sources)
        self.assertEqual(validate_sources(self.sources),self.sources)

    def test_rehashed_changed_sources_and_origins_fail_closed(self):
        for field in ('stock','future_demand','dimensions','known_at'):
            c=deepcopy(self.catalog)
            if field=='stock':c['source_versions'][0]['keys'][0]['stock']+=1
            elif field=='future_demand':c['source_versions'][0]['keys'][0]['future_demand'][0]+=1
            elif field=='dimensions':c['dimensions']['skus'][0]['size']='XL'
            else:c['source_versions'][0]['known_at']='2026-04-07T07:00:00+00:00'
            c['original_input_text']=json.dumps(c['source_versions'])
            c['cutoffs'][0]['source_digest']=archive_digest(c['source_versions'][0],False)
            c['digest']=archive_digest(c)
            with self.subTest(field=field),self.assertRaises(ValueError):validate_catalog(c)

    def test_immutable_publication_and_retained_original_bytes(self):
        self.assertEqual(self.catalog['original_input_text'],(ROOT/'docs/examples/dynamic-controls-v1.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            path=publish(self.catalog,tmp);original=path.read_bytes()
            with self.assertRaises(FileExistsError):publish(self.catalog,tmp)
            bad=deepcopy(self.catalog);bad['digest']='0'*64
            with self.assertRaises(ValueError):publish(bad,tmp)
            self.assertEqual(path.read_bytes(),original)
            self.assertEqual(load_catalog(path),self.catalog)

    def test_duplicate_json_fields_and_oversize_input_rejected(self):
        with self.assertRaises(ValueError):parse_input('{"quantity":0,"quantity":9}')
        with self.assertRaises(ValueError):parse_input(' '* (24*1024*1024+1))

    def test_multiline_supply_does_not_get_collapsed_by_legacy_scenario(self):
        from inventory_intelligence.product import normalize_report
        c=deepcopy(self.catalog);key=c['cutoffs'][0]['keys'][0];r=deepcopy(_report(c,key['plan_run_id']))
        r['result']['supply']['reservations'].append(r['result']['supply']['reservations'][0]|dict(reservation_id='second'))
        c['reports'][r['run_id']]['report']=normalize_report(r,c['objects'])
        result=scenario(c,'2026-04-06',*KEY)
        self.assertIsNone(result['baseline']['plan'])
        self.assertIn('use_one_review_contrast',result['baseline']['reasons'][0])

    def test_history_retains_discovery_and_common_comparison_api(self):
        points=history(self.catalog,*KEY)['points']
        self.assertIn('Worsening replenishment risk',[r['title'] for r in points[1]['discovery_findings']])
        client=TestClient(HostedLab(create_app(catalog_path=SAVED),burst=100))
        query='?cutoff=2026-04-06&sku_id=product-dynamic:a&warehouse_id=product-dynamic:harbor&quantity=12'
        result=client.get('/api/product/contrast'+query)
        self.assertEqual(result.status_code,200);self.assertEqual(result.json()['arms']['alternative']['total_cost'],'14609')
        self.assertEqual(client.get('/api/product/contrast'+query+'&delay_days=-1').status_code,422)

    def test_read_only_api_and_stale_source_bindings(self):
        client=TestClient(HostedLab(create_app(catalog_path=SAVED),burst=100))
        self.assertEqual(client.get('/api/product/overview').status_code,200)
        response=client.get('/api/product/insights?cutoff=2026-04-06')
        self.assertEqual(response.status_code,200);self.assertEqual(len(response.json()['findings']),3)
        self.assertEqual(client.get('/api/product/insights?archive_digest='+'0'*64).status_code,409)
        self.assertEqual(client.get('/api/product/insights?cutoff=2026-04-06&cutoff=2026-04-13').status_code,422)
        for path in ('/api/product/upload','/api/product/replay','/api/product/ingest'):
            self.assertEqual(client.post(path,json=self.sources).status_code,404)
        self.assertEqual(client.post('/api/product/insights',json={}).status_code,405)

    def test_incompatible_policy_suppresses_history_patterns(self):
        # An independently changed comparison signature cannot claim persistence.
        c=deepcopy(self.catalog)
        from inventory_intelligence.product import normalize_report
        key=c['cutoffs'][1]['keys'][0];r=deepcopy(_report(c,key['plan_run_id']))
        r['model_version']='other-model'
        c['reports'][r['run_id']]['report']=normalize_report(r,c['objects'])
        found=discover(c,'2026-04-13')['findings']
        self.assertFalse(any(f['rule_id'] in ('I202','I203','I204','I205') and f['warehouse_id']==KEY[1] for f in found))

    def test_zero_baseline_growth_is_undefined_and_negative_change_supported(self):
        from inventory_intelligence.product import normalize_report
        for values, title in (([0]*14+[2]*14,'Recent demand increase'),([4]*14+[2]*14,'Recent demand decrease')):
            c=deepcopy(self.catalog);key=c['cutoffs'][0]['keys'][0];r=deepcopy(_report(c,key['plan_run_id']))
            for day,qty in zip(r['result']['training']['days'],values):day['quantity']=qty
            c['reports'][r['run_id']]['report']=normalize_report(r,c['objects'])
            finding=next(f for f in discover(c,'2026-04-06')['findings'] if f['rule_id']=='I201' and f['warehouse_id']==KEY[1])
            self.assertEqual(finding['title'],title)
            if values[0]==0:self.assertIsNone(finding['values']['change_ratio'])

if __name__=='__main__':unittest.main()
