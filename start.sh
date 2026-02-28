#!/bin/bash

echo ""
echo "🤖 Supplement Assistant Bot"
echo "==========================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file with TELEGRAM_BOT_TOKEN"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python not found! Please install Python 3.8+"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "✅ Starting Supplement Assistant Bot..."
echo ""
echo "📋 Available commands:"
echo "   /start - Start supplement selection"
echo "   /add [name] - Add new supplement"
echo "   /schedule - Manage meal times & reminders"
echo "   /stats - View intelligent lookup stats"
echo ""
echo "💡 To enable smart lookup:"
echo "   1. Get free API key: https://brave.com/search/api/"
echo "   2. Add to .env: BRAVE_SEARCH_API_KEY=your_key"
echo ""
echo "🚀 Press Ctrl+C to stop"
echo "=========================================="
echo ""

$PYTHON_CMD run_all.py