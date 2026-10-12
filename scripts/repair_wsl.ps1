param(
    [string]$LogDir = (Join-Path $PSScriptRoot '..\.cache\wsl-repair')
)

$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this script as Administrator to restart WslService.'
}

$LogDir = [IO.Path]::GetFullPath($LogDir)
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
$logPath = Join-Path $LogDir 'repair.log'
$resultPath = Join-Path $LogDir 'result.json'
function Write-RepairLog([string]$Message) {
    ('{0:o} {1}' -f (Get-Date), $Message) | Add-Content -LiteralPath $logPath -Encoding UTF8
}

try {
    Write-RepairLog 'Stopping Docker Desktop and WSL command clients. Images, volumes and VHD files are preserved.'
    foreach ($processName in @('Docker Desktop', 'com.docker.backend', 'com.docker.build', 'docker-desktop', 'wsl')) {
        Get-Process -Name $processName -ErrorAction SilentlyContinue |
            Stop-Process -Force -ErrorAction SilentlyContinue
    }

    Write-RepairLog 'Requesting WslService stop.'
    & sc.exe stop WslService 2>&1 | Out-String | Add-Content -LiteralPath $logPath -Encoding UTF8
    $service = Get-Service WslService
    try {
        $service.WaitForStatus('Stopped', [TimeSpan]::FromSeconds(20))
    } catch {
        # A hung service cannot process the normal stop request. Only terminate
        # the PID currently registered for WslService, after checking its name.
        $serviceInfo = Get-CimInstance Win32_Service -Filter "Name='WslService'"
        if ($serviceInfo.ProcessId -gt 0) {
            $serviceProcess = Get-Process -Id $serviceInfo.ProcessId -ErrorAction Stop
            if ($serviceProcess.ProcessName -ne 'wslservice') {
                throw 'Unexpected WslService process; refusing to terminate it.'
            }
            Write-RepairLog 'WslService stop timed out; terminating its verified service process.'
            Stop-Process -Id $serviceProcess.Id -Force
            Start-Sleep -Seconds 3
        }
    }

    $service = Get-Service WslService
    if ($service.Status -ne 'Running') { Start-Service WslService }
    $service.WaitForStatus('Running', [TimeSpan]::FromSeconds(20))
    Write-RepairLog 'WslService is running. Checking WSL distribution enumeration (25 second timeout).'

    $stdout = Join-Path $LogDir 'wsl-list.txt'
    $stderr = Join-Path $LogDir 'wsl-error.txt'
    # Start the process directly so Windows PowerShell retains its exit code,
    # including when wsl.exe exits before Start-Process returns.
    $startInfo = New-Object Diagnostics.ProcessStartInfo
    $startInfo.FileName = "$env:WINDIR\System32\wsl.exe"
    $startInfo.Arguments = '--list --verbose'
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.StandardOutputEncoding = [Text.Encoding]::Unicode
    $startInfo.StandardErrorEncoding = [Text.Encoding]::Unicode
    $check = New-Object Diagnostics.Process
    $check.StartInfo = $startInfo
    $null = $check.Start()
    $stdoutTask = $check.StandardOutput.ReadToEndAsync()
    $stderrTask = $check.StandardError.ReadToEndAsync()
    if (-not $check.WaitForExit(25000)) {
        Stop-Process -Id $check.Id -Force -ErrorAction SilentlyContinue
        throw 'WSL enumeration still timed out after restarting WslService.'
    }
    $stdoutTask.GetAwaiter().GetResult() | Set-Content -LiteralPath $stdout -Encoding UTF8
    $stderrTask.GetAwaiter().GetResult() | Set-Content -LiteralPath $stderr -Encoding UTF8
    if ($check.ExitCode -ne 0) { throw "WSL enumeration exited with code $($check.ExitCode). See wsl-error.txt." }
    Write-RepairLog 'WSL responds successfully. Docker Desktop can now be started normally.'
    @{ success = $true; completed_at = (Get-Date).ToString('o'); message = 'WSL responds successfully.' } |
        ConvertTo-Json | Set-Content -LiteralPath $resultPath -Encoding UTF8
} catch {
    Write-RepairLog $_.Exception.Message
    @{ success = $false; completed_at = (Get-Date).ToString('o'); message = $_.Exception.Message } |
        ConvertTo-Json | Set-Content -LiteralPath $resultPath -Encoding UTF8
    exit 1
}
