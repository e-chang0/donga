import test from 'node:test';
import assert from 'node:assert/strict';
import { evaluateAudit } from './audit-policy.mjs';

const report = (extra = {}) => ({ metadata: { vulnerabilities: {
  info: 0, low: 0, moderate: 0, high: 0, critical: 0, total: 0, ...extra,
} } });

test('allows clean scans and reports lower severity findings without blocking', () => {
  assert.equal(evaluateAudit(report(), 0).blocked, false);
  assert.equal(evaluateAudit(report({ moderate: 1, total: 1 }), 1).blocked, false);
});

test('blocks high and critical vulnerabilities', () => {
  assert.equal(evaluateAudit(report({ high: 1, total: 1 }), 1).blocked, true);
  assert.equal(evaluateAudit(report({ critical: 1, total: 1 }), 1).blocked, true);
});

test('fails closed for network errors, invalid reports, and invalid counts', () => {
  for (const [input, code, processError] of [
    [{ error: { code: 'EAI_AGAIN' } }, 1, false], [{}, 0, false],
    [report({ high: '0' }), 0, false], [report({ high: -1 }), 0, false],
    [report(), 2, false], [report(), null, true],
  ]) {
    assert.equal(evaluateAudit(input, code, processError).blocked, true);
  }
});
