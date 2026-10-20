"""Unit and smoke tests for isolated research shadow variants (never live)."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import paper_research_lab_v11_10 as lab
from research.paper_shadow_experiments import (
    VARIANTS, Variant, eligible, effective_spec, generate, qualifies_flow,
    risk_allows, summarize, update_confirmation,
)


def candidate(regime="RISK_OFF", **overrides):
    x = {
        "token_address": "synthetic-token", "symbol": "TEST",
        "momentum_state": "SURGING", "liquidity": 200_000,
        "volume_5m": 35_000, "volume_acceleration": 3.0,
        "buy_sell_ratio_5m": 2.5, "buys_5m": 75, "sells_5m": 10,
        "price_5m": 4.0, "price_1h": 20.0, "price_usd": 0.001,
        "quant_score_raw": 98, "score_delta": 65,
    }
    x.update(overrides)
    return x


class VariantTests(unittest.TestCase):
    def test_policy_compares_control_strict_riskoff_and_neutral_only(self):
        control = next(x for x in VARIANTS if x.name == "xp_diy_control")
        restricted = next(x for x in VARIANTS if x.name == "xp_diy_neutral_only")
        strict = next(x for x in VARIANTS if x.name == "xp_diy_riskoff_strict")
        self.assertTrue(risk_allows(control, candidate(), {"name": "RISK_OFF"}))
        self.assertFalse(risk_allows(restricted, candidate(), {"name": "RISK_OFF"}))
        self.assertTrue(risk_allows(restricted, candidate(), {"name": "NEUTRAL"}))
        self.assertTrue(risk_allows(strict, candidate(), {"name": "RISK_OFF"}))
        self.assertFalse(risk_allows(strict, candidate(liquidity=30_000), {"name": "RISK_OFF"}))

    def test_confirmations_are_independent_and_strictly_time_ordered(self):
        model = {}
        t = datetime(2026, 10, 19, 12, 0, 0)
        self.assertEqual(update_confirmation(model, "X", t, True), 1)
        self.assertEqual(update_confirmation(model, "X", t + timedelta(seconds=1), True), 1)
        self.assertEqual(update_confirmation(model, "X", t + timedelta(seconds=15), True), 2)
        variant = Variant("test", "runner_hunter", confirmations=2)
        self.assertTrue(eligible(variant, model, {"token_address": "X"}, {"name": "NEUTRAL"}, t + timedelta(seconds=15)))
        self.assertEqual(update_confirmation(model, "X", t + timedelta(seconds=30), False), 0)
        self.assertFalse(eligible(variant, model, {"token_address": "X"}, {"name": "NEUTRAL"}, t + timedelta(seconds=30)))
        self.assertEqual(update_confirmation(model, "X", t + timedelta(minutes=7), True), 1)
        self.assertFalse(eligible(variant, model, {"token_address": "X"}, {"name": "NEUTRAL"}, t + timedelta(minutes=7)))

    def test_loss_cooldown_and_exit_modification_are_variant_only(self):
        variant = Variant("test", "balanced_ev", loss_cooldown_minutes=60)
        now = datetime(2026, 10, 19, 16, 0, 0)
        state = {"shadow_last_loss": {"X": (now-timedelta(minutes=40)).isoformat()}}
        self.assertFalse(eligible(variant, state, {"token_address": "X"}, {"name": "NEUTRAL"}, now))
        self.assertTrue(eligible(variant, state, {"token_address": "X"}, {"name": "NEUTRAL"}, now+timedelta(minutes=21)))
        spec = lab.MODEL_SPECS["runner_hunter"]
        v = Variant("test", "runner_hunter", runner_activate_pct=8, trail_pct=5)
        changed = effective_spec(v, spec)
        self.assertEqual(spec.trail_pct, 9)
        self.assertEqual(changed.trail_pct, 5)

    def test_summary_is_raw_mark_only(self):
        report = summarize("/nonexistent/shadow_trades.csv", "2026-10-19")
        self.assertFalse(report["source_present"])
        self.assertTrue(report["not_executable_net_returns"])
        self.assertFalse(report["variants"]["xp_balanced_cd30"]["sample_qualified_for_preliminary_review"])
        with tempfile.TemporaryDirectory() as temp:
            data = generate("/nonexistent/shadow_trades.csv", "2026-10-19", temp)
            self.assertIn("UNPRICED", (Path(temp)/"shadow_experiments.md").read_text())
            self.assertEqual(len(data["variants"]), len(VARIANTS))

    def test_experiment_engine_never_executes_and_controls_keep_specs(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            overrides = {
                "DATA_DIR": p, "STATE_FILE": p/"state.json",
                "OBS_FILE": p/"candidates.csv", "DECISION_FILE": p/"decisions.csv",
                "TRADE_FILE": p/"paper_trades.csv",
                "SHADOW_TRADE_FILE": p/"shadow_trades.csv",
                "EQUITY_FILE": p/"model_equity.csv",
            }
            with patch.multiple(lab, **overrides), patch.dict(
                "os.environ", {"PAPER_SHADOW_EXPERIMENTS_ENABLED": "true",
                               "PAPER_RESEARCH_ENABLED": "true"}
            ):
                old_spec = lab.MODEL_SPECS["runner_hunter"]
                lab.run_paper_research(
                    [candidate()], {"NORMAL_TRADE_SIZE_USDC": 1.5},
                    price_lookup=lambda token: {"price_usd": 0.001},
                    integrity_lookup=lambda c, sz: {"passed": False},
                )
                state = json.loads((p/"state.json").read_text())
                self.assertIn("experiments", state)
                self.assertIn("xp_runner_control", state["experiments"])
                self.assertIs(lab.MODEL_SPECS["runner_hunter"], old_spec)
                self.assertTrue(state["experiments"]["xp_runner_control"]["shadow_positions"])
                self.assertEqual(state["experiments"]["xp_runner_confirm2"]["shadow_positions"], [])
                self.assertFalse((p/"paper_trades.csv").exists() or
                                 any(line.find("action,BUY") >= 0 for line in []))


if __name__ == "__main__":
    unittest.main()
