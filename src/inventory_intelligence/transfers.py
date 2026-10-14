"""One-review, donor-safe synthetic transfers; exact pieces and immutable lifecycle."""
from datetime import date, timedelta
from fractions import Fraction
import json
import sqlite3
from pathlib import Path
from .product import _key, _report, _wire, archive_digest
from .planner_loop import fulfil_fifo
from .replenishment import project

VERSION = 'donor-safe-transfer-v1'
DAYS = 33


def _integer(value, maximum=1000000):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError('Bounded nonnegative whole pieces required')
    return value


def _date(value):
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError('Exact business date required')
    return date.fromisoformat(value)


def _execute(stock, demand, reservations, inbound, *, remove=0, extra=(), transport=0):
    stock -= remove
    if stock < 0: raise ValueError('Dispatch exceeds physical stock')
    queue = []; days = []; immediate = eventual = consumed = 0
    costs = dict(purchase=2*(stock+remove+sum(q for _, q in inbound)),
                 holding=0, backlog=0, setup=2*len(inbound), transport=transport)
    for day in range(DAYS):
        receipt = sum(q for d, q in (*inbound, *extra) if d == day)
        stock += receipt
        for identity, due, quantity in reservations:
            if due == day and quantity:
                queue.append(dict(id='reservation:'+identity, day=day, kind='reservation', remaining=quantity))
        amount = demand[day] if day < 28 else 0
        if amount: queue.append(dict(id='demand:'+str(day), day=day, kind='demand', remaining=amount))
        kinds = {r['id']: r['kind'] for r in queue}
        stock, queue, filled, new, _ = fulfil_fifo(stock, queue, day)
        consumed += sum(f['quantity'] for f in filled)
        immediate += new
        eventual += sum(f['quantity'] for f in filled if kinds[f['acceptance_id']] == 'demand')
        backlog = sum(r['remaining'] for r in queue)
        costs['holding'] += stock; costs['backlog'] += 10*backlog
        days.append(dict(day=day, receipts=receipt, end_stock=stock, end_backlog=backlog,
                         consumed=sum(f['quantity'] for f in filled), accepted=amount))
    accepted = sum(demand)
    return dict(accepted=accepted, immediate_fulfilled=immediate, eventual_fulfilled=eventual,
                immediate_fill=Fraction(immediate, accepted) if accepted else None,
                terminal_stock=stock, terminal_backlog=backlog, consumed=consumed,
                cost_components=costs, total_cost=sum(costs.values()), days=days)


def _inputs(catalog, cutoff, sku, location):
    _, key = _key(catalog, cutoff, sku, location)
    report = _report(catalog, key['plan_run_id']); result = report['result']
    if report['status'] != 'assessable': raise ValueError('Unassessable source location')
    origin = _date(cutoff)
    reservations = [(r['reservation_id'], (_date(r['due_day'])-origin).days, r['remaining_qty'])
                    for r in result['supply']['reservations'] if r['status'] == 'open' and r['remaining_qty']]
    inbound = [((_date(r['arrival_day'])-origin).days, r['remaining_qty'])
               for r in result['supply']['inbound'] if r['status'] == 'confirmed' and r['remaining_qty']]
    if any(not 0 <= d < DAYS for _, d, _ in reservations) or any(not 0 <= d < DAYS for d, _ in inbound):
        raise ValueError('Source outside common paid window')
    return dict(stock=result['inventory']['on_hand'], demand=key['future_demand']['quantities'],
                reservations=reservations, inbound=inbound, report=report)


