"""Immutable 8/100-key product acceptance fixtures; actual SQL/core saved runs."""
from datetime import date, timedelta
from psycopg import sql
from inventory_intelligence.demand import midnight, BUSINESS_TIMEZONE
from synthetic.planning_demo import _insert

CUTOFFS = (date(2026, 1, 5), date(2026, 1, 12), date(2026, 1, 19))


def specification(index, cutoff_index):
    profile = index % 8
    stock = ((10, 4, 22) if profile == 0 else (40, 10, 10) if profile == 1
             else (40, 40, 40) if profile in (2, 6) else (0, 0, 0) if profile == 3
             else (10, 10, 10))[cutoff_index]
    return dict(stock=stock, daily=0 if profile == 3 else 4,
                reservations=0 if profile == 3 else 3,
                confirmed=0 if profile in (3, 7) else 5,
                supply_complete=not (profile == 5 and cutoff_index == 2),
                demand_complete=not (profile == 6 and cutoff_index == 0))


def load_inputs(owner, sku_count=50, prefix='product'):
    if sku_count not in (4, 50):
        raise ValueError('fixture size must be 4 or 50 SKUs')
    styles = [dict(style_id=f'{prefix}:style-{i:02}', style_code=f'ST-{i:02}',
                   name=('Essential Tee', 'Everyday Hoodie', 'Field Jacket', 'Straight Trouser',
                         'Travel Knit', 'Weekend Shirt', 'Active Short', 'Layer Vest',
                         'Rib Tank', 'Utility Overshirt')[i]) for i in range((sku_count+4)//5)]
    skus = [dict(sku_id=f'{prefix}:sku-{i:02}', style_id=styles[i//5]['style_id'],
                 sku_code=f'II-{i:02}', color='Ink' if i//5 % 2 == 0 else 'Clay',
                 size=('XS','S','M','L','XL')[i%5], base_uom='each') for i in range(sku_count)]
    warehouses = [dict(warehouse_id=f'{prefix}:{name.lower()}',warehouse_code=name.upper(),name=name)
                  for name in ('Harbor','Upland')]
    with owner.transaction():
        for table, rows in (('styles',styles),('skus',skus),('warehouses',warehouses)):
            _insert(owner,'operational_fixture',table,rows)
    keys = [dict(**s, **w, style=styles[i//5]['name']) for i,s in enumerate(skus) for w in warehouses]
    for ci, day in enumerate(CUTOFFS):
        origin, stem = midnight(day), f'{prefix}:{day}'
        batches,coverage,opening,snapshots = [],[],[],[]
        for kind in ('ledger','snapshot'):
            batch=stem+':'+kind
            batches.append(dict(batch_id=batch,kind=kind,status='complete',as_of=origin,
                                baseline_at=origin-timedelta(days=1) if kind=='ledger' else None,
                                watermark=0,observed_at=origin,
                                expected_row_count=0 if kind=='ledger' else len(keys)))
            for ki,key in enumerate(keys):
                fields={k:key[k] for k in ('sku_id','warehouse_id')}
                coverage.append(dict(row_id=f'{batch}:coverage:{ki}',batch_id=batch,**fields))
                qty=specification(ki,ci)['stock']
                if kind=='ledger':
                    opening.append(dict(row_id=f'{batch}:opening:{ki}',batch_id=batch,**fields,
                        quantity=qty,as_of=origin-timedelta(days=1),baseline_ref='independent-synthetic-count'))
                else:
                    snapshots.append(dict(row_id=f'{batch}:snapshot:{ki}',batch_id=batch,**fields,
                        on_hand_qty=qty,as_of=origin,watermark=0,observed_at=origin))
        with owner.transaction():
            for table,rows in (('batches',batches),('coverage',coverage),('opening_balances',opening),('snapshots',snapshots)):
                _insert(owner,'operational_fixture',table,rows)
        for ki,key in enumerate(keys):
            fields={k:key[k] for k in ('sku_id','warehouse_id')}
            spec=specification(ki,ci)
            batch=f'{stem}:key-{ki}:demand'
            days,orders=[],[]
            for i in range(28):
                business_day=day-timedelta(days=28-i)
                known=midnight(business_day+timedelta(days=1))
                if not spec['demand_complete'] and i==0:
                    continue
                days.append(dict(row_id=f'{batch}:day:{i}',batch_id=batch,**fields,
                    business_day=business_day,revision=1,source_recorded_at=known,observed_at=known,
                    coverage='complete',availability='available',expected_lines=int(spec['daily']>0)))
                if spec['daily']:
                    orders.append(dict(row_id=f'{batch}:order:{i}',batch_id=batch,**fields,
                        source_system='synthetic-orders',order_id=f'{batch}:order:{i}',line_id='1',revision=1,
                        accepted_at=midnight(business_day)+timedelta(hours=12),source_recorded_at=known,
                        observed_at=known,accepted_qty=spec['daily'],status='accepted'))
            # A future revision is retained but must never enter this origin's result.
            if orders:
                orders.append(orders[0] | dict(row_id=orders[0]['row_id']+':future',revision=2,
                    accepted_qty=99,source_recorded_at=origin+timedelta(days=1),observed_at=origin+timedelta(days=1)))
            supply=f'{stem}:key-{ki}:supply'
            supply_rows=[dict(batch_id=supply,version_id='product-supply-v1',**fields,
                as_of=origin,observed_at=origin,status='complete',reservations_complete=spec['supply_complete'],
                inbound_complete=True,expected_reservations=1,expected_inbound=2)]
            policy=[dict(row_id=supply+':policy',batch_id=supply,lead_days=2,review_days=3,
                safety_qty=0 if spec['daily']==0 else 2,pack_size=6,moq=10,
                source_recorded_at=origin,observed_at=origin)]
            reservation=[dict(row_id=supply+':reservation',batch_id=supply,source_system='synthetic',
                reservation_id='remaining-commitment',remaining_qty=spec['reservations'],due_day=day,
                status='open',source_recorded_at=origin,observed_at=origin)]
            inbound=[dict(row_id=supply+':'+name,batch_id=supply,source_system='synthetic',inbound_id=name,
                remaining_qty=qty,arrival_day=day+timedelta(days=arrival),status=status,
                source_recorded_at=origin,observed_at=origin) for name,qty,arrival,status in
                (('confirmed',spec['confirmed'],1,'confirmed'),('pending',100,0,'pending'))]
            with owner.transaction():
                _insert(owner,'planning_input','demand_batches',[dict(batch_id=batch,version_id='product-demand-v1',
                    business_timezone=BUSINESS_TIMEZONE,start_day=day-timedelta(days=28),end_day=day,
                    assembled_at=origin+timedelta(days=1),status='complete',expected_orders=len(orders),expected_days=len(days))])
                for table,rows in (('day_observations',days),('order_versions',orders),('supply_batches',supply_rows),
                                   ('policies',policy),('reservations',reservation),('inbound',inbound)):
                    if rows:
                        _insert(owner,'planning_input',table,rows)
    return dict(keys=keys,cutoffs=CUTOFFS,prefix=prefix)
