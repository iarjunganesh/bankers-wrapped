# Stop the Banker's Wrapped demo stack
# Usage: .\scripts\stop_demo.ps1

$ROOT = Split-Path $PSScriptRoot -Parent
$LOGS = Join-Path $ROOT "logs"

function Stop-ByPidFile {
    param([string]$PidFile, [string]$Label)
    if (Test-Path $PidFile) {
        $id = [int](Get-Content $PidFile -Raw).Trim()
        try {
            Stop-Process -Id $id -Force -ErrorAction Stop
            Write-Host "Stopped $Label (PID $id)"
        } catch {
            Write-Host "$Label (PID $id) was already stopped."
        }
        Remove-Item $PidFile -Force
    } else {
        Write-Host "No PID file found for $Label — skipping."
    }
}

function Stop-ByPort {
    param([int]$Port, [string]$Label)
    $connections = netstat -ano 2>$null | Select-String ":$Port\s"
    $pids = $connections | ForEach-Object {
        ($_ -split '\s+' | Where-Object { $_ }) | Select-Object -Last 1
    } | Sort-Object -Unique

    foreach ($procId in $pids) {
        if ($procId -match '^\d+$' -and [int]$procId -ne 0) {
            try {
                Stop-Process -Id ([int]$procId) -Force -ErrorAction Stop
                Write-Host "Stopped $Label process on :$Port (PID $procId)"
            } catch {}
        }
    }
}

Write-Host "Stopping Banker's Wrapped demo stack...`n"

Stop-ByPidFile (Join-Path $LOGS "backend.pid")  "Backend"
Stop-ByPidFile (Join-Path $LOGS "frontend.pid") "Frontend"

# Fallback: kill by port in case PID files are stale
Stop-ByPort 8000 "Backend"
Stop-ByPort 3000 "Frontend"

Write-Host "`nAll services stopped."
