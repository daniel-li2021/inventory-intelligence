"""Bounded read-only synthetic catalog over immutable actual saved core reports."""
from copy import deepcopy
from datetime import date, datetime, timedelta
from fractions import Fraction
import gzip
import hashlib
import json
from math import ceil
from pathlib import Path
from uuid import UUID

from .copilot_planning import answer_planning
from .copilot import _validate_report
from .demand import midnight
from .forecasting import forecast
from .lab import BOUNDS, CONTROLS
from .planning_runs import exact_json
from .replenishment import project
from .decision import simulate

CONTRACT_VERSION='inventory-product-v1'
MAX_BYTES=64*1024*1024
CAPABILITIES={
    'prefix_projection':{'supported':True,'label':'Advisory prefix-stock-v1 proposal'},
    'periodic_simulation':{'supported':True,'label':'Separate periodic policy simulation; not execution of the prefix proposal'},
    'transfer':{'supported':False,'reason':'No transit or donor-service contract'},
    'expedite':{'supported':False,'reason':'No supplier capacity or feasible receipt contract'},
    'markdown':{'supported':False,'reason':'No price elasticity or margin evidence'},
    'purchase_execution':{'supported':False,'reason':'Read-only synthetic replay'},
    'commercial_savings':{'supported':False,'reason':'Synthetic penalty costs are not observed commercial savings'},
}


def archive_digest(value,exclude_digest=True):
    if exclude_digest and isinstance(value,dict):
        value={k:v for k,v in value.items() if k!='digest'}
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def normalize_report(report,objects):
    def visit(value,key=None):
        if key in ('source','training') and isinstance(value,dict):
            identity=archive_digest(value,exclude_digest=False)
            objects[identity]=value
            return {'$ref':identity}
        if isinstance(value,dict):
            return {k:visit(v,k) for k,v in value.items()}
        if isinstance(value,list):
            return [visit(v) for v in value]
        return value
    return visit(report)


def _expand(value,objects):
    if isinstance(value,dict):
        if set(value)=={'$ref'}:
            return objects[value['$ref']]
        return {k:_expand(v,objects) for k,v in value.items()}
    if isinstance(value,list):
        return [_expand(v,objects) for v in value]
    return value


def _report(catalog,run_id):
    """Internal view; interned source/training objects remain immutable."""
    return _expand(catalog['reports'][run_id]['report'],catalog['objects'])


def _require(condition):
    if not condition:
        raise ValueError('invalid or inconsistent product evidence')


def _instant(value):
    result=datetime.fromisoformat(value)
    _require(result.utcoffset()==timedelta(0))
    return result


def _exact(value):
    _require(not isinstance(value,float))
    if isinstance(value,dict):
        for child in value.values(): _exact(child)
    elif isinstance(value,list):
        for child in value: _exact(child)


def _inventory(source,origin,dimensions,run):
    _require(set(source)=={'batches','coverage','opening_balances','movements','snapshots'} and not source['movements'])
    _require(len(source['batches'])==2)
    batch_ids={run['ledger_batch_id'],run['snapshot_batch_id']}
    _require(all(r['batch_id'] in batch_ids for rows in source.values() for r in rows))
    known_keys={(s['sku_id'],w['warehouse_id']) for s in dimensions['skus'] for w in dimensions['warehouses']}
    quantities={}
    for kind,table,qty in (('ledger','opening_balances','quantity'),('snapshot','snapshots','on_hand_qty')):
        batch_id=run[kind+'_batch_id']
        batches=[r for r in source['batches'] if r['batch_id']==batch_id]
        _require(len(batches)==1)
        batch=batches[0]
        _require(batch['kind']==kind and batch['status']=='complete' and type(batch['watermark']) is int and batch['watermark']==0 and
                 _instant(batch['as_of'])==origin and _instant(batch['observed_at'])<=origin)
        rows=source[table]
        _require(all(r['batch_id']==batch_id for r in rows))
        if kind=='ledger': _require(_instant(batch['baseline_at'])<origin)
        keys=[(r['sku_id'],r['warehouse_id']) for r in rows]
        _require(len(set(keys))==len(keys) and set(keys)==known_keys)
        _require(type(batch['expected_row_count']) is int)
        _require(batch['expected_row_count']==(0 if kind=='ledger' else len(rows)))
        covered=[(r['sku_id'],r['warehouse_id']) for r in source['coverage'] if r['batch_id']==batch_id]
        _require(len(covered)==len(keys) and set(covered)==set(keys))
        for row in rows:
            _require(type(row[qty]) is int and 0<=row[qty]<=9223372036854775807)
            _require(_instant(row['as_of'])==(_instant(batch['baseline_at']) if kind=='ledger' else origin))
            if kind=='snapshot':
                _require(row['watermark']==0 and _instant(row['observed_at'])<=origin)
        quantities[kind]={key:row[qty] for key,row in zip(keys,rows)}
    _require(len(source['coverage'])==2*len(known_keys))
    _require(quantities['ledger']==quantities['snapshot'])
    for rows in source.values():
        identities=[r.get('row_id',r.get('batch_id')) for r in rows]
        _require(len(identities)==len(set(identities)))
    return quantities['snapshot']


