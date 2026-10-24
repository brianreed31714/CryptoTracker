"""Deterministic, read-only checks for prospective shadow report integrity."""
import csv
import tempfile
import unittest
from pathlib import Path

from research.paper_shadow_experiments import generate, render_markdown, summarize

STUDY = "NOVELTY_FLOW_V1_20261022"


def row(model, action, mint, entered, mark="", *, day="2026-10-23", version=STUDY):
    return {
        "date": day,
        "timestamp": day + "T18:00:00",
        "model": model,
        "action": action,
        "symbol": "TEST",
        "token_address": mint,
        "entry_time": entered,
        "net_return_pct": mark,
        "novelty_study_version": version,
    }


def write_rows(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class ShadowObservationIntegrityTests(unittest.TestCase):
    def test_missing_source_never_means_zero_opportunities(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = summarize(Path(tmp) / "missing.csv", "2026-10-23")
            arm = report["variants"]["xp_diy_raunchy_flow"]
            self.assertFalse(report["source_present"])
            self.assertEqual(report["source_rows_observed"], 0)
            self.assertEqual(arm["row_observation_status"], "NO_ROWS_ACTIVATION_UNVERIFIED")
            self.assertEqual(arm["n_completed_since_first_observed"], 0)
            self.assertIsNone(arm["raw_mark_avg_return_per_exit_pct"])
            self.assertIsNone(arm["raw_mark_win_rate_pct"])
            self.assertFalse(arm["sample_qualified_for_preliminary_review"])
            self.assertFalse(report["host_runtime_activation_verified"])
            self.assertFalse(arm["promotable"])
            self.assertIn("not", render_markdown(report).lower())

    def test_missing_invalid_and_future_marks_are_not_zero_return_trades(self):
        model = "xp_diy_raunchy_flow"
        rows = [
            row(model, "BUY", "A", "2026-10-23T10:00:00"),
            row(model, "SELL", "A", "2026-10-23T10:00:00", "12.5"),
            row(model, "BUY", "B", "2026-10-23T11:00:00"),
            row(model, "SELL", "B", "2026-10-23T11:00:00", "nan"),
            row(model, "BUY", "C", "2026-10-23T12:00:00"),
            row(model, "SELL", "D", "2026-10-23T13:00:00", ""),
            row(model, "BUY", "FUTURE", "2026-10-24T10:00:00", day="2026-10-24"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "shadow.csv"
            write_rows(source, rows)
            report = summarize(source, "2026-10-23")
            arm = report["variants"][model]
            self.assertEqual(arm["n_entries_today"], 3)
            self.assertEqual(arm["n_completed_today"], 3)
            self.assertEqual(arm["n_valid_raw_mark_exits"], 1)
            self.assertEqual(arm["n_invalid_raw_mark_exits"], 2)
            self.assertEqual(arm["n_unclosed_observed_entries"], 1)
            self.assertEqual(arm["n_unmatched_exit_rows"], 1)
            self.assertEqual(arm["n_distinct_mints_closed"], 3)
            self.assertEqual(arm["raw_mark_avg_return_per_exit_pct"], 12.5)
            self.assertEqual(arm["raw_mark_win_rate_pct"], 100.0)
            self.assertEqual(arm["row_observation_status"], "SHADOW_ROWS_OBSERVED_NOT_RUNTIME_ATTESTATION")
            self.assertFalse(arm["sample_qualified_for_preliminary_review"])
            self.assertEqual(report["variants"]["xp_diy_name12"]["row_observation_status"],
                             "NO_ROWS_ACTIVATION_UNVERIFIED")
            generated = generate(source, "2026-10-23", tmp)
            self.assertEqual(generated["mode"], "NO_ORDERS_RAW_SHADOW_MARKS_ONLY")
            text = (Path(tmp) / "shadow_experiments.md").read_text(encoding="utf-8")
            self.assertIn("1/3", text)
            self.assertIn("UNPRICED", text)

    def test_missing_novelty_version_does_not_prove_activation(self):
        model = "xp_diy_name12"
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "shadow.csv"
            write_rows(source, [
                row(model, "BUY", "A", "2026-10-23T10:00:00", version=""),
                row(model, "SELL", "A", "2026-10-23T10:00:00", "2", version=""),
            ])
            arm = summarize(source, "2026-10-23")["variants"][model]
            self.assertEqual(arm["row_observation_status"], "MISSING_OR_MIXED_NOVELTY_VERSION_UNVERIFIED")
            self.assertFalse(arm["sample_qualified_for_preliminary_review"])

    def test_complete_30_exits_still_never_promotable(self):
        model = "xp_diy_organic_flow"
        rows = []
        for i in range(30):
            mint = "MINT" + str(i)
            entered = f"2026-10-23T12:{i:02d}:00"
            rows.extend([row(model, "BUY", mint, entered),
                         row(model, "SELL", mint, entered, "-1" if i % 2 else "2")])
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "shadow.csv"
            write_rows(source, rows)
            arm = summarize(source, "2026-10-23")["variants"][model]
            self.assertTrue(arm["sample_qualified_for_preliminary_review"])
            self.assertFalse(arm["promotable"])
            self.assertEqual(arm["n_negative_raw_mark_exits"], 15)
            self.assertEqual(arm["raw_mark_win_rate_pct"], 50)
            self.assertEqual(arm["raw_mark_avg_return_per_exit_pct"], 0.5)


if __name__ == "__main__":
    unittest.main()
