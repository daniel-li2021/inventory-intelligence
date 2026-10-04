"""Fresh matched synthetic backlog/lost-sales experiment and saved-trajectory audit."""

import argparse
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import random
import subprocess

from inventory_intelligence import decision, lost_sales
from scripts.decision_benchmark import canonical, digest

VERSION = "lost-sales-research-v1"
SEEDS = (9101, 9127, 9181)
FAMILIES = ("constant", "weekly", "zero", "lumpy", "pause_recovery", "cessation")
WARMUP = 56
N = 84
COMMON_END = 100
PARAMETERS = dict(on_hand=10,review_days=7,pack_size=2,moq=4,holding_cost=1,order_cost=2)
SOURCES = ("docs/CONTRACTS.md", "scripts/lost_sales_benchmark.py",
           "scripts/lost_sales_audit.py",
           "src/inventory_intelligence/lost_sales.py", "src/inventory_intelligence/decision.py",
           "src/inventory_intelligence/forecasting.py", "scripts/decision_benchmark.py")


def require(condition, message):
    if not condition: raise ValueError(message)


def decode(text):
    def exact(value):
        if set(value)=={'numerator','denominator'}:
            return Fraction(value['numerator'],value['denominator'])
        return value
    return json.loads(text,object_hook=exact)


def observations(family, seed):
    rng=random.Random(seed + 100003 * FAMILIES.index(family))
    if family=='constant': return [3]*140
    if family=='weekly': return ([0,1,2,3,4,5,6]*20)
    if family=='zero': return [0]*140
    if family=='lumpy': return [rng.choice((0,0,0,0,0,2,8,16)) for _ in range(140)]
    result=[rng.randint(1,5) for _ in range(140)]
    if family=='pause_recovery': result[98:119]=[0]*21
    elif family=='cessation': result[112:]=[0]*28
    else: raise ValueError('unknown frozen demand family')
    return result


def supplier(family, seed, profile):
    if profile=='fixed': return [0]*15
    if profile!='variable': raise ValueError('unknown supplier profile')
    rng=random.Random(500009 + seed + 300007 * FAMILIES.index(family))
    values=[]
    while len(values)<15:
        block=[0,0,1,1,2,4]; rng.shuffle(block); values.extend(block)
    return values[:15]


def summarize(simulation, demand, *, semantics, initial_stock, warmup_days, common_end, inbound=(), review_days=7):
    require(semantics in ('backlog','lost_sales'), 'unknown fulfillment semantics')
    days=simulation['days']; n=len(demand)
    require(type(warmup_days) is int and 0<warmup_days<n
            and type(review_days) is int and review_days>0 and warmup_days%review_days==0, 'invalid warmup boundary')
    require(len(days)<=common_end and not simulation['terminal']['outstanding_qty']
            and not simulation['terminal']['backlog'], 'unsettled or unequal closure')
    result=dict(costs={},periods={})
    for name,start,end in (('warmup',0,warmup_days),('score',warmup_days,n),('settlement',n,len(days))):
        window=days[start:end]
        acquisition=2*sum(row['order_qty'] for row in window)
        if name=='warmup': acquisition+=2*(initial_stock+sum(row['quantity'] for row in inbound))
        holding=sum(row['on_hand'] for row in window)
        if name=='settlement': holding+=(common_end-len(days))*simulation['terminal']['on_hand']
        missed=sum(row['newly_unmet_units'] for row in window)
        penalty10=(10*sum(row['backlog'] for row in window) if semantics=='backlog' else 10*missed)
        penalty40=(penalty10 if semantics=='backlog' else 40*missed)
        setup=2*sum(row['order_qty']>0 for row in window)
        result['costs'][name]=dict(acquisition=acquisition,holding=holding,setup=setup,
            penalty10=penalty10,penalty40=penalty40,total10=acquisition+holding+setup+penalty10,
            total40=acquisition+holding+setup+penalty40)
        if name=='settlement': continue
        units=sum(demand[start:end]); immediate=sum(row['immediately_filled_units'] for row in window)
        eventual=sum(f['quantity'] for row in days for f in row['fulfillments'] if start<=f['due_day']<end)
        starts=list(range(start,end-review_days+1,review_days))
        clear=sum(not any(row['newly_unmet_units'] for row in days[t:t+review_days]) for t in starts)
        native_clear=sum(not any(row['shortage'] for row in days[t:t+review_days]) for t in starts)
        result['periods'][name]=dict(days=end-start,demand_units=units,immediate_units=immediate,
            immediate_fill=Fraction(immediate,units) if units else None,eventual_units=eventual,
            eventual_fill=Fraction(eventual,units) if units else None,new_unmet_units=missed,
            permanently_lost_units=missed if semantics=='lost_sales' else 0,cycles=len(starts),
            new_shortage_free_cycles=clear,new_cycle_service=Fraction(clear,len(starts)) if starts else None,
            native_shortage_free_cycles=native_clear,
            backlog_piece_days=sum(row['backlog'] for row in window),
            on_hand_piece_days=sum(row['on_hand'] for row in window))
    result.update(full_cost10=sum(c['total10'] for c in result['costs'].values()),
        full_cost40=sum(c['total40'] for c in result['costs'].values()),
        purchased_pieces=initial_stock+sum(row['quantity'] for row in inbound)+sum(row['order_qty'] for row in days),
        ordered_pieces=sum(row['order_qty'] for row in days),
        first_order=simulation['reviews'][0]['order_qty'] if simulation['reviews'] else 0,
        boundary_state={k:days[warmup_days-1][k] for k in ('on_hand','backlog','outstanding_qty')},
        terminal_stock=simulation['terminal']['on_hand'],accounting_days=common_end,native_days=len(days))
    return result


