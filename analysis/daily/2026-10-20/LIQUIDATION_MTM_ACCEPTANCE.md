# October 20 — Paper-only liquidation MTM acceptance contract

Status: **research specification, not deployed**. Issue #7. PR #6 and PR #8 are already merged; do not repeat their work. Frozen Balanced EV, Runner Hunter and DIY Whale baselines remain unchanged.

## Next independent engineering milestone

Implement a *read-only* quote-based capital-equity valuation for the three controls and prospective shadow variants. Do not infer account return from average trade return, realized-only equity, midprice, or raw shadow marks.

At each fixed UTC day boundary require a host-attested timestamped model state (starting equity, realized P&L, exact open token and raw quantity, remaining fraction, staged partial P&L), plus a fresh exact-quantity Jupiter liquidation quote. Accept a quote only when token address, raw input amount, route, fee, impact, timestamp, and observed host state agree. Reject missing, future, stale, wrong-token, wrong-quantity, failed-route, invalid-decimal, or unsupported-cost evidence as **UNPRICED**. Do not forward-fill stale marks or interpret UNPRICED as 0% return. Require independent source/provenance for quote timestamps and amount; an estimated swap is not an executed fill.

For an open position, account-equity estimate = starting capital + booked realized P&L + staged partial P&L + (net quoted liquidation proceeds - remaining position cost basis). For no open position, certify the absence of positions before treating realized equity as full equity. Do not double-count staged partial exits or closed trade proceeds.

A daily portfolio return needs two consecutive fully priced day-boundary snapshots. Since-inception return and equity-path max drawdown require an unbroken dated series; flag gaps. Compare daily result against +1% and inception against (1.01^calendar_days - 1), including idle days. Report 7/30-day capital-based windows only when sufficiently many consecutive boundaries are priced. All results are hypothetical paper estimates, not executable performance guarantees.

## Deterministic test cases required before wiring publication

1. Cash-only, state attested: priced equity equals starting capital plus realized P&L.
2. Open position with $1.50 cost and $1.20 exact-size net liquidation: equity decreases $0.30; no mark from entry price alone.
3. Partial position: account for remaining cost basis and staged partial P&L exactly once.
4. Reject future or >120-second stale quote/state, mismatched token/raw amount, missing route, invalid fee or impact, and missing token decimals.
5. No quote -> UNPRICED, never zero-return. Quote failure -> UNPRICED, never fictitious fill.
6. Missing, duplicate or unordered daily boundaries -> unavailable daily/inception returns and drawdown.
7. Two fully priced days -> correct daily ROI and goal hit; contiguous 8/31 snapshots -> correct 7/30-day windows.
8. Replay uses only information available at each boundary; no future quote leakage; never send transactions or modify baseline trading logic.

## Evidence and release blockers

- Latest sanitized publication checked: 2026-10-19 (published 20:01 Pacific); 2026-10-20 EOD is not yet due at the time of this review.
- The October 19 quality audit reports campaign-vs-daily reconciliation mismatches for all three controls.
- The remote `cryptotracker-host-status` branch does not exist as of this review, so no independently published Windows activation attestation is available.
- P-20261019-01 remains READY_TO_DEPLOY in tracked GitHub request, with no independently verified processed/host-active status.
- Keep P-20261019-02 PENDING_HOST_VERIFICATION. No duplicate restarts or approval escalation.

Next step: implement the pure valuation contract and deterministic tests on a separate paper-only PR, pass Python/Windows/registry CI, then wire sanitized snapshots without execution-path changes. No automatic strategy promotion; require >=30 completed prospective net exits per variant and several weeks of out-of-sample observations.
