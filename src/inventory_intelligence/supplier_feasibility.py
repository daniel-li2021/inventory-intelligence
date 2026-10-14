"""Bounded, source-bound synthetic supplier promises; no operational execution."""
from datetime import date, timedelta
from .product import archive_digest

VERSION = 'supplier-feasibility-v1'


def _day(value):
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError('Exact ISO supplier business day required')
    return date.fromisoformat(value)


def example_profile(cutoff, sku_id, warehouse_id):
    """Explicit demonstration assumption, independent of the saved source archive."""
    origin = _day(cutoff)
    return dict(contract_version=VERSION, synthetic_only=True,
                supplier_id='synthetic-demo-supplier',
                version_id='demo-capacity-12-'+cutoff+'-'+archive_digest([sku_id,warehouse_id],False)[:12],
                sku_id=sku_id, warehouse_id=warehouse_id, known_day=cutoff,
                order_weekdays=[0, 1, 2, 3, 4], receipt_weekdays=list(range(7)),
                cutoff_minute=1020,
                capacity=[dict(day=(origin + timedelta(days=i)).isoformat(),
                               capacity=12, reserved=0) for i in range(33)])


def promise(profile, cutoff, sku_id, warehouse_id, quantity, lead_days, order_minute=540):
    """Earliest calendar acceptance, then nominal lead and receiving calendar.

    Capacity exhaustion blocks rather than inventing a later allocation or split.
    Dates and minutes use the explicitly declared supplier-local business calendar.
    """
    origin = _day(cutoff)
    if (type(quantity) is not int or not 0 <= quantity <= 2000 or
            type(lead_days) is not int or not 1 <= lead_days <= 366 or
            type(order_minute) is not int or not 0 <= order_minute < 1440):
        raise ValueError('Exact bounded quantity, lead and local order minute required')
    empty = dict(status='not_assessable', accepted_day=None, promised_day=None,
                 available_capacity=None, profile_digest=None)
    if profile is None:
        return empty | dict(reasons=['supplier_profile_missing'])
    fields = {'contract_version', 'synthetic_only', 'supplier_id', 'version_id',
              'sku_id', 'warehouse_id', 'known_day', 'order_weekdays',
              'receipt_weekdays', 'cutoff_minute', 'capacity'}
    if (not isinstance(profile, dict) or set(profile) != fields or
            profile['contract_version'] != VERSION or profile['synthetic_only'] is not True or
            any(not isinstance(profile[k], str) or not profile[k].strip() or len(profile[k]) > 200
                for k in ('supplier_id', 'version_id', 'sku_id', 'warehouse_id')) or
            type(profile['cutoff_minute']) is not int or not 0 < profile['cutoff_minute'] < 1440):
        raise ValueError('Invalid synthetic supplier profile')
    for name in ('order_weekdays', 'receipt_weekdays'):
        values = profile[name]
        if (not isinstance(values, list) or not values or len(values) > 7 or
                any(type(v) is not int or not 0 <= v <= 6 for v in values) or
                len(set(values)) != len(values)):
            raise ValueError('Explicit distinct supplier weekdays required')
    known = _day(profile['known_day'])
    capacity = profile['capacity']
    if not isinstance(capacity, list) or len(capacity) > 33:
        raise ValueError('Bounded dated supplier capacity required')
    by_day = {}
    for row in capacity:
        if (not isinstance(row, dict) or set(row) != {'day', 'capacity', 'reserved'} or
                any(type(row[k]) is not int or not 0 <= row[k] <= 2000 for k in ('capacity', 'reserved')) or
                row['reserved'] > row['capacity']):
            raise ValueError('Exact nonnegative capacity and reservations required')
        day = _day(row['day'])
        if day in by_day:
            raise ValueError('Duplicate supplier capacity day')
        by_day[day] = row['capacity'] - row['reserved']
    empty['profile_digest'] = archive_digest(profile, False)
    if (profile['sku_id'], profile['warehouse_id']) != (sku_id, warehouse_id):
        return empty | dict(reasons=['supplier_key_mismatch'])
    if known > origin:
        return empty | dict(reasons=['supplier_profile_not_yet_known'])
    if not quantity:
        return empty | dict(status='feasible', reasons=[])
    if origin.toordinal()>date.max.toordinal()-lead_days-14:
        return empty | dict(reasons=['promise_outside_common_window'])
    accepted = origin
    while accepted.weekday() not in profile['order_weekdays'] or (accepted == origin and order_minute >= profile['cutoff_minute']):
        accepted += timedelta(days=1)
    earliest = accepted + timedelta(days=lead_days)
    while earliest.weekday() not in profile['receipt_weekdays']:
        earliest += timedelta(days=1)
    result = empty | dict(accepted_day=accepted.isoformat(), promised_day=earliest.isoformat(),
                          available_capacity=str(by_day[accepted]) if accepted in by_day else None)
    if accepted not in by_day:
        return result | dict(reasons=['dispatch_capacity_missing'])
    if quantity > by_day[accepted]:
        return result | dict(reasons=['dispatch_capacity_exceeded'])
    if (earliest - origin).days >= 33:
        return result | dict(reasons=['promise_outside_common_window'])
    return result | dict(status='feasible', reasons=[])


def receipt_schedule(feasibility, cutoff, quantity, deliveries=None):
    """Declared synthetic outcome path; cannot change the earliest feasible promise."""
    origin = _day(cutoff)
    if feasibility['status'] != 'feasible':
        return None
    if deliveries is None:
        return [(int((date.fromisoformat(feasibility['promised_day']) - origin).days), quantity)] if quantity else []
    if not isinstance(deliveries, list) or len(deliveries) > 16:
        raise ValueError('At most sixteen declared partial receipts required')
    schedule = []
    for row in deliveries:
        if (not isinstance(row, dict) or set(row) != {'arrival_day', 'quantity'} or
                type(row['quantity']) is not int or row['quantity'] <= 0):
            raise ValueError('Positive exact partial receipt pieces required')
        day = _day(row['arrival_day'])
        if not quantity or row['arrival_day'] < feasibility['promised_day'] or not 0 <= (day-origin).days < 33:
            raise ValueError('Partial receipt before promise or outside common paid window')
        schedule.append(((day-origin).days, row['quantity']))
    if sum(q for _, q in schedule) != quantity or schedule != sorted(schedule) or len({d for d, _ in schedule}) != len(schedule):
        raise ValueError('Chronological distinct receipts must conserve the complete order')
    return schedule