def _training(series,context):
    origin=_instant(context['origin']); start=date.fromisoformat(context['start_day']); end=date.fromisoformat(context['origin_day'])
    _require((end-start).days==28 and origin==midnight(end) and len(series['days'])==28 and
             series['known_at']==context['origin'] and series['start_day']==context['start_day'] and
             series['end_day']==context['origin_day'] and series['batch']['batch_id']==context['batch_id'] and
             all(series[k]==context[k] for k in ('sku_id','warehouse_id')))
    reasons=[]
    for i,day in enumerate(series['days']):
        current=start+timedelta(days=i)
        _require(day['day']==current.isoformat())
        record=day['day_record']; orders=day['order_records']
        for row in ([record] if record else [])+orders:
            _require(row['batch_id']==context['batch_id'] and all(row[k]==context[k] for k in ('sku_id','warehouse_id')))
            _require(_instant(row['source_recorded_at'])<=_instant(row['observed_at'])<=origin)
        expected=[]
        if record is None: expected.append('missing_day_evidence')
        else:
            _require(record['business_day']==day['day'])
            _require(_instant(record['source_recorded_at'])>=midnight(current+timedelta(days=1)))
            if record['coverage']!='complete': expected.append('incomplete_day')
            if record['availability']!='available': expected.append('constrained_or_unknown_availability')
            if record['expected_lines']!=len(orders): expected.append('line_count_mismatch')
        for row in orders:
            _require(type(row['accepted_qty']) is int and 0<=row['accepted_qty']<=9223372036854775807 and row['status']=='accepted')
            _require(midnight(current)<=_instant(row['accepted_at'])<midnight(current+timedelta(days=1)))
            _require(_instant(row['accepted_at'])<=_instant(row['source_recorded_at']))
        _require(day['reasons']==sorted(expected))
        _require(day['quantity'] is None or type(day['quantity']) is int)
        _require(day['quantity']==(None if expected or series['reasons'] else sum(r['accepted_qty'] for r in orders)))
        reasons.extend(expected)
    _require((series['status']=='eligible')==(not reasons and not series['reasons']))
    for table in ('order_versions','day_versions'):
        rows=series[table]
        _require(len({r['row_id'] for r in rows})==len(rows))
        _require(all(_instant(r['source_recorded_at'])<=_instant(r['observed_at'])<=origin for r in rows))
    return series['status']=='eligible'


