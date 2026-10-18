"""Read-only Smart Money v2.3 dashboard health classification.

Windows may hide Python process command lines for scheduled-task children.
A recent, internally consistent feed-health heartbeat is stronger evidence
of wallet monitoring than a command-line substring.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import time


def smart_money_status(path: Path, *, now_epoch: float | None = None,
                       stale_after_seconds: int = 360) -> dict | None:
    """Return a display status, or None when v2.3 has not produced any report.

    Does not assert the process is currently alive: RUNNING here means the
    monitor successfully completed a recent wallet-check cycle.
    """
    path = Path(path)
    if not path.exists():
        return None
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(report, dict):
            raise ValueError("Health report is not an object")
        observed = datetime.fromisoformat(str(report["observed_at_utc"]).replace("Z", "+00:00"))
        if observed.tzinfo is None:
            raise ValueError("Health timestamp is missing timezone")
        age = (time.time() if now_epoch is None else now_epoch) - observed.timestamp()
        tracked = int(report["tracked_wallets"])
        successful = int(report["successful_wallet_checks"])
        failed = int(report["failed_wallet_checks"])
        status = str(report["status"]).upper()
        cycle = int(report["cycle_number"])
        if tracked <= 0 or successful < 0 or failed < 0 or successful + failed != tracked:
            raise ValueError("Inconsistent wallet coverage")
        if cycle < 1 or status not in {"OK", "DEGRADED", "ERROR"}:
            raise ValueError("Invalid cycle or status")
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        return {"state": "UNKNOWN", "css": "stop",
                "detail": "v2.3 health report unreadable", "last_error": ""}

    age_text = f"{max(0, age) / 60:.1f}m ago"
    detail = f"v2.3 | {successful}/{tracked} wallets | {age_text}"
    last_error = str(report.get("last_error") or "")

    if age < -60:
        return {"state": "CLOCK SKEW", "css": "stop",
                "detail": "v2.3 health timestamp is in the future", "last_error": last_error}
    if age > stale_after_seconds:
        return {"state": "STALE", "css": "stop",
                "detail": detail, "last_error": last_error}
    if status == "OK" and successful == tracked and failed == 0:
        return {"state": "RUNNING", "css": "run",
                "detail": detail, "last_error": last_error}
    if status == "DEGRADED" and successful > 0 and failed > 0:
        return {"state": "DEGRADED", "css": "warn",
                "detail": detail, "last_error": last_error}
    if status == "ERROR" and successful == 0 and failed > 0:
        return {"state": "ERROR", "css": "stop",
                "detail": detail, "last_error": last_error}
    return {"state": "UNKNOWN", "css": "stop",
            "detail": "v2.3 inconsistent feed status", "last_error": last_error}
