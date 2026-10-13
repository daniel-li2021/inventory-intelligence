"""Bounded offline views of actual synthetic planner execution and paired outcomes."""
import gzip
import hashlib
import json
from pathlib import Path
from threading import Lock

from .planner_loop_audit import audit_archive
from .product import _wire

_lock=Lock()
_cache=None
_identity=None


def load_execution():
    global _cache, _identity
    path=Path(__file__).with_name('execution_evidence.json.gz')
    controls_path=path.with_name('execution_controls.json')
    def identity():
        return tuple((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
                     for s in (path.stat(),controls_path.stat()))
    with _lock:
        current=identity()
        if _cache is None or current!=_identity:
            if path.stat().st_size>2*1024*1024 or controls_path.stat().st_size>100*1024:
                raise ValueError('Execution archive exceeds supported envelope')
            with gzip.open(path,'rb') as stream:raw=stream.read(32*1024*1024+1)
            if len(raw)>32*1024*1024:raise ValueError('Execution archive exceeds expanded envelope')
            archive=json.loads(raw);controls=json.loads(controls_path.read_text())
            for key,name in (('manual','planner-loop-manual-v1.json'),('errata','planner-loop-errata-v1.json'),
                             ('stress','planner-quality-stress-v1.json')):
                control_bytes=(json.dumps(controls[key],indent=2,sort_keys=True)+'\n').encode()
                if hashlib.sha256(control_bytes).hexdigest()!=archive['source_hashes']['docs/examples/'+name]:
                    raise ValueError('Packaged controls differ from frozen source')
            audit_archive(archive,controls['manual']|controls['errata'],controls['stress'])
            if identity()!=current:raise ValueError('Execution archive changed during validation')
            _cache=(archive,hashlib.sha256(raw).hexdigest());_identity=current
        return _cache


def overview(loaded=None):
    archive,digest=load_execution() if loaded is None else loaded
    return dict(version='planner-execution-view-v1',synthetic_only=True,archive_digest=digest,
        start='2026-03-07',end='2026-03-20',score_days=9,closure_days=5,
        code_commit=archive['code_commit'],runtime=archive['runtime'],
        manual=[dict(name=name,summary=_wire(case['summary'])) for name,case in archive['manual'].items()],
        comparisons=[dict(name=name,policies={policy:_wire(case['summary']) for policy,case in cells.items()})
                     for name,cells in archive['stress'].items()],
        limitations=['Synthetic stress controls; no universal policy winner or commercial benefit',
            'Original cold-shortage oracle rejected; explicit arithmetic erratum yields 18 pieces',
            'Stockout training/overdue commitments still block; journal does not waive gates',
            'Public runtime, PostgreSQL17 reference and authenticated operational execution unverified'])


def selected(name,loaded=None):
    archive,digest=load_execution() if loaded is None else loaded
    if name not in archive['manual']:raise ValueError('Unknown execution control')
    case=archive['manual'][name]
    return dict(name=name,archive_digest=digest,summary=_wire(case['summary']),days=_wire(case['days']),
        initial_purchase_cost=str(case['initial_stock']*2),
        reviews=[dict(day=r['day'],origin=r['report']['context']['origin'],status=r['report']['status'],
            reasons=r['report']['result']['reasons'],proposed_order_qty=_wire(r['decision']['proposal']),
            report_id=r['report']['run_id'],input_digest=r['report']['input_digest'],source_digest=r['source_digest'])
            for r in case['reviews']])


def evidence(name,day,loaded=None):
    archive,digest=load_execution() if loaded is None else loaded
    if name not in archive['manual'] or type(day) is not int or day not in (0,3,6):
        raise ValueError('Unknown execution review')
    case=archive['manual'][name];review=case['reviews'][day//3]
    return dict(name=name,day=day,archive_digest=digest,report=_wire(review['report']),
                reliability=_wire(review['reliability']),source_digest=review['source_digest'])