def validate_catalog(catalog):
    """Validate complete bounded package and every selected claim before serving it."""
    try:
        _require(isinstance(catalog,dict) and len(json.dumps(catalog))<=MAX_BYTES)
        _exact(catalog)
        _require(catalog['contract_version']=='inventory-product-evidence-v1' and catalog['synthetic'] is True and
                 catalog['business_data']=='synthetic only' and catalog['rules_version']=='inventory-insights-v1' and
                 catalog['digest']==archive_digest(catalog))
        dimensions=catalog['dimensions']
        _require(set(dimensions)=={'styles','skus','warehouses'} and len(dimensions['skus']) in (4,50) and len(dimensions['warehouses'])==2)
        for table,field in (('styles','style_id'),('skus','sku_id'),('warehouses','warehouse_id')):
            _require(len({r[field] for r in dimensions[table]})==len(dimensions[table]))
            _require(all(isinstance(r[field],str) and r[field].startswith('product') for r in dimensions[table]))
        styles={r['style_id'] for r in dimensions['styles']}
        for table,columns in (('styles',{'style_id','style_code','name'}),('skus',{'sku_id','style_id','sku_code','color','size','base_uom'}),('warehouses',{'warehouse_id','warehouse_code','name'})):
            _require(all(set(row)==columns and all(isinstance(value,str) and value.strip() for value in row.values()) for row in dimensions[table]))
        _require(all(s['style_id'] in styles and s['base_uom']=='each' for s in dimensions['skus']))
        _require(len(catalog['objects'])<=700 and len(catalog['reports'])<=610 and len(catalog['cutoffs'])==3)
        for identity,obj in catalog['objects'].items():
            _require(identity==archive_digest(obj,exclude_digest=False))
        expanded={run_id:_report(catalog,run_id) for run_id in catalog['reports']}
        for run_id,report in expanded.items():
            UUID(run_id); _require(report['run_id']==run_id)
            _require(catalog['reports'][run_id]['digest']==archive_digest(report,exclude_digest=False))
            if 'kind' in report:
                answer_planning(report)
                result=report['result']
                inputs=result['training'] if report['kind']=='forecast' else {k:result[k] for k in ('inventory','supply','training')}
                _require(report['input_digest']==archive_digest(dict(context=report['context'],inputs=inputs),exclude_digest=False))
        cutoffs=[b['cutoff'] for b in catalog['cutoffs']]
        _require(cutoffs==sorted(set(cutoffs)))
        keys={(s['sku_id'],w['warehouse_id']) for s in dimensions['skus'] for w in dimensions['warehouses']}
        selected_runs=set()
        for binding in catalog['cutoffs']:
            origin=midnight(date.fromisoformat(binding['cutoff']))
            reliability=expanded[binding['reliability_run_id']]
            _require(reliability['overall_status']=='pass' and not reliability['findings'] and
                     reliability['checks']==[dict(rule_id=f'R00{i}',status='pass') for i in range(1,6)] and
                     _instant(reliability['as_of'])==_instant(reliability['evaluated_at'])==origin)
            bound_keys=[(k['sku_id'],k['warehouse_id']) for k in binding['keys']]
            _require(len(bound_keys)==len(keys) and set(bound_keys)==keys)
            validated_sources={}
            for key in binding['keys']:
                fc,plan=(expanded[key[field]] for field in ('forecast_run_id','plan_run_id'))
                for report,kind in ((fc,'forecast'),(plan,'replenishment')):
                    _require(report['kind']==kind and report['context']['origin_day']==binding['cutoff'] and
                             report['context']['origin']==origin.isoformat() and report['context']['method']=='mean' and
                             all(report['context'][k]==key[k] for k in ('sku_id','warehouse_id')))
                    _require(report['run_id'] not in selected_runs); selected_runs.add(report['run_id'])
                pr=plan['result']; inv=pr['inventory']; supply=pr['supply']; context=plan['context']
                _require(context['policy_version']=='prefix-stock-v1' and context['reliability_run_id']==reliability['run_id'])
                _require(pr['training']==fc['result']['training'] and context['batch_id']==fc['context']['batch_id'])
                eligible=_training(pr['training'],context)
                _require((fc['status']=='assessable')==eligible and fc['context']['horizon']==28)
                if eligible:
                    predictions=exact_json(forecast([d['quantity'] for d in pr['training']['days']],method='mean',horizon=28))
                    _require(fc['result']['predictions']==predictions)
                else:
                    _require(fc['result']['predictions'] is None)
                _require(all(inv['run'][k]==reliability[k] for k in ('run_id','contract_version','code_version','ledger_batch_id','snapshot_batch_id','as_of','evaluated_at','overall_status')))
                _require(inv['run']['run_id']==reliability['run_id'] and inv['checks']==reliability['checks'] and not inv['reasons'] and not inv['findings'])
                _require(inv['current_validation']['checks']==reliability['checks'] and not inv['current_validation']['findings'])
                identity=archive_digest(inv['source'],exclude_digest=False)
                if identity not in validated_sources:
                    validated_sources[identity]=_inventory(inv['source'],origin,dimensions,reliability)
                _require(inv['on_hand']==validated_sources[identity][key['sku_id'],key['warehouse_id']])
                batch=supply['batch']; policy=supply['policy']
                _require(batch['batch_id']==context['supply_batch_id'] and batch['as_of']==origin.isoformat() and
                         all(batch[k]==key[k] for k in ('sku_id','warehouse_id')) and _instant(batch['observed_at'])<=origin)
                _require(type(batch['reservations_complete']) is bool and type(batch['inbound_complete']) is bool)
                # V1 controls replace one obligation and one confirmed receipt.
                _require(len(supply['reservations'])==1 and supply['reservations'][0]['status']=='open' and
                         len(supply['inbound'])==2 and sorted(r['status'] for r in supply['inbound'])==['confirmed','pending'])
                supply_rows=supply['policies']+supply['reservations']+supply['inbound']
                row_ids=[row['row_id'] for row in supply_rows]
                _require(all(isinstance(identity,str) and identity.strip() for identity in row_ids) and len(set(row_ids))==len(row_ids))
                _require(type(batch['expected_reservations']) is int and type(batch['expected_inbound']) is int)
                _require(batch['expected_reservations']==len(supply['reservations']) and batch['expected_inbound']==len(supply['inbound']))
                _require(len(supply['policies'])==1 and supply['policies'][0]==policy and policy['batch_id']==batch['batch_id'])
                _require(_instant(policy['source_recorded_at'])<=_instant(policy['observed_at'])<=origin)
                for field in ('lead_days','review_days','safety_qty','pack_size','moq'):
                    _,minimum,maximum=BOUNDS[field]; _require(type(policy[field]) is int and minimum<=policy[field]<=maximum)
                supply_reasons=[]
                if not batch['reservations_complete'] or not batch['inbound_complete'] or batch['status']!='complete':
                    supply_reasons.append('incomplete_or_mismatched_supply')
                for table,id_field,statuses,dayfield in (('reservations','reservation_id',('open','fulfilled','cancelled'),'due_day'),('inbound','inbound_id',('confirmed','pending','cancelled'),'arrival_day')):
                    rows=supply[table]
                    _require(all(isinstance(r[field],str) and r[field].strip() for r in rows for field in ('source_system',id_field)))
                    _require(len({(r['source_system'],r[id_field]) for r in rows})==len(rows))
                    for row in rows:
                        _require(row['batch_id']==batch['batch_id'] and type(row['remaining_qty']) is int and 0<=row['remaining_qty']<=9223372036854775807 and row['status'] in statuses)
                        _require(_instant(row['source_recorded_at'])<=_instant(row['observed_at'])<=origin)
                        _require(date.fromisoformat(row[dayfield])>=date.fromisoformat(binding['cutoff']))
                _require(supply['reasons']==supply_reasons)
                reasons=supply_reasons+(['ineligible_or_unavailable_forecast'] if not eligible or supply_reasons else [])
                _require(pr['reasons']==sorted(reasons) and (plan['status']=='assessable')==(not reasons))
                if reasons:
                    _require(pr['proposed_order_qty'] is None and pr['projection'] is None)
                else:
                    _require(pr['forecast']['predictions']==fc['result']['predictions'][:policy['lead_days']+policy['review_days']])
                future=key['future_demand']
                _require(len(future['quantities'])==28 and all(type(q) is int and q>=0 for q in future['quantities']) and future['id'].startswith(context['batch_id'].rsplit(':demand',1)[0]))
            _require(len(validated_sources)==1)
        control=catalog['controls']['duplicate_inventory']
        defect=expanded[control['reliability_run_id']]; blocked=expanded[control['plan_run_id']]
        _validate_report(defect)
        _require(defect['overall_status']=='fail' and blocked['status']=='not_assessable' and
                 blocked['context']['reliability_run_id']==defect['run_id'] and
                 'nonpassing_or_missing_inventory_run' in blocked['result']['reasons'] and
                 blocked['result']['proposed_order_qty'] is None)
        latest=catalog['cutoffs'][-1]
        selected=next(k for k in latest['keys'] if all(k[field]==blocked['context'][field] for field in ('sku_id','warehouse_id')))
        normal=expanded[selected['plan_run_id']]
        _require(all(blocked['context'][field]==value for field,value in normal['context'].items() if field!='reliability_run_id'))
        _require(defect['as_of']==defect['evaluated_at']==normal['context']['origin'])
        _require(all(defect[k]==normal['result']['inventory']['run'][k]+':duplicate-control' for k in ('ledger_batch_id','snapshot_batch_id')))
        _require(blocked['result']['training']==normal['result']['training'] and blocked['result']['supply']==normal['result']['supply'])
        _require(blocked['result']['inventory']['run']=={k:v for k,v in defect.items() if k not in ('checks','findings')})
        _require(blocked['result']['inventory']['checks']==defect['checks'])
        _require([{k:v for k,v in f.items() if k!='run_id'} for f in blocked['result']['inventory']['findings']]==defect['findings'])
        _require(len(defect['findings'])==1)
        finding=defect['findings'][0]
        _require(finding['rule_id']=='R005' and finding['reason']=='duplicate_snapshot' and
                 all(finding[field]==selected[field] for field in ('sku_id','warehouse_id')))
        snapshots=[row for row in normal['result']['inventory']['source']['snapshots'] if all(row[field]==selected[field] for field in ('sku_id','warehouse_id'))]
        _require(len(snapshots)==1)
        expected=snapshots[0]|dict(batch_id=defect['snapshot_batch_id'],row_id=snapshots[0]['row_id']+':duplicate-control')
        duplicate=expected|dict(row_id=expected['row_id']+':extra')
        records=finding['evidence']['source_records']
        _require(finding['evidence']['row_count']==2 and records==[dict(source='snapshot',record=expected),dict(source='snapshot',record=duplicate)] and
                 finding['source_row_ids']==[expected['row_id'],duplicate['row_id']])
        return catalog
    except (KeyError,TypeError,ValueError,OverflowError,AttributeError,RecursionError,StopIteration):
        raise ValueError('invalid or inconsistent product evidence') from None


