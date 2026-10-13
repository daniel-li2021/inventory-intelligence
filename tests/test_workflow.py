"""Frozen durable receipt controls against independently audited saved actual reports."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from inventory_intelligence.workflow import Journal


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        archive=json.loads(gzip.decompress((Path(__file__).resolve().parents[1]/'docs/review/planner-loop-v1.json.gz').read_bytes()))
        cls.clean=archive['manual']['clean'];cls.blocked=archive['manual']['missing'];cls.zero=archive['manual']['zero']

    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.path=Path(directory.name)/'journal.sqlite';self.journal=Journal(self.path)

    def admit(self):return self.journal.admit(self.clean,0)['id']

    def test_partial_receipt_eta_history_reopen_and_exact_conservation(self):
        identity=self.admit()
        self.assertEqual(self.journal.snapshot('2026-03-08')['pending_pieces'],12)
        self.journal.record(decision_id=identity,event_id='partial',kind='receipt',known_day='2026-03-09',quantity=5)
        self.journal.record(decision_id=identity,event_id='notice',kind='eta',known_day='2026-03-10',eta='2026-03-11')
        again=Journal(self.path);again.admit(self.clean,0)
        self.assertEqual((again.snapshot('2026-03-09')['received_pieces'],again.snapshot('2026-03-09')['pending_pieces']),(5,7))
        self.assertEqual(again.inbound('2026-03-09')[0]['arrival_day'],'2026-03-09')
        self.assertEqual(again.inbound('2026-03-10')[0]['arrival_day'],'2026-03-11')
        event=dict(decision_id=identity,event_id='final',kind='receipt',known_day='2026-03-11',quantity=7)
        again.record(**event);again.record(**event)
        snapshot=again.snapshot('2026-03-11')
        self.assertEqual((snapshot['received_pieces'],snapshot['pending_pieces'],len(snapshot['events'])),(12,0,4))
        self.assertEqual(again.inbound('2026-03-11'),[])
        self.assertEqual(again.snapshot('2026-03-08')['received_pieces'],0)

    def test_rejected_mutations_preserve_last_good_journal(self):
        identity=self.admit();self.journal.record(decision_id=identity,event_id='partial',kind='receipt',known_day='2026-03-09',quantity=5)
        before=self.journal.snapshot('2026-03-20')
        base=dict(decision_id=identity,event_id='bad',kind='receipt',known_day='2026-03-10',quantity=8)
        for event in (base,base|dict(quantity=0),base|dict(quantity=-1),base|dict(quantity=1.5),base|dict(quantity=True),
            base|dict(quantity=1,known_day='2026-03-08'),base|dict(decision_id='unknown'),
            base|dict(event_id='partial',quantity=4),
            dict(decision_id=identity,event_id='notice',kind='eta',known_day='2026-03-08',eta='2026-03-11'),
            dict(decision_id=identity,event_id='notice',kind='eta',known_day='2026-03-10',eta='2026-03-09')):
            with self.subTest(event=event),self.assertRaises(ValueError):self.journal.record(**event)
            self.assertEqual(self.journal.snapshot('2026-03-20'),before)

    def test_blocked_zero_and_corrupt_report_cannot_create_an_order(self):
        for case in (self.blocked,self.zero):
            decision=self.journal.admit(case,0)
            with self.assertRaises(ValueError):self.journal.record(decision_id=decision['id'],event_id='receipt',
                kind='receipt',known_day='2026-03-09',quantity=1)
        self.assertEqual(self.journal.snapshot('2026-03-20')['orders'],[])
        changed=deepcopy(self.clean);changed['reviews'][0]['decision']['quantity']=18
        with self.assertRaises(ValueError):self.journal.admit(changed,0)
        self.assertEqual(self.journal.snapshot('2026-03-20')['orders'],[])

    def test_transaction_failure_and_external_update_delete_rejected(self):
        with sqlite3.connect(self.path) as conn:
            conn.execute("CREATE TRIGGER fail_order BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT,'injected'); END")
        with self.assertRaises(sqlite3.IntegrityError):self.admit()
        self.assertEqual(self.journal.snapshot('2026-03-20')['decisions'],[])
        with sqlite3.connect(self.path) as conn:conn.execute('DROP TRIGGER fail_order')
        self.admit()
        for query in ('UPDATE decisions SET binding=\'wrong\'','DELETE FROM decisions','DELETE FROM events','UPDATE events SET kind=\'eta\''):
            with sqlite3.connect(self.path) as conn,self.assertRaises(sqlite3.IntegrityError):conn.execute(query)
        self.assertEqual(len(self.journal.snapshot('2026-03-20')['orders']),1)

    def test_concurrent_partial_receipts_cannot_exceed_committed_pieces(self):
        identity=self.admit()
        def receive(i):
            try:return Journal(self.path).record(decision_id=identity,event_id=f'parallel-{i}',
                kind='receipt',known_day='2026-03-09',quantity=7)
            except ValueError:return None
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(receive,range(2)))
        self.assertEqual(sum(r is not None for r in results),1)
        self.assertEqual(self.journal.snapshot('2026-03-09')['received_pieces'],7)
