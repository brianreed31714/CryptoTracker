"""Select the most recently completed Pacific calendar day for crypto review.

The 18:05 Pacific research task cannot certify a full *current* calendar day
because CryptoTracker runs 24/7. This selector never changes trader timing,
trading state, orders, notification settings, or Windows Task Scheduler.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")


def completed_pacific_day(now: datetime | None = None) -> str:
    if now is None:
        now = datetime.now(PACIFIC)
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("Completed-day selector requires a timezone-aware clock")
    return (now.astimezone(PACIFIC).date() - timedelta(days=1)).isoformat()


if __name__ == "__main__":
    print(completed_pacific_day())
