"""Read-only synthetic count corroboration; no source repair or physical-truth claim."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json

VERSION = 'physical-count-evidence-v1'
SYSTEM_FIELDS = set('source_system record_id sku_id warehouse_id as_of observed_at status uom quantity'.split())
MANIFEST_FIELDS = set('source_system session_id sku_id warehouse_id as_of freeze_start freeze_end observed_at uom coverage_complete frozen expected_rows'.split())
COUNT_FIELDS = set('source_system count_id session_id observer_id blind_count sku_id warehouse_id as_of counted_at observed_at quantity uom'.split())
REVIEW_FIELDS = set('source_system review_id proposal_id reviewer_id decision reason_code reviewed_at observed_at'.split())
REASONS = {'shrinkage','damage','count_correction','receiving_error','unexplained_variance'}


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def instant(value):
    if not isinstance(value,str): raise ValueError('timestamp must be an aware ISO8601 string')
    try: result=datetime.fromisoformat(value)
    except ValueError as error: raise ValueError('invalid timestamp') from error
    if result.tzinfo is None or result.utcoffset() is None: raise ValueError('naive timestamp')
    return result.astimezone(timezone.utc)


def text(value):
    if not isinstance(value,str) or not value.strip(): raise ValueError('identity/text must be nonempty')
    return value


def quantity(value):
    if type(value) is not int or value<0: raise ValueError('quantity must be a nonnegative integer')
    return value


def schema(row,fields):
    if not isinstance(row,dict) or set(row)!=fields: raise ValueError('source schema mismatch')


def ref(row,kind,identity):
    return dict(kind=kind,source_system=row.get('source_system') if isinstance(row,dict) and isinstance(row.get('source_system'),str) else None,
                record_id=row.get(identity) if isinstance(row,dict) and isinstance(row.get(identity),str) else None)


def evaluate(system,manifest,counts,*,evaluated_at,adjustment_reviews=()):
    evaluated=instant(evaluated_at)
    normalized=evaluated.isoformat()
    payload=dict(system=system,manifest=manifest,counts=counts,adjustment_reviews=adjustment_reviews)
    try: source_hash=digest(payload)
    except (TypeError,ValueError): source_hash=None
    report=dict(contract_version=VERSION,run_id='physical:'+digest(dict(contract_version=VERSION,source_sha256=source_hash,evaluated_at=normalized)) if source_hash else None,
        evaluated_at=normalized,source_payload_sha256=source_hash,as_of=None,sku_id=None,warehouse_id=None,
        physical_status='not_assessable',
        evidence_confidence='none',system_quantity=None,physical_quantity=None,variance_quantity=None,
        count_evidence=deepcopy(counts) if source_hash and isinstance(counts,(list,tuple)) else [],
        evidence_refs=[ref(system,'system','record_id'),ref(manifest,'manifest','session_id')],
        findings=[],proposal=None,adjustment_status='no_proposal',approved_adjustment_quantity=None,
        adjustment_evidence=[])
    def finding(reason,refs=()):
        report['findings'].append(dict(reason=reason,source_refs=list(refs)))
    def finish():
        report['evidence_refs']=sorted(report['evidence_refs'],key=lambda value:canonical(value))
        report['findings']=sorted(report['findings'],key=lambda value:canonical(value))
        return report
    if source_hash is None:
        finding('source_payload_not_json');return finish()
    if not isinstance(counts,(list,tuple)):
        finding('missing_count_records');return finish()
    try:
        schema(system,SYSTEM_FIELDS);schema(manifest,MANIFEST_FIELDS)
        for row,keys in ((system,('source_system','record_id','sku_id','warehouse_id','status','uom')),
                         (manifest,('source_system','session_id','sku_id','warehouse_id','uom'))):
            for key in keys: text(row[key])
        system_qty=quantity(system['quantity']);expected_rows=quantity(manifest['expected_rows'])
        cutoff=instant(system['as_of']);system_seen=instant(system['observed_at'])
        batch_cutoff=instant(manifest['as_of']);start=instant(manifest['freeze_start'])
        end=instant(manifest['freeze_end']);batch_seen=instant(manifest['observed_at'])
    except (ValueError,TypeError):
        finding('invalid_source_context');return finish()
    report.update(as_of=cutoff.isoformat(),sku_id=system['sku_id'],warehouse_id=system['warehouse_id'])
    if system['status']!='pass': finding('system_not_pass',[report['evidence_refs'][0]])
    if system['uom']!='each' or manifest['uom']!='each': finding('unsupported_uom')
    if (system['sku_id'],system['warehouse_id'],cutoff)!=(manifest['sku_id'],manifest['warehouse_id'],batch_cutoff):
        finding('count_scope_mismatch')
    if type(manifest['coverage_complete']) is not bool or not manifest['coverage_complete']: finding('incomplete_count_coverage')
    if type(manifest['frozen']) is not bool or not manifest['frozen']: finding('inventory_not_frozen')
    if expected_rows!=len(counts): finding('count_row_count_mismatch')
    if not start<=cutoff<=end or batch_seen<end: finding('invalid_freeze_window')
    if not cutoff<=system_seen<=evaluated: finding('system_not_available')
    if batch_seen>evaluated: finding('manifest_not_available')
    ids=set();valid=[]
    for row in counts:
        source_ref=ref(row,'count','count_id');report['evidence_refs'].append(source_ref)
        try:
            schema(row,COUNT_FIELDS)
            for key in ('source_system','count_id','session_id','observer_id','sku_id','warehouse_id','uom'): text(row[key])
            quantity(row['quantity']);count_cutoff=instant(row['as_of'])
            counted=instant(row['counted_at']);seen=instant(row['observed_at'])
        except (ValueError,TypeError):
            finding('invalid_count_row',[source_ref]);continue
        identity=(row['source_system'],row['count_id'])
        if identity in ids: finding('duplicate_count_identity',[source_ref])
        ids.add(identity)
        if (row['session_id'],row['sku_id'],row['warehouse_id'],count_cutoff,row['uom'])!=(manifest['session_id'],system['sku_id'],system['warehouse_id'],cutoff,'each'):
            finding('count_scope_mismatch',[source_ref])
        if type(row['blind_count']) is not bool or not row['blind_count']: finding('count_not_blind',[source_ref])
        if not cutoff<=counted<=end or counted<start: finding('count_outside_freeze',[source_ref])
        if seen<counted or seen>batch_seen: finding('count_observation_invalid',[source_ref])
        if seen>evaluated: finding('count_not_available',[source_ref])
        valid.append(row)
    if report['findings']:
        if adjustment_reviews:
            report['adjustment_status']='not_assessable';finding('review_without_proposal')
        return finish()
    valid=sorted(valid,key=lambda row:(row['source_system'],row['count_id']))
    report['count_evidence']=deepcopy(valid);report['system_quantity']=system_qty
    observers={row['observer_id'] for row in valid}
    values={row['quantity'] for row in valid}
    if len(values)>1:
        report.update(physical_status='recount_required',evidence_confidence='conflicting')
        finding('conflicting_counts')
    elif len(observers)<2:
        report.update(physical_status='recount_required',evidence_confidence='single_observer' if observers else 'none')
        finding('independent_recount_required')
    else:
        physical=next(iter(values));variance=physical-system_qty
        report.update(physical_status='confirmed_variance' if variance else 'confirmed_match',evidence_confidence='corroborated',
                      physical_quantity=physical,variance_quantity=variance)
        if variance:
            binding=dict(system=system,manifest=manifest,counts=valid)
            identity=digest(binding)
            report['proposal']=dict(proposal_id=identity,source_binding_sha256=identity,sku_id=system['sku_id'],
                warehouse_id=system['warehouse_id'],as_of=system['as_of'],before_quantity=system_qty,
                physical_quantity=physical,delta_quantity=variance)
            report['adjustment_status']='review_required'
    if not isinstance(adjustment_reviews,(list,tuple)):
        report['adjustment_status']='not_assessable';finding('invalid_review_records');return finish()
    if not adjustment_reviews: return finish()
    report['adjustment_evidence']=deepcopy(adjustment_reviews)
    if report['proposal'] is None:
        report['adjustment_status']='not_assessable';finding('review_without_proposal');return finish()
    review_ids=set();eligible=[];bad=False
    evidence_time=max([system_seen,batch_seen,*[instant(row['observed_at']) for row in valid]])
    for row in adjustment_reviews:
        source_ref=ref(row,'review','review_id');report['evidence_refs'].append(source_ref)
        try:
            schema(row,REVIEW_FIELDS)
            for key in ('source_system','review_id','proposal_id','reviewer_id','decision','reason_code'): text(row[key])
            reviewed=instant(row['reviewed_at']);seen=instant(row['observed_at'])
        except (ValueError,TypeError):
            finding('invalid_review_row',[source_ref]);bad=True;continue
        identity=(row['source_system'],row['review_id'])
        if identity in review_ids: finding('duplicate_review_identity',[source_ref]);bad=True
        review_ids.add(identity)
        if row['proposal_id']!=report['proposal']['proposal_id']: finding('review_binding_mismatch',[source_ref]);bad=True
        if row['reviewer_id'] in observers: finding('reviewer_not_independent',[source_ref]);bad=True
        if row['decision'] not in ('approve','reject') or row['reason_code'] not in REASONS:
            finding('invalid_review_decision',[source_ref]);bad=True
        if not evidence_time<=reviewed<=seen<=evaluated:
            finding('review_clock_invalid',[source_ref]);bad=True
        eligible.append(row)
    if len(adjustment_reviews)>1: finding('ambiguous_review_history');bad=True
    if bad:
        report['adjustment_status']='not_assessable'
    elif eligible[0]['decision']=='approve':
        report['adjustment_status']='approved_evidence';report['approved_adjustment_quantity']=report['variance_quantity']
    else: report['adjustment_status']='rejected'
    return finish()
