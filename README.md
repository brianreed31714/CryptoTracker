# CryptoTracker

Paper-mode, multi-sleeve Solana momentum research system with a separately
supervised Smart Money/Whale observer, read-only Streamlit dashboard, and
local Windows deployment agent.

**Infrastructure source of truth:** [registry](infrastructure/registry.json)
and [architecture / operations guide](infrastructure/OPERATIONS.md).

The local `deploy/state/active_release.json` and the Windows process
inventory determine which version is actually active; GitHub HEAD alone
does **not** establish live deployment. Runtime secrets, wallet tracking
state, and deployment logs stay local and ignored.

Protected settings: `LIVE_TRADING=false`, `HELIUS_ENABLED=0`,
`SMART_MONEY_HELIUS_ENABLED=0`. No live-trading promotion is authorized.

Read-only local inventory, after a clean explicit fast-forward:

```powershell
python -m infrastructure.registry_contract --local-safety
python -m infrastructure.runtime_inventory --write-local
```

Do not restart the trading engine just to resolve a dashboard or Smart Money
status discrepancy. The infrastructure contract is checked before local
deployment-agent process replacement.
