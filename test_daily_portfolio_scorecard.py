import unittest
from research.daily_portfolio_scorecard import scorecard

class PortfolioScorecardTests(unittest.TestCase):
    def test_compounding_and_hit_rate(self):
        rows=[{"model":"balanced_ev","date":"2026-10-17","equity":"100"},{"model":"balanced_ev","date":"2026-10-18","equity":"101"},{"model":"balanced_ev","date":"2026-10-19","equity":"100"}]
        r=scorecard(rows,as_of="2026-10-19")["sleeves"]["balanced_ev"]
        self.assertEqual(r["observed_target_days"],1)
        self.assertEqual(r["observed_daily_return_days"],2)
        self.assertEqual(r["target_hit_rate_pct"],50)
        self.assertEqual(r["since_inception_portfolio_return_pct"],0)
        self.assertAlmostEqual(r["compounded_1pct_target_return_pct"],2.01)
        self.assertLess(r["daily_portfolio_return_pct"],0)
    def test_missing_equity_does_not_fabricate_returns(self):
        r=scorecard([],as_of="2026-10-19")["sleeves"]["diy_whale"]
        self.assertIsNone(r["daily_portfolio_return_pct"])
        self.assertTrue(r["stale"])
    def test_missing_day_not_counted_as_daily_return(self):
        rows=[{"model":"runner_hunter","date":"2026-10-17","equity":"100"},{"model":"runner_hunter","date":"2026-10-19","equity":"105"}]
        r=scorecard(rows,as_of="2026-10-19")["sleeves"]["runner_hunter"]
        self.assertEqual(r["observed_daily_return_days"],0)
        self.assertIsNone(r["daily_portfolio_return_pct"])
    def test_future_equity_cannot_leak_into_inception_or_drawdown(self):
        rows=[
            {"model":"balanced_ev","date":"2026-10-17","equity":"100"},
            {"model":"balanced_ev","date":"2026-10-18","equity":"101"},
            {"model":"balanced_ev","date":"2026-10-19","equity":"1"},
        ]
        r=scorecard(rows,as_of="2026-10-18")["sleeves"]["balanced_ev"]
        self.assertEqual(r["latest_equity_date"],"2026-10-18")
        self.assertEqual(r["excluded_future_rows"],1)
        self.assertEqual(r["since_inception_portfolio_return_pct"],1.0)
        self.assertEqual(r["max_observed_equity_drawdown_pct"],0.0)

    def test_conflicting_same_day_equity_is_not_silently_overwritten(self):
        rows=[
            {"model":"runner_hunter","date":"2026-10-17","equity":"100"},
            {"model":"runner_hunter","date":"2026-10-18","equity":"105"},
            {"model":"runner_hunter","date":"2026-10-18","equity":"95"},
        ]
        r=scorecard(rows,as_of="2026-10-18")["sleeves"]["runner_hunter"]
        self.assertEqual(r["conflicting_equity_dates"],["2026-10-18"])
        self.assertIsNone(r["daily_portfolio_return_pct"])
        self.assertIsNone(r["since_inception_portfolio_return_pct"])
        self.assertTrue(r["stale"])

    def test_malformed_nonfinite_equity_and_dates_are_excluded(self):
        rows=[
            {"model":"diy_whale","date":"2026-10-17","equity":"100"},
            {"model":"diy_whale","date":"2026-10-18","equity":"nan"},
            {"model":"diy_whale","date":"2026-10-19","equity":"inf"},
            {"model":"diy_whale","date":"2026-10-xx","equity":"150"},
        ]
        r=scorecard(rows,as_of="2026-10-19")["sleeves"]["diy_whale"]
        self.assertEqual(r["excluded_invalid_rows"],3)
        self.assertIsNone(r["daily_portfolio_return_pct"])
        self.assertIsNone(r["since_inception_portfolio_return_pct"])
        with self.assertRaises(ValueError):
            scorecard([],as_of="20261019")

if __name__=="__main__":
    unittest.main()