def compare(catalog, cutoff, sku_id, donor_id, recipient_id, quantity, profile, supplier=None):
    """Only validated catalogs enter this adapter; transport assumptions remain explicit."""
    _integer(quantity, 2000)
    if donor_id == recipient_id: raise ValueError('Distinct locations required')
    required = {'version_id', 'known_day', 'transit_days', 'capacity', 'setup_cost', 'per_piece_cost'}
    if not isinstance(profile, dict) or set(profile) != required or not isinstance(profile['version_id'], str) or not profile['version_id'].strip():
        raise ValueError('Complete synthetic transport profile required')
    if _date(profile['known_day']) > _date(cutoff): raise ValueError('Future transport evidence')
    for name in required-{'version_id', 'known_day'}: _integer(profile[name], 2000)
    if not 1 <= profile['transit_days'] < DAYS: raise ValueError('Transit must be 1–32 days')
    binding = dict(archive_digest=catalog['digest'], cutoff=cutoff, sku_id=sku_id,
                   donor_id=donor_id, recipient_id=recipient_id, quantity=quantity,
                   transport_profile=profile, supplier_profile=supplier)
    envelope = dict(contract_version=VERSION, synthetic=True, binding=binding,
                    calculation_id=archive_digest(binding, False), common_days=DAYS,
                    limitations=['Declared synthetic demand protects donor service only within this scenario.',
                                 'One review; residual purchase uses existing prefix projection, no global optimum.',
                                 'Missing supplier evidence withholds purchase outcomes; transport profile is a declared synthetic assumption.'])
    try:
        donor = _inputs(catalog, cutoff, sku_id, donor_id)
        recipient = _inputs(catalog, cutoff, sku_id, recipient_id)
    except ValueError:
        return envelope | dict(status='not_assessable', reasons=['incomplete_or_incompatible_location_evidence'], arms=None, safe_surplus=None)
    base = _execute(donor['stock'], donor['demand'], donor['reservations'], donor['inbound'])
    safety = donor['report']['result']['supply']['policy']['safety_qty']
    safe = max(0, min([donor['stock']-safety]+[d['end_stock']-safety for d in base['days']]))
    if any(d['end_backlog'] for d in base['days']): safe = 0
    if quantity > min(safe, profile['capacity']):
        return envelope | dict(status='not_assessable', reasons=['donor_surplus_or_transport_capacity_exceeded'], arms=None, safe_surplus=str(safe))
    origin = _date(cutoff); result = recipient['report']['result']; policy = result['supply']['policy']
    transfer_arrival = origin+timedelta(days=profile['transit_days'])
    inbound = [dict(r, arrival_day=_date(r['arrival_day'])) for r in result['supply']['inbound']]
    if quantity:
        inbound.append(dict(status='confirmed', remaining_qty=quantity, arrival_day=transfer_arrival))
    reservations = [dict(r, due_day=_date(r['due_day'])) for r in result['supply']['reservations']]
    forecasts = [Fraction(v['numerator'], v['denominator']) if isinstance(v, dict) else Fraction(v)
                 for v in result['forecast']['predictions']]
    residual = project(on_hand=recipient['stock'], forecasts=forecasts, reservations=reservations,
                       inbound=inbound, origin_day=origin, policy=policy)['proposed_order_qty']
    proposals = dict(no_action=(0, 0), purchase_only=(0, result['proposed_order_qty']),
                     transfer_before_purchase=(quantity, residual))
    arms = {}
    for name, (transfer, purchase) in proposals.items():
        arrival = None; feasibility = dict(status='feasible', reasons=[])
        if purchase:
            if purchase > 2000:
                feasibility = dict(status='not_assessable', reasons=['purchase_outside_execution_envelope'])
            elif supplier is None:
                feasibility = dict(status='not_assessable', reasons=['missing_supplier_calendar_capacity'])
            else:
                from .supplier_feasibility import promise
                feasibility = promise(supplier, cutoff, sku_id, recipient_id, purchase, policy['lead_days'])
                arrival = feasibility.get('promised_day')
                if feasibility['status'] == 'feasible' and (arrival is None or not 0 <= (_date(arrival)-origin).days < DAYS):
                    feasibility = dict(status='not_assessable', reasons=['purchase_outside_common_window'])
        if feasibility['status'] != 'feasible':
            arms[name] = dict(status='not_assessable', reasons=feasibility['reasons'], purchase_quantity=purchase, outcome=None)
            continue
        paid_inbound = recipient['inbound']+([((_date(arrival)-origin).days, purchase)] if purchase else [])
        transport = profile['setup_cost']+profile['per_piece_cost']*transfer if transfer else 0
        a = _execute(donor['stock'], donor['demand'], donor['reservations'], donor['inbound'], remove=transfer)
        b = _execute(recipient['stock'], recipient['demand'], recipient['reservations'], paid_inbound,
                     extra=[(profile['transit_days'], transfer)] if transfer else [], transport=transport)
        if transfer and (a['immediate_fulfilled'] != base['immediate_fulfilled'] or a['terminal_backlog'] > base['terminal_backlog']):
            raise ValueError('Donor service conservation failed')
        network_initial = donor['stock']+recipient['stock']+sum(q for _, q in donor['inbound'])+sum(q for _, q in paid_inbound)
        if network_initial != a['terminal_stock']+b['terminal_stock']+a['consumed']+b['consumed']:
            raise ValueError('Network inventory conservation failed')
        arms[name] = dict(status='feasible', reasons=[], purchase_quantity=purchase, transfer_quantity=transfer,
                          purchase_promise=feasibility, donor=a, recipient=b, total_cost=a['total_cost']+b['total_cost'],
                          network_pieces=network_initial, terminal_pieces=a['terminal_stock']+b['terminal_stock'])
    envelope.update(status='assessable', reasons=[], safe_surplus=safe, arms=arms,
                    donor_input_digest=donor['report']['input_digest'], recipient_input_digest=recipient['report']['input_digest'],
                    donor_report_id=donor['report']['run_id'], recipient_report_id=recipient['report']['run_id'])
    return _wire(envelope)


