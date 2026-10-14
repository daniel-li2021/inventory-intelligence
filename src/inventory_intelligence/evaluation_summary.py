"""Immutable offline summary of the fresh actual-planner baseline study."""
from pathlib import Path
import hashlib
import json

SUMMARY_SHA256 = 'a53d04e358ff7e2f86b4309fe44935c97d93541b5f7755a09ebcd383abe12f03'


def load_summary():
    data = Path(__file__).with_name('forecast_decision_summary.json').read_bytes()
    if hashlib.sha256(data).hexdigest() != SUMMARY_SHA256:
        raise ValueError('Evaluation summary binding changed')
    return json.loads(data)


FEEDBACK_SHA256 = '709d7474d46834a5fdb0da06381ce0d1d64030555cc6f9ce336c9b8b180e138b'


def load_feedback():
    from .copilot_planning import _validate
    data = Path(__file__).with_name('transfer_feedback_evidence.json').read_bytes()
    if hashlib.sha256(data).hexdigest() != FEEDBACK_SHA256:
        raise ValueError('Feedback evidence binding changed')
    result = json.loads(data)
    for report in result['reports'].values(): _validate(report)
    return result
