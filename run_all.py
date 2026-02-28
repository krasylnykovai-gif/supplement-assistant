"""
Run all supplement assistant services
Starts telegram bot and reminder service simultaneously
"""
import asyncio
import subprocess
import sys
import signal
import platform
from pathlib import Path

# Fix for Python 3.14+
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def run_bot():
    """Run telegram bot"""
    subprocess.run([sys.executable, "bot/telegram_bot.py"], cwd=Path(__file__).parent)


def run_reminder_service():
    """Run reminder service"""
    subprocess.run([sys.executable, "services/reminder_service.py"], cwd=Path(__file__).parent)


async def main():
    """Run both services concurrently"""
    print("Starting Supplement Assistant...")
    print("Bot + Reminder Service")
    print("Press Ctrl+C to stop\n")
    
    # Create tasks for both services
    loop = asyncio.get_event_loop()
    
    bot_task = loop.run_in_executor(None, run_bot)
    reminder_task = loop.run_in_executor(None, run_reminder_service)
    
    try:
        # Wait for either to complete (they should run indefinitely)
        await asyncio.gather(bot_task, reminder_task)
    except KeyboardInterrupt:
        print("\nShutting down services...")
        # Tasks will be cancelled automatically
        
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServices stopped.")