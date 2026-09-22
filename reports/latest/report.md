# Weekly DORA report

Generated at **2026-09-22T06:32:32Z** for `e-chang0/donga`.
Measurement window: **2026-08-23T06:32:32Z – 2026-09-22T06:32:32Z** (30.0 days)

| Metric | Result | Evidence |
|---|---:|---:|
| Lead time for changes | **N/A** | 0 linked PR(s) |
| Deployment frequency | **0.00/day** | 0 successful deployment(s) |
| Mean time to restore | **N/A** | 0 resolved incident(s) |
| Change failure rate | **N/A** | 0 failed / 0 completed |

## Measurement notes

- Production is selected with the environment regex `^(production|prod)$`.
- Lead time uses the first PR commit → successful production deployment. Deployments whose SHA cannot be linked to a merged PR are excluded.
- MTTR starts at the first failed/error deployment in an incident and ends at the next success.
- `N/A` means GitHub does not yet contain enough matching events; it is not treated as zero.
- Full source events and machine-readable values are in `dora-metrics.json`.
