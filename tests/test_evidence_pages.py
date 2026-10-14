"""Real PostgreSQL pages above legacy aggregate caps, with strict inspection boundaries."""
import json
import os
from pathlib import Path
import unittest
from uuid import uuid4
import psycopg
from psycopg.types.json import Jsonb
from inventory_intelligence.evidence_pages import read_page
from inventory_intelligence.copilot import load_run
from inventory_intelligence.copilot_planning import load_planning_run


class EvidencePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owner=psycopg.connect(os.environ['TEST_DATABASE_URL'],autocommit=True)
        cls.runner=psycopg.connect(os.environ['DATABASE_URL'],autocommit=True)
        cls.reliability=str(uuid4());cls.planning=str(uuid4());cls.huge=str(uuid4())
        cls.owner.execute("INSERT INTO reliability.runs VALUES (%s,'1','inspection-test','synthetic-ledger','synthetic-count','2026-06-01T00:00Z','2026-06-01T00:00Z','fail')",(cls.reliability,))
        for i in range(1,6):cls.owner.execute('INSERT INTO reliability.check_results VALUES (%s,%s,%s)',(cls.reliability,f'R00{i}','fail' if i==1 else 'pass'))
        cls.owner.execute("""INSERT INTO reliability.findings SELECT %s, 'finding-'||lpad(i::text,4,'0'),'R001','error','quantity_mismatch','a','b',
            '["source"]'::jsonb,1,2,1,jsonb_build_object('record',repeat('x',30000)) FROM generate_series(0,99)i""",(cls.reliability,))
        cls.owner.execute("""INSERT INTO planning.runs VALUES (%s,'planning-v1','inspection-test','baselines-v1','backtest',now(),'synthetic-input','assessable','{}',
            jsonb_build_object('candidates',jsonb_build_array(jsonb_build_object('training',jsonb_build_object('days',
            (SELECT jsonb_agg(jsonb_build_object('quantity',i,'padding',repeat('x',1000)) ORDER BY i) FROM generate_series(0,17999)i))))))""",(cls.planning,))
        cls.owner.execute("INSERT INTO planning.runs VALUES (%s,'planning-v1','inspection-test','baselines-v1','replenishment',now(),'input','assessable','{}',%s)",(cls.huge,Jsonb(dict(projection=[dict(evidence='x'*300000)]))))

    @classmethod
    def tearDownClass(cls):cls.owner.close();cls.runner.close()

    def test_dense_reliability_pages_keep_original_reader_gate(self):
        with self.assertRaises(ValueError):load_run(self.runner,self.reliability)
        first=read_page(self.runner,self.reliability,'reliability','findings',page_size=2)
        self.assertGreater(first['metadata']['report_bytes'],2*1024*1024)
        self.assertEqual(first['total_rows'],100)
        self.assertEqual([r['finding_id'] for r in first['rows']],['finding-0000','finding-0001'])
        second=read_page(self.runner,self.reliability,'reliability','findings',page=2,page_size=2,expected_binding=first['binding'])
        self.assertEqual(second['binding'],first['binding'])
        self.assertEqual(second['rows'][0]['finding_id'],'finding-0002')
        self.assertEqual(second['rows'][0]['observed_qty'],2)
        self.assertEqual(len(second['rows'][0]['evidence']['record']),30000)
        with self.assertRaises(ValueError):read_page(self.runner,self.reliability,'reliability','findings',page_size=100)
        with self.assertRaises(ValueError):read_page(self.runner,self.reliability,'reliability','findings',expected_binding='0'*64)

    def test_long_backtest_subsection_without_full_payload(self):
        with self.assertRaises(ValueError):load_planning_run(self.runner,self.planning)
        first=read_page(self.runner,self.planning,'planning','candidate_training',candidate=0,page_size=5)
        self.assertGreater(first['metadata']['report_bytes'],16*1024*1024)
        self.assertEqual(first['total_rows'],18000)
        self.assertEqual([r['ordinal'] for r in first['rows']],list(range(5)))
        self.assertEqual(first['rows'][4]['record']['quantity'],4)
        last=read_page(self.runner,self.planning,'planning','candidate_training',candidate=0,page=3600,page_size=5,expected_binding=first['binding'])
        self.assertIsNone(last['next_page'])
        self.assertEqual(last['rows'][-1]['ordinal'],17999)
        self.assertIn('inspection_only',last['semantic_validation'])
        self.assertLess(len(json.dumps(last)),256*1024)

    def test_negative_boundaries_and_source_immutability(self):
        for kwargs in (dict(page=True),dict(page_size=0),dict(page_size=101),dict(page=1001),dict(candidate=0)):
            with self.assertRaises(ValueError):read_page(self.runner,self.reliability,'reliability','findings',**kwargs)
        with self.assertRaises(ValueError):read_page(self.runner,self.huge,'planning','projection',page_size=1)
        with self.assertRaises(ValueError):read_page(self.runner,self.planning,'planning','projection')
        with self.assertRaises(ValueError):read_page(self.runner,self.planning,'planning','candidate_training')
        with self.assertRaises(ValueError):read_page(self.owner,self.reliability,'reliability','findings')
        with self.assertRaises(psycopg.Error):self.runner.execute('DELETE FROM planning.runs WHERE run_id=%s',(self.planning,))
        self.assertEqual(self.owner.execute('SELECT count(*) FROM reliability.findings WHERE run_id=%s',(self.reliability,)).fetchone()[0],100)

    def test_binding_rejects_equal_length_section_and_candidate_changes(self):
        run=str(uuid4())
        result=dict(projection=[dict(quantity=1),dict(quantity=2)],
                    training=dict(days=[dict(quantity=3),dict(quantity=4)]),
                    candidates=[dict(training=dict(days=[dict(quantity=5),dict(quantity=6)])),
                                dict(training=dict(days=[dict(quantity=7),dict(quantity=8)]))])
        self.owner.execute("INSERT INTO planning.runs VALUES (%s,'planning-v1','inspection-test','baselines-v1','backtest',now(),'input','assessable','{}',%s)",(run,Jsonb(result)))
        first=read_page(self.runner,run,'planning','projection',page_size=1)
        second=read_page(self.runner,run,'planning','projection',page=2,page_size=1,expected_binding=first['binding'])
        self.assertEqual(second['rows'],[dict(ordinal=1,record=dict(quantity=2))])
        with self.assertRaisesRegex(ValueError,'binding changed'):
            read_page(self.runner,run,'planning','training',expected_binding=first['binding'])
        candidate=read_page(self.runner,run,'planning','candidate_training',candidate=0)
        with self.assertRaisesRegex(ValueError,'binding changed'):
            read_page(self.runner,run,'planning','candidate_training',candidate=1,expected_binding=candidate['binding'])
        self.assertEqual(self.owner.execute('SELECT result FROM planning.runs WHERE run_id=%s',(run,)).fetchone()[0],result)


if __name__=='__main__':unittest.main()
