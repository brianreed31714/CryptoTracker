import unittest
from research.shadow_activation_provenance import ARMS, assess_arm, assess_all

D = "a" * 64
E = "b" * 64


class ShadowProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.a = {"independently_observed": True, "loaded_code_digest": D,
                  "loaded_dependency_digest": E, "activation_id": "host-1",
                  "activated_at_utc": "2026-10-27T18:00:00Z"}
        self.exit = {"arm": ARMS[0], "event": "EXIT",
                     "entered_at_utc": "2026-10-27T18:30:00Z",
                     "exited_at_utc": "2026-10-27T19:00:00Z",
                     "loaded_code_digest": D, "loaded_dependency_digest": E,
                     "activation_id": "host-1", "trade_id": "t1"}

    def run_gate(self, activation=None, trades=None, quotes=None):
        return assess_arm(ARMS[0], self.a if activation is None else activation,
                          [self.exit] if trades is None else trades,
                          [] if quotes is None else quotes,
                          as_of="2026-10-27T20:00:00Z")

    def test_source_only_does_not_verify_runtime(self):
        self.assertEqual(self.run_gate({"git_head": "f" * 40})["runtime"], "UNVERIFIED")

    def test_all_six_fail_closed_without_host_evidence(self):
        rows = assess_all({}, [], [], as_of="2026-10-27T20:00:00Z")
        self.assertEqual(set(rows), set(ARMS))
        self.assertTrue(all(x["runtime"] == "UNVERIFIED" for x in rows.values()))

    def test_trade_version_and_activation_match(self):
        self.assertEqual(self.run_gate()["trade_provenance"], "HOST_CLAIM_ONLY")
        self.assertEqual(self.run_gate()["runtime"], "UNVERIFIED")
        self.assertIn("INDEPENDENT_ATTESTATION_VALIDATOR_NOT_CONNECTED", self.run_gate()["reasons"])
        self.assertEqual(self.run_gate()["executable_net"], "MISSING")

    def test_stale_trade_not_counted(self):
        old = {**self.exit, "exited_at_utc": "2026-10-26T19:00:00Z"}
        self.assertEqual(self.run_gate(trades=[old])["valid_post_activation_exits"], 0)

    def test_wrong_digest_not_counted(self):
        bad = {**self.exit, "loaded_code_digest": E}
        self.assertEqual(self.run_gate(trades=[bad])["trade_provenance"], "MISSING")

    def test_self_asserted_quote_flags_do_not_verify_executable_net(self):
        q = self.good_quote()
        report = self.run_gate(quotes=[q])
        self.assertEqual(report["quote_evidence"], "HOST_CLAIM_ONLY")
        self.assertEqual(report["executable_net"], "MISSING")
        self.assertIn("INDEPENDENT_QUOTE_AND_COST_VALIDATOR_NOT_CONNECTED", report["reasons"])

    @staticmethod
    def good_quote():
        return {"trade_id": "t1", "independent_entry_quote_verified": True,
                "independent_exit_quote_verified": True,
                "priority_fees_verified": True, "slippage_modeled": True,
                "entry_quote_at_utc": "2026-10-27T18:29:45Z",
                "exit_quote_at_utc": "2026-10-27T18:59:50Z"}

    def test_missing_quote_timestamps_fail_closed(self):
        q = self.good_quote()
        q.pop("exit_quote_at_utc")
        self.assertEqual(self.run_gate(quotes=[q])["quote_evidence"], "MISSING")

    def test_stale_and_future_quotes_fail_closed(self):
        for timestamp in ("2026-10-27T18:58:00Z",
                          "2026-10-27T19:00:01Z"):
            q = {**self.good_quote(), "exit_quote_at_utc": timestamp}
            self.assertEqual(self.run_gate(quotes=[q])["quote_evidence"], "MISSING")

    def test_duplicate_trade_quote_fails_closed(self):
        q = self.good_quote()
        self.assertEqual(self.run_gate(quotes=[q, q])["quote_evidence"], "MISSING")

    def test_quote_before_activation_fails_closed_even_when_fresh(self):
        near_activation = {**self.exit, "entered_at_utc": "2026-10-27T18:00:10Z"}
        q = {**self.good_quote(), "entry_quote_at_utc": "2026-10-27T17:59:55Z"}
        report = self.run_gate(trades=[near_activation], quotes=[q])
        self.assertEqual(report["quote_evidence"], "MISSING")
        self.assertEqual(report["executable_net"], "MISSING")

    def test_pre_activation_entry_with_post_activation_exit_is_excluded(self):
        old_entry = {**self.exit, "entered_at_utc": "2026-10-27T17:59:59Z"}
        report = self.run_gate(trades=[old_entry])
        self.assertEqual(report["valid_post_activation_exits"], 0)
        self.assertEqual(report["trade_provenance"], "MISSING")

    def test_exit_before_entry_is_excluded(self):
        backwards = {**self.exit, "entered_at_utc": "2026-10-27T19:00:01Z"}
        self.assertEqual(self.run_gate(trades=[backwards])["valid_post_activation_exits"], 0)

    def test_duplicate_trade_ids_cannot_inflate_sample(self):
        duplicated = [{**self.exit, "trade_id": "t1"} for _ in range(30)]
        report = self.run_gate(trades=duplicated)
        self.assertEqual(report["valid_post_activation_exits"], 0)
        self.assertEqual(report["trade_provenance"], "MISSING")
        self.assertIn("DUPLICATE_TRADE_IDS_EXCLUDED", report["reasons"])
        self.assertNotIn("SAMPLE_THRESHOLD_MET_BUT_RUNTIME_UNVERIFIED", report["reasons"])

    def test_missing_or_non_string_trade_ids_are_excluded(self):
        for bad_id in (None, "", " ", {"id": "t1"}):
            row = {**self.exit, "trade_id": bad_id}
            self.assertEqual(self.run_gate(trades=[row])["valid_post_activation_exits"], 0)

    def test_thirty_host_claimed_exits_do_not_verify_sample(self):
        trades = [{**self.exit, "trade_id": f"t{i}"} for i in range(30)]
        report = self.run_gate(trades=trades)
        self.assertEqual(report["valid_post_activation_exits"], 30)
        self.assertEqual(report["preliminary_sample"], "UNVERIFIED")
        self.assertIn("SAMPLE_THRESHOLD_MET_BUT_RUNTIME_UNVERIFIED", report["reasons"])


if __name__ == "__main__":
    unittest.main()
