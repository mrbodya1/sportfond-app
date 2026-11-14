import test from 'node:test';
import assert from 'node:assert/strict';
import {reviewRows,activeReview} from '../src/admin-queue.mjs';
const queue=[{id:'one',status:'pending',person:'A'},{id:'two',status:'pending',person:'B'}];
test('resolved selected workout gives way to next pending workout',()=>{
 for(const status of ['approved','rejected']){
  const rows=queue.map(r=>r.id==='one'?{...r,status}:r);
  const visible=reviewRows(rows,'pending');
  assert.deepEqual(visible.map(r=>r.id),['two']);
  assert.equal(activeReview(visible,'one').id,'two');
 }
});
test('last resolved workout leaves no review panel and history remains available',()=>{
 const rows=[{...queue[0],status:'approved'}];
 assert.equal(activeReview(reviewRows(rows,'pending'),'one'),null);
 assert.equal(reviewRows(rows,'approved').length,1);
});
test('selected hidden workout is not retained after filtering',()=>{
 assert.equal(activeReview(reviewRows(queue,'pending','B'),'one').id,'two');
 assert.equal(activeReview(reviewRows(queue,'pending','missing'),'one'),null);
});
