# CryptoTracker Proposals — 2026-11-19

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261119-01 — Validate outcome attribution before strategy changes

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Daily research outcome joins and reporting`
- **Current:** Follow-up horizons_found is empty; Luna outcomes have 0 rows; trade metrics have 0 buys and sells; the missed-opportunity audit reports 46 usable rejected signals without outcome aggregates in the supplied metrics.
- **Proposed:** In RESEARCH/SHADOW, validate token-and-time joins and report 30/60/120-minute MFE/MAE, accepted-versus-rejected outcomes, execution costs where available, exit reasons, and adjudicated Luna labels. Do not change thresholds or live behavior as part of this work.
- **Confidence:** HIGH
- **Recommended mode:** SHADOW
- **Risk:** Join or labeling errors could produce misleading outcome attribution; results must be audited and treated as exploratory before informing strategy decisions.
- **Evidence:**
  - The 60,593 follow-up rows have no reported outcome horizons, preventing hit-rate and MFE/MAE analysis.
  - Luna has 7 reviews but 0 labeled outcome rows.
  - The missed-opportunity audit has 46 usable rejected signals but no supplied outcome summary.
  - There are no live trades from which to estimate realized execution or exit costs.

**Approve in ChatGPT:**

`Approve P-20261119-01`

**Decline in ChatGPT:**

`Decline P-20261119-01`

---

## P-20261119-02 — Continue one-variable runner-exit comparison in shadow

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `xp_runner_early_trail versus xp_runner_control shadow experiment`
- **Current:** Each variant has 16 completed observations. Early trail has a 56.25% win rate and 4.1919% median return; control has a 50.0% win rate and 0.2459% median return. Both report 0 realized PnL.
- **Proposed:** Keep both variants in SHADOW, verify whether their token-event cohorts are comparable, and extend the comparison with all entry settings held constant. Include costs and drawdown uncertainty; do not promote either variant based on the current sample.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** The apparent difference may reflect small-sample variation, cohort overlap, or shadow pricing that omits executable costs; treating it as a proven exit improvement could increase losses.
- **Evidence:**
  - Early trail's observed median return is higher than control's (4.1919% versus 0.2459%) on 16 observations per variant.
  - The win-rate difference is modest (56.25% versus 50.0%), and the samples may overlap.
  - Both variants have substantial reported max drawdown (36.2029% and 39.4469%), and shadow realized PnL is 0.

**Approve in ChatGPT:**

`Approve P-20261119-02`

**Decline in ChatGPT:**

`Decline P-20261119-02`

---

## Quick commands

`Review today's CryptoTracker proposals`
