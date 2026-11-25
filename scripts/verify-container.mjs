import { execFileSync } from 'node:child_process';
import { setTimeout } from 'node:timers/promises';
import assert from 'node:assert/strict';

const image = process.argv[2];
if (!image) throw new Error('Usage: node scripts/verify-container.mjs IMAGE');
const docker = (...args) => execFileSync('docker', args, { encoding: 'utf8' }).trim();
let id;
try {
  id = docker('run', '--detach', '--rm', '--publish', '127.0.0.1::3000', image);
  const binding = docker('port', id, '3000/tcp');
  const base = `http://${binding}`;
  let healthy = false;
  for (let attempt = 0; attempt < 30; attempt++) {
    try {
      const response = await fetch(`${base}/health`, { signal: AbortSignal.timeout(1000) });
      if (response.ok) { assert.equal((await response.json()).status, 'ok'); healthy = true; break; }
    } catch { /* Container may still be starting. */ }
    await setTimeout(1000);
  }
  assert.ok(healthy, 'Container failed to become healthy within 30 seconds');
  const result = await fetch(`${base}/progress?completed=3&total=9`);
  assert.equal(result.status, 200);
  assert.deepEqual(await result.json(), { completed: 3, total: 9, remaining: 6, percent: 33 });
  assert.equal((await fetch(`${base}/progress?completed=10&total=9`)).status, 400);
  assert.equal(docker('inspect', '--format', '{{.Config.User}}', id), 'node');
  console.log(JSON.stringify({ image, health: 'ok', progress: 'ok', invalidInput: 'ok', user: 'node' }));
} catch (error) {
  if (id) console.error(docker('logs', id));
  throw error;
} finally {
  if (id) docker('stop', id);
}
