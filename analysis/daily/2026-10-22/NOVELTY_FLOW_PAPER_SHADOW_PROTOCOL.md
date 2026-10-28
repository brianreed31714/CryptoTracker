# Pre-registered novelty-name + organic-flow research — 2026-10-22

## Decision and scope

The 2026 external study **does not validate a positive edge** for crude or raunchy names. In a public Solana call dataset (July 1–October 14 analysis window), crude ticker calls reached 2x about 30.2% of the time versus 34.4% for other calls; these are *subsequent peaks*, not fills. A second multi-chain price-snapshot dataset also showed no clear positive edge. Neither dataset covers an unbiased complete year of executable trades.

**Action:** Add independent, *raw-mark-only* prospective DIY Whale shadow variants. Never change the existing DIY Whale, Runner Hunter, Balanced EV, or Novelty Probe execution/eligibility code. No real-money swaps, order routing, leverage, strategy auto-promotion, or altered capital allocation.

## Fixed experimental arms

All arms begin from the existing DIY Whale eligibility, scoring, exit spec and candidate stream. They start from their own empty state, use **one** simulated shadow position per arm, and independently observe the same arrival times and price lookups. They do not obtain executable swap fill quotes; these are NOT portfolio or fee-adjusted returns.

| Arm | Incremental predeclared gate |
|---|---|
| `xp_diy_control` | Existing baseline shadow control; no additional filter |
| `xp_diy_name12` | Existing paper name novelty score >=12 at entry |
| `xp_diy_organic_flow` | Liquidity >=$50,000; 5-minute volume >=$5,000; >=10 buys and >=15 total trades; buy/sell >=1.4; 5-minute volume acceleration >=1.4; positive current price |
| `xp_diy_name12_flow` | Name score >=12 AND stricter organic flow gate |
| `xp_diy_raunchy` | Text classifier matches sexual, profane, or toilet/bodily humor in token name or symbol |
| `xp_diy_raunchy_flow` | Raunchy text category AND stricter organic flow gate |

No historical parameter optimization justified these thresholds. They are intentionally **hypotheses**, not trading advice. Name score >=12 is the legacy scoring scale and should not be interpreted as linguistic originality; the name classifier is a transparent imperfect keyword heuristic, not a semantic model. Sex/profanity/toilet categories overlap. Name/symbol fields, novelty score, categories and flow decisions are captured **when the shadow entry is created**, and copied unchanged to shadow exit records even if the token later changes metadata.

The incremental flow test measures observable buying **activity**, not guaranteed organic demand. It cannot identify wash trading, creator-controlled wallets, or manipulation without independent wallet evidence. All variants inherit DIY Whale's existing safety eligibility. Missing score, liquidity or flow values fail their respective incremental gate.

## Fair-comparison and interpretation contract

- Freeze thresholds and code for the prospective observation period. Do not evaluate the new variants' hypothetical trades before their actual GitHub/Windows activation timestamps. Separate retrospective descriptive findings from prospective tests.
- Same input feed and clock; note that independent single-position capacity creates **selection/censoring differences** between arms. Their average trades are **not paired causal treatment effects**. Track exposure, rejected/qualified candidate counts and missed gains before inference.
- Publish arm-specific entries, completed exits, win rate, mean and median **raw-mark** returns, maxima, number of distinct token mints, liquidity at entry, and category exposure. Existing EOD `shadow_experiments.json` and `.md` include the new arms.
- A minimum of **30 closed exits per arm** permits preliminary review only. Prefer substantially larger samples across weeks and several market regimes, cluster inference by mint and day, and use a strict chronological holdout; assess multiple testing across naming categories.
- Do not claim execution profitability without executable entry/exit Jupiter quotations, priority fees, price impact, swap failures and current capital exposure / mark-to-market drawdown.
- No automatic promotion, no live trading or purchases. If measured performance is flat or negative after costs, retire the name-based filter.

## Deployment and evidence gates

1. GitHub branch / PR test: run `test_paper_shadow_experiments` and `test_novelty_shadow_research` plus existing CI.
2. Merge only after required checks succeed. Merge indicates **code published**, not host activation.
3. Windows activation must be independently verified from `deploy/state/active_release.json`, runtime inventory/process identity and post-sync EOD execution evidence; GitHub cannot assert these by itself.
4. The EOD reports must explicitly retain `NO_ORDERS_RAW_SHADOW_MARKS_ONLY`. Never present `net_return_pct` from `shadow_trades.csv` as fee-adjusted net P&L; the legacy column holds raw price-mark return.

## Public research references

- Solana memecoin calls dataset: https://github.com/Smurfetc/solana-memecoin-calls-dataset
- Price snapshot dataset: https://github.com/am-mong/Code-and-Dataset-for-A-Midsummer-Meme-s-Dream-
- Internal October 22 name-by-trade exploratory analysis: `published/daily/2026-10-22/raw/paper_trades.csv`

No production host installation or post-sync runtime attestation is claimed in this document.
