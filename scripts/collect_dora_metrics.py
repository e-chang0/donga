#!/usr/bin/env python3
"""Collect four DORA metrics from GitHub deployments and pull requests.

The implementation intentionally uses only the Python standard library so it can
run on a stock GitHub-hosted runner without a dependency-install step.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


UTC = timezone.utc
FINAL_STATES = {"success", "failure", "error"}
FAILED_STATES = {"failure", "error"}


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def iso_time(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def median_or_none(values: Iterable[float]) -> float | None:
    materialized = list(values)
    return statistics.median(materialized) if materialized else None


def mean_or_none(values: Iterable[float]) -> float | None:
    materialized = list(values)
    return statistics.mean(materialized) if materialized else None


def format_duration(hours: float | None) -> str:
    if hours is None:
        return "N/A"
    if hours < 1:
        return f"{hours * 60:.1f} min"
    if hours < 48:
        return f"{hours:.1f} h"
    return f"{hours / 24:.1f} d"


class GitHubClient:
    def __init__(self, token: str) -> None:
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "dora-metrics-action",
        }

    def get(self, path: str, params: dict[str, Any] | None = None) -> tuple[Any, dict[str, str]]:
        url = f"https://api.github.com{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response), dict(response.headers.items())
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API returned {error.code} for {path}: {detail}") from error

    def pages(self, path: str, params: dict[str, Any] | None = None) -> Iterable[dict[str, Any]]:
        query = dict(params or {})
        query["per_page"] = 100
        page = 1
        while True:
            query["page"] = page
            data, _ = self.get(path, query)
            if not isinstance(data, list):
                raise RuntimeError(f"Expected a list response from {path}")
            yield from data
            if len(data) < 100:
                return
            page += 1


def collect_deployments(
    client: GitHubClient,
    repository: str,
    start: datetime,
    environment_pattern: str,
) -> list[dict[str, Any]]:
    environment_re = re.compile(environment_pattern, re.IGNORECASE)
    deployments: list[dict[str, Any]] = []
    for deployment in client.pages(f"/repos/{repository}/deployments"):
        created_at = parse_time(deployment["created_at"])
        if created_at < start:
            break
        environment = deployment.get("environment") or ""
        if not environment_re.search(environment):
            continue
        statuses = list(client.pages(deployment["statuses_url"].replace("https://api.github.com", "")))
        final_status = next((item for item in statuses if item.get("state") in FINAL_STATES), None)
        if final_status is None:
            continue
        deployments.append(
            {
                "id": deployment["id"],
                "sha": deployment.get("sha"),
                "ref": deployment.get("ref"),
                "environment": environment,
                "created_at": deployment["created_at"],
                "completed_at": final_status.get("created_at") or deployment["created_at"],
                "state": final_status["state"],
                "url": final_status.get("environment_url") or final_status.get("target_url"),
            }
        )
    return sorted(deployments, key=lambda item: item["completed_at"])


def find_pull_request(
    client: GitHubClient,
    repository: str,
    sha: str | None,
    cache: dict[str, dict[str, Any] | None],
) -> dict[str, Any] | None:
    if not sha:
        return None
    if sha not in cache:
        pulls, _ = client.get(f"/repos/{repository}/commits/{sha}/pulls", {"per_page": 100})
        merged = [pull for pull in pulls if pull.get("merged_at")]
        cache[sha] = max(merged, key=lambda pull: pull["merged_at"]) if merged else None
    return cache[sha]


def find_first_commit_time(
    client: GitHubClient,
    repository: str,
    pull_number: int,
    cache: dict[int, str | None],
) -> str | None:
    if pull_number not in cache:
        dates = []
        for commit in client.pages(f"/repos/{repository}/pulls/{pull_number}/commits"):
            commit_data = commit.get("commit", {})
            author = commit_data.get("author") or {}
            committer = commit_data.get("committer") or {}
            date = author.get("date") or committer.get("date")
            if date:
                dates.append(date)
        cache[pull_number] = min(dates, key=parse_time) if dates else None
    return cache[pull_number]


def calculate_metrics(
    deployments: list[dict[str, Any]],
    deployed_pull_requests: list[dict[str, Any]],
    period_days: float,
) -> dict[str, Any]:
    successes = [item for item in deployments if item["state"] == "success"]
    failures = [item for item in deployments if item["state"] in FAILED_STATES]

    lead_times = []
    for item in deployed_pull_requests:
        change_started_at = parse_time(item["first_commit_at"])
        deployed_at = parse_time(item["deployed_at"])
        if deployed_at >= change_started_at:
            lead_times.append((deployed_at - change_started_at).total_seconds() / 3600)

    recovery_times: list[float] = []
    incident_start: datetime | None = None
    for deployment in deployments:
        completed_at = parse_time(deployment["completed_at"])
        if deployment["state"] in FAILED_STATES and incident_start is None:
            incident_start = completed_at
        elif deployment["state"] == "success" and incident_start is not None:
            recovery_times.append((completed_at - incident_start).total_seconds() / 3600)
            incident_start = None

    completed_count = len(successes) + len(failures)
    return {
        "lead_time_for_changes": {
            "median_hours": median_or_none(lead_times),
            "sample_size": len(lead_times),
            "definition": "first PR commit to the observed successful production deployment of its SHA",
        },
        "deployment_frequency": {
            "per_day": len(successes) / max(period_days, 1 / 24),
            "successful_deployments": len(successes),
            "definition": "successful production deployments per day",
        },
        "mean_time_to_restore": {
            "mean_hours": mean_or_none(recovery_times),
            "resolved_incidents": len(recovery_times),
            "open_incident": incident_start is not None,
            "definition": "first failed production deployment to the next successful deployment",
        },
        "change_failure_rate": {
            "percent": (len(failures) / completed_count * 100) if completed_count else None,
            "failed_deployments": len(failures),
            "completed_deployments": completed_count,
            "definition": "failed or errored production deployments / completed production deployments",
        },
    }


def render_report(payload: dict[str, Any]) -> str:
    metrics = payload["metrics"]
    lead = metrics["lead_time_for_changes"]
    frequency = metrics["deployment_frequency"]
    mttr = metrics["mean_time_to_restore"]
    failure = metrics["change_failure_rate"]
    failure_display = "N/A" if failure["percent"] is None else f'{failure["percent"]:.1f}%'
    return f"""# Weekly DORA report

