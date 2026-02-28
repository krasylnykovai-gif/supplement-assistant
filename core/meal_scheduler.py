"""
Meal-based Dynamic Scheduler for Supplements
Handles flexible meal times and reminder notifications
"""
import json
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass 
class MealTime:
    """User's meal time preferences"""
    name: str  # breakfast, lunch, dinner
    typical_time: time  # user's typical time (e.g., 8:00)
    flexibility_minutes: int = 60  # ±60 min window
    reminder_offset_minutes: int = 30  # remind 30 min before
    enabled: bool = True


@dataclass
class SupplementReminder:
    """A supplement reminder tied to a meal"""
    supplement_id: str
    supplement_name: str
    meal: str  # breakfast, lunch, dinner
    dosage: str
    notes: str = ""
    enabled: bool = True


@dataclass
class UserSchedule:
    """User's complete meal and supplement schedule"""
    user_id: int
    timezone: str = "Europe/Kiev"
    meals: List[MealTime] = None
    reminders: List[SupplementReminder] = None
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.meals is None:
            # Default meal times for Ukraine
            self.meals = [
                MealTime("breakfast", time(8, 0), 60, 30),
                MealTime("lunch", time(13, 0), 90, 30), 
                MealTime("dinner", time(19, 0), 120, 30)
            ]
        if self.reminders is None:
            self.reminders = []
        if self.last_updated is None:
            self.last_updated = datetime.now()


