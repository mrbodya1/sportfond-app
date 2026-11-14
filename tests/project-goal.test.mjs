import test from 'node:test';
import assert from 'node:assert/strict';
import {projectProgress} from '../src/project-goal.mjs';
test('remaining goal uses hundredths without floating-point residue',()=>{
 assert.deepEqual(projectProgress(25.39),{remaining:8974.61,completed:25.39});
 assert.equal(projectProgress(0).remaining,9000);
});
test('goal stops at zero and remains consistent after a credited workout is removed',()=>{
 assert.deepEqual(projectProgress(9001),{remaining:0,completed:9000});
 assert.equal(projectProgress(25.39+3.71).remaining,8970.9);
 assert.equal(projectProgress(25.39).remaining,8974.61);
});
