# CryptoTracker Proposals — 2026-10-31

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261031-01 — Run paired entry and exit attribution in shadow

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `paper_research evaluation protocol`
- **Current:** Model results are reported as aggregate completed-trade metrics; the supplied summary does not establish matched entries or isolate one exit variable.
- **Proposed:** In SHADOW, compare exit variants on the same eligible entries while holding entry rules fixed; report sample size, median net return, hit rate, MFE/MAE, drawdown, and estimated costs. Evaluate one exit variable at a time and do not promote a model from this study alone.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Matched shadow results may still be affected by overlapping candidates, selection bias, quote assumptions, and limited independent market regimes; apparent improvements may not transfer to live execution.
- **Evidence:**
  - Paper DIY Whale has 29 completed trades, 34.48% wins, -0.4056% median net return, and 0.5123 profit factor.
  - Shadow DIY Whale has 48 completed trades, 50.0% wins, -0.1055% median net return, and 0.7277 profit factor.
  - Several reported exit-model paper samples have only 7–8 completed trades, while larger shadow exit aggregates do not isolate exit effects from entry differences.

**Approve in ChatGPT:**

`Approve P-20261031-01`

**Decline in ChatGPT:**

`Decline P-20261031-01`

---

## P-20261031-02 — Validate Luna calibration without changing its influence

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Luna outcome calibration analysis`
- **Current:** Luna can contribute up to a 5-point bonus; no calibration or bonus change is supported by the supplied outcome sample.
- **Proposed:** Keep current Luna settings and run a shadow-only, signal-level calibration analysis that accounts for repeated 30m/60m/120m labels and compares Luna sentiment/confidence against outcomes conditional on the underlying quant setup.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Small effective sample size and confounding by the quant setup may produce unstable calibration estimates; reducing or increasing Luna influence prematurely could discard useful information or add noise.
- **Evidence:**
  - The outcome file has 108 signals and 324 labeled rows across horizons, so horizon rows are not independent observations.
  - NEUTRAL|LOW median returns are negative at 30m (n=90), 60m (n=85), and 120m (n=83), with substantial median MAE.
  - POSITIVE|MEDIUM medians are negative at each reported horizon, but each horizon has only 9–11 observations; confidence-high groups have n=1.

**Approve in ChatGPT:**

`Approve P-20261031-02`

**Decline in ChatGPT:**

`Decline P-20261031-02`

---

## P-20261031-03 — Report rejection outcomes by reason and false-positive cost

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `missed-opportunity audit`
- **Current:** The supplied daily metrics report rejection and usable-sample counts but do not provide rejection-reason-specific outcome or false-positive-cost estimates.
- **Proposed:** For SHADOW analysis, join rejected signals to accepted signals and forward outcomes by rejection reason; report horizon-specific sample sizes, median return, hit rate, MFE/MAE, and the cost of including rejected signals. Do not relax filters unless the comparison is sufficiently sampled and robust.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Outcome availability and selection may differ between accepted and rejected signals; hindsight labels and correlated token-days could overstate the value of missed opportunities.
- **Evidence:**
  - The audit contains 108 signal rows, including 92 rejected and 89 usable rejected signals.
  - The audit reports 104 30m and 98 60m samples, but the supplied metrics do not show their outcome distributions or adverse excursions.
  - Paper and shadow aggregate strategy returns are generally negative, making unmeasured false-positive costs material to any proposed relaxation.

**Approve in ChatGPT:**

`Approve P-20261031-03`

**Decline in ChatGPT:**

`Decline P-20261031-03`

---

## P-20261031-04 — Keep smart-money signals observational pending outcome validation

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `SmartMoneyMonitor campaign validation`
- **Current:** Campaign observations are available, but the supplied evidence does not establish predictive value or multi-wallet convergence; no score or entry-weight change is justified.
- **Proposed:** Continue observational tracking and evaluate campaign strength against forward outcomes only after linking independent campaigns to usable outcome samples; report coverage failures and empty scorecard periods alongside results.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Few independent campaigns and intermittent wallet-check failures may make estimated predictive value unstable or biased toward better-covered wallets.
- **Evidence:**
  - There are 53 campaign rows but only 11 unique campaigns; median campaign strength is 2.0 and multi-wallet convergence count is zero.
  - The wallet scorecard has zero rows.
  - Feed health is currently OK with 100% latest coverage, but the history includes 1,233 failed wallet checks.

**Approve in ChatGPT:**

`Approve P-20261031-04`

**Decline in ChatGPT:**

`Decline P-20261031-04`

---

## Quick commands

`Review today's CryptoTracker proposals`
