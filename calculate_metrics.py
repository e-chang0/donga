"""GitHub Issue의 작업 시작부터 종료까지 걸린 시간을 계산한다."""

import os
from datetime import datetime

import requests


def calculate_cycle_time(issue_number):
    # Issue 정보 가져오기 (GITHUB_REPOSITORY 예: owner/repo)
    repository = os.getenv("GITHUB_REPOSITORY", "owner/repo")
    url = f"https://api.github.com/repos/{repository}/issues/{issue_number}"
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    issue = requests.get(url, headers=headers, timeout=15)
    issue.raise_for_status()
    data = issue.json()

    # "In Progress" 라벨이 추가된 시각 찾기
    start_time = None
    events_url = data["events_url"]
    query = {"per_page": 100}
    while events_url:
        events_response = requests.get(
            events_url,
            headers=headers,
            params=query,
            timeout=15,
        )
        events_response.raise_for_status()
        for event in events_response.json():
            if (
                event.get("event") == "labeled"
                and event.get("label", {}).get("name") == "In Progress"
            ):
                start_time = event["created_at"]
                break
        if start_time:
            break
        events_url = events_response.links.get("next", {}).get("url")
        query = None

    # 라벨 추가 기록이 없거나 아직 닫히지 않은 Issue는 계산할 수 없다.
    if start_time is None or data.get("closed_at") is None:
        return None

    started_at = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    closed_at = datetime.fromisoformat(data["closed_at"].replace("Z", "+00:00"))
    return closed_at - started_at
