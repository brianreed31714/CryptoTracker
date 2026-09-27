# CryptoTracker Proposals — 2026-09-26

These are the current model-improvement proposals from the nightly review.
P-01 through P-04 are approved for SHADOW research and bundled into one safe full-release deployment.

## P-20260926-01 — Audit forward-outcome collection

- **Status:** READY_TO_DEPLOY
- **Type:** RESEARCH
- **Target:** `surge follow-up outcome pipeline`
- **Current:** 12 follow-up rows; all path NONE; no forward horizons found
- **Proposed:** Run a SHADOW audit that traces candidate creation, path assignment, deduplication, and scheduled 30/60/120-minute outcome capture without changing entry thresholds. Require at least 12 outcome-labeled relevant observations before proposing calibration.
- **Confidence:** HIGH
- **Recommended mode:** SHADOW
- **Deployment:** BUNDLED via `P-20260926-04`
- **Risk:** Additional shadow logging may increase storage and investigation workload; an audit may also find that the empty outcomes were legitimate because no eligible signals occurred.
- **Evidence:**
  - surge_followup_log contains n=12 rows, with NONE accounting for 12 of 12
  - horizons_found is empty, so MFE, MAE, hit rates, medians, and false-positive cost cannot be computed

---

## P-20260926-02 — Verify smart-money feed health

- **Status:** READY_TO_DEPLOY
- **Type:** RESEARCH
- **Target:** `local smart-money event and campaign pipeline`
- **Current:** SMART_MONEY_ENABLED=1 and WHALE_DISCOVERY_ENABLED=1, but daily event, campaign, and trader-performance files each contain 0 filtered rows
- **Proposed:** Run a SHADOW feed-health audit covering monitor uptime, polling, source responses, timestamp filtering, wallet coverage, and event-to-campaign propagation. Do not change campaign-strength weights or bonuses.
- **Confidence:** MEDIUM
- **Recommended mode:** SHADOW
- **Deployment:** BUNDLED via `P-20260926-04`
- **Risk:** Zero rows may represent genuinely inactive tracked wallets rather than a pipeline fault, so changing scoring before the audit could create false positives.
- **Evidence:**
  - smart_money_events_v21.csv has 0 daily rows
  - smart_money_campaigns_v21.csv and trader_performance_v21.csv each have 0 daily rows, with 0 unique campaigns and 0 convergence observations

---

## P-20260926-03 — Create Luna outcome scorecard

- **Status:** READY_TO_DEPLOY
- **Type:** RESEARCH
- **Target:** `Luna confirmation calibration`
- **Current:** 0 Luna observations; current confidence thresholds and bonus limits are not empirically assessable
- **Proposed:** Keep all Luna settings unchanged and build a SHADOW scorecard linking each future Luna decision and confidence band to 30/60/120-minute MFE, MAE, and quant-only baseline outcomes. Defer calibration until at least 12 outcome-labeled confirmations exist.
- **Confidence:** HIGH
- **Recommended mode:** SHADOW
- **Deployment:** BUNDLED via `P-20260926-04`
- **Risk:** Outcome attribution may be confounded by candidate selection and changing market regimes; a minimum sample of 12 remains preliminary rather than proof.
- **Evidence:**
  - luna.rows is 0
  - AI confirmation is enabled, but no daily observations exist to estimate confidence-band hit rates or incremental value over quant ranking

---

## P-20260926-04 — Audit missed-opportunity report generation

- **Status:** READY_TO_DEPLOY
- **Type:** RESEARCH
- **Target:** `nightly false-negative review`
- **Current:** MISSED_OPPORTUNITY_REPORT_ENABLED=1, but no missed-opportunity file is listed and no forward horizons are available
- **Proposed:** Run a SHADOW audit to distinguish a valid zero-case day from missing report generation or missing forward-price outcomes. Preserve the current 20% 30-minute and 50% 60-minute MFE thresholds during the audit.
- **Confidence:** MEDIUM
- **Recommended mode:** SHADOW
- **Deployment:** READY_TO_DEPLOY via `P-20260926-04`
- **Risk:** Forcing an output file on zero-case days could add operational noise; lowering MFE thresholds without evidence would inflate false-negative counts.
- **Evidence:**
  - files_present does not include a missed_opportunities_2026-09-26.csv file
  - horizons_found is empty, preventing measurement of false-negative count, MFE distribution, and opportunity cost

---

## Combined release

`P-20260926-04` is the single deployment request for P-01 through P-04. It starts the updated trader, Smart Money monitor, and existing dashboard together so one partial deployment cannot stop the other components.

No trading thresholds, sizing, entry/exit logic, or execution gates are changed by this SHADOW release.
