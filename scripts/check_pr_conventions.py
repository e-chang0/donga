"""Validate this repository's PR policy without executing event data as code."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


CONVENTIONAL = re.compile(
    r"(?:feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(?:\([A-Za-z0-9_./-]+\))?!?: \S[^\r\n]*"
)
FEATURE_BRANCH = re.compile(r"feature/[a-z0-9]+(?:[/-][a-z0-9]+)*")
SHA = re.compile(r"[0-9a-f]{40}")


def validate_metadata(title, branch, subjects):
    errors = []
    if not CONVENTIONAL.fullmatch(title):
        errors.append("PR title must use Conventional Commits.")
    if not FEATURE_BRANCH.fullmatch(branch):
        errors.append("PR branch must use feature/<lowercase-kebab-name>.")
    if not subjects:
        errors.append("PR must contain at least one non-merge commit.")
    for index, subject in enumerate(subjects, start=1):
        if not CONVENTIONAL.fullmatch(subject):
            errors.append(f"Commit {index} must use Conventional Commits.")
    return errors


def check_event(event):
    pull = event["pull_request"]
    base, head = pull["base"]["sha"], pull["head"]["sha"]
    if not SHA.fullmatch(base) or not SHA.fullmatch(head):
        raise ValueError("Invalid base/head commit SHA.")
    subjects = subprocess.run(
        ["git", "log", "--no-merges", "--format=%s", f"{base}..{head}"],
        check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout.splitlines()
    errors = validate_metadata(pull["title"], pull["head"]["ref"], subjects)
    whitespace = subprocess.run(
        ["git", "diff", "--check", f"{base}...{head}"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if whitespace.returncode:
        errors.append("PR diff has whitespace errors or could not be inspected.")
    return errors


def main():
    try:
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        errors = check_event(event)
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"PR policy could not be validated ({type(error).__name__}).", file=sys.stderr)
        return 1
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("PR title, feature branch, new commits, and diff whitespace passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
