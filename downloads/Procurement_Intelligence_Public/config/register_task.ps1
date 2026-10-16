param([Parameter(Mandatory=$true)][string]$PythonExe,[Parameter(Mandatory=$true)][string]$ProjectRoot)
# Run explicitly on your own Windows machine; not installed by this package.
$Arguments = '"' + (Join-Path $ProjectRoot 'scheduled_refresh.py') + '" "' + (Join-Path $ProjectRoot 'config\schedule.json') + '"'
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument $Arguments -WorkingDirectory $ProjectRoot
$Trigger = New-ScheduledTaskTrigger -Daily -At '08:00'
$Settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable
Register-ScheduledTask -TaskName 'ProcurementExportRefresh' -Action $Action -Trigger $Trigger -Settings $Settings -Description 'Validates authorised local exports; no website scraping or orders.'
