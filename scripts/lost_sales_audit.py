"""Independent saved-event reconciliation; no kernel replay or model invocation."""

import argparse
from fractions import Fraction
import hashlib
from math import ceil
from pathlib import Path
import json
import subprocess

from scripts.lost_sales_benchmark import (COMMON_END, FAMILIES, N, PARAMETERS, SEEDS, SOURCES,
    VERSION, WARMUP, contrast, decode, digest, observations, read_report, require, supplier)


def audit_arm(record, *, warmup=WARMUP, common_end=COMMON_END):
    inputs=record['inputs'];simulation=record['simulation'];summary=record['summary']
    require(digest(simulation)==record['trajectory_sha256'],'trajectory bytes changed')
    history,demand,args,kind=(inputs[k] for k in ('history','demand','parameters','semantics'))
    require(kind in ('backlog','lost_sales'),'unknown semantics')
    require(simulation['contract_version']==(VERSION if kind=='lost_sales' else 'decision-benchmark-v1'),
            'kernel contract changed')
    stock=args['on_hand']; queue={};arrivals={}
    for row in args.get('inbound',()): arrivals[row['arrival_day']]=arrivals.get(row['arrival_day'],0)+row['quantity']
    days=simulation['days']; reviews={r['day']:r for r in simulation['reviews']}
    lead,review=args['lead_days'],args['review_days'];n=len(demand)
    require(len(days)==n+lead+max(args['supplier_delays'],default=0)+review,'native calendar changed')
    require([r['day'] for r in days]==list(range(len(days))) and len(days)<=common_end,'day/settlement calendar changed')
    require(len(reviews)==len(simulation['reviews']),'duplicate review identity')
    completed=list(history);filled_total=lost_total=0
    for day,row in enumerate(days):
        require(row['scored']==(day<n),'scoring labels changed')
        require(all(type(row[k]) is int and row[k]>=0 for k in
                    ('receipts','order_qty','outstanding_qty','on_hand','backlog','fulfilled_units','newly_unmet_units')),'invalid pieces')
        received=arrivals.pop(day,0);stock+=received
        require(row['receipts']==received,'receipt timing changed')
        fills=[]
        def fill_queue():
            nonlocal stock
            for due in sorted(queue):
                qty=min(stock,queue[due]);stock-=qty;queue[due]-=qty
                if qty: fills.append(dict(id=f'new:{due}',kind='new',due_day=due,quantity=qty))
            for due in list(queue):
                if not queue[due]: del queue[due]
        if kind=='backlog': fill_queue()
        review_day=day%review==0
        order=0
        if review_day:
            require(day in reviews,'missing review')
            receipt=reviews[day]; horizon=lead+review
            if day<n:
                if args['method']=='mean': expected=[Fraction(sum(completed),len(completed))]*horizon
                elif args['method']=='seasonal_naive': expected=[Fraction(completed[-7:][i%7]) for i in range(horizon)]
                elif args['method']=='naive': expected=[Fraction(completed[-1])]*horizon
                elif args['method']=='zero': expected=[Fraction(0)]*horizon
                else: raise ValueError('unknown forecast method')
                target=sum(expected)+args.get('safety_qty',0)
            else: expected=[];target=Fraction(0)
            position=stock+sum(arrivals.values())-sum(queue.values())
            need=max(0,target-position)
            if need:
                whole=max(ceil(need),args.get('moq',1));pack=args.get('pack_size',1)
                order=pack*((whole+pack-1)//pack)
            require(receipt==dict(day=day,runoff=day>=n,forecast=expected,target=target,
                                 inventory_position=position,order_qty=order),'review knowledge/action changed')
            if order:
                due=day+lead+args['supplier_delays'][day//review]
                arrivals[due]=arrivals.get(due,0)+order
        else: require(day not in reviews,'unexpected review')
        attempted=demand[day] if day<n else 0
        immediate=min(stock,attempted)
        if kind=='backlog':
            if attempted: queue[day]=attempted
            fill_queue();lost=0;penalty=10*sum(queue.values())
        else:
            stock-=immediate;lost=attempted-immediate;penalty=10*lost
            if immediate: fills.append(dict(id=f'new:{day}',kind='new',due_day=day,quantity=immediate))
            require(row['lost_units']==lost,'lost event changed or restored later')
        require(row['new_demand']==attempted and row['prior_demand']==0,'attempt mapping changed')
        require(row['fulfillments']==fills and row['fulfilled_units']==sum(f['quantity'] for f in fills),
                'fulfillment identity/FIFO changed')
        require(row['immediately_filled_units']==immediate and row['newly_unmet_units']==attempted-immediate,
                'immediate service changed')
        require(row['on_hand']==stock and row['backlog']==sum(queue.values()) and row['outstanding_qty']==sum(arrivals.values()),
                'stock/debt/pipeline conservation failed')
        require(row['order_qty']==order and row['shortage']==(bool(queue) if kind=='backlog' else bool(lost)),
                'action/shortage changed')
        penalty_key='backlog_cost' if kind=='backlog' else 'lost_cost'
        require(row['holding_cost']==stock and row[penalty_key]==penalty and row['order_cost']==2*bool(order)
                and row['total_cost']==stock+penalty+2*bool(order),'kernel rate/cost changed')
        filled_total+=sum(f['quantity'] for f in fills);lost_total+=lost
        if day<n: completed.append(attempted)
    require(not queue and not arrivals,'unsettled terminal obligations/pipeline')
    purchased=args['on_hand']+sum(row['quantity'] for row in args.get('inbound',()))+sum(r['order_qty'] for r in days)
    require(purchased==filled_total+stock and sum(demand)==filled_total+lost_total,'full conservation failed')
    require(simulation['terminal']==dict(on_hand=stock,backlog=0,outstanding_qty=0,orders=[]),'terminal changed')
    metrics=simulation['metrics'];immediate=sum(r['immediately_filled_units'] for r in days[:n])
    cycle_starts=range(0,n-review+1,review)
    clear=sum(not any(r['shortage'] for r in days[t:t+review]) for t in cycle_starts)
    native_metrics=dict(new_demand_units=sum(demand),immediately_filled_units=immediate,
        complete_cycles=len(cycle_starts),shortage_free_cycles=clear,
        cycle_service=Fraction(clear,len(cycle_starts)) if cycle_starts else None,
        shortage_days=sum(r['shortage'] for r in days[:n]),
        order_count=sum(r['order_qty']>0 for r in days[:n]),
        runoff_order_count=sum(r['order_qty']>0 for r in days[n:]),
        scored_cost=sum(r['total_cost'] for r in days[:n]),runoff_cost=sum(r['total_cost'] for r in days[n:]))
    require(all(metrics[k]==v for k,v in native_metrics.items()),'native service/cost metric changed')
    if kind=='lost_sales': require(metrics['lost_units']==lost_total,'native permanent loss changed')
    require(metrics['immediate_fill_rate']==(Fraction(immediate,sum(demand)) if sum(demand) else None),
            'native fill denominator changed')
    require(metrics['eventually_filled_units']==filled_total and metrics['eventual_fill_rate']==
            (Fraction(filled_total,sum(demand)) if sum(demand) else None),'eventual service changed')
    require(metrics['total_cost']==sum(r['total_cost'] for r in days),'native total cost changed')
    expected_costs={};periods={}
    for label,start,end in (('warmup',0,warmup),('score',warmup,n),('settlement',n,len(days))):
        window=days[start:end]
        acquisition=2*sum(r['order_qty'] for r in window)
        if label=='warmup': acquisition+=2*(args['on_hand']+sum(r['quantity'] for r in args.get('inbound',())))
        holding=sum(r['on_hand'] for r in window)+(stock*(common_end-len(days)) if label=='settlement' else 0)
        missed=sum(r['newly_unmet_units'] for r in window)
        p10=10*sum(r['backlog'] for r in window) if kind=='backlog' else 10*missed
        p40=p10 if kind=='backlog' else 40*missed
        setup=2*sum(r['order_qty']>0 for r in window)
        expected_costs[label]=dict(acquisition=acquisition,holding=holding,setup=setup,penalty10=p10,penalty40=p40,
                                   total10=acquisition+holding+setup+p10,total40=acquisition+holding+setup+p40)
        if label=='settlement': continue
        units=sum(demand[start:end]);served=sum(r['immediately_filled_units'] for r in window)
        eventual=sum(f['quantity'] for r in days for f in r['fulfillments'] if start<=f['due_day']<end)
        starts=range(start,end-review+1,review)
        clear=sum(not any(r['newly_unmet_units'] for r in days[t:t+review]) for t in starts)
        native=sum(not any(r['shortage'] for r in days[t:t+review]) for t in starts)
        periods[label]=dict(days=end-start,demand_units=units,immediate_units=served,
            immediate_fill=Fraction(served,units) if units else None,eventual_units=eventual,
            eventual_fill=Fraction(eventual,units) if units else None,new_unmet_units=units-served,
            permanently_lost_units=units-served if kind=='lost_sales' else 0,cycles=len(starts),
            new_shortage_free_cycles=clear,new_cycle_service=Fraction(clear,len(starts)) if starts else None,
            native_shortage_free_cycles=native,backlog_piece_days=sum(r['backlog'] for r in window),
            on_hand_piece_days=sum(r['on_hand'] for r in window))
    expected_summary=dict(costs=expected_costs,periods=periods,
        full_cost10=sum(c['total10'] for c in expected_costs.values()),full_cost40=sum(c['total40'] for c in expected_costs.values()),
        purchased_pieces=purchased,ordered_pieces=sum(r['order_qty'] for r in days),
        first_order=simulation['reviews'][0]['order_qty'] if simulation['reviews'] else 0,
        boundary_state={k:days[warmup-1][k] for k in ('on_hand','backlog','outstanding_qty')},
        terminal_stock=stock,accounting_days=common_end,native_days=len(days))
    require(summary==expected_summary,'paid windows/service summary changed')


def audit(path):
    report=read_report(path);root=Path(__file__).resolve().parents[1]
    require(report['protocol_version']==VERSION and report['synthetic'] is True
            and report['observation']=='completed attempted demand, not censored sales'
            and report['warmup_days']==56 and report['scored_days']==28 and report['common_accounting_days']==100,
            'study semantic metadata changed')
    require(report['source_sha256']=={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in SOURCES},
            'pinned study source changed')
    for name in SOURCES:
        pinned=subprocess.check_output(['git','show',f"{report['code_commit']}:{name}"],cwd=root)
        require(hashlib.sha256(pinned).hexdigest()==report['source_sha256'][name],'recorded code commit differs')
    paths={p['id']:p for p in report['paths']}
    require(len(paths)==18 and len(report['paths'])==18,'path identity changed')
    for family in FAMILIES:
        for seed in SEEDS:
            p=paths[f'{family}:{seed}'];values=observations(family,seed)
            expected=dict(id=f'{family}:{seed}',family=family,seed=seed,history=values[:56],demand=values[56:],
                demand_sha256=digest(values[56:]),supplier_paths={profile:supplier(family,seed,profile) for profile in ('fixed','variable')})
            require(p==expected,'frozen trace changed')
    trajectories=report['trajectories'];seen=set();cells=set()
    for pair in report['pairs']:
        cell=(pair['path_id'],pair['method'],pair['safety_qty'],pair['lead_days'],pair['supply_profile'])
        require(cell not in cells,'duplicate paired identity');cells.add(cell)
        require(pair['method'] in ('mean','seasonal_naive') and pair['safety_qty'] in (0,6)
                and pair['lead_days'] in (2,5) and pair['supply_profile'] in ('fixed','variable'),'unfrozen arm')
        p=paths[pair['path_id']];trace=p['supplier_paths'][pair['supply_profile']];lead=pair['lead_days']
        args=dict(PARAMETERS,method=pair['method'],safety_qty=pair['safety_qty'],lead_days=lead,
                  supplier_delays=trace[:len(range(0,N+lead+max(trace)+7,7))])
        require(set(pair['arms'])=={'backlog','lost_sales'},'semantic pair missing')
        for kind,identity in pair['arms'].items():
            record=trajectories[identity];expected=dict(history=p['history'],demand=p['demand'],parameters=args,semantics=kind)
            require(record['inputs']==expected and digest(expected)==identity,'paired input changed')
            if identity not in seen: audit_arm(record);seen.add(identity)
        back,lost=(trajectories[pair['arms'][k]] for k in ('backlog','lost_sales'))
        receipts=lambda r:[(x['day'],x['forecast'],x['target']) for x in r['simulation']['reviews'] if not x['runoff']]
        require(receipts(back)==receipts(lost),'forecast changed across semantics')
        require(pair['differences']==contrast(back['summary'],lost['summary']),'paired arithmetic changed')
    require(len(cells)==288 and seen==set(trajectories),'pair/trajectory denominator changed')
    differences=[pair['differences'] for pair in report['pairs']]
    physical=lambda r:[{k:day.get(k,0) for k in ('day','on_hand','backlog','new_demand','fulfilled_units',
                       'immediately_filled_units','receipts','order_qty','outstanding_qty','lost_units')}
                       for day in r['simulation']['days']]
    expected_summary=dict(path_labels=18,distinct_demand_paths=len({p['demand_sha256'] for p in paths.values()}),
        distinct_supplier_paths=len({digest(t) for p in paths.values() for t in p['supplier_paths'].values()}),
        pairs=288,logical_arms=576,unique_arm_computations=len(seen),
        distinct_native_physical_trajectories=len({digest(physical(r)) for r in trajectories.values()}),
        fill_improved=sum(d['fill_difference'] is not None and d['fill_difference']>0 for d in differences),
        fill_regressed=sum(d['fill_difference'] is not None and d['fill_difference']<0 for d in differences),
        fill_equal=sum(d['fill_difference']==0 for d in differences),fill_undefined=sum(d['fill_difference'] is None for d in differences),
        cost10_lower=sum(d['cost10_difference']<0 for d in differences),cost10_higher=sum(d['cost10_difference']>0 for d in differences),
        cost40_lower=sum(d['cost40_difference']<0 for d in differences),cost40_higher=sum(d['cost40_difference']>0 for d in differences),
        ordered_pieces_different=sum(d['ordered_pieces_difference']!=0 for d in differences),
        first_order_different=sum(d['first_order_difference']!=0 for d in differences))
    require(report['summary']==expected_summary,'aggregate comparison count changed')
    mirror_path=path.with_name(path.name.removesuffix('.json.gz')+'-summary.json')
    mirror=decode(mirror_path.read_text())
    expected={k:v for k,v in report.items() if k!='trajectories'}
    expected['trajectory_archive_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    require(mirror==expected,'summary/archive bytes disagree')
    return dict(pairs=288,logical_arms=576,unique_arm_audits=len(seen),archive_bytes=path.stat().st_size,
                simulation_replays=0,model_invocations=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,default=Path('docs/review/lost-sales-v1.json.gz'))
    args=parser.parse_args();print(json.dumps(audit(args.report),sort_keys=True))
