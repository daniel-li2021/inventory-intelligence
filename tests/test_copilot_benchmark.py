"""The benchmark grader must reject wrong routes, citations, quantities and policy."""
from copy import deepcopy
import unittest

from scripts.copilot_benchmark import expected_citations, grade, summary
from tests.test_copilot import report


class BenchmarkGrader(unittest.TestCase):
    def test_exact_evidence_and_independent_negative_controls(self):
        inputs = {'combined':report(dirty=True)}
        case = dict(id='F01',source='combined',expected_intent='finding',
                    finding='manual-mismatch',status='answered')
        refs = expected_citations(case,inputs)
        answer = dict(intent='finding',status='answered',citations=deepcopy(refs),
                      summary=f"Snapshot 26 minus ledger expectation 25 equals +1 pieces [{refs[1]['id']}].",
                      proposed_order_qty=None,limitations=[])
        self.assertTrue(all(grade(case,inputs,0,answer,'').values()))
        for metric, mutate in (
            ('routing',lambda a:a.update(intent='readiness')),
            ('numeric_fidelity',lambda a:a['citations'][1]['data'].update(expected_qty=25.0)),
            ('numeric_fidelity',lambda a:a.update(summary='Snapshot 0 minus ledger expectation 0 equals 0 pieces.')),
            ('evidence_selection',lambda a:a['citations'].pop()),
            ('citations',lambda a:a['citations'][1].update(source='fabricated')),
            ('readiness_refusal',lambda a:a.update(proposed_order_qty=12)),
            ('status_exit',lambda a:a.update(status='refused'))):
            wrong = deepcopy(answer)
            mutate(wrong)
            self.assertFalse(grade(case,inputs,0,wrong,'')[metric],metric)
        # JSON key order must not affect exact-number checking.
        reordered = deepcopy(answer)
        reordered['citations'][1]['data'] = dict(reversed(list(refs[1]['data'].items())))
        self.assertTrue(grade(case,inputs,0,reordered,'')['numeric_fidelity'])
        invalid = dict(error='invalid evidence')
        self.assertTrue(grade(invalid,{},2,None,'invalid evidence')['validation'])
        self.assertFalse(grade(invalid,{},2,{},'invalid evidence')['validation'])

    def test_unknown_usage_is_not_a_zero_or_success(self):
        rows = [dict(case=dict(id='X',expected_intent='unsupported'),checks=dict(routing=False,readiness_refusal=True,status_exit=True),latency_ms=12,
                     answer=dict(routing=dict(source='fallback')),call_accounting='measured',
                     telemetry=dict(attempted_calls=1,api_latency_ms=10,
                                    usage=dict(input_tokens=30,output_tokens=None,total_tokens=None,
                                               cached_tokens=0,reasoning_tokens=None)))]
        result = summary(rows)
        self.assertEqual(result['passed'],0)
        self.assertEqual(result['attempted_api_calls'],1)
        self.assertIsNone(result['usage']['total_tokens']['measured_total'])
        self.assertEqual(result['usage']['total_tokens']['unknown_calls'],1)
        self.assertEqual(result['usage']['cached_tokens']['measured_total'],0)


if __name__=='__main__':
    unittest.main()
