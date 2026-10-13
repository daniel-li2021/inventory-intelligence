"""A bounded single saved-planner review, with common paid execution windows."""
from datetime import date
from fractions import Fraction
from .product import _key, _report, _envelope, _rational, archive_digest, _wire
from .planner_loop import fulfil_fifo


def compare(catalog, cutoff, sku_id, warehouse_id, quantity=None, delay_days=0):
    binding,key=_key(catalog,cutoff,sku_id,warehouse_id)
    report=_report(catalog,key['plan_run_id']); result=report['result']
    if type(delay_days) is not int or not 0<=delay_days<=3: raise ValueError('delay must be 0–3 full days')
    if quantity is not None and (type(quantity) is not int or not 0<=quantity<=2000): raise ValueError('quantity must be 0–2000 exact pieces')
    envelope=_envelope(catalog,binding)|dict(contract_version='one-review-contrast-v1',source_run_id=report['run_id'],
        input_digest=report['input_digest'],scored_days=28,common_days=33,rates=dict(purchase='2',holding='1',backlog='10',setup='2'),
        semantics='One saved actual prefix proposal with FIFO execution; no later reviews/orders. Distinct from the periodic simulator and repeated actual-planner study.',
        limitations=['Declared future synthetic demand, not observed outcomes.','Nominal lead/pack/MOQ only; supplier calendar/capacity feasibility unverified.','All stock and confirmed inbound paid; terminal backlog retained, no salvage.'])
    if report['status']!='assessable': return envelope|dict(status='not_assessable',reasons=result['reasons'],arms=None)
    policy=result['supply']['policy'];lead=policy['lead_days']
    if quantity and (quantity<policy['moq'] or quantity%policy['pack_size']): raise ValueError('alternative violates saved MOQ or pack constraint')
    proposal=result['proposed_order_qty']
    if proposal>2000 or lead+delay_days>=33: return envelope|dict(status='not_assessable',reasons=['outside_execution_envelope'],arms=None)
    origin=date.fromisoformat(cutoff)
    inbound=[r for r in result['supply']['inbound'] if r['status']=='confirmed' and r['remaining_qty']]
    reservations=[r for r in result['supply']['reservations'] if r['status']=='open' and r['remaining_qty']]
    if any(not 0<=(date.fromisoformat(r[field])-origin).days<33 for rows,field in ((inbound,'arrival_day'),(reservations,'due_day')) for r in rows):
        return envelope|dict(status='not_assessable',reasons=['source_outside_common_window'],arms=None)
    demand=key['future_demand']['quantities'];accepted=sum(demand)
    def execute(order, delay):
        stock=result['inventory']['on_hand'];queue=[];days=[];immediate=eventual=0
        costs=dict(purchase=2*(stock+sum(r['remaining_qty'] for r in inbound)+order),holding=0,backlog=0,setup=2*(len(inbound)+int(order>0)))
        for day in range(33):
            receipts=sum(r['remaining_qty'] for r in inbound if (date.fromisoformat(r['arrival_day'])-origin).days==day)+(order if day==lead+delay else 0)
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
        return dict(quantity=str(order),arrival_day=str(lead+delay) if order else None,
            accepted=str(accepted),immediate_fulfilled=str(immediate),eventual_fulfilled=str(eventual),
            immediate_fill=_rational(Fraction(immediate,accepted)) if accepted else None,eventual_fill=_rational(Fraction(eventual,accepted)) if accepted else None,
            terminal_stock=str(stock),terminal_backlog=str(backlog),cost_components={k:str(v) for k,v in costs.items()},total_cost=str(sum(costs.values())),days=days)
    arms=dict(actual_proposal=execute(proposal,delay_days),no_action=execute(0,0))
    if quantity is not None:arms['alternative']=execute(quantity,delay_days)
    return envelope|dict(status='assessable',reasons=[],calculation_id=archive_digest(dict(input_digest=report['input_digest'],future=demand,quantity=quantity,delay=delay_days,contract='one-review-contrast-v1'),False),arms=arms)
