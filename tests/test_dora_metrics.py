import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "collect_dora_metrics.py"
SPEC = importlib.util.spec_from_file_location("dora", MODULE_PATH)
dora = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(dora)


class DoraMetricTests(unittest.TestCase):
    def test_calculates_all_four_metrics_and_groups_incident(self):
        deployments = [
            {"state": "success", "completed_at": "2026-01-01T12:00:00Z"},
            {"state": "failure", "completed_at": "2026-01-02T10:00:00Z"},
            {"state": "error", "completed_at": "2026-01-02T11:00:00Z"},
            {"state": "success", "completed_at": "2026-01-02T14:00:00Z"},
        ]
        pulls = [
            {"first_commit_at": "2026-01-01T07:00:00Z", "deployed_at": "2026-01-01T12:00:00Z"},
            {"first_commit_at": "2026-01-02T05:00:00Z", "deployed_at": "2026-01-02T14:00:00Z"},
        ]

        metrics = dora.calculate_metrics(deployments, pulls, period_days=2)

        self.assertEqual(metrics["lead_time_for_changes"]["median_hours"], 7)
        self.assertEqual(metrics["deployment_frequency"]["per_day"], 1)
        self.assertEqual(metrics["mean_time_to_restore"]["mean_hours"], 4)
        self.assertEqual(metrics["mean_time_to_restore"]["resolved_incidents"], 1)
        self.assertEqual(metrics["change_failure_rate"]["percent"], 50)

    def test_missing_events_are_explicitly_not_available(self):
        metrics = dora.calculate_metrics([], [], period_days=30)

        self.assertIsNone(metrics["lead_time_for_changes"]["median_hours"])
        self.assertEqual(metrics["deployment_frequency"]["per_day"], 0)
        self.assertIsNone(metrics["mean_time_to_restore"]["mean_hours"])
        self.assertIsNone(metrics["change_failure_rate"]["percent"])


if __name__ == "__main__":
    unittest.main()
