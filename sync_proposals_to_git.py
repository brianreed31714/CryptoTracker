#!/usr/bin/env python3
"""
Push sanitized proposal artifacts to the private GitHub repo.

This intentionally stages only allowlisted analysis paths, never .env,
traders.json, raw runtime data, or secrets.
"""

from __future__ import annotations

import argparse
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent

ALLOWLIST = [
    "analysis/proposals",
]


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(args),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def ensure_repo():
    r = run("git", "rev-parse", "--show-toplevel", check=False)
    if r.returncode != 0:
        raise RuntimeError("CryptoTracker folder is not a Git repository.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--message", default="")
    args = ap.parse_args()

    ensure_repo()

    for path in ALLOWLIST:
        run("git", "add", "--", path)

    status = run("git", "diff", "--cached", "--name-only").stdout.strip()
    if not status:
        print("No proposal changes to push.")
        return

    # Refuse the push if anything outside the allowlist somehow became staged.
    staged = [x.strip() for x in status.splitlines() if x.strip()]
    bad = [x for x in staged if not any(x == a or x.startswith(a + "/") for a in ALLOWLIST)]
    if bad:
        raise RuntimeError(f"Refusing push: non-allowlisted staged files: {bad}")

    msg = args.message or f"Publish CryptoTracker proposals {datetime.now():%Y-%m-%d %H:%M}"
    run("git", "commit", "-m", msg)
    run("git", "push")
    print("Proposal registry committed and pushed.")
    for x in staged:
        print(f"  {x}")


if __name__ == "__main__":
    main()
