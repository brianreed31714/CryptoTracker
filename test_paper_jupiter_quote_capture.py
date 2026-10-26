"""Offline deterministic tests for opt-in paper-only quote collection."""
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from research.paper_jupiter_quote_capture import (
    CaptureRejected, USDC_MINT, capture,
)
from research.paper_liquidation_mtm import assess

MINT = "So11111111111111111111111111111111111111112"
NOW = datetime(2026, 10, 26, 1, 0, tzinfo=timezone.utc)  # Oct 25 18:00 Pacific
CYCLE = "2026-10-25T17:59:30"


def state(position=None):
    return {
        "last_cycle_at": CYCLE,
        "models": {
            "balanced_ev": {"starting_equity": 15, "realized_pnl": 2, "position": position},
            "runner_hunter": {"starting_equity": 15, "realized_pnl": 0, "position": None},
            "diy_whale": {"starting_equity": 15, "realized_pnl": 0, "position": None},
        },
    }


def position(**overrides):
    result = {"token_address": MINT, "entry_token_raw": 1234567, "size_usdc": 1.5}
    result.update(overrides)
    return result


class QuoteCaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.state_path = root / "state.json"
        self.output = root / "liquidation_quotes.json"
        self.write(state(position()))
        self.calls = []
        self.now = NOW

    def write(self, data):
        self.state_path.write_text(json.dumps(data), encoding="utf-8")

    def get(self, params, headers, timeout):
        self.calls.append((params, headers, timeout))
        return {"outAmount": "1099999", "inAmount": params["amount"],
                "inputMint": params["inputMint"], "outputMint": USDC_MINT,
                "transaction": None, "requestId": "PRIVATE_REQUEST_ID"}

    def run_capture(self, *, get=None, enabled=True, key="PRIVATE_KEY"):
        return capture(self.state_path, self.output, api_key=key,
                       enabled=enabled, http_get=get or self.get,
                       clock=lambda: self.now)

    def test_opt_in_quote_only_and_mtm_contract(self):
        with patch.dict(os.environ, {"LIVE_TRADING": "false"}):
            result = self.run_capture()
        self.assertEqual(result["open_positions_quoted"], 1)
        self.assertFalse(result["orders_submitted"])
        self.assertEqual(len(self.calls), 1)
        params, headers, timeout = self.calls[0]
        self.assertEqual(set(params), {"inputMint", "outputMint", "amount"})
        self.assertEqual(params["amount"], "1234567")
        self.assertNotIn("taker", params)
        self.assertEqual(headers["x-api-key"], "PRIVATE_KEY")
        self.assertEqual(timeout, 12)
        contents = self.output.read_text()
        self.assertNotIn("PRIVATE_KEY", contents)
        self.assertNotIn("PRIVATE_REQUEST_ID", contents)
        report = assess(self.state_path, self.output, "2026-10-25", now_utc=NOW)
        item = report["sleeves"]["balanced_ev"]
        self.assertEqual(item["status"], "READ_ONLY_QUOTE_ESTIMATE")
        self.assertAlmostEqual(item["quoted_open_liquidation_value_usdc"], 1.099999)
        self.assertAlmostEqual(item["point_in_time_paper_equity_usdc"], 16.599999)
        self.assertIsNone(report["full_portfolio_daily_return_pct"])

    def test_default_off_and_live_guard_block_before_network(self):
        with patch.dict(os.environ, {"LIVE_TRADING": "false"}):
            with self.assertRaisesRegex(CaptureRejected, "NOT_OPTED_IN"):
                self.run_capture(enabled=False)
        with patch.dict(os.environ, {"LIVE_TRADING": "true"}):
            with self.assertRaisesRegex(CaptureRejected, "LIVE_TRADING_MODE_REJECTED"):
                self.run_capture()
        self.assertEqual(self.calls, [])
        self.assertFalse(self.output.exists())

    def test_stale_future_and_wrong_timezone_cycles_reject_before_network(self):
        for cycle in ("2026-10-25T17:45:00", "2026-10-25T18:02:00",
                      "2026-10-25T17:59:30+00:00", "INVALID"):
            with self.subTest(cycle=cycle):
                s = state(position())
                s["last_cycle_at"] = cycle
                self.write(s)
                with patch.dict(os.environ, {"LIVE_TRADING": "false"}):
                    with self.assertRaisesRegex(CaptureRejected, "STATE_CYCLE_STALE_OR_FUTURE"):
                        self.run_capture()
        self.assertEqual(self.calls, [])

    def test_invalid_position_blocks_every_quote(self):
        for change in ({"entry_token_raw": 0}, {"entry_token_raw": 1.2},
                       {"token_address": "BAD_MINT"}, {"size_usdc": 100},
                       {"remaining_fraction": 0.5}):
            with self.subTest(change=change):
                self.write(state(position(**change)))
                with patch.dict(os.environ, {"LIVE_TRADING": "false"}):
                    with self.assertRaises(CaptureRejected):
                        self.run_capture()
        self.assertEqual(self.calls, [])

    def test_provider_failures_do_not_write_success_snapshot(self):
        cases = [
            {"outAmount": 0}, {"outAmount": "-1"}, {"outAmount": "nan"},
            {"outAmount": "1.5"}, {"outAmount": "100", "inAmount": "1234568"},
            {"outAmount": "100", "outputMint": MINT},
            {"outAmount": "100", "inputMint": USDC_MINT},
            {"outAmount": "100", "transaction": "UNSIGNED_TX"},
            {"outAmount": "100", "errorCode": 500},
            {"outAmount": "100", "error": "NO_ROUTE"},
            {},
        ]
        for response in cases:
            with self.subTest(response=response):
                with patch.dict(os.environ, {"LIVE_TRADING": "false"}):
                    with self.assertRaises(CaptureRejected):
                        self.run_capture(get=lambda *args: response)
                self.assertFalse(self.output.exists())

    def test_changed_state_mid_request_rejects_old_quote(self):
        def changed(*args):
            self.write(state(None))
            return {"outAmount": "12345"}
        with patch.dict(os.environ, {"LIVE_TRADING": "false"}):
            with self.assertRaisesRegex(CaptureRejected, "STATE_CHANGED_DURING_QUOTE"):
                self.run_capture(get=changed)
        self.assertFalse(self.output.exists())

    def test_expired_cycle_during_network_rejects(self):
        def slow(*args):
            self.now += timedelta(minutes=3)
            return {"outAmount": "12345"}
        with patch.dict(os.environ, {"LIVE_TRADING": "false"}):
            with self.assertRaisesRegex(CaptureRejected, "STATE_CYCLE_EXPIRED_DURING_QUOTE"):
                self.run_capture(get=slow)
        self.assertFalse(self.output.exists())

    def test_partial_provider_failure_is_atomic(self):
        s = state(position())
        s["models"]["runner_hunter"]["position"] = position()
        self.write(s)
        def partial(params, headers, timeout):
            if len(self.calls) == 0:
                self.calls.append("one")
                return {"outAmount": "123456"}
            raise TimeoutError("secret error body")
        with patch.dict(os.environ, {"LIVE_TRADING": "false"}):
            with self.assertRaisesRegex(CaptureRejected, "QUOTE_REQUEST_FAILED"):
                self.run_capture(get=partial)
        self.assertFalse(self.output.exists())

    def test_flat_sleeves_need_no_network_and_no_quote_rows(self):
        self.write(state(None))
        with patch.dict(os.environ, {"LIVE_TRADING": "false"}):
            report = self.run_capture()
        self.assertEqual(report["open_positions_quoted"], 0)
        self.assertEqual(self.calls, [])
        self.assertEqual(json.loads(self.output.read_text())["quotes"], [])


if __name__ == "__main__":
    unittest.main()
