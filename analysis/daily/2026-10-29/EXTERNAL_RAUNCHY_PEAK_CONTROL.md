# External raunchy-ticker historical peak comparison — 2026-10-29

**PAPER / READ-ONLY / DESCRIPTIVE. NOT A TRADING BACKTEST.**

## Evidence and methodology

- Source: [Smurfetc public CC0 Solana calls](https://github.com/Smurfetc/solana-memecoin-calls-dataset), Git blob `0e59010a6c98892ad18c4490e609fa6cc4698e5c`; 11,171 unique mints, June 30–October 29, 2026.
- Reused the three **frozen** raunchy regex categories from `research/external_raunchy_flow_audit.py` (equivalent to the shadow research classifier) on ticker text available at call time. No retrospective classifier fitting.
- Outcome is whether the **future observed peak** reached 2x or 3x the caller's reference market cap. It is **not** a realizable sale price, strategy exit, ROI, or fill.
- The caller-selected sample is not an unbiased population of all Solana launches or our DIY Whale candidate stream. Recent calls have shorter observation windows. No time-indexed 5-minute buy/sell, acceleration, liquidity, wallet-attribution, quote, or exit-path evidence.

## Independent observations

| Group | Calls | Later peak >=2x | >=2x rate | Later peak >=3x | >=3x rate |
|---|---:|---:|---:|---:|---:|
| Raunchy ticker | 197 | 60 | 30.46% | 35 | 17.77% |
| Other ticker | 10,974 | 3,902 | 35.56% | 2,368 | 21.58% |

Difference in 2x incidence: **−5.10 percentage points**. Approximate unadjusted normal 95% CI: **[−11.59,+1.39] pp**. This does **not** establish a statistically reliable effect or trading edge. Median future peak 1.502x for matched versus 1.582x for other calls.

| Calendar slice | Raunchy >=2x | Other >=2x | Difference |
|---|---:|---:|---:|
| July–August | 35/107 (32.71%) | 2,139/5,943 (35.99%) | −3.28 pp |
| September–October | 25/90 (27.78%) | 1,749/5,017 (34.86%) | −7.08 pp |

The later calendar slice is **descriptive chronological separation, not independent prospective predictive validation**. Its approximate unadjusted 95% difference interval is [−16.43,+2.26] pp. October observations are right-censored. Month + market-cap bucket standardization gives a control reference of 34.91% against 30.46% observed for raunchy tickers (−4.45 pp); still descriptive and not causal.

Overlapping frozen categories: sexual 20/95 (21.05%) later 2x, profanity 14/39 (35.90%), toilet 27/72 (37.50%). Categories are not mutually exclusive and multiple comparisons were not adjusted.

## Fail-closed trading conclusions

- **Frozen `xp_diy_raunchy_flow` eligibility:** MISSING; the dataset lacks five-minute volume, buy/sell counts, liquidity and acceleration, plus DIY Whale baseline eligibility.
- **Six-month coverage:** MISSING for April 29–June 29, 2026; this source begins June 30.
- **Quote-net returns, true portfolio ROI, drawdown, stop behavior and prospective out-of-sample edge:** MISSING.
- **Promotion:** NOT AUTHORIZED. No changes to paper baselines, risk, live swaps, Jupiter V2 or Windows processes.

The separately inspected [June 10–30 GMGN dataset](https://github.com/ian05012/solana-memecoin-dataset) offers 44,460 snapshots, 9.5 million trades and 15-minute candles, but only a 20-day regime and no guaranteed executable quotes. A proper replay must reconstruct strictly prior-to-entry flow and independent executable exits before computing ROI.

Reproduction: `python -m research.external_raunchy_peak_comparison --input calls.jsonl --output external_raunchy_peak_comparison.json`. The workflow produces a dated immutable artifact when GitHub Actions jobs can actually start; local deterministic tests passed before PR creation. **GitHub CI and merge remain separate gates.**
