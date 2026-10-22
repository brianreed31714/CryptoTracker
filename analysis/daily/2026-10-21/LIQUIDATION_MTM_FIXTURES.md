# Paper-only liquidation MTM: deterministic fixture and data contract (2026-10-21)

Issue #7 · Follow-up to the existing October 20 acceptance contract · **Documentation only; not implemented or deployed**.

## New objective milestone

Specify exact input fields and numerical acceptance fixtures for a pure, read-only liquidation-equity module. No existing Balanced EV, Runner Hunter or DIY Whale entry/exit logic is changed. PR #6 and PR #8 are already merged and must not be reimplemented. New PR #8 variants remain **UNPRICED raw shadow marks** and are not promotion evidence.

## Required sanitized, host-attested boundary record

At each **00:00:00 UTC** day boundary, publish only when independently evidenced:

- `boundary_utc`, `observed_at_utc` (UTC with offset), `state_attested=true`, `positions_complete=true`, `paper_only=true`, `source_commit`, and immutable provenance identifying the active paper model version
- `starting_capital_usd`, `booked_closed_pnl_usd`, `staged_partial_pnl_usd` with explicit rule that the booked figure excludes the staged partial amount; otherwise fail closed
- `quote_currency_mint` (actual USDC mint), `open_positions` containing `token_address`, `remaining_quantity_raw`, `token_decimals`, `remaining_cost_basis_usd`
- One read-only Jupiter liquidation quote per open position: `input_token_address`, `input_amount_raw`, `output_token_address`, `output_decimals`, `output_amount_raw`, `route_id`, `observed_at_utc`, `quote_success`, `additional_fee_usd`, `price_impact_pct`, and a failed-fill/no-route indicator
- All quote amounts are raw integers, all dollar amounts decimal strings, all timestamps timezone-aware; quote output already incorporates route price impact, so **do not subtract impact twice**
- The quote must precede the boundary by no more than 120 seconds, and never be from the future. No stale price forward fill; quote failures, missing decimals, wrong tokens/quantities, negative fees, or invalid impact => **UNPRICED**, not zero return
- Explicit signed source of timestamps and quote provenance is necessary before these values can be trusted. No actual swap is performed.

## Numerical fixture set (expected results)

| Fixture | Starting USD | Closed P&L | Staged P&L | Remaining cost | Net liquidation proceeds | Expected equity |
|---|---:|---:|---:|---:|---:|---:|
| Attested cash-only, no positions | 15.00 | +0.50 | 0.00 | 0.00 | 0.00 | 15.50 |
| Open losing position | 15.00 | 0.00 | 0.00 | 1.50 | 1.20 | 14.70 |
| Partial exit booked separately | 15.00 | 0.00 | +0.20 | 0.75 | 0.60 | 15.05 |
| Same partial exit already included in booked P&L | 15.00 | +0.20 | 0.00 | 0.75 | 0.60 | 15.05 |
| Partial P&L included in both fields | — | — | — | — | — | **REJECT** (ambiguous double count) |
| Wrong raw token quantity | — | — | — | — | — | **UNPRICED** |
| Missing/failed Jupiter route | — | — | — | — | — | **UNPRICED** |
| Quote timestamp 121 seconds old | — | — | — | — | — | **UNPRICED** |
| Quote timestamp 1 second after boundary | — | — | — | — | — | **UNPRICED** |
| Missing token decimals | — | — | — | — | — | **UNPRICED** |

For every open position: equity = starting capital + booked closed P&L + staged partial P&L + (net exact-size liquidation proceeds - remaining cost basis). **The input is a hypothetical liquidation quote, not an executed fill or a guaranteed realizable exit.** A cash-only equity mark requires an explicit complete/empty position inventory.

## Time-series acceptance

- Require consecutive, unique, ascending, fully priced UTC-midnight snapshots from the declared inception boundary. A missing day, duplicate boundary, unpriced position, or later restatement makes affected since-inception return and max drawdown unavailable.
- Daily capital return requires two consecutive fully priced boundaries; seven-day and thirty-day returns require respectively 8 and 31 consecutive priced boundaries. An idle day is still part of the 1%-per-calendar-day target.
- Example: $15.00 -> $15.15 over one day = +1.00% daily capital return, target hit. A third consecutive boundary at $15.00 = -0.990099% daily, cumulative 0%, and max drawdown 0.990099%.
- The since-inception target is `(1.01 ** elapsed_calendar_days - 1) * 100`, **not** compounded trade returns. Missing price => target status **UNKNOWN**, never fail or pass by assumption.
- Stop overrun, stale quote, failed fill, no-route, slippage and $0.75/$100/$800/$1000 hypothetical size tests remain independent prospective research, not baseline strategy changes.

## Evidence and deployment gates

As of October 21 17:59 Pacific, latest sanitized report is dated **2026-10-20**; it does not provide verifiable liquidation portfolio returns. `cryptotracker-host-status` branch and `status.json` remain absent. The existing `P-20261019-01` request remains `READY_TO_DEPLOY` without independent Windows processing evidence. Therefore `P-20261019-02` remains **PENDING_HOST_VERIFICATION**; no activation, promotion, or restart is authorized.

Next engineering work: implement these fixtures as deterministic tests and a pure quote valuation library, then independently review and pass Python, Windows, registry and release gates. Publication wiring must not touch trading execution paths. No user-run PowerShell reconciliation should be necessary.
