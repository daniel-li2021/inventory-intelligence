"""Bounded HTTP acceptance of a chosen synthetic hosted Lab; no source writes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import urllib.error
import urllib.request


def check(base_url, *, ca_file=None):
    context=ssl.create_default_context(cafile=str(ca_file) if ca_file else None)
    records=[]
    def request(path,payload=None,*,raw=None,status=200):
        body=json.dumps(payload).encode() if payload is not None else raw
        req=urllib.request.Request(base_url.rstrip('/')+path,data=body,
            headers={'Content-Type':'application/json'} if body is not None else {})
        try: response=urllib.request.urlopen(req,context=context,timeout=10)
        except urllib.error.HTTPError as error: response=error
        with response:
            data=response.read()
            if response.status!=status: raise ValueError(f'{path}: expected {status}, received {response.status}')
            if response.headers.get('X-Content-Type-Options')!='nosniff': raise ValueError('missing nosniff')
            if "frame-ancestors 'none'" not in response.headers.get('Content-Security-Policy',''): raise ValueError('missing CSP')
            if response.headers.get('Referrer-Policy')!='no-referrer': raise ValueError('missing referrer policy')
            records.append(dict(path=path,method=req.get_method(),status=response.status,bytes=len(data),
                                sha256=hashlib.sha256(data).hexdigest()))
            return json.loads(data) if response.headers.get_content_type()=='application/json' else data
    for path in ('/','/static/lab.css','/static/lab.js'): request(path)
    baseline=request('/api/lab')
    assert baseline['metadata']['synthetic'] is True
    assert baseline['baseline']['plan']['proposed_order_qty']==12
    assert baseline['baseline']['costs']['total']=='327'
    default=request('/api/scenarios',{})
    assert default==baseline
    spike=request('/api/scenarios',{'demand_percent':125})
    assert spike['scenario']['plan']['proposed_order_qty']==18 and spike['scenario']['costs']['total']=='351'
    delay=request('/api/scenarios',{'supplier_delay_days':3})
    assert delay['scenario']['plan']['proposed_order_qty']==12
    assert delay['scenario']['simulation']['metrics']['immediate_fill_rate']=='11/28'
    assert delay['scenario']['simulation']['metrics']['shortage_days']==17 and delay['scenario']['costs']['total']=='1171'
    blocked=request('/api/scenarios',{'evidence_case':'incomplete_supply'})
    assert blocked['scenario']['status']=='not_assessable'
    for field in ('plan','simulation','risk','costs'): assert blocked['scenario'][field] is None
    zero=request('/api/scenarios',{'demand_percent':0})
    assert zero['scenario']['simulation']['metrics']['new_demand_units']==0
    assert zero['scenario']['simulation']['metrics']['immediate_fill_rate'] is None
    for result in (spike,delay,blocked,zero): assert result['baseline']==baseline['baseline']
    evidence=request('/api/evidence')
    assert evidence['synthetic'] is True and evidence['business_data']=='synthetic only'
    assert evidence['digest']==baseline['metadata']['archive_digest']
    request('/api/scenarios',{'demand_percent':True},status=422)
    request('/api/scenarios',raw=b'x'*4097,status=413)
    request('/docs',status=404)
    return dict(verified_at=datetime.now(timezone.utc).isoformat(),base_url=base_url,
                tls_verified=base_url.startswith('https://'),private_ca=ca_file is not None,
                requests=len(records),checks=records,archive_digest=evidence['digest'],
                baseline_proposal=12,spike_proposal=18,delay_fill='11/28',
                blocked_outputs_null=True,zero_demand_fill_null=True,baseline_preserved=True,
                operational_writes=0)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',required=True)
    parser.add_argument('--ca-file',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=check(args.base_url,ca_file=args.ca_file)
    if args.output: args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(requests=result['requests'],tls_verified=result['tls_verified'],
                         private_ca=result['private_ca'],archive_digest=result['archive_digest'])))


if __name__=='__main__': main()
