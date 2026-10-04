"""Archive hand-declared synthetic count outcomes and verify their immutable lineage."""

import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess

from inventory_intelligence.physical_count import VERSION,canonical,digest,evaluate

ROOT=Path(__file__).resolve().parents[1]
FIXTURE='docs/examples/physical-count-inputs-v1.json'
SOURCES=('docs/CONTRACTS.md',FIXTURE,'src/inventory_intelligence/physical_count.py',
         'scripts/physical_count_benchmark.py','tests/test_physical_count.py')
CONFIG=dict(observer_minimum=2,all_counts_agree=True,blind_counts_required=True,uom='each',
            review_policy='one independent bound review',operational_write=False)


def require(condition,message):
    if not condition: raise ValueError(message)


def sources(): return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def fixtures():
    document=json.loads((ROOT/FIXTURE).read_text())
    require(document['protocol_version']==VERSION and document['synthetic'] is True,'fixture boundary changed')
    rows=document['cases'];ids=[row['id'] for row in rows]
    require(len(ids)==40 and len(set(ids))==40,'fixture identity/count changed')
    return rows


def lineage(rows,source_hashes):
    """Edges name all files and exact input/result fingerprints, not source authenticity."""
    nodes={f'file:{name}':dict(kind='file',path=name,sha256=value,depends_on=[])
           for name,value in source_hashes.items()}
    nodes['policy:physical-count-v1']=dict(kind='policy',sha256=digest(CONFIG),config=CONFIG,
        depends_on=['file:docs/CONTRACTS.md'])
    for record in rows:
        identity=record['id'];source=f'input:{identity}';result=f'assessment:{identity}'
        nodes[source]=dict(kind='input',case_id=identity,sha256=record['input_sha256'],depends_on=[f'file:{FIXTURE}'])
        nodes[result]=dict(kind='assessment',case_id=identity,sha256=record['result_sha256'],
            depends_on=[source,'policy:physical-count-v1','file:src/inventory_intelligence/physical_count.py',
                        'file:scripts/physical_count_benchmark.py'])
    return nodes


def audit_document(document):
    """Check saved outputs against independent goldens, bindings and dependency bytes."""
    source_hashes=sources()
    require(document['protocol_version']==VERSION and document['synthetic'] is True,'report boundary changed')
    require(document['source_sha256']==source_hashes and document['policy']==CONFIG,'source/config changed')
    for name,value in source_hashes.items():
        pinned=subprocess.check_output(['git','show',f"{document['code_commit']}:{name}"],cwd=ROOT)
        require(hashlib.sha256(pinned).hexdigest()==value,'code commit/source bytes disagree')
    golden={row['id']:row for row in fixtures()}
    ids=[row['id'] for row in document['cases']]
    require(len(ids)==40 and set(ids)==set(golden) and len(set(ids))==40,'saved case identity changed')
    for record in document['cases']:
        case=golden[record['id']];inputs=case['inputs'];result=record['result'];expected=case['expected']
        require(record['input_sha256']==digest(inputs) and record['result_sha256']==digest(result),'case fingerprints changed')
        actual={k:result[k] for k in expected if k!='finding_reasons'}
        actual['finding_reasons']=sorted(f['reason'] for f in result['findings'])
        require(actual==expected,'hand-declared semantic outcome changed')
        payload={k:inputs[k] for k in ('system','manifest','counts','adjustment_reviews')}
        fingerprint=digest(payload)
        clock=datetime.fromisoformat(inputs['evaluated_at']).astimezone(timezone.utc).isoformat()
        require(result['contract_version']==VERSION and result['source_payload_sha256']==fingerprint and result['evaluated_at']==clock,
                'source/knowledge-clock identity changed')
        require(result['run_id']=='physical:'+digest(dict(contract_version=VERSION,source_sha256=fingerprint,evaluated_at=clock)),
                'run identity changed')
        raw_counts=inputs['counts'] if isinstance(inputs['counts'],list) else []
        require(sorted(canonical(row) for row in raw_counts)==sorted(canonical(row) for row in result['count_evidence']),
                'raw count evidence changed/dropped')
        if expected['physical_status']=='confirmed_variance':
            counts=sorted(inputs['counts'],key=lambda row:(row['source_system'],row['count_id']))
            binding=digest(dict(system=inputs['system'],manifest=inputs['manifest'],counts=counts))
            proposal=dict(proposal_id=binding,source_binding_sha256=binding,sku_id=inputs['system']['sku_id'],
                warehouse_id=inputs['system']['warehouse_id'],as_of=inputs['system']['as_of'],
                before_quantity=expected['system_quantity'],physical_quantity=expected['physical_quantity'],delta_quantity=expected['variance_quantity'])
            require(result['proposal']==proposal,'proposal source/quantity binding changed')
        else: require(result['proposal'] is None,'uncorroborated/matched stock created a proposal')
        require(result['adjustment_evidence']==inputs['adjustment_reviews'],'review evidence changed/dropped')
    expected_lineage=lineage(document['cases'],source_hashes)
    require(document['lineage']==expected_lineage,'dependency graph changed')
    nodes=document['lineage']
    visiting=set();done=set()
    def visit(identity):
        require(identity in nodes,'dangling dependency')
        require(identity not in visiting,'cyclic dependency')
        if identity in done: return
        visiting.add(identity)
        for dependency in nodes[identity]['depends_on']: visit(dependency)
        visiting.remove(identity);done.add(identity)
    for identity in nodes: visit(identity)
    from collections import Counter
    summary=dict(cases=40,physical_statuses=dict(Counter(row['result']['physical_status'] for row in document['cases'])),
                 adjustment_statuses=dict(Counter(row['result']['adjustment_status'] for row in document['cases'])))
    require(document['summary']==summary,'outcome denominators changed')
    return dict(cases=40,lineage_nodes=len(nodes),reassessments=0,operational_writes=0)


def write(path,document):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_bytes(canonical(document)+b'\n');temporary.replace(path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/review/physical-count-v1.json')
    parser.add_argument('--audit',action='store_true')
    args=parser.parse_args()
    if args.output.exists():
        document=json.loads(args.output.read_text())
        print(json.dumps(dict(cache_reused=True,**audit_document(document)),sort_keys=True));return
    require(not args.audit,'no accepted artifact to audit')
    hashes=sources()
    for name in SOURCES:
        require(subprocess.check_output(['git','show',f'HEAD:{name}'],cwd=ROOT)==(ROOT/name).read_bytes(),
                'commit protocol/oracles/implementation before archiving')
    from collections import Counter
    rows=[]
    for case in fixtures():
        result=evaluate(**case['inputs'])
        rows.append(dict(id=case['id'],input_sha256=digest(case['inputs']),result=result,result_sha256=digest(result)))
    document=dict(protocol_version=VERSION,synthetic=True,source_sha256=hashes,policy=CONFIG,
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),cases=rows,
        lineage=lineage(rows,hashes),summary=dict(cases=40,
        physical_statuses=dict(Counter(row['result']['physical_status'] for row in rows)),
        adjustment_statuses=dict(Counter(row['result']['adjustment_status'] for row in rows))),
        limitations=['Declared synthetic upstream status, blind observers and freeze; not externally authenticated warehouse truth.',
                     'Categorical corroboration, not calibrated probability or measured shrinkage rate.',
                     'Adjustment evidence is advisory; no source write or operational planner integration.'])
    audit_document(document)
    write(args.output,document)
    print(json.dumps(document['summary'],sort_keys=True))


if __name__=='__main__': main()
