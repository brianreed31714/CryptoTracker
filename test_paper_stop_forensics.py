"""Stop-loss overrun is not quote age or executable fill quality."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from research.paper_stop_forensics import analyze, generate, duration_minutes


def sell(model, raw, net, cost, *, reason="STOP", date="2026-10-23", symbol="TEST"):
    return {
        "date": date, "model": model, "action": "SELL",
        "reason": reason, "raw_return_pct": raw,
        "net_return_pct": net, "estimated_cost_pct": cost,
        "realized_pnl_usd": "-0.5", "symbol": symbol,
        "token_address": "PRIVATE_MINT_SHOULD_NOT_PUBLISH",
        "entry_time": date + "T18:15:49", "timestamp": date + "T18:19:52",
        "entry_regime": "RISK_OFF", "exit_quote_status": "EXECUTABLE_JUPITER",
    }


class StopForensicsTests(unittest.TestCase):
    def test_separates_price_gap_and_quote_cost(self):
        data = analyze([
            sell("diy_whale", -50.06530612, -62.15573333, 12.09042721, symbol="YMBCOIN"),
            sell("runner_hunter", -11.59178568, -18.87333333, 7.28154766, symbol="SI276"),
            sell("balanced_ev", 1, -2, 3, reason="MOMENTUM_DECAY"),
        ], "2026-10-23")
        whale = data["models"]["diy_whale"]
        self.assertEqual(whale["stop_exits"], 1)
        self.assertEqual(whale["stop_net_overrun_count"], 1)
        self.assertAlmostEqual(whale["worst_stops"][0]["raw_stop_overrun_pp"], 42.065306, places=5)
        self.assertAlmostEqual(whale["worst_stops"][0]["net_stop_overrun_pp"], 54.155733, places=5)
        self.assertEqual(whale["quote_timestamp_verified_count"], 0)
        self.assertEqual(data["models"]["balanced_ev"]["stop_exits"], 0)
        self.assertEqual(data["models"]["runner_hunter"]["stop_raw_gap_count"], 1)
        self.assertAlmostEqual(whale["worst_stops"][0]["holding_minutes"], 4.05, places=1)

    def test_invalid_marks_not_treated_as_zero(self):
        report = analyze([
            sell("runner_hunter", "nan", -60, 10),
            sell("runner_hunter", -8, "-inf", 1),
            sell("runner_hunter", -9, -10, -1),
        ], "2026-10-23")
        runner = report["models"]["runner_hunter"]
        self.assertEqual(runner["stop_exits"], 3)
        self.assertEqual(runner["valid_stop_exits"], 1)
        self.assertEqual(runner["invalid_stop_marks"], 2)
        self.assertEqual(runner["negative_estimated_quote_cost_count"], 1)
        self.assertEqual(runner["quote_timestamp_verified_count"], 0)

    def test_output_sanitized_no_mint_and_no_false_quote_age(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "paper.csv"
            rows = [sell("diy_whale", -50, -62, 12)]
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            dest = Path(tmp) / "out"
            report = generate(path, "2026-10-23", dest)
            self.assertEqual(report["models"]["diy_whale"]["stop_exits"], 1)
            for name in ("stop_forensics.json", "stop_forensics.md"):
                content = (dest / name).read_text(encoding="utf-8")
                self.assertNotIn("PRIVATE_MINT_SHOULD_NOT_PUBLISH", content)
            self.assertIsNone(duration_minutes("bad", "2026-10-23T18:19:52"))
            self.assertIsNone(duration_minutes("2026-10-23T19:00:00", "2026-10-23T18:00:00"))


if __name__ == "__main__":
    unittest.main()
