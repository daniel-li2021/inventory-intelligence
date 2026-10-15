// Status text stays meaningful without relying on color. Unrecognized states stay neutral.
const tones = {
  risk: 'warning', worsening: 'warning', stale: 'warning', investigating: 'warning',
  evidence: 'danger', not_assessable: 'danger', fail: 'danger', blocked: 'danger',
  infeasible: 'danger', ineligible: 'danger', withheld: 'danger',
  opportunity: 'success', assessable: 'success', pass: 'success', improved: 'success',
  eligible: 'success', feasible: 'success', resolved: 'success', received: 'success',
  unknown: 'unknown', synthetic: 'unknown',
};
const labels = {not_assessable:'Blocked', evidence:'Evidence problem', none:'No alert'};
export function badgePresentation(value) {
  const state = typeof value === 'string' && value.trim() ? value.trim() : 'unknown';
  return {label: Object.hasOwn(labels,state) ? labels[state] : state.replaceAll('_',' ').replace(/^./, c=>c.toUpperCase()), tone: Object.hasOwn(tones,state) ? tones[state] : 'neutral'};
}
