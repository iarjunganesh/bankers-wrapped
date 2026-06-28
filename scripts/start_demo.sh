#!/usr/bin/env bash
# Start the Banker's Wrapped demo stack: FastAPI backend + Next.js frontend
# Usage: bash scripts/start_demo.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS="$ROOT/logs"
mkdir -p "$LOGS"

# ── Resolve tool paths ───────────────────────────────────────────────────────
UV=$(command -v uv 2>/dev/null || true)

# On Windows/Git Bash, uv may live in LOCALAPPDATA or USERPROFILE but not bash PATH
if [ -z "$UV" ] && [ -n "${LOCALAPPDATA:-}" ]; then
    WIN_UV=$(find "$LOCALAPPDATA/uv" -name "uv.exe" 2>/dev/null | head -1 || true)
    [ -n "$WIN_UV" ] && UV="$WIN_UV"
fi
if [ -z "$UV" ] && [ -n "${USERPROFILE:-}" ]; then
    WIN_UV=$(find "$USERPROFILE/.cargo/bin" -name "uv.exe" 2>/dev/null | head -1 || true)
    [ -n "$WIN_UV" ] && UV="$WIN_UV"
fi

POETRY=$(command -v poetry 2>/dev/null || true)

if [ -z "$UV" ] && [ -z "$POETRY" ]; then
    echo "ERROR: Neither uv nor poetry found in PATH. Install uv: https://docs.astral.sh/uv/" >&2
    exit 1
fi

RUNNER="${UV:-$POETRY}"
RUNNER_NAME=$([ -n "$UV" ] && echo "uv" || echo "poetry")
echo "  Using runner: $RUNNER_NAME"

# ── Sync / install project dependencies ─────────────────────────────────────
echo "Syncing project dependencies..."
SYNC_CMD=$([ -n "$UV" ] && echo "sync" || echo "install")
if ! "$RUNNER" $SYNC_CMD 2>&1; then
    echo "ERROR: Dependency sync failed." >&2
    exit 1
fi
echo "  Dependencies ready."

# ── Locate venv uvicorn ──────────────────────────────────────────────────────
UVICORN="$ROOT/.venv/bin/uvicorn"
if [ ! -f "$UVICORN" ]; then
    # poetry puts venv elsewhere; fall back to runner
    UVICORN=""
fi

# ── Backend (uvicorn on :8000) ──────────────────────────────────────────────
echo "Starting FastAPI backend on http://localhost:8000 ..."
BACKEND_OUT="$LOGS/backend.stdout.log"
BACKEND_ERR="$LOGS/backend.stderr.log"

if [ -n "$UVICORN" ]; then
    nohup "$UVICORN" backend.main:app --port 8000 \
        >"$BACKEND_OUT" 2>"$BACKEND_ERR" &
else
    nohup "$RUNNER" run uvicorn backend.main:app --port 8000 \
        >"$BACKEND_OUT" 2>"$BACKEND_ERR" &
fi
echo $! > "$LOGS/backend.pid"
echo "  Backend PID $(cat "$LOGS/backend.pid")"
echo "  Logs: logs/backend.stdout.log / backend.stderr.log"

# ── Frontend (Next.js on :3000) ─────────────────────────────────────────────
echo "Installing frontend dependencies..."
(cd "$ROOT/frontend" && npm install) || echo "WARNING: npm install failed — frontend may not start correctly." >&2
echo "Starting Next.js frontend on http://localhost:3000 ..."
FRONTEND_OUT="$LOGS/frontend.stdout.log"
FRONTEND_ERR="$LOGS/frontend.stderr.log"
(cd "$ROOT/frontend" && nohup npm run dev >"$FRONTEND_OUT" 2>"$FRONTEND_ERR" &
 echo $! > "$LOGS/frontend.pid")
echo "  Frontend PID $(cat "$LOGS/frontend.pid")"
echo "  Logs: logs/frontend.stdout.log / frontend.stderr.log"

# ── Wait for API readiness ───────────────────────────────────────────────────
echo ""
echo "Waiting for API to become ready..."
DEADLINE=$(( $(date +%s) + 40 ))
READY=0
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
    if curl -sf http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
        READY=1
        break
    fi
    sleep 2
done

if [ "$READY" -eq 1 ]; then
    echo ""
    echo "Demo stack is up."
    echo "  API    -> http://localhost:8000"
    echo "  UI     -> http://localhost:3000"
    echo "  Docs   -> http://localhost:8000/docs"
    echo ""
    echo "To run the demo pipeline:  python scripts/demo_run.py"
    echo "To stop all services:      bash scripts/stop_demo.sh"
else
    echo "WARNING: API did not become ready within 40s." >&2
    echo "Check logs:"
    echo "  tail -30 logs/backend.stdout.log"
    echo "  tail -30 logs/backend.stderr.log"
fi
