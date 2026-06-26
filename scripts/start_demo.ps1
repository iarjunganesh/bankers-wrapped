# Start the Banker's Wrapped demo stack: FastAPI backend + Next.js frontend
# Usage: .\scripts\start_demo.ps1

$ROOT = Split-Path $PSScriptRoot -Parent
$LOGS = Join-Path $ROOT "logs"

if (-not (Test-Path $LOGS)) {
    New-Item -ItemType Directory -Path $LOGS | Out-Null
}

# ── Resolve tool paths ───────────────────────────────────────────────────────
$uv     = (Get-Command uv     -ErrorAction SilentlyContinue)?.Source
$poetry = (Get-Command poetry -ErrorAction SilentlyContinue)?.Source
$pwsh   = (Get-Command pwsh   -ErrorAction SilentlyContinue)?.Source ?? "pwsh"

if (-not $uv -and -not $poetry) {
    Write-Error "Neither uv nor poetry found in PATH. Install uv: https://docs.astral.sh/uv/"
    exit 1
}

$runner     = if ($uv) { $uv } else { $poetry }
$runnerName = if ($uv) { "uv" } else { "poetry" }
Write-Host "  Using runner: $runnerName"

# ── Sync / install project dependencies ─────────────────────────────────────
Write-Host "Syncing project dependencies..."
$syncCmd = if ($uv) { "sync" } else { "install" }
$syncResult = & $runner $syncCmd 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Dependency sync failed:`n$syncResult"
    exit 1
}
Write-Host "  Dependencies ready."

# ── Locate venv uvicorn ──────────────────────────────────────────────────────
$uvicorn = Join-Path $ROOT ".venv\Scripts\uvicorn.exe"
if (-not (Test-Path $uvicorn)) {
    # poetry puts venv elsewhere; fall back to runner
    $uvicorn = $null
}

# ── Backend (uvicorn on :8000) ──────────────────────────────────────────────
# Launch via pwsh so we can merge stderr into stdout with 2>&1. This ensures
# uvicorn startup messages (emitted before app import) land in backend.log too.
Write-Host "Starting FastAPI backend on http://localhost:8000 ..."
$backendLog = Join-Path $LOGS "backend.log"

$uvicornCmd = if ($uvicorn) {
    "& '$uvicorn' backend.main:app --port 8000 2>&1 | Out-File -FilePath '$backendLog' -Encoding utf8 -Append"
} else {
    "& '$runner' run uvicorn backend.main:app --port 8000 2>&1 | Out-File -FilePath '$backendLog' -Encoding utf8 -Append"
}

$backend = Start-Process -FilePath $pwsh `
    -ArgumentList "-NoProfile", "-NonInteractive", "-Command", $uvicornCmd `
    -WorkingDirectory $ROOT `
    -PassThru -WindowStyle Hidden

$backend.Id | Out-File (Join-Path $LOGS "backend.pid") -Encoding utf8
Write-Host "  Backend PID $($backend.Id)"
Write-Host "  Log : logs\backend.log (stdout + stderr merged)"

# ── Frontend (Next.js on :3000) ─────────────────────────────────────────────
# npm on Windows is a .ps1 script — must be invoked through pwsh, not directly
$frontendDir = Join-Path $ROOT "frontend"
$frontendOut = Join-Path $LOGS "frontend.stdout.log"
$frontendErr = Join-Path $LOGS "frontend.stderr.log"

Write-Host "Installing frontend dependencies..."
$npmInstall = Start-Process -FilePath $pwsh `
    -ArgumentList "-NoProfile", "-NonInteractive", "-Command", "npm install" `
    -WorkingDirectory $frontendDir `
    -PassThru -WindowStyle Hidden -Wait
if ($npmInstall.ExitCode -ne 0) {
    Write-Warning "npm install exited with code $($npmInstall.ExitCode) — frontend may not start correctly."
}
Write-Host "Starting Next.js frontend on http://localhost:3000 ..."
$frontend = Start-Process -FilePath $pwsh `
    -ArgumentList "-NoProfile", "-NonInteractive", "-Command", "npm run dev" `
    -WorkingDirectory $frontendDir `
    -RedirectStandardOutput $frontendOut `
    -RedirectStandardError  $frontendErr `
    -PassThru -WindowStyle Hidden
$frontend.Id | Out-File (Join-Path $LOGS "frontend.pid") -Encoding utf8
Write-Host "  Frontend PID $($frontend.Id)"
Write-Host "  Logs: logs\frontend.stdout.log / frontend.stderr.log"

# ── Wait for API readiness ───────────────────────────────────────────────────
Write-Host "`nWaiting for API to become ready..."
$deadline = (Get-Date).AddSeconds(40)
$ready = $false
while ((Get-Date) -lt $deadline) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    Start-Sleep -Seconds 2
}

if ($ready) {
    Write-Host "`nDemo stack is up."
    Write-Host "  API    -> http://localhost:8000"
    Write-Host "  UI     -> http://localhost:3000"
    Write-Host "  Docs   -> http://localhost:8000/docs"
    Write-Host "`nTo run the demo pipeline:  python scripts/demo_run.py"
    Write-Host "To stop all services:       .\scripts\stop_demo.ps1"
} else {
    Write-Warning "API did not become ready within 40s."
    Write-Host "Check logs:"
    Write-Host "  Get-Content logs\backend.log -Tail 30"
}
