"""Fail-closed, read-only CryptoTracker EOD publication evidence gate.

This does not infer that an absent report means zero trades or host outage.\nLocal send-state timestamps and host EOD claims do not independently prove\nprovider acceptance or device delivery; never label them VERIFIED.
No credentials, process actions, notifications, or trading side effects.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

DAY = re.compile(r"^20\d{2}-\d{2}-\d{2}$")
STATES = {"VERIFIED", "MISSING", "UNVERIFIED"}


def evaluate(*, review_date: str, send_state: dict | None,
             host_status: dict | None, now: datetime) -> dict:
    if not DAY.fullmatch(review_date) or date.fromisoformat(review_date).isoformat() != review_date:
        raise ValueError("Invalid review date")
    if now.tzinfo is None:
        raise ValueError("Clock must be timezone aware")
    sent = send_state if isinstance(send_state, dict) else {}
    host = host_status if isinstance(host_status, dict) else {}
    result = {
        "schema": "cryptotracker_eod_evidence_gate_v1",
        "review_date": review_date,
        "observed_at_utc": now.astimezone(timezone.utc).isoformat(),
        "send_receipt": "MISSING",
        "host_eod": "UNVERIFIED",
        "overall": "UNVERIFIED",
        "reasons": [],
    }
    if sent.get("last_sent_date") == review_date:
        try:
            timestamp = datetime.fromisoformat(str(sent.get("sent_at", "")).replace("Z", "+00:00"))
            if timestamp.tzinfo is None or timestamp > now or timestamp.date().isoformat() < review_date:
                raise ValueError("Invalid send timestamp")
            result["send_receipt"] = "LOCAL_STATE_MATCHED_UNCORROBORATED"
        except ValueError:
            result["reasons"].append("SEND_TIMESTAMP_INVALID")
    else:
        result["reasons"].append("SEND_RECEIPT_NOT_FOUND_FOR_DATE")
    if host.get("post_sync_eod_verified") is True and host.get("verified_review_date") == review_date:
        result["host_eod"] = "HOST_CLAIM_ONLY"
    else:
        result["reasons"].append("HOST_POST_SYNC_EOD_NOT_VERIFIED")
    if (result["send_receipt"] == "LOCAL_STATE_MATCHED_UNCORROBORATED" and
            result["host_eod"] == "HOST_CLAIM_ONLY"):
        result["overall"] = "CLAIMS_COMPLETE_UNCORROBORATED"
    return result


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--send-state", type=Path, default=Path("data/crypto_eod_report_state.json"))
    parser.add_argument("--host-status", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(review_date=args.date, send_state=read_json(args.send_state),
                      host_status=read_json(args.host_status), now=datetime.now(timezone.utc))
    print(json.dumps(result, sort_keys=True))
    return 2  # Provider/device receipt not independently corroborated.


if __name__ == "__main__":
    raise SystemExit(main())
