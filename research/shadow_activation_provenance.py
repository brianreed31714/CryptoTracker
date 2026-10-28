"""Fail-closed provenance gate for six DIY shadow research arms.

Read-only evidence assessment; never establishes in-memory activation merely
from a Git revision, local source hash, or published trade CSV.
"""
from __future__ import annotations

from datetime import datetime, timezone

ARMS = ("xp_diy_control", "xp_diy_name12", "xp_diy_organic_flow",
        "xp_diy_name12_flow", "xp_diy_raunchy", "xp_diy_raunchy_flow")


def _utc(value):
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except (ValueError, TypeError):
        return None


def assess_arm(arm: str, activation: dict | None, trades: list[dict],
               quotes: list[dict], *, as_of: str) -> dict:
    if arm not in ARMS:
        raise ValueError("Unknown pre-registered arm")
    report = {"arm": arm, "runtime": "UNVERIFIED", "trade_provenance": "MISSING",
              "executable_net": "MISSING", "quote_evidence": "MISSING",
              "preliminary_sample": "UNVERIFIED",
              "valid_post_activation_exits": 0, "reasons": []}
    a = activation if isinstance(activation, dict) else {}
    stamp = _utc(a.get("activated_at_utc"))
    now = _utc(as_of)
    if now is None:
        raise ValueError("Invalid as_of timestamp")
    # This read-only evaluator cannot independently validate a host signature.
    # Treat even a structurally complete host claim as UNVERIFIED until an
    # external attestation verifier is integrated. Git/disk hashes alone
    # cannot establish loaded trader code or dependencies.
    loaded = a.get("loaded_code_digest")
    deps = a.get("loaded_dependency_digest")
    if not (a.get("independently_observed") is True and
            isinstance(loaded, str) and len(loaded) == 64 and
            isinstance(deps, str) and len(deps) == 64 and
            all(c in "0123456789abcdef" for c in loaded + deps) and
            stamp is not None and stamp <= now):
        report["reasons"].append("LOADED_RUNTIME_PROVENANCE_UNVERIFIED")
        return report
    report["runtime"] = "UNVERIFIED"
    report["reasons"].append("INDEPENDENT_ATTESTATION_VALIDATOR_NOT_CONNECTED")
    matching = []
    for row in trades:
        if not isinstance(row, dict) or row.get("arm") != arm or row.get("event") != "EXIT":
            continue
        entry = _utc(row.get("entered_at_utc"))
        when = _utc(row.get("exited_at_utc"))
        trade_id = row.get("trade_id")
        if (entry is not None and when is not None and
                stamp <= entry <= when <= now and
                isinstance(trade_id, str) and bool(trade_id.strip()) and
                row.get("loaded_code_digest") == loaded and
                row.get("loaded_dependency_digest") == deps and
                row.get("activation_id") == a.get("activation_id") and
                a.get("activation_id")):
            matching.append(row)
    # Never inflate the sample with repeated EXIT records for one trade.
    # Reject every conflicting duplicate rather than trusting the first row.
    counts = {}
    for row in matching:
        trade_id = row["trade_id"]
        counts[trade_id] = counts.get(trade_id, 0) + 1
    if any(count > 1 for count in counts.values()):
        report["reasons"].append("DUPLICATE_TRADE_IDS_EXCLUDED")
        matching = [row for row in matching if counts[row["trade_id"]] == 1]
    report["valid_post_activation_exits"] = len(matching)
    if not matching:
        report["reasons"].append("NO_VERSION_MATCHED_POST_ACTIVATION_EXITS")
        return report
    report["trade_provenance"] = "HOST_CLAIM_ONLY"
    if len(matching) >= 30:
        report["reasons"].append("SAMPLE_THRESHOLD_MET_BUT_RUNTIME_UNVERIFIED")
    # Quotes must be independent timestamp-matched entry AND exit executable
    # observations; a raw mark or a historical spot price is not a fill quote.
    # Require pre-trade/pre-exit quotes, not future information or undated
    # flags. Thirty seconds is a research freshness contract, not a live
    # trading threshold. Self-asserted quote flags are not independent
    # validation of quote provenance, fee economics, or executable net P/L.
    quote_by_trade = {}
    duplicates = set()
    for q in quotes:
        if not isinstance(q, dict):
            continue
        key = q.get("trade_id")
        # Malformed, unhashable IDs must never crash an EOD research audit.
        if not isinstance(key, str) or not key.strip():
            continue
        if key in quote_by_trade:
            duplicates.add(key)
        quote_by_trade[key] = q

    def matched_quote(t):
        trade_id = t.get("trade_id")
        if not trade_id or trade_id in duplicates:
            return False
        q = quote_by_trade.get(trade_id)
        # A quote for another arm, activation, or loaded version cannot
        # substantiate this trade, even as an unverified host claim.
        if (not q or q.get("arm") != arm or
                q.get("activation_id") != a.get("activation_id") or
                q.get("loaded_code_digest") != loaded or
                q.get("loaded_dependency_digest") != deps):
            return False
        if not all(q.get(field) is True for field in (
            "independent_entry_quote_verified",
            "independent_exit_quote_verified",
            "priority_fees_verified",
            "slippage_modeled",
        )):
            return False
        entry = _utc(t.get("entered_at_utc"))
        exit_at = _utc(t.get("exited_at_utc"))
        entry_quote = _utc(q.get("entry_quote_at_utc"))
        exit_quote = _utc(q.get("exit_quote_at_utc"))
        if not all((entry, exit_at, entry_quote, exit_quote)):
            return False
        if not (stamp <= entry <= exit_at <= now):
            return False
        return (stamp <= entry_quote <= entry and
                stamp <= exit_quote <= exit_at and
                0 <= (entry - entry_quote).total_seconds() <= 30 and
                0 <= (exit_at - exit_quote).total_seconds() <= 30)

    if len({t.get("trade_id") for t in matching}) == len(matching) and all(
            matched_quote(t) for t in matching):
        report["quote_evidence"] = "HOST_CLAIM_ONLY"
        report["reasons"].append("INDEPENDENT_QUOTE_AND_COST_VALIDATOR_NOT_CONNECTED")
    else:
        report["reasons"].append("MATCHED_EXECUTABLE_QUOTES_INCOMPLETE")
    return report


def assess_all(activation: dict | None, trades: list[dict],
               quotes: list[dict], *, as_of: str) -> dict:
    return {arm: assess_arm(arm, activation, trades, quotes, as_of=as_of)
            for arm in ARMS}
