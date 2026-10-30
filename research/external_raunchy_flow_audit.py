"""External SmugCalls dataset: read-only, fail-closed raunchy-name screening.

Run: python research/external_raunchy_flow_audit.py --input calls.jsonl
Get calls.jsonl from https://github.com/Smurfetc/solana-memecoin-calls-dataset
The dataset does NOT contain liquidity, 5m volume, buy/sell counts,
acceleration, or executable entry/exit price paths. Do not infer strategy P&L.
"""
import argparse
import collections
import datetime as dt
import hashlib
import json
import pathlib
import re

PATTERNS = [
    re.compile(x, re.I) for x in (
        r"sex(?!ton)|sexy|porn|xxx|nsfw|nude|naked|dick|cock(?!roach)|pussy|tits|boob|cum(?!ber|ulat)|jizz|horny|boner|dildo|milf|sperm|orgasm|slut|whore|onlyfans|fap|thot",
        r"fuck|fuk|fck|shit|bitch|cunt|bastard|wtf|damn|piss|motherf|stfu|bullshit",
        r"fart|poop|toilet|diarrhea|turd|peepee|puke|vomit|shart|butt(?!on|er)",
    )
]

def analyze(path, start="2026-04-29", end="2026-10-29"):
    counts = collections.Counter()
    matches = []
    dates = []
    seen = set()
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            counts["source_rows"] += 1
            row = json.loads(line)
            try:
                day = dt.datetime.fromtimestamp(int(row["t"]), dt.timezone.utc).date().isoformat()
            except (ValueError, KeyError, TypeError):
                counts["invalid_timestamp"] += 1
                continue
            dates.append(day)
            if not start <= day <= end:
                continue
            counts["window_rows"] += 1
            mint = str(row.get("mint") or "")
            if not mint or mint in seen:
                counts["duplicate_or_missing_mint"] += 1
                continue
            seen.add(mint)
            if any(pattern.search(str(row.get("sym") or "")) for pattern in PATTERNS):
                counts["raunchy_symbol_matches"] += 1
                matches.append({
                    "mint": mint, "symbol": row.get("sym"), "date": day,
                    "market_cap_at_call": row.get("mc"),
                    "future_peak_multiple_NOT_EXIT_RETURN": row.get("peak"),
                    "name_only_classification": True,
                    "flow_gate": "MISSING", "entry": "UNVERIFIED",
                    "exit": "UNVERIFIED"
                })
    return {
        "source": "Smurfetc/solana-memecoin-calls-dataset/calls.jsonl",
        "source_sha256": hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest(),
        "requested_window": [start, end],
        "observed_window": [min(dates), max(dates)] if dates else None,
        "counts": dict(counts), "matches": matches,
        "flow_eligibility": "MISSING", "executable_net_roi": "MISSING",
        "drawdown": "MISSING", "status": "NAME_SCREEN_ONLY_NOT_BACKTEST",
        "limitations": [
            "No full token name; symbol-only name screening undercounts matches",
            "No 5m volume, buys/sells, liquidity or volume acceleration",
            "No timestamped post-entry exit path or executable quotes",
            "Source is a selected caller stream, not all Solana launches",
            "Future peak is not a realizable return and must not be used as an exit"
        ]
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="external_raunchy_flow_audit.json")
    parser.add_argument("--start", default="2026-04-29")
    parser.add_argument("--end", default="2026-10-29")
    args = parser.parse_args()
    result = analyze(args.input, args.start, args.end)
    pathlib.Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "matches"}, indent=2))