class MealScheduler:
    """Manages meal-based supplement scheduling"""
    
    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = data_dir
        self.schedules_file = data_dir / "user_schedules.json"
        self.data_dir.mkdir(exist_ok=True)
        self.schedules: Dict[int, UserSchedule] = {}
        self.load_schedules()
    
    def load_schedules(self):
        """Load user schedules from file"""
        if self.schedules_file.exists():
            try:
                with open(self.schedules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for user_id_str, schedule_data in data.items():
                    user_id = int(user_id_str)
                    
                    # Convert time strings back to time objects
                    meals = []
                    for meal_data in schedule_data['meals']:
                        time_str = meal_data['typical_time']
                        hour, minute = map(int, time_str.split(':'))
                        meal_data['typical_time'] = time(hour, minute)
                        meals.append(MealTime(**meal_data))
                    
                    # Convert datetime string back
                    last_updated = datetime.fromisoformat(schedule_data['last_updated'])
                    
                    reminders = [SupplementReminder(**r) for r in schedule_data['reminders']]
                    
                    schedule = UserSchedule(
                        user_id=user_id,
                        timezone=schedule_data['timezone'],
                        meals=meals,
                        reminders=reminders,
                        last_updated=last_updated
                    )
                    self.schedules[user_id] = schedule
                    
            except Exception as e:
                print(f"Error loading schedules: {e}")
    
    def save_schedules(self):
        """Save user schedules to file"""
        data = {}
        for user_id, schedule in self.schedules.items():
            schedule_dict = asdict(schedule)
            
            # Convert time objects to strings
            for meal in schedule_dict['meals']:
                meal['typical_time'] = meal['typical_time'].strftime('%H:%M')
            
            # Convert datetime to string
            schedule_dict['last_updated'] = schedule.last_updated.isoformat()
            
            data[str(user_id)] = schedule_dict
        
        with open(self.schedules_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_user_schedule(self, user_id: int) -> UserSchedule:
        """Get user schedule, create default if doesn't exist"""
        if user_id not in self.schedules:
            self.schedules[user_id] = UserSchedule(user_id=user_id)
            self.save_schedules()
        return self.schedules[user_id]
    
    def update_meal_time(self, user_id: int, meal_name: str, new_time: time, 
                        flexibility_minutes: int = None, reminder_offset: int = None):
        """Update user's meal time"""
        schedule = self.get_user_schedule(user_id)
        
        for meal in schedule.meals:
            if meal.name == meal_name:
                meal.typical_time = new_time
                if flexibility_minutes is not None:
                    meal.flexibility_minutes = flexibility_minutes
                if reminder_offset is not None:
                    meal.reminder_offset_minutes = reminder_offset
                break
        else:
            # Add new meal
            schedule.meals.append(MealTime(
                meal_name, new_time, 
                flexibility_minutes or 60,
                reminder_offset or 30
            ))
        
        schedule.last_updated = datetime.now()
        self.save_schedules()
    
    def add_supplement_reminder(self, user_id: int, supplement_id: str, 
                              supplement_name: str, meal: str, dosage: str, notes: str = ""):
        """Add supplement reminder to meal"""
        schedule = self.get_user_schedule(user_id)
        
        # Remove existing reminder for this supplement
        schedule.reminders = [r for r in schedule.reminders if r.supplement_id != supplement_id]
        
        # Add new reminder
        reminder = SupplementReminder(
            supplement_id=supplement_id,
            supplement_name=supplement_name,
            meal=meal,
            dosage=dosage,
            notes=notes
        )
        schedule.reminders.append(reminder)
        schedule.last_updated = datetime.now()
        self.save_schedules()
    
    def remove_supplement_reminder(self, user_id: int, supplement_id: str):
        """Remove supplement reminder"""
        schedule = self.get_user_schedule(user_id)
        schedule.reminders = [r for r in schedule.reminders if r.supplement_id != supplement_id]
        schedule.last_updated = datetime.now()
        self.save_schedules()
    
    def get_next_reminders(self, user_id: int, hours_ahead: int = 2) -> List[Tuple[datetime, SupplementReminder, MealTime]]:
        """Get upcoming reminders for user within next X hours"""
        schedule = self.get_user_schedule(user_id)
        if not schedule.reminders:
            return []
        
        now = datetime.now()
        cutoff = now + timedelta(hours=hours_ahead)
        upcoming = []
        
        for reminder in schedule.reminders:
            if not reminder.enabled:
                continue
                
            # Find corresponding meal
            meal_time = None
            for meal in schedule.meals:
                if meal.name == reminder.meal and meal.enabled:
                    meal_time = meal
                    break
            
            if not meal_time:
                continue
            
            # Calculate reminder time for today and tomorrow
            for days_offset in [0, 1]:
                target_date = now.date() + timedelta(days=days_offset)
                
                # Meal time
                meal_datetime = datetime.combine(target_date, meal_time.typical_time)
                
                # Reminder time (before meal)
                reminder_datetime = meal_datetime - timedelta(minutes=meal_time.reminder_offset_minutes)
                
                # Skip past reminders
                if reminder_datetime <= now:
                    continue
                    
                # Check if within our window
                if reminder_datetime <= cutoff:
                    upcoming.append((reminder_datetime, reminder, meal_time))
        
        # Sort by time
        upcoming.sort(key=lambda x: x[0])
        return upcoming
    
    def get_current_meal_supplements(self, user_id: int, tolerance_minutes: int = 30) -> List[SupplementReminder]:
        """Get supplements that should be taken now (within tolerance of meal time)"""
        schedule = self.get_user_schedule(user_id)
        now = datetime.now()
        current_time = now.time()
        
        current_supplements = []
        
        for meal in schedule.meals:
            if not meal.enabled:
                continue
                
            # Check if current time is within meal window
            meal_start = (datetime.combine(now.date(), meal.typical_time) - 
                         timedelta(minutes=tolerance_minutes)).time()
            meal_end = (datetime.combine(now.date(), meal.typical_time) + 
                       timedelta(minutes=tolerance_minutes)).time()
            
            # Handle midnight crossing
            if meal_start <= meal_end:
                in_window = meal_start <= current_time <= meal_end
            else:  # Crosses midnight
                in_window = current_time >= meal_start or current_time <= meal_end
            
            if in_window:
                # Get supplements for this meal
                meal_supplements = [r for r in schedule.reminders 
                                 if r.meal == meal.name and r.enabled]
                current_supplements.extend(meal_supplements)
        
        return current_supplements
    
    def format_schedule(self, user_id: int) -> str:
        """Format user's schedule for display"""
        schedule = self.get_user_schedule(user_id)
        
        text = "📅 *Твій розклад прийому БАДів:*\n\n"
        
        # Group reminders by meal
        meal_groups = {}
        for reminder in schedule.reminders:
            if reminder.enabled:
                if reminder.meal not in meal_groups:
                    meal_groups[reminder.meal] = []
                meal_groups[reminder.meal].append(reminder)
        
        # Display each meal
        meal_emojis = {"breakfast": "🍳", "lunch": "🍽", "dinner": "🌙"}
        meal_names = {"breakfast": "Сніданок", "lunch": "Обід", "dinner": "Вечеря"}
        
        for meal in schedule.meals:
            if not meal.enabled:
                continue
                
            emoji = meal_emojis.get(meal.name, "🍽")
            meal_display = meal_names.get(meal.name, meal.name.title())
            reminder_time = (datetime.combine(datetime.now().date(), meal.typical_time) - 
                           timedelta(minutes=meal.reminder_offset_minutes)).time()
            
            text += f"{emoji} *{meal_display}* ({meal.typical_time.strftime('%H:%M')})\n"
            text += f"  💭 Нагадування: {reminder_time.strftime('%H:%M')}\n"
            
            if meal.name in meal_groups:
                for reminder in meal_groups[meal.name]:
                    text += f"  • {reminder.supplement_name}"
                    if reminder.dosage:
                        text += f" ({reminder.dosage})"
                    if reminder.notes:
                        text += f" - {reminder.notes}"
                    text += "\n"
            else:
                text += "  _Немає БАДів_\n"
            text += "\n"
        
        if not meal_groups:
            text += "_Ще немає налаштованих нагадувань._\n"
            text += "Використай /start щоб створити план!"
        
        return text
    
    def suggest_meal_times(self, current_time: time) -> Dict[str, time]:
        """Suggest meal times based on current time"""
        current_hour = current_time.hour
        
        # Smart suggestions based on current time
        if 5 <= current_hour < 10:  # Early morning
            return {
                "breakfast": time(current_hour + 1, 0),
                "lunch": time(13, 0),
                "dinner": time(19, 0)
            }
        elif 10 <= current_hour < 14:  # Late morning
            return {
                "breakfast": time(8, 0),
                "lunch": time(current_hour + 1, 0),
                "dinner": time(19, 0)
            }
        elif 14 <= current_hour < 20:  # Afternoon
            return {
                "breakfast": time(8, 0),
                "lunch": time(13, 0),
                "dinner": time(current_hour + 1, 0)
            }
        else:  # Evening/night
            return {
                "breakfast": time(8, 0),
                "lunch": time(13, 0),
                "dinner": time(19, 0)
            }


if __name__ == "__main__":
    # Test
    scheduler = MealScheduler(Path("../data"))
    
    # Add test user
    user_id = 123
    scheduler.update_meal_time(user_id, "breakfast", time(8, 30))
    scheduler.add_supplement_reminder(user_id, "vitamin_d", "Вітамін D", "breakfast", "2000 IU")
    
    print(scheduler.format_schedule(user_id))
    print("\nUpcoming reminders:")
    for when, reminder, meal in scheduler.get_next_reminders(user_id, 24):
        print(f"{when.strftime('%H:%M')} - {reminder.supplement_name} перед {meal.name}")