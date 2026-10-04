"""Supplemental synthetic reader fixtures at actual JSON-validation boundaries."""
from copy import deepcopy
import json,time
from pathlib import Path
from uuid import uuid4
from psycopg.types.json import Jsonb
from scripts.engineering_benchmark import connect,history
from inventory_intelligence.copilot import load_run,MAX_BYTES
from inventory_intelligence.copilot_planning import load_planning_run,MAX_PLANNING_BYTES

output=Path(__file__).parent
records=[]
with connect('TEST_DATABASE_URL') as owner,connect('DATABASE_URL') as runner:
 for name,loader,limit in (('reliability',load_run,MAX_BYTES),('planning',load_planning_run,MAX_PLANNING_BYTES)):
  if name=='reliability':
   original=owner.execute("SELECT run_id FROM reliability.runs WHERE code_version='synthetic-reader-v1' AND (SELECT count(*) FROM reliability.findings f WHERE f.run_id=reliability.runs.run_id)=1 LIMIT 1").fetchone()[0]
  else:
   original=owner.execute("SELECT run_id FROM planning.runs WHERE code_version='synthetic-reader-v1' LIMIT 1").fetchone()[0]
  for offset in (-1,0,1):
   run=str(uuid4())
   with owner.transaction():
    if name=='reliability':
     owner.execute("INSERT INTO reliability.runs SELECT %s,contract_version,code_version,ledger_batch_id,snapshot_batch_id,as_of,evaluated_at,overall_status FROM reliability.runs WHERE run_id=%s",(run,original))
     owner.execute("INSERT INTO reliability.check_results SELECT %s,rule_id,status FROM reliability.check_results WHERE run_id=%s",(run,original))
     owner.execute("INSERT INTO reliability.findings SELECT %s,finding_id,rule_id,severity,reason,sku_id,warehouse_id,source_row_ids,expected_qty,observed_qty,delta_qty,%s FROM reliability.findings WHERE run_id=%s",(run,Jsonb(dict(padding='')),original))
    else:
     owner.execute("INSERT INTO planning.runs SELECT %s,contract_version,code_version,model_version,kind,created_at,input_digest,status,context,result || %s FROM planning.runs WHERE run_id=%s",(run,Jsonb(dict(padding='')),original))
   baseline=loader(runner,run)
   base_bytes=len(json.dumps(baseline,allow_nan=False).encode())
   padding='x'*(limit+offset-base_bytes)
   if name=='reliability':
    owner.execute("UPDATE reliability.findings SET evidence=%s WHERE run_id=%s",(Jsonb(dict(padding=padding)),run))
    baseline['findings'][0]['evidence']['padding']=padding
    size_sql='SELECT sum(octet_length(row_to_json(f)::text)) FROM reliability.findings f WHERE run_id=%s'
   else:
    owner.execute("UPDATE planning.runs SET result=result || %s WHERE run_id=%s",(Jsonb(dict(padding=padding)),run))
    baseline['result']['padding']=padding
    size_sql='SELECT octet_length(row_to_json(r)::text) FROM planning.runs r WHERE run_id=%s'
   actual=len(json.dumps(baseline,allow_nan=False).encode())
   assert actual==limit+offset
   before=history(owner)
   spec=dict(case=f'{name}-json-{offset}',run_id=run,accounting='actual loader JSON validation representation',
             validation_json_bytes=actual,db_bytes=int(owner.execute(size_sql,(run,)).fetchone()[0]),limit=limit,
             expected_status='completed' if offset<=0 else 'rejected',synthetic_reader_only=True)
   (output/f'{name}-json-{offset}.manifest.json').write_text(json.dumps(spec,sort_keys=True)+'\n')
   begin=time.perf_counter_ns()
   try:
    loaded=loader(runner,run);status='completed'
    assert loaded['run_id']==run
   except ValueError: status='rejected'
   elapsed=time.perf_counter_ns()-begin
   after=history(owner)
   assert before==after and status==spec['expected_status']
   records.append(dict(**spec,status=status,loader_ns=elapsed,history_before=before,history_after=after))
(output/'reader-json-boundaries.json').write_text(json.dumps(records,indent=2)+'\n')
print([(r['case'],r['status']) for r in records])
