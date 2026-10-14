"""Fresh paired research; selection never consumes evaluation outcomes."""
from fractions import Fraction
from .forecasting import forecast
from .planner_loop import digest, run_case
from .planner_loop_audit import audit_case

METHODS = ('naive', 'mean', 'seasonal_naive')


def accuracy(trace, method, *, independent=False):
    """15 origin/lead pairs, including overlapping labels; exact point MAE/bias."""
    errors=[]; truth=trace['demand']+[0]*5
    for origin in (0,3,6):
        history=(trace['history']+truth[:origin])[-28:]
        if independent:
            predicted=([Fraction(history[-1])]*5 if method=='naive' else
                       [Fraction(sum(history),28)]*5 if method=='mean' else
                       list(map(Fraction,history[-7:-2])))
        else:
            predicted=forecast(history,method=method,horizon=5)
        errors.extend(p-truth[origin+i] for i,p in enumerate(predicted))
    total=sum(truth[origin+i] for origin in (0,3,6) for i in range(5))
    return dict(origin_lead_pairs=len(errors),mae=str(sum(map(abs,errors))/len(errors)),
                bias=str(sum(errors)/len(errors)),
                wape=str(sum(map(abs,errors))/total) if total else None,
                calibration=None,calibration_reason='Point baselines have no predictive intervals')


def conclusions(cells, protocol):
    families=sorted({trace['family'] for trace in protocol['traces']}); comparisons=[]
    for family in families:
        selection=cells[family+':selection']; evaluation=cells[family+':evaluation']
        selected=min(METHODS,key=lambda m:(Fraction(selection[m]['accuracy']['mae']),METHODS.index(m)))
        candidate=evaluation[selected]['case']['summary']; mean=evaluation['mean']['case']['summary']
        candidate_blocks=sum(r['report']['status']!='assessable' for r in evaluation[selected]['case']['reviews'])
        mean_blocks=sum(r['report']['status']!='assessable' for r in evaluation['mean']['case']['reviews'])
        fill=(Fraction(candidate['immediate_fill']) if candidate['immediate_fill'] is not None else None)
        baseline_fill=(Fraction(mean['immediate_fill']) if mean['immediate_fill'] is not None else None)
        reasons=[]
        if candidate['total_cost']>=mean['total_cost']:reasons.append('paid_cost_not_lower')
        if fill is None or baseline_fill is None:reasons.append('service_undefined')
        elif fill<baseline_fill:reasons.append('service_regression')
        if candidate_blocks>mean_blocks:reasons.append('additional_blocked_reviews')
        costs={m:evaluation[m]['case']['summary']['total_cost'] for m in METHODS}
        lowest=[m for m in METHODS if costs[m]==min(costs.values())]
        comparisons.append(dict(family=family,selected_from_selection=selected,
            evaluation_cost_delta_vs_mean=candidate['total_cost']-mean['total_cost'],
            evaluation_fill= candidate['immediate_fill'],mean_fill=mean['immediate_fill'],
            selected_blocked_reviews=candidate_blocks,mean_blocked_reviews=mean_blocks,
            decision_gate_passed=not reasons,decision_gate_failures=reasons,
            evaluation_cost_minima=lowest,unique_cost_winner=lowest[0] if len(lowest)==1 else None))
    return dict(families=comparisons,decision_gate_passes=sum(c['decision_gate_passed'] for c in comparisons),
                promoted_policy=None,global_winner=None)


def run(owner, runner, protocol, *, code_version):
    if protocol['version']!='forecast-decision-study-v1' or protocol['methods']!=list(METHODS):
        raise ValueError('Unknown frozen protocol')
    if runner.execute('SELECT current_user').fetchone()[0]!='ii_runner':
        raise ValueError('Restricted runner required')
    cells={}
    for trace in protocol['traces']:
        cells[trace['id']]={}
        for method in METHODS:
            config={k:trace[k] for k in ('demand','history','initial_stock','first_order_delay','notification','missing_day_zero')}
            case=run_case(owner,runner,namespace=protocol['namespace']+':'+trace['id']+':'+method,
                          method=method,code_version=code_version,**config)
            audit_case(case)
            cells[trace['id']][method]=dict(case=case,accuracy=accuracy(trace,method))
    report=dict(version=protocol['version'],synthetic_only=True,protocol_sha256=digest(protocol),
                runtime=dict(server_version=runner.info.server_version,runner='ii_runner'),cells=cells)
    report['conclusions']=conclusions(cells,protocol)
    audit(report,protocol)
    return report


def audit(report, protocol):
    if report['version']!=protocol['version'] or report['protocol_sha256']!=digest(protocol) or report['synthetic_only'] is not True:
        raise ValueError('Protocol binding changed')
    if set(report['cells'])!={t['id'] for t in protocol['traces']}:
        raise ValueError('Missing independent split')
    reviews=0;blocked=0
    for trace in protocol['traces']:
        cells=report['cells'][trace['id']]
        if set(cells)!=set(METHODS):raise ValueError('Losing policy omitted')
        for method,cell in cells.items():
            case=cell['case']
            if (case.get('method','mean')!=method or case['policy']!='actual' or
                case['namespace']!=protocol['namespace']+':'+trace['id']+':'+method or
                any(case[k]!=trace[k] for k in ('demand','history','initial_stock','first_order_delay','notification','missing_day_zero'))):
                raise ValueError('Unpaired physical trace')
            audit_case(case)
            if cell['accuracy']!=accuracy(trace,method,independent=True):raise ValueError('Independent forecast scores disagree')
            reviews+=len(case['reviews']);blocked+=sum(r['report']['status']!='assessable' for r in case['reviews'])
    if report['conclusions']!=conclusions(report['cells'],protocol):raise ValueError('Selection/evaluation boundary changed')
    return dict(status='pass',loops=sum(len(c) for c in report['cells'].values()),reviews=reviews,
                blocked_reviews=blocked,independent_paths=len(protocol['traces']),
                decision_gate_passes=report['conclusions']['decision_gate_passes'],promoted_policy=None)