Generated at **{payload['generated_at']}** for `{payload['repository']}`.
Measurement window: **{payload['period']['start']} – {payload['period']['end']}** ({payload['period']['days']:.1f} days)

| Metric | Result | Evidence |
|---|---:|---:|
| Lead time for changes | **{format_duration(lead['median_hours'])}** | {lead['sample_size']} linked PR(s) |
| Deployment frequency | **{frequency['per_day']:.2f}/day** | {frequency['successful_deployments']} successful deployment(s) |
| Mean time to restore | **{format_duration(mttr['mean_hours'])}** | {mttr['resolved_incidents']} resolved incident(s) |
| Change failure rate | **{failure_display}** | {failure['failed_deployments']} failed / {failure['completed_deployments']} completed |

## Measurement notes

- Production is selected with the environment regex `{payload['configuration']['production_environment_pattern']}`.
- Lead time uses the first PR commit → successful production deployment. Deployments whose SHA cannot be linked to a merged PR are excluded.
- MTTR starts at the first failed/error deployment in an incident and ends at the next success.
- `N/A` means GitHub does not yet contain enough matching events; it is not treated as zero.
- Full source events and machine-readable values are in `dora-metrics.json`.
"""


def render_dashboard(payload: dict[str, Any]) -> str:
    metrics = payload["metrics"]
    lead = format_duration(metrics["lead_time_for_changes"]["median_hours"])
    frequency = f'{metrics["deployment_frequency"]["per_day"]:.2f}/day'
    mttr = format_duration(metrics["mean_time_to_restore"]["mean_hours"])
    failure_value = metrics["change_failure_rate"]["percent"]
    failure = "N/A" if failure_value is None else f"{failure_value:.1f}%"
    values = [lead, frequency, mttr, failure]
    labels = ["LEAD TIME", "DEPLOY FREQUENCY", "MTTR", "CHANGE FAILURE RATE"]
    cards = []
    for index, (label, value) in enumerate(zip(labels, values)):
        x = 28 + index * 236
        cards.append(
            f'<rect x="{x}" y="96" width="216" height="118" rx="14" fill="#172033" stroke="#293650"/>'
            f'<text x="{x + 18}" y="129" class="label">{html.escape(label)}</text>'
            f'<text x="{x + 18}" y="178" class="value">{html.escape(value)}</text>'
        )
    generated = html.escape(payload["generated_at"])
    window = html.escape(f"{payload['period']['start']} - {payload['period']['end']}")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="260" viewBox="0 0 1000 260" role="img" aria-labelledby="title desc">
<title id="title">DORA metrics dashboard</title>
<desc id="desc">Current four key DORA metrics for the repository</desc>
<style>.title{{font:700 24px system-ui;fill:#f4f7ff}}.meta{{font:13px system-ui;fill:#91a0bb}}.label{{font:600 12px system-ui;fill:#8ea5cd;letter-spacing:.7px}}.value{{font:700 27px system-ui;fill:#63e6be}}</style>
<rect width="1000" height="260" rx="18" fill="#0d1423"/>
<text x="28" y="43" class="title">DORA delivery performance</text>
<text x="28" y="69" class="meta">Window: {window} · Updated: {generated}</text>
{''.join(cards)}
</svg>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--environment", default=r"^(production|prod)$")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/latest"))
    args = parser.parse_args()
    if not args.repo or not args.token:
        parser.error("--repo and --token (or GITHUB_REPOSITORY/GITHUB_TOKEN) are required")

    end = datetime.now(UTC)
    start = end - timedelta(days=args.days)
    client = GitHubClient(args.token)
    deployments = collect_deployments(client, args.repo, start, args.environment)

    pull_cache: dict[str, dict[str, Any] | None] = {}
    first_commit_cache: dict[int, str | None] = {}
    deployed_pull_numbers: set[int] = set()
    deployed_pull_requests = []
    for deployment in deployments:
        if deployment["state"] != "success":
            continue
        pull = find_pull_request(client, args.repo, deployment.get("sha"), pull_cache)
        first_commit_at = (
            find_first_commit_time(client, args.repo, pull["number"], first_commit_cache) if pull else None
        )
        if pull and first_commit_at and pull["number"] not in deployed_pull_numbers:
            deployed_pull_numbers.add(pull["number"])
            deployed_pull_requests.append(
                {
                    "number": pull["number"],
                    "first_commit_at": first_commit_at,
                    "merged_at": pull["merged_at"],
                    "deployed_at": deployment["completed_at"],
                    "deployment_id": deployment["id"],
                }
            )

    payload = {
        "schema_version": 1,
        "repository": args.repo,
        "generated_at": iso_time(end),
        "period": {"start": iso_time(start), "end": iso_time(end), "days": args.days},
        "configuration": {"production_environment_pattern": args.environment},
        "metrics": calculate_metrics(deployments, deployed_pull_requests, args.days),
        "source_data": {
            "deployments": deployments,
            "deployed_pull_requests": deployed_pull_requests,
        },
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "dora-metrics.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "report.md").write_text(render_report(payload), encoding="utf-8")
    (args.output_dir / "dashboard.svg").write_text(render_dashboard(payload), encoding="utf-8")
    print(json.dumps(payload["metrics"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
