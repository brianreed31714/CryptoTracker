# CryptoTracker infrastructure architecture and operations contract

This file describes the **repository design**, not a claim that every service is running on the Windows trading PC. The machine-readable authority for code relationships is [registry.json](registry.json). Actual runtime evidence is created by `runtime_inventory.py` on that PC only. The runtime manifest, credentials, databases and logs remain local.

## Component boundaries

| Component | Entrypoint or resolution | Process owner | Responsibility |
|---|---|---|---|
| Supervisor | `cryptotracker_supervisor.py` | Scheduled task: CryptoTracker Supervisor | Starts/restarts services |
| Deployment agent | `deployment_agent.py` | Supervisor | Git sync, request validation, release records |
| Trader | Active-release manifest, example `auto_trader_with_alerts_v11_10_research_fairness.py` | Supervisor | Paper trading and scanner |
| Smart Money v2.3 | `SmartMoneyMonitor/smart_money_monitor_v2_3_feed_health_audit.py` | Supervisor / config | Wallet observation, campaigns, feed-health heartbeat |
| Solana RPC observer | `SmartMoneyMonitor/solana_public_rpc_v23.py` | Smart Money library | Public read-only RPC |
| Dashboard | `cryptotracker_dashboard_v11_8_2.py` | Supervisor | Read-only status and research |
| Daily review | `run_daily_model_review.bat` | Trader / scheduled workflow | Paper performance/evidence |

## Provider and data dependencies

`registry.json` lists outbound providers, whether they are paper/read-only, local evidence files, producer/consumer relationships, and freshness semantics. A component may be *alive but not healthy* or *invisible to Windows command-line inspection but writing healthy heartbeats*. We test these separately.

## Existing knowledge gaps (do not guess)

- The Windows run previously showed Smart Money PID 3096 and 4/4 wallets as a **past observation**, not a persistent expected PID.
- The dashboard now trusts v2.3's heartbeat (within 360 seconds); it does not prove a particular PID.
- The configured SMART_MONEY script is v2.3; active trader selection follows the local release manifest, then the supervisor fallback.
- Helius and paid Smart Money polling are disabled by tracked configuration. Never enable automatically.
- Crypto EOD is implemented in the trader and reporting workflow; data activity is not equivalent to an independently running EOD process.

## Non-negotiable operating constraints

`LIVE_TRADING=false`, `HELIUS_ENABLED=0`, and `SMART_MONEY_HELIUS_ENABLED=0` must remain effective. The local `.env` must not override them to true. `SmartMoneyMonitor/traders.json` and wallet credentials remain local, ignored, and never uploaded.

## Local host inventory (read-only)

After a clean fast-forward to the exact expected `origin/main`, run from the respective repository root in PowerShell:

```powershell
python -m infrastructure.registry_contract --local-safety
python -m infrastructure.runtime_inventory --write-local
```

The latter inspects Windows scheduled-task metadata, non-secret Python process identity and start time, local active manifest, HEAD commit, and declared heartbeat files. The output `deploy/state/infrastructure_inventory.json` is **gitignored**, never auto-committed or sent to GitHub. It deliberately never writes raw command lines, usernames, secret values, or wallet addresses. If process command lines are hidden, PID attribution requires a matching supervisor launch record *and* start time; otherwise the identity stays UNKNOWN.

A green GitHub Action alone establishes **code/test validation only**, not live deployment. The host inventory is an observation, not proof of successful trading or sustained service health.

## Local release preflight and safety gate

Both local deployment agents invoke `release_preflight()` from [registry_contract.py](registry_contract.py) in `validate_request` before calling `stop_active` or issuing a controlled restart. The gate rejects:
- Missing/invalid/inconsistent component registry or declared source files;
- Missing configured entrypoints or invalid component script families;
- Missing trader paper-only markers and forbidden locally enabled safety flags;
- Requests naming undeclared components or duplicate components;
- Syntax errors in proposed release modules and their declared dependencies.

The pre-existing deployment agents **also** guard component-specific capabilities and Git release blob identity. A deployment request must be explicitly approved before any process replacement; a green test run is not approval.

Both deployment agents use explicit `git fetch origin main` + `git merge --ff-only origin/main`, rather than ambiguous `git pull`. A non-fast-forward or unexpected local code change must stop deployment.

## Verification discipline / exit criteria

1. **Plan:** identify source owner and downstream consumers with `change_impact()`; note unowned Python modules explicitly.
2. **Test:** validate architecture and paper safety; run Python negative tests on Linux and Windows; run project-specific regression tests; no credentials in CI.
3. **Approve:** code review and explicit release request; do not auto-enable live trading or paid feeds.
4. **Deploy:** local agent verifies source blob and registry before touching a running process; preserve previous manifest and rollback plan.
5. **Verify on the host:** compare manifest/commit and start times, scheduled task and component identity, dashboard status, and required data-feed heartbeat. Require repeated successful observation after startup (not just one good JSON report).
6. **Report:** declare "code committed", "CI validated", "host observed", or "release verified" separately. Never collapse those into "deployed successfully" without host evidence.

The repository does **not yet** contain a fully proven autonomous deployment-attestation loop for every service. Treat any unresolved runtime verification as `UNVERIFIED`, not success. In particular, the existing supervisor success handshake primarily verifies processes, not three independent healthy operating cycles.

## Incident / dependency protocol

When a status is incorrect, compare its data source with producer output before restarting. Verify PID start time and process ownership before stopping anything. Stop only the affected component with minimal privilege. Do not restart healthy trading engines to repair a dashboard or auxiliary feed. When a test fails, capture the precise failing path, build log and expected runtime evidence; never suppress the failure to make CI green.

## Updating the contract

Any change that adds, renames, retires, or reconnects a component must update `registry.json`, source ownership, dependencies, data/provider contracts, negative tests, and this document in the same release. The registry is checked on every main-branch change affecting infrastructure and on deployment preflight. CI branch-protection settings must be verified separately; a GitHub Action cannot guarantee branch blocking without repository rules.
