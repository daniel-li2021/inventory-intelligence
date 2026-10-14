#!/usr/bin/env python3
"""Execute once in a disposable database, or audit saved bytes entirely offline."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess

from inventory_intelligence.forecast_decision_study import run, audit

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/'docs/examples/forecast-decision-study-v1.json'
SOURCES=('docs/examples/forecast-decision-study-v1.json','src/inventory_intelligence/forecast_decision_study.py',
         'src/inventory_intelligence/planner_loop.py','src/inventory_intelligence/planner_loop_audit.py',
         'src/inventory_intelligence/forecasting.py','src/inventory_intelligence/replenishment.py',
         'src/inventory_intelligence/reliability.py','src/inventory_intelligence/demand.py',
         'src/inventory_intelligence/planning_runs.py','src/inventory_intelligence/copilot_planning.py',
         'sql/schema.sql','sql/planning_schema.sql','sql/views.sql','sql/checks.sql',
         'scripts/forecast_decision_study.py')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--audit',action='store_true');args=parser.parse_args()
    protocol=json.loads(PROTOCOL.read_text())
    if args.audit:
        report=json.loads(gzip.decompress(args.output.read_bytes()))
    else:
        if args.output.exists():raise ValueError('Refuse to overwrite consumed study')
        import psycopg
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        with psycopg.connect(os.environ['TEST_DATABASE_URL'],autocommit=True) as owner, psycopg.connect(os.environ['DATABASE_URL'],autocommit=True) as runner:
            report=run(owner,runner,protocol,code_version='forecast-decision-study-v1')
        report['source_hashes']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}
        report['parent_commit']=commit
        report['source_binding']='Exact working source hashes; parent commit is ancestry, not claim these files were committed there'
        args.output.parent.mkdir(parents=True,exist_ok=True)
        raw=json.dumps(report,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        with args.output.open('xb') as f:f.write(gzip.compress(raw,mtime=0))
    print(json.dumps(audit(report,protocol)|dict(artifact_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
        current_source_drift=[p for p,h in report['source_hashes'].items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h],
        conclusions=report['conclusions']),sort_keys=True))


if __name__=='__main__':main()
