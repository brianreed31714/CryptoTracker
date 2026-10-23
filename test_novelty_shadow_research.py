"""Safety and prospective feature tests for read-only DIY name/flow variants.

These tests NEVER connect to the chain or send a swap.
"""
import csv
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import paper_research_lab_v11_10 as lab
from research.paper_shadow_experiments import (
    VARIANTS, eligible, name_categories, novelty_metadata,
    qualifies_diy_organic_flow, summarize,
)


def sample(**changes):
    item = {
        "token_address": "TEST_MINT_1",
        "name": "FuckRocket",
        "symbol": "FRKT",
        "momentum_state": "SURGING",
        "price_usd": 0.001,
        "liquidity": 200_000,
        "volume_5m": 35_000,
        "buys_5m": 75,
        "sells_5m": 10,
        "buy_sell_ratio_5m": 2.5,
        "volume_acceleration": 3.0,
        "price_5m": 4.0,
        "price_1h": 20.0,
        "quant_score_raw": 98,
        "score_delta": 65,
    }
    item.update(changes)
    return item


class NoveltyShadowTests(unittest.TestCase):
    def test_classifier_includes_sexual_profanity_and_toilet_language(self):
        self.assertIn("sexual", name_categories(sample(name="CumRocket", symbol="CUM")))
        self.assertIn("profanity", name_categories(sample(name="FuckRocket", symbol="FUCK")))
        self.assertIn("toilet", name_categories(sample(name="FARTCOIN", symbol="FART")))
        self.assertFalse(name_categories(sample(name="Butterfly", symbol="BUTTER")))
        self.assertFalse(name_categories(sample(name="", symbol="")))

    def test_require_known_at_entry_score_and_extra_flow(self):
        now = datetime(2026, 10, 22, 13, 0)
        variants = {v.name: v for v in VARIANTS}
        self.assertFalse(eligible(variants["xp_diy_name12"], {}, sample(), {"name": "NEUTRAL"}, now))
        candidate = sample(paper_name_novelty={"name_novelty_score": 18.0})
        self.assertTrue(eligible(variants["xp_diy_name12"], {}, candidate, {"name": "NEUTRAL"}, now))
        self.assertTrue(eligible(variants["xp_diy_raunchy"], {}, candidate, {"name": "NEUTRAL"}, now))
        self.assertTrue(eligible(variants["xp_diy_name12_flow"], {}, candidate, {"name": "NEUTRAL"}, now))
        self.assertTrue(eligible(variants["xp_diy_raunchy_flow"], {}, candidate, {"name": "NEUTRAL"}, now))
        weak = sample(paper_name_novelty={"name_novelty_score": 18.0},
                      buy_sell_ratio_5m=1.15, volume_acceleration=1.15)
        self.assertFalse(qualifies_diy_organic_flow(weak))
        self.assertFalse(eligible(variants["xp_diy_name12_flow"], {}, weak, {"name": "NEUTRAL"}, now))
        self.assertTrue(eligible(variants["xp_diy_name12"], {}, weak, {"name": "NEUTRAL"}, now))
        self.assertFalse(eligible(variants["xp_diy_raunchy"], {},
                                  sample(name="Ordinary Word", symbol="ORD",
                                         paper_name_novelty={"name_novelty_score": 18}),
                                  {"name": "NEUTRAL"}, now))

    def test_invalid_score_is_not_silently_treated_as_novel(self):
        now = datetime(2026, 10, 22, 13, 0)
        variant = next(v for v in VARIANTS if v.name == "xp_diy_name12")
        for value in (None, "nan", float("inf"), "", -9):
            item = sample(paper_name_novelty={"name_novelty_score": value})
            self.assertFalse(eligible(variant, {}, item, {"name": "RISK_OFF"}, now))
        self.assertIsNone(novelty_metadata(sample())["name_novelty_score"])

    def test_engine_writes_prospective_shadow_rows_without_baseline_orders(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = {
                "DATA_DIR": root,
                "STATE_FILE": root / "state.json",
                "OBS_FILE": root / "observations.csv",
                "DECISION_FILE": root / "decisions.csv",
                "TRADE_FILE": root / "paper_trades.csv",
                "SHADOW_TRADE_FILE": root / "shadow_trades.csv",
                "EQUITY_FILE": root / "equity.csv",
            }
            with patch.multiple(lab, **paths), patch.dict(
                "os.environ",
                {"PAPER_SHADOW_EXPERIMENTS_ENABLED": "true",
                 "PAPER_RESEARCH_ENABLED": "true", "LIVE_TRADING": "false"},
            ):
                unchanged = lab.MODEL_SPECS["diy_whale"]
                lab.run_paper_research(
                    [sample()],
                    {"NORMAL_TRADE_SIZE_USDC": 1.5},
                    price_lookup=lambda _: {"price_usd": 0.001},
                    integrity_lookup=lambda c, size: {"passed": False},
                )
                state = json.loads((root / "state.json").read_text())
                for name in ("xp_diy_control", "xp_diy_name12",
                             "xp_diy_organic_flow", "xp_diy_name12_flow",
                             "xp_diy_raunchy", "xp_diy_raunchy_flow"):
                    self.assertEqual(len(state["experiments"][name]["shadow_positions"]), 1, name)
                self.assertIs(lab.MODEL_SPECS["diy_whale"], unchanged)
                self.assertFalse((root / "paper_trades.csv").exists())
                with (root / "shadow_trades.csv").open(newline="", encoding="utf-8") as handle:
                    buys = [row for row in csv.DictReader(handle)
                            if row["action"] == "BUY" and row["model"] == "xp_diy_raunchy_flow"]
                self.assertEqual(len(buys), 1)
                self.assertEqual(buys[0]["name"], "FuckRocket")
                self.assertIn("profanity", buys[0]["name_category_flags"])
                self.assertEqual(buys[0]["organic_flow_at_entry"], "True")
                self.assertEqual(buys[0]["novelty_study_version"], "NOVELTY_FLOW_V1_20261022")

                # Price-only shadow stop: preserve original ENTRY metadata even
                # if the current token metadata subsequently changes.
                lab.run_paper_research(
                    [sample(name="Unrelated Updated Name", symbol="UPDATED",
                            price_usd=0.0006)],
                    {"NORMAL_TRADE_SIZE_USDC": 1.5},
                    price_lookup=lambda _: {"price_usd": 0.0006},
                    integrity_lookup=lambda c, size: {"passed": False},
                )
                with (root / "shadow_trades.csv").open(newline="", encoding="utf-8") as handle:
                    sells = [row for row in csv.DictReader(handle)
                             if row["action"] == "SELL" and row["model"] == "xp_diy_raunchy_flow"]
                self.assertEqual(len(sells), 1)
                self.assertEqual(sells[0]["name"], "FuckRocket")
                self.assertEqual(sells[0]["organic_flow_at_entry"], "True")
                self.assertEqual(sells[0]["novelty_study_version"], "NOVELTY_FLOW_V1_20261022")
                report = summarize(root / "shadow_trades.csv", datetime.now().date().isoformat())
                self.assertFalse(report["variants"]["xp_diy_raunchy_flow"]["promotable"])
                self.assertTrue(report["not_executable_net_returns"])
                self.assertEqual(report["variants"]["xp_diy_raunchy_flow"]["n_completed_today"], 1)
                self.assertFalse((root / "paper_trades.csv").exists())


if __name__ == "__main__":
    unittest.main()
