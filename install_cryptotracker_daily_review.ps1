# Opt-in CryptoTracker daily research review scheduler.
# This installer does not start, stop, or restart any trading process.
# Run manually as the Windows account that owns the existing CryptoTracker tasks.
$ErrorActionPreference = "Stop"

$Repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$ReviewBat = Join-Path $Repo "run_daily_model_review.bat"
$TaskName = "CryptoTracker Daily Review"
$CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

if (-not (Test-Path -LiteralPath $ReviewBat -PathType Leaf)) {
    throw "Missing CryptoTracker daily review batch file."
}
# The batch selects the prior completed Pacific day; require the intended host zone.
if ((Get-TimeZone).Id -ne "Pacific Standard Time") {
    throw "Host timezone must be Pacific Standard Time before installing the 6:05 PM review."
}

$Existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($Existing) {
    throw "Daily review task already exists; refusing to replace its definition."
}

$Principal = New-ScheduledTaskPrincipal -UserId $CurrentUser -LogonType Interactive -RunLevel Highest
$Trigger = New-ScheduledTaskTrigger -Daily -At 6:05PM
$Action = New-ScheduledTaskAction -Execute $env:ComSpec -Argument ('/d /c ""' + $ReviewBat + '""') -WorkingDirectory $Repo
# Preserve the proposed 6:05 PM cadence; do not silently add catch-up runs.
$Settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings | Out-Null

Write-Host "Installed $TaskName at 6:05 PM Pacific daily for $CurrentUser."
Write-Host "Task registration is NOT proof of execution, GitHub publication, or Pushover delivery."
Write-Host "No task was started, no trading process was restarted, and no live trading was enabled."
