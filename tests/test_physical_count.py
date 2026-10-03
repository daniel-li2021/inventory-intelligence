"""Independent physical-count quantities, knowledge clocks and review-binding controls."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from inventory_intelligence.physical_count import evaluate, digest

SOURCE=Path(__file__).resolve().parents[1]/'docs/examples/physical-count-inputs-v1.json'


class PhysicalCountOracles(unittest.TestCase):
    def cases(self): return json.loads(SOURCE.read_text())['cases']
    def base(self): return deepcopy(self.cases()[0]['inputs'])

    def test_all_hand_declared_status_quantity_and_reason_oracles(self):
        cases=self.cases()
        self.assertEqual(len(cases),40)
        for case in cases:
            with self.subTest(case=case['id']):
                inputs=deepcopy(case['inputs']);before=deepcopy(inputs)
                result=evaluate(**inputs)
                actual={k:result[k] for k in case['expected'] if k!='finding_reasons'}
                actual['finding_reasons']=sorted(f['reason'] for f in result['findings'])
                self.assertEqual(actual,case['expected'])
                self.assertEqual(inputs,before)

    def test_confirmation_does_not_repair_book_or_infer_shrinkage(self):
        source=self.base();result=evaluate(**source)
        self.assertEqual((result['system_quantity'],result['physical_quantity'],result['variance_quantity']),(100,96,-4))
        self.assertEqual(result['adjustment_status'],'review_required')
        self.assertIsNone(result['approved_adjustment_quantity'])
        self.assertEqual(source['system']['quantity'],100)
        self.assertEqual(result['as_of'],'2026-02-01T00:00:00+00:00')
        self.assertEqual(result['proposal']['proposal_id'],'ccc019c879383526418a3a59ae78f797052920dd8c51e6c85d4ac40c932b985e')
        self.assertEqual(result['proposal']['delta_quantity'],-4)
        self.assertNotIn('shrinkage',str(result['findings']))

    def test_source_order_and_later_evaluation_preserve_proposal_but_new_run_identity(self):
        source=self.base();first=evaluate(**source)
        reversed_source=deepcopy(source);reversed_source['counts'].reverse()
        reordered=evaluate(**reversed_source)
        self.assertEqual(first['proposal'],reordered['proposal'])
        self.assertEqual(first['count_evidence'],reordered['count_evidence'])
        later=evaluate(**dict(source,evaluated_at='2026-02-01T00:22:00+00:00'))
        self.assertEqual(first['proposal'],later['proposal'])
        self.assertNotEqual(first['run_id'],later['run_id'])
        self.assertEqual(first,evaluate(**source))

    def test_rehashed_source_version_changes_cannot_keep_old_approval(self):
        approved=next(deepcopy(c['inputs']) for c in self.cases() if c['id']=='approved_review')
        valid=evaluate(**approved)
        self.assertEqual(valid['adjustment_status'],'approved_evidence')
        self.assertEqual(valid['approved_adjustment_quantity'],-4)
        for change in ('version','quantity','clock'):
            source=deepcopy(approved)
            if change=='version': source['system']['record_id']='stock-v2'
            elif change=='quantity':
                for row in source['counts']: row['quantity']=98
            else: source['counts'][1]['observed_at']='2026-02-01T00:08:00+00:00'
            # Hash the entire revised source again; semantic binding must still fail.
            digest(source)
            report=evaluate(**source)
            self.assertEqual(report['adjustment_status'],'not_assessable')
            self.assertIsNone(report['approved_adjustment_quantity'])
            self.assertIn('review_binding_mismatch',[f['reason'] for f in report['findings']])

    def test_metadata_rehash_does_not_authorize_invalid_count_scope_or_independence(self):
        for fault in ('scope','blind','frozen','identity','clock'):
            source=self.base()
            if fault=='scope': source['counts'][1]['warehouse_id']='other-warehouse'
            elif fault=='blind': source['counts'][1]['blind_count']=False
            elif fault=='frozen': source['manifest']['frozen']=False
            elif fault=='identity': source['counts'][1]['count_id']='count-1'
            else: source['counts'][1]['counted_at']='2026-02-01T00:30:00+00:00'
            digest(source)
            result=evaluate(**source)
            self.assertEqual(result['physical_status'],'not_assessable')
            self.assertIsNone(result['physical_quantity'])
            self.assertIsNone(result['variance_quantity'])
            self.assertIsNone(result['approved_adjustment_quantity'])

    def test_a_single_match_and_multiple_same_observer_matches_are_not_corroboration(self):
        source=self.base()
        for row in source['counts']: row.update(quantity=100,observer_id='same-observer')
        result=evaluate(**source)
        self.assertEqual(result['physical_status'],'recount_required')
        self.assertEqual(result['evidence_confidence'],'single_observer')
        self.assertIsNone(result['physical_quantity'])
        self.assertIsNone(result['variance_quantity'])

    def test_request_clock_errors_and_non_json_source_fail_closed(self):
        for clock in ('2026-02-01T00:20:00','invalid',None):
            with self.assertRaises(ValueError): evaluate(**dict(self.base(),evaluated_at=clock))
        source=self.base();source['counts'][0]['quantity']=object()
        result=evaluate(**source)
        self.assertEqual(result['physical_status'],'not_assessable')
        self.assertIsNone(result['physical_quantity'])
        self.assertIsNone(result['source_payload_sha256'])


if __name__=='__main__': unittest.main()
