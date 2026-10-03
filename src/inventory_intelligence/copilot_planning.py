"""Read-only historical explanations of explicit persisted planning-v1 runs."""

from copy import deepcopy
from datetime import date, timedelta
from fractions import Fraction
from uuid import UUID

from psycopg.pq import TransactionStatus
from psycopg.rows import dict_row

from .copilot import _bounded, _text, _time, _validate_benchmark, _validate_report, _rational
from .forecasting import METHODS
from .demand import midnight, CALENDAR

# Complete 180-day benchmarks retain ~4 MiB of replay evidence; never truncate.
MAX_PLANNING_BYTES = 16 * 1024 * 1024


def _exact(value):
    if isinstance(value, float):
        raise ValueError('planning evidence must use exact quantities')
    if isinstance(value, dict):
        for child in value.values():
            _exact(child)
    elif isinstance(value, list):
        for child in value:
            _exact(child)


def _eligible_series(series, context, *, start, end, known_at, minimum=1):
    """Check retained daily evidence without replaying inputs or forecasting."""
    if (series['status'] != 'eligible' or series['reasons']
            or series['business_timezone'] != context['business_timezone']
            or series['batch']['batch_id'] != context['batch_id']
            or any(series[k] != context[k] for k in ('sku_id', 'warehouse_id'))
            or date.fromisoformat(series['start_day']) != start
            or date.fromisoformat(series['end_day']) != end
            or _time(series['known_at']) != known_at
            or len(series['days']) != (end-start).days or len(series['days']) < minimum):
        raise ValueError
    values = []
    for i, day in enumerate(series['days']):
        business_day = start+timedelta(days=i)
        if (date.fromisoformat(day['day']) != business_day or day['reasons']
                or type(day['quantity']) is not int or day['quantity'] < 0
                or midnight(business_day+timedelta(days=1)) > known_at):
            raise ValueError
        evidence, orders = day['day_record'], day['order_records']
        if (evidence['coverage'] != 'complete' or evidence['availability'] != 'available'
                or type(evidence['expected_lines']) is not int
                or evidence['expected_lines'] != len(orders)
                or date.fromisoformat(evidence['business_day']) != business_day
                or not midnight(business_day+timedelta(days=1)) <= _time(evidence['source_recorded_at'])
                    <= _time(evidence['observed_at']) <= known_at
                or any(evidence[k] != context[k] for k in ('batch_id','sku_id','warehouse_id'))):
            raise ValueError
        for order in orders:
            if (type(order['accepted_qty']) is not int or order['accepted_qty'] < 0
                    or order['status'] not in ('accepted','cancelled')
                    or _time(order['accepted_at']).astimezone(CALENDAR).date() != business_day
                    or not _time(order['accepted_at']) <= _time(order['source_recorded_at'])
                        <= _time(order['observed_at']) <= known_at
                    or any(order[k] != context[k] for k in ('batch_id','sku_id','warehouse_id'))):
                raise ValueError
        if sum(order['accepted_qty'] for order in orders) != day['quantity']:
            raise ValueError
        values.append(day['quantity'])
    return values


def _training(series, context):
    origin_day = date.fromisoformat(context['origin_day'])
    origin = midnight(origin_day)
    if _time(context['origin']) != origin or context['method'] not in METHODS:
        raise ValueError
    return _eligible_series(series, context, start=date.fromisoformat(context['start_day']),
                            end=origin_day, known_at=origin, minimum=28)


