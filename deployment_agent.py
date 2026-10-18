#!/usr/bin/env python3
"""
CryptoTracker local deployment agent.

Runs on the Windows trading PC. It polls the private Git repo for an approved
deployment request written by ChatGPT/Codex. It can only deploy allowlisted
CryptoTracker components and never executes arbitrary shell commands from Git.

Expected request:
  deploy/requests/P-YYYYMMDD-NN.json

Example:
{
  "proposal_id": "P-20260926-01",
  "status": "READY_TO_DEPLOY",
  "commit": "<full-or-short-git-sha>",
  "components": ["trader", "smart_money", "dashboard"],
  "files": {
    "trader": "auto_trader_with_alerts_v11_8_3.py",
    "smart_money": "SmartMoneyMonitor/smart_money_monitor_v2_3.py",
    "dashboard": "cryptotracker_dashboard_v11_8_3.py"
  }
}

Security model:
- exact allowlisted component names only
- Python files must stay inside the repo
- no arbitrary command fields are honored
- py_compile before activation
- Git commit must exist locally
- previous active manifest is kept for rollback
"""

from __future__ import annotations

import json
import os
import py_compile
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from infrastructure.registry_contract import release_preflight

ROOT = Path(__file__).resolve().parent
DEPLOY_DIR = ROOT / "deploy"
REQUEST_DIR = DEPLOY_DIR / "requests"
STATE_DIR = DEPLOY_DIR / "state"
ACTIVE_MANIFEST = STATE_DIR / "active_release.json"
PREVIOUS_MANIFEST = STATE_DIR / "previous_release.json"
PROCESSED_REQUESTS = STATE_DIR / "processed_requests.json"
LOG_FILE = STATE_DIR / "deployment_agent.log"

load_dotenv(ROOT / ".env.config")
load_dotenv(ROOT / ".env", override=True)

POLL_SECONDS = int(os.getenv("DEPLOYMENT_AGENT_POLL_SECONDS", "60"))
AUTO_DEPLOY = os.getenv("DEPLOYMENT_AGENT_ENABLED", "1").strip().lower() not in {"0","false","no"}

PUSH_TOKEN = (
    os.getenv("PUSHOVER_DEPLOY_TOKEN", "").strip()
    or os.getenv("PUSHOVER_CRYPTO_EOD_TOKEN", "").strip()
    or os.getenv("PUSHOVER_API_TOKEN", "").strip()
)
PUSH_USER = (
    os.getenv("PUSHOVER_DEPLOY_GROUP_KEY", "").strip()
    or os.getenv("PUSHOVER_CRYPTO_EOD_GROUP_KEY", "").strip()
    or os.getenv("PUSHOVER_USER_KEY", "").strip()
)

ALLOWED_COMPONENTS = {"trader", "smart_money", "dashboard"}
ALLOWED_PREFIXES = {
    "trader": ("auto_trader_with_alerts_",),
    "smart_money": ("SmartMoneyMonitor/smart_money_monitor_",),
    "dashboard": ("cryptotracker_dashboard_",),
}

# Capabilities that must survive every future trader deployment unless this
# guard itself is deliberately changed in an approved release.
PROTECTED_TRADER_CAPABILITIES = {
    "remote_autostart": (
        "REQUIRE_START_LIVE_CONFIRMATION",
        "Live startup confirmation: DISABLED (automatic)",
    ),
    "helius_wallet_cache": (
        "WALLET_BALANCE_CACHE_SECONDS",
        "_WALLET_USDC_BALANCE_CACHE",
    ),
    "helius_backoff": (
        "HELIUS_MAX_RETRIES",
        "def _helius_post_json",
    ),
    "scanner_pressure_cap": (
        "MAX_ACTIVE_SCAN_TOKENS",
    ),
    "shadow_forward_outcomes": (
        "SURGE_FOLLOWUP_AUDIT_FILE",
    ),
    "shadow_missed_opportunity_audit": (
        "MISSED_OPPORTUNITY_AUDIT_FILE",
    ),
    "v11_10_research_fairness": (
        "paper_research_lab_v11_10",
        "exit_value_lookup",
    ),
    "daily_evidence_publish": (
        "publish_daily_evidence",
        "Evidence publish:",
    ),
}


def log(msg: str):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now().isoformat(timespec='seconds')} | {msg}"
    print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def push(title: str, message: str):
    if not PUSH_TOKEN or not PUSH_USER:
        return
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={"token": PUSH_TOKEN, "user": PUSH_USER, "title": title, "message": message[:1024]},
            timeout=20,
        )
    except Exception:
        pass


def run(*args: str, check=True):
    return subprocess.run(
        list(args), cwd=ROOT, text=True, capture_output=True, check=check
    )


def safe_rel(component: str, rel: str) -> Path:
    if component not in ALLOWED_COMPONENTS:
        raise ValueError(f"Component not allowlisted: {component}")

    rel = str(rel).replace("\\", "/")
    if rel.startswith("/") or ".." in Path(rel).parts:
        raise ValueError(f"Unsafe path: {rel}")

    if not rel.endswith(".py"):
        raise ValueError(f"Only Python files may be activated: {rel}")

    if not any(rel.startswith(prefix) for prefix in ALLOWED_PREFIXES[component]):
        raise ValueError(f"File is not valid for {component}: {rel}")

    path = (ROOT / rel).resolve()
    if ROOT.resolve() not in path.parents:
        raise ValueError(f"File escapes repository: {rel}")
    if not path.exists():
        raise FileNotFoundError(rel)
    return path


