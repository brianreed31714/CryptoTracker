"""Deterministic read-only MTM quote/provenance tests; no network or trading."""
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from research.paper_liquidation_mtm import (
    assess, generate, render_markdown, FOCUS, QUOTE_STATUS
)

DAY = "2026-10-24"
CYCLE = DAY + "T17:59:30.123456"
CLOCK = datetime(2026, 10, 25, 1, 0, tzinfo=timezone.utc)


def model(position=None, start=15, pnl=2):
    return {"starting_equity": start, "realized_pnl": pnl, "position": position}


def position(token="SENSITIVE_MINT", raw=12345, size=1.5):
    return {"token_address": token, "entry_token_raw": raw, "size_usdc": size,
            "entry_price": 0.00001, "symbol": "SECRET_SYMBOL"}


def quote(token="SENSITIVE_MINT", raw=12345, value=1.1, observed=None,
          status=QUOTE_STATUS, model_name="balanced_ev"):
    return {"model": model_name, "token_address": token, "entry_token_raw": raw,
            "exit_value_usdc": value,
            "observed_at_utc": observed or (CLOCK-timedelta(seconds=15)).isoformat(),
            "status": status}


class LiquidationMTMTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / "state.json"
        self.quotes = self.root / "quotes.json"
        self.write_state({"last_cycle_at": CYCLE, "models": {
            "balanced_ev": model(position()),
            "runner_hunter": model(),
            "diy_whale": model(),
        }})

    def write_state(self, data):
        self.state.write_text(json.dumps(data), encoding="utf-8")

    def write_quotes(self, rows, *, cycle=CYCLE):
        self.quotes.write_text(
            json.dumps({"state_last_cycle_at": cycle, "quotes": rows}),
            encoding="utf-8",
        )

    def audit(self):
        return assess(self.state, self.quotes, DAY, now_utc=CLOCK)

    def test_missing_quote_is_unavailable_not_spot_price_or_zero(self):
        report = self.audit()
        item = report["sleeves"]["balanced_ev"]
        self.assertEqual(item["status"], "MISSING_QUOTE_SNAPSHOT")
        self.assertIsNone(item["point_in_time_paper_equity_usdc"])
        self.assertFalse(report["all_sleeves_point_in_time_equity_available"])
        self.assertEqual(report["sleeves"]["runner_hunter"]["status"],
                         "FLAT_STATE_QUOTE_NOT_REQUIRED")
        self.assertEqual(report["sleeves"]["runner_hunter"]["point_in_time_paper_equity_usdc"], 17)
        self.assertIsNone(report["full_portfolio_daily_return_pct"])
        self.assertIsNone(report["full_portfolio_drawdown_pct"])

    def test_valid_read_only_quote_calculates_cash_plus_liquidation(self):
        self.write_quotes([quote()])
        report = self.audit()
        item = report["sleeves"]["balanced_ev"]
        self.assertEqual(item["status"], "READ_ONLY_QUOTE_ESTIMATE")
        self.assertAlmostEqual(item["point_in_time_paper_equity_usdc"], 16.6)
        self.assertAlmostEqual(item["quoted_open_liquidation_value_usdc"], 1.1)
        self.assertTrue(report["all_sleeves_point_in_time_equity_available"])
        self.assertEqual(item["quote_age_seconds"], 15)
        self.assertIsNone(report["full_portfolio_daily_return_pct"])
        self.assertIsNone(report["full_portfolio_inception_return_pct"])
        self.assertIsNone(report["full_portfolio_drawdown_pct"])
        self.assertTrue(report["paper_only"])
        self.assertFalse(report["orders_submitted"])

    def test_stale_future_unaware_and_failed_quote_fail_closed(self):
        cases = [
            ({"observed_at_utc": (CLOCK-timedelta(seconds=121)).isoformat()},
             "QUOTE_STALE_OR_FUTURE"),
            ({"observed_at_utc": (CLOCK+timedelta(seconds=1)).isoformat()},
             "QUOTE_STALE_OR_FUTURE"),
            ({"observed_at_utc": "2026-10-24T17:59:30"},
             "QUOTE_TIMESTAMP_UNVERIFIED"),
            ({"observed_at_utc": "bad"},
             "QUOTE_TIMESTAMP_UNVERIFIED"),
            ({"status": "NO_ROUTE"}, "QUOTE_NOT_READ_ONLY_JUPITER_SUCCESS"),
            ({"exit_value_usdc": 0}, "INVALID_QUOTE_VALUE"),
            ({"exit_value_usdc": -1}, "INVALID_QUOTE_VALUE"),
            ({"exit_value_usdc": "nan"}, "INVALID_QUOTE_VALUE"),
            ({"exit_value_usdc": "inf"}, "INVALID_QUOTE_VALUE"),
            ({"exit_value_usdc": True}, "INVALID_QUOTE_VALUE"),
            ({"token_address": "OTHER"}, "QUOTE_POSITION_IDENTITY_MISMATCH"),
            ({"entry_token_raw": 12346}, "QUOTE_POSITION_IDENTITY_MISMATCH"),
        ]
        for changes, expected in cases:
            with self.subTest(changes=changes):
                self.write_quotes([{**quote(), **changes}])
                item = self.audit()["sleeves"]["balanced_ev"]
                self.assertEqual(item["status"], expected)
                self.assertIsNone(item["point_in_time_paper_equity_usdc"])

    def test_duplicate_or_mismatched_cycle_never_selects_quote(self):
        self.write_quotes([quote(), quote(value=4)])
        self.assertEqual(self.audit()["sleeves"]["balanced_ev"]["status"],
                         "DUPLICATE_MODEL_QUOTES")
        self.write_quotes([quote()], cycle="WRONG_CYCLE")
        self.assertEqual(self.audit()["sleeves"]["balanced_ev"]["status"],
                         "QUOTE_STATE_CYCLE_MISMATCH")

    def test_wrong_day_and_missing_state_fail_closed(self):
        self.write_quotes([quote()])
        self.assertEqual(assess(self.state, self.quotes, "2026-10-23", now_utc=CLOCK)
                         ["sleeves"]["balanced_ev"]["status"],
                         "STATE_MISSING_OR_WRONG_REPORT_DATE")
        self.state.unlink()
        self.assertFalse(self.audit()["state_present"])
        self.assertIsNone(self.audit()["sleeves"]["runner_hunter"]["point_in_time_paper_equity_usdc"])

    def test_invalid_open_position_provenance_fails(self):
        for invalid in [
            position(raw=0), position(raw=1.5), position(size=-1),
            position(size=18), position(token=""), position(size=float("nan")),
        ]:
            with self.subTest(invalid=invalid):
                self.write_state({"last_cycle_at": CYCLE, "models": {
                    "balanced_ev": model(invalid),
                    "runner_hunter": model(),
                    "diy_whale": model(),
                }})
                self.write_quotes([quote()])
                item = self.audit()["sleeves"]["balanced_ev"]
                self.assertEqual(item["status"], "INVALID_POSITION_PROVENANCE")
                self.assertIsNone(item["point_in_time_paper_equity_usdc"])

    def test_output_is_sanitized_and_only_aggregate(self):
        self.write_quotes([quote()])
        destination = self.root / "output"
        report = generate(self.state, self.quotes, DAY, destination, now_utc=CLOCK)
        self.assertEqual(set(report["sleeves"]), set(FOCUS))
        for file in ("liquidation_mtm_readiness.json", "liquidation_mtm_readiness.md"):
            data = (destination / file).read_text(encoding="utf-8")
            self.assertNotIn("SENSITIVE_MINT", data)
            self.assertNotIn("SECRET_SYMBOL", data)
            self.assertNotIn("entry_token_raw", data)
            self.assertIn("paper", data.lower())
        self.assertIn("N/A", render_markdown(report))

    def test_missing_one_quote_prevents_complete_multi_sleeve_equity(self):
        state = json.loads(self.state.read_text())
        state["models"]["runner_hunter"]["position"] = position("OTHER_MINT", raw=67890)
        self.write_state(state)
        self.write_quotes([quote()])
        report = self.audit()
        self.assertEqual(report["sleeves"]["balanced_ev"]["status"], "READ_ONLY_QUOTE_ESTIMATE")
        self.assertEqual(report["sleeves"]["runner_hunter"]["status"], "MISSING_LIQUIDATION_QUOTE")
        self.assertFalse(report["all_sleeves_point_in_time_equity_available"])


if __name__ == "__main__":
    unittest.main()