def _validate(report):
    try:
        _bounded(report, max_bytes=MAX_PLANNING_BYTES)
        _exact(report)
        UUID(report['run_id'])
        _time(report['created_at'])
        if (report['contract_version'] != 'planning-v1' or report['model_version'] != 'baselines-v1'
                or not _text(report['code_version']) or len(report['input_digest']) != 64
                or int(report['input_digest'], 16) < 0
                or report['kind'] not in ('backtest', 'forecast', 'replenishment')
                or report['status'] not in ('assessable', 'not_assessable')
                or report['status'] != report['result']['status']):
            raise ValueError
        context, result = report['context'], report['result']
        if not all(_text(context[k]) for k in ('batch_id', 'sku_id', 'warehouse_id')):
            raise ValueError
        if context['business_timezone'] != 'America/Los_Angeles':
            raise ValueError
        if report['kind'] == 'backtest':
            start = date.fromisoformat(context['start_day'])
            holdout = date.fromisoformat(context['holdout_day'])
            end = date.fromisoformat(context['end_day'])
            if (holdout != end-timedelta(days=28) or start >= end
                    or context['horizons'] != [7,14,28] or context['min_train'] != 28
                    or context['season_length'] != 7 or context['step'] != 7):
                raise ValueError
            expected_origins = [start+timedelta(days=i) for i in range(28, (holdout-start).days-28+1, 7)]
            if [date.fromisoformat(f['origin_day']) for f in result['candidates']] != expected_origins:
                raise ValueError
            folds = result['candidates']+[result['holdout']] if result['holdout'] else result['candidates']
            if (result['holdout'] is not None) != ((holdout-start).days >= 28):
                raise ValueError
            for f in folds:
                origin_day = date.fromisoformat(f['origin_day'])
                is_holdout = f is result['holdout']
                if (_time(f['origin']) != midnight(origin_day)
                        or (is_holdout and origin_day != holdout)
                        or f['status'] not in ('assessable','not_assessable')
                        or (f['status'] == 'assessable') != (f['training']['status'] == 'eligible'
                            and f['truth']['status'] == 'eligible' and len(f['training']['days']) >= 28)):
                    raise ValueError
                if f['status'] == 'not_assessable':
                    if f['actual'] is not None or f['predictions'] is not None:
                        raise ValueError
                    continue
                _eligible_series(f['training'], context, start=start, end=origin_day,
                                 known_at=midnight(origin_day), minimum=28)
                truth = _eligible_series(f['truth'], context, start=origin_day,
                    end=origin_day+timedelta(days=28), known_at=_time(context['evaluated_at']) if is_holdout
                    else min(_time(context['evaluated_at']), midnight(holdout)))
                if f['actual'] != truth or any(type(v) is not int for v in f['actual']):
                    raise ValueError
            included = [f for f in result['candidates'] if f['status'] == 'assessable']
            for section, folds in (('selection', included), ('holdout_scores',
                    [result['holdout']] if result['holdout'] and result['holdout']['status']=='assessable' else [])):
                for h in (7,14,28):
                    scores = result[section][str(h)]
                    if not folds:
                        if scores != dict(scored_points=0, scores=None):
                            raise ValueError
                        continue
                    _validate_benchmark(dict(horizon=h, season_length=7,
                        scored_points=scores['scored_points'], scores=scores['scores'], folds=[dict(
                            origin=(date.fromisoformat(f['origin_day'])-start).days,
                            actual=f['actual'][:h], predictions={m:f['predictions'][m][:h] for m in METHODS})
                            for f in folds]))
            chosen = min(METHODS, key=lambda m: Fraction(result['selection']['28']['scores'][m]['mae'])) if included else None
            if result['chosen_method'] != chosen:
                raise ValueError
            assessable = chosen is not None and result['holdout'] is not None and result['holdout']['status']=='assessable'
            if (report['status']=='assessable') != assessable:
                raise ValueError
        elif report['kind'] == 'replenishment':
            if not isinstance(result['reasons'], list) or not all(_text(r) for r in result['reasons']):
                raise ValueError
            if report['status'] == 'not_assessable':
                if not result['reasons'] or result['proposed_order_qty'] is not None or result['projection'] is not None:
                    raise ValueError
            else:
                from .replenishment import project
                inventory, supply, forecast = (result[k] for k in ('inventory','supply','forecast'))
                _training(forecast['training'], context)
                if result['training'] != forecast['training']:
                    raise ValueError
                _validate_report(inventory['run'] | dict(checks=inventory['checks'], findings=inventory['findings']))
                if (result['reasons'] or inventory['reasons'] or supply['reasons']
                        or forecast['status'] != 'assessable' or type(inventory['on_hand']) is not int
                        or inventory['on_hand'] < 0 or inventory['run']['overall_status'] != 'pass'
                        or str(inventory['run']['run_id']) != context['reliability_run_id']
                        or forecast['training']['status'] != 'eligible'):
                    raise ValueError
                from .planning_runs import exact_json
                policy = supply['policy']
                if (any(type(policy[k]) is not int or policy[k] < 1 for k in ('lead_days','review_days','pack_size','moq'))
                        or type(policy['safety_qty']) is not int or policy['safety_qty'] < 0
                        or policy['lead_days']+policy['review_days'] > 366
                        or context['horizon'] != policy['lead_days']+policy['review_days']
                        or len(forecast['predictions']) != policy['lead_days']+policy['review_days']):
                    raise ValueError
                quantities = [_rational(p) for p in forecast['predictions']]
                if any(q < 0 for q in quantities):
                    raise ValueError
                reservations = [r | dict(due_day=date.fromisoformat(r['due_day'])) for r in supply['reservations']]
                inbound = [r | dict(arrival_day=date.fromisoformat(r['arrival_day'])) for r in supply['inbound']]
                expected = exact_json(project(on_hand=inventory['on_hand'], forecasts=quantities,
                    reservations=reservations, inbound=inbound, origin_day=date.fromisoformat(context['origin_day']), policy=policy))
                if any(result[k] != value or (type(value) is int and type(result[k]) is not int)
                       for k,value in expected.items()):
                    raise ValueError
        else:
            if report['status'] == 'not_assessable':
                if result['predictions'] is not None or not result['reasons']:
                    raise ValueError
            elif (result['reasons'] or len(result['predictions']) != context['horizon']
                    or result['training']['status'] != 'eligible'
                    or any(_rational(p)<0 for p in result['predictions'])):
                raise ValueError
            if report['status'] == 'assessable':
                if type(context['horizon']) is not int or context['horizon'] < 1:
                    raise ValueError
                _training(result['training'], context)
    except (KeyError, TypeError, ValueError, AttributeError, ZeroDivisionError):
        raise ValueError('invalid or inconsistent persisted planning-v1 report') from None


