import semver from 'semver';

export function summarizeProgress(completed, total) {
  if (!Number.isSafeInteger(total) || total < 0 ||
      !Number.isSafeInteger(completed) || completed < 0 || completed > total) {
    throw new RangeError('Use safe integers with 0 <= completed <= total.');
  }
  return { completed, total, remaining: total - completed,
    percent: total === 0 ? 0 : Math.round((completed / total) * 100) };
}

export function isNewerVersion(candidate, current) {
  if (!semver.valid(candidate) || !semver.valid(current)) {
    throw new TypeError('Both versions must be valid semantic versions.');
  }
  return semver.gt(candidate, current);
}
