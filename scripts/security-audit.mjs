import { spawnSync } from 'node:child_process';
import { mkdirSync, writeFileSync, appendFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { evaluateAudit } from './audit-policy.mjs';

const output = resolve(process.argv[2] || 'reports/week9-local');
mkdirSync(output, { recursive: true });
// Windows invokes npm-cli.js directly to avoid shell interpolation.
const args = ['audit', '--json', '--registry=https://registry.npmjs.org'];
const result = process.platform === 'win32'
  ? spawnSync(process.execPath, [resolve(process.execPath, '..', 'node_modules/npm/bin/npm-cli.js'), ...args],
      { cwd: 'packages/study-progress', encoding: 'utf8' })
  : spawnSync('npm', args, { cwd: 'packages/study-progress', encoding: 'utf8' });
writeFileSync(resolve(output, 'npm-audit.json'), result.stdout || '{}');
let report;
try { report = JSON.parse(result.stdout); } catch { report = {}; }
const { counts, scanFailed, blocked } = evaluateAudit(report, result.status, !!result.error);
const markdown = [
  '# Dependency security report', '',
  `- Scan time: ${new Date().toISOString()}`,
  `- Commit: ${process.env.GITHUB_SHA || 'local working tree'}`,
  `- Run: ${process.env.GITHUB_RUN_ID ? `${process.env.GITHUB_SERVER_URL}/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}` : 'local'}`,
  '- Scanner: npm audit (all production and development dependencies)',
  `- Result: ${scanFailed ? 'SCAN ERROR' : blocked ? 'BLOCKED' : 'PASSED'}`, '',
  '| Severity | Count |', '|---|---:|',
  ...['info', 'low', 'moderate', 'high', 'critical', 'total'].map(level => `| ${level} | ${counts?.[level] ?? 'unknown'} |`), '',
  'Policy: high/critical vulnerabilities and scan failures block CI, release, and automatic merging.',
  'For dependency paths, advisories, and fix availability, see npm-audit.json.', '',
].join('\n');
writeFileSync(resolve(output, 'security-report.md'), markdown);
if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, markdown);
console.log(markdown);
if (scanFailed) console.error(result.error?.message || result.stderr || 'Invalid audit response');
process.exitCode = blocked ? 1 : 0;
