import unittest
import paper_research_lab_v11_10 as lab

class RunnerHunterTests(unittest.TestCase):
    def test_registered(self):
        self.assertIn("runner_hunter", lab.MODEL_SPECS)
        self.assertEqual(lab.MODEL_SPECS["runner_hunter"].size_key, "PROBE")

    def test_high_momentum_can_qualify(self):
        c = dict(momentum_state="SURGING",price_usd=.001,liquidity=50000,
                 volume_5m=25000,buys_5m=100,sells_5m=20,
                 volume_acceleration=5,buy_sell_ratio_5m=5,
                 score_delta=90,price_5m=55,price_1h=130,quant_score_raw=110)
        spec=lab.MODEL_SPECS["runner_hunter"]
        score=lab._model_score(c,spec,{"name":"NEUTRAL"})
        ok,reasons=lab._model_safety_pass("runner_hunter",c,spec,{"name":"NEUTRAL"},score)
        self.assertTrue(ok, reasons)

    def test_diy_whale_early_organic_flow(self):
        c = dict(momentum_state="BUILDING", price_usd=.0001, liquidity=90000,
                 volume_5m=18000, buys_5m=80, sells_5m=25,
                 volume_acceleration=3.5, buy_sell_ratio_5m=3.2,
                 score_delta=30, price_5m=4, price_1h=12, quant_score_raw=95)
        spec = lab.MODEL_SPECS["diy_whale"]
        score = lab._model_score(c, spec, {"name":"NEUTRAL"})
        ok, reasons = lab._model_safety_pass("diy_whale", c, spec, {"name":"NEUTRAL"}, score)
        self.assertTrue(ok, reasons)

    def test_diy_whale_rejects_illiquid(self):
        c = dict(price_usd=.0001, liquidity=2000, volume_5m=18000,
                 buys_5m=80, sells_5m=25, volume_acceleration=3.5,
                 buy_sell_ratio_5m=3.2, score_delta=30, price_5m=4,
                 price_1h=12, quant_score_raw=95)
        spec = lab.MODEL_SPECS["diy_whale"]
        ok, reasons = lab._model_safety_pass("diy_whale", c, spec, {"name":"NEUTRAL"}, 100)
        self.assertFalse(ok)
        self.assertIn("liquidity_lt_50k", reasons)

    def test_low_liquidity_rejected(self):
        c = dict(momentum_state="SURGING",price_usd=.001,liquidity=100,
                 volume_5m=25000,buys_5m=100,sells_5m=20,
                 volume_acceleration=5,buy_sell_ratio_5m=5,
                 score_delta=90,price_5m=55,price_1h=130,quant_score_raw=110)
        spec=lab.MODEL_SPECS["runner_hunter"]
        ok,reasons=lab._model_safety_pass("runner_hunter",c,spec,{"name":"NEUTRAL"},100)
        self.assertFalse(ok)
        self.assertIn("liquidity_lt_20k",reasons)

if __name__=="__main__":
    unittest.main()
