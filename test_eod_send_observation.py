import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.eod_send_observation import inspect_local_eod_send
from infrastructure.host_status_publisher import sanitized

NOW = datetime(2026, 10, 28, 4, 30, tzinfo=timezone.utc)
HEAD = "a" * 40


class EodSendObservationTests(unittest.TestCase):
    def observe(self, payload=None):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            if payload is not None:
                (root / "data").mkdir()
                (root / "data" / "crypto_eod_report_state.json").write_text(json.dumps(payload))
            return inspect_local_eod_send(root, now=NOW)

    def test_missing_is_not_a_verified_send(self):
        self.assertEqual(self.observe()["status"], "MISSING_OR_INVALID")

    def test_valid_local_state_is_only_a_claim(self):
        value = self.observe({"last_sent_date": "2026-10-27",
                              "sent_at": "2026-10-27T20:01:00-07:00",
                              "manual_once_key": "irrelevant"})
        self.assertEqual(value["status"], "HOST_LOCAL_SEND_STATE_CLAIM")
        self.assertFalse(value["provider_delivery_verified"])
        self.assertEqual(value["sent_at_utc"], "2026-10-28T03:01:00+00:00")

    def test_future_or_wrong_date_fails_closed(self):
        self.assertEqual(self.observe({"last_sent_date": "2026-10-27",
                          "sent_at": "2026-10-28T05:00:00Z"})["status"], "MISSING_OR_INVALID")
        self.assertEqual(self.observe({"last_sent_date": "2026-10-26",
                          "sent_at": "2026-10-27T20:01:00-07:00"})["status"], "MISSING_OR_INVALID")

    def test_host_status_whitelists_claim_without_secrets(self):
        report = {"state": "HOST_PROCESSES_STABLE_SOURCE_ONLY",
                  "git_head": HEAD, "observed_at_utc": NOW.isoformat(),
                  "code_synced": True, "processes_stable": True,
                  "eod_execution_verified": False,
                  "local_eod_send_observation": {
                      "status": "HOST_LOCAL_SEND_STATE_CLAIM",
                      "review_date": "2026-10-27",
                      "sent_at_utc": "2026-10-28T03:01:00+00:00",
                      "secret": "do-not-publish",
                  }}
        result = sanitized(report)
        self.assertEqual(result["local_eod_send_state"], "HOST_LOCAL_CLAIM_ONLY")
        self.assertEqual(result["local_eod_send_date"], "2026-10-27")
        self.assertFalse(result["eod_device_delivery_verified"])
        self.assertNotIn("secret", json.dumps(result))
        self.assertFalse(result["post_sync_eod_verified"])

    def test_forged_future_claim_is_rejected(self):
        report = {"state": "HOST_PROCESSES_STABLE_SOURCE_ONLY",
                  "git_head": HEAD, "observed_at_utc": NOW.isoformat(),
                  "code_synced": True, "processes_stable": True,
                  "eod_execution_verified": False,
                  "local_eod_send_observation": {
                      "status": "HOST_LOCAL_SEND_STATE_CLAIM",
                      "review_date": "2026-10-27",
                      "sent_at_utc": "2026-10-28T05:01:00+00:00"}}
        result = sanitized(report)
        self.assertEqual(result["local_eod_send_state"], "MISSING_OR_INVALID")
        self.assertNotIn("local_eod_send_date", result)


if __name__ == "__main__":
    unittest.main()
