"""Bounded synthetic execution of actual persisted planner proposals, never real orders."""
from copy import deepcopy
from datetime import date, timedelta
from fractions import Fraction
import hashlib
import json

from psycopg import sql
from psycopg.rows import dict_row

from .copilot_planning import _validate, load_planning_run
from .demand import BUSINESS_TIMEZONE, midnight
from .planning_runs import exact_json
from .reliability import run_checks
from .replenishment import run_plan
from .forecasting import METHODS

START = date(2026, 3, 7)
POLICIES = ('actual', 'do-nothing', 'fixed-18')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def fulfil_fifo(stock, backlog, day):
    """Shared physical execution step; callers supply accepted obligations."""
    fulfilled=[]; new_filled=0; total=0
    for row in backlog:
        quantity=min(stock,row['remaining'])
        if quantity:
            stock-=quantity;row['remaining']-=quantity;total+=quantity
            new_filled+=quantity if row['day']==day and row.get('kind','demand')=='demand' else 0
            fulfilled.append(dict(acceptance_id=row['id'],accepted_day=row['day'],quantity=quantity))
    return stock,[row for row in backlog if row['remaining']],fulfilled,new_filled,total


class Admission:
    """One-process research admission; durable workflow is a separate contract."""
    def __init__(self):
        self.decisions = {}

    def admit(self, identity, report, context, policy='actual'):
        _validate(report)
        if policy not in POLICIES or report['kind'] != 'replenishment' or report['context'] != context:
            raise ValueError('Wrong decision context or policy')
        result = report['result']
        inputs = {key: result[key] for key in ('inventory', 'supply', 'training')}
        if report['input_digest'] != digest(dict(context=context, inputs=inputs)):
            raise ValueError('Contradictory source digest')
        if context['origin'] != midnight(date.fromisoformat(context['origin_day'])).isoformat():
            raise ValueError('Wrong decision origin')
        proposal = result['proposed_order_qty']
        if proposal is not None and (type(proposal) is not int or proposal < 0):
            raise ValueError('Noninteger proposal')
        quantity = (proposal if policy == 'actual' else 0 if policy == 'do-nothing'
                    else 18) if report['status'] == 'assessable' else None
        decision = dict(id=identity, context=deepcopy(context), input_digest=report['input_digest'],
                        proposal=proposal, quantity=quantity, policy=policy, status=report['status'])
        if identity in self.decisions:
            if decision != self.decisions[identity]:
                raise ValueError('Conflicting repeated decision')
            return deepcopy(decision), False
        self.decisions[identity] = decision
        return deepcopy(decision), True


def _insert(conn, schema, table, rows):
    if not rows:
        return
    keys = list(rows[0])
    statement = sql.SQL('INSERT INTO {}.{} ({}) VALUES ({})').format(
        sql.Identifier(schema), sql.Identifier(table), sql.SQL(',').join(map(sql.Identifier, keys)),
        sql.SQL(',').join(sql.Placeholder() for _ in keys))
    with conn.cursor() as cursor:
        cursor.executemany(statement, [[row[key] for key in keys] for row in rows])


