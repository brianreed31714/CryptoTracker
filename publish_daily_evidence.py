#!/usr/bin/env python3
"""Publish a sanitized CryptoTracker daily evidence bundle to the private repo.

Only allowlisted research/reporting files are copied. Secret/config files,
wallet credentials, local state, and arbitrary runtime files are never staged.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
PAPER_DIR = DATA_DIR / "paper_research"
PUBLISHED_ROOT = ROOT / "published" / "daily"

PAPER_CSV = (
    "candidate_observations.csv",
    "model_decisions.csv",
    "paper_trades.csv",
    "shadow_trades.csv",
    "model_equity.csv",
)

ROOT_DATA_CSV = (
    "surge_followup_log.csv",
    "surge_followup_audit.csv",
    "confirmation_feed_log.csv",
    "ai_confirmation_log.csv",
    "reacceleration_watch_log.csv",
    "discovery_source_log.csv",
    "x_api_usage_log.csv",
    "missed_opportunity_audit.csv",
)

DENIED_COLUMNS = {
    "api_key",
    "private_key",
    "secret",
    "seed_phrase",
    "mnemonic",
    "pushover_token",
    "wallet_private_key",
}


def _enabled():
    return str(
        os.getenv("EVIDENCE_PUBLISH_ENABLED", "1")
    ).strip().lower() not in {"0", "false", "no", "off"}


def _run(*args, check=True):
    return subprocess.run(
        list(args),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def _row_matches_date(row, report_date):
    for key in (
        "date",
        "report_date",
        "signal_time",
        "timestamp",
        "sample_time",
        "logged_at",
        "trade_time_utc",
        "created_at",
        "updated_at_utc",
    ):
        value = str(row.get(key) or "")
        if value.startswith(report_date):
            return True
    return False


def _safe_row(row):
    return {
        key: value
        for key, value in row.items()
        if str(key).strip().lower() not in DENIED_COLUMNS
    }


def _filter_csv(source, destination, report_date):
    if not source.exists() or source.stat().st_size == 0:
        return 0
    try:
        with source.open("r", newline="", encoding="utf-8") as handle:
            rows = [
                _safe_row(row)
                for row in csv.DictReader(handle)
                if _row_matches_date(row, report_date)
            ]
    except Exception:
        return 0

    if not rows:
        return 0

    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def _copy_if_exists(source, destination):
    if not source.exists() or not source.is_file():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return True


def _repo_clean_before_publish():
    result = _run("git", "status", "--porcelain", check=False)
    return result.returncode == 0 and not result.stdout.strip()


def publish_daily_evidence(report_date=None):
    if not _enabled():
        return {"status": "DISABLED"}

    report_date = report_date or datetime.now().date().isoformat()

    # Never mix arbitrary local edits into an automated evidence commit.
    if not _repo_clean_before_publish():
        return {
            "status": "SKIPPED_DIRTY_REPO",
            "date": report_date,
        }

    destination = PUBLISHED_ROOT / report_date
    raw = destination / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    counts = {}
    for name in PAPER_CSV:
        count = _filter_csv(
            PAPER_DIR / name,
            raw / name,
            report_date,
        )
        if count:
            counts[name] = count

    for name in ROOT_DATA_CSV:
        count = _filter_csv(
            DATA_DIR / name,
            raw / name,
            report_date,
        )
        if count:
            counts[name] = count

    for dated_name in (
        f"trades_{report_date}.csv",
        f"missed_opportunities_{report_date}.csv",
        f"luna_outcomes_{report_date}.csv",
    ):
        if _copy_if_exists(
            DATA_DIR / dated_name,
            raw / dated_name,
        ):
            counts[dated_name] = "copied"

    paper_daily = PAPER_DIR / "daily"
    for suffix in ("json", "md"):
        _copy_if_exists(
            paper_daily / f"{report_date}.{suffix}",
            destination / f"paper_summary.{suffix}",
        )

    _copy_if_exists(
        PAPER_DIR / "campaign_summary.json",
        destination / "campaign_summary.json",
    )

    # Audits describe simulated execution and history reconciliation; they
    # never modify the trader, its positions, or its decision thresholds.
    from research.paper_quality_audit import csv_rows, audit_paper_day
    quality = audit_paper_day(csv_rows(raw / "paper_trades.csv"), report_date, PUBLISHED_ROOT)
    (destination / "quality_audit.json").write_text(
        json.dumps(quality, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    counts["quality_audit.json"] = "generated"

    # Automated research diagnostics are read-only and aggregate-only.
    # They publish with the ordinary EOD evidence; no manual reconciliation.
    from research.crypto_improvement_diagnostics import generate
    improvement = generate(
        PAPER_DIR / "paper_trades.csv",
        report_date,
        destination,
        float(os.getenv("PAPER_STARTING_EQUITY_USDC", "15")),
    )
    counts["improvement_diagnostics.json"] = "generated"
    counts["improvement_diagnostics.md"] = "generated"

    # Prospective shadow variants are marked explicitly as UNPRICED marks.
    # They never place orders or claim simulated returns are executable.
    from research.paper_shadow_experiments import generate as generate_shadow
    generate_shadow(PAPER_DIR / "shadow_trades.csv", report_date, destination)
    counts["shadow_experiments.json"] = "generated"
    counts["shadow_experiments.md"] = "generated"

    # Read-only paper liquidation readiness. The private state and any raw
    # Jupiter quote snapshot stay local; only sanitized per-sleeve aggregates
    # are committed. Missing or stale quotes are explicitly UNAVAILABLE.
    from research.paper_liquidation_mtm import generate as generate_mtm
    generate_mtm(
        PAPER_DIR / "state.json",
        PAPER_DIR / "liquidation_quotes.json",
        report_date,
        destination,
    )
    counts["liquidation_mtm_readiness.json"] = "generated"
    counts["liquidation_mtm_readiness.md"] = "generated"

    commit = _run(
        "git",
        "rev-parse",
        "HEAD",
        check=False,
    ).stdout.strip()

    manifest = {
        "report_date": report_date,
        "published_at": datetime.now().isoformat(),
        "source_commit": commit,
        "files": counts,
        "paper_only": str(
            os.getenv("LIVE_TRADING", "false")
        ).strip().lower() in {"0", "false", "no", "off"},
        "sanitized": True,
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    rel = str(destination.relative_to(ROOT)).replace("\\", "/")
    add = _run("git", "add", "--", rel, check=False)
    if add.returncode != 0:
        return {
            "status": "GIT_ADD_FAILED",
            "error": add.stderr[-500:],
        }

    changed = _run(
        "git",
        "diff",
        "--cached",
        "--quiet",
        "--",
        rel,
        check=False,
    )
    if changed.returncode == 0:
        return {
            "status": "NO_CHANGES",
            "date": report_date,
            "files": counts,
        }

    commit_result = _run(
        "git",
        "commit",
        "-m",
        f"Publish CryptoTracker evidence {report_date}",
        "--",
        rel,
        check=False,
    )
    if commit_result.returncode != 0:
        _run("git", "reset", "--", rel, check=False)
        return {
            "status": "GIT_COMMIT_FAILED",
            "error": commit_result.stderr[-500:],
        }

    push = _run("git", "push", check=False)
    if push.returncode != 0:
        return {
            "status": "GIT_PUSH_FAILED",
            "error": push.stderr[-500:],
            "date": report_date,
        }

    return {
        "status": "PUBLISHED",
        "date": report_date,
        "files": counts,
    }


if __name__ == "__main__":
    print(json.dumps(publish_daily_evidence(), indent=2))
