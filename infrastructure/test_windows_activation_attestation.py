"""Fail-closed offline tests of Windows source sync and activation attestation."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from infrastructure import windows_activation_attestation as attest

T0 = datetime(2026, 10, 19, 20, 0, tzinfo=timezone.utc)
COMMIT = "a" * 40


def good_snapshot(pid_base=500, started=None):
    started = started or T0 - timedelta(minutes=7)
    started = started.isoformat() if isinstance(started, datetime) else str(started)
    components = {}
    for i, component in enumerate(attest.REQUIRED_PROCESSES):
        components[component] = {
            "process": {"state": "OBSERVED", "pids": [pid_base + i],
                        "started_utc": started, "script": component + ".py"},
            "script_version": {"state": "MATCHED"},
        }
    components["smart_money"] = {"artifact": {"state": "HEALTHY", "age_seconds": 20}}
    return {"components": components}


class AttestationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_unmatched_or_dirty_code_cannot_claim_sync(self):
        snapshot = good_snapshot()
        for head, origin, clean in ((COMMIT, "b"*40, True), (COMMIT, COMMIT, False),
                                    ("", COMMIT, True)):
            state = attest.advance(self.root, {}, snapshot, head=head, upstream=origin,
                                   clean=clean, clock=T0)
            self.assertEqual(state["state"], "UNVERIFIED")
            self.assertFalse(state["code_synced"])
            self.assertFalse(state["processes_stable"])

    def test_duplicate_missing_and_old_version_never_verified(self):
        cases = []
        missing = good_snapshot()
        missing["components"]["trader"]["process"]["state"] = "UNKNOWN"
        cases.append(missing)
        duplicate = good_snapshot()
        duplicate["components"]["trader"]["process"]["pids"] = [1, 2]
        cases.append(duplicate)
        wrong = good_snapshot()
        wrong["components"]["dashboard"]["script_version"]["state"] = "MISMATCH"
        cases.append(wrong)
        unproven = good_snapshot()
        unproven["components"]["trader"]["process"].pop("started_utc")
        cases.append(unproven)
        for snapshot in cases:
            state = attest.advance(self.root, {}, snapshot, head=COMMIT,
                                   upstream=COMMIT, clean=True, clock=T0)
            self.assertEqual(state["state"], "CODE_SYNCED_RUNTIME_UNVERIFIED")
            self.assertFalse(state["processes_stable"])

    def test_three_distinct_time_separated_stable_process_samples(self):
        snapshot = good_snapshot()
        a = attest.advance(self.root, {}, snapshot, head=COMMIT, upstream=COMMIT,
                           clean=True, clock=T0)
        b = attest.advance(self.root, a, snapshot, head=COMMIT, upstream=COMMIT,
                           clean=True, clock=T0 + timedelta(seconds=10))
        self.assertEqual(b["consecutive_observations"], 1)
        c = attest.advance(self.root, b, snapshot, head=COMMIT, upstream=COMMIT,
                           clean=True, clock=T0 + timedelta(seconds=40))
        self.assertEqual(c["consecutive_observations"], 2)
        d = attest.advance(self.root, c, snapshot, head=COMMIT, upstream=COMMIT,
                           clean=True, clock=T0 + timedelta(seconds=80))
        self.assertEqual(d["consecutive_observations"], 3)
        self.assertEqual(d["state"], "HOST_PROCESSES_STABLE_SOURCE_ONLY")
        self.assertFalse(d["eod_execution_verified"])
        self.assertEqual(d["first_seen_at_utc"], T0.isoformat())

    def test_recycled_pid_start_time_resets(self):
        snapshot = good_snapshot()
        a = attest.advance(self.root, {}, snapshot, head=COMMIT, upstream=COMMIT,
                           clean=True, clock=T0)
        next_sample = good_snapshot(started=T0.isoformat())
        b = attest.advance(self.root, a, next_sample, head=COMMIT,
                           upstream=COMMIT, clean=True, clock=T0 + timedelta(seconds=60))
        self.assertEqual(b["consecutive_observations"], 1)

    def test_post_sync_crypto_eod_send_record(self):
        day = "2026-10-19"
        data = self.root / "data"
        data.mkdir()
        state = data / "crypto_eod_report_state.json"
        state.write_text(json.dumps({
            "last_sent_date": day,
            "sent_at": (T0 - timedelta(minutes=1)).isoformat(),
        }))
        before = attest.review_after_sync(self.root, T0.isoformat(),
                                          clock=T0+timedelta(minutes=2))
        self.assertEqual(before["state"], "NOT_VERIFIED")
        state.write_text(json.dumps({
            "last_sent_date": day,
            "sent_at": (T0 + timedelta(minutes=1)).isoformat(),
        }))
        valid = attest.review_after_sync(self.root, T0.isoformat(),
                                         clock=T0+timedelta(minutes=2))
        self.assertEqual(valid, {"state": "VERIFIED", "review_date": day})

    def test_crypto_eod_send_timestamp_or_day_mismatch(self):
        data = self.root / "data"
        data.mkdir()
        state = data / "crypto_eod_report_state.json"
        for payload in (
            {"last_sent_date": "2026-10-19", "sent_at": "invalid"},
            {"last_sent_date": "../../token", "sent_at": T0.isoformat()},
            {"last_sent_date": "2026-10-20", "sent_at": (T0 + timedelta(minutes=3)).isoformat()},
        ):
            state.write_text(json.dumps(payload))
            output = attest.review_after_sync(self.root, T0.isoformat(),
                                               clock=T0+timedelta(minutes=2))
            self.assertEqual(output["state"], "NOT_VERIFIED")

    def test_smart_money_heartbeat_required_even_when_process_hidden(self):
        observed = good_snapshot()
        observed["components"]["smart_money"]["process"] = {
            "state": "UNKNOWN", "pids": []}
        good = attest.advance(self.root, {}, observed, head=COMMIT,
                              upstream=COMMIT, clean=True, clock=T0)
        self.assertEqual(good["state"], "CODE_SYNCED_PROCESS_OBSERVED")
        observed["components"]["smart_money"]["artifact"]["state"] = "STALE"
        blocked = attest.advance(self.root, good, observed, head=COMMIT,
                                 upstream=COMMIT, clean=True,
                                 clock=T0+timedelta(minutes=1))
        self.assertEqual(blocked["state"], "CODE_SYNCED_RUNTIME_UNVERIFIED")
        self.assertIn("SMART_MONEY_HEARTBEAT_NOT_HEALTHY", blocked["reasons"])

    def test_notification_only_marks_success_when_api_accepts(self):
        called = []
        def accepted(title, body):
            called.append((title, body))
            return True
        with patch.object(attest, "git_head", return_value=COMMIT), \
             patch.object(attest, "_head", return_value=COMMIT), \
             patch.object(attest, "_code_clean", return_value=True):
            a = attest.poll(self.root, observation=good_snapshot(), clock=T0,
                            notify=accepted)
            b = attest.poll(self.root, observation=good_snapshot(),
                            clock=T0 + timedelta(seconds=60), notify=accepted)
        self.assertTrue(a["code_synced"])
        self.assertEqual(a["notification"], "API_ACCEPTED")
        self.assertEqual(len(called), 1)
        self.assertNotIn("EOD Verified", called[0][0])
        self.assertNotIn("pid", str(called).lower())
        self.assertEqual(b["notice_key"], a["notice_key"])

    def test_failed_notification_may_retry_without_spamming_success(self):
        attempts = []
        def flaky(*_):
            attempts.append(1)
            return len(attempts) == 2
        with patch.object(attest, "git_head", return_value=COMMIT), \
             patch.object(attest, "_head", return_value=COMMIT), \
             patch.object(attest, "_code_clean", return_value=True):
            first = attest.poll(self.root, observation=good_snapshot(),
                                clock=T0, notify=flaky)
            second = attest.poll(self.root, observation=good_snapshot(),
                                 clock=T0 + timedelta(seconds=60), notify=flaky)
            attest.poll(self.root, observation=good_snapshot(),
                        clock=T0 + timedelta(seconds=120), notify=flaky)
        self.assertEqual(first["notification"], "UNCONFIRMED")
        self.assertEqual(second["notification"], "API_ACCEPTED")
        self.assertEqual(len(attempts), 2)

    def test_agent_hook_is_windows_only_and_read_only(self):
        import inspect
        import deployment_agent as agent
        source = inspect.getsource(agent.scan_once)
        observer = inspect.getsource(agent._observe_host_read_only)
        self.assertIn("_observe_host_read_only()", source)
        self.assertIn('if os.name == "nt":', observer)
        self.assertIn("run_fresh_host_attestation(ROOT)", observer)
        self.assertNotIn("poll(ROOT, notify=push_attestation)", source + observer)
        self.assertNotIn("stop_active(", source + observer)


if __name__ == "__main__":
    unittest.main()
