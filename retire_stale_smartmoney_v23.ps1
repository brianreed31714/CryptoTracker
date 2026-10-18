# One-time retirement of a verified stale Smart Money process.
# Does NOT restart the CryptoTracker supervisor, trader, dashboard, or StockTracker.
param(
  [Parameter(Mandatory=$true)]
  [int]$StalePid
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$logPath = Join-Path $root 'deploy\state\supervisor.log'
$rpcPath = Join-Path $root 'SmartMoneyMonitor\solana_public_rpc_v23.py'
if (-not (Test-Path $logPath)) { throw 'Supervisor log is missing. No process stopped.' }
if (-not (Test-Path $rpcPath)) { throw 'Public RPC module is missing. No process stopped.' }
$rpcSource = Get-Content $rpcPath -Raw
if (-not $rpcSource.Contains('"maxSupportedTransactionVersion":1')) {
  throw 'Version-1 RPC fix not present locally. No process stopped.'
}

# Match the exact launch record for this PID, not an unrelated python.exe.
$needle = 'Started Smart Money: SmartMoneyMonitor/smart_money_monitor_v2_3_feed_health_audit.py pid=' + $StalePid
$record = Get-Content $logPath | Where-Object { $_.EndsWith($needle) } | Select-Object -Last 1
if (-not $record) { throw "Supervisor launch record for PID $StalePid not found. No process stopped." }
$timestamp = ($record -split ' \| ',2)[0]
$launched = [datetime]::ParseExact($timestamp,'yyyy-MM-ddTHH:mm:ss',
                                  [Globalization.CultureInfo]::InvariantCulture)

$proc = Get-Process -Id $StalePid -ErrorAction SilentlyContinue
if (-not $proc) {
  Write-Host "Verified stale PID $StalePid has already exited; nothing stopped."
  exit 0
}
if ($proc.ProcessName -notmatch '^python(w)?$') {
  throw "PID $StalePid is not a Python process. No process stopped."
}
$seconds = [math]::Abs(($proc.StartTime - $launched).TotalSeconds)
if ($seconds -gt 90) {
  throw "PID $StalePid start time does not match supervisor launch record ($seconds seconds apart). No process stopped."
}
Write-Host "Verified old Smart Money PID $StalePid started $($proc.StartTime)."
Write-Host 'Stopping ONLY this previously launched monitor.'
try {
  Stop-Process -Id $StalePid -Force -ErrorAction Stop
} catch {
  throw "Unable to stop verified stale PID $StalePid. Windows may require elevated PowerShell: $($_.Exception.Message)"
}
Start-Sleep -Seconds 2
if (Get-Process -Id $StalePid -ErrorAction SilentlyContinue) {
  throw "PID $StalePid still appears active. Inspect manually."
}
Write-Host 'Stale Smart Money monitor stopped successfully.'
Write-Host 'Supervisor and trading engines were not restarted or intentionally interrupted.'
Write-Host 'Allow 2-3 minutes for supervised recovery, then check the fresh feed-health timestamp and wallet coverage.'
