# Controlled local activation of Smart Money v2.3 on the CryptoTracker PC.
# Never enables Helius, sends trades, or changes live-trading settings.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host 'Checking CryptoTracker Git synchronization...'
git pull --ff-only
if ($LASTEXITCODE -ne 0) { throw 'Git pull failed. Supervisor was not restarted.' }

$config = Get-Content (Join-Path $root '.env.config')
foreach ($expected in @(
  'HELIUS_ENABLED=0',
  'SMART_MONEY_HELIUS_ENABLED=0',
  'SMART_MONEY_MONITOR_ENABLED=1',
  'SMART_MONEY_SOLANA_PUBLIC_RPC_ENABLED=1',
  'SUPERVISOR_SMART_MONEY_SCRIPT=SmartMoneyMonitor/smart_money_monitor_v2_3_feed_health_audit.py'
)) {
  if ($config -notcontains $expected) { throw "Expected configuration missing: $expected" }
}
$wallets = Join-Path $root 'SmartMoneyMonitor\traders.json'
if (-not (Test-Path $wallets)) { throw "Tracked wallet list missing: $wallets. No restart performed." }

Write-Host 'Running offline safety tests...'
python -m unittest -v test_solana_public_rpc_v23
if ($LASTEXITCODE -ne 0) { throw 'Offline tests failed. No restart performed.' }

Write-Host 'Checking public Solana RPC connectivity...'
python -c "from SmartMoneyMonitor.solana_public_rpc_v23 import rpc; slot=rpc('getSlot',[{'commitment':'confirmed'}]); assert isinstance(slot,int) and slot>0; print('Public Solana RPC slot:',slot)"
if ($LASTEXITCODE -ne 0) { throw 'Public Solana RPC unavailable. No restart performed.' }

$taskName = 'CryptoTracker Supervisor'
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
$started = Get-Date
Write-Host "Restarting scheduled task: $taskName"
Stop-ScheduledTask -TaskName $taskName
Start-Sleep -Seconds 5

# Stop ONLY the Smart Money v2.3 Python process so the updated RPC code
# is loaded. Do not stop the trader, dashboard, or unrelated Python processes.
$oldMonitors = @(Get-CimInstance Win32_Process | Where-Object {
  $_.Name -match '^python(w)?(\.exe)?

$healthPath = Join-Path $root 'SmartMoneyMonitor\data\smart_money_feed_health_v23.json'
$deadline = (Get-Date).AddMinutes(5)
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Seconds 5
  $process = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^python(w)?(\.exe)?$' -and
    $_.CommandLine -like '*smart_money_monitor_v2_3_feed_health_audit.py*'
  })
  if ($process.Count -gt 0 -and (Test-Path $healthPath)) {
    $item = Get-Item $healthPath
    if ($item.LastWriteTime -gt $started) {
      $health = Get-Content $healthPath -Raw | ConvertFrom-Json
      Write-Host "Monitor process(es): $($process.Count); feed health: $($health.status)"
      Write-Host "Wallet checks: $($health.successful_wallet_checks)/$($health.tracked_wallets)"
      if ($health.status -eq 'OK') {
        Write-Host 'Smart Money v2.3 is running with healthy public RPC feeds.' -ForegroundColor Green
        exit 0
      }
      throw "Smart Money feed health is $($health.status): $($health.last_error)"
    }
  }
}
throw 'No fresh healthy Smart Money feed report within 5 minutes. Inspect deploy/state/supervisor.log and SmartMoneyMonitor/data/smart_money_feed_health_v23.json.'
 -and
  $_.CommandLine -like '*smart_money_monitor_v2_3_feed_health_audit.py*'
})
foreach ($monitor in $oldMonitors) {
  Write-Host "Stopping old Smart Money monitor PID $($monitor.ProcessId)"
  Stop-Process -Id $monitor.ProcessId -Force -ErrorAction Stop
}
Start-Sleep -Seconds 3

Start-ScheduledTask -TaskName $taskName

$healthPath = Join-Path $root 'SmartMoneyMonitor\data\smart_money_feed_health_v23.json'
$deadline = (Get-Date).AddMinutes(5)
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Seconds 5
  $process = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^python(w)?(\.exe)?$' -and
    $_.CommandLine -like '*smart_money_monitor_v2_3_feed_health_audit.py*'
  })
  if ($process.Count -gt 0 -and (Test-Path $healthPath)) {
    $item = Get-Item $healthPath
    if ($item.LastWriteTime -gt $started) {
      $health = Get-Content $healthPath -Raw | ConvertFrom-Json
      Write-Host "Monitor process(es): $($process.Count); feed health: $($health.status)"
      Write-Host "Wallet checks: $($health.successful_wallet_checks)/$($health.tracked_wallets)"
      if ($health.status -eq 'OK') {
        Write-Host 'Smart Money v2.3 is running with healthy public RPC feeds.' -ForegroundColor Green
        exit 0
      }
      throw "Smart Money feed health is $($health.status): $($health.last_error)"
    }
  }
}
throw 'No fresh healthy Smart Money feed report within 5 minutes. Inspect deploy/state/supervisor.log and SmartMoneyMonitor/data/smart_money_feed_health_v23.json.'