def contrast(backlog, lost):
    a,b=backlog['periods']['score'],lost['periods']['score']
    missed=sum(p['permanently_lost_units'] for p in lost['periods'].values())
    fixed_cost=lost['full_cost10']-10*missed
    return dict(fill_difference=b['immediate_fill']-a['immediate_fill'] if a['immediate_fill'] is not None else None,
        new_cycle_difference=b['new_cycle_service']-a['new_cycle_service'],
        ordered_pieces_difference=lost['ordered_pieces']-backlog['ordered_pieces'],
        first_order_difference=lost['first_order']-backlog['first_order'],
        cost10_difference=lost['full_cost10']-backlog['full_cost10'],
        cost40_difference=lost['full_cost40']-backlog['full_cost10'],
        break_even_lost_unit_penalty=Fraction(backlog['full_cost10']-fixed_cost,missed) if missed else None)


def evaluate():
    trajectories={}; cache={}; pairs=[]; paths=[]
    for family in FAMILIES:
        for seed in SEEDS:
            values=observations(family,seed);history,demand=values[:56],values[56:]
            path=dict(id=f'{family}:{seed}',family=family,seed=seed,history=history,demand=demand,
                      demand_sha256=digest(demand),supplier_paths={p:supplier(family,seed,p) for p in ('fixed','variable')})
            paths.append(path)
            for method in ('mean','seasonal_naive'):
                for safety in (0,6):
                    for lead in (2,5):
                        for profile,trace in path['supplier_paths'].items():
                            slots=len(range(0,N+lead+max(trace)+7,7))
                            args=dict(PARAMETERS,method=method,safety_qty=safety,lead_days=lead,supplier_delays=trace[:slots])
                            arms={}
                            for semantics,kernel in (('backlog',decision),('lost_sales',lost_sales)):
                                payload=dict(history=history,demand=demand,parameters=args,semantics=semantics)
                                identity=digest(payload)
                                if identity not in cache:
                                    simulation=kernel.simulate(history,demand,**args,**({'backlog_cost':10} if semantics=='backlog' else {'lost_cost':10}))
                                    cache[identity]=dict(inputs=payload,simulation=simulation,
                                        trajectory_sha256=digest(simulation),summary=summarize(simulation,demand,
                                        semantics=semantics,initial_stock=10,warmup_days=WARMUP,common_end=COMMON_END))
                                trajectories[identity]=cache[identity]
                                arms[semantics]=identity
                            back,lost=(trajectories[arms[name]] for name in ('backlog','lost_sales'))
                            forecasts=lambda r:[(x['day'],x['forecast'],x['target']) for x in r['simulation']['reviews'] if not x['runoff']]
                            require(forecasts(back)==forecasts(lost),'semantic policy saw different demand forecasts')
                            pairs.append(dict(path_id=path['id'],method=method,safety_qty=safety,lead_days=lead,
                                supply_profile=profile,arms=arms,differences=contrast(back['summary'],lost['summary'])))
    physical=lambda r:[{k:day.get(k,0) for k in ('day','on_hand','backlog','new_demand','fulfilled_units',
                                               'immediately_filled_units','receipts','order_qty','outstanding_qty','lost_units')}
                        for day in r['simulation']['days']]
    differences=[p['differences'] for p in pairs]
    summary=dict(path_labels=len(paths),distinct_demand_paths=len({p['demand_sha256'] for p in paths}),
        distinct_supplier_paths=len({digest(t) for p in paths for t in p['supplier_paths'].values()}),
        pairs=len(pairs),logical_arms=2*len(pairs),unique_arm_computations=len(trajectories),
        distinct_native_physical_trajectories=len({digest(physical(r)) for r in trajectories.values()}),
        fill_improved=sum(d['fill_difference'] is not None and d['fill_difference']>0 for d in differences),
        fill_regressed=sum(d['fill_difference'] is not None and d['fill_difference']<0 for d in differences),
        fill_equal=sum(d['fill_difference']==0 for d in differences),fill_undefined=sum(d['fill_difference'] is None for d in differences),
        cost10_lower=sum(d['cost10_difference']<0 for d in differences),cost10_higher=sum(d['cost10_difference']>0 for d in differences),
        cost40_lower=sum(d['cost40_difference']<0 for d in differences),cost40_higher=sum(d['cost40_difference']>0 for d in differences),
        ordered_pieces_different=sum(d['ordered_pieces_difference']!=0 for d in differences),
        first_order_different=sum(d['first_order_difference']!=0 for d in differences))
    return dict(protocol_version=VERSION,synthetic=True,observation='completed attempted demand, not censored sales',
        warmup_days=WARMUP,scored_days=28,common_accounting_days=COMMON_END,paths=paths,trajectories=trajectories,pairs=pairs,summary=summary,
        limits=['Different business obligations and penalty units; no recommendation to cancel accepted orders.',
                'Repriced events and repeated controls are not independent trials; no policy/model promotion.',
                'Synthetic observed attempts include lost units; sales-only feedback needs a new protocol.'])


