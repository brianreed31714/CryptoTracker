import csv
import json
import tempfile
import unittest
from pathlib import Path

from infrastructure.eod_pushover_qc import format_paper_sleeves


class EodPushoverQcTests(unittest.TestCase):
    def test_missing_evidence_is_not_zero(self):
        with tempfile.TemporaryDirectory() as folder:
            lines = format_paper_sleeves(folder, "2026-11-02")
            self.assertIn("MISSING", " ".join(lines))
            self.assertNotIn("day +0.00%", " ".join(lines))

    def test_reconciled_counts_and_missing_portfolio_roi(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder) / "published/daily/2026-11-02"
            (base / "raw").mkdir(parents=True)
            sleeves = {}
            for key in ("balanced_ev", "runner_hunter", "diy_whale"):
                sleeves[key] = {
                    "daily_completed": 2, "daily_realized_equity_return_pct": 1.25,
                    "since_inception_realized_equity_return_pct": 3.5,
                    "since_inception_realized_equity_drawdown_pct": 2.5,
                    "daily_realized_pnl_usd": 0.25,
                }
            (base / "paper_summary.json").write_text(json.dumps({
                "date": "2026-11-02", "goal_1pct_daily": {"sleeves": sleeves}
            }))
            with (base / "raw/paper_trades.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["date", "model", "action", "net_return_pct"])
                writer.writeheader()
                for key in sleeves:
                    for net in ("2.0", "-1.0"):
                        writer.writerow({"date": "2026-11-02", "model": key,
                                         "action": "SELL", "net_return_pct": net})
            lines = "\n".join(format_paper_sleeves(folder, "2026-11-02"))
            self.assertEqual(lines.count("W/L/flat 1/1/0"), 3)
            self.assertIn("day +1.25%", lines)
            self.assertIn("Invested-capital portfolio ROI: MISSING", lines)
            sleeves["balanced_ev"]["daily_completed"] = 3
            (base / "paper_summary.json").write_text(json.dumps({
                "date": "2026-11-02", "goal_1pct_daily": {"sleeves": sleeves}
            }))
            lines = "\n".join(format_paper_sleeves(folder, "2026-11-02"))
            self.assertIn("Core: MISSING / RECONCILIATION REQUIRED", lines)


if __name__ == "__main__":
    unittest.main()