class TransferJournal:
    """Atomic donor reservations, dispatch and exact partial receipts in a local sandbox."""
    def __init__(self, path):
        from .workflow import Journal
        self.storage = Journal(path)
        with self.storage._connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS transfers (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS transfer_events (sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                  id TEXT UNIQUE NOT NULL, transfer_id TEXT NOT NULL REFERENCES transfers(id),
                  known_day TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS immutable_transfers_update BEFORE UPDATE ON transfers BEGIN
                  SELECT RAISE(ABORT,'immutable transfer'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_transfers_delete BEFORE DELETE ON transfers BEGIN
                  SELECT RAISE(ABORT,'immutable transfer'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_transfer_events_update BEFORE UPDATE ON transfer_events BEGIN
                  SELECT RAISE(ABORT,'immutable transfer event'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_transfer_events_delete BEFORE DELETE ON transfer_events BEGIN
                  SELECT RAISE(ABORT,'immutable transfer event'); END;
            ''')

    def reserve(self, catalog, cutoff, sku_id, donor_id, recipient_id, quantity, profile, supplier=None):
        from .product import validate_catalog
        validate_catalog(catalog)
        return self._reserve(compare(catalog, cutoff, sku_id, donor_id, recipient_id, quantity, profile, supplier))

    def _reserve(self, comparison):
        if (comparison['contract_version'] != VERSION or comparison['status'] != 'assessable' or
            comparison['arms']['transfer_before_purchase']['status'] != 'feasible'):
            raise ValueError('Validated assessable comparison required')
        binding = json.loads(json.dumps(comparison['binding']))
        raw_quantity = binding['quantity']
        if not isinstance(raw_quantity, str) or not raw_quantity.isdecimal() or str(int(raw_quantity)) != raw_quantity:
            raise ValueError('Canonical wire quantity required')
        quantity = _integer(int(raw_quantity), 2000)
        binding['quantity'] = quantity
        binding['transport_profile']['transit_days'] = int(binding['transport_profile']['transit_days'])
        if not quantity: raise ValueError('Positive transfer required')
        # Internal admission receives only a freshly recomputed, validated comparison.
        identity = archive_digest(dict(cutoff=binding['cutoff'], sku_id=binding['sku_id'], donor_id=binding['donor_id'], recipient_id=binding['recipient_id']), False)
        payload = dict(id=identity, binding=binding, calculation_id=comparison['calculation_id'],
                       donor_input_digest=comparison['donor_input_digest'], safe_surplus=int(comparison['safe_surplus']))
        encoded = json.dumps(payload, sort_keys=True)
        with self.storage._connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            existing = conn.execute('SELECT payload FROM transfers WHERE id=?', (identity,)).fetchone()
            if existing:
                if existing[0] != encoded: raise ValueError('Conflicting natural transfer identity')
                return payload
            rows = [json.loads(r[0]) for r in conn.execute('SELECT payload FROM transfers')]
            if len(rows) >= 128: raise ValueError('Transfer sandbox limit')
            latest = conn.execute('SELECT max(known_day) FROM transfer_events').fetchone()[0]
            if latest and binding['cutoff'] < latest: raise ValueError('Backdated reservation')
            for previous in rows:
                old_terms=previous['binding']['transport_profile']
                if old_terms['version_id']==binding['transport_profile']['version_id'] and old_terms!=binding['transport_profile']:
                    raise ValueError('Conflicting immutable transport version')
            own = [r for r in rows if (r['binding']['sku_id'], r['binding']['donor_id']) == (binding['sku_id'], binding['donor_id'])]
            if any(r['donor_input_digest'] != payload['donor_input_digest'] for r in own):
                raise ValueError('New donor basis requires explicit reconciliation; cannot reset spent stock')
            if quantity+sum(r['binding']['quantity'] for r in own) > payload['safe_surplus']:
                raise ValueError('Donor surplus already reserved or dispatched')
            conn.execute('INSERT INTO transfers VALUES (?,?)', (identity, encoded))
            event = dict(id=identity+':reserve', transfer_id=identity, kind='reserve', known_day=binding['cutoff'], quantity=quantity)
            self._append(conn, event)
        return payload

    @staticmethod
    def _append(conn, event):
        conn.execute('INSERT INTO transfer_events(id,transfer_id,known_day,payload) VALUES (?,?,?,?)',
                     (event['id'], event['transfer_id'], event['known_day'], json.dumps(event, sort_keys=True)))

    def record(self, transfer_id, event_id, kind, known_day, quantity=None, eta=None):
        day = _date(known_day)
        if kind not in ('dispatch', 'receipt', 'eta') or not isinstance(event_id, str) or not event_id.strip() or len(event_id) > 200:
            raise ValueError('Valid transfer event required')
        if kind == 'receipt':
            if not _integer(quantity, 2000): raise ValueError('Positive receipt required')
            if eta is not None: raise ValueError('Receipt cannot contain ETA')
        elif quantity is not None: raise ValueError('Dispatch/ETA cannot contain quantity')
        if kind == 'eta':
            if _date(eta) < day: raise ValueError('ETA cannot precede notice')
        elif eta is not None: raise ValueError('ETA only allowed in a notice')
        event = dict(id=event_id, transfer_id=transfer_id, kind=kind, known_day=known_day, quantity=quantity, eta=eta)
        with self.storage._connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            existing = conn.execute('SELECT payload FROM transfer_events WHERE id=?', (event_id,)).fetchone()
            if existing:
                if json.loads(existing[0]) != event: raise ValueError('Conflicting event identity')
                return event
            row = conn.execute('SELECT payload FROM transfers WHERE id=?', (transfer_id,)).fetchone()
            if row is None: raise ValueError('Unknown transfer')
            transfer = json.loads(row[0]); binding = transfer['binding']
            latest = conn.execute('SELECT max(known_day) FROM transfer_events').fetchone()[0]
            if latest and known_day < latest: raise ValueError('Backdated transfer event')
            if conn.execute('SELECT count(*) FROM transfer_events').fetchone()[0] >= 256: raise ValueError('Transfer event limit')
            events = [json.loads(r[0]) for r in conn.execute('SELECT payload FROM transfer_events WHERE transfer_id=? ORDER BY sequence', (transfer_id,))]
            dispatched = [e for e in events if e['kind'] == 'dispatch']
            if kind == 'dispatch':
                if dispatched or known_day != binding['cutoff']: raise ValueError('Dispatch must match protected origin; replan a late dispatch')
            else:
                if not dispatched: raise ValueError('Receipt/ETA needs dispatch')
                earliest = _date(dispatched[0]['known_day'])+timedelta(days=binding['transport_profile']['transit_days'])
                received = sum(e['quantity'] for e in events if e['kind'] == 'receipt')
                if received == binding['quantity']: raise ValueError('Transfer already fully received')
                if kind == 'receipt' and (day < earliest or received+quantity > binding['quantity']):
                    raise ValueError('Early or excess transfer receipt')
                if kind == 'eta' and _date(eta) < earliest: raise ValueError('ETA precedes feasible transit')
            self._append(conn, event)
        return event

    def snapshot(self, as_of):
        _date(as_of)
        with self.storage._connection() as conn:
            conn.execute('BEGIN')
            rows = [json.loads(r[0]) for r in conn.execute('SELECT payload FROM transfers ORDER BY id')]
            events = [json.loads(r[0]) for r in conn.execute('SELECT payload FROM transfer_events WHERE known_day<=? ORDER BY sequence', (as_of,))]
        transfers = []
        for row in rows:
            if row['binding']['cutoff'] > as_of: continue
            own = [e for e in events if e['transfer_id'] == row['id']]
            dispatched = any(e['kind'] == 'dispatch' for e in own)
            received = sum(e['quantity'] for e in own if e['kind'] == 'receipt')
            quantity = row['binding']['quantity']
            arrival = (_date(row['binding']['cutoff'])+timedelta(days=int(row['binding']['transport_profile']['transit_days']))).isoformat()
            revised = [e['eta'] for e in own if e['kind'] == 'eta']
            arrival = revised[-1] if revised else arrival
            transfers.append(row | dict(eta=arrival, overdue=dispatched and received<quantity and arrival<as_of,
                                       reserved=0 if dispatched else quantity, dispatched=quantity if dispatched else 0,
                                       in_transit=quantity-received if dispatched else 0, received=received))
        return _wire(dict(synthetic_only=True, as_of=as_of, transfers=transfers, events=events))

    def supply_effects(self, as_of, sku_id, warehouse_id):
        """Known reservations/in-transit only; physical counts/movements stay separate."""
        rows = self.snapshot(as_of)['transfers']
        reservations = []; inbound = []
        for row in rows:
            binding = row['binding']
            if binding['sku_id'] != sku_id: continue
            if binding['donor_id'] == warehouse_id and int(row['reserved']):
                reservations.append(dict(source_system='synthetic-transfer', reservation_id=row['id']+':reserved',
                                         remaining_qty=int(row['reserved']), due_day=as_of, status='open'))
            if binding['recipient_id'] == warehouse_id and int(row['in_transit']):
                inbound.append(dict(source_system='synthetic-transfer', inbound_id=row['id']+':in-transit',
                                    remaining_qty=int(row['in_transit']), arrival_day=row['eta'], status='confirmed'))
        return dict(reservations=reservations, inbound=inbound,
                    boundary='Supply projection only; dispatch/receipts require separately reconciled stock evidence.')

    def publish_supply(self, owner, *, batch_id, sku_id, warehouse_id, as_of, reservations, inbound, policy):
        """Synthetic owner explicitly declares complete external supply plus journal effects."""
        from .demand import midnight
        from .planner_loop import _insert
        from .planning_runs import exact_json
        from .synthetic_replay import _local
        _local(owner)
        origin = midnight(_date(as_of))
        visible=self.snapshot(as_of)['transfers']
        if not any(r['binding']['sku_id']==sku_id and warehouse_id in (r['binding']['donor_id'],r['binding']['recipient_id']) for r in visible):
            raise ValueError('Unknown origin-visible transfer source key')
        if not isinstance(batch_id,str) or not batch_id.strip(): raise ValueError('New supply batch required')
        fields = {'lead_days','review_days','safety_qty','pack_size','moq'}
        if (not isinstance(policy,dict) or set(policy)!=fields or any(type(v) is not int for v in policy.values()) or
            policy['safety_qty']<0 or any(policy[k]<1 for k in fields-{'safety_qty'}) or policy['lead_days']+policy['review_days']>366):
            raise ValueError('Exact complete policy required')
        effects = self.supply_effects(as_of, sku_id, warehouse_id)
        for values, expected, identity, clock, statuses in (
            (reservations, {'source_system','reservation_id','remaining_qty','due_day','status'}, 'reservation_id','due_day', {'open','fulfilled','cancelled'}),
            (inbound, {'source_system','inbound_id','remaining_qty','arrival_day','status'}, 'inbound_id','arrival_day', {'confirmed','pending','cancelled'})):
            if not isinstance(values,list) or len(values)>16: raise ValueError('Complete bounded explicit supply required')
            for row in values:
                if not isinstance(row,dict) or set(row)!=expected or row['status'] not in statuses:
                    raise ValueError('Invalid supply row')
                if any(not isinstance(row[k],str) or not row[k].strip() for k in ('source_system',identity)):
                    raise ValueError('Supply source identity required')
                _integer(row['remaining_qty']); _date(row[clock])
        reservations = reservations+effects['reservations']; inbound=inbound+effects['inbound']
        for rows, identity in ((reservations,'reservation_id'),(inbound,'inbound_id')):
            if len(rows)>16 or len({(r['source_system'],r[identity]) for r in rows})!=len(rows):
                raise ValueError('Duplicate or excessive combined supply')
        tables = dict(supply_batches=[dict(batch_id=batch_id,version_id='synthetic-transfer-supply-v1',sku_id=sku_id,warehouse_id=warehouse_id,
            as_of=origin,observed_at=origin,status='complete',reservations_complete=True,inbound_complete=True,
            expected_reservations=len(reservations),expected_inbound=len(inbound))],
            reservations=[dict(row_id=batch_id+':r:'+str(i),batch_id=batch_id,**dict(r,due_day=_date(r['due_day'])),source_recorded_at=origin,observed_at=origin) for i,r in enumerate(reservations)],
            inbound=[dict(row_id=batch_id+':i:'+str(i),batch_id=batch_id,**dict(r,arrival_day=_date(r['arrival_day'])),source_recorded_at=origin,observed_at=origin) for i,r in enumerate(inbound)],
            policies=[dict(row_id=batch_id+':policy',batch_id=batch_id,**policy,source_recorded_at=origin,observed_at=origin)])
        with owner.transaction():
            for table,rows in tables.items(): _insert(owner,'planning_input',table,rows)
        return exact_json(tables)
