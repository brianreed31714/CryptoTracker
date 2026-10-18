# CryptoTracker unattended startup (tracked installer behavior)

The current `install_cryptotracker_startup.ps1` registers the
**CryptoTracker Supervisor** scheduled task at **user logon**, with a
30-second delay, a Highest run level and Interactive logon type.
**It does not ask for a Windows password or start before logon.**
An older version of this document incorrectly described boot-time,
password-based startup.

The supervisor launches the deployment agent, active trader, Smart Money
v2.3 monitor and the read-only dashboard independently. Smart Money's
configured entrypoint is `SmartMoneyMonitor/smart_money_monitor_v2_3_feed_health_audit.py`;
the trader is selected from local active-release manifest when present.
Process command lines may be invisible to non-elevated Windows sessions.

Installer changes Windows tasks and should not be run during routine
testing. A running task is not proof that every dependent process is
healthy. For host verification use the read-only infrastructure collector:

```powershell
python -m infrastructure.registry_contract --local-safety
python -m infrastructure.runtime_inventory --write-local
```

See [operations / deployment gates](infrastructure/OPERATIONS.md) for
safety invariants, evidence and recovery. Maintain paper-only trading
and disabled Helius paid polling.
