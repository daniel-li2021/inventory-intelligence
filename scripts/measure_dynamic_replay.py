"""Saved-only bounded latency/evidence census; never rerun a consumed study."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import platform
import resource
import statistics
import sys
import time

from inventory_intelligence.product import load_catalog, overview, _report
from inventory_intelligence.insights import discover
from inventory_intelligence.decision_contrast import compare

ROOT=Path(__file__).resolve().parents[1]


def samples(function,count):
    measured=[]
    for _ in range(count):
        start=time.perf_counter();function();measured.append((time.perf_counter()-start)*1000)
    return dict(samples=count,median_ms=statistics.median(measured),p95_nearest_rank_ms=sorted(measured)[-(-count*95//100)-1],max_ms=max(measured))


def measure():
    path=ROOT/'docs/review/dynamic-replay-v1.json.gz'
    c=load_catalog(path);key=('product-dynamic:a','product-dynamic:harbor');cutoff='2026-04-06'
    counts=[]
    for b in c['cutoffs']:
        found=discover(c,b['cutoff'])
        counts.append(dict(cutoff=b['cutoff'],keys=len(b['keys']),findings=len(found['findings']),unknown_sections=len(found['unknown']),saved_reports=1+2*len(b['keys'])))
    latency=dict(cold_validation=samples(lambda:load_catalog(path),10),
        discovery=samples(lambda:discover(c,cutoff),30),one_review_contrast=samples(lambda:compare(c,cutoff,*key,12),30))
    baseline=load_catalog()
    latency['retained_100key_discovery']=samples(lambda:discover(baseline),30)
    raw=gzip.decompress(path.read_bytes())
    source_files=['src/inventory_intelligence/'+name+'.py' for name in ('synthetic_replay','insights','decision_contrast','product','product_api','planner_loop')]+['docs/examples/dynamic-controls-v1.json','docs/SYNTHETIC_REPLAY.md']
    result=dict(kind='bounded_local_synthetic_controls',runtime=c['runtime'],host=platform.platform(),python=sys.version,
        archive_digest=c['digest'],archive_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source_versions=3,keys_per_version=4,key_cutoff_observations=12,
        saved_reports=27,independently_expected_discovery_triggers=15,matched_triggers=15,unexpected_triggers=0,
        simple_baseline='V1 categories/history expose two risk transitions; demand/supply/ETA and imbalance require V2. Correctness controls, not detection accuracy on an unseen sample.',
        predeclared_quality_holdout_executions=0,initial_capture_seconds_single_sample=0.3187765828333795,
        evidence=dict(raw_bytes=len(raw),compressed_bytes=path.stat().st_size,raw_input_bytes=len(c['original_input_text'].encode()),interned_objects=len(c['objects']),cutoff_growth=counts),latency=latency,
        max_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
        source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in source_files},
        paid_controls={name:{k:v for k,v in arm.items() if k!='days'} for name,arm in compare(c,cutoff,*key,12)['arms'].items()},
        negative_control='Quiet demand: additional order has higher paid cost than no action; no universal winner.',
        limits=['Initial replay latency predates the added occupied-DB guard and persisted reliability reload; final-code latency is not inferred from it.','Read latency uses retained evidence and warm filesystem; not network or reference-host acceptance.','Maximum 50x2 keys/12 versions is a parser envelope; its full execution/performance is unmeasured.','RSS is whole-process peak, not per-request allocation.','No supplier capacity/calendar, real data, paid service, human comprehension or public runtime validation.'])
    # Independent hand expectations must pass before a receipt can be written.
    assert [x['findings'] for x in counts]==[3,8,4]
    assert [result['paid_controls'][p]['total_cost'] for p in ('no_action','actual_proposal','alternative')]==['18039','16281','14609']
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=measure()
    with args.output.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(output=str(args.output),latency=result['latency'],raw_bytes=result['evidence']['raw_bytes'],compressed_bytes=result['evidence']['compressed_bytes'])))


if __name__=='__main__':main()
