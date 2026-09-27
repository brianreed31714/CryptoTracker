# Run this PowerShell script AS ADMINISTRATOR.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$Supervisor = Join-Path $Repo "cryptotracker_supervisor.py"
if (-not (Test-Path $Supervisor)) { throw "cryptotracker_supervisor.py not found" }
$Python = (Get-Command python.exe -ErrorAction Stop).Source
$DefaultUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
Write-Host ""
Write-Host "CryptoTracker unattended startup setup"
Write-Host "Repository: $Repo"
Write-Host "Python: $Python"
$TaskUser = Read-Host "Windows account for task [$DefaultUser]"
if ([string]::IsNullOrWhiteSpace($TaskUser)) { $TaskUser = $DefaultUser }
Write-Host "Enter the WINDOWS ACCOUNT PASSWORD for $TaskUser (not your Windows Hello PIN)."
$SecurePassword = Read-Host "Password" -AsSecureString
$BSTR = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword)
try {
  $PlainPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
  $Action = New-ScheduledTaskAction -Execute $Python -Argument ("`"" + $Supervisor + "`"") -WorkingDirectory $Repo
  $Trigger = New-ScheduledTaskTrigger -AtStartup
  $Trigger.Delay = "PT1M"
  $Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
  Register-ScheduledTask -TaskName "CryptoTracker Supervisor" -Action $Action -Trigger $Trigger -Settings $Settings -User $TaskUser -Password $PlainPassword -RunLevel Highest -Force | Out-Null
  Write-Host "Created: CryptoTracker Supervisor"
  Write-Host "Starting it now for a test..."
  Start-ScheduledTask -TaskName "CryptoTracker Supervisor"
  Start-Sleep -Seconds 3
  $Info = Get-ScheduledTaskInfo -TaskName "CryptoTracker Supervisor"
  Write-Host "LastTaskResult: $($Info.LastTaskResult)"
} finally {
  if ($BSTR -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR) }
  $PlainPassword = $null
}
