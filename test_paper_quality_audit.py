import json
import tempfile
import unittest
from pathlib import Path
from research.paper_quality_audit import audit_paper_day

class PaperQualityAuditTests(unittest.TestCase):
    def test_execution_flags_and_repeated_losses(self):
        rows = [
            {"model":"diy_whale","date":"2026-10-19","action":"BUY","token_address":"ABC","entry_regime":"RISK_OFF"},
            {"model":"diy_whale","date":"2026-10-19","action":"SELL","token_address":"ABC",
             "realized_pnl_usd":"-0.2","net_return_pct":"-23","estimated_cost_pct":"-3",
             "helius_status":"UNAVAILABLE_DISABLED"},
            {"model":"diy_whale","date":"2026-10-19","action":"SELL","token_address":"ABC",
             "realized_pnl_usd":"-0.1","net_return_pct":"-5","estimated_cost_pct":"8",
             "data_quality_flags":"HELIUS_UNAVAILABLE_OPTIONAL"},
        ]
        d=audit_paper_day(rows,"2026-10-19")["models"]["diy_whale"]
        self.assertEqual(d["completed"],2)
        self.assertEqual(d["negative_estimated_execution_cost_exits"],1)
        self.assertEqual(d["over_5pct_estimated_execution_cost_exits"],1)
        self.assertEqual(d["severe_net_loss_below_minus_20pct"],1)
        self.assertEqual(d["risk_off_entries"],1)
        self.assertEqual(d["tokens_with_repeated_loss_exits"],{"ABC":2})
        self.assertEqual(d["unavailable_helius_exits"],2)

    def test_campaign_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            previous=root/"2026-10-18"
            current=root/"2026-10-19"
            previous.mkdir();current.mkdir()
            def write(path, counts):
                path.write_text(json.dumps({"models":[{"model":k,"all":{"n":v,"realized_pnl_usd":0}} for k,v in counts.items()]}))
            write(previous/"campaign_summary.json",{"balanced_ev":100,"runner_hunter":40,"diy_whale":90})
            write(current/"campaign_summary.json",{"balanced_ev":100,"runner_hunter":41,"diy_whale":93})
            rows=[
                {"model":"runner_hunter","date":"2026-10-19","action":"SELL"},
                {"model":"diy_whale","date":"2026-10-19","action":"SELL"},
                {"model":"diy_whale","date":"2026-10-19","action":"SELL"},
            ]
            r=audit_paper_day(rows,"2026-10-19",root)["reconciliation"]
            self.assertEqual(r["status"],"mismatch_review_required")
            self.assertEqual(r["by_sleeve"]["diy_whale"]["campaign_completed_delta"],3)
            self.assertEqual(r["by_sleeve"]["diy_whale"]["daily_completed"],2)

if __name__=="__main__":
    unittest.main()
