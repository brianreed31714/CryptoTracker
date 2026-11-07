# CryptoTracker Proposals — 2026-11-05

These are the current model-improvement proposals from the nightly review.
Each proposal has a stable ID that can be used directly in ChatGPT.

## P-20261105-01 — Validate anti-chase on a matched shadow cohort

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `paper_research anti_chase evaluation`
- **Current:** Paper anti_chase: 12 completed trades, 50% wins, median net return +0.0754%, profit factor 3.2332. Shadow anti_chase: 50 completed trades, 32% wins, median -1.0657%, profit factor 0.7574.
- **Proposed:** Research only: compare anti_chase with a fixed baseline on identical candidate/time snapshots and execution assumptions; report signal-level median net return, hit rate, profit factor, drawdown, and false-positive cost. Keep both in shadow until a preregistered sample of at least 30 non-overlapping completed trades per model is available.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** Matched shadow results may still be affected by overlapping tokens, market-regime changes, or quote assumptions and may not predict live execution.
- **Evidence:**
  - The paper and shadow summaries disagree materially on anti_chase outcomes.
  - The existing paper sample is only 12 trades, and the summaries do not establish that the two cohorts are comparable.

**Approve in ChatGPT:**

`Approve P-20261105-01`

**Decline in ChatGPT:**

`Decline P-20261105-01`

---

## P-20261105-02 — Shadow-test Luna horizon decay before changing exits

- **Status:** PENDING
- **Type:** RESEARCH
- **Target:** `Luna POSITIVE|MEDIUM outcome and exit evaluation`
- **Current:** No Luna-driven exit change is established; the POSITIVE|MEDIUM group has 11 observations per reported horizon.
- **Proposed:** Research only: run a signal-level, paired shadow comparison of fixed 30-minute and 60-minute exits for this group, including net returns, MFE/MAE, and transaction costs. Keep current exit settings unchanged and collect at least 30 independent signals before considering calibration.
- **Confidence:** LOW
- **Recommended mode:** SHADOW
- **Risk:** The apparent decay may be driven by a few tokens, overlapping horizon labels, or unmodeled costs; a fixed time exit could also truncate genuine runners.
- **Evidence:**
  - For 11 POSITIVE|MEDIUM observations, the reported positive rate falls from 63.64% at 30 minutes to 27.27% at 60 minutes.
  - Median return falls from +0.471% at 30 minutes to -2.216% at 60 minutes, while median MAE worsens from -2.640% to -6.794%.

**Approve in ChatGPT:**

`Approve P-20261105-02`

**Decline in ChatGPT:**

`Decline P-20261105-02`

---

## Quick commands

`Review today's CryptoTracker proposals`
