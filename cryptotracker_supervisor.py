#!/usr/bin/env python3
from __future__ import annotations
import json, os, re, subprocess, sys, time
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv, dotenv_values
from project_process_control import stop_project_services, project_services

ROOT = Path(__file__).resolve().parent
STATE_DIR = ROOT / "deploy" / "state"
ACTIVE_MANIFEST = STATE_DIR / "active_release.json"
LOG_FILE = STATE_DIR / "supervisor.log"
RESTART_REQUEST = STATE_DIR / "restart_services.request"
RESTART_RESULT = STATE_DIR / "restart_services.result"
load_dotenv(ROOT / ".env.config")
load_dotenv(ROOT / ".env", override=True)
CHECK_SECONDS = int(os.getenv("SUPERVISOR_CHECK_SECONDS", "60"))
GRACE_SECONDS = int(os.getenv("SUPERVISOR_RESTART_GRACE_SECONDS", "20"))
BOOT_DELAY_SECONDS = int(os.getenv("SUPERVISOR_BOOT_DELAY_SECONDS", "45"))
SMART = os.getenv("SUPERVISOR_SMART_MONEY_SCRIPT", "SmartMoneyMonitor/smart_money_monitor_v2_2_1_campaign_strength.py").strip()
DASH = os.getenv("SUPERVISOR_DASHBOARD_SCRIPT", "cryptotracker_dashboard_v11_8_2.py").strip()
AGENT = "deployment_agent.py"
PUSH_TOKEN = (os.getenv("PUSHOVER_DEPLOY_TOKEN", "").strip() or os.getenv("PUSHOVER_CRYPTO_EOD_TOKEN", "").strip() or os.getenv("PUSHOVER_API_TOKEN", "").strip())
PUSH_USER = (os.getenv("PUSHOVER_DEPLOY_GROUP_KEY", "").strip() or os.getenv("PUSHOVER_CRYPTO_EOD_GROUP_KEY", "").strip() or os.getenv("PUSHOVER_USER_KEY", "").strip())

def log(msg):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now().isoformat(timespec='seconds')} | {msg}"
    print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as f: f.write(line + "\n")

def push(title, message):
    if not PUSH_TOKEN or not PUSH_USER: return
    try:
        requests.post("https://api.pushover.net/1/messages.json", data={"token":PUSH_TOKEN,"user":PUSH_USER,"title":title,"message":message[:1024]}, timeout=20)
    except Exception: pass

def load_json(path):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return {}

def active_trader():
    m = load_json(ACTIVE_MANIFEST)
    rel = str((m.get("files") or {}).get("trader") or "").strip()
    if rel and (ROOT / rel).exists(): return rel.replace("\\","/")
    files = list(ROOT.glob("auto_trader_with_alerts_v11_8_*.py"))
    if not files: raise FileNotFoundError("No v11.8 trader found")
    def key(p): return tuple(int(x) for x in re.findall(r"\d+", p.stem))
    return str(max(files, key=key).relative_to(ROOT)).replace("\\","/")

def command_lines():
    ps = "Get-CimInstance Win32_Process | Where-Object {$_.CommandLine} | Select-Object -ExpandProperty CommandLine"
    r = subprocess.run(["powershell","-NoProfile","-Command",ps], text=True, capture_output=True)
    return [x.strip() for x in r.stdout.splitlines() if x.strip()] if r.returncode == 0 else []

def running(marker):
    marker = Path(marker).name.lower()
    return any(marker in x.lower() for x in command_lines())

def start(rel, dashboard=False):
    path = (ROOT / rel).resolve()
    if not path.exists(): raise FileNotFoundError(rel)
    cmd = [sys.executable, "-m", "streamlit", "run", str(path)] if dashboard else [sys.executable, str(path)]
    flags = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    return subprocess.Popen(cmd, cwd=ROOT, creationflags=flags).pid

def ensure(name, rel, dashboard=False):
    if running(rel): return "RUNNING"
    log(f"{name} missing; waiting {GRACE_SECONDS}s")
    time.sleep(GRACE_SECONDS)
    if running(rel): return "RUNNING"
    pid = start(rel, dashboard)
    time.sleep(2)
    if not running(rel):
        raise RuntimeError(f"{name} process exited immediately: {rel}")
    log(f"Started {name}: {rel} pid={pid}")
    return f"STARTED pid={pid}"

def handle_restart_request():
    if not RESTART_REQUEST.exists():
        return
    request = RESTART_REQUEST.read_text(encoding="utf-8").strip()
    if not request:
        raise RuntimeError("Empty restart request")
    log(f"Controlled restart requested: {request}")
    stopped = stop_project_services("crypto")
    log(f"Stopped project service PIDs: {stopped}")
    # Refuse to start any service if cleanup was incomplete.
    if project_services("crypto"):
        raise RuntimeError("Duplicate project services still running")
    cycle(False)
    # Confirm expected trader is running, not just that spawning returned a PID.
    trader = active_trader()
    if not running(trader):
        raise RuntimeError("Trading engine not running after controlled restart")
    smart_script, smart_enabled = smart_money_settings()
    if smart_enabled and not running(smart_script):
        raise RuntimeError("Smart Money monitor did not survive controlled restart")
    RESTART_RESULT.write_text(request + "|OK",encoding="utf-8")
    RESTART_REQUEST.unlink(missing_ok=True)
    log("Controlled restart verified")

def smart_money_settings():
    config = dotenv_values(ROOT / ".env.config")
    script = str(config.get("SUPERVISOR_SMART_MONEY_SCRIPT") or SMART).strip()
    enabled = str(config.get("SMART_MONEY_MONITOR_ENABLED", os.getenv("SMART_MONEY_MONITOR_ENABLED", "0"))).strip().lower() in {"1", "true", "yes", "on"}
    return script, enabled

def cycle(notify=False):
    trader = active_trader()
    s = {}
    s["Deployment Agent"] = ensure("Deployment Agent", AGENT)
    s["Trader"] = ensure("Trader", trader)
    # Re-read repository config each cycle, so a safe opt-in is effective after git pull.
    smart_script, smart_enabled = smart_money_settings()
    s["Smart Money"] = ensure("Smart Money", smart_script) if smart_enabled else "DISABLED (credit protection)"
    s["Dashboard"] = ensure("Dashboard", DASH, True)
    if notify:
        msg = ["CryptoTracker supervisor online.", f"Trader: {trader}"] + [f"{k}: {v}" for k,v in s.items()]
        push("CryptoTracker Startup", "\n".join(msg))

def main():
    log(f"Supervisor starting; boot delay {BOOT_DELAY_SECONDS}s")
    time.sleep(max(0, BOOT_DELAY_SECONDS))
    try: cycle(True)
    except Exception as exc:
        log(f"Initial startup error: {exc}")
        push("CryptoTracker Startup FAILED", str(exc))
    while True:
        try:
            if RESTART_REQUEST.exists():
                handle_restart_request()
            else:
                cycle(False)
        except Exception as exc:
            log(f"Supervisor cycle error: {exc}")
            if RESTART_REQUEST.exists():
                request = RESTART_REQUEST.read_text(encoding="utf-8").strip()
                RESTART_RESULT.write_text(request + "|ERROR|" + str(exc)[:300], encoding="utf-8")
                RESTART_REQUEST.unlink(missing_ok=True)
        time.sleep(max(15, CHECK_SECONDS))

if __name__ == "__main__": main()
