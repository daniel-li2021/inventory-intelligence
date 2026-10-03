"""Bounded synthetic replay adapter; all quantities use unchanged exact core kernels."""
from copy import deepcopy
from datetime import date, datetime, timedelta
from fractions import Fraction
import hashlib
import json
from math import ceil
from pathlib import Path

from .copilot_planning import answer_planning
from .decision import simulate
from .demand import midnight
from .forecasting import forecast
from .planning_runs import exact_json
from .replenishment import project

CONTRACT_VERSION = 'decision-lab-v1'
KEY = dict(sku_id='planning-demo:tee-m', warehouse_id='planning-demo:harbor')
BOUNDS = {
    'demand_percent': (100, 0, 200), 'lead_days': (2, 1, 14),
    'review_days': (3, 1, 7), 'supplier_delay_days': (0, 0, 14),
    'inbound_day': (1, 0, 27), 'reservation_qty': (3, 0, 100),
    'safety_qty': (2, 0, 100), 'pack_size': (6, 1, 24),
    'moq': (10, 1, 100), 'service_target_percent': (90, 0, 100),
}
DEFAULTS = {name: spec[0] for name, spec in BOUNDS.items()} | {'evidence_case': 'clean'}
CONTROLS = {name: dict(default=spec[0], min=spec[1], max=spec[2])
            for name, spec in BOUNDS.items()} | {
    'evidence_case': dict(default='clean', options=['clean', 'incomplete_supply'])}


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def archive_digest(evidence):
    """Content integrity, not a signature or independent source certification."""
    return _digest({k: v for k, v in evidence.items() if k != 'digest'})


def _require(condition):
    if not condition:
        raise ValueError('invalid or inconsistent synthetic Lab evidence')


def _no_floats(value):
    _require(not isinstance(value, float))
    if isinstance(value, dict):
        for child in value.values():
            _no_floats(child)
    elif isinstance(value, list):
        for child in value:
            _no_floats(child)


def _saved_digest(report):
    result = report['result']
    inputs = (result['training'] if report['kind'] == 'forecast' else
              {k: result[k] for k in ('inventory', 'supply', 'training')})
    _require(report['input_digest'] == _digest(dict(context=report['context'], inputs=inputs)))


def _validate_training(training, context):
    _require(training['status'] == 'eligible' and not training['reasons'])
    _require(all(training[k] == KEY[k] for k in KEY))
    _require(training['start_day'] == context['start_day'] and
             training['end_day'] == context['origin_day'] and
             training['known_at'] == context['origin'])
    start, origin = date.fromisoformat(context['start_day']), date.fromisoformat(context['origin_day'])
    _require((origin-start).days == 28 and len(training['days']) == 28)
    for i, day in enumerate(training['days']):
        expected_day = start+timedelta(days=i)
        record, orders = day['day_record'], day['order_records']
        _require(day['day'] == expected_day.isoformat() and not day['reasons'] and
                 type(day['quantity']) is int and day['quantity'] == 4)
        _require(record['business_day'] == day['day'] and record['coverage'] == 'complete'
                 and record['availability'] == 'available' and record['expected_lines'] == len(orders))
        _require(len(orders) == 1 and sum(r['accepted_qty'] for r in orders) == day['quantity'])
        for row in [record, *orders]:
            _require(all(row[k] == KEY[k] for k in KEY))
            _require(row['batch_id'] == context['batch_id'] and row['row_id'].startswith('planning-demo:'))
            _require(datetime.fromisoformat(row['source_recorded_at']) <=
                     datetime.fromisoformat(row['observed_at']) <= datetime.fromisoformat(context['origin']))
        _require(orders[0]['source_system'] == 'synthetic-orders' and orders[0]['status'] == 'accepted'
                 and type(orders[0]['accepted_qty']) is int and orders[0]['accepted_qty'] == 4)
        _require(midnight(expected_day+timedelta(days=1)) <=
                 datetime.fromisoformat(record['source_recorded_at']))
        _require(midnight(expected_day) <= datetime.fromisoformat(orders[0]['accepted_at']) <
                 midnight(expected_day+timedelta(days=1)))


