"""Persistent, fail-closed credit reservations shared by the current services.

Reservations are estimates, not Helius billing records. Reserve before every
attempt, including retries; never refund uncertain/failed requests. No keys,
URLs, wallets or payloads are written to usage rows. Cached provider responses
remain private local data in the same ignored database.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from dotenv import dotenv_values


class HeliusBudgetDenied(RuntimeError):
    pass


# Explicit allowlist: an unfamiliar method must not silently cost one credit.
COSTS = {
    "getTokenAccounts": 10,
    "getTokenSupply": 1,
    "getTokenAccountsByOwner": 1,
    "getBalance": 1,
    "getSignatureStatuses": 1,
    "getTransaction": 1,
    "getSignaturesForAddress": 1,
    "enhanced_history": 100,
}
DEFAULTS = {
    "HELIUS_CREDITS_PER_HOUR": 1000,
    "HELIUS_CREDITS_PER_DAY": 20000,
    "HELIUS_CREDITS_PER_31_DAYS": 600000,
    "HOLDER_METRICS_CACHE_SECONDS": 21600,
    "HOLDER_METRICS_MAX_PAGES": 2,
    "SMART_MONEY_HELIUS_CACHE_SECONDS": 3600,
    "HELIUS_FAILURE_COOLDOWN_SECONDS": 900,
}


class HeliusUsage:
    def __init__(self, root=None, clock=time.time):
        self.root = Path(root) if root is not None else Path(__file__).resolve().parent
        self.path = self.root / "data" / "helius_usage.sqlite3"
        self.clock = clock

    def policy(self):
        # Read tracked policy directly: stale .env/process settings cannot raise caps.
        try:
            config = dotenv_values(self.root / ".env.config", interpolate=False)
            if config.get("HELIUS_ENABLED") != "1":
                raise HeliusBudgetDenied("HELIUS_DISABLED")
            values = {k: int(config.get(k, v)) for k, v in DEFAULTS.items()}
            if any(v <= 0 for v in values.values()):
                raise ValueError("limits must be positive")
            return values
        except HeliusBudgetDenied:
            raise
        except Exception:
            raise HeliusBudgetDenied("HELIUS_INVALID_POLICY") from None

    def _connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        try:
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("CREATE TABLE IF NOT EXISTS usage (at REAL NOT NULL, method TEXT NOT NULL, credits INTEGER NOT NULL)")
            conn.execute("CREATE INDEX IF NOT EXISTS usage_at ON usage(at)")
            conn.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT, fetched REAL NOT NULL DEFAULT 0, retry_after REAL NOT NULL DEFAULT 0)")
            return conn
        except Exception:
            conn.close()
            raise

    def reserve(self, method):
        policy = self.policy()
        if method not in COSTS:
            raise HeliusBudgetDenied("HELIUS_UNPRICED_METHOD")
        now, cost = self.clock(), COSTS[method]
        try:
            with closing(self._connect()) as conn:
                conn.execute("BEGIN IMMEDIATE")
                halt = conn.execute("SELECT retry_after FROM cache WHERE key='provider_halt'").fetchone()
                if halt and now < halt[0]:
                    raise HeliusBudgetDenied("HELIUS_PROVIDER_HALTED")
                for seconds, key in ((3600, "HELIUS_CREDITS_PER_HOUR"),
                                     (86400, "HELIUS_CREDITS_PER_DAY"),
                                     (31 * 86400, "HELIUS_CREDITS_PER_31_DAYS")):
                    spent = conn.execute("SELECT COALESCE(SUM(credits),0) FROM usage WHERE at > ?", (now - seconds,)).fetchone()[0]
                    if spent + cost > policy[key]:
                        raise HeliusBudgetDenied(f"HELIUS_BUDGET_EXHAUSTED: {key}")
                conn.execute("INSERT INTO usage VALUES (?,?,?)", (now, method, cost))
                conn.execute("DELETE FROM usage WHERE at <= ?", (now - 31 * 86400,))
                conn.execute("COMMIT")
        except HeliusBudgetDenied:
            raise
        except Exception:
            raise HeliusBudgetDenied("HELIUS_LEDGER_UNAVAILABLE") from None

    def halt(self, seconds=86400):
        """Persist a provider-wide outage across process restarts."""
        try:
            with closing(self._connect()) as conn:
                conn.execute("INSERT INTO cache(key,retry_after) VALUES ('provider_halt',?) ON CONFLICT(key) DO UPDATE SET retry_after=MAX(retry_after,excluded.retry_after)",
                             (self.clock() + seconds,))
        except Exception:
            raise HeliusBudgetDenied("HELIUS_LEDGER_UNAVAILABLE") from None

    def cached(self, resource, ttl, fetch):
        """Persist results and failure cooldowns; coalesce simultaneous refreshes.

        Cache hits do not reserve credits. The fetch callback must reserve each
        actual HTTP attempt. Failures never return stale data as a fresh sample.
        """
        policy = self.policy()
        now = self.clock()
        key = hashlib.sha256(resource.encode()).hexdigest()
        try:
            with closing(self._connect()) as conn:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute("SELECT value,fetched,retry_after FROM cache WHERE key=?", (key,)).fetchone()
                if row and row[0] is not None and 0 <= now - row[1] < ttl:
                    conn.execute("COMMIT")
                    return json.loads(row[0])
                if row and now < row[2]:
                    raise HeliusBudgetDenied("HELIUS_REFRESH_COOLDOWN")
                # A crashed worker leaves a cooldown rather than a restart storm.
                conn.execute("INSERT INTO cache(key,retry_after) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET retry_after=excluded.retry_after",
                             (key, now + policy["HELIUS_FAILURE_COOLDOWN_SECONDS"]))
                conn.execute("COMMIT")
            value = fetch()
            with closing(self._connect()) as conn:
                conn.execute("UPDATE cache SET value=?,fetched=?,retry_after=0 WHERE key=?",
                             (json.dumps(value), self.clock(), key))
            return value
        except HeliusBudgetDenied:
            raise
        except Exception:
            # Provider exceptions can contain API keys in their URLs.
            raise HeliusBudgetDenied("HELIUS_REFRESH_FAILED; cooldown active") from None

    def summary(self):
        """Local estimated usage; no provider calls or secret configuration reads."""
        now = self.clock()
        with closing(self._connect()) as conn:
            return {label: dict(conn.execute(
                "SELECT method,SUM(credits) FROM usage WHERE at > ? GROUP BY method", (now - seconds,)))
                for label, seconds in (("hour", 3600), ("day", 86400), ("rolling_31_days", 31 * 86400))}


if __name__ == "__main__":
    print(json.dumps(HeliusUsage().summary(), indent=2))
