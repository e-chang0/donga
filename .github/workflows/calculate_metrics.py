import requests
from datetime import datetime


def calculate_cycle_time(issue_number):
    # Issue 정보 가져오기
    url = f"https://api.github.com/repos/owner/repo/issues/{issue_number}"
    issue = requests.get(url)
    data = issue.json()

    # "In Progress" 라벨 추가 시간 찾기
    start_time = None
    for event in data['events']:
        if event['label']['name'] == 'In Progress':
            start_time = event['created_at']
            break