def load_planning_run(conn, run_id):
    try:
        run_id = str(UUID(run_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError('run_id must be a UUID') from None
    if not conn.autocommit or conn.info.transaction_status != TransactionStatus.IDLE:
        raise ValueError('connection must be idle with autocommit=True')
    with conn.transaction(), conn.cursor(row_factory=dict_row) as cur:
        cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        cur.execute("SET LOCAL TIME ZONE 'UTC'")
        if cur.execute('SELECT current_user AS name').fetchone()['name'] != 'ii_runner':
            raise ValueError('connection must use ii_runner')
        size = cur.execute('SELECT octet_length(row_to_json(r)::text) AS bytes FROM planning.runs r WHERE run_id=%s', (run_id,)).fetchone()
        if size is None or size['bytes'] > MAX_PLANNING_BYTES:
            raise ValueError('selected planning run is missing or exceeds the 16 MiB limit')
        report = cur.execute('SELECT * FROM planning.runs WHERE run_id=%s', (run_id,)).fetchone()
        report['run_id'] = str(report['run_id'])
        report['created_at'] = _time(report['created_at']).isoformat()
        _validate(report)
        return report


def answer_planning(report):
    _validate(report)
    report = deepcopy(report)
    r = report['result']
    if report['kind'] == 'backtest':
        # Cite selected fields explicitly; the complete bounded run is validated.
        report['result'] = {k:r[k] for k in ('status','chosen_method','selection','holdout_scores')}
        report['result']['origins'] = [dict(origin=f['origin'],status=f['status']) for f in r['candidates']]
        report['result']['holdout_origin'] = r['holdout']['origin'] if r['holdout'] else None
    return dict(contract_version='copilot-2', intent='planning', status='answered',
        summary=f"Stored {report['kind']} run was {report['status']} [planning:{report['run_id']}].",
        citations=[dict(id='planning:'+report['run_id'], source='planning.runs', data=report)],
        limitations=['Historical synthetic evidence; current inputs and stock have not been revalidated.',
                     'A stored model choice or advisory proposal does not authorize an order.',
                     'WAPE is a ratio; null means zero actual demand or no eligible scoring evidence.'] if report['kind']=='backtest' else
                    ['Historical synthetic evidence; current inputs and stock have not been revalidated.',
                     'The cited order quantity describes the stored proposal; no current order is proposed.'],
        next_steps=['Run planning at a new cutoff with complete current inputs before acting.'],
        proposed_order_qty=None)