def validate_trader_capabilities(path: Path):
    source = path.read_text(encoding="utf-8", errors="replace")
    missing = []
    for capability, markers in PROTECTED_TRADER_CAPABILITIES.items():
        if not all(marker in source for marker in markers):
            missing.append(capability)

    if missing:
        raise ValueError(
            "Trader regression guard failed; missing protected capabilities: "
            + ", ".join(missing)
        )


def validate_release_blob(commit: str, rel: str):
    """Do not activate a file whose code differs from its approved commit."""
    approved = run("git", "rev-parse", f"{commit}:{rel}", check=False)
    current = run("git", "rev-parse", f"HEAD:{rel}", check=False)
    if approved.returncode or current.returncode:
        raise ValueError(f"Cannot verify approved release blob: {rel}")
    if approved.stdout.strip() != current.stdout.strip():
        raise ValueError(
            f"Approved release file changed since {commit}: {rel}; "
            "new deployment approval is required."
        )


def validate_request(req: dict):
    if req.get("status") != "READY_TO_DEPLOY":
        raise ValueError("Request is not READY_TO_DEPLOY.")

    pid = str(req.get("proposal_id") or "")
    if not pid.startswith("P-"):
        raise ValueError("Invalid proposal_id.")

    commit = str(req.get("commit") or "").strip()
    if not commit:
        raise ValueError("Missing commit.")
    if run("git", "cat-file", "-e", f"{commit}^{{commit}}", check=False).returncode != 0:
        raise ValueError(f"Unknown commit: {commit}")

    comps = req.get("components") or []
    files = req.get("files") or {}
    # Fail closed on the version-controlled infrastructure contract BEFORE any process stop.
    release_preflight(ROOT, comps, files)
    if not comps:
        raise ValueError("No components requested.")

    validated = {}
    for comp in comps:
        validated[comp] = safe_rel(comp, files.get(comp, ""))
        if comp == "trader":
            validate_trader_capabilities(validated[comp])
        py_compile.compile(str(validated[comp]), doraise=True)
        validate_release_blob(commit, str(validated[comp].relative_to(ROOT)).replace("\\", "/"))

        # Compile versioned local dependencies referenced by protected traders.
        if comp == "trader":
            trader_source = validated[comp].read_text(
                encoding="utf-8",
                errors="replace",
            )
            dependency_markers = {
                "paper_research_lab_v11_10": ROOT / "paper_research_lab_v11_10.py",
                "publish_daily_evidence": ROOT / "publish_daily_evidence.py",
            }
            for marker, dep_path in dependency_markers.items():
                if marker in trader_source:
                    if not dep_path.exists():
                        raise FileNotFoundError(str(dep_path.relative_to(ROOT)))
                    py_compile.compile(str(dep_path), doraise=True)

    return pid, commit, validated


def pull_repo():
    # Do not merge dirty local code.
    dirty = run("git", "status", "--porcelain").stdout.strip()
    if dirty:
        raise RuntimeError("Local repo has uncommitted changes; deployment halted.")
    # Pin the exact repository branch; local git pull can have multiple configured upstreams.
    branch = run("git", "branch", "--show-current").stdout.strip()
    if branch != "main":
        raise RuntimeError("Deployment agent must run on main, not " + branch)
    run("git", "fetch", "origin", "main")
    run("git", "merge", "--ff-only", "origin/main")


def taskkill_for_script(script_name: str):
    # PowerShell is used only with our locally constructed exact filename.
    escaped = script_name.replace("'", "''")
    cmd = (
        "$p=Get-CimInstance Win32_Process | "
        f"Where-Object {{$_.CommandLine -like '*{escaped}*' -and $_.ProcessId -ne $PID}}; "
        "$p | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", cmd], cwd=ROOT)


def start_component(component: str, path: Path):
    rel = str(path.relative_to(ROOT))
    if component == "dashboard":
        cmd = [sys.executable, "-m", "streamlit", "run", rel]
    else:
        cmd = [sys.executable, rel]

    flags = 0
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP

    return subprocess.Popen(cmd, cwd=ROOT, creationflags=flags)


