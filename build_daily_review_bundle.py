#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, json, re, shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
SMART_DATA_DIR = ROOT / "SmartMoneyMonitor" / "data"
ANALYSIS_DIR = ROOT / "analysis" / "daily"

DENY_NAMES = {".env", "traders.json", "wallet.json", "wallets.json"}
DENY_PARTS = {"private_key", "private-key", "seed", "mnemonic", "keystore", "secret", "credential"}
TIMESTAMP_COLUMNS = [
    "timestamp","time","datetime","detected_at","detected_at_utc","reviewed_at",
    "trade_time_utc","sample_time_utc","updated_at_utc","created_at"
]

ROOT_PATTERNS = [
    "trades_{date}.csv","missed_opportunities_{date}.csv","surge_followup_log.csv",
    "confirmation_feed_log.csv","ai_confirmation_log.csv","reacceleration_watch_log.csv",
    "discovery_source_log.csv","holder_metrics_history.csv","x_api_usage_log.csv"
]
SMART_FILES = [
    "smart_money_events_v22.csv","smart_money_campaigns_v22.csv",
    "trader_performance_v22.csv","wallet_scorecard_v22.csv",
    "smart_money_events_v21.csv","smart_money_campaigns_v21.csv","trader_performance_v21.csv"
]
VERSION_PATTERNS = [
    "auto_trader_with_alerts_*.py","cryptotracker_dashboard_*.py",
    "SmartMoneyMonitor/smart_money_monitor_*.py"
]

def args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    return ap.parse_args()

def safe(path: Path) -> bool:
    s = str(path).lower()
    return path.name.lower() not in DENY_NAMES and not any(x in s for x in DENY_PARTS)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def ts_col(fields):
    m = {x.lower(): x for x in fields}
    for c in TIMESTAMP_COLUMNS:
        if c in m:
            return m[c]
    return None

def row_matches_date(value, date_str):
    t = str(value or "").strip()
    if t.startswith(date_str):
        return True
    for fmt in ("%m/%d/%Y %H:%M:%S","%m/%d/%Y %H:%M","%Y-%m-%d %H:%M:%S","%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(t[:19], fmt).strftime("%Y-%m-%d") == date_str
        except Exception:
            pass
    return False

def copy_csv(src: Path, dst: Path, date_str: str):
    with src.open("r", newline="", encoding="utf-8-sig", errors="replace") as f:
        r = csv.DictReader(f)
        fields = r.fieldnames or []
        col = ts_col(fields)
        if not fields or not col:
            shutil.copy2(src, dst)
            return {"mode":"copied","rows":None,"timestamp_column":None}
        rows = [x for x in r if row_matches_date(x.get(col), date_str)]
    with dst.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return {"mode":"filtered","rows":len(rows),"timestamp_column":col}

def copy_one(src: Path, dst_dir: Path, date_str: str):
    if not src.exists() or not src.is_file() or not safe(src):
        return None
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    info = copy_csv(src, dst, date_str) if src.suffix.lower()==".csv" else (
        shutil.copy2(src, dst) or {"mode":"copied","rows":None,"timestamp_column":None}
    )
    if not isinstance(info, dict):
        info = {"mode":"copied","rows":None,"timestamp_column":None}
    return {
        "source":str(src.relative_to(ROOT)),
        "bundle_file":str(dst.relative_to(ROOT)),
        "bytes":dst.stat().st_size,
        "sha256":sha256(dst),
        **info
    }

def newest(pattern):
    xs = [p for p in ROOT.glob(pattern) if p.is_file()]
    return max(xs, key=lambda p:p.stat().st_mtime) if xs else None

def main():
    a = args()
    date_str = a.date or datetime.now().strftime("%Y-%m-%d")
    bundle = ANALYSIS_DIR / date_str
    raw = bundle / "raw"
    meta = bundle / "meta"
    raw.mkdir(parents=True, exist_ok=True)
    meta.mkdir(parents=True, exist_ok=True)

    manifest = {
        "review_date":date_str,
        "created_at_local":datetime.now().isoformat(timespec="seconds"),
        "files":[],
        "versions":[],
        "notes":["Secrets excluded.",".env.config may be included because it is intended to be non-secret."]
    }

    for pat in ROOT_PATTERNS:
        fn = pat.format(date=date_str)
        for src in (DATA_DIR/fn, ROOT/fn):
            item = copy_one(src, raw, date_str)
            if item:
                manifest["files"].append(item)
                break

    v22_keys = set()
    for name in SMART_FILES:
        key = re.sub(r"_v2[12]", "_vXX", name)
        if "_v21" in name and key in v22_keys:
            continue
        item = copy_one(SMART_DATA_DIR/name, raw, date_str)
        if item:
            manifest["files"].append(item)
            if "_v22" in name:
                v22_keys.add(key)

    cfg = ROOT / ".env.config"
    if cfg.exists():
        item = copy_one(cfg, meta, date_str)
        if item:
            manifest["files"].append(item)

    for pat in VERSION_PATTERNS:
        q = newest(pat)
        if q:
            manifest["versions"].append({
                "path":str(q.relative_to(ROOT)),
                "modified":datetime.fromtimestamp(q.stat().st_mtime).isoformat(timespec="seconds"),
                "sha256":sha256(q)
            })

    manifest["file_count"] = len(manifest["files"])
    manifest["version_count"] = len(manifest["versions"])
    (bundle/"manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Daily review bundle created: {bundle}")
    print(f"Files included: {manifest['file_count']}")
    for x in manifest["files"]:
        extra = f" | rows={x['rows']}" if x.get("rows") is not None else ""
        print(f"  {x['bundle_file']}{extra}")

if __name__ == "__main__":
    main()
