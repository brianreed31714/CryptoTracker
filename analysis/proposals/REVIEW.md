# CryptoTracker Proposals — 2026-11-07

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261107-01 — Continue prospective cooldown comparison in shadow

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `paper_shadow cooldown variants: xp_balanced_cd60 versus xp_balanced_cd120`
- **Current:** Both variants are in shadow research; cd60 has 31 completed observations and cd120 has 29.
- **Proposed:** Keep both variants SHADOW-only and compare them prospectively on non-overlapping candidate outcomes, changing cooldown only. Report paired return differences, hit rates, drawdown, and uncertainty before considering promotion.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Shared or regime-concentrated candidates can make the apparent difference spurious; a cooldown change could also reduce opportunity frequency without improving out-of-sample returns.
- **Evidence:**
  - cd120: n=29, 51.72% wins, 1.5189% average net return, 0.0358% median net return, profit factor 1.5093, maximum drawdown 30.89%.
  - cd60: n=31, 45.16% wins, 0.8883% average net return, -1.1168% median net return, profit factor 1.3027, maximum drawdown 29.66%.
  - The apparent advantage is not conclusive because model samples may share candidates and cd120 still has a near-zero median and substantial drawdown.

**Approve in ChatGPT:**

`Approve P-20261107-01`

**Decline in ChatGPT:**

`Decline P-20261107-01`

---

## P-20261107-02 — Audit Luna confidence and direction calibration before rescoring

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Luna outcome calibration report`
- **Current:** Luna can contribute up to a 5-point bonus; no calibration change is supported by the 14 daily reviews.
- **Proposed:** In SHADOW, evaluate signal-level outcomes by Luna direction and confidence at each horizon, with distinct-signal counts and MFE/MAE; do not change the bonus or entry gates during the study.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Repeated horizons, market-regime effects, and small or imbalanced confidence buckets may create misleading calibration estimates.
- **Evidence:**
  - NEUTRAL|LOW has 56 to 58 observations per horizon, negative median returns from -5.262% to -8.180%, and median MAE from -9.588% to -13.254%.
  - POSITIVE|MEDIUM has only 5 observations per horizon and its median return declines from 1.285% at 30 minutes to -11.127% at 120 minutes.
  - The daily Luna review sample is 14, and outcomes at different horizons may reuse the same signals.

**Approve in ChatGPT:**

`Approve P-20261107-02`

**Decline in ChatGPT:**

`Decline P-20261107-02`

---

## P-20261107-03 — Expose rejected-signal outcome and false-positive costs

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `missed-opportunity and surge-follow-up reporting`
- **Current:** The audit reports 57 usable rejected signals and follow-up path counts, but the supplied summary omits stratified return, MFE/MAE, and rejection-reason outcomes.
- **Proposed:** Produce a SHADOW research report stratified by rejection reason and accepted/rejected path, including distinct-signal denominators, 30/60/120-minute return, MFE/MAE, and false-positive cost before proposing any gate adjustment.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Overlapping signals, incomplete follow-up, and outcome-window selection can bias retrospective comparisons; no entry threshold should be loosened based on counts alone.
- **Evidence:**
  - The missed-opportunity audit has 57 usable rejected signals and reports 68 30-minute and 67 60-minute outcome rows.
  - The follow-up log has 51,603 rows, but the summary reports no horizons found and no score bands.
  - Without outcome distributions and rejection reasons, rejected-signal counts cannot quantify missed upside or the cost of admitting false positives.

**Approve in ChatGPT:**

`Approve P-20261107-03`

**Decline in ChatGPT:**

`Decline P-20261107-03`

---

## Quick commands

`Review today's CryptoTracker proposals`
