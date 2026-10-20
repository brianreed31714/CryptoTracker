"""Regression tests for 1% target reporting; no exchange access required."""
import csv
import tempfile
import unittest
from pathlib import Path
from research.paper_goal_scorecard import goal_scorecard

class GoalScorecardTests(unittest.TestCase):
    def test_daily_vs_inception_and_compounding(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "paper_trades.csv"
            with path.open("w", newline="") as h:
                w = csv.DictWriter(h, fieldnames=["date","timestamp","model","action","realized_pnl_usd","net_return_pct"])
                w.writeheader()
                w.writerows([
                    {"date":"2026-10-17","timestamp":"2026-10-17T12:00","model":"balanced_ev","action":"BUY"},
                    {"date":"2026-10-17","timestamp":"2026-10-17T13:00","model":"balanced_ev","action":"SELL","realized_pnl_usd":"1.5","net_return_pct":"50"},
                    {"date":"2026-10-18","timestamp":"2026-10-18T13:00","model":"balanced_ev","action":"SELL","realized_pnl_usd":"0.165","net_return_pct":"1"},
                ])
            data = goal_scorecard(path, "2026-10-18", {"balanced_ev":15,"runner_hunter":15,"diy_whale":15})
            s = data["sleeves"]["balanced_ev"]
            self.assertAlmostEqual(s["daily_realized_equity_return_pct"], 1.0)
            self.assertAlmostEqual(s["since_inception_realized_equity_return_pct"], 11.1)
            self.assertAlmostEqual(s["since_inception_compounded_1pct_daily_target_pct"], 2.01)
            self.assertTrue(s["daily_goal_met_on_realized_basis"])
            self.assertEqual(s["elapsed_calendar_days_inclusive"], 2)
            self.assertEqual(s["full_portfolio_daily_return_pct"], None)
            self.assertEqual(data["sleeves"]["runner_hunter"]["daily_completed"], 0)
            self.assertIsNone(data["sleeves"]["runner_hunter"]["since_inception_compounded_1pct_daily_target_pct"])

    def test_negative_equity_drawdown_not_compounded_trade_return(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trades.csv"
            with path.open("w", newline="") as h:
                w = csv.DictWriter(h, fieldnames=["date","timestamp","model","action","realized_pnl_usd","net_return_pct"])
                w.writeheader()
                w.writerows([
                    {"date":"2026-10-19","timestamp":"2026-10-19T01:00","model":"diy_whale","action":"SELL","realized_pnl_usd":"-0.75","net_return_pct":"-99"},
                    {"date":"2026-10-19","timestamp":"2026-10-19T02:00","model":"diy_whale","action":"SELL","realized_pnl_usd":"0.15","net_return_pct":"20"},
                ])
            s=goal_scorecard(path,"2026-10-19",{"diy_whale":15})["sleeves"]["diy_whale"]
            self.assertAlmostEqual(s["daily_realized_equity_return_pct"], -4.0)
            self.assertAlmostEqual(s["daily_realized_equity_drawdown_pct"], 5.0)
            self.assertFalse(s["daily_goal_met_on_realized_basis"])

if __name__ == "__main__":
    unittest.main()
