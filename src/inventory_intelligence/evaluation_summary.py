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
