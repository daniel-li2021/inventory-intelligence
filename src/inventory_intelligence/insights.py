"""Additive deterministic discovery over validated, origin-known saved evidence."""
from fractions import Fraction

from .product import _report, _card, archive_digest, _rational, _ref, _envelope, _binding

VERSION = 'inventory-insights-v2'


def discover(catalog, cutoff=None):
    binding = _binding(catalog,cutoff)
    previous = next((b for b in reversed(catalog['cutoffs']) if b['cutoff'] < binding['cutoff']),None)
    old_keys = {(k['sku_id'],k['warehouse_id']): k for k in previous['keys']} if previous else {}
    findings, unknown = [], []
    cards = {c['id']:c for c in (_card(catalog,binding,k) for k in binding['keys'])}

    def add(rule, key, category, title, observation, values, refs, next_step, hypothesis=None, members=None):
        identity = dict(version=VERSION,rule=rule,keys=sorted(members or [key['sku_id']+'|'+key['warehouse_id']]))
        if rule=='I204': identity['inbound_id']=values['inbound_id']
        findings.append(dict(id='insight:'+archive_digest(identity,False),observation_id='observation:'+archive_digest(dict(identity=identity,archive=catalog['digest'],cutoff=binding['cutoff']),False),
            rule_id=rule,rules_version=VERSION,category=category,title=title,sku_id=key['sku_id'],warehouse_id=key['warehouse_id'],members=identity['keys'],
            observed=observation,values=values,references=refs,next_step=next_step,
            model_hypothesis=hypothesis,missing_evidence=['External causes, forecast uncertainty and commercial impact are not established.'],
            as_of=binding['cutoff'],known_at=_report(catalog,key['plan_run_id'])['context']['origin']))

    for key in binding['keys']:
        report = _report(catalog,key['plan_run_id']); result = report['result']; series = result['training']; supply = result['supply']
        ref = [_ref('planning.runs',key['plan_run_id']),_ref('planning.runs',key['forecast_run_id'])]
        natural = (key['sku_id'],key['warehouse_id']); card = cards['|'.join(natural)]
        old_key = old_keys.get(natural)
        old = _report(catalog,old_key['plan_run_id']) if old_key else None
        old_card = _card(catalog,previous,old_key) if old_key else None
        comparable = old_card is not None and old_card['comparison_signature'] == card['comparison_signature']
        prior_refs = ref + ([_ref('planning.runs',old['run_id']),_ref('planning.runs',old_key['forecast_run_id'])] if old else [])
        if series['status'] == 'eligible':
            values = [d['quantity'] for d in series['days']]
            older,recent = Fraction(sum(values[:14]),14),Fraction(sum(values[14:]),14)
            if abs(recent-older) >= 1 and (older == 0 and recent > 0 or older > 0 and abs(recent-older) >= older/2):
                add('I201',key,'risk' if recent>older else 'opportunity','Recent demand increase' if recent>older else 'Recent demand decrease',
                    'Two complete 14-day accepted-demand windows differ by at least 1 piece/day and 50%; growth from zero has no percentage.',
                    dict(older_daily=_rational(older),recent_daily=_rational(recent),delta_daily=_rational(recent-older),change_ratio=_rational((recent-older)/older) if older else None),ref,
                    'Inspect accepted-order evidence and compare the saved mean proposal with a declared demand scenario.',
                    'A constant 28-day mean may lag this observed change; future persistence is unmeasured.')
            if comparable and old['result']['training']['status']=='eligible':
                prior = Fraction(sum(d['quantity'] for d in old['result']['training']['days']),28)
                current = Fraction(sum(values),28)
                if abs(current-prior)>=1 and (prior==0 and current>0 or prior>0 and abs(current-prior)>=prior/4):
                    add('I202',key,'risk' if current>prior else 'opportunity','Demand changed since prior cutoff',
                        'Comparable complete 28-day accepted-demand means differ by at least 1 piece/day and 25%; these may be overlapping windows.',
                        dict(previous_daily=_rational(prior),current_daily=_rational(current),delta_daily=_rational(current-prior),previous_cutoff=previous['cutoff']),prior_refs,
                        'Review order evidence and the current proposal; do not infer an external cause or realized future demand.')
        else:
            unknown.append(dict(sku_id=key['sku_id'],warehouse_id=key['warehouse_id'],section='demand',reason='incomplete_training',references=ref))
        if old and comparable and not supply['reasons'] and not old['result']['supply']['reasons']:
            prior_supply = old['result']['supply']
            def confirmed(s): return sum(r['remaining_qty'] for r in s['inbound'] if r['status']=='confirmed')
            before, after = confirmed(prior_supply),confirmed(supply)
            if before != after:
                add('I203',key,'risk' if after<before else 'opportunity','Confirmed supply reduced' if after<before else 'Confirmed supply increased',
                    'Origin-known confirmed remaining inbound changed. Receipts, cancellation and new commitments cannot be distinguished by snapshots alone.',
                    dict(previous_pieces=str(before),current_pieces=str(after),delta_pieces=str(after-before)),prior_refs,
                    'Inspect the natural inbound identities and receipt journal before attributing a cause; compare current saved planning evidence.')
            before_rows = {(r['source_system'],r['inbound_id']):r for r in prior_supply['inbound'] if r['status']=='confirmed' and r['remaining_qty']>0}
            for row in supply['inbound']:
                prior = before_rows.get((row['source_system'],row['inbound_id']))
                if prior and row['status']=='confirmed' and row['remaining_qty']>0 and row['arrival_day']!=prior['arrival_day']:
                    add('I204',key,'risk' if row['arrival_day']>prior['arrival_day'] else 'opportunity','Known ETA changed',
                        'The same natural confirmed inbound identity has a different promised business date. No hidden physical arrival or supplier blame is inferred.',
                        dict(inbound_id=row['inbound_id'],previous_eta=prior['arrival_day'],current_eta=row['arrival_day']),prior_refs,
                        'Inspect the ETA notice and pre-arrival exposure. Expedite and supplier calendar feasibility remain unsupported.')
        elif old:
            unknown.append(dict(sku_id=key['sku_id'],warehouse_id=key['warehouse_id'],section='supply_history',reason='incomplete_or_incompatible_supply',references=prior_refs))
        if comparable and report['status']==old['status']=='assessable' and card['category']==old_card['category']=='risk':
            before,after = int(old_card['proposed_order_qty']),int(card['proposed_order_qty'])
            pre_before,pre_after = len(old['result']['pre_arrival_shortage_days']),len(result['pre_arrival_shortage_days'])
            if after>=before and pre_after>=pre_before:
                worsening = after>before or pre_after>pre_before
                add('I205',key,'risk','Worsening replenishment risk' if worsening else 'Persistent replenishment risk',
                    'Comparable actual prefix proposals and pre-arrival shortage-day counts both persist or increase. This is modeled exposure, not observed stockout.',
                    dict(previous_proposal=str(before),current_proposal=str(after),previous_shortage_days=str(pre_before),current_shortage_days=str(pre_after)),prior_refs,
                    'Review the contributing demand, stock, obligations and known inbound, then compare supported quantities.',
                    'The declared prefix model predicts continued safety exposure; causal attribution is not identified.')
    # Require complete evidence for the entire same-SKU location scope.
    for sku in catalog['dimensions']['skus']:
        scope = [c for c in cards.values() if c['sku_id']==sku['sku_id']]
        if len(scope)<2: continue
        if any(c['status']!='assessable' for c in scope):
            unknown.append(dict(sku_id=sku['sku_id'],section='location_pattern',reason='incomplete_location_scope'))
            continue
        risks = [c for c in scope if c['category']=='risk']
        surplus = [c for c in scope if c['category']=='opportunity']
        if risks and surplus:
            risk, donor = risks[0],surplus[0]
            key = next(k for k in binding['keys'] if (k['sku_id'],k['warehouse_id'])==(risk['sku_id'],risk['warehouse_id']))
            add('I206',key,'risk','Same-item location imbalance',
                'One location has prefix replenishment exposure while another has at least 20 terminal pieces above safety; both have complete saved evidence.',
                dict(risk_location=risk['warehouse_id'],surplus_location=donor['warehouse_id'],proposal_pieces=risk['proposed_order_qty'],surplus_exposure=donor['exposure']),risk['references']+donor['references'],
                'Review location allocation. A transfer requires donor service, transit, reservation and capacity evidence; no transferable quantity is claimed.',
                members=[risk['id'],donor['id']])
    # These factors explain modeled exposure; they do not attribute external causes.
    for finding in findings:
        key = next(k for k in binding['keys'] if
                   (k['sku_id'], k['warehouse_id']) == (finding['sku_id'], finding['warehouse_id']))
        result = _report(catalog, key['plan_run_id'])['result']
        supply = result['supply']; training = result['training']
        assessable = result['status'] == 'assessable'
        daily = Fraction(sum(d['quantity'] for d in training['days']), len(training['days'])) if training['status'] == 'eligible' else None
        finding['contributing_factors'] = dict(
            stock_pieces=str(result['inventory']['on_hand']) if result['inventory']['on_hand'] is not None else None,
            accepted_daily=_rational(daily) if daily is not None else None,
            reservation_pieces=str(sum(r['remaining_qty'] for r in supply['reservations'] if r['status']=='open')) if not supply['reasons'] else None,
            confirmed_inbound_pieces=str(sum(r['remaining_qty'] for r in supply['inbound'] if r['status']=='confirmed')) if not supply['reasons'] else None,
            safety_pieces=str(supply['policy']['safety_qty']) if not supply['reasons'] else None,
            proposal_pieces=str(result['proposed_order_qty']) if assessable else None,
            pre_arrival_shortage_days=str(len(result['pre_arrival_shortage_days'])) if assessable else None,
            boundary='Origin-known inputs and modeled exposure; factors are not additive causal effects.')
    # Explicit lexicographic urgency; no arbitrary weighted confidence score.
    def priority_key(f):
        factors = f['contributing_factors']
        return ({'risk':0,'opportunity':1}[f['category']],
                -int(factors['pre_arrival_shortage_days'] or 0),
                -int(factors['proposal_pieces'] or 0), f['rule_id'], f['id'])
    findings.sort(key=priority_key)
    for rank, finding in enumerate(findings, 1):
        finding['priority'] = dict(rank=rank,
            basis='Risk before opportunity, then more modeled pre-arrival shortage days, then larger saved proposal; rule and stable identity break ties.',
            category=finding['category'],
            pre_arrival_shortage_days=finding['contributing_factors']['pre_arrival_shortage_days'],
            proposal_pieces=finding['contributing_factors']['proposal_pieces'])
    return _envelope(catalog,binding)|dict(rules_version=VERSION,findings=findings,unknown=unknown,
        evaluated_keys=len(binding['keys']),previous_cutoff=previous['cutoff'] if previous else None,
        boundary='Observed input changes and modeled exposure are distinct. Next steps are advisory; no commercial certainty or feasible transfer is implied.')