def load_catalog(path=None):
    path=Path(path) if path else Path(__file__).with_name('product_evidence.json.gz')
    _require(path.stat().st_size<=MAX_BYTES)
    if path.suffix=='.gz':
        with gzip.open(path,'rb') as stream:
            raw=stream.read(MAX_BYTES+1)
    else: raw=path.read_bytes()
    _require(len(raw)<=MAX_BYTES)
    return validate_catalog(json.loads(raw))


def _binding(catalog,cutoff):
    cutoff=cutoff or catalog['cutoffs'][-1]['cutoff']
    matches=[b for b in catalog['cutoffs'] if b['cutoff']==cutoff]
    if len(matches)!=1: raise ValueError('unknown cutoff')
    return matches[0]


def _key(catalog,cutoff,sku_id,warehouse_id):
    binding=_binding(catalog,cutoff)
    keys=[k for k in binding['keys'] if k['sku_id']==sku_id and k['warehouse_id']==warehouse_id]
    if len(keys)!=1: raise ValueError('unknown catalog key')
    return binding,keys[0]


def _rational(value):
    value=Fraction(value)
    return dict(numerator=str(value.numerator),denominator=str(value.denominator))


def _wire(value):
    if isinstance(value,Fraction): return _rational(value)
    if type(value) is int: return str(value)
    if isinstance(value,(datetime,date)): return value.isoformat()
    if isinstance(value,dict): return {k:_wire(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [_wire(v) for v in value]
    return value


def _envelope(catalog,binding):
    return dict(contract_version=CONTRACT_VERSION,archive_digest=catalog['digest'],synthetic=True,cutoff=binding['cutoff'])


def _ref(source,identity): return dict(source=source,id=identity)


def _card(catalog,binding,key):
    plan=_report(catalog,key['plan_run_id']); result=plan['result']
    sku=next(s for s in catalog['dimensions']['skus'] if s['sku_id']==key['sku_id'])
    style=next(s for s in catalog['dimensions']['styles'] if s['style_id']==sku['style_id'])
    location=next(w for w in catalog['dimensions']['warehouses'] if w['warehouse_id']==key['warehouse_id'])
    blocked=plan['status']!='assessable'
    end=Fraction(result['end_projected_balance']) if not blocked else None
    exposure=Fraction(result['proposed_order_qty']) if not blocked and result['proposed_order_qty'] else max(Fraction(0),end-result['supply']['policy']['safety_qty']) if not blocked else None
    category='evidence' if blocked else 'risk' if result['proposed_order_qty'] or result['pre_arrival_shortage_days'] else 'opportunity' if exposure>=20 else 'none'
    title={'risk':'Replenishment attention','opportunity':'Review surplus exposure','evidence':'Evidence incomplete','none':'Within declared policy'}[category]
    explanation={'risk':'Prefix demand and reservations create a safety shortfall; the advisory quantity respects MOQ and packs.',
                 'opportunity':'Projected terminal surplus is at least 20 pieces above declared safety. Review before buying; transfer and markdown are unsupported.',
                 'evidence':'Required saved evidence is incomplete. Quantities and comparisons are suppressed; missing does not mean zero.',
                 'none':'No replenishment shortfall or surplus highlight under these declared thresholds.'}[category]
    daily=Fraction(_report(catalog,key['forecast_run_id'])['result']['predictions'][0]) if not blocked else None
    context=plan['context']; policy=result['supply']['policy']
    comparison_signature=archive_digest(dict(sku_id=key['sku_id'],warehouse_id=key['warehouse_id'],unit=sku['base_uom'],
        rules_version=catalog['rules_version'],model_version=plan['model_version'],method=context['method'],
        policy_version=context['policy_version'],business_timezone=context['business_timezone'],
        training_window_days=(date.fromisoformat(context['origin_day'])-date.fromisoformat(context['start_day'])).days,
        projection_days=policy['lead_days']+policy['review_days'],
        policy={field:policy[field] for field in ('lead_days','review_days','safety_qty','pack_size','moq')}),exclude_digest=False)
    return dict(id=key['sku_id']+'|'+key['warehouse_id'],sku_id=key['sku_id'],warehouse_id=key['warehouse_id'],
        sku_code=sku['sku_code'],style_id=sku['style_id'],style=style['name'],color=sku['color'],size=sku['size'],location=location['name'],
        insight_id='insight:'+archive_digest(dict(rules_version=catalog['rules_version'],rule_id={'risk':'I001','opportunity':'I002','evidence':'I003','none':'I000'}[category],sku_id=key['sku_id'],warehouse_id=key['warehouse_id']),exclude_digest=False),
        observation_id='observation:'+archive_digest(dict(archive=catalog['digest'],cutoff=binding['cutoff'],run=plan['run_id'],rule_id={'risk':'I001','opportunity':'I002','evidence':'I003','none':'I000'}[category]),exclude_digest=False),
        rule_id={'risk':'I001','opportunity':'I002','evidence':'I003','none':'I000'}[category],
        rules_version=catalog['rules_version'],as_of=plan['context']['origin'],known_at=plan['context']['origin'],
        evaluated_at=_report(catalog,binding['reliability_run_id'])['evaluated_at'],report_created_at=plan['created_at'],
        category=category,status=plan['status'],title=title,explanation=explanation,
        inventory_status='assessable' if not result['inventory']['reasons'] else 'not_assessable',
        on_hand=str(result['inventory']['on_hand']) if result['inventory']['on_hand'] is not None else None,
        proposed_order_qty=None if blocked else str(result['proposed_order_qty']),
        forecast_daily=_rational(daily) if daily is not None else None,exposure=_rational(exposure) if exposure is not None else None,
        history_state='unknown',comparison_signature=comparison_signature,reasons=result['reasons'],
        references=[_ref('planning.runs',plan['run_id']),_ref('planning.runs',key['forecast_run_id']),_ref('reliability.runs',binding['reliability_run_id'])])


def _transition(before,after):
    if before is None or after['status']!='assessable' or before['comparison_signature']!=after['comparison_signature']: return 'unknown'
    if before['status']!='assessable': return 'new' if after['category'] in ('risk','opportunity') else 'unknown'
    if before['category']!=after['category']:
        if before['category']=='risk' and after['category']!='risk': return 'improved'
        return 'new' if after['category']!='none' else 'improved'
    def exposure(card):
        q=card['exposure']; return Fraction(int(q['numerator']),int(q['denominator']))
    a,b=exposure(before),exposure(after)
    return 'persistent' if a==b else 'worsening' if b>a else 'improved'


def _cards(catalog,binding):
    previous=next((b for b in reversed(catalog['cutoffs']) if b['cutoff']<binding['cutoff']),None)
    old={c['id']:c for c in [_card(catalog,previous,k) for k in previous['keys']]} if previous else {}
    cards=[_card(catalog,binding,k) for k in binding['keys']]
    for card in cards: card['history_state']=_transition(old.get(card['id']),card)
    return cards


def overview(catalog,cutoff=None):
    binding=_binding(catalog,cutoff); cards=_cards(catalog,binding)
    summary={name:sum(c['category']==name for c in cards) for name in ('risk','opportunity','evidence','none')}
    summary.update(keys=len(cards),assessable=sum(c['status']=='assessable' for c in cards),blocked=summary['evidence'])
    groups={category:sorted((c for c in cards if c['category']==category),key=_priority)[:limit]
            for category,limit in (('risk',3),('opportunity',2),('evidence',3))}
    highlights=groups['risk']+groups['opportunity']+groups['evidence']
    return _envelope(catalog,binding)|dict(cutoffs=[b['cutoff'] for b in catalog['cutoffs']],summary=summary,
        highlights=highlights,highlight_groups=groups,highlight_policy='Up to three highest-priority risks, two surplus opportunities and three evidence blockers; exact key tie-breaks.',dimensions=deepcopy(catalog['dimensions']),capabilities=deepcopy(CAPABILITIES),
        controls=deepcopy(catalog['controls']),rules_version=catalog['rules_version'])


def _priority(card):
    rank={'evidence':0,'risk':1,'opportunity':2,'none':3}
    q=card['exposure']; exposure=Fraction(int(q['numerator']),int(q['denominator'])) if q else Fraction(0)
    return rank[card['category']],-exposure,card['sku_id'],card['warehouse_id']


def explore(catalog,cutoff=None,filters=None,page=1,page_size=20,sort='priority'):
    filters=filters or {}
    allowed={'style_id','color','size','warehouse_id','category','status','search'}
    if not isinstance(filters,dict) or set(filters)-allowed or any(not isinstance(v,str) for v in filters.values()): raise ValueError('invalid filter')
    if type(page) is not int or page<1 or type(page_size) is not int or not 1<=page_size<=100 or sort not in ('priority','sku','stock'): raise ValueError('invalid page or sort')
    binding=_binding(catalog,cutoff); cards=_cards(catalog,binding); available=cards
    for field,value in filters.items():
        if not value: continue
        if field=='search': cards=[c for c in cards if value.casefold() in ' '.join(str(c[k]) for k in ('sku_code','style','color','size','location')).casefold()]
        else:
            valid={'category':{'risk','opportunity','evidence','none'},'status':{'assessable','not_assessable'}}.get(field,{c[field] for c in available})
            if value not in valid: raise ValueError('unknown filter value')
            cards=[c for c in cards if c[field]==value]
    if sort=='priority': cards.sort(key=_priority)
    elif sort=='sku': cards.sort(key=lambda c:(c['sku_id'],c['warehouse_id']))
    else: cards.sort(key=lambda c:(c['on_hand'] is None,int(c['on_hand'] or 0),c['id']))
    total=len(cards); pages=max(1,ceil(total/page_size))
    if page>pages: raise ValueError('page outside result')
    matrix=[{k:c[k] for k in ('id','sku_id','warehouse_id','style_id','color','size','status','on_hand','category')} for c in cards]
    return _envelope(catalog,binding)|dict(items=cards[(page-1)*page_size:page*page_size],total=total,page=page,page_size=page_size,pages=pages,matrix=matrix,dimensions=deepcopy(catalog['dimensions']))


def detail(catalog,cutoff,sku_id,warehouse_id):
    binding,key=_key(catalog,cutoff,sku_id,warehouse_id); report=_report(catalog,key['plan_run_id']); result=report['result']
    card=next(c for c in _cards(catalog,binding) if c['id']==sku_id+'|'+warehouse_id)
    trace=[dict(stage=stage,label=label,explanation=explanation,references=refs,data=data) for stage,label,explanation,refs,data in (
        ('reliability','Saved inventory reliability','All catalog keys require the same passing R001–R005 run.',[card['references'][2]],dict(status=result['inventory']['run']['overall_status'])),
        ('demand','Origin-known demand','Mean of 28 complete accepted-order days; future revisions excluded.',[card['references'][1]],dict(status=result['training']['status'],start_day=report['context']['start_day'],end_day=report['context']['origin_day'])),
        ('supply','Supply completeness','Only confirmed inbound counts. Pending inbound is excluded.',[_ref('planning_input.supply_batches',report['context']['supply_batch_id'])],dict(reasons=result['supply']['reasons'])),
        ('proposal','Prefix proposal','Exact maximum safety shortfall after lead time, rounded to whole packs/MOQ. Advisory only.',[card['references'][0]],dict(proposed_order_qty=card['proposed_order_qty'],reasons=result['reasons'])))]
    return _envelope(catalog,binding)|card|dict(clocks=dict(business_cutoff=report['context']['origin'],decision_known_at=report['context']['origin'],
        inventory_evaluated_at=card['evaluated_at'],report_created_at=report['created_at'],business_timezone=report['context']['business_timezone'],
        training_start=report['context']['start_day'],training_end=report['context']['origin_day']),
        trace=trace,capabilities=deepcopy(CAPABILITIES),evidence=dict(sections=['inventory','training','supply','plan','forecast','reliability'],references=card['references']),
        explanation=card['explanation']+' '+('The saved proposal is blocked: '+', '.join(card['reasons'])+'.' if card['reasons'] else 'This explanation is deterministic and cites saved synthetic runs; no model call.'))


def evidence(catalog,cutoff,sku_id,warehouse_id,section,page=1,page_size=20):
    binding,key=_key(catalog,cutoff,sku_id,warehouse_id)
    if type(page) is not int or page<1 or type(page_size) is not int or not 1<=page_size<=100: raise ValueError('invalid evidence page')
    report=_report(catalog,key['plan_run_id']); result=report['result']
    if section=='inventory':
        rows=[dict(table=t,**r) for t,records in result['inventory']['source'].items() for r in records if t=='batches' or (r.get('sku_id'),r.get('warehouse_id'))==(sku_id,warehouse_id)]
    elif section=='training': rows=result['training']['days']
    elif section=='supply': rows=[dict(table=t,**r) for t in ('reservations','inbound','policies') for r in result['supply'][t]]+[dict(table='supply_batches',**result['supply']['batch'])]
    elif section=='plan': rows=result['projection'] or []
    elif section=='forecast': rows=[dict(day=(date.fromisoformat(binding['cutoff'])+timedelta(days=i)).isoformat(),quantity=q) for i,q in enumerate(_report(catalog,key['forecast_run_id'])['result']['predictions'] or [])]
    elif section=='reliability': rows=[_report(catalog,binding['reliability_run_id'])]
    else: raise ValueError('unknown evidence section')
    pages=max(1,ceil(len(rows)/page_size))
    if page>pages: raise ValueError('page outside evidence')
    return _envelope(catalog,binding)|dict(section=section,sku_id=sku_id,warehouse_id=warehouse_id,status=report['status'],reasons=result['reasons'],rows=_wire(rows[(page-1)*page_size:page*page_size]),total=len(rows),page=page,page_size=page_size,pages=pages,references=[_ref('planning.runs',report['run_id'])])


def history(catalog,sku_id,warehouse_id):
    points=[]; before=None
    for binding in catalog['cutoffs']:
        _,key=_key(catalog,binding['cutoff'],sku_id,warehouse_id); card=_card(catalog,binding,key)
        card['history_state']=_transition(before,card)
        reason=('no_previous_cutoff' if before is None else 'incompatible_comparison_basis' if before['comparison_signature']!=card['comparison_signature']
                else 'incomplete_evidence' if before['status']!='assessable' or card['status']!='assessable' else None)
        comparable=reason is None
        delta=str(int(card['on_hand'])-int(before['on_hand'])) if comparable and before['on_hand'] is not None and card['on_hand'] is not None else None
        points.append(dict(cutoff=binding['cutoff'],item=card,state=card['history_state'],stock_delta=delta,comparable=comparable,comparison_reason=reason))
        before=card
    return dict(contract_version=CONTRACT_VERSION,archive_digest=catalog['digest'],synthetic=True,sku_id=sku_id,warehouse_id=warehouse_id,points=points,
        comparison_basis='An emerging insight after missing coverage is new but numeric comparability remains unavailable. Comparability requires identical key/unit/rules/model/policy/timezone/window and lead/review/safety/pack/MOQ signature. Changed scope is unknown with no numeric delta. Same 28-day origin-known training windows; independent synthetic snapshots, not a movement narrative.')


def control(catalog,name):
    """Inspect an isolated saved defect without relabelling the clean catalog."""
    if name!='duplicate_inventory':
        raise ValueError('unknown product control')
    saved=catalog['controls'][name]
    reliability=_report(catalog,saved['reliability_run_id'])
    report=_report(catalog,saved['plan_run_id'])
    result=report['result']
    return _envelope(catalog,catalog['cutoffs'][-1])|dict(name=name,
        explanation='Separate synthetic duplicate-snapshot fixture. Its nonpassing global reliability run blocks planning even for locally clean keys; it does not replace the normal catalog.',
        reliability=_wire(reliability),blocked_plan=dict(run_id=report['run_id'],
            sku_id=report['context']['sku_id'],warehouse_id=report['context']['warehouse_id'],
            status=report['status'],reasons=deepcopy(result['reasons']),
            proposed_order_qty=result['proposed_order_qty'],projection=deepcopy(result['projection'])),
        references=[_ref('reliability.runs',reliability['run_id']),_ref('planning.runs',report['run_id'])])


def _parameters(report,overrides):
    result=report['result']; policy=result['supply']['policy']
    defaults={name:spec[0] for name,spec in BOUNDS.items()}
    defaults.update({k:policy[k] for k in ('lead_days','review_days','safety_qty','pack_size','moq')})
    defaults['reservation_qty']=sum(r['remaining_qty'] for r in result['supply']['reservations'] if r['status']=='open')
    origin=date.fromisoformat(report['context']['origin_day'])
    confirmed=[r for r in result['supply']['inbound'] if r['status']=='confirmed']
    defaults['inbound_day']=(date.fromisoformat(confirmed[0]['arrival_day'])-origin).days if confirmed else 1
    defaults['evidence_case']='clean'
    if overrides is None: overrides={}
    if not isinstance(overrides,dict) or set(overrides)-(set(BOUNDS)|{'evidence_case'}): raise ValueError('unknown scenario parameter')
    values=defaults|overrides
    for name,(_,minimum,maximum) in BOUNDS.items():
        if type(values[name]) is not int or not minimum<=values[name]<=maximum: raise ValueError('invalid '+name)
    if values['evidence_case'] not in ('clean','incomplete_supply'): raise ValueError('invalid evidence_case')
    return values


def _side(catalog,binding,key,parameters):
    report=_report(catalog,key['plan_run_id']); result=report['result']; refs=[_ref('planning.runs',report['run_id']),_ref('planning.runs',key['forecast_run_id'])]
    run_id='product:'+archive_digest(dict(archive=catalog['digest'],key=key['plan_run_id'],parameters=parameters),exclude_digest=False)
    if report['status']!='assessable' or parameters['evidence_case']=='incomplete_supply':
        return dict(status='not_assessable',reasons=result['reasons'] or ['counterfactual_incomplete_supply'],parameters=parameters,plan=None,forecast=None,simulation=None,costs=None,risk=None,trace=[],run_id=None)
    origin=date.fromisoformat(binding['cutoff']); percent=parameters['demand_percent']
    training=[ceil(Fraction(d['quantity']*percent,100)) for d in result['training']['days']]
    demand=[ceil(Fraction(q*percent,100)) for q in key['future_demand']['quantities']]
    predictions=forecast(training,method='mean',horizon=28)
    policy={k:parameters[k] for k in ('lead_days','review_days','safety_qty','pack_size','moq')}
    reservations=[r|dict(due_day=origin,remaining_qty=parameters['reservation_qty']) for r in result['supply']['reservations']]
    inbound=[r|dict(arrival_day=origin+timedelta(days=parameters['inbound_day']) if r['status']=='confirmed' else date.fromisoformat(r['arrival_day'])) for r in result['supply']['inbound']]
    plan=project(on_hand=result['inventory']['on_hand'],forecasts=predictions[:parameters['lead_days']+parameters['review_days']],reservations=reservations,inbound=inbound,origin_day=origin,policy=policy)
    runoff=parameters['lead_days']+parameters['supplier_delay_days']+parameters['review_days']
    delays=[parameters['supplier_delay_days']]*len(range(0,28+runoff,parameters['review_days']))
    simulation=simulate(training,demand,method='mean',on_hand=result['inventory']['on_hand'],**policy,
        commitments=[dict(id=r['reservation_id'],due_day=0,quantity=r['remaining_qty']) for r in reservations if r['remaining_qty']],
        inbound=[dict(id=r['inbound_id'],arrival_day=parameters['inbound_day'],quantity=r['remaining_qty']) for r in inbound if r['status']=='confirmed' and r['remaining_qty']],
        supplier_delays=delays,holding_cost=1,backlog_cost=10,order_cost=2)
    simulation['assumptions'].update(new_demand_source=key['future_demand']['id'],delay_known_to_ordering=False,
        recommendation_policy='prefix-stock-v1; distinct periodic simulation is not its executed outcome')
    def charges(scored):
        return {name:sum((d[field] for d in simulation['days'] if d['scored'] is scored),Fraction(0)) for name,field in (('holding','holding_cost'),('backlog','backlog_cost'),('setup','order_cost'),('total','total_cost'))}
    costs=dict(rates=dict(holding=Fraction(1),backlog=Fraction(10),setup=Fraction(2)),scored=charges(True),runoff=charges(False),total=simulation['metrics']['total_cost'])
    target=Fraction(parameters['service_target_percent'],100); fill=simulation['metrics']['immediate_fill_rate']
    risk=dict(pre_arrival_shortage_days=plan['pre_arrival_shortage_days'],stockout_days=[d['day'] for d in plan['projection'] if d['balance_with_order']<0],service_target=target,meets_service_target=fill>=target if fill is not None else None,
        definition='Exact deterministic prefix exposure; service and penalty costs belong to a distinct periodic policy, not prefix order execution.')
    refs=[_ref('product.calculation',run_id),_ref('planning.runs.inputs',report['run_id']),_ref('planning.runs.inputs',key['forecast_run_id'])]
    trace=[dict(stage='proposal',label='Prefix proposal',explanation='Saved inputs with explicit counterfactual copies. Exact pieces, MOQ and pack rounding.',references=refs,data=plan),dict(stage='simulation',label='Periodic policy',explanation='Separate periodic ordering policy over 28 declared synthetic demand days plus runoff; synthetic penalties, not realized savings.',references=refs+[_ref('synthetic.future_demand',key['future_demand']['id'])],data=dict(metrics=simulation['metrics'],costs=costs))]
    return _wire(dict(status='assessable',reasons=[],parameters=parameters,plan=plan,forecast=dict(predictions=predictions,demand=demand,source_run_id=key['forecast_run_id']),simulation=simulation,costs=costs,risk=risk,trace=trace,run_id=run_id))


def scenario(catalog,cutoff,sku_id,warehouse_id,overrides=None):
    binding,key=_key(catalog,cutoff,sku_id,warehouse_id); report=_report(catalog,key['plan_run_id'])
    defaults=_parameters(report,None); parameters=_parameters(report,overrides)
    baseline=_side(catalog,binding,key,defaults); side=_side(catalog,binding,key,parameters)
    fields={}
    def rational(value):
        return Fraction(int(value['numerator']),int(value['denominator'])) if isinstance(value,dict) else Fraction(value)
    compatible=baseline['status']==side['status']=='assessable'
    for name in ('proposed_order_qty','immediate_fill_rate','cycle_service','total_cost','shortage_days','average_on_hand','backlog_piece_days'):
        def value(s):
            if s['status']!='assessable': return None
            return s['plan'][name] if name=='proposed_order_qty' else s['simulation']['metrics'][name]
        a,b=value(baseline),value(side)
        common_window=name!='total_cost' or defaults['lead_days']+defaults['supplier_delay_days']+defaults['review_days']==parameters['lead_days']+parameters['supplier_delay_days']+parameters['review_days']
        fields[name]=dict(baseline=a,scenario=b,compatible=compatible and common_window,delta=_rational(rational(b)-rational(a)) if a is not None and b is not None and common_window else None)
    for name in ('holding','backlog','setup','total'):
        a=baseline['costs']['scored'][name] if compatible else None; b=side['costs']['scored'][name] if compatible else None
        fields['scored_'+name+'_cost']=dict(baseline=a,scenario=b,compatible=compatible,delta=_rational(rational(b)-rational(a)) if compatible else None)
    return _envelope(catalog,binding)|dict(baseline=baseline,scenario=side,parameters=parameters,
        controls={k:CONTROLS[k]|dict(default=defaults[k]) for k in BOUNDS}|{'evidence_case':CONTROLS['evidence_case']},capabilities=deepcopy(CAPABILITIES),
        comparison=dict(compatible=compatible,scored_days=28,baseline_runoff_days=defaults['lead_days']+defaults['supplier_delay_days']+defaults['review_days'],scenario_runoff_days=parameters['lead_days']+parameters['supplier_delay_days']+parameters['review_days'],fields=fields,notes=['Advisory prefix quantities; simulation metrics describe a separate periodic policy.',
            '28 scored days are shared; changed lead/delay/review can alter runoff length. Total cost includes runoff and is not a common-window savings claim.']))
