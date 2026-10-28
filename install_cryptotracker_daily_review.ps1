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
# The batch uses the host's local calendar date; refuse to silently schedule
# a partial-day report at the wrong local time.
if ((Get-TimeZone).Id -ne "Pacific Standard Time") {
    throw "Host timezone must be Pacific Standard Time before installing the 6:05 PM review."
}

$Existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($Existing -and $Existing.State -eq "Running") {
    throw "Daily review task is running; refusing to replace its definition."
}

$Principal = New-ScheduledTaskPrincipal -UserId $CurrentUser -LogonType Interactive -RunLevel Highest
$Trigger = New-ScheduledTaskTrigger -Daily -At 6:05PM
$Action = New-ScheduledTaskAction -Execute $env:ComSpec -Argument ('/d /c ""' + $ReviewBat + '""') -WorkingDirectory $Repo
# Do not catch up a missed 6:05 PM run the next morning: the batch defaults
# to today's date and that would publish a misleading partial-day snapshot.
$Settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force | Out-Null

Write-Host "Installed $TaskName at 6:05 PM Pacific daily for $CurrentUser."
Write-Host "Task registration is NOT proof of execution, GitHub publication, or Pushover delivery."
Write-Host "No task was started, no trading process was restarted, and no live trading was enabled."
