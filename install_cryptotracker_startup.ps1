# CryptoTracker logon-start installer (no Windows password required).
# Run this PowerShell script AS ADMINISTRATOR.
$ErrorActionPreference = "Stop"

$Repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$Supervisor = Join-Path $Repo "cryptotracker_supervisor.py"
if (-not (Test-Path $Supervisor)) { throw "cryptotracker_supervisor.py not found in $Repo" }

$Python = (Get-Command python.exe -ErrorAction Stop).Source
$CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$TaskName = "CryptoTracker Supervisor"

Write-Host ""
Write-Host "CryptoTracker logon startup setup"
Write-Host "Repository: $Repo"
Write-Host "Python:     $Python"
Write-Host "User:       $CurrentUser"
Write-Host ""

# Remove any old version of the task first.
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$Action = New-ScheduledTaskAction `
    -Execute $Python `
    -Argument ("`"" + $Supervisor + "`"") `
    -WorkingDirectory $Repo

$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $CurrentUser
$Trigger.Delay = "PT30S"

$Principal = New-ScheduledTaskPrincipal `
    -UserId $CurrentUser `
    -LogonType Interactive `
    -RunLevel Highest

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RestartCount 10 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Settings $Settings `
    -Force | Out-Null

Write-Host "Created scheduled task: $TaskName"
Write-Host "Trigger: At logon for $CurrentUser (30 second delay)"
Write-Host "No Windows account password was stored."
Write-Host ""
Write-Host "Starting the task now for a test..."
Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 3
$Info = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Host "LastTaskResult: $($Info.LastTaskResult)"
Write-Host ""
Write-Host "On future reboots: sign in with your PIN and CryptoTracker will start automatically."
