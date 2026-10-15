import test from 'node:test';
import assert from 'node:assert/strict';
import {badgePresentation} from '../src/presentation.mjs';

test('known category and status variants have explicit semantic tones',()=>{
  for (const [tone,states] of Object.entries({warning:['risk','worsening','stale','investigating'],danger:['evidence','not_assessable','fail','blocked','infeasible','ineligible','withheld'],success:['opportunity','assessable','pass','improved','eligible','feasible','resolved','received'],unknown:['unknown','synthetic'],neutral:['none','persistent','new','acknowledged','reserved','in_transit']})) {
    for(const state of states) assert.equal(badgePresentation(state).tone,tone,state);
  }
  assert.equal(badgePresentation('not_assessable').label,'Blocked');
  assert.equal(badgePresentation('evidence').label,'Evidence problem');
});
test('unknown, empty and arbitrary status values remain readable and neutral',()=>{
  assert.deepEqual(badgePresentation('future_source_state'),{label:'Future source state',tone:'neutral'});
  for(const value of ['',null,undefined,42]) assert.deepEqual(badgePresentation(value),{label:'Unknown',tone:'unknown'});
  for(const value of ['__proto__','constructor','toString','long_state_'.repeat(30)]) {
    assert.equal(badgePresentation(value).tone,'neutral');
    assert.equal(typeof badgePresentation(value).label,'string');
  }
});