def validate_evidence(evidence):
    """Verify bounded content, saved core reports/digests and fixture lineage.

    This verifies the immutable replay at its saved cutoff, not live inventory.
    The included digest detects edits; it is not cryptographic source authority.
    """
    try:
        _require(isinstance(evidence, dict) and len(json.dumps(evidence, allow_nan=False)) <= 32*1024*1024)
        _no_floats(evidence)
        _require(evidence['contract_version'] == 'decision-lab-evidence-v1' and
                 evidence['synthetic'] is True and evidence['business_data'] == 'synthetic only' and
                 evidence['digest'] == archive_digest(evidence))
        _require(set(evidence['plans']) == {'clean', 'incomplete_supply'})
        clean, blocked, saved_forecast = (evidence['plans']['clean'],
            evidence['plans']['incomplete_supply'], evidence['forecast'])
        for report in (clean, blocked, saved_forecast):
            answer_planning(report)
            _saved_digest(report)
            context = report['context']
            _require(all(context[k] == KEY[k] for k in KEY) and context['batch_id'] == 'planning-demo:demand')
            _require(context['method'] == 'mean' and
                     context['origin'] == midnight(date.fromisoformat(context['origin_day'])).isoformat())
            _validate_training(report['result']['training'], context)
        _require(clean['status'] == saved_forecast['status'] == 'assessable' and
                 blocked['status'] == 'not_assessable' and
                 'incomplete_or_mismatched_supply' in blocked['result']['reasons'])
        _require(saved_forecast['kind'] == 'forecast' and saved_forecast['context']['horizon'] == 28 and
                 clean['kind'] == blocked['kind'] == 'replenishment')
        _require(saved_forecast['result']['training'] == clean['result']['training'] == blocked['result']['training'])
        expected = exact_json(forecast([d['quantity'] for d in clean['result']['training']['days']], method='mean', horizon=28))
        _require(saved_forecast['result']['predictions'] == expected)
        inv = clean['result']['inventory']
        reliability = evidence['reliability']
        _require(reliability['overall_status'] == 'pass' and not reliability['findings'] and
                 reliability['checks'] == inv['checks'])
        _require(all(inv['run'][k] == reliability[k] for k in
                     ('run_id', 'contract_version', 'code_version', 'ledger_batch_id',
                      'snapshot_batch_id', 'as_of', 'evaluated_at', 'overall_status')))
        _require(clean['context']['reliability_run_id'] == blocked['context']['reliability_run_id'] == reliability['run_id'])
        _require(clean['context']['origin'] == reliability['as_of'] == reliability['evaluated_at'])
        _require(blocked['result']['inventory'] == inv and not inv['reasons'] and
                 not inv['current_validation']['findings'] and
                 all(c['status'] == 'pass' for c in inv['current_validation']['checks']))
        source = inv['source']
        snapshots = [r for r in source['snapshots'] if all(r[k] == KEY[k] for k in KEY)]
        openings = [r for r in source['opening_balances'] if all(r[k] == KEY[k] for k in KEY)]
        _require(len(snapshots) == len(openings) == 1 and not source['movements'])
        _require(type(inv['on_hand']) is int and inv['on_hand'] == snapshots[0]['on_hand_qty'] == openings[0]['quantity'])
        for kind in ('ledger', 'snapshot'):
            batch_id = 'planning-demo:'+kind
            batches = [r for r in source['batches'] if r['batch_id'] == batch_id]
            _require(len(batches) == 1 and batches[0]['status'] == 'complete' and
                     batches[0]['as_of'] == reliability['as_of'] and
                     any(r['batch_id'] == batch_id and all(r[k] == KEY[k] for k in KEY) for r in source['coverage']))
        for rows in source.values():
            for row in rows:
                for clock in ('source_recorded_at', 'observed_at'):
                    _require(row.get(clock) is None or datetime.fromisoformat(row[clock]) <= datetime.fromisoformat(reliability['as_of']))
        for case, report in evidence['plans'].items():
            supply = report['result']['supply']
            label = 'complete' if case == 'clean' else 'incomplete'
            _require(report['context']['supply_batch_id'] == supply['batch']['batch_id'] == 'planning-demo:supply:'+label)
            _require(supply['batch']['inbound_complete'] is True and
                     supply['batch']['reservations_complete'] is (case == 'clean'))
            _require(len(supply['reservations']) == 1 and len(supply['inbound']) == 2 and len(supply['policies']) == 1)
            _require(supply['policy'] == supply['policies'][0])
            _require(all(supply['policy'][k] == DEFAULTS[k] and type(supply['policy'][k]) is int
                         for k in ('lead_days', 'review_days', 'safety_qty', 'pack_size', 'moq')))
            reservation = supply['reservations'][0]
            _require(reservation['source_system'] == 'synthetic' and reservation['status'] == 'open' and
                     type(reservation['remaining_qty']) is int and reservation['remaining_qty'] == 3 and
                     reservation['due_day'] == report['context']['origin_day'])
            confirmed = [r for r in supply['inbound'] if r['status'] == 'confirmed']
            pending = [r for r in supply['inbound'] if r['status'] == 'pending']
            _require(len(confirmed) == len(pending) == 1 and type(confirmed[0]['remaining_qty']) is int and
                     confirmed[0]['remaining_qty'] == 5 and pending[0]['remaining_qty'] == 100)
            _require(confirmed[0]['arrival_day'] == (date.fromisoformat(report['context']['origin_day'])+timedelta(days=1)).isoformat())
            for row in [supply['batch'], *supply['reservations'], *supply['inbound'], *supply['policies']]:
                _require(row['batch_id'] == report['context']['supply_batch_id'])
                for clock in ('source_recorded_at', 'observed_at'):
                    _require(row.get(clock) is None or datetime.fromisoformat(row[clock]) <= datetime.fromisoformat(reliability['as_of']))
        future = evidence['future_demand']
        _require(future == dict(origin_day=clean['context']['origin_day'], quantities=[4]*28,
                source='declared synthetic constant demand', id='decision-lab:future-constant-v1'))
        return evidence
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError, ZeroDivisionError):
        raise ValueError('invalid or inconsistent synthetic Lab evidence') from None