def save_manifest(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_manifest(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def stop_active(manifest: dict):
    for comp, rel in (manifest.get("files") or {}).items():
        if comp in ALLOWED_COMPONENTS and rel:
            taskkill_for_script(Path(rel).name)


def processed_requests():
    data = load_manifest(PROCESSED_REQUESTS)
    return data if isinstance(data, dict) else {}


def mark_processed(proposal_id: str, status: str, **extra):
    data = processed_requests()
    data[proposal_id] = {
        "status": status,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        **extra,
    }
    save_manifest(PROCESSED_REQUESTS, data)


def deploy(req_path: Path, req: dict):
    old = load_manifest(ACTIVE_MANIFEST)
    pid, commit, validated = validate_request(req)

    log(f"{pid}: validation passed at commit {commit}")
    stop_active(old)

    started = []
    try:
        for comp, path in validated.items():
            proc = start_component(comp, path)
            started.append((comp, proc))
            log(f"{pid}: started {comp} pid={proc.pid}")
            time.sleep(2)
            if proc.poll() is not None:
                raise RuntimeError(f"{comp} exited immediately with code {proc.returncode}")

        if old:
            save_manifest(PREVIOUS_MANIFEST, old)

        active = {
            "proposal_id": pid,
            "commit": commit,
            "deployed_at": datetime.now().isoformat(timespec="seconds"),
            "files": {c: str(p.relative_to(ROOT)).replace("\\","/") for c,p in validated.items()},
            "pids": {c: p.pid for c,p in started},
        }
        save_manifest(ACTIVE_MANIFEST, active)

        # Never mutate the Git-tracked deployment request locally. Doing so
        # dirties the repo and blocks the next git pull. Record local lifecycle
        # state under deploy/state instead.
        mark_processed(
            pid,
            "DEPLOYED",
            commit=commit,
            deployed_at=active["deployed_at"],
        )
        # A deployed trader is not healthy until the supervisor has cycled all project services.
        # Supervisor is intentionally separate and is never terminated by this operation.
        restart_request = STATE_DIR / "restart_services.request"
        restart_result = STATE_DIR / "restart_services.result"
        restart_result.unlink(missing_ok=True)
        restart_request.write_text(pid, encoding="utf-8")
        supervisor_name = "cryptotracker_supervisor.py"
        ps = ("Get-CimInstance Win32_Process | Where-Object { "
              "$_.Name -match '^python' -and $_.CommandLine -like '*" + supervisor_name + "*' } | "
              "Select-Object -First 1 -ExpandProperty ProcessId")
        check = subprocess.run(["powershell","-NoProfile","-Command",ps],capture_output=True,text=True,timeout=20)
        if check.returncode or not check.stdout.strip():
            subprocess.Popen([sys.executable, str(ROOT / supervisor_name)],cwd=ROOT,
                             creationflags=(subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP)
                             if os.name == "nt" else 0)
        deadline = time.monotonic() + 150
        while time.monotonic() < deadline:
            if restart_result.exists():
                result = restart_result.read_text(encoding="utf-8").strip()
                if result == pid + "|OK":
                    break
                if result.startswith(pid + "|ERROR|"):
                    raise RuntimeError("Supervisor restart failed: " + result)
            time.sleep(1)
        else:
            raise RuntimeError("Supervisor did not confirm controlled restart")
        log(f"{pid}: deployment successful")
        push("CryptoTracker Deployment", f"{pid} deployed successfully.\nCommit {commit[:10]}")
        return True

    except Exception as exc:
        log(f"{pid}: deployment FAILED: {exc}")
        for _, proc in started:
            try: proc.terminate()
            except Exception: pass

        # Best-effort rollback to previous known active scripts.
        if old:
            try:
                for comp, rel in (old.get("files") or {}).items():
                    path = safe_rel(comp, rel)
                    start_component(comp, path)
                save_manifest(ACTIVE_MANIFEST, old)
                req["status"] = "ROLLED_BACK"
                log(f"{pid}: rolled back to previous release")
            except Exception as rollback_exc:
                req["status"] = "FAILED"
                req["rollback_error"] = str(rollback_exc)
                log(f"{pid}: rollback FAILED: {rollback_exc}")
        else:
            req["status"] = "FAILED"

        mark_processed(
            pid,
            req.get("status", "FAILED"),
            commit=commit,
            error=str(exc),
        )
        push("CryptoTracker Deployment FAILED", f"{pid}: {exc}")
        return False


def scan_once():
    if not AUTO_DEPLOY:
        return
    REQUEST_DIR.mkdir(parents=True, exist_ok=True)
    pull_repo()
    for path in sorted(REQUEST_DIR.glob("P-*.json")):
        try:
            req = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if req.get("status") == "READY_TO_DEPLOY":
            pid = str(req.get("proposal_id") or "")
            done = processed_requests().get(pid)
            if done and done.get("status") in {"DEPLOYED", "ROLLED_BACK"}:
                continue

            # Migration guard for deployments completed by the older agent,
            # which marked the tracked request file locally instead of using
            # deploy/state. If the active manifest already matches this exact
            # proposal+commit, treat it as processed and do not redeploy it.
            active = load_manifest(ACTIVE_MANIFEST)
            if (
                active.get("proposal_id") == pid
                and str(active.get("commit") or "") == str(req.get("commit") or "")
            ):
                mark_processed(
                    pid,
                    "DEPLOYED",
                    commit=req.get("commit"),
                    migrated_from_active_manifest=True,
                )
                continue

            deploy(path, req)


def main():
    log("Deployment agent started.")
    push("CryptoTracker Deployment Agent", "Local deployment agent is running.")
    while True:
        try:
            scan_once()
        except Exception as exc:
            log(f"scan error: {exc}")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
