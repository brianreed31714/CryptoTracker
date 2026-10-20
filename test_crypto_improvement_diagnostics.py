"""Unit tests for read-only sleeve-improvement diagnostics."""
import tempfile
import unittest
from pathlib import Path

from research.crypto_improvement_diagnostics import analyze, generate, render_markdown


def event(date, stamp, model, action, token="TOKEN", pnl="", ret="", regime="NEUTRAL",
          cost="", raw="", peak="", quote="EXECUTABLE_JUPITER", reason=""):
    return {
        "date": date, "timestamp": stamp, "model": model, "action": action,
        "token_address": token, "symbol": token, "entry_time": stamp,
        "realized_pnl_usd": pnl, "net_return_pct": ret, "entry_regime": regime,
        "estimated_cost_pct": cost, "raw_return_pct": raw, "peak_return_pct": peak,
        "exit_quote_status": quote, "reason": reason,
    }


class DiagnosticsTests(unittest.TestCase):
    def test_zero_sample_is_unknown_not_profitable(self):
        report = analyze([], "2026-10-19")
        for row in report["sleeves"].values():
            self.assertEqual(row["daily"]["completed"], 0)
            self.assertIsNone(row["daily"]["profit_factor"])
            self.assertIsNone(row["daily"]["win_rate_pct"])
        self.assertFalse(report["full_mark_to_market_available"])
        self.assertFalse(report["promotion_allowed"])

    def test_loss_cooldown_counts_and_regime_research_are_noncausal(self):
        trades = [
            event("2026-10-19", "2026-10-19T12:00:00", "diy_whale", "SELL",
                  pnl="-0.3", ret="-20", regime="RISK_OFF", cost="6.2", reason="STOP"),
            event("2026-10-19", "2026-10-19T12:25:00", "diy_whale", "BUY"),
            event("2026-10-19", "2026-10-19T12:45:00", "diy_whale", "BUY"),
            event("2026-10-19", "2026-10-19T14:10:00", "diy_whale", "BUY"),
        ]
        r = analyze(trades, "2026-10-19")["sleeves"]["diy_whale"]
        self.assertEqual(r["regime_selection"]["risk_off"]["completed"], 1)
        self.assertEqual(r["regime_selection"]["risk_off"]["net_pnl_usd"], -0.3)
        self.assertEqual(r["cooldown_candidates"]["30"]["observed_reentries_after_loss"], 1)
        self.assertEqual(r["cooldown_candidates"]["60"]["observed_reentries_after_loss"], 2)
        self.assertEqual(r["cooldown_candidates"]["120"]["observed_reentries_after_loss"], 2)
        self.assertEqual(r["execution"]["negative_or_over_5pct_estimated_cost_count"], 1)
        self.assertEqual(r["execution"]["stops_exceeding_threshold_by_more_than_3pp"][0]["token"], "TOKEN")

    def test_no_future_trade_leakage(self):
        rows = [
            event("2026-10-19", "2026-10-19T09:00:00", "balanced_ev", "SELL",
                  pnl="-0.2", ret="-12", raw="-8", peak="9"),
            event("2026-10-20", "2026-10-20T09:00:00", "balanced_ev", "SELL",
                  pnl="9", ret="900", raw="900", peak="910"),
        ]
        r = analyze(rows, "2026-10-19")["sleeves"]["balanced_ev"]
        self.assertEqual(r["inception"]["completed"], 1)
        self.assertEqual(r["daily"]["net_pnl_usd"], -0.2)
        self.assertEqual(r["exit_capture"]["losing_exits_after_at_least_8pct_observed_peak"], 1)

    def test_generated_reports_do_not_contain_token_addresses(self):
        # Aggregates only. No wallet, secrets or individual trading addresses.
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "paper_trades.csv"
            csv_path.write_text(
                "date,timestamp,model,action,token_address,symbol,realized_pnl_usd,net_return_pct\n"
                "2026-10-19,2026-10-19T15:00:00,runner_hunter,SELL,"
                "SecretOpaqueTokenAddressShouldNotBePublished,CAT,-0.10,-13\n",
                encoding="utf-8",
            )
            target = Path(tmp) / "out"
            result = generate(csv_path, "2026-10-19", target)
            self.assertEqual(result["sleeves"]["runner_hunter"]["daily"]["completed"], 1)
            for filename in ("improvement_diagnostics.json", "improvement_diagnostics.md"):
                text = (target / filename).read_text(encoding="utf-8")
                self.assertNotIn("SecretOpaqueTokenAddressShouldNotBePublished", text)
                self.assertNotIn("private_key", text)
            self.assertIn("NOT a", "NOT a" if result["full_mark_to_market_available"] is False else "")

    def test_markdown_labels_1pct_goal_as_unverified_portfolio(self):
        text = render_markdown(analyze([], "2026-10-19"))
        self.assertIn("Target: +1.00%", text)
        self.assertIn("unavailable until verified", text)
        self.assertIn("read-only audit", text)


if __name__ == "__main__":
    unittest.main()
