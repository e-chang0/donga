import test from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { summarizeProgress, isNewerVersion } from '../src/index.js';
import { createApp } from '../src/server.js';

test('summarizes normal, empty, and completed study plans', () => {
  assert.deepEqual(summarizeProgress(3, 9), { completed: 3, total: 9, remaining: 6, percent: 33 });
  assert.equal(summarizeProgress(0, 0).percent, 0);
  assert.equal(summarizeProgress(9, 9).percent, 100);
});

test('rejects impossible, fractional, and unsafe progress', () => {
  for (const [completed, total] of [[-1, 9], [10, 9], [1.5, 9], [0, -1], [0, Infinity], [0, 2 ** 53]]) {
    assert.throws(() => summarizeProgress(completed, total), RangeError);
  }
});

test('compares patch releases and prereleases correctly', () => {
  assert.equal(isNewerVersion('1.0.1', '1.0.0'), true);
  assert.equal(isNewerVersion('1.0.0', '1.0.0'), false);
  assert.equal(isNewerVersion('1.0.0-rc.1', '1.0.0'), false);
  assert.throws(() => isNewerVersion('latest', '1.0.0'), TypeError);
});

test('HTTP API health, progress, invalid input, and missing routes', async t => {
  const server = createApp().listen(0, '127.0.0.1');
  t.after(() => new Promise(resolve => server.close(resolve)));
  await once(server, 'listening');
  const base = `http://127.0.0.1:${server.address().port}`;
  assert.equal((await (await fetch(`${base}/health`)).json()).status, 'ok');
  assert.equal((await (await fetch(`${base}/progress?completed=3&total=9`)).json()).remaining, 6);
  for (const query of ['', '?completed=&total=9', '?completed=-1&total=9', '?completed=10&total=9']) {
    assert.equal((await fetch(`${base}/progress${query}`)).status, 400);
  }
  assert.equal((await fetch(`${base}/missing`)).status, 404);
  assert.equal((await fetch(`${base}/health`, { method: 'POST' })).status, 405);
});
