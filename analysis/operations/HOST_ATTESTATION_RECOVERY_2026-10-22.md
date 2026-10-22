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
