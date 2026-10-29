"""Regression tests for the Pacific-day EOD publication classification.

A date being elapsed never proves full-account equity or provider delivery.
"""
import io
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from publish_daily_evidence import _publication_phase, main


class PublicationPhaseTests(unittest.TestCase):
    def test_pacific_day_incomplete_even_after_six_pm(self):
        stamp = datetime(2026, 10, 29, 3, 15, tzinfo=timezone.utc)
        self.assertEqual(
            _publication_phase("2026-10-28", observed_utc=stamp),
            "INCOMPLETE_PACIFIC_DAY",
        )

    def test_previous_pacific_day_elapsed_but_unverified(self):
        stamp = datetime(2026, 10, 29, 7, 15, tzinfo=timezone.utc)
        self.assertEqual(
            _publication_phase("2026-10-28", observed_utc=stamp),
            "ELAPSED_PACIFIC_DAY_UNVERIFIED",
        )

    def test_future_date_rejected_from_eod_claim(self):
        stamp = datetime(2026, 10, 29, 3, 15, tzinfo=timezone.utc)
        self.assertEqual(
            _publication_phase("2026-10-29", observed_utc=stamp),
            "FUTURE_DATED",
        )

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            _publication_phase("2026-10-28", observed_utc=datetime(2026, 10, 29, 3, 15))


class ScheduledCompletedDayPublicationTests(unittest.TestCase):
    def test_scheduled_batch_publishes_after_proposal_sync(self):
        batch = (Path(__file__).resolve().parent / "run_daily_model_review.bat").read_text(encoding="utf-8")
        self.assertIn("publish_daily_evidence.py --date %REVIEWDATE% --completed-only", batch)
        self.assertLess(batch.index("sync_proposals_to_git.py"),
                        batch.index("publish_daily_evidence.py"))
        self.assertGreaterEqual(batch.lower().count("if errorlevel 1 goto :fail"), 5)

    def test_incomplete_day_never_calls_publisher(self):
        with patch("publish_daily_evidence._publication_phase", return_value="INCOMPLETE_PACIFIC_DAY"), \\
             patch("publish_daily_evidence.publish_daily_evidence") as publish, \\
             redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--date", "2026-10-28", "--completed-only"]), 2)
            publish.assert_not_called()

    def test_completed_day_requires_successful_publication(self):
        with patch("publish_daily_evidence._publication_phase", return_value="ELAPSED_PACIFIC_DAY_UNVERIFIED"), \\
             patch("publish_daily_evidence.publish_daily_evidence", return_value={"status": "PUBLISHED"}) as publish, \\
             redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--date", "2026-10-28", "--completed-only"]), 0)
            publish.assert_called_once_with("2026-10-28")
        with patch("publish_daily_evidence._publication_phase", return_value="ELAPSED_PACIFIC_DAY_UNVERIFIED"), \\
             patch("publish_daily_evidence.publish_daily_evidence", return_value={"status": "SKIPPED_DIRTY_REPO"}), \\
             redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--date", "2026-10-28", "--completed-only"]), 2)


if __name__ == "__main__":
    unittest.main()
