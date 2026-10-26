"""Opt-in, read-only Jupiter V2 liquidation quote capture for paper positions.

This module is NOT scheduled or imported by the trader. It never sends a POST,
signs, executes, submits, or builds a transaction. Without a taker address the
Jupiter V2 GET /order endpoint is quote-only. It refuses returned transactions.
Private mint/amount snapshots stay in local data/paper_research, never published.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from research.paper_liquidation_mtm import FOCUS, QUOTE_STATUS, finite_number, positive_raw_amount

USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
ORDER_URL = "https://api.jup.ag/swap/v2/order"
MAX_CYCLE_AGE_SECONDS = 120
MINT_PATTERN = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
PACIFIC = ZoneInfo("America/Los_Angeles")


class CaptureRejected(ValueError):
    """Fail closed; never reveal wallet, mint, API key or provider body."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        # Never forward the API key to a redirected host.
        return None


def _read_only_get(params, headers, timeout):
    # Constant HTTPS destination, GET only. Never accept a wallet/taker param.
    url = ORDER_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers=headers, method="GET")
    opener = urllib.request.build_opener(_NoRedirect)
    with opener.open(request, timeout=timeout) as response:
        if response.status != 200:
            raise CaptureRejected("QUOTE_HTTP_NOT_SUCCESS")
        raw = response.read(65537)
    if len(raw) > 65536:
        raise CaptureRejected("QUOTE_RESPONSE_TOO_LARGE")
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise CaptureRejected("QUOTE_RESPONSE_INVALID_JSON") from exc


def _utc(clock):
    now = clock()
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise CaptureRejected("CLOCK_NOT_TIMEZONE_AWARE")
    return now.astimezone(timezone.utc)


def _cycle_is_recent(cycle, now, max_age):
    if not isinstance(cycle, str) or len(cycle) < 19:
        return False
    try:
        dt = datetime.fromisoformat(cycle.replace("Z", "+00:00"))
    except ValueError:
        return False
    if dt.tzinfo:
        candidates = [dt.astimezone(timezone.utc)]
    else:
        # Paper engine stores naive Pacific local cycle timestamps.
        # DST repeated hour is accepted only when one fold is fresh.
        candidates = [dt.replace(tzinfo=PACIFIC, fold=fold).astimezone(timezone.utc)
                      for fold in (0, 1)]
    return any(0 <= (now - observed).total_seconds() <= max_age
               for observed in candidates)


def _position_request(model):
    if not isinstance(model, dict):
        raise CaptureRejected("MODEL_STATE_MISSING")
    starting = finite_number(model.get("starting_equity"))
    realized = finite_number(model.get("realized_pnl"))
    if starting is None or starting <= 0 or realized is None:
        raise CaptureRejected("INVALID_EQUITY_LEDGER")
    equity = starting + realized
    if not math.isfinite(equity) or equity < 0:
        raise CaptureRejected("INVALID_EQUITY_LEDGER")
    position = model.get("position")
    if position is None:
        return None
    if not isinstance(position, dict):
        raise CaptureRejected("INVALID_POSITION_STATE")
    mint = position.get("token_address")
    raw = positive_raw_amount(position.get("entry_token_raw"))
    size = finite_number(position.get("size_usdc"))
    if not isinstance(mint, str) or not MINT_PATTERN.fullmatch(mint):
        raise CaptureRejected("INVALID_POSITION_MINT")
    if raw is None or size is None or not 0 < size <= equity:
        raise CaptureRejected("INVALID_POSITION_PROVENANCE")
    # Focus sleeves have no staged partial exits; reject unexpected fractional
    # state rather than silently quoting a full original token amount.
    if "remaining_fraction" in position and position["remaining_fraction"] != 1:
        raise CaptureRejected("PARTIAL_POSITION_UNSUPPORTED")
    return mint, raw


def _validate_quote(payload, mint, raw):
    if not isinstance(payload, dict):
        raise CaptureRejected("QUOTE_RESPONSE_INVALID")
    if payload.get("error") or payload.get("errorCode") or payload.get("errorMessage"):
        raise CaptureRejected("QUOTE_PROVIDER_REJECTED")
    if payload.get("transaction") not in (None, ""):
        raise CaptureRejected("QUOTE_UNEXPECTED_TRANSACTION")
    if payload.get("inputMint") not in (None, mint):
        raise CaptureRejected("QUOTE_INPUT_MINT_MISMATCH")
    if payload.get("outputMint") not in (None, USDC_MINT):
        raise CaptureRejected("QUOTE_OUTPUT_MINT_MISMATCH")
    if payload.get("inAmount") is not None and positive_raw_amount(payload["inAmount"]) != raw:
        raise CaptureRejected("QUOTE_INPUT_AMOUNT_MISMATCH")
    out_raw = positive_raw_amount(payload.get("outAmount"))
    if out_raw is None:
        raise CaptureRejected("QUOTE_OUTPUT_AMOUNT_INVALID")
    return out_raw / 1_000_000


