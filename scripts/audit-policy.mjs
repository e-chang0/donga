export function evaluateAudit(report, exitCode, processError = false) {
  const counts = report?.metadata?.vulnerabilities;
  const severities = ['info', 'low', 'moderate', 'high', 'critical', 'total'];
  const validCounts = !!counts && severities.every(level =>
    Number.isSafeInteger(counts[level]) && counts[level] >= 0);
  const scanFailed = processError || ![0, 1].includes(exitCode) || !!report?.error || !validCounts;
  return { counts: validCounts ? counts : undefined, scanFailed,
    blocked: scanFailed || counts.high > 0 || counts.critical > 0 };
}
