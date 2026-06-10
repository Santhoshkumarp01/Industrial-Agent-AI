#!/bin/bash
# Force restart the backend server to ensure all code changes are loaded

echo "🔄 Forcefully restarting backend server..."

# Kill existing server
echo "Killing existing uvicorn process..."
pkill -f "uvicorn main:app"
sleep 2

# Verify it's stopped
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "⚠️  Process still running, force killing..."
    pkill -9 -f "uvicorn main:app"
    sleep 1
fi

echo "✅ Old server stopped"

# Start new server
echo "Starting new server..."
cd "$(dirname "$0")"
.venv/bin/uvicorn main:app --reload &

sleep 3

# Check if started
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ Server restarted successfully"
    echo "📋 Check logs for: 'ANSWERER MODULE LOADED: CITATION_RELABEL_FIX_v3'"
else
    echo "❌ Server failed to start"
    exit 1
fi