def capture(state_path, output_path, *, api_key, enabled=False,
            http_get=None, clock=None, max_cycle_age_seconds=MAX_CYCLE_AGE_SECONDS):
    """Capture a complete single-state snapshot, or write nothing.

    A callable http_get(params, headers, timeout) allows offline CI tests.
    The caller must explicitly opt in; this is not a trading or scheduling API.
    """
    if not enabled:
        raise CaptureRejected("CAPTURE_NOT_OPTED_IN")
    if os.getenv("LIVE_TRADING", "false").strip().lower() not in ("0", "false", "no", "off"):
        raise CaptureRejected("LIVE_TRADING_MODE_REJECTED")
    if not isinstance(api_key, str) or not api_key.strip():
        raise CaptureRejected("JUPITER_API_KEY_MISSING")
    if max_cycle_age_seconds <= 0 or max_cycle_age_seconds > 120:
        raise CaptureRejected("INVALID_CYCLE_AGE_LIMIT")
    state_path, output_path = Path(state_path), Path(output_path)
    try:
        original = state_path.read_bytes()
        state = json.loads(original)
    except (OSError, ValueError) as exc:
        raise CaptureRejected("STATE_UNREADABLE") from exc
    if not isinstance(state, dict) or not isinstance(state.get("models"), dict):
        raise CaptureRejected("STATE_INVALID")
    cycle = state.get("last_cycle_at")
    now = _utc(clock or (lambda: datetime.now(timezone.utc)))
    if not _cycle_is_recent(cycle, now, max_cycle_age_seconds):
        raise CaptureRejected("STATE_CYCLE_STALE_OR_FUTURE")
    # Prevalidate *all* sleeves before issuing a single HTTP request.
    positions = {name: _position_request(state["models"].get(name)) for name in FOCUS}
    fetch = http_get or _read_only_get
    rows = []
    for name, held in positions.items():
        if held is None:
            continue
        mint, raw = held
        params = {"inputMint": mint, "outputMint": USDC_MINT, "amount": str(raw)}
        headers = {"x-api-key": api_key, "Accept": "application/json"}
        try:
            response = fetch(params, headers, 12)
        except CaptureRejected:
            raise
        except (OSError, ValueError, urllib.error.URLError) as exc:
            raise CaptureRejected("QUOTE_REQUEST_FAILED") from exc
        value = _validate_quote(response, mint, raw)
        observed = _utc(clock or (lambda: datetime.now(timezone.utc)))
        if not _cycle_is_recent(cycle, observed, max_cycle_age_seconds):
            raise CaptureRejected("STATE_CYCLE_EXPIRED_DURING_QUOTE")
        rows.append({
            "model": name, "token_address": mint, "entry_token_raw": raw,
            "exit_value_usdc": value, "observed_at_utc": observed.isoformat(),
            "status": QUOTE_STATUS,
        })
    # Protect against a race with the running paper trader. No old-state
    # quote snapshot can be attributed to a changed state.
    try:
        if state_path.read_bytes() != original:
            raise CaptureRejected("STATE_CHANGED_DURING_QUOTE")
    except OSError as exc:
        raise CaptureRejected("STATE_CHANGED_DURING_QUOTE") from exc
    if not _cycle_is_recent(cycle, _utc(clock or (lambda: datetime.now(timezone.utc))),
                            max_cycle_age_seconds):
        raise CaptureRejected("STATE_CYCLE_EXPIRED_BEFORE_WRITE")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Never write raw provider payloads, wallets, request IDs or API keys.
    result = {"state_last_cycle_at": cycle, "quotes": rows}
    fd, temp_name = tempfile.mkstemp(prefix=".paper_quotes_", dir=output_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(result, handle, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, output_path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return {"status": "LOCAL_READ_ONLY_QUOTE_SNAPSHOT", "open_positions_quoted": len(rows),
            "paper_only": True, "orders_submitted": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Opt-in, no-orders, paper-only Jupiter quote snapshot")
    parser.add_argument("--collect", action="store_true", help="Explicitly request a local quote snapshot")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1] / "data" / "paper_research"
    try:
        report = capture(root / "state.json", root / "liquidation_quotes.json",
                         api_key=os.getenv("JUPITER_API_KEY", ""),
                         enabled=args.collect and
                         os.getenv("PAPER_QUOTE_CAPTURE_ENABLED", "").strip() == "1")
    except CaptureRejected as exc:
        print("Paper quote capture unavailable: " + str(exc))
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
