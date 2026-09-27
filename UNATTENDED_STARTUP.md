# CryptoTracker Unattended Reboot Recovery

One long-running supervisor keeps the deployment agent, current trader, Smart Money Monitor, and dashboard alive.

Install:
1. Pull the latest GitHub changes.
2. Open PowerShell as Administrator.
3. From the CryptoTracker folder run:
   powershell -ExecutionPolicy Bypass -File .\install_cryptotracker_startup.ps1
4. Enter your Windows account password when prompted. A Windows Hello PIN is not the same as the account password.

The scheduled task is named CryptoTracker Supervisor and starts about one minute after Windows boots.
It runs under your Windows account even when you are not logged in, so Git credentials, OneDrive paths, and .env access remain available.

Optional .env.config settings:
SUPERVISOR_CHECK_SECONDS=60
SUPERVISOR_RESTART_GRACE_SECONDS=20
SUPERVISOR_BOOT_DELAY_SECONDS=45
SUPERVISOR_SMART_MONEY_SCRIPT=SmartMoneyMonitor/smart_money_monitor_v2_2_1_campaign_strength.py
SUPERVISOR_DASHBOARD_SCRIPT=cryptotracker_dashboard_v11_8_2.py
