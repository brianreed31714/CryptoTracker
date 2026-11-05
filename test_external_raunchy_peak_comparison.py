import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from research.external_raunchy_peak_comparison import analyze


def call(symbol, mint, day, peak, mc=12000):
    return {"sym": symbol, "mint": mint, "t": int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()), "peak": peak, "mc": mc}


class TestExternalPeakComparison(unittest.TestCase):
    def test_frozen_classifier_calendar_split_and_no_roi(self):
        rows = [call("FARTCOIN", "a", "2026-07-10", 3),
                call("CUM", "b", "2026-08-10", 1.2),
                call("SAFE", "c", "2026-07-10", 2.5),
                call("NORMAL", "d", "2026-08-10", 1.1),
                call("PORN", "e", "2026-09-10", 1.5),
                call("SAFE2", "f", "2026-09-10", 3),
                call("SAFE2", "f", "2026-09-10", 3)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calls.jsonl"
            path.write_text("\n".join(json.dumps(x) for x in rows) + "\n")
            result = analyze(path)
        self.assertEqual(result["source_rows"], 7)
        self.assertEqual(result["unique_window_mints"], 6)
        self.assertEqual(result["overall"]["raunchy_ticker"]["n"], 3)
        self.assertEqual(result["overall"]["raunchy_ticker"]["future_peak_at_least_2x"], 1)
        self.assertEqual(result["chronological_calendar_slices"]["sep_oct_later_calendar_slice"]["raunchy_ticker"]["n"], 1)
        self.assertIsNone(result["executable_net_roi_pct"])
        self.assertIsNone(result["portfolio_drawdown_pct"])
        self.assertFalse(result["promotable"])

    def test_invalid_peak_does_not_become_zero_or_false_loss(self):
        rows = [call("FART", "a", "2026-07-10", None),
                call("SAFE", "b", "2026-07-10", 3)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calls.jsonl"
            path.write_text("\n".join(json.dumps(x) for x in rows) + "\n")
            result = analyze(path)
        self.assertEqual(result["overall"]["raunchy_ticker"]["n"], 1)
        self.assertEqual(result["overall"]["raunchy_ticker"]["valid_peak_observations"], 0)
        self.assertIsNone(result["overall"]["raunchy_ticker"]["future_peak_at_least_2x_pct"])
        self.assertIsNone(result["overall"]["difference_percentage_points"])


if __name__ == "__main__":
    unittest.main()
