"""Independent saved-event arithmetic. No database, planner, forecast or simulator calls."""
from datetime import date, datetime, timedelta, time, timezone
from fractions import Fraction
import hashlib
import json
from zoneinfo import ZoneInfo


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',', ':'),allow_nan=False).encode()).hexdigest()


def _midnight(day):
    return datetime.combine(day,time(),ZoneInfo('America/Los_Angeles')).astimezone(timezone.utc).isoformat()


def _clock(value):
    parsed=datetime.fromisoformat(value)
    _require(parsed.tzinfo is not None and parsed.utcoffset()==timedelta(0), 'Source knowledge must be canonical UTC')
    return parsed


def audit_case(case, manual=None):
    """Recompute FIFO, stock, purchase/holding/backlog/setup and service denominators."""
    start=date(2026,3,7)
    _require(len(case['days'])==14 and [r['day'] for r in case['reviews']]==[0,3,6], 'Wrong common window')
    _require(len(case['sources'])==3 and len(case['demand'])==9, 'Incomplete archive')
    stock=case['initial_stock']; open_orders={}; queue=[]; ordered=received=filled=immediate=accepted=0
    costs=dict(purchase=stock*2,holding=0,backlog=0,setup=0); score=stock*2
    proposals=[]
    for day,row in enumerate(case['days']):
        _require(row['day']==day and row['date']==(start+timedelta(days=day)).isoformat()
                 and row['phase']==('score' if day<9 else 'closure'), 'Wrong daily clock')
        _require(row['accepted']==(case['demand'][day] if day<9 else 0), 'Changed exogenous demand')
        _require(all(type(row[k]) is int and row[k]>=0 for k in ('accepted','new_filled','end_stock','end_backlog')),
                 'Physical quantities must be whole pieces')
        for receipt in row['receipts']:
            order=open_orders.get(receipt['order_id'])
            _require(order is not None and receipt['quantity']==order['quantity'], 'Unknown/partial/duplicate receipt')
            expected_delay=case['first_order_delay'] if order['ordinal']==0 else 0
            _require(day==order['promise_day']+expected_delay, 'Changed hidden schedule')
            stock+=receipt['quantity'];received+=receipt['quantity'];del open_orders[receipt['order_id']]
        for notice in row['notifications']:
            order=open_orders.get(notice['order_id'])
            _require(case['notification'] and order is not None and day==order['promise_day']
                     and notice['known_day']==day and notice['revised_eta']==day+case['first_order_delay'], 'Invalid notification')
            order['eta']=notice['revised_eta']
        if day in (0,3,6):
            review=case['reviews'][day//3];source=case['sources'][day//3]
            report=review['report'];context=report['context'];result=report['result'];decision=review['decision']
            _require(review['source_digest']==_hash(source), 'Changed source digest')
            _require(review['reliability']['overall_status']=='pass', 'Untrusted inventory')
            _require(context['origin_day']==row['date'] and context['origin']==_midnight(start+timedelta(days=day))
                     and context['start_day']==(start+timedelta(days=day-28)).isoformat()
                     and context['method']==case.get('method','mean')
                     and context['method'] in ('mean','naive','seasonal_naive')
                     and context['business_timezone']=='America/Los_Angeles', 'Wrong review binding')
            inputs={key:result[key] for key in ('inventory','supply','training')}
            _require(report['input_digest']==_hash(dict(context=context,inputs=inputs)), 'Changed persisted source inputs')
            inventory=source['inventory'];planning=source['planning']
            _require(inventory==result['inventory']['source'], 'Inventory source mismatch')
            _require(len(inventory['snapshots'])==1 and inventory['snapshots'][0]['on_hand_qty']==stock, 'Physical snapshot mismatch')
            _require(inventory['opening_balances'][0]['quantity']==case['initial_stock'], 'Unpaid opening stock')
            _require(sum(m['quantity'] for m in inventory['movements'])+case['initial_stock']==stock, 'Ledger conservation failure')
            _require(context['reliability_run_id']==review['reliability']['run_id']
                     and str(result['inventory']['run']['run_id'])==review['reliability']['run_id'], 'Wrong reliability identity')
            _require(context['batch_id']==planning['demand_batches'][0]['batch_id']
                     and context['supply_batch_id']==planning['supply_batches'][0]['batch_id']
                     and inventory['batches'][0]['batch_id']==review['reliability']['ledger_batch_id']
                     and inventory['batches'][1]['batch_id']==review['reliability']['snapshot_batch_id'], 'Wrong source batch binding')
            expected_quantities=case['history']+case['demand'][:day]
            _require(len(planning['day_observations'])==len(expected_quantities), 'Missing completed evidence')
            for index,(observation,amount) in enumerate(zip(planning['day_observations'],expected_quantities)):
                local_day=(start+timedelta(days=index-28)).isoformat()
                orders=[r for r in planning['order_versions'] if r['accepted_at'][:10]==local_day]
                availability='available' if index<28 or case['days'][index-28]['new_filled']==amount else 'stockout'
                _require(observation['business_day']==local_day and observation['availability']==availability
                         and observation['expected_lines']==int(amount>0) and len(orders)==int(amount>0)
                         and sum(r['accepted_qty'] for r in orders)==amount, 'Accepted/history evidence changed')
                _require(all((r['sku_id'],r['warehouse_id'])==(context['sku_id'],context['warehouse_id'])
                             for r in [observation,*orders]), 'Wrong source key')
            for records in (planning['order_versions'],planning['day_observations'],
                            planning['inbound'],planning['reservations'],inventory['movements']):
                for record in records:
                    _require(all(_clock(record.get(clock,context['origin']))<=_clock(context['origin'])
                                 for clock in ('source_recorded_at','observed_at')), 'Future knowledge leakage')
            _require(all(r['business_day']<row['date'] for r in planning['day_observations']), 'Future demand leakage')
            supply=result['supply']
            _require(supply['batch']==planning['supply_batches'][0]
                     and supply['reservations']==planning['reservations'] and supply['inbound']==planning['inbound']
                     and supply['policy']==planning['policies'][0], 'Supply source mismatch')
            _require({k:supply['policy'][k] for k in ('lead_days','review_days','safety_qty','pack_size','moq')}==
                     dict(lead_days=2,review_days=3,safety_qty=2,pack_size=6,moq=10), 'Frozen planning policy changed')
            _require({r['reservation_id']:(r['remaining_qty'],r['due_day']) for r in supply['reservations']}==
                     {q['id']:(q['remaining'],(start+timedelta(days=q['day'])).isoformat()) for q in queue}, 'Backlog identity/date loss')
            _require({r['inbound_id']:(r['remaining_qty'],r['arrival_day']) for r in supply['inbound']}==
                {k:(v['quantity'],(start+timedelta(days=v['eta'])).isoformat()) for k,v in open_orders.items()}, 'Promise/physical information boundary failure')
            expected_days=planning['day_observations'][-28:]
            _require(len(expected_days)==28 and [r['day_record'] for r in result['training']['days']]==expected_days, 'Wrong rolling history')
            supply_missing=case['missing_day_zero'] and day==0
            blocked=(supply_missing or any(r['availability']!='available' for r in expected_days)
                     or any(q['day']<day for q in queue) or any(o['eta']<day for o in open_orders.values()))
            _require(report['status']==('not_assessable' if blocked else 'assessable'), 'Blocked gate changed')
            proposal=result['proposed_order_qty'];proposals.append(proposal)
            if blocked:
                _require(proposal is None and result['projection'] is None and result['reasons'], 'Blocked is not zero')
            else:
                train=result['training']['days']
                _require(all(type(r['quantity']) is int and r['quantity']>=0 for r in train), 'Invalid exact training')
                values=[r['quantity'] for r in train]
                predictions=([Fraction(sum(values),28)]*5 if context['method']=='mean' else
                    [Fraction(values[-1])]*5 if context['method']=='naive' else
                    [Fraction(values[-7+i]) for i in range(5)])
                _require(result['forecast']['predictions']==list(map(str,predictions)), 'Forecast differs from independent baseline')
                balance=Fraction(stock); deficits=[]
                for i in range(5):
                    current=(start+timedelta(days=day+i)).isoformat()
                    inbound=sum(o['quantity'] for o in open_orders.values() if o['eta']==day+i)
                    reserved=sum(q['remaining'] for q in queue if q['day']==day+i)
                    balance+=inbound-reserved-predictions[i]
                    projection=result['projection'][i]
                    _require(projection['day']==current and Fraction(projection['balance_without_order'])==balance
                             and projection['inbound']==inbound and projection['reservations']==reserved, 'Independent projection mismatch')
                    if i>=2:deficits.append(Fraction(2)-balance)
                need=max([Fraction(0),*deficits]);whole=-(-need.numerator//need.denominator)
                expected=((max(whole,10)+5)//6)*6 if whole else 0
                _require(type(proposal) is int and proposal==expected, 'Independent proposal mismatch')
                _require(all(Fraction(p['balance_with_order'])==Fraction(p['balance_without_order'])+(expected if i>=2 else 0)
                             for i,p in enumerate(result['projection'])), 'Wrong with-order projection')
            quantity=(proposal if case['policy']=='actual' else 0 if case['policy']=='do-nothing' else 18) if not blocked else None
            _require(decision['quantity']==quantity and decision['proposal']==proposal and decision['context']==context
                     and decision['input_digest']==report['input_digest'] and decision['id']==case['namespace']+f':review-{day}'
                     and decision['policy']==case['policy'], 'Decision identity/quantity mismatch')
            _require(len(row['executions'])==int(bool(quantity)), 'Incorrect admission count')
        else:
            _require(not row['executions'], 'Order outside scored reviews')
        daily=dict(purchase=0,holding=0,backlog=0,setup=0)
        for order in row['executions']:
            _require(order['order_id'] not in open_orders and order['quantity']==quantity and order['promise_day']==day+2, 'Wrong order execution')
            open_orders[order['order_id']]=order|dict(ordinal=costs['setup']//2,eta=order['promise_day'])
            ordered+=order['quantity'];daily.update(purchase=order['quantity']*2,setup=2)
        accepted+=row['accepted']
        if row['accepted']:queue.append(dict(id=case['namespace']+f':accepted-{day}',day=day,remaining=row['accepted']))
        fulfilments=[];new=0
        for q in queue:
            amount=min(stock,q['remaining']);stock-=amount;q['remaining']-=amount;filled+=amount
            if amount:
                fulfilments.append(dict(acceptance_id=q['id'],accepted_day=q['day'],quantity=amount))
                if q['day']==day:new+=amount
        queue=[q for q in queue if q['remaining']];debt=sum(q['remaining'] for q in queue)
        _require(row['fulfilled']==fulfilments and row['new_filled']==new, 'FIFO/new fill mismatch')
        immediate+=new
        _require(row['end_stock']==stock and row['end_backlog']==debt
                 and case['initial_stock']+received-filled==stock and accepted-filled==debt, 'Physical conservation failure')
        daily.update(holding=stock,backlog=debt*10)
        _require(row['cost']==daily, 'Daily cost mismatch')
        for key,value in daily.items():costs[key]+=value
        if day<9:score+=sum(daily.values())
    _require(not open_orders and received==ordered, 'Unsettled admitted orders')
    summary=dict(proposals=proposals,accepted=accepted,immediate_fulfilled=immediate,eventual_fulfilled=filled,
        immediate_fill=str(Fraction(immediate,accepted)) if accepted else None,
        eventual_fill=str(Fraction(filled,accepted)) if accepted else None,terminal_stock=stock,terminal_backlog=debt,
        cost_components=costs,total_cost=sum(costs.values()),score_cost=score,closure_cost=sum(costs.values())-score)
    _require(case['summary']==summary, 'Summary/service/cost mismatch')
    if manual is not None:
        observed=summary|dict(score_end_stock=[r['end_stock'] for r in case['days'][:9]],
                              score_end_backlog=[r['end_backlog'] for r in case['days'][:9]])
        _require(all(observed[key]==value for key,value in manual.items()), 'Frozen manual outcome mismatch')
    return summary


def audit_archive(archive, expectations, stress):
    _require(archive['version']=='planner-loop-evidence-v1' and archive['synthetic_only'] is True, 'Wrong archive contract')
    _require(set(archive['manual'])==set(expectations), 'Missing manual controls')
    for name,case in archive['manual'].items():audit_case(case,expectations[name])
    _require(set(archive['stress'])=={r['id'] for r in stress['traces']}, 'Incomplete paired grid')
    for trace in stress['traces']:
        cells=archive['stress'][trace['id']]
        _require(set(cells)==set(stress['policies']), 'Missing policy cell')
        for policy,case in cells.items():
            _require(case['policy']==policy and case['demand']==trace['demand']
                     and case['history']==stress['history'] and case['initial_stock']==stress['initial_stock']
                     and case['first_order_delay']==trace['first_order_delay']
                     and case['notification']==trace['notification'] and case['missing_day_zero']==trace['missing_day_zero'], 'Unpaired physical trace')
            audit_case(case)
    return dict(status='pass',manual_controls=len(expectations),paired_traces=len(stress['traces']),
                paired_policy_cells=sum(len(c) for c in archive['stress'].values()),
                reviews=sum(len(c['reviews']) for c in archive['manual'].values())+
                    sum(len(c['reviews']) for cells in archive['stress'].values() for c in cells.values()))
