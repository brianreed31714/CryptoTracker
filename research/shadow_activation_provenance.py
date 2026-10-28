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
              "executable_net": "MISSING", "preliminary_sample": "UNVERIFIED",
              "valid_post_activation_exits": 0, "reasons": []}
    a = activation if isinstance(activation, dict) else {}
    stamp = _utc(a.get("activated_at_utc"))
    now = _utc(as_of)
    if now is None:
        raise ValueError("Invalid as_of timestamp")
    # Host-signed runtime manifest must independently assert both loaded code
    # and dependency digest, not merely git sync or a file-on-disk checksum.
    loaded = a.get("loaded_code_digest")
    deps = a.get("loaded_dependency_digest")
    if not (a.get("independently_observed") is True and
            isinstance(loaded, str) and len(loaded) == 64 and
            isinstance(deps, str) and len(deps) == 64 and
            all(c in "0123456789abcdef" for c in loaded + deps) and
            stamp is not None and stamp <= now):
        report["reasons"].append("LOADED_RUNTIME_PROVENANCE_UNVERIFIED")
        return report
    report["runtime"] = "VERIFIED"
    matching = []
    for row in trades:
        if not isinstance(row, dict) or row.get("arm") != arm or row.get("event") != "EXIT":
            continue
        when = _utc(row.get("exited_at_utc"))
        if (when is not None and stamp <= when <= now and
                row.get("loaded_code_digest") == loaded and
                row.get("loaded_dependency_digest") == deps and
                row.get("activation_id") == a.get("activation_id") and
                a.get("activation_id")):
            matching.append(row)
    report["valid_post_activation_exits"] = len(matching)
    if not matching:
        report["reasons"].append("NO_VERSION_MATCHED_POST_ACTIVATION_EXITS")
        return report
    report["trade_provenance"] = "VERIFIED"
    if len(matching) >= 30:
        report["preliminary_sample"] = "MODELED"
    # Quotes must be independent timestamp-matched entry AND exit executable
    # observations; a raw mark or a historical spot price is not a fill quote.
    quote_by_trade = {q.get("trade_id"): q for q in quotes if isinstance(q, dict)}
    if all((q := quote_by_trade.get(t.get("trade_id"))) and
           q.get("independent_entry_quote_verified") is True and
           q.get("independent_exit_quote_verified") is True and
           q.get("priority_fees_verified") is True and
           q.get("slippage_modeled") is True
           for t in matching):
        report["executable_net"] = "MODELED"
    else:
        report["reasons"].append("MATCHED_EXECUTABLE_QUOTES_INCOMPLETE")
    return report


def assess_all(activation: dict | None, trades: list[dict],
               quotes: list[dict], *, as_of: str) -> dict:
    return {arm: assess_arm(arm, activation, trades, quotes, as_of=as_of)
            for arm in ARMS}
