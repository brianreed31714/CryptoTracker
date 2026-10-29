"""Regression tests for the Pacific-day EOD publication classification.

A date being elapsed never proves full-account equity or provider delivery.
"""
import unittest
from datetime import datetime, timezone
from publish_daily_evidence import _publication_phase


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


if __name__ == "__main__":
    unittest.main()
