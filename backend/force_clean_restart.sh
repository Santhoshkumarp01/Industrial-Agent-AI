#!/bin/bash
# Force clean restart - clear Python cache and restart server

echo "🧹 Cleaning Python cache and restarting server..."

cd "$(dirname "$0")"

# Kill existing server
echo "1. Killing existing server..."
pkill -9 -f "uvicorn main:app" 2>/dev/null
sleep 2

# Clear ALL Python cache
echo "2. Clearing Python bytecode cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null

echo "✅ Cache cleared"

# Start fresh server
echo "3. Starting fresh server..."
.venv/bin/uvicorn main:app --reload &

sleep 4

# Check if started
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ Server restarted successfully"
    echo ""
    echo "📋 Look for this in server logs:"
    echo "   '🔧 ANSWERER MODULE LOADED: CITATION_RELABEL_FIX_v3'"
    echo ""
    echo "🧪 Test with:"
    echo "   .venv/bin/python check_live_version.py"
else
    echo "❌ Server failed to start"
    exit 1
fi
