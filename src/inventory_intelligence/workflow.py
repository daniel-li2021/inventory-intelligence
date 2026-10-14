"""Local synthetic commitment journal; no operational tables or real purchases."""
from datetime import date
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3

from .planner_loop import digest
from .planner_loop_audit import audit_case


def _day(value):
    if not isinstance(value,str) or date.fromisoformat(value).isoformat()!=value:
        raise ValueError('Exact ISO business date required')
    return value


class Journal:
    """SQLite atomic append and idempotency for one configured local synthetic sandbox."""
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self._connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY, binding TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL,
                    decision_id TEXT NOT NULL REFERENCES decisions(id), kind TEXT NOT NULL,
                    known_day TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS immutable_decisions_update BEFORE UPDATE ON decisions BEGIN
                    SELECT RAISE(ABORT, 'immutable decision'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_decisions_delete BEFORE DELETE ON decisions BEGIN
                    SELECT RAISE(ABORT, 'immutable decision'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_events_update BEFORE UPDATE ON events BEGIN
                    SELECT RAISE(ABORT, 'immutable event'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_events_delete BEFORE DELETE ON events BEGIN
                    SELECT RAISE(ABORT, 'immutable event'); END;
            ''')

    @contextmanager
    def _connection(self):
        conn=sqlite3.connect(self.path,timeout=5)
        conn.row_factory=sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def admit(self,case,day):
        audit_case(case)
        if case['policy']!='actual' or type(day) is not int or day not in (0,3,6):
            raise ValueError('Only frozen actual-planner reviews supported')
        review=case['reviews'][day//3];report=review['report'];decision=review['decision']
        # Binding intentionally ignores a new report UUID but retains its exact source/context.
        binding=digest(dict(context=report['context'],input_digest=report['input_digest'],quantity=decision['quantity']))
        payload=dict(id=decision['id'],synthetic_only=True,kind='synthetic_commitment',
            report_id=report['run_id'],input_digest=report['input_digest'],context=report['context'],
            quantity=decision['quantity'],status=decision['status'],source_case_digest=digest(case))
        origin=report['context']['origin_day']
        with self._connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            existing=conn.execute('SELECT * FROM decisions WHERE id=?',(payload['id'],)).fetchone()
            if existing:
                if existing['binding']!=binding:raise ValueError('Conflicting decision identity')
                return json.loads(existing['payload'])
            latest=conn.execute('SELECT max(known_day) FROM events').fetchone()[0]
            if latest is not None and origin<latest:raise ValueError('Backdated decision admission')
            conn.execute('INSERT INTO decisions VALUES (?,?,?)',(payload['id'],binding,json.dumps(payload,sort_keys=True)))
            if payload['quantity']:
                event=dict(id=payload['id']+':confirmed',decision_id=payload['id'],kind='confirmed',known_day=origin,
                           quantity=payload['quantity'],eta=report['result']['order_arrival_day'])
                self._append(conn,event)
        return payload

    @staticmethod
    def _append(conn,event):
        conn.execute('INSERT INTO events (id,decision_id,kind,known_day,payload) VALUES (?,?,?,?,?)',
            (event['id'],event['decision_id'],event['kind'],event['known_day'],json.dumps(event,sort_keys=True)))

    def admit_supplier(self,catalog,*,cutoff,sku_id,warehouse_id,supplier,quantity=None,
                       order_minute=540,arm='actual_proposal'):
        """Bind one feasible saved-source choice; assumed receipt outcomes are not admissions."""
        from .product import validate_catalog,_key,_report
        from .decision_contrast import compare
        validate_catalog(catalog)
        if supplier is None or arm not in ('actual_proposal','alternative','no_action'):
            raise ValueError('Explicit supplier profile and compared arm required')
        comparison=compare(catalog,cutoff,sku_id,warehouse_id,quantity,
                           supplier=supplier,order_minute=order_minute)
        selected=(comparison.get('arms') or {}).get(arm)
        if selected is None or selected['status']!='assessable':
            raise ValueError('Only feasible, assessable supplier decisions may be admitted')
        _,key=_key(catalog,cutoff,sku_id,warehouse_id)
        report=_report(catalog,key['plan_run_id']);context=report['context']
        feasibility=selected['feasibility'];pieces=int(selected['quantity'])
        identity=digest(dict(cutoff=cutoff,sku_id=sku_id,warehouse_id=warehouse_id,
                             demand_batch=context['batch_id'],supply_batch=context['supply_batch_id'],
                             supplier_id=supplier['supplier_id']))
        binding=digest(dict(context=context,input_digest=report['input_digest'],quantity=pieces,
                            supplier=supplier,order_minute=order_minute))
        payload=dict(id='supplier:'+identity,synthetic_only=True,kind='synthetic_supplier_commitment',
                     report_id=report['run_id'],input_digest=report['input_digest'],context=context,
                     quantity=pieces,status='assessable',source_case_digest=comparison['calculation_id'],
                     supplier_profile=supplier,feasibility=feasibility)
        with self._connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            existing=conn.execute('SELECT * FROM decisions WHERE id=?',(payload['id'],)).fetchone()
            if existing:
                if existing['binding']!=binding:raise ValueError('Conflicting decision identity')
                return json.loads(existing['payload'])
            if conn.execute('SELECT count(*) FROM decisions').fetchone()[0]>=256:
                raise ValueError('Local synthetic decision envelope exhausted')
            latest=conn.execute('SELECT max(known_day) FROM events').fetchone()[0]
            if latest is not None and cutoff<latest:raise ValueError('Backdated decision admission')
            prior=[json.loads(r['payload']) for r in conn.execute('SELECT payload FROM decisions')]
            profile_identity=tuple(supplier[k] for k in ('supplier_id','version_id','sku_id','warehouse_id'))
            for d in prior:
                old=d.get('supplier_profile')
                if old and tuple(old[k] for k in ('supplier_id','version_id','sku_id','warehouse_id'))==profile_identity and old!=supplier:
                    raise ValueError('Conflicting immutable supplier profile version')
            if pieces:
                day=feasibility['accepted_day']
                terms=next(r for r in supplier['capacity'] if r['day']==day)
                for previous in prior:
                    if (previous.get('supplier_profile',{}).get('supplier_id')==supplier['supplier_id'] and
                        previous.get('feasibility',{}).get('accepted_day')==day and previous['quantity']):
                        previous_terms=next(r for r in previous['supplier_profile']['capacity'] if r['day']==day)
                        if previous_terms!=terms:
                            raise ValueError('Conflicting shared supplier/day capacity; reconcile before new admission')
                allocated=sum(d['quantity'] for d in prior if d.get('supplier_profile',{}).get('supplier_id')==supplier['supplier_id']
                              and d.get('feasibility',{}).get('accepted_day')==feasibility['accepted_day'])
                if allocated+pieces>int(feasibility['available_capacity']):
                    raise ValueError('Journal commitments exhaust declared supplier dispatch capacity')
                if conn.execute('SELECT count(*) FROM events').fetchone()[0]>=256:
                    raise ValueError('Local synthetic journal event envelope exhausted')
            conn.execute('INSERT INTO decisions VALUES (?,?,?)',(payload['id'],binding,json.dumps(payload,sort_keys=True)))
            if pieces:self._append(conn,dict(id=payload['id']+':confirmed',decision_id=payload['id'],kind='confirmed',
                                          known_day=cutoff,quantity=pieces,eta=feasibility['promised_day']))
        return payload

    def record(self,*,decision_id,event_id,kind,known_day,quantity=None,eta=None):
        _day(known_day)
        if not isinstance(event_id,str) or not event_id.strip() or len(event_id)>200 or kind not in ('receipt','eta'):
            raise ValueError('Invalid event identity/kind')
        if kind=='receipt':
            if type(quantity) is not int or quantity<1 or eta is not None:raise ValueError('Positive whole pieces required')
        elif quantity is not None or _day(eta)<known_day:
            raise ValueError('ETA cannot precede its notification')
        event=dict(id=event_id,decision_id=decision_id,kind=kind,known_day=known_day,quantity=quantity,eta=eta)
        with self._connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            existing=conn.execute('SELECT payload FROM events WHERE id=?',(event_id,)).fetchone()
            if existing:
                if json.loads(existing['payload'])!=event:raise ValueError('Conflicting event identity')
                return event
            if conn.execute('SELECT count(*) FROM events').fetchone()[0]>=256:
                raise ValueError('Local synthetic journal event envelope exhausted')
            decision=conn.execute('SELECT payload FROM decisions WHERE id=?',(decision_id,)).fetchone()
            if decision is None:raise ValueError('Unknown decision')
            decision=json.loads(decision['payload'])
            if not decision['quantity']:raise ValueError('Blocked/zero decision has no inbound order')
            events=[json.loads(r['payload']) for r in conn.execute('SELECT payload FROM events WHERE decision_id=? ORDER BY sequence',(decision_id,))]
            latest=conn.execute('SELECT max(known_day) FROM events').fetchone()[0]
            if known_day<latest:raise ValueError('Backdated journal knowledge')
            remaining=decision['quantity']-sum(e['quantity'] for e in events if e['kind']=='receipt')
            if remaining==0:raise ValueError('Order is already fully received')
            if kind=='receipt' and (quantity>remaining or known_day<events[0]['eta']):
                raise ValueError('Overreceipt or receipt before feasible promise')
            self._append(conn,event)
        return event

    def snapshot(self,as_of):
        _day(as_of)
        with self._connection() as conn:
            conn.execute('BEGIN')
            decisions=[json.loads(r['payload']) for r in conn.execute('SELECT payload FROM decisions ORDER BY id')]
            events=[json.loads(r['payload']) for r in conn.execute('SELECT payload FROM events WHERE known_day<=? ORDER BY sequence',(as_of,))]
        visible=[d for d in decisions if d['context']['origin_day']<=as_of]
        orders=[]
        for decision in visible:
            if not decision['quantity']:continue
            own=[e for e in events if e['decision_id']==decision['id']]
            received=sum(e['quantity'] for e in own if e['kind']=='receipt')
            eta=next(e['eta'] for e in reversed(own) if e['kind'] in ('confirmed','eta'))
            orders.append(dict(decision_id=decision['id'],quantity=decision['quantity'],received=received,
                remaining=decision['quantity']-received,eta=eta,
                state='received' if received==decision['quantity'] else 'partial' if received else 'confirmed',
                overdue=decision['quantity']>received and eta<as_of,input_digest=decision['input_digest']))
        return dict(synthetic_only=True,as_of=as_of,decisions=visible,events=events,orders=orders,
                    received_pieces=sum(o['received'] for o in orders),pending_pieces=sum(o['remaining'] for o in orders))

    def inbound(self,as_of):
        """Origin-visible owner input projection; does not insert or repair source rows."""
        snapshot=self.snapshot(as_of)
        return [dict(source_system='synthetic-journal',inbound_id=o['decision_id']+':order',
                     remaining_qty=o['remaining'],arrival_day=o['eta'],status='confirmed',
                     decision_input_digest=o['input_digest']) for o in snapshot['orders'] if o['remaining']]

    def publish_supply(self,owner,*,batch_id,sku_id,warehouse_id,as_of,reservations,policy):
        """Synthetic owner stages new supply; never writes stock or repairs old batches."""
        from datetime import timedelta
        from .demand import midnight
        from .planner_loop import _insert
        from .planning_runs import exact_json
        _day(as_of)
        if not isinstance(batch_id,str) or not batch_id.strip():raise ValueError('New batch identity required')
        snapshot=self.snapshot(as_of);origin=midnight(date.fromisoformat(as_of))
        selected={d['id'] for d in snapshot['decisions'] if
                  (d['context']['sku_id'],d['context']['warehouse_id'])==(sku_id,warehouse_id)}
        if not selected:raise ValueError('Unknown journal key')
        # Caller supplies complete current obligations explicitly, with original due dates.
        if any(set(r)!={'source_system','reservation_id','remaining_qty','due_day'} or
               type(r['remaining_qty']) is not int or r['remaining_qty']<0 for r in reservations):
            raise ValueError('Explicit exact reservation evidence required')
        if (set(policy)!={'lead_days','review_days','safety_qty','pack_size','moq'} or
            any(type(v) is not int for v in policy.values()) or policy['safety_qty']<0 or
            any(policy[k]<1 for k in ('lead_days','review_days','pack_size','moq')) or
            policy['lead_days']+policy['review_days']>366):raise ValueError('Invalid policy')
        for row in reservations:_day(row['due_day'])
        inbound=[dict(row_id=f'{batch_id}:inbound-{i}',batch_id=batch_id,source_system='synthetic-journal',
            inbound_id=o['decision_id']+':order',remaining_qty=o['remaining'],arrival_day=date.fromisoformat(o['eta']),
            status='confirmed',source_recorded_at=origin,observed_at=origin)
            for i,o in enumerate(snapshot['orders']) if o['decision_id'] in selected and o['remaining']]
        obligations=[row|dict(row_id=f'{batch_id}:reservation-{i}',batch_id=batch_id,
            due_day=date.fromisoformat(row['due_day']),status='open',source_recorded_at=origin,observed_at=origin)
            for i,row in enumerate(reservations)]
        tables=dict(supply_batches=[dict(batch_id=batch_id,version_id='synthetic-journal-supply-v1',
            sku_id=sku_id,warehouse_id=warehouse_id,as_of=origin,observed_at=origin,status='complete',
            reservations_complete=True,inbound_complete=True,expected_reservations=len(obligations),expected_inbound=len(inbound))],
            reservations=obligations,inbound=inbound,policies=[dict(row_id=batch_id+':policy',batch_id=batch_id,
                **policy,source_recorded_at=origin,observed_at=origin)])
        with owner.transaction():
            for table,rows in tables.items():_insert(owner,'planning_input',table,rows)
        return exact_json(tables)
