"""Read-only contract checks for the opt-in Windows daily review task.

These tests do not register scheduled tasks or interact with trading processes.
"""
import json
import unittest
from datetime import datetime, timezone

from infrastructure.completed_crypto_day import completed_pacific_day
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class DailyReviewSchedulerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "infrastructure" / "registry.json").read_text(encoding="utf-8"))
        cls.installer = (ROOT / "install_cryptotracker_daily_review.ps1").read_text(encoding="utf-8")
        cls.batch = (ROOT / "run_daily_model_review.bat").read_text(encoding="utf-8")

    def test_review_task_registered_but_not_host_verified(self):
        tasks = [t for t in self.registry["scheduled_tasks"] if t["name"] == "CryptoTracker Daily Review"]
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertEqual(task["trigger"], "daily_18_05_pacific")
        self.assertEqual(task["installer"], "install_cryptotracker_daily_review.ps1")
        self.assertEqual(task["script"], "run_daily_model_review.bat")
        self.assertIs(task["host_verified"], False)

    def test_installer_only_touches_review_task_and_never_starts_it(self):
        source = self.installer.lower()
        self.assertIn('cryptotracker daily review', source)
        self.assertIn("new-scheduledtasktrigger -daily -at 6:05pm", source)
        self.assertIn('get-timezone', source)
        self.assertIn('pacific standard time', source)
        self.assertIn('register-scheduledtask', source)
        for forbidden in ("start-scheduledtask", "stop-scheduledtask",
                          "unregister-scheduledtask", "restart-service",
                          "start-process", "stop-process"):
            self.assertNotIn(forbidden, source)

    def test_review_batch_fails_on_pipeline_errors(self):
        for command in ("build_daily_review_bundle.py", "daily_model_review.py",
                        "proposal_registry.py publish", "sync_proposals_to_git.py"):
            self.assertIn(command, self.batch)
        self.assertGreaterEqual(self.batch.lower().count("if errorlevel 1 goto :fail"), 4)

    def test_scheduled_review_uses_completed_day_not_current_partial_day(self):
        self.assertIn("python -m infrastructure.completed_crypto_day", self.batch)
        self.assertIn("if not defined REVIEWDATE goto :fail", self.batch)
        self.assertNotIn("Get-Date -Format yyyy-MM-dd", self.batch)
        self.assertEqual(completed_pacific_day(
            datetime(2026, 10, 29, 1, 5, tzinfo=timezone.utc)), "2026-10-27")

    def test_selector_handles_pacific_dst_boundaries(self):
        self.assertEqual(completed_pacific_day(
            datetime(2026, 3, 9, 1, 5, tzinfo=timezone.utc)), "2026-03-07")
        self.assertEqual(completed_pacific_day(
            datetime(2026, 11, 2, 2, 5, tzinfo=timezone.utc)), "2026-10-31")

    def test_selector_rejects_naive_clock(self):
        with self.assertRaises(ValueError):
            completed_pacific_day(datetime(2026, 10, 28, 18, 5))

    def test_task_is_not_misrepresented_as_pushover_delivery(self):
        source = self.installer.lower()
        self.assertIn("not proof of execution", source)
        self.assertIn("pushover delivery", source)


if __name__ == "__main__":
    unittest.main()