def read_report(path):
    return decode(gzip.decompress(path.read_bytes()))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('docs/review/lost-sales-v1.json.gz'))
    args=parser.parse_args()
    require(args.output.name.endswith('.json.gz'),'output must be a compressed .json.gz artifact')
    root=Path(__file__).resolve().parents[1]
    sources={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in SOURCES}
    if args.output.exists():
        report=read_report(args.output)
        require(report['source_sha256']==sources,'current sources differ from consumed study; do not overwrite')
        from scripts.lost_sales_audit import audit
        audit(args.output)
        print(json.dumps(dict(cache_reused=True,**report['summary'])));return
    for name in SOURCES:
        committed=subprocess.check_output(['git','show',f'HEAD:{name}'],cwd=root)
        require(committed==(root/name).read_bytes(),'commit implementation/protocol before fresh scoring')
    report=evaluate();report['source_sha256']=sources
    report['code_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    temporary=args.output.with_name(args.output.name+'.tmp')
    temporary.write_bytes(gzip.compress(canonical(report)+b'\n',mtime=0));temporary.replace(args.output)
    summary_path=args.output.with_name(args.output.name.removesuffix('.json.gz')+'-summary.json')
    mirror={k:v for k,v in report.items() if k!='trajectories'}
    mirror['trajectory_archive_sha256']=hashlib.sha256(args.output.read_bytes()).hexdigest()
    summary_path.write_bytes(canonical(mirror)+b'\n')
    print(json.dumps(report['summary'],sort_keys=True))


if __name__=='__main__': main()