def load_evidence(path=None):
    path = Path(path) if path is not None else Path(__file__).with_name('lab_evidence.json')
    if path.stat().st_size > 32*1024*1024:
        raise ValueError('Lab evidence exceeds archive size limit')
    return validate_evidence(json.loads(path.read_text(encoding='utf-8')))


def _parameters(overrides):
    if overrides is None:
        return DEFAULTS.copy()
    if not isinstance(overrides, dict) or set(overrides)-set(DEFAULTS):
        raise ValueError('unknown scenario field')
    parameters = DEFAULTS | overrides
    for name, (_, minimum, maximum) in BOUNDS.items():
        value = parameters[name]
        if type(value) is not int or not minimum <= value <= maximum:
            raise ValueError(f'{name} must be an integer from {minimum} to {maximum}')
    if parameters['evidence_case'] not in ('clean', 'incomplete_supply'):
        raise ValueError('evidence_case must be clean or incomplete_supply')
    return parameters


def _node(stage, label, explanation, references, data):
    return dict(stage=stage, label=label, explanation=explanation,
                references=references, data=data)


def _ref(source, identity):
    return dict(source=source, id=identity)


def _blocked(parameters, reasons, trace=()):
    return dict(status='not_assessable', reasons=reasons, parameters=parameters,
                forecast=None, plan=None, simulation=None, costs=None, risk=None,
                trace=list(trace), run_id=None)


