import unittest
from datetime import datetime, timezone

from infrastructure.eod_evidence_gate import evaluate


class EodEvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 27, 23, 0, tzinfo=timezone.utc)
        self.day = "2026-10-27"
        self.send = {"last_sent_date": self.day, "sent_at": "2026-10-27T22:00:00+00:00"}
        self.host = {"post_sync_eod_verified": True, "verified_review_date": self.day}

    def test_matching_local_claims_are_not_independent_verification(self):
        self.assertEqual(evaluate(review_date=self.day, send_state=self.send,
                                  host_status=self.host, now=self.now)["overall"], "CLAIMS_COMPLETE_UNCORROBORATED")

    def test_missing_send_is_not_zero_activity(self):
        result = evaluate(review_date=self.day, send_state={}, host_status=self.host, now=self.now)
        self.assertEqual(result["overall"], "UNVERIFIED")
        self.assertEqual(result["send_receipt"], "MISSING")

    def test_source_only_host_fails_closed(self):
        result = evaluate(review_date=self.day, send_state=self.send,
                          host_status={"post_sync_eod_verified": False}, now=self.now)
        self.assertEqual(result["overall"], "UNVERIFIED")

    def test_wrong_date_fails_closed(self):
        result = evaluate(review_date=self.day, send_state=self.send,
                          host_status={"post_sync_eod_verified": True,
                                       "verified_review_date": "2026-10-26"}, now=self.now)
        self.assertEqual(result["overall"], "UNVERIFIED")

    def test_future_send_rejected(self):
        sent = {**self.send, "sent_at": "2026-10-28T00:00:00+00:00"}
        self.assertEqual(evaluate(review_date=self.day, send_state=sent,
                                  host_status=self.host, now=self.now)["overall"], "UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
