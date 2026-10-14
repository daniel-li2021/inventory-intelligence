"""A bounded single saved-planner review, with common paid execution windows."""
from datetime import date, timedelta
from fractions import Fraction
from .product import _key, _report, _envelope, _rational, archive_digest, _wire
from .planner_loop import fulfil_fifo


def compare(catalog, cutoff, sku_id, warehouse_id, quantity=None, delay_days=0, *,
            supplier=None, order_minute=540, deliveries=None):
    binding,key=_key(catalog,cutoff,sku_id,warehouse_id)
    report=_report(catalog,key['plan_run_id']); result=report['result']
    if type(delay_days) is not int or not 0<=delay_days<=3: raise ValueError('delay must be 0–3 full days')
    if quantity is not None and (type(quantity) is not int or not 0<=quantity<=2000): raise ValueError('quantity must be 0–2000 exact pieces')
    constrained=supplier is not None
    if deliveries is not None and not constrained:raise ValueError('Supplier promise required for partial receipt scenarios')
    if constrained and delay_days:raise ValueError('Use declared receipt scenarios with supplier feasibility')
    version='supplier-one-review-contrast-v1' if constrained else 'one-review-contrast-v1'
    envelope=_envelope(catalog,binding)|dict(contract_version=version,source_run_id=report['run_id'],
        input_digest=report['input_digest'],scored_days=28,common_days=33,rates=dict(purchase='2',holding='1',backlog='10',setup='2'),
        semantics='One saved actual prefix proposal with FIFO execution; no later reviews/orders. Distinct from the periodic simulator and repeated actual-planner study.',
        limitations=['Declared future synthetic demand, not observed outcomes.','Nominal lead/pack/MOQ only; supplier calendar/capacity feasibility unverified.','All stock and confirmed inbound paid; terminal backlog retained, no salvage.'])
    if constrained:
        envelope['supplier_profile']=supplier
        envelope['limitations'][1]='Source-bound declared synthetic calendar/capacity; receipt scenarios are assumed outcomes, not executed orders.'
    if report['status']!='assessable': return envelope|dict(status='not_assessable',reasons=result['reasons'],arms=None)
    policy=result['supply']['policy'];lead=policy['lead_days']
    if quantity and (quantity<policy['moq'] or quantity%policy['pack_size']): raise ValueError('alternative violates saved MOQ or pack constraint')
    proposal=result['proposed_order_qty']
    if proposal>2000 or (not constrained and lead+delay_days>=33): return envelope|dict(status='not_assessable',reasons=['outside_execution_envelope'],arms=None)
    origin=date.fromisoformat(cutoff)
    inbound=[r for r in result['supply']['inbound'] if r['status']=='confirmed' and r['remaining_qty']]
    reservations=[r for r in result['supply']['reservations'] if r['status']=='open' and r['remaining_qty']]
    if any(not 0<=(date.fromisoformat(r[field])-origin).days<33 for rows,field in ((inbound,'arrival_day'),(reservations,'due_day')) for r in rows):
        return envelope|dict(status='not_assessable',reasons=['source_outside_common_window'],arms=None)
    demand=key['future_demand']['quantities'];accepted=sum(demand)
    def execute(order, delay, schedule=None):
        schedule=[(lead+delay,order)] if schedule is None else schedule
        stock=result['inventory']['on_hand'];queue=[];days=[];immediate=eventual=0
        costs=dict(purchase=2*(stock+sum(r['remaining_qty'] for r in inbound)+order),holding=0,backlog=0,setup=2*(len(inbound)+int(order>0)))
        for day in range(33):
            receipts=sum(r['remaining_qty'] for r in inbound if (date.fromisoformat(r['arrival_day'])-origin).days==day)+sum(q for d,q in schedule if day==d)
            stock+=receipts
            for r in reservations:
                if (date.fromisoformat(r['due_day'])-origin).days==day:
                    queue.append(dict(id='reservation:'+r['reservation_id'],day=day,kind='reservation',remaining=r['remaining_qty']))
            amount=demand[day] if day<28 else 0
            if amount:queue.append(dict(id='demand:'+str(day),day=day,kind='demand',remaining=amount))
            kinds={r['id']:r['kind'] for r in queue}
            stock,queue,filled,new_filled,_=fulfil_fifo(stock,queue,day)
            immediate+=new_filled;eventual+=sum(f['quantity'] for f in filled if kinds[f['acceptance_id']]=='demand')
            backlog=sum(r['remaining'] for r in queue)
            costs['holding']+=stock;costs['backlog']+=10*backlog
            days.append(dict(day=str(day),receipts=str(receipts),accepted=str(amount),fulfilled=_wire(filled),end_stock=str(stock),end_backlog=str(backlog)))
        return dict(quantity=str(order),arrival_day=str(schedule[0][0]) if order else None,
            accepted=str(accepted),immediate_fulfilled=str(immediate),eventual_fulfilled=str(eventual),
            immediate_fill=_rational(Fraction(immediate,accepted)) if accepted else None,eventual_fill=_rational(Fraction(eventual,accepted)) if accepted else None,
            terminal_stock=str(stock),terminal_backlog=str(backlog),cost_components={k:str(v) for k,v in costs.items()},total_cost=str(sum(costs.values())),days=days)
    orders=dict(actual_proposal=proposal,no_action=0)
    if quantity is not None:orders['alternative']=quantity
    if deliveries is not None and (not isinstance(deliveries,dict) or set(deliveries)-set(orders)):
        raise ValueError('Receipt scenario names must match compared arms')
    arms={}
    for name,order in orders.items():
        if not constrained:
            arms[name]=execute(order,delay_days if order else 0)
            continue
        from .supplier_feasibility import promise,receipt_schedule
        feasible=promise(supplier,cutoff,sku_id,warehouse_id,order,lead,order_minute)
        if feasible['status']!='feasible':
            arms[name]=dict(quantity=str(order),feasibility=feasible,status='not_assessable',total_cost=None,
                            immediate_fill=None,eventual_fill=None,terminal_stock=None,terminal_backlog=None,days=None)
            continue
        schedule=receipt_schedule(feasible,cutoff,order,(deliveries or {}).get(name))
        if any((origin+timedelta(days=d)).weekday() not in supplier['receipt_weekdays'] for d,_ in schedule):
            raise ValueError('Declared receipt violates supplier receiving calendar')
        arms[name]=execute(order,0,schedule)|dict(status='assessable',feasibility=feasible,
            receipt_scenario=[dict(arrival_day=str(d),quantity=str(q)) for d,q in schedule])
    identity=dict(input_digest=report['input_digest'],future=demand,quantity=quantity,delay=delay_days,contract=version)
    if constrained:identity.update(supplier=supplier,order_minute=order_minute,deliveries=deliveries)
    return envelope|dict(status='assessable',reasons=[],calculation_id=archive_digest(identity,False),arms=arms)