def _side(parameters, evidence):
    report = evidence['plans'][parameters['evidence_case']]
    result = report['result']
    inv, supply = result['inventory'], result['supply']
    run_id = 'lab:'+_digest(dict(contract_version=CONTRACT_VERSION,
                                archive_digest=evidence['digest'], parameters=parameters))
    calculation_ref = _ref('lab.calculation', run_id)
    refs = [calculation_ref, _ref('planning.runs.inputs', report['run_id'])]
    trace = [_node('reliability', 'Reliability run',
        'Saved synthetic inventory passed R001–R005 at the replay cutoff.',
        [_ref('reliability.runs', evidence['reliability']['run_id'])], evidence['reliability']),
        _node('inventory', 'Inventory inputs',
        'Stock is retained from the reconciled snapshot; operational sources are immutable.',
        [_ref('operational_fixture.snapshots', r['row_id']) for r in inv['source']['snapshots']
         if all(r[k] == KEY[k] for k in KEY)],
        dict(on_hand=inv['on_hand'], cutoff=report['context']['origin'], source=inv['source']))]
    if report['status'] != 'assessable':
        trace.append(_node('supply', 'Supply gate',
            'Incomplete supply suppresses recommendation, projection, simulation and risk.', refs,
            dict(batch=supply['batch'], reasons=result['reasons'])))
        return _blocked(parameters, result['reasons'], trace)
    origin = date.fromisoformat(report['context']['origin_day'])
    percent = parameters['demand_percent']
    training = [dict(day=d['day'], quantity=ceil(Fraction(d['quantity']*percent, 100)),
        source_quantity=d['quantity'], source_row_ids=[d['day_record']['row_id'],
        *[r['row_id'] for r in d['order_records']]]) for d in result['training']['days']]
    history = [d['quantity'] for d in training]
    demand = [ceil(Fraction(q*percent, 100)) for q in evidence['future_demand']['quantities']]
    predictions = forecast(history, method='mean', horizon=28)
    policy = supply['policy'] | {k: parameters[k] for k in
            ('lead_days', 'review_days', 'safety_qty', 'pack_size', 'moq')}
    reservations = [supply['reservations'][0] | dict(due_day=origin,
                                                  remaining_qty=parameters['reservation_qty'])]
    inbound = [r | dict(arrival_day=origin+timedelta(days=parameters['inbound_day'])
                       if r['status'] == 'confirmed' else date.fromisoformat(r['arrival_day']))
               for r in supply['inbound']]
    plan = project(on_hand=inv['on_hand'], forecasts=predictions[:policy['lead_days']+policy['review_days']],
                   reservations=reservations, inbound=inbound, origin_day=origin, policy=policy)
    runoff = parameters['lead_days']+parameters['supplier_delay_days']+parameters['review_days']
    delays = [parameters['supplier_delay_days']]*len(range(0, len(demand)+runoff, parameters['review_days']))
    simulation = simulate(history, demand, method='mean', on_hand=inv['on_hand'],
        **{k: parameters[k] for k in ('lead_days', 'review_days', 'safety_qty', 'pack_size', 'moq')},
        commitments=[dict(id=reservations[0]['reservation_id'], due_day=0,
                          quantity=parameters['reservation_qty'])] if parameters['reservation_qty'] else [],
        inbound=[dict(id=r['inbound_id'], arrival_day=parameters['inbound_day'],
                      quantity=r['remaining_qty']) for r in inbound if r['status'] == 'confirmed'],
        supplier_delays=delays, holding_cost=1, backlog_cost=10, order_cost=2)
    simulation['assumptions'].update(supplier_delays=delays, delay_known_to_ordering=False,
        confirmed_inbound_day=parameters['inbound_day'], reservation_due_day=0,
        new_demand_source=evidence['future_demand']['id'],
        recommendation_policy='prefix-stock-v1; simulation reevaluates a distinct periodic policy')
    def charges(scored):
        rows = [d for d in simulation['days'] if d['scored'] is scored]
        return {name: sum((d[field] for d in rows), Fraction(0)) for name, field in
                (('holding', 'holding_cost'), ('backlog', 'backlog_cost'),
                 ('setup', 'order_cost'), ('total', 'total_cost'))}
    costs = dict(rates=dict(holding=Fraction(1), backlog=Fraction(10), setup=Fraction(2)),
                 scored=charges(True), runoff=charges(False), total=simulation['metrics']['total_cost'])
    surplus = [max(Fraction(0), d['balance_with_order']-parameters['safety_qty']) for d in plan['projection']]
    target = Fraction(parameters['service_target_percent'], 100)
    service = simulation['metrics']['immediate_fill_rate']
    risk = dict(stockout_days=[d['day'] for d in plan['projection'] if d['balance_with_order'] < 0],
        pre_arrival_shortage_days=plan['pre_arrival_shortage_days'], excess_piece_days=sum(surplus, Fraction(0)),
        peak_excess_qty=max(surplus), service_target=target, service_target_metric='immediate_fill_rate',
        meets_service_target=service >= target if service is not None else None,
        definition='Projected stockout means negative prefix balance; excess is projected surplus above safety. These are deterministic exposures, not probabilities. Service target compares immediate fill rate; zero demand leaves it unavailable. It does not set safety.')
    forecast_result = dict(method='mean', horizon=28, training=training, predictions=predictions,
        total=sum(predictions, Fraction(0)), demand=demand, source_run_id=evidence['forecast']['run_id'])
    trace += [_node('demand_forecast', 'Demand and forecast',
        'Counterfactual copies use ceil(source pieces × demand_percent / 100); saved orders remain unchanged. Mean forecast reuses the exact core.',
        [calculation_ref, _ref('planning.runs', evidence['forecast']['run_id']),
         _ref('synthetic.future_demand', evidence['future_demand']['id'])],
        dict(saved_training=result['training'], counterfactual=forecast_result, demand_percent=percent)),
        _node('supply', 'Supply assumptions',
        'Only five confirmed inbound pieces count; pending inbound is excluded. Reservations are separate prior demand due at day zero. Supplier delay affects simulated orders and is hidden from ordering.',
        [_ref('planning_input.supply_batches', supply['batch']['batch_id'])],
        dict(saved=supply, reservations=reservations, inbound=inbound, supplier_delays=delays)),
        _node('policy', 'Policy parameters',
        'Declared safety and service comparison target are user inputs; no model or calibrated safety selection occurs.',
        [_ref('planning_input.policies', supply['policy']['row_id'])],
        dict(policy=policy, service_target=target, holding_cost=1, backlog_cost=10, setup_cost=2)),
        _node('raw_requirement', 'Raw requirement',
        'Maximum safety shortfall over projection days after the full declared lead time, bounded below by zero.', refs,
        dict(unrounded_need=plan['unrounded_need'], projection=plan['projection'], horizon=len(plan['projection']))),
        _node('rounding', 'MOQ and pack rounding',
        'Ceil fractional need to pieces; positive need is raised to MOQ and rounded up to a whole pack. Zero need remains zero.', refs,
        {k: plan[k] for k in ('unrounded_need', 'whole_piece_need', 'rounding_extra', 'proposed_order_qty')} |
        dict(moq=parameters['moq'], pack_size=parameters['pack_size'])),
        _node('recommendation', 'Replenishment recommendation',
        'Advisory prefix-stock-v1 proposal; any pre-arrival shortage remains explicit.', refs, plan),
        _node('simulation', 'Simulated outcome',
        'Distinct periodic inventory-position policy reevaluates each review using completed demand only; scored and runoff costs are separate synthetic penalties.',
        [calculation_ref, _ref('decision.simulate', simulation['contract_version'])], dict(simulation=simulation, costs=costs, risk=risk,
            prefix_proposal_qty=plan['proposed_order_qty'],
            first_periodic_review=simulation['reviews'][0] | dict(
                raw_requirement=max(Fraction(0), simulation['reviews'][0]['target']-simulation['reviews'][0]['inventory_position'])),
            event_sequence=['receipts', 'prior commitments and backlog fulfillment',
                            'periodic review and order', 'new demand and fulfillment', 'end-of-day costs']))]
    return exact_json(dict(status='assessable', reasons=[], parameters=parameters,
        forecast=forecast_result, plan=plan, simulation=simulation, costs=costs, risk=risk,
        trace=trace, run_id=run_id))


