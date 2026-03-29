#!/bin/bash
# Launch OpenClaw Dashboard

cd /Users/sirius_bot/.openclaw/workspace

# Check if server is already running
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Dashboard server already running"
else
    echo "Starting dashboard server..."
    python3 dashboard_server.py &
    sleep 2
fi

# Open in browser
open http://localhost:8080/dashboard.html

echo "Dashboard opened at http://localhost:8765/dashboard.html"
