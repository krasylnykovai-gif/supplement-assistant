"""
Reminder Service - sends automatic supplement reminders to users
Runs as background service, checks for upcoming reminders and sends notifications
"""
import asyncio
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram import Bot
from telegram.error import TelegramError
from core.meal_scheduler import MealScheduler
from dotenv import load_dotenv

# Load environment
load_dotenv(Path(__file__).parent.parent / ".env")

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ReminderService:
    """Service for sending automatic supplement reminders"""
    
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment!")
            
        self.bot = Bot(token=self.token)
        self.scheduler = MealScheduler(Path(__file__).parent.parent / "data")
        self.check_interval = 5 * 60  # Check every 5 minutes
        self.reminder_window = 10  # Send reminders within 10 minutes of target time
        
        # Track sent reminders to avoid duplicates
        self.sent_reminders = set()  # Format: "{user_id}_{supplement_id}_{datetime}"
    
    async def send_reminder(self, user_id: int, reminders: list, meal_name: str):
        """Send reminder message to user"""
        try:
            meal_emojis = {"breakfast": "🍳", "lunch": "🍽", "dinner": "🌙"}
            meal_names = {"breakfast": "сніданок", "lunch": "обід", "dinner": "вечеря"}
            
            emoji = meal_emojis.get(meal_name, "🍽")
            meal_display = meal_names.get(meal_name, meal_name)
            
            text = f"{emoji} *Час для БАДів перед {meal_display}!*\n\n"
            
            for reminder in reminders:
                text += f"💊 {reminder.supplement_name}"
                if reminder.dosage:
                    text += f" ({reminder.dosage})"
                if reminder.notes:
                    text += f"\n   _{reminder.notes}_"
                text += "\n"
            
            current_time = datetime.now()
            text += f"\n⏰ Нагадування: {current_time.strftime('%H:%M')}"
            text += "\n\n_💡 Налашуй розклад: /schedule_"
            
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode='Markdown'
            )
            
            logger.info(f"Sent reminder to user {user_id} for {meal_display} ({len(reminders)} supplements)")
            
        except TelegramError as e:
            if e.message == "Forbidden: bot was blocked by the user":
                logger.warning(f"User {user_id} has blocked the bot")
            else:
                logger.error(f"Failed to send reminder to user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending reminder to user {user_id}: {e}")
    
    def should_send_reminder(self, user_id: int, reminder_time: datetime, supplement_id: str) -> bool:
        """Check if reminder should be sent (not sent recently)"""
        now = datetime.now()
        
        # Only send if within reminder window
        time_diff = abs((reminder_time - now).total_seconds() / 60)
        if time_diff > self.reminder_window:
            return False
        
        # Check if already sent today for this supplement
        today = now.date()
        reminder_key = f"{user_id}_{supplement_id}_{today}"
        
        if reminder_key in self.sent_reminders:
            return False
            
        # Mark as sent
        self.sent_reminders.add(reminder_key)
        return True
    
    def cleanup_old_reminders(self):
        """Clean up old reminder tracking (older than 2 days)"""
        cutoff_date = (datetime.now() - timedelta(days=2)).date()
        
        to_remove = []
        for reminder_key in self.sent_reminders:
            try:
                parts = reminder_key.split('_')
                if len(parts) >= 3:
                    date_str = parts[-1]  # Last part should be date
                    reminder_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    if reminder_date < cutoff_date:
                        to_remove.append(reminder_key)
            except:
                # Invalid format, remove it
                to_remove.append(reminder_key)
        
        for key in to_remove:
            self.sent_reminders.discard(key)
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old reminder tracking entries")
    
    async def check_and_send_reminders(self):
        """Check for due reminders and send them"""
        now = datetime.now()
        logger.debug(f"Checking for reminders at {now.strftime('%H:%M:%S')}")
        
        # Get all user schedules
        user_ids = list(self.scheduler.schedules.keys())
        reminders_sent = 0
        
        for user_id in user_ids:
            try:
                # Get upcoming reminders for this user (next 15 minutes)
                upcoming = self.scheduler.get_next_reminders(user_id, hours_ahead=0.25)
                
                if not upcoming:
                    continue
                
                # Group reminders by meal and time
                meal_groups = {}
                for reminder_time, reminder, meal_time in upcoming:
                    # Only process reminders due within reminder window
                    if not self.should_send_reminder(user_id, reminder_time, reminder.supplement_id):
                        continue
                    
                    meal_key = f"{reminder.meal}_{reminder_time.strftime('%H:%M')}"
                    if meal_key not in meal_groups:
                        meal_groups[meal_key] = []
                    meal_groups[meal_key].append(reminder)
                
                # Send grouped reminders
                for meal_key, reminders in meal_groups.items():
                    meal_name = meal_key.split('_')[0]
                    await self.send_reminder(user_id, reminders, meal_name)
                    reminders_sent += 1
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error processing reminders for user {user_id}: {e}")
        
        if reminders_sent > 0:
            logger.info(f"Sent {reminders_sent} reminder groups")
    
    async def run(self):
        """Main service loop"""
        logger.info("Reminder service starting...")
        
        try:
            # Test bot connection
            bot_info = await self.bot.get_me()
            logger.info(f"Connected as @{bot_info.username}")
        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {e}")
            return
        
        while True:
            try:
                await self.check_and_send_reminders()
                
                # Clean up old tracking data once per hour
                if datetime.now().minute == 0:
                    self.cleanup_old_reminders()
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Reminder service stopping...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in reminder service: {e}")
                # Continue running even after errors
                await asyncio.sleep(30)


async def main():
    """Run the reminder service"""
    import platform
    
    # Fix for Python 3.14+ event loop
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    service = ReminderService()
    await service.run()


if __name__ == "__main__":
    asyncio.run(main())