def _comparison(baseline, scenario):
    def delta(a, b):
        return dict(baseline=a, scenario=b,
                    delta=str(Fraction(b)-Fraction(a)) if a is not None and b is not None else None)
    fields = {}
    for name in ('proposed_order_qty', 'immediate_fill_rate', 'cycle_service', 'total_cost',
                 'shortage_days', 'average_on_hand', 'backlog_piece_days'):
        def value(side):
            if side['status'] != 'assessable':
                return None
            return (side['plan'][name] if name == 'proposed_order_qty' else side['simulation']['metrics'][name])
        fields[name] = delta(value(baseline), value(scenario))
    def cost(side, group, field):
        if side['costs'] is None:
            return None
        return side['costs'][group][field] if field is not None else side['costs'][group]
    fields['costs'] = {group: {field: delta(cost(baseline, group, field), cost(scenario, group, field))
                              for field in ('holding', 'backlog', 'setup', 'total')}
                       for group in ('scored', 'runoff')}
    fields['costs']['total'] = delta(cost(baseline, 'total', None), cost(scenario, 'total', None))
    return fields


def evaluate(overrides=None, evidence=None):
    parameters = _parameters(overrides)
    try:
        archive = load_evidence() if evidence is None else validate_evidence(deepcopy(evidence))
    except (ValueError, OSError):
        baseline = _blocked(DEFAULTS.copy(), ['invalid_evidence_archive'])
        scenario = _blocked(parameters, ['invalid_evidence_archive'])
        return dict(contract_version=CONTRACT_VERSION, metadata=dict(synthetic=True, key=KEY.copy(),
                    cutoff=None, archive_digest=None, source_run_ids={}, on_hand=None, trusted_state=None),
                    defaults=DEFAULTS.copy(), controls=deepcopy(CONTROLS), baseline=baseline, scenario=scenario,
                    comparison=_comparison(baseline, scenario), warnings=['Invalid or missing archived evidence; all business outputs are suppressed.'])
    clean = archive['plans']['clean']
    inventory = clean['result']['inventory']
    metadata = dict(synthetic=True, key=KEY.copy(), cutoff=clean['context']['origin'],
        source_run_ids=dict(reliability=archive['reliability']['run_id'], forecast=archive['forecast']['run_id'],
                           clean_plan=clean['run_id'], incomplete_supply_plan=archive['plans']['incomplete_supply']['run_id']),
        archive_digest=archive['digest'], on_hand=inventory['on_hand'], units='whole pieces',
        confirmed_inbound_qty=sum(r['remaining_qty'] for r in clean['result']['supply']['inbound']
                                 if r['status'] == 'confirmed'),
        trusted_state=dict(on_hand=inventory['on_hand'], status='pass', cutoff=clean['context']['origin'],
                           ledger_batch_id=archive['reliability']['ledger_batch_id'],
                           snapshot_batch_id=archive['reliability']['snapshot_batch_id']))
    baseline = _side(DEFAULTS.copy(), archive)
    scenario = deepcopy(baseline) if parameters == DEFAULTS else _side(parameters, archive)
    return dict(contract_version=CONTRACT_VERSION, metadata=metadata, defaults=DEFAULTS.copy(),
        controls=deepcopy(CONTROLS), baseline=baseline, scenario=scenario,
        comparison=_comparison(baseline, scenario), warnings=[
            'Historical synthetic replay at the recorded cutoff; current stock is not revalidated.',
            'Recommendations are advisory; the simulation reevaluates a distinct periodic policy.',
            'Costs are synthetic finite-window penalties; service target is a comparison threshold.'])
