"""Bind immutable research deliveries to complete historical source snapshots."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE='f6d3d16034af038eda4c8687ea4f1ed6d2445ef6'
DELIVERIES={
14:('d2cb98ba1016f80bd2c2dd40159092f4f1b21395',['fresh-warmup-v1.json','safety-retention-v1.json','supply-sensitivity-v1.json']),
15:('97d1f8a00a00cecdcd01368403bdfeab8b92d510',['public-sales-forecast-v1.json']),
16:('39bf64d7e70b9221afbe1d697fe49fd348fcdc04',['policy-comparison-v1.json']),
17:('706fa82c7520f5119ffd85b8c6a2a65f40fc2f10',['public-sales-safety-v1.json']),
18:('3d66b4309cc465d39ed830b4db59ef0860807c25',['lab-accessibility-browser.json']),
19:('758d5d317ff8470841cc376bba49b86909ebb69c',['portfolio-claims.json']),
20:('e7473a595d4ef6deca33c283ea6b27e23ad83bc4',['public-calibration-freeze-v1.json','public-calibration-v1.json','public-calibration-acceptance.json']),
21:('d06badeb2a61b2f76da5ebb4afbd9ff6ffc38023',['lost-sales-v1.json.gz','lost-sales-v1-summary.json','lost-sales-acceptance.json']),
22:('c916c046b3af06503574aaea208a0197e0615a3e',['physical-count-v1.json','physical-count-acceptance.json']),
23:('c337a5616dda27398b0f82e9b9e011aba9fe9c6f',['hosted-lab-image-manifests.json','hosted-lab-local-http.json','hosted-lab-acceptance.json'])}
PARENTS={'parent_forecast_sha256':'public-sales-forecast-v1.json',
         'parent_safety_sha256':'public-sales-safety-v1.json','freeze_sha256':'public-calibration-freeze-v1.json'}
POLICY_FIELDS=('parameters','configurations','policy','dates','methods','horizons','target')


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(condition,message):
    if not condition:raise ValueError(message)
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,stderr=subprocess.DEVNULL)
def document(raw,name):return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
def path_ok(name):return isinstance(name,str) and not Path(name).is_absolute() and '..' not in Path(name).parts


def build(candidate=None):
    candidate=candidate or git('rev-parse','HEAD').decode().strip()
    require(bool(re.fullmatch('[0-9a-f]{40}',candidate)),'invalid candidate identity')
    require(subprocess.run(['git','merge-base','--is-ancestor',candidate,'HEAD'],cwd=ROOT).returncode==0,'candidate history lost')
    require(subprocess.run(['git','merge-base','--is-ancestor',BASE,candidate],cwd=ROOT).returncode==0,'base not retained')
    nodes={};artifacts={};bindings=[];drift=[];snapshots={};blob_cache={}
    def blob(commit,path):
        require(path_ok(path),'unsafe source path')
        key=(commit,path)
        if key not in blob_cache:
            try:blob_cache[key]=git('show',f'{commit}:{path}')
            except subprocess.CalledProcessError:blob_cache[key]=None
        return blob_cache[key]
    entries=[('core',BASE,['decision-benchmark.json','intermittent-benchmark.json','copilot-benchmark.json','feasibility-diagnostic.json'])]
    entries += [(str(pr),head,names) for pr,(head,names) in DELIVERIES.items()]
    for package,head,names in entries:
        require(subprocess.run(['git','merge-base','--is-ancestor',head,candidate],cwd=ROOT).returncode==0,f'package {package} not retained')
        nodes['git:'+head]=dict(kind='git_snapshot',commit=head,depends_on=[])
        for name in names:
            path='docs/review/'+name;raw=(ROOT/path).read_bytes()
            require(raw==blob(head,path),f'published artifact changed: {path}')
            identity='artifact:'+path
            artifacts[name]=identity
            data=document(raw,name)
            nodes[identity]=dict(kind='artifact',path=path,sha256=sha(raw),bytes=len(raw),delivery=package,
                                 published_head=head,depends_on=['git:'+head])
            if not isinstance(data,dict):continue
            hashes=data.get('source_sha256',{})
            require(isinstance(hashes,dict),'invalid source map')
            if hashes:
                options=[data.get('code_commit'),head,BASE]
                options += git('rev-list','--first-parent',head).decode().splitlines()
                match=None
                for commit in dict.fromkeys(c for c in options if c):
                    require(bool(re.fullmatch('[0-9a-f]{40}',commit)),'invalid code identity')
                    if all(blob(commit,p) is not None and sha(blob(commit,p))==h for p,h in hashes.items()):
                        match=commit;break
                require(match is not None,f'no complete historical source snapshot: {path}')
                snapshots[path]=match
                git_node='git:'+match
                nodes[identity]['depends_on'].append(git_node)
                nodes.setdefault(git_node,dict(kind='git_snapshot',commit=match,depends_on=[]))
                for source,expected in hashes.items():
                    require(bool(re.fullmatch('[0-9a-f]{64}',expected)),'invalid source fingerprint')
                    key='source:'+expected+':'+source
                    nodes.setdefault(key,dict(kind='versioned_source',path=source,sha256=expected,depends_on=[git_node]))
                    nodes[identity]['depends_on'].append(key)
                    current=sha((ROOT/source).read_bytes()) if (ROOT/source).is_file() else None
                    if current!=expected:drift.append(dict(artifact=path,source=source,historical_sha256=expected,current_sha256=current))
                if data.get('code_commit'):require(match==data['code_commit'],'recorded run source commit disagrees')
            policy={k:data[k] for k in POLICY_FIELDS if k in data}
            if policy:
                key='policy:'+sha(canonical(policy))
                nodes.setdefault(key,dict(kind='declared_policy',sha256=sha(canonical(policy)),value=policy,depends_on=[]))
                nodes[identity]['depends_on'].append(key)
            for field,value in data.items():
                if field in PARENTS:
                    bindings.append((identity,PARENTS[field],value))
                elif field.endswith('_sha256') and isinstance(value,str):
                    require(bool(re.fullmatch('[0-9a-f]{64}',value)),'invalid declared input fingerprint')
                    key='external:'+field+':'+value
                    nodes.setdefault(key,dict(kind='declared_external_fingerprint',field=field,sha256=value,
                                              local_verification='not performed by manifest',depends_on=[]))
                    nodes[identity]['depends_on'].append(key)
    # Packaged Lab is synthetic; UUID/calculation semantics stay with its validator.
    path='src/inventory_intelligence/lab_evidence.json';raw=(ROOT/path).read_bytes()
    require(raw==blob(BASE,path),'packaged historical Lab archive changed')
    nodes['artifact:'+path]=dict(kind='artifact',path=path,sha256=sha(raw),bytes=len(raw),delivery='core',published_head=BASE,depends_on=['git:'+BASE])
    for identity,parent,value in bindings:
        require(parent in artifacts and nodes[artifacts[parent]]['sha256']==value,'parent/freeze binding changed')
        nodes[identity]['depends_on'].append(artifacts[parent])
    validator='git:'+candidate
    nodes.setdefault(validator,dict(kind='git_snapshot',commit=candidate,depends_on=[]))
    for source in ('docs/EVIDENCE.md','scripts/research_lineage.py','tests/test_research_lineage.py'):
        raw=(ROOT/source).read_bytes()
        require(raw==blob(candidate,source),'commit lineage validator/protocol/oracles before archiving')
        key='validator:'+source
        nodes[key]=dict(kind='validator_source',path=source,sha256=sha(raw),depends_on=[validator])
    for node in nodes.values():node['depends_on']=sorted(set(node['depends_on']))
    return dict(protocol_version='research-integration-lineage-v1',candidate_commit=candidate,base_commit=BASE,
                deliveries={str(k):v[0] for k,v in DELIVERIES.items()},nodes=nodes,source_snapshots=snapshots,
                historical_current_drift=sorted(drift,key=lambda x:(x['artifact'],x['source'])),
                summary=dict(deliveries=10,artifacts=sum(n['kind']=='artifact' for n in nodes.values()),
                    nodes=len(nodes),source_maps=len(snapshots),parent_bindings=len(bindings),
                    current_drift_bindings=len(drift),model_refits=0,simulation_replays=0,operational_writes=0),
                limitations=['Byte/metadata lineage, not signed authenticity or semantic validation.',
                    'External fingerprints are declared; local-cache semantic audits are separate.',
                    'Candidate ancestry does not prove main integration, CI or public hosting.'])


def audit(manifest):
    # Receipt/docs commits can follow; the recorded candidate retains every delivery.
    candidate=manifest['candidate_commit']
    require(bool(re.fullmatch('[0-9a-f]{40}',candidate)),'invalid candidate identity')
    require(subprocess.run(['git','merge-base','--is-ancestor',candidate,'HEAD'],cwd=ROOT).returncode==0,'candidate history lost')
    expected=build(candidate=candidate)
    require(manifest==expected,'manifest nodes/bindings/drift/denominators changed')
    active=set();done=set()
    def visit(identity):
        require(identity in manifest['nodes'],'missing dependency')
        require(identity not in active,'cyclic dependency')
        if identity in done:return
        active.add(identity)
        for dep in manifest['nodes'][identity]['depends_on']:visit(dep)
        active.remove(identity);done.add(identity)
    for identity in manifest['nodes']:visit(identity)
    return manifest['summary']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/review/research-integration-lineage-v1.json')
    parser.add_argument('--audit',action='store_true')
    args=parser.parse_args()
    if args.output.exists():result=audit(json.loads(args.output.read_text()))
    else:
        require(not args.audit,'no saved manifest')
        value=build();result=audit(value);args.output.write_bytes(canonical(value)+b'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
