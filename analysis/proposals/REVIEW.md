# CryptoTracker Proposals — 2026-09-26

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20260926-01 — Audit forward-outcome collection

- **Status:** READY_TO_DEPLOY
- **Type:** RESEARCH
- **Target:** `surge follow-up outcome pipeline`
- **Current:** 12 follow-up rows; all path NONE; no forward horizons found
- **Proposed:** Run a SHADOW audit that traces candidate creation, path assignment, deduplication, and scheduled 30/60/120-minute outcome capture without changing entry thresholds. Require at least 12 outcome-labeled relevant observations before proposing calibration.
- **Confidence:** HIGH
- **Recommended mode:** SHADOW
- **Risk:** Additional shadow logging may increase storage and investigation workload; an audit may also find that the empty outcomes were legitimate because no eligible signals occurred.
- **Evidence:**
  - surge_followup_log contains n=12 rows, with NONE accounting for 12 of 12
  - horizons_found is empty, so MFE, MAE, hit rates, medians, and false-positive cost cannot be computed

**Approve in ChatGPT:**

`Approve P-20260926-01`

**Decline in ChatGPT:**

`Decline P-20260926-01`

---

## P-20260926-02 — Verify smart-money feed health

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `local smart-money event and campaign pipeline`
- **Current:** SMART_MONEY_ENABLED=1 and WHALE_DISCOVERY_ENABLED=1, but daily event, campaign, and trader-performance files each contain 0 filtered rows
- **Proposed:** Run a SHADOW feed-health audit covering monitor uptime, polling, source responses, timestamp filtering, wallet coverage, and event-to-campaign propagation. Do not change campaign-strength weights or bonuses.
- **Confidence:** MEDIUM
- **Recommended mode:** SHADOW
- **Risk:** Zero rows may represent genuinely inactive tracked wallets rather than a pipeline fault, so changing scoring before the audit could create false positives.
- **Evidence:**
  - smart_money_events_v21.csv has 0 daily rows
  - smart_money_campaigns_v21.csv and trader_performance_v21.csv each have 0 daily rows, with 0 unique campaigns and 0 convergence observations

**Approve in ChatGPT:**

`Approve P-20260926-02`

**Decline in ChatGPT:**

`Decline P-20260926-02`

---

## P-20260926-03 — Create Luna outcome scorecard

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Luna confirmation calibration`
- **Current:** 0 Luna observations; current confidence thresholds and bonus limits are not empirically assessable
- **Proposed:** Keep all Luna settings unchanged and build a SHADOW scorecard linking each future Luna decision and confidence band to 30/60/120-minute MFE, MAE, and quant-only baseline outcomes. Defer calibration until at least 12 outcome-labeled confirmations exist.
- **Confidence:** HIGH
- **Recommended mode:** SHADOW
- **Risk:** Outcome attribution may be confounded by candidate selection and changing market regimes; a minimum sample of 12 remains preliminary rather than proof.
- **Evidence:**
  - luna.rows is 0
  - AI confirmation is enabled, but no daily observations exist to estimate confidence-band hit rates or incremental value over quant ranking

**Approve in ChatGPT:**

`Approve P-20260926-03`

**Decline in ChatGPT:**

`Decline P-20260926-03`

---

## P-20260926-04 — Audit missed-opportunity report generation

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `nightly false-negative review`
- **Current:** MISSED_OPPORTUNITY_REPORT_ENABLED=1, but no missed-opportunity file is listed and no forward horizons are available
- **Proposed:** Run a SHADOW audit to distinguish a valid zero-case day from missing report generation or missing forward-price outcomes. Preserve the current 20% 30-minute and 50% 60-minute MFE thresholds during the audit.
- **Confidence:** MEDIUM
- **Recommended mode:** SHADOW
- **Risk:** Forcing an output file on zero-case days could add operational noise; lowering MFE thresholds without evidence would inflate false-negative counts.
- **Evidence:**
  - files_present does not include a missed_opportunities_2026-09-26.csv file
  - horizons_found is empty, preventing measurement of false-negative count, MFE distribution, and opportunity cost

**Approve in ChatGPT:**

`Approve P-20260926-04`

**Decline in ChatGPT:**

`Decline P-20260926-04`

---

## Quick commands

`Review today's CryptoTracker proposals`
