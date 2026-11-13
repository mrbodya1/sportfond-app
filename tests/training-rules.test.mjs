import test from 'node:test';
import assert from 'node:assert/strict';
import {approvalError} from '../src/training-rules.mjs';
const valid={id:'new',date:'2026-10-29',distance:1.25,gpsConfirmed:true,hash:'abc'};
const check=(patch={},rows=[])=>approvalError({...valid,...patch},rows,'2026-11-13');
test('October 29 is inclusive and prior dates are excluded',()=>{assert.equal(check(),'');assert.match(check({date:'2026-10-28'}),/29 октября/);});
test('GPS is required while pace and duration are not required',()=>{assert.match(check({gpsConfirmed:false}),/GPS/);assert.equal(check(),'');});
test('invalid dates, future dates and nonpositive distances are excluded',()=>{assert.match(check({date:'2026-02-30'}),/корректную дату/);assert.match(check({date:'2026-11-14'}),/будущем/);assert.match(check({distance:0}),/больше нуля/);assert.match(check({distance:NaN}),/больше нуля/);});
test('the same image cannot be credited twice, but editing its own decision is allowed',()=>{assert.match(check({},[{id:'other',hash:'abc',status:'approved'}]),/Повторный зачёт/);assert.equal(check({},[{id:'new',hash:'abc',status:'approved'}]),'');assert.equal(check({},[{id:'other',hash:'abc',status:'rejected'}]),'');});
