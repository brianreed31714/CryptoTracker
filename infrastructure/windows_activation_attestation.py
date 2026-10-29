"""CryptoTracker Windows activation attestation (non-destructive, fail closed).

Called by the *already authorized* CryptoTracker deployment-agent loop after
its successful fast-forward sync. This never starts/stops a process, submits a
trade, modifies scheduled tasks, exposes a command line, or publishes raw logs.

Important distinction:
  CODE_SYNCED: Git source files are on Windows, not proof of an in-memory reload.
  PROCESSES_STABLE: three separated host observations of expected script IDs.
  EOD_EXECUTION_VERIFIED: a newly executed post-sync local review completed and
      wrote matching, fresh artifacts. This is not broker correctness or reboot
      recovery proof.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from infrastructure.runtime_inventory import collect, git_head, parse_timestamp

REPORT_NAME = "activation_attestation.json"
REQUIRED_PROCESSES = ("supervisor", "deployment_agent", "trader", "dashboard")
REQUIRED_SCRIPT_VERSIONS = ("trader", "dashboard")
MIN_SECONDS_BETWEEN_SAMPLES = 20
REQUIRED_SAMPLES = 3
REMOTE_HEARTBEAT_SECONDS = 60 * 60  # Sanitized GitHub heartbeat, not a process restart.
SHA = re.compile(r"^[0-9a-f]{40}$")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, TypeError, ValueError):
        return {}


def _head(root: Path, rev: str) -> str:
    try:
        response = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", rev],
            text=True, capture_output=True, timeout=10,
        )
        value = response.stdout.strip().lower()
        return value if response.returncode == 0 and SHA.fullmatch(value) else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _code_clean(root: Path) -> bool:
    """Only compare source files; mutable external reports must stay irrelevant."""
    try:
        res = subprocess.run(
            ["git", "-C", str(root), "diff", "--quiet", "--",
             "infrastructure", "deployment_agent.py",
             "cryptotracker_supervisor.py", "run_daily_model_review.bat",
             "sync_proposals_to_git.py", "build_daily_review_bundle.py",
             "daily_model_review.py", "proposal_registry.py",
             "publish_daily_evidence.py", "build_daily_review_bundle.py"],
            timeout=10, capture_output=True,
        )
        staged = subprocess.run(
            ["git", "-C", str(root), "diff", "--cached", "--quiet", "--",
             "infrastructure", "deployment_agent.py",
             "cryptotracker_supervisor.py", "run_daily_model_review.bat",
             "sync_proposals_to_git.py", "build_daily_review_bundle.py",
             "daily_model_review.py", "proposal_registry.py",
             "publish_daily_evidence.py", "build_daily_review_bundle.py"],
            timeout=10, capture_output=True,
        )
        return res.returncode == staged.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def review_after_sync(root: Path, first_seen: str, *, clock: datetime | None = None) -> dict:
    """Confirm crypto paper EOD sender recorded a post-sync successful send.

    Neither Pushover device delivery nor live trading is established.
    """
    state = _read_json(root / "data" / "crypto_eod_report_state.json")
    day = str(state.get("last_sent_date") or "")
    if not re.fullmatch(r"20\d\d-\d\d-\d\d", day):
        return {"state": "NOT_VERIFIED", "reason": "CRYPTO_EOD_SEND_NOT_RECORDED"}
    try:
        date = datetime.fromisoformat(day).date().isoformat()
        sent = parse_timestamp(str(state.get("sent_at") or ""))
        first = parse_timestamp(first_seen)
        now = clock or now_utc()
        if day != date or not first <= sent <= now:
            return {"state": "NOT_VERIFIED", "reason": "EOD_SEND_OUTSIDE_SYNC_WINDOW"}
    except (ValueError, TypeError):
        return {"state": "NOT_VERIFIED", "reason": "EOD_SEND_TIMESTAMP_UNVERIFIED"}
    return {"state": "VERIFIED", "review_date": day}


def evaluate_snapshot(snapshot: dict) -> tuple[bool, dict, list[str]]:
    components = snapshot.get("components") or {}
    reasons = []
    # Process and script-version checks must ALL be positively observed.
    evidence = {}
    for name in REQUIRED_PROCESSES:
        component = components.get(name) or {}
        proc = component.get("process") or {}
        version = component.get("script_version") or {}
        pids = proc.get("pids") or []
        if proc.get("state") != "OBSERVED" or len(pids) != 1 or not isinstance(pids[0], int):
            reasons.append("PROCESS_UNVERIFIED_" + name.upper())
            continue
        # Include observed Windows creation time to reject PID reuse across polls.
        started = proc.get("started_utc")
        try:
            if not started:
                raise ValueError("missing start provenance")
            parse_timestamp(started)
        except (ValueError, TypeError):
            reasons.append("START_TIME_UNVERIFIED_" + name.upper())
            continue
        if name in REQUIRED_SCRIPT_VERSIONS and version.get("state") != "MATCHED":
            reasons.append("SCRIPT_VERSION_UNVERIFIED_" + name.upper())
            continue
        evidence[name] = (pids[0], started, str(proc.get("script") or ""))
    # Smart Money v2.3 heartbeat is more authoritative than hidden CIM
    # command lines. It proves fresh feed output, never PID or script digest.
    smart = (components.get("smart_money") or {}).get("artifact") or {}
    if smart.get("state") != "HEALTHY":
        reasons.append("SMART_MONEY_HEARTBEAT_NOT_HEALTHY")
    else:
        evidence["smart_money_feed"] = ("HEARTBEAT", "HEALTHY", "READ_ONLY")
    return not reasons, evidence, reasons


def advance(root: Path, previous: dict, snapshot: dict, *,
            head: str, upstream: str, clean: bool, clock: datetime) -> dict:
    """Pure state machine; never equate synchronized source with executing code."""
    timestamp = clock.isoformat()
    result = {
        "schema_version": 1,
        "observed_at_utc": timestamp,
        "git_head": head if SHA.fullmatch(head or "") else "UNVERIFIED",
        "origin_main": upstream if SHA.fullmatch(upstream or "") else "UNVERIFIED",
        "state": "UNVERIFIED",
        "code_synced": False,
        "processes_stable": False,
        "eod_execution_verified": False,
        "consecutive_observations": 0,
        "first_seen_at_utc": timestamp,
        "last_sample_at_utc": timestamp,
        "fingerprint": {},
        "reasons": [],
        "notice_key": str(previous.get("notice_key") or ""),
        "notification": "UNCONFIRMED",
    }
    if not head or head != upstream or not SHA.fullmatch(head) or not clean:
        result["reasons"] = ["GIT_SYNC_OR_SOURCE_INTEGRITY_UNVERIFIED"]
        return result
    result["code_synced"] = True
    same_head = previous.get("git_head") == head and previous.get("code_synced") is True
    if same_head:
        result["first_seen_at_utc"] = previous.get("first_seen_at_utc", timestamp)
    passed, evidence, reasons = evaluate_snapshot(snapshot)
    if not passed:
        result["state"] = "CODE_SYNCED_RUNTIME_UNVERIFIED"
        result["reasons"] = reasons
        return result
    result["state"] = "CODE_SYNCED_PROCESS_OBSERVED"
    fingerprint = {name: list(details) for name, details in sorted(evidence.items())}
    result["fingerprint"] = fingerprint
    prior_fingerprint = previous.get("fingerprint") or {}
    previous_stamp = previous.get("last_sample_at_utc") or ""
    try:
        interval = (clock - parse_timestamp(previous_stamp)).total_seconds()
    except (ValueError, TypeError):
        interval = -1
    if same_head and prior_fingerprint == fingerprint and interval >= MIN_SECONDS_BETWEEN_SAMPLES:
        result["consecutive_observations"] = min(
            REQUIRED_SAMPLES, max(0, int(previous.get("consecutive_observations") or 0)) + 1
        )
    else:
        result["consecutive_observations"] = 1
    if result["consecutive_observations"] < REQUIRED_SAMPLES:
        return result
    result["processes_stable"] = True
    result["state"] = "HOST_PROCESSES_STABLE_SOURCE_ONLY"
    status = review_after_sync(root, result["first_seen_at_utc"], clock=clock)
    if status.get("state") == "VERIFIED":
        result["state"] = "EOD_EXECUTION_VERIFIED"
        result["eod_execution_verified"] = True
        result["verified_review_date"] = status["review_date"]
    else:
        result["reasons"] = [str(status.get("reason") or "REVIEW_NOT_VERIFIED")]
    # Trading correctness / in-memory source digest / reboot recovery NOT proven.
    return result


def atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate = path.with_suffix(".tmp")
    candidate.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    candidate.replace(path)


def poll(root: Path, *, observation: dict | None = None,
         clock: datetime | None = None, expected_sha: str = "",
         notify: Callable[[str, str], bool] | None = None,
         remote_publish: Callable[[Path, dict], str] | None = None) -> dict:
    """One bounded observation by a Windows-hosted, already running agent.

    Optional notification is supplied by agent's Pushover sender; an unverified
    or missing process never sends a 'verified deployment' message.
    """
    if os.name != "nt" and observation is None:
        raise RuntimeError("Windows-only host collection")
    root = Path(root).resolve()
    state_path = root / "deploy" / "state" / REPORT_NAME
    previous = _read_json(state_path)
    stamp = clock or now_utc()
    head = git_head(root)
    origin = _head(root, "refs/remotes/origin/main")
    if expected_sha and (not SHA.fullmatch(expected_sha) or expected_sha != head):
        origin = ""  # Explicit pinned commit does not match.
    clean = _code_clean(root)
    # Never use a GitHub CI snapshot as a substitute for this Windows read.
    try:
        snapshot = observation if observation is not None else collect(root)
        report = advance(root, previous, snapshot, head=head,
                         upstream=origin, clean=clean, clock=stamp)
    except (ValueError, TypeError, OSError, RuntimeError):
        report = advance(root, previous, {}, head="", upstream="", clean=False, clock=stamp)
        report["reasons"] = ["HOST_INVENTORY_UNAVAILABLE"]
    # Collect sanitized disk evidence from the same Windows observation.
    # These hashes are explicitly NOT in-memory process attestation.
    try:
        from infrastructure.host_evidence_collector import collect_host_evidence
        from infrastructure.registry_contract import validate_registry
        registry = validate_registry(root, check_local_safety=True)
        dep_files = ("paper_research_lab_v11_10.py", "publish_daily_evidence.py") if registry["project"] == "CryptoTracker" else ("daily_model_review.py",)
        disk = collect_host_evidence(root, snapshot, dependencies=dep_files)
    except (OSError, RuntimeError, ValueError, KeyError, UnboundLocalError):
        disk = {"disk_code_sha256": None, "disk_dependencies_sha256": None,
                "process_identity_observed": False, "loaded_code_verified": False,
                "loaded_dependencies_verified": False}
    report["disk_evidence"] = disk
    # Publish only the date/timestamp of a locally recorded EOD send, even if
    # it predates source sync. This is a claim, never provider/device proof.
    try:
        from infrastructure.eod_send_observation import inspect_local_eod_send
        report["local_eod_send_observation"] = inspect_local_eod_send(root, now=stamp)
    except (OSError, RuntimeError, ValueError, TypeError):
        report["local_eod_send_observation"] = {"status": "MISSING_OR_INVALID"}
    # Read-only scheduler evidence; task exit code never establishes EOD delivery.
    try:
        from infrastructure.daily_review_task_probe import inspect_daily_review_task
        report["daily_review_task_observation"] = inspect_daily_review_task(clock=stamp)
    except (OSError, RuntimeError, ValueError, TypeError):
        report["daily_review_task_observation"] = {"status": "UNVERIFIED"}
    # Every distinct commit gets a CODE_SYNCED notice after positive source
    # integrity; a later EOD verification gets a second distinct notice.
    # Do not send repeated notices for each 60-second polling interval.
    if report["code_synced"]:
        target = "EOD_VERIFIED" if report["eod_execution_verified"] else "SOURCE_SYNCED"
        key = report["git_head"] + ":" + target
        if key == previous.get("notice_key"):
            report["notice_key"] = key
            report["notification"] = previous.get("notification", "UNCONFIRMED")
        elif notify is not None:
            title = ("CryptoTracker Windows EOD Send Recorded" if report["eod_execution_verified"]
                     else "CryptoTracker Windows Code Synced")
            body = (f"{report['git_head'][:10]} | {report['state']}. "
                    "Source sync is not proof of a reloaded trader."
                    if target == "SOURCE_SYNCED" else
                    f"{report['git_head'][:10]} | Crypto EOD sender recorded successful Pushover API send "
                    f"for {report['verified_review_date']}. Device delivery and broker/trading health not attested.")
            try:
                delivered = notify(title, body) is True
            except Exception:
                delivered = False
            # Failed Pushover attempts remain eligible for one later retry.
            if delivered:
                report["notice_key"] = key
                report["notification"] = "API_ACCEPTED"
    # Dedicated non-main Git branch makes this proof independently readable
    # in GitHub/ChatGPT, without committing into the trading checkout. Never
    # publish process IDs, account data or raw receipt contents.
    # One-time republish after fixing Windows mktree CRLF filename corruption.
    # The version suffix invalidates only the old publication cache key;
    # it does not reset process observations or trigger a service restart.
    # Re-publish only meaningful changes in bounded, allowlisted health codes
    # or the three-sample stability sequence. No raw host diagnostics leave Windows.
    from infrastructure.host_status_publisher import safe_process_reasons, stability_samples
    remote_key = (report["git_head"] + ":" + report["state"] + ":" +
                  ",".join(safe_process_reasons(report)) + ":" +
                  str(stability_samples(report)) + ":" +
                  str(report.get("verified_review_date") or "") + ":" +
                  str((report.get("disk_evidence") or {}).get("disk_code_sha256") or "") + ":" +
                  str((report.get("local_eod_send_observation") or {}).get("review_date") or "") + ":" +
                  str((report.get("daily_review_task_observation") or {}).get("status") or "") + ":" +
                  str((report.get("daily_review_task_observation") or {}).get("last_run_utc") or "") + ":" +
                  str((report.get("daily_review_task_observation") or {}).get("last_task_result") or "") + ":status-file-v5")
    previous_publish = str(previous.get("remote_published_at_utc") or "")
    try:
        age_seconds = (stamp - parse_timestamp(previous_publish)).total_seconds()
    except (ValueError, TypeError):
        age_seconds = -1
    recent_publish = 0 <= age_seconds < REMOTE_HEARTBEAT_SECONDS
    if remote_publish is None and os.name == "nt" and observation is None:
        from infrastructure.host_status_publisher import publish as remote_publish
    enabled = os.getenv("CRYPTOTRACKER_ATTESTATION_REMOTE_ENABLED", "1").strip().lower() not in (
        "0", "false", "no", "off")
    if report["code_synced"] and remote_publish is not None and enabled:
        if remote_key == previous.get("remote_key") and recent_publish:
            report["remote_key"] = remote_key
            report["remote_published_at_utc"] = previous_publish
            report["remote_publish"] = "PUBLISHED"
        else:
            try:
                remote_publish(root, report)
                report["remote_key"] = remote_key
                report["remote_published_at_utc"] = stamp.isoformat()
                report["remote_publish"] = "PUBLISHED"
            except Exception:
                # Git credentials, branch protection or concurrency may reject
                # the update; this must never interrupt the trader or EOD.
                report["remote_key"] = str(previous.get("remote_key") or "")
                report["remote_published_at_utc"] = previous_publish
                report["remote_publish"] = "UNCONFIRMED"
    else:
        report["remote_key"] = str(previous.get("remote_key") or "")
        report["remote_published_at_utc"] = previous_publish
        report["remote_publish"] = "DISABLED" if not enabled else "UNCONFIRMED"
    atomic_write(state_path, report)
    return report

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="One-shot, read-only Windows activation evidence")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--expect", default="", help="Optional exact 40-character expected Git HEAD")
    parser.add_argument("--notify", action="store_true", help="Send Pushover if host-configured and state changed")
    args = parser.parse_args()
    try:
        if os.name != "nt":
            raise RuntimeError("Windows required for host attestation")
        notifier = None
        if args.notify:
            from deployment_agent import push_attestation
            notifier = push_attestation
        receipt = poll(args.root, expected_sha=args.expect, notify=notifier)
        # Output intentionally excludes PIDs, task history, user paths, logs and secrets.
        print(json.dumps({
            "state": receipt["state"],
            "git_head": receipt["git_head"],
            "processes_stable": receipt["processes_stable"],
            "eod_execution_verified": receipt["eod_execution_verified"],
            "notification": receipt["notification"],
            "remote_publish": receipt["remote_publish"],
        }, sort_keys=True))
        return 0 if receipt["code_synced"] else 2
    except (OSError, RuntimeError, ValueError):
        print('{"state": "UNVERIFIED", "reason": "HOST_ATTESTATION_UNAVAILABLE"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
