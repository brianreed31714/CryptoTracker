# Host attestation recovery gate — 2026-10-22

## Independently observed
- The remote `cryptotracker-host-status` branch is absent (GitHub branches API 404).
- `P-20261019-01` is `READY_TO_DEPLOY`, **not verified processed on Windows**.
- `P-20261019-02` is `PENDING_HOST_VERIFICATION`; keep it there.
- Source has `deployment_agent.py` polling `windows_activation_attestation.poll` and a dedicated `host_status_publisher.publish`. Source presence does not establish that this version is running.
- Latest GitHub CI success is source-level evidence only.

## Non-disruptive recovery sequence
1. **No restart or approval-status change.** Inspect remote attestation branch and sanitized publication for a newly timestamped, Windows-origin receipt.
2. If branch remains absent, distinguish: (a) old running deployment-agent version without attestation hook, (b) attestor cannot establish code-sync/clean checkout, (c) publishing disabled by `STOCKTRACKER_ATTESTATION_REMOTE_ENABLED`, (d) Git credential or remote push denied, (e) network/scheduler/agent not running. These are hypotheses until host evidence exists.
3. The attestor currently attempts remote publish **only when** `report.code_synced` is true. A failed source-integrity check may therefore suppress all remote receipts; a missing branch alone cannot distinguish that from a stopped agent.
4. Any one-time host bootstrap must be explicitly controlled and limited to restarting/updating the **deployment agent itself** only after inspecting current process ownership and local git state. Do not restart trader, supervisor, Smart Money or dashboard to repair reporting. Do not execute an unreviewed remote command.
5. Confirm three separated process observations, expected source/active commit and process versions, healthy Smart Money heartbeat, and fresh post-sync EOD artifacts. Correlate host processed-request ledger and active-release manifest to `P-20261019-01` (do not infer from current Git HEAD).
6. Verify dependent blobs, branch CI and release-preflight checks before considering `P-20261019-02` READY. Then allow exactly one normal agent-controlled activation, verify host attestation and fresh publication, and suppress duplicate restarts/notifications.

## Fail-closed decision
If Windows-origin proof of prior request processing and running versions is absent, leave both activation confirmation and `P-20261019-02` readiness **unverified**. GitHub merge, passing CI and a paper-summary file are not substitutes. Preserve PAPER ONLY, frozen baselines, and no automatic strategy promotion.

## Known limitation
This repository cannot remotely attest to an agent that is stopped, lacks the attestation hook, or cannot push Git objects. An independent host-side signal or one-time authorized bootstrap is necessary in that case.

## 2026-10-22 confirmed root cause and fix
- Windows-host Git plumbing used Python `subprocess.run(..., text=True)` for `git mktree` stdin. Windows newline conversion stored a filename literally named `status.json` plus a carriage return, making standard GitHub `status.json` fetches return 404 despite a successful push.
- Windows directly executed the read-only attestor and pushed `5232215e5a8ec2a9436d8c52a621376c85b49dee`: `CODE_SYNCED_PROCESS_OBSERVED`, `source_code_synced=true`, `processes_stable=false`, `post_sync_eod_verified=false`. Independent GitHub tree inspection confirmed the malformed filename.
- [PR #11](https://github.com/brianreed31714/CryptoTracker/pull/11) merged as `ec3b4d059118ff06ec15ff26de9366915cbe3a0a`, after all three project CI checks passed. It sends byte-mode Git stdin, strictly accepts only an exact single-file legacy branch for fast-forward repair, and forces a one-time host-status republish upon loading the new source.
- **Still required:** confirm Windows checkout synchronizes merged main, perform a separately gated deployment-agent-only process reload (never all-services restart), verify repeated healthy host attestation and fresh post-sync EOD proof. The source-level merge is not Windows activation confirmation.
