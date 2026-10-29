"""Temporary, source-bound demand plans over validated synthetic catalog evidence."""
from datetime import date, timedelta
from fractions import Fraction

from . import product
from .forecasting import METHODS, forecast
from .planning_runs import MIN_TRAIN
from .replenishment import project

VERSION = 'demand-planning-v1'
HORIZONS = (7, 14, 28)


class DemandPlanningError(ValueError):
    """An intentionally user-facing planning validation message."""


def _adjustment(value, origin, horizon):
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {'kind', 'value', 'start_day', 'end_day'}:
        raise DemandPlanningError('Choose one percentage or pieces-per-day adjustment and its future date range.')
    kind, amount = value['kind'], value['value']
    limit = 100 if kind == 'percent' else 1000
    minimum = -100 if kind == 'percent' else -1000
    if kind not in ('percent', 'pieces') or type(amount) is not int or not minimum <= amount <= limit:
        raise DemandPlanningError('Use a whole percentage from -100 to 100, or whole pieces per day from -1000 to 1000.')
    try:
        start, end = (date.fromisoformat(value[k]) for k in ('start_day', 'end_day'))
    except (ValueError, TypeError):
        raise DemandPlanningError('Choose valid future start and end dates.') from None
    if (start.isoformat() != value['start_day'] or end.isoformat() != value['end_day'] or
            not origin <= start <= end < origin + timedelta(days=horizon)):
        raise DemandPlanningError('The adjustment range must be inside the selected future forecast period.')
    return dict(kind=kind, value=amount, start_day=start.isoformat(), end_day=end.isoformat())


def _weeks(rows):
    """Calendar weeks, split at the forecast origin; incomplete coverage stays null."""
    groups = {}
    for row in rows:
        day = date.fromisoformat(row['day'])
        monday = day - timedelta(days=day.weekday())
        groups.setdefault((row['period'], monday), []).append(row)
    result = []
    for (period, monday), days in groups.items():
        totals = {}
        for field in ('history', 'baseline', 'adjusted'):
            values = [d[field] for d in days]
            totals[field] = sum(values, Fraction(0)) if all(v is not None for v in values) else None
        result.append(dict(period=period, day=days[0]['day'], end_day=days[-1]['day'],
                           calendar_start=monday.isoformat(), day_count=len(days),
                           partial=len(days) != 7, **totals))
    return result


