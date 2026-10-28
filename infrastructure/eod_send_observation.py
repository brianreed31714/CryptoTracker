"""Read-only observation of the CryptoTracker local EOD send-state claim.

A local state file is NOT an independent Pushover provider receipt or device
delivery confirmation. Never publish raw state, user keys, tokens or message text.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


def inspect_local_eod_send(root: Path, *, now: datetime) -> dict:
    missing = {"status": "MISSING_OR_INVALID", "provider_delivery_verified": False}
    if now.tzinfo is None:
        raise ValueError("now must be timezone aware")
    try:
        state = json.loads((Path(root) / "data" / "crypto_eod_report_state.json").read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            return missing
        day = str(state.get("last_sent_date") or "")
        # date.fromisoformat accepts some noncanonical strings; require exact YYYY-MM-DD.
        from datetime import date
        if len(day) != 10 or date.fromisoformat(day).isoformat() != day:
            return missing
        sent = datetime.fromisoformat(str(state.get("sent_at") or "").replace("Z", "+00:00"))
        if sent.tzinfo is None or sent > now or sent.astimezone(ZoneInfo("America/Los_Angeles")).date().isoformat() != day:
            return missing
        return {
            "status": "HOST_LOCAL_SEND_STATE_CLAIM",
            "review_date": day,
            "sent_at_utc": sent.astimezone(timezone.utc).isoformat(),
            "provider_delivery_verified": False,
        }
    except (OSError, ValueError, TypeError, OverflowError):
        return missing
