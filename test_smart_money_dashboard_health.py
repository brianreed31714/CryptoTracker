"""Regression tests for Smart Money status even with hidden Windows command lines."""
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from smart_money_dashboard_health import smart_money_status


NOW = datetime(2026, 10, 18, 18, 0, tzinfo=timezone.utc).timestamp()


class SmartMoneyDashboardHealthTests(unittest.TestCase):
    def report(self, data):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p = Path(tmp.name) / "health.json"
        if data is not None:
            p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def sample(self, **changes):
        result = {
            "observed_at_utc": "2026-10-18T17:59:00+00:00",
            "cycle_number": 2,
            "tracked_wallets": 4,
            "successful_wallet_checks": 4,
            "failed_wallet_checks": 0,
            "status": "OK",
            "last_error": "",
        }
        result.update(changes)
        return result

    def test_recent_four_of_four_is_running_without_process_inspection(self):
        result = smart_money_status(self.report(self.sample()), now_epoch=NOW)
        self.assertEqual(result["state"], "RUNNING")
        self.assertEqual(result["css"], "run")
        self.assertIn("4/4", result["detail"])

    def test_degraded_is_not_reported_as_running(self):
        result = smart_money_status(self.report(self.sample(
            successful_wallet_checks=3, failed_wallet_checks=1,
            status="DEGRADED", last_error="Solana RPC failure")), now_epoch=NOW)
        self.assertEqual(result["state"], "DEGRADED")
        self.assertEqual(result["last_error"], "Solana RPC failure")

    def test_stale_healthy_report_is_stale(self):
        result = smart_money_status(self.report(self.sample(
            observed_at_utc="2026-10-18T17:40:00+00:00")), now_epoch=NOW)
        self.assertEqual(result["state"], "STALE")

    def test_no_report_allows_legacy_process_fallback(self):
        self.assertIsNone(smart_money_status(self.report(None), now_epoch=NOW))

    def test_invalid_json_is_unknown(self):
        p = self.report(self.sample())
        p.write_text("{corrupted", encoding="utf-8")
        self.assertEqual(smart_money_status(p, now_epoch=NOW)["state"], "UNKNOWN")

    def test_all_failed_is_error(self):
        result = smart_money_status(self.report(self.sample(
            successful_wallet_checks=0, failed_wallet_checks=4,
            status="ERROR")), now_epoch=NOW)
        self.assertEqual(result["state"], "ERROR")

    def test_inconsistent_ok_is_not_running(self):
        result = smart_money_status(self.report(self.sample(
            successful_wallet_checks=3, failed_wallet_checks=1)), now_epoch=NOW)
        self.assertEqual(result["state"], "UNKNOWN")

    def test_future_timestamp_is_not_running(self):
        result = smart_money_status(self.report(self.sample(
            observed_at_utc="2026-10-18T18:15:00+00:00")), now_epoch=NOW)
        self.assertEqual(result["state"], "CLOCK SKEW")


if __name__ == "__main__":
    unittest.main()
