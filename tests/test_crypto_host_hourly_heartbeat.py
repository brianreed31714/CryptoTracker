"""Non-disruptive CryptoTracker GitHub host-status heartbeat regression."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from infrastructure import windows_activation_attestation as att


def test_unchanged_host_status_republishes_after_one_hour(tmp_path):
    head = "a" * 40
    start = datetime(2026, 10, 28, 20, 0, tzinfo=timezone.utc)
    publishes = []

    def report(*args, **kwargs):
        return {
            "observed_at_utc": kwargs["clock"].isoformat(),
            "git_head": head,
            "state": "HOST_PROCESSES_STABLE_SOURCE_ONLY",
            "code_synced": True,
            "processes_stable": True,
            "eod_execution_verified": False,
            "consecutive_observations": 3,
            "reasons": [],
            "notice_key": "",
            "notification": "UNCONFIRMED",
        }

    def publish(root, payload):
        publishes.append(payload["observed_at_utc"])
        return "b" * 40

    with (
        patch.object(att, "git_head", return_value=head),
        patch.object(att, "_head", return_value=head),
        patch.object(att, "_code_clean", return_value=True),
        patch.object(att, "advance", side_effect=report),
    ):
        for offset in (0, 30, 61):
            att.poll(
                tmp_path, observation={}, clock=start + timedelta(minutes=offset),
                remote_publish=publish,
            )

    assert att.REMOTE_HEARTBEAT_SECONDS == 60 * 60
    assert len(publishes) == 2
    assert publishes[0] == start.isoformat()
    assert publishes[1] == (start + timedelta(minutes=61)).isoformat()