def publish(owner, *, namespace, day, initial_stock, stock, movements, observations,
            backlog, orders, missing=False):
    """Insert a fresh immutable source archive. Hidden physical ETA never enters it."""
    origin, stem = midnight(START+timedelta(days=day)), f'{namespace}:day-{day}'
    fields = dict(sku_id=namespace+':sku', warehouse_id=namespace+':warehouse')
    ledger, snapshot, demand, supply = (stem+':'+name for name in ('ledger','snapshot','demand','supply'))
    inventory = dict(batches=[], coverage=[], opening_balances=[], movements=[], snapshots=[])
    baseline = midnight(START-timedelta(days=1))
    for kind, batch in (('ledger',ledger), ('snapshot',snapshot)):
        inventory['batches'].append(dict(batch_id=batch,kind=kind,status='complete',as_of=origin,
            baseline_at=baseline if kind=='ledger' else None,watermark=len(movements),
            observed_at=origin,expected_row_count=len(movements) if kind=='ledger' else 1))
        inventory['coverage'].append(dict(row_id=batch+':coverage',batch_id=batch,**fields))
    inventory['opening_balances'].append(dict(row_id=ledger+':opening',batch_id=ledger,**fields,
        quantity=initial_stock,as_of=baseline,baseline_ref='paid synthetic initial stock'))
    inventory['snapshots'].append(dict(row_id=snapshot+':stock',batch_id=snapshot,**fields,
        on_hand_qty=stock,as_of=origin,watermark=len(movements),observed_at=origin))
    for seq, event in enumerate(movements, 1):
        clock = midnight(START+timedelta(days=event['day']))+timedelta(hours=event['hour'])
        inventory['movements'].append(dict(row_id=f'{ledger}:event-{seq}',batch_id=ledger,
            source_system='synthetic-loop',event_id=event['id'],document_id=event['id'],document_line_id='1',
            leg_id='1',**fields,quantity=event['quantity'],movement_type=event['type'],posting_status='posted',
            effective_at=clock,source_recorded_at=clock,source_seq=seq,observed_at=clock,
            transfer_id=None,reversal_of_row_id=None,reason='synthetic physical execution'))
    planning = dict(demand_batches=[], day_observations=[], order_versions=[], supply_batches=[],
                    policies=[], reservations=[], inbound=[])
    for index, observation in enumerate(observations):
        business_day = START+timedelta(days=index-28)
        known = midnight(business_day+timedelta(days=1))
        planning['day_observations'].append(dict(row_id=f'{demand}:day-{index}',batch_id=demand,**fields,
            business_day=business_day,revision=1,source_recorded_at=known,observed_at=known,
            coverage='complete',availability=observation['availability'],expected_lines=int(observation['quantity']>0)))
        if observation['quantity']:
            planning['order_versions'].append(dict(row_id=f'{demand}:order-{index}',batch_id=demand,**fields,
                source_system='synthetic-accepted',order_id=f'{namespace}:accepted-{index-28}',line_id='1',revision=1,
                accepted_at=midnight(business_day)+timedelta(hours=12),source_recorded_at=known,
                observed_at=known,accepted_qty=observation['quantity'],status='accepted'))
    planning['demand_batches'].append(dict(batch_id=demand,version_id='planner-loop-demand-v1',
        business_timezone=BUSINESS_TIMEZONE,start_day=START-timedelta(days=28),end_day=START+timedelta(days=day),
        assembled_at=origin,status='complete',expected_orders=len(planning['order_versions']),
        expected_days=len(planning['day_observations'])))
    planning['reservations'] = [dict(row_id=f'{supply}:reservation-{i}',batch_id=supply,
        source_system='synthetic-accepted',reservation_id=row['id'],remaining_qty=row['remaining'],
        due_day=START+timedelta(days=row['day']),status='open',source_recorded_at=origin,observed_at=origin)
        for i,row in enumerate(backlog)]
    planning['inbound'] = [dict(row_id=f'{supply}:inbound-{i}',batch_id=supply,
        source_system='synthetic-loop',inbound_id=row['id'],remaining_qty=row['quantity'],
        arrival_day=START+timedelta(days=row['eta']),status='confirmed',
        source_recorded_at=origin,observed_at=origin) for i,row in enumerate(orders) if not row['received']]
    planning['supply_batches'].append(dict(batch_id=supply,version_id='planner-loop-supply-v1',**fields,
        as_of=origin,observed_at=origin,status='complete',reservations_complete=True,inbound_complete=not missing,
        expected_reservations=len(planning['reservations']),expected_inbound=len(planning['inbound'])))
    planning['policies'].append(dict(row_id=supply+':policy',batch_id=supply,lead_days=2,review_days=3,
        safety_qty=2,pack_size=6,moq=10,source_recorded_at=origin,observed_at=origin))
    with owner.transaction():
        for schema, tables in (('operational_fixture', inventory), ('planning_input', planning)):
            for table, rows in tables.items():
                _insert(owner, schema, table, rows)
    sources = exact_json(dict(inventory=inventory, planning=planning))
    return dict(ledger_batch_id=ledger,snapshot_batch_id=snapshot,batch_id=demand,supply_batch_id=supply,
                **fields), sources


