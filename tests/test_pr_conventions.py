import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "pr_policy", Path(__file__).parents[1] / "scripts" / "check_pr_conventions.py"
)
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)


class PullRequestPolicyTests(unittest.TestCase):
    def test_accepts_scoped_unscoped_and_breaking_changes(self):
        self.assertEqual(policy.validate_metadata(
            "ci(review): add checks", "feature/collaboration-checks",
            ["docs: 한글 문서 추가", "feat(api)!: change response", "fix: handle empty input"],
        ), [])

    def test_rejects_nonconventional_title(self):
        self.assertTrue(policy.validate_metadata("Update files", "feature/checks", ["docs: add guide"]))

    def test_rejects_direct_main_and_invalid_feature_names(self):
        for branch in ["main", "fix/checks", "feature/", "feature/Bad Name", "feature/a--b"]:
            with self.subTest(branch=branch):
                self.assertTrue(policy.validate_metadata("fix: check", branch, ["fix: check"]))

    def test_rejects_invalid_commit_even_with_valid_pr_title(self):
        self.assertTrue(policy.validate_metadata("fix: check", "feature/checks", ["update code"]))

    def test_rejects_empty_commit_range_and_multiline_title(self):
        self.assertTrue(policy.validate_metadata("fix: check", "feature/checks", []))
        self.assertTrue(policy.validate_metadata("fix: check\nextra", "feature/checks", ["fix: check"]))

    def test_shell_text_is_treated_as_plain_metadata(self):
        with patch.object(policy.subprocess, "run") as run:
            errors = policy.validate_metadata("fix: $(touch should-not-exist)", "feature/checks", ["fix: check"])
        self.assertEqual(errors, [])
        run.assert_not_called()

    def test_rejects_invalid_commit_sha_before_git(self):
        event = {"pull_request": {"base": {"sha": "--help"}, "head": {"sha": "a" * 40}}}
        with patch.object(policy.subprocess, "run") as run:
            with self.assertRaises(ValueError):
                policy.check_event(event)
        run.assert_not_called()

    def test_real_git_history_keeps_shell_metadata_literal(self):
        real_run = subprocess.run
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)

            def git(*args):
                return real_run(
                    ["git", *args], cwd=repository, check=True,
                    capture_output=True, text=True, encoding="utf-8",
                ).stdout.strip()

            git("init", "--initial-branch=main")
            git("-c", "user.name=Policy Test", "-c", "user.email=test@example.com",
                "commit", "--allow-empty", "-m", "chore: initialize fixture")
            base = git("rev-parse", "HEAD")
            git("switch", "-c", "feature/injection-check")
            (repository / "fixture.txt").write_text("safe input\n", encoding="utf-8")
            git("add", "fixture.txt")
            git("-c", "user.name=Policy Test", "-c", "user.email=test@example.com",
                "commit", "-m", "fix: $(touch injected)")
            event = {"pull_request": {
                "title": "fix: $(touch injected)", "base": {"sha": base},
                "head": {"sha": git("rev-parse", "HEAD"), "ref": "feature/injection-check"},
            }}

            def run_in_repository(args, **kwargs):
                return real_run(args, cwd=repository, **kwargs)

            with patch.object(policy.subprocess, "run", side_effect=run_in_repository):
                self.assertEqual(policy.check_event(event), [])
            self.assertFalse((repository / "injected").exists())


if __name__ == "__main__":
    unittest.main()
