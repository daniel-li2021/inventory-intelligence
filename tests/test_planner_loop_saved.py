"""Saved-only independent decision-quality audit and coherent corruption controls."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from inventory_intelligence.planner_loop import digest
from inventory_intelligence.planner_loop_audit import audit_archive, audit_case


class PlannerLoopSavedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[1]
        cls.archive=json.loads(gzip.decompress((root/'docs/review/planner-loop-v1.json.gz').read_bytes()))
        cls.manual=json.loads((root/'docs/examples/planner-loop-manual-v1.json').read_text())|json.loads((root/'docs/examples/planner-loop-errata-v1.json').read_text())
        cls.stress=json.loads((root/'docs/examples/planner-quality-stress-v1.json').read_text())

    def test_complete_grid_without_database_planner_forecast_or_simulation(self):
        with patch('psycopg.connect',side_effect=AssertionError('No DB in saved audit')), \
             patch('inventory_intelligence.replenishment.project',side_effect=AssertionError('No implementation calculator')), \
             patch('inventory_intelligence.forecasting.forecast',side_effect=AssertionError('No forecast')), \
             patch('inventory_intelligence.decision.simulate',side_effect=AssertionError('No periodic simulator')):
            self.assertEqual(audit_archive(self.archive,self.manual,self.stress),
                dict(status='pass',manual_controls=7,paired_traces=12,paired_policy_cells=36,reviews=129))

    def test_missing_policy_changed_trace_and_rehashed_future_or_history_reject(self):
        changed=deepcopy(self.archive);del changed['stress']['quiet']['do-nothing']
        with self.assertRaises(ValueError):audit_archive(changed,self.manual,self.stress)
        changed=deepcopy(self.archive);changed['stress']['rising']['actual']['demand'][0]+=1
        with self.assertRaises(ValueError):audit_archive(changed,self.manual,self.stress)
        for mutation in ('future','offset-future','accepted','availability','key'):
            case=deepcopy(self.archive['manual']['clean']);source=case['sources'][0]
            if mutation=='future':source['planning']['order_versions'][0]['observed_at']='2099-01-01T00:00:00+00:00'
            elif mutation=='offset-future':source['planning']['order_versions'][0]['observed_at']='2026-03-07T01:00:00-08:00'
            elif mutation=='accepted':source['planning']['order_versions'][0]['accepted_qty']+=1
            elif mutation=='availability':source['planning']['day_observations'][0]['availability']='stockout'
            else:source['planning']['order_versions'][0]['sku_id']='other'
            case['reviews'][0]['source_digest']=digest(source)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):audit_case(case)