def run_case(owner, runner, *, namespace, demand, initial_stock=10, history=None,
             first_order_delay=0, notification=True, missing_day_zero=False, policy='actual',
             code_version='planner-loop-v1', method='mean'):
    """Nine scored days plus five common closure days; owner and runner are separate."""
    if (len(demand)!=9 or any(type(q) is not int or q<0 for q in demand)
            or type(initial_stock) is not int or initial_stock<0
            or type(first_order_delay) is not int or first_order_delay not in range(4)
            or type(notification) is not bool or type(missing_day_zero) is not bool or policy not in POLICIES
            or method not in METHODS):
        raise ValueError('Outside frozen execution envelope')
    history = [3]*28 if history is None else list(history)
    if len(history)!=28 or any(type(q) is not int or q<0 for q in history):
        raise ValueError('Exactly 28 complete historical days required')
    fields = dict(sku_id=namespace+':sku',warehouse_id=namespace+':warehouse')
    with owner.transaction():
        _insert(owner,'operational_fixture','styles',[dict(style_id=namespace+':style',style_code='LOOP',name='Synthetic Loop')])
        _insert(owner,'operational_fixture','skus',[dict(sku_id=fields['sku_id'],style_id=namespace+':style',
            sku_code='LOOP',color='Ink',size='M',base_uom='each')])
        _insert(owner,'operational_fixture','warehouses',[dict(warehouse_id=fields['warehouse_id'],warehouse_code='LOOP',name='Synthetic Loop')])
    observations = [dict(quantity=q,availability='available') for q in history]
    stock, backlog, orders, movements, days, reviews, sources = initial_stock, [], [], [], [], [], []
    admission = Admission()
    costs = dict(purchase=initial_stock*2,holding=0,backlog=0,setup=0)
    score_cost = initial_stock*2
    immediate = eventual = 0
    for day in range(14):
        receipts, notifications, executions = [], [], []
        for order in orders:
            if not order['received'] and day==order['actual_day']:
                order['received']=True
                stock+=order['quantity']
                receipts.append(dict(order_id=order['id'],quantity=order['quantity']))
                movements.append(dict(id=order['id']+':receipt',day=day,hour=0,quantity=order['quantity'],type='receipt'))
            elif not order['received'] and day==order['promise_day'] and notification:
                order['eta']=order['actual_day']
                notifications.append(dict(order_id=order['id'],known_day=day,revised_eta=order['eta']))
        daily_cost = dict(purchase=0,holding=0,backlog=0,setup=0)
        if day in (0,3,6):
            identifiers, source = publish(owner,namespace=namespace,day=day,initial_stock=initial_stock,
                stock=stock,movements=movements,observations=observations,backlog=backlog,orders=orders,
                missing=missing_day_zero and day==0)
            origin_day=START+timedelta(days=day)
            reliability=run_checks(runner,**{key:identifiers[key] for key in ('ledger_batch_id','snapshot_batch_id')},
                as_of=midnight(origin_day),evaluated_at=midnight(origin_day),code_version=code_version)
            if reliability['overall_status']!='pass':
                raise ValueError('Physical state failed real SQL reconciliation')
            report=run_plan(runner,**{key:identifiers[key] for key in ('batch_id','supply_batch_id','sku_id','warehouse_id')},
                reliability_run_id=reliability['run_id'],start_day=origin_day-timedelta(days=28),
                origin_day=origin_day,method=method,code_version=code_version)
            saved=load_planning_run(runner,report['run_id'])
            if saved!=report:
                raise ValueError('Persisted planner report changed')
            decision, fresh=admission.admit(f'{namespace}:review-{day}',saved,saved['context'],policy)
            if not fresh:
                raise ValueError('Unexpected repeated review')
            reviews.append(dict(day=day,reliability=reliability,report=saved,decision=decision,
                                source_digest=digest(source)))
            sources.append(source)
            if decision['quantity']:
                quantity=decision['quantity']; identity=decision['id']+':order'
                delay=first_order_delay if not orders else 0
                orders.append(dict(id=identity,quantity=quantity,promise_day=day+2,eta=day+2,
                                   actual_day=day+2+delay,received=False))
                executions.append(dict(order_id=identity,quantity=quantity,promise_day=day+2))
                daily_cost.update(purchase=quantity*2,setup=2)
        accepted = demand[day] if day<9 else 0
        if accepted:
            backlog.append(dict(id=f'{namespace}:accepted-{day}',day=day,remaining=accepted))
        stock,backlog,fulfilled,new_filled,total=fulfil_fifo(stock,backlog,day)
        eventual+=total
        for row in fulfilled:
            movements.append(dict(id=f'{row["acceptance_id"]}:shipment-{day}',day=day,hour=12,quantity=-row['quantity'],type='shipment'))
        immediate+=new_filled
        end_backlog=sum(row['remaining'] for row in backlog)
        if day<9:
            observations.append(dict(quantity=accepted,availability='stockout' if new_filled<accepted else 'available'))
        daily_cost.update(holding=stock,backlog=end_backlog*10)
        for key, value in daily_cost.items():costs[key]+=value
        if day<9:score_cost+=sum(daily_cost.values())
        days.append(dict(day=day,date=(START+timedelta(days=day)).isoformat(),phase='score' if day<9 else 'closure',
            receipts=receipts,notifications=notifications,executions=executions,accepted=accepted,
            fulfilled=fulfilled,new_filled=new_filled,end_stock=stock,end_backlog=end_backlog,cost=daily_cost))
    # Prove earlier database rows stayed immutable, not just copied archive dictionaries.
    with owner.cursor(row_factory=dict_row) as cur:
        for source in sources:
            for schema, tables in (('operational_fixture',source['inventory']),('planning_input',source['planning'])):
                for table, rows in tables.items():
                    for row in rows:
                        key='row_id' if 'row_id' in row else 'batch_id'
                        current=cur.execute(sql.SQL('SELECT * FROM {}.{} WHERE {}=%s').format(
                            sql.Identifier(schema),sql.Identifier(table),sql.Identifier(key)),(row[key],)).fetchone()
                        if exact_json(current)!=row:raise ValueError('Earlier source row mutated')
    accepted=sum(demand)
    result=dict(namespace=namespace,policy=policy,initial_stock=initial_stock,history=history,demand=list(demand),
        first_order_delay=first_order_delay,notification=notification,missing_day_zero=missing_day_zero,
        days=days,reviews=reviews,sources=sources,movements=movements,orders=orders,
        summary=dict(proposals=[r['decision']['proposal'] for r in reviews],accepted=accepted,
            immediate_fulfilled=immediate,eventual_fulfilled=eventual,
            immediate_fill=str(Fraction(immediate,accepted)) if accepted else None,
            eventual_fill=str(Fraction(eventual,accepted)) if accepted else None,
            terminal_stock=stock,terminal_backlog=sum(row['remaining'] for row in backlog),
            cost_components=costs,total_cost=sum(costs.values()),score_cost=score_cost,
            closure_cost=sum(costs.values())-score_cost))
    if method != 'mean':
        result['method'] = method
    return exact_json(result)
