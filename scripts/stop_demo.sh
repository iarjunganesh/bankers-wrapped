#!/usr/bin/env bash
# Stop the Banker's Wrapped demo stack
# Usage: bash scripts/stop_demo.sh

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS="$ROOT/logs"

stop_by_pid_file() {
    local pid_file="$1"
    local label="$2"
    if [ -f "$pid_file" ]; then
        local proc_id
        proc_id=$(cat "$pid_file")
        if kill -0 "$proc_id" 2>/dev/null; then
            kill "$proc_id" && echo "Stopped $label (PID $proc_id)"
        else
            echo "$label (PID $proc_id) was already stopped."
        fi
        rm -f "$pid_file"
    else
        echo "No PID file found for $label — skipping."
    fi
}

stop_by_port() {
    local port="$1"
    local label="$2"
    local proc_ids
    proc_ids=$(lsof -ti:"$port" 2>/dev/null || true)
    if [ -n "$proc_ids" ]; then
        echo "$proc_ids" | xargs kill -9 2>/dev/null \
            && echo "Stopped $label processes on :$port"
    fi
}

echo "Stopping Banker's Wrapped demo stack..."
echo ""

stop_by_pid_file "$LOGS/backend.pid"  "Backend"
stop_by_pid_file "$LOGS/frontend.pid" "Frontend"

# Fallback: kill by port in case PID files are stale
stop_by_port 8000 "Backend"
stop_by_port 3000 "Frontend"

echo ""
echo "All services stopped."
