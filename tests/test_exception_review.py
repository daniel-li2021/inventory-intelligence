from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from inventory_intelligence.exception_review import ReviewJournal, finding_binding
from inventory_intelligence.insights import discover
from inventory_intelligence.product import load_catalog, archive_digest

ROOT = Path(__file__).resolve().parents[1]


class ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(ROOT / 'docs/review/dynamic-replay-v1.json.gz')
        cls.cutoff = '2026-04-06'
        cls.finding = discover(cls.catalog, cls.cutoff)['findings'][0]

    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'reviews.sqlite'
        self.journal = ReviewJournal(self.path)
        self.request = dict(cutoff=self.cutoff, finding_id=self.finding['id'], event_id='review:1',
                            status='acknowledged', note='Inspect exact contributing stock and known inbound.',
                            reviewed_at='2026-04-06T08:00:00+00:00',
                            calculation_digest=archive_digest(self.finding, False))

    def test_bound_state_reopen_retry_and_resolution_never_change_facts(self):
        before = deepcopy(discover(self.catalog, self.cutoff))
        event = self.journal.append(self.catalog, **self.request)
        self.assertEqual(event, ReviewJournal(self.path).append(self.catalog, **self.request))
        self.assertEqual(event['observation_id'], self.finding['observation_id'])
        self.journal.append(self.catalog, **(self.request | dict(event_id='review:2', status='resolved', reviewed_at='2026-04-06T09:00:00+00:00')))
        self.journal.append(self.catalog, **(self.request | dict(event_id='review:3', status='investigating', reviewed_at='2026-04-06T10:00:00+00:00')))
        snapshot = ReviewJournal(self.path).snapshot(self.catalog, self.cutoff)
        self.assertEqual([e['status'] for e in snapshot['events']], ['acknowledged', 'resolved', 'investigating'])
        self.assertEqual(snapshot['reviews'][0]['status'], 'investigating')
        self.assertEqual(discover(self.catalog, self.cutoff), before)
        self.assertEqual(self.journal.snapshot(self.catalog, '2026-04-13')['events'], [])
        self.assertEqual(self.journal.snapshot(self.catalog, '2026-04-13')['retained_event_count'], 3)

    def test_changed_or_unknown_evidence_and_bad_fields_leave_empty_history(self):
        for change in (dict(calculation_digest='0' * 64), dict(finding_id='unknown'),
                       dict(status='approved'), dict(note=' '), dict(note='a' * 501),
                       dict(event_id='bad/id'), dict(reviewed_at='2026-04-05T08:00:00+00:00'),
                       dict(reviewed_at='2026-04-06T08:00:00'), dict(reviewed_at=None)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.journal.append(self.catalog, **(self.request | change))
        self.assertEqual(self.journal.snapshot(self.catalog, self.cutoff)['events'], [])
        with self.assertRaises(ValueError):
            finding_binding(self.catalog, self.cutoff, 'missing')

    def test_conflicting_identity_backdate_immutability_and_transaction_rollback(self):
        first = self.journal.append(self.catalog, **self.request)
        for change in (dict(note='Conflicting content'), dict(event_id='review:2', reviewed_at='2026-04-06T07:30:00+00:00')):
            with self.assertRaises(ValueError):
                self.journal.append(self.catalog, **(self.request | change))
        with sqlite3.connect(self.path) as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE exception_reviews SET reviewed_at='wrong'")
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute('DELETE FROM exception_reviews')
            conn.executescript("CREATE TRIGGER late_failure BEFORE INSERT ON exception_reviews BEGIN SELECT RAISE(ABORT,'late failure'); END;")
        with self.assertRaises(sqlite3.IntegrityError):
            self.journal.append(self.catalog, **(self.request | dict(event_id='review:2')))
        self.assertEqual(self.journal.snapshot(self.catalog, self.cutoff)['events'], [first])

    def test_concurrent_duplicate_admission_and_bound(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            rows = list(pool.map(lambda _: ReviewJournal(self.path).append(self.catalog, **self.request), range(4)))
        self.assertTrue(all(row == rows[0] for row in rows))
        self.assertEqual(len(self.journal.snapshot(self.catalog, self.cutoff)['events']), 1)
        with patch('inventory_intelligence.exception_review.MAX_EVENTS', 1), self.assertRaises(ValueError):
            self.journal.append(self.catalog, **(self.request | dict(event_id='review:2')))
        self.assertEqual(len(self.journal.snapshot(self.catalog, self.cutoff)['events']), 1)


if __name__ == '__main__':
    unittest.main()
