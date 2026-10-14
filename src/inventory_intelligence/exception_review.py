"""Append-only local synthetic review state; reviews never change discovered facts."""
from contextlib import contextmanager
from pathlib import Path
import json
import re
import sqlite3

from .insights import discover
from .product import archive_digest, validate_catalog, _instant

VERSION = 'exception-review-v1'
MAX_EVENTS = 256


def finding_binding(catalog, cutoff, finding_id):
    validate_catalog(catalog)
    findings = discover(catalog, cutoff)['findings']
    selected = [f for f in findings if f['id'] == finding_id]
    if len(selected) != 1:
        raise ValueError('Unknown finding at selected cutoff')
    finding = selected[0]
    return dict(finding_id=finding_id, observation_id=finding['observation_id'],
                calculation_digest=archive_digest(finding, False),
                archive_digest=catalog['digest'], cutoff=finding['as_of'],
                known_at=finding['known_at'], references=finding['references'])


class ReviewJournal:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS exception_reviews (
                    sequence INTEGER PRIMARY KEY, event_id TEXT NOT NULL UNIQUE,
                    observation_id TEXT NOT NULL, reviewed_at TEXT NOT NULL,
                    payload TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS exception_reviews_no_update
                    BEFORE UPDATE ON exception_reviews BEGIN
                    SELECT RAISE(ABORT, 'immutable exception review'); END;
                CREATE TRIGGER IF NOT EXISTS exception_reviews_no_delete
                    BEFORE DELETE ON exception_reviews BEGIN
                    SELECT RAISE(ABORT, 'immutable exception review'); END;
            ''')

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.path, timeout=5)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def append(self, catalog, *, cutoff, finding_id, event_id, status, note,
               reviewed_at, calculation_digest):
        binding = finding_binding(catalog, cutoff, finding_id)
        if calculation_digest != binding['calculation_digest']:
            raise ValueError('Finding changed; inspect current evidence before reviewing')
        if not isinstance(event_id, str) or not re.fullmatch(r'[A-Za-z0-9:_-]{1,100}', event_id):
            raise ValueError('Bounded event identity required')
        if status not in ('acknowledged', 'investigating', 'resolved'):
            raise ValueError('Unsupported review state')
        if not isinstance(note, str) or not note.strip() or len(note) > 500:
            raise ValueError('Review note must contain 1–500 characters')
        if not isinstance(reviewed_at, str):
            raise ValueError('Aware UTC review timestamp required')
        moment = _instant(reviewed_at)
        if moment < _instant(binding['known_at']):
            raise ValueError('Review precedes known finding')
        payload = dict(contract_version=VERSION, synthetic=True, event_id=event_id,
                       status=status, note=note, reviewed_at=moment.isoformat(), **binding)
        encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        with self._connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            prior = conn.execute('SELECT payload FROM exception_reviews WHERE event_id=?', (event_id,)).fetchone()
            if prior:
                if prior[0] != encoded:
                    raise ValueError('Conflicting review event identity')
                return json.loads(prior[0])
            previous = conn.execute('SELECT reviewed_at FROM exception_reviews WHERE observation_id=? ORDER BY sequence DESC LIMIT 1',
                                    (binding['observation_id'],)).fetchone()
            if previous and moment < _instant(previous[0]):
                raise ValueError('Backdated review event')
            if conn.execute('SELECT count(*) FROM exception_reviews').fetchone()[0] >= MAX_EVENTS:
                raise ValueError('Synthetic review event limit reached')
            conn.execute('INSERT INTO exception_reviews(event_id,observation_id,reviewed_at,payload) VALUES (?,?,?,?)',
                         (event_id, binding['observation_id'], payload['reviewed_at'], encoded))
        return payload

    def snapshot(self, catalog, cutoff=None):
        validate_catalog(catalog)
        discovery = discover(catalog, cutoff)
        current = {f['observation_id']: f for f in discovery['findings']}
        with self._connection() as conn:
            events = [json.loads(row[0]) for row in conn.execute('SELECT payload FROM exception_reviews ORDER BY sequence')]
        selected = [e for e in events if e['observation_id'] in current and e['archive_digest'] == catalog['digest']]
        if len(events) > MAX_EVENTS:
            raise ValueError('Synthetic review journal exceeds event limit')
        for event in selected:
            finding = current[event['observation_id']]
            if (event['calculation_digest'] != archive_digest(finding, False) or
                event['finding_id'] != finding['id'] or event['references'] != finding['references']):
                raise ValueError('Inconsistent stored review binding')
        latest = {e['finding_id']: e for e in selected}
        return dict(contract_version=VERSION, synthetic=True, archive_digest=catalog['digest'],
                    cutoff=discovery['cutoff'], reviews=list(latest.values()), events=selected,
                    retained_event_count=len(events),
                    boundary='Local synthetic review notes only; resolved does not suppress facts, waive evidence gates or execute inventory actions.')
