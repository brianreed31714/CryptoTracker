# CryptoTracker nightly project knowledge — 2026-10-20 (Pacific)

**Evidence cutoff:** newest sanitized daily publication is **2026-10-19**, generated ~20:01 Pacific on Oct 19. Oct 20 EOD not due at this review. Research only; NO live swaps.

## Daily 2026-10-19 paper scorecard

| Measure | Balanced EV | Runner Hunter | DIY Whale |
|---|---:|---:|---:|
| Completed paper exits | 8 | 9 | 19 |
| Wins / losses | 3 / 5 | 3 / 6 | 11 / 8 |
| Win rate | 37.50% | 33.33% | 57.89% |
| Realized P&L (USD) | +0.545272 | +0.156478 | +0.741383 |
| Mean net trade return | +4.54% | +2.32% | +5.20% |
| Daily realized-equity change | +3.37% | +1.07% | +5.38% |
| Daily +1% goal on realized-only proxy | hit | hit | hit |
| Daily realized-equity drawdown | 1.19% | 0.62% | 0.73% |
| Additional legacy shadow exits | 31 | 12 | 22 |

**These are NOT daily full-portfolio returns.** Open positions and quote liquidation are not valued. New PR #8 prospective variants have no verified executable/net results; raw shadow marks must not be promoted.

## Since first observed entry / campaign through 2026-10-19

| Measure | Balanced EV | Runner Hunter | DIY Whale |
|---|---:|---:|---:|
| Campaign completed exits | 140 | 64 | 152 |
| Wins / losses (derived from published win rate) | 62 / 78 | 27 / 37 | 64 / 88 |
| Campaign realized P&L (USD) | +1.734149 | -0.192191 | -0.467869 |
| Campaign mean net trade return | +0.83% | -0.40% | -0.41% |
| Since-inception realized-equity change | +11.56% | -1.28% | -3.12% |
| 1%/calendar-day compounded target | +23.24% | +11.57% | +11.57% |
| Gap to target (USD) | -1.751730 | -1.927216 | -2.202894 |
| Realized-equity max drawdown | 11.93% | 3.15% | 9.82% |
| Chronological holdout exits | 42 | 20 | 46 |
| Holdout average net trade return | +2.21% | +0.27% | +0.90% |
| Stable positive holdout | NO | NO | NO |
| Full portfolio MTM return / drawdown | UNVERIFIED | UNVERIFIED | UNVERIFIED |

## Changes since 2026-10-18

- Balanced EV daily realized P&L reversed from -$0.453126 to +$0.545272; campaign average trade return rose from +0.61% to +0.83%.
- Runner Hunter daily realized P&L reversed from -$0.073106 to +$0.156478; campaign average trade return improved from -0.97% to -0.40%.
- DIY Whale daily realized P&L improved from +$0.349249 to +$0.741383; campaign average trade return improved from -0.47% to -0.41%, still negative.
- No model is eligible for promotion. A single positive day is not evidence of stable +1% portfolio growth.

## Missed runner / execution quality

- Rejected forward-outcome evidence: 58 distinct eligible rejected signals (144 horizon observations). 13 reached >=20% MFE at 30 minutes; 3 reached >=50% MFE at 60 minutes. Overlapping horizon observations and MFE are not executable returns.
- Simulated Jupiter exits: negative estimated cost flags 3 / 6 / 7 (Balanced / Runner / DIY), and >5% cost flags 1 / 1 / 1. Optional Helius unavailable on all 8 / 9 / 19 exits. These are simulated quote estimates, not live swaps.
- DIY Whale: 14 of 20 new entries in RISK_OFF; one token had six repeated losing exits. Runner Hunter had five repeated losing exits for that token; Balanced EV two losses each in two tokens.
- Quality audit: campaign count delta vs dated exits mismatches: Balanced 10 vs 8; Runner 10 vs 9; DIY 20 vs 19. Campaign P&L deltas likewise do not match daily. Backfills/corrections are plausible but unproven; reconcile by trade identity, never call those differences daily profits.

## Deployment / pipeline / incident status

- Latest sanitized publication manifest: report_date 2026-10-19, published_at 20:01:03, source_commit 6a8e011, paper_only true.
- Main repository at 9b24d7d; latest Python validation and infrastructure contract workflows PASS. Windows host activation is NOT proven by GitHub CI.
- P-20261019-01 remains READY_TO_DEPLOY in GitHub; independently processed status not verified. Remote cryptotracker-host-status branch absent, so no host process/start-time, Smart Money heartbeat or post-sync EOD attestation available.
- P-20261019-02 remains PENDING_HOST_VERIFICATION. DO NOT change its status or trigger another restart until predecessor processed, host runtime/version repeated health, dependent blobs, CI/release gates and fresh EOD agree.
- Repository registry declares trader v11.10, research v11.10, Smart Money v2.3, dashboard v11.8.2; exact Windows active versions unverified.
- Historical publication 2026-10-13 remains missing.

## Decisions / next independent milestone

1. Keep Balanced EV, Runner Hunter, DIY Whale baselines unchanged, paper-only. PR #6 and PR #8 already merged; do not duplicate.
2. Prioritize read-only exact-size Jupiter liquidation MTM accounting with timestamp, raw quantity, fee/impact and failed/stale quote gates; deterministic tests before integration. See LIQUIDATION_MTM_ACCEPTANCE.md on this branch.
3. Then validate prospective organic-demand DIY filters, 2/3 independent runner flow observations, net-loss cooldowns and realistic profit capture against same-period frozen controls; require >=30 completed net exits per variant and multiple weeks out-of-sample.
4. Do not infer $800-$1000 hypothetical capacity from $0.75 probes; price depth and slippage separately.
5. No automatic promotion, live trading, leverage, or artificial market activity.

**Persistence:** this nightly note and MTM acceptance contract are committed to a research branch, not main. New executable module write and PR creation were blocked by safety controls; no code or trading logic change is merged or deployed.

Sources: published/daily/2026-10-19/{paper_summary.json,campaign_summary.json,quality_audit.json,manifest.json}, raw/luna_outcomes_2026-10-19.csv; issue #7; deploy/requests/P-20261019-{01,02}.json; infrastructure/registry.json.
