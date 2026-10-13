"""Bounded offline actual-execution views and opt-in loopback journal boundaries."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from inventory_intelligence import execution
from inventory_intelligence.lab_api import create_app
from inventory_intelligence.lab_hosted import HostedLab


class ExecutionAPITests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.path=Path(self.directory.name)/'journal.sqlite'
        self.client=TestClient(HostedLab(create_app(journal_path=self.path),burst=100),base_url='http://127.0.0.1')
        self.digest=self.client.get('/api/execution').json()['archive_digest']

    def test_exact_actual_outcomes_supported_paired_comparisons_and_source_inspection(self):
        overview=self.client.get('/api/execution').json()
        self.assertEqual(len(overview['manual']),7);self.assertEqual(len(overview['comparisons']),12)
        cold=self.client.get('/api/execution/detail',params={'name':'cold-shortage','archive_digest':self.digest}).json()
        self.assertEqual(cold['summary']['proposals'],['18',None,None])
        self.assertEqual((cold['summary']['total_cost'],cold['summary']['terminal_backlog']),('776','9'))
        quiet=next(c for c in overview['comparisons'] if c['name']=='quiet')
        self.assertEqual([quiet['policies'][p]['total_cost'] for p in ('actual','do-nothing','fixed-18')],['330','160','760'])
        self.assertTrue(all(quiet['policies'][p]['immediate_fill'] is None for p in quiet['policies']))
        evidence=self.client.get('/api/execution/evidence',params={'name':'clean','day':0,'archive_digest':self.digest})
        self.assertEqual(evidence.status_code,200)
        self.assertEqual(evidence.json()['report']['result']['proposed_order_qty'],'12')
        self.assertLess(len(evidence.content),250*1024)
        self.assertEqual(self.client.get('/api/execution?unknown=true').status_code,422)
        self.assertEqual(self.client.get('/api/execution/detail?name=clean&name=zero').status_code,422)
        self.assertEqual(self.client.get('/api/execution/detail?name=clean&archive_digest='+'0'*64).status_code,409)
        self.assertEqual(self.client.get('/api/execution/evidence?name=clean&day=1').status_code,422)

    def test_opt_in_same_origin_exact_receipts_persist_and_preserve_history(self):
        body=dict(name='clean',day=0,archive_digest=self.digest)
        admitted=self.client.post('/api/execution/admit',json=body).json();identity=admitted['id']
        self.assertEqual(self.client.post('/api/execution/admit',json=body).json(),admitted)
        partial=dict(decision_id=identity,event_id='partial',kind='receipt',known_day='2026-03-09',quantity=5,archive_digest=self.digest)
        self.assertEqual(self.client.post('/api/execution/event',json=partial).status_code,200)
        reopened=TestClient(HostedLab(create_app(journal_path=self.path),burst=100),base_url='http://127.0.0.1')
        current=reopened.get('/api/execution/journal').json()
        self.assertEqual((current['received_pieces'],current['pending_pieces']),('5','7'))
        self.assertEqual(reopened.get('/api/execution/journal?as_of=2026-03-08').json()['received_pieces'],'0')
        self.assertEqual(self.client.post('/api/execution/event',json=partial|dict(quantity=8,event_id='bad')).status_code,422)
        self.assertEqual(self.client.post('/api/execution/event',json=partial|dict(quantity=1.5)).status_code,422)
        self.assertEqual(self.client.post('/api/execution/event',json=partial,headers={'Origin':'https://evil.example'}).status_code,403)
        self.assertEqual(self.client.post('/api/execution/admit',json=body|dict(archive_digest='0'*64)).status_code,409)
        self.assertEqual(reopened.get('/api/execution/journal').json(),current)
        default=TestClient(HostedLab(burst=100))
        self.assertFalse(default.get('/api/execution').json()['journal_enabled'])
        self.assertEqual(default.post('/api/execution/admit',json=body).status_code,404)
        self.assertEqual(default.post('/api/execution/event',json=partial).status_code,404)
        self.assertEqual(default.get('/api/execution/journal').json(),dict(enabled=False,synthetic_only=True))

    def test_corrupt_archive_and_frozen_controls_fail_closed_and_recover(self):
        original=Path(execution.__file__).parent
        archive=json.loads(gzip.decompress((original/'execution_evidence.json.gz').read_bytes()))
        controls=json.loads((original/'execution_controls.json').read_text())
        directory=Path(self.directory.name);path=directory/'execution_evidence.json.gz';control_path=directory/'execution_controls.json'
        control_path.write_text(json.dumps(controls))
        wrong=deepcopy(archive);wrong['manual']['clean']['days'][0]['end_stock']+=1
        path.write_bytes(gzip.compress(json.dumps(wrong).encode()))
        with patch.object(execution,'__file__',str(directory/'execution.py')):
            self.assertEqual(self.client.get('/api/execution').status_code,503)
            path.write_bytes(b'not a gzip archive')
            self.assertEqual(self.client.get('/api/execution').status_code,503)
            self.assertEqual(self.client.get('/health/ready').status_code,503)
            path.write_bytes((original/'execution_evidence.json.gz').read_bytes())
            self.assertEqual(self.client.get('/api/execution').status_code,200)
            controls['errata']['cold-shortage']['total_cost']=1
            control_path.write_text(json.dumps(controls))
            self.assertEqual(self.client.get('/api/execution').status_code,503)