def calculate(catalog, cutoff, sku_id, warehouse_id, *, horizon=28, method='mean', adjustment=None):
    """Do not mutate sources or pass declared future outcomes into a forecast fit."""
    if type(horizon) is not int or horizon not in HORIZONS or method not in METHODS:
        raise DemandPlanningError('Choose a supported method and a 7, 14 or 28 day forecast.')
    binding, key = product._key(catalog, cutoff, sku_id, warehouse_id)
    saved = product._report(catalog, key['plan_run_id'])
    saved_forecast = product._report(catalog, key['forecast_run_id'])
    inputs = saved['result']
    training = inputs['training']
    origin = date.fromisoformat(binding['cutoff'])
    adjustment = _adjustment(adjustment, origin, horizon)
    eligible = training['status'] == 'eligible' and len(training['days']) >= MIN_TRAIN
    history = [dict(day=d['day'], end_day=d['day'], period='history', history=d['quantity'],
                    baseline=None, adjusted=None, day_count=1, partial=False,
                    reasons=d['reasons']) for d in training['days']]
    models = {m: forecast([d['quantity'] for d in training['days']], method=m, horizon=28)
              for m in METHODS} if eligible else {}
    baseline = models.get(method)
    adjusted = list(baseline) if baseline is not None else None
    if adjustment is not None and adjusted is not None:
        for i in range(horizon):
            day = (origin + timedelta(days=i)).isoformat()
            if adjustment['start_day'] <= day <= adjustment['end_day']:
                adjusted[i] = (baseline[i] * Fraction(100 + adjustment['value'], 100)
                               if adjustment['kind'] == 'percent' else baseline[i] + adjustment['value'])
                if adjusted[i] < 0:
                    raise DemandPlanningError('This adjustment would make future demand negative. Reduce the decrease or choose another date range.')
    future = [dict(day=(origin + timedelta(days=i)).isoformat(),
                   end_day=(origin + timedelta(days=i)).isoformat(), period='forecast', history=None,
                   baseline=baseline[i] if baseline is not None else None,
                   adjusted=adjusted[i] if adjusted is not None else None, day_count=1, partial=False)
              for i in range(horizon)]
    policy = inputs['supply']['policy']
    protection = policy['lead_days'] + policy['review_days']
    reasons = sorted(set(inputs['inventory']['reasons'] + inputs['supply']['reasons'] +
                         ([] if eligible else ['ineligible_or_insufficient_training'])))
    before = after = None
    if not reasons:
        # Dates are copied to native values for the existing projection kernel.
        reservations = [r | dict(due_day=date.fromisoformat(r['due_day'])) for r in inputs['supply']['reservations']]
        inbound = [r | dict(arrival_day=date.fromisoformat(r['arrival_day'])) for r in inputs['supply']['inbound']]
        common = dict(on_hand=inputs['inventory']['on_hand'], reservations=reservations,
                      inbound=inbound, origin_day=origin, policy=policy)
        before = project(forecasts=baseline[:protection], **common)
        after = project(forecasts=adjusted[:protection], **common)
    if reasons:
        effect = 'blocked'
        explanation = 'Inventory impact is unavailable because required demand, stock or supply evidence is incomplete.'
    elif before['proposed_order_qty'] != after['proposed_order_qty']:
        effect = 'changed'
        explanation = 'The future-demand adjustment changes the current advisory replenishment quantity.'
    elif baseline[:protection] != adjusted[:protection]:
        effect = 'same_order'
        explanation = 'Projected balances change, but available stock, safety, MOQ and pack rounding leave the current order quantity unchanged.'
    elif baseline != adjusted:
        effect = 'outside_protection_window'
        explanation = 'The adjustment is outside the current protection window. It changes the demand outlook but not today’s replenishment proposal.'
    else:
        effect = 'no_change'
        explanation = 'No demand change is applied within the current protection window.'
    def total(values):
        return sum(values[:horizon], Fraction(0)) if values is not None else None
    baseline_total, adjusted_total = total(baseline), total(adjusted)
    identity = dict(contract_version=VERSION, archive=catalog['digest'], source_plan=saved['run_id'],
                    source_forecast=saved_forecast['run_id'], cutoff=binding['cutoff'], sku_id=sku_id,
                    warehouse_id=warehouse_id, horizon=horizon, method=method, adjustment=adjustment)
    digest = product.archive_digest(identity, exclude_digest=False)
    sku = next(s for s in catalog['dimensions']['skus'] if s['sku_id'] == sku_id)
    warehouse = next(w for w in catalog['dimensions']['warehouses'] if w['warehouse_id'] == warehouse_id)
    rows = history + future
    response = product._wire(dict(
        contract_version=VERSION, archive_digest=catalog['digest'], calculation_digest=digest,
        synthetic=True, cutoff=binding['cutoff'], sku_id=sku_id, warehouse_id=warehouse_id,
        sku=sku, location=warehouse['name'], method=method, operational_default='mean',
        adjustment=adjustment, forecast_status='assessable' if eligible else 'not_assessable',
        forecast_reasons=[] if eligible else sorted(set(training['reasons'] +
            [r for d in training['days'] for r in d['reasons']] + ['ineligible_or_insufficient_training'])),
        totals=dict(historical_daily_mean=Fraction(sum(d['quantity'] for d in training['days']), len(history)) if eligible else None,
                    baseline=baseline_total, adjusted=adjusted_total,
                    delta=adjusted_total-baseline_total if eligible else None),
        methods=[dict(method=m, total=total(models.get(m))) for m in METHODS],
        accuracy=dict(status='unavailable', mae=None, bias=None, wape=None, scored_points=0,
                      reason='No matching per-item backtest is packaged. The 28 historical days are needed for training; no completed evaluation target remains. Other study results are not this item’s accuracy.'),
        impact=dict(status='assessable' if not reasons else 'not_assessable', reasons=reasons,
                    protection_start=origin, protection_end=origin+timedelta(days=protection-1),
                    policy=policy, baseline=before, adjusted=after,
                    order_delta=after['proposed_order_qty']-before['proposed_order_qty'] if before else None,
                    effect=effect, explanation=explanation),
        clocks=dict(business_timezone=training['business_timezone'], origin=saved['context']['origin'],
                    known_at=training['known_at'], training_start=training['start_day'],
                    training_end_inclusive=training['days'][-1]['day'],
                    training_end_exclusive=training['end_day'], source_created_at=saved['created_at']),
        references=[product._ref('planning.runs', saved['run_id']),
                    product._ref('planning.runs', saved_forecast['run_id']),
                    product._ref('reliability.runs', binding['reliability_run_id'])],
        limits=['Point forecasts; uncertainty is not quantified.',
                'Projected balances are expected net inventory, not physical stock or achieved service.',
                'Temporary synthetic calculation; no saved business plan or real order.']))
    # These are bounded calendar metadata, not quantities.
    response.update(horizon=horizon, protection_days=protection)
    response['accuracy']['scored_points'] = 0
    response['daily'] = [product._wire(row) | dict(day_count=row['day_count']) for row in rows]
    response['weekly'] = [product._wire(row) | dict(day_count=row['day_count']) for row in _weeks(rows)]
    return response
