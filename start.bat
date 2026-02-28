@echo off
echo.
echo 🤖 Supplement Assistant Bot
echo ===========================
echo.

REM Check if .env exists
if not exist ".env" (
    echo ❌ .env file not found!
    echo Please create .env file with TELEGRAM_BOT_TOKEN
    pause
    exit /b 1
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

echo ✅ Starting Supplement Assistant Bot...
echo.
echo 📋 Available commands:
echo    /start - Start supplement selection
echo    /add [name] - Add new supplement
echo    /schedule - Manage meal times ^& reminders
echo    /stats - View intelligent lookup stats
echo.
echo 💡 To enable smart lookup:
echo    1. Get free API key: https://brave.com/search/api/
echo    2. Add to .env: BRAVE_SEARCH_API_KEY=your_key
echo.
echo 🚀 Press Ctrl+C to stop
echo ==========================================
echo.

python run_all.py

pause