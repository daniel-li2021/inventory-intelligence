"""Export the bounded synthetic Lab replay from a fresh disposable database.

Run after schema bootstrap; never point this at an existing fixture database.
The loader refuses existing fixture identities instead of updating inputs.
"""
import argparse
from datetime import timedelta
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg
from inventory_intelligence.demand import midnight
from inventory_intelligence.lab import archive_digest, validate_evidence
from inventory_intelligence.planning_runs import exact_json, run_forecast
from inventory_intelligence.reliability import run_checks
from inventory_intelligence.replenishment import run_plan
from synthetic.demand import END
from synthetic.planning_demo import load_inputs


def export(owner, runner):
    inputs = load_inputs(owner)
    cutoff = midnight(END)
    reliability = run_checks(runner, ledger_batch_id='planning-demo:ledger',
        snapshot_batch_id='planning-demo:snapshot', as_of=cutoff,
        evaluated_at=cutoff, code_version='decision-lab-export-v1')
    options = dict(batch_id=inputs['batch_id'], sku_id='planning-demo:tee-m',
        warehouse_id='planning-demo:harbor', start_day=END-timedelta(days=28),
        origin_day=END, method='mean', code_version='decision-lab-export-v1')
    forecast = run_forecast(runner, **options, horizon=28)
    plans = {case: run_plan(runner, **options,
        reliability_run_id=reliability['run_id'],
        supply_batch_id='planning-demo:supply:'+label)
        for case, label in (('clean', 'complete'), ('incomplete_supply', 'incomplete'))}
    evidence = exact_json(dict(contract_version='decision-lab-evidence-v1',
        synthetic=True, business_data='synthetic only', reliability=reliability,
        forecast=forecast, plans=plans, future_demand=dict(
            origin_day=END, quantities=[4]*28,
            source='declared synthetic constant demand', id='decision-lab:future-constant-v1')))
    evidence['digest'] = archive_digest(evidence)
    validate_evidence(evidence)
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] /
                        'src/inventory_intelligence/lab_evidence.json')
    args = parser.parse_args()
    with psycopg.connect(os.environ['FIXTURE_DATABASE_URL'], autocommit=True) as owner, \
         psycopg.connect(os.environ['DATABASE_URL'], autocommit=True) as runner:
        evidence = export(owner, runner)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(f"Exported synthetic replay {evidence['digest']} to {args.output}")


if __name__ == '__main__':
    main()
