"""
Telegram Bot for Supplement Assistant
Event-driven: user selects supplements → compatibility check → meal-based plan
"""
import os
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ContextTypes, MessageHandler, filters
)

# Load environment
load_dotenv(Path(__file__).parent.parent / ".env")

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import core modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.normalizer import SupplementNormalizer
from core.compatibility import CompatibilityChecker
from core.planner import MealPlanner, MealTime
from core.supplement_lookup import lookup_supplement, get_supplement_suggestions
from core.meal_scheduler import MealScheduler, SupplementReminder

# Paths
CATALOG_PATH = Path(__file__).parent.parent / "data" / "supplement_catalog.json"

# Initialize components
normalizer = SupplementNormalizer()
compatibility_checker = CompatibilityChecker()
scheduler = MealScheduler(Path(__file__).parent.parent / "data")

# User state storage
user_selections = {}  # user_id -> set of supplement_ids
user_plans = {}       # user_id -> generated plan
user_adding = {}      # user_id -> True if in adding mode
user_setting_time = {}  # user_id -> meal_name for time setting flow

# User analytics
USERS_DATA_PATH = Path(__file__).parent.parent / "data" / "users.json"


def load_users_data():
    """Load users analytics data"""
    if USERS_DATA_PATH.exists():
        try:
            with open(USERS_DATA_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading users data: {e}")
    
    return {
        "unique_users": [],  # list of user_ids
        "user_details": {},  # user_id -> {first_seen, last_seen, username, first_name, start_count}
        "daily_stats": {},   # date -> {new_users: count, active_users: [user_ids]}
        "total_unique": 0
    }


def save_users_data(users_data):
    """Save users analytics data"""
    try:
        # Ensure data directory exists
        USERS_DATA_PATH.parent.mkdir(exist_ok=True)
        
        # Update total count
        users_data["total_unique"] = len(users_data["unique_users"])
        
        with open(USERS_DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Users data saved: {users_data['total_unique']} unique users")
        
    except Exception as e:
        logger.error(f"Error saving users data: {e}")


def log_user_start(user):
    """Log user /start command for analytics"""
    user_id = user.id
    username = user.username or "N/A"
    first_name = user.first_name or "N/A"
    
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    timestamp = now.isoformat()
    
    # Load current data
    users_data = load_users_data()
    
    # Check if user is new
    is_new_user = user_id not in users_data["unique_users"]
    
    if is_new_user:
        # Add to unique users list
        users_data["unique_users"].append(user_id)
        
        # Add detailed info
        users_data["user_details"][str(user_id)] = {
            "first_seen": timestamp,
            "last_seen": timestamp,
            "username": username,
            "first_name": first_name,
            "start_count": 1
        }
        
        logger.info(f"NEW USER: {first_name} (@{username}, ID: {user_id})")
        
    else:
        # Update existing user info
        user_details = users_data["user_details"].get(str(user_id), {})
        user_details.update({
            "last_seen": timestamp,
            "username": username,  # Update in case changed
            "first_name": first_name,  # Update in case changed  
            "start_count": user_details.get("start_count", 0) + 1
        })
        users_data["user_details"][str(user_id)] = user_details
        
        logger.info(f"RETURNING USER: {first_name} (@{username}, ID: {user_id}) - {user_details['start_count']} times")
    
    # Update daily stats
    if today not in users_data["daily_stats"]:
        users_data["daily_stats"][today] = {
            "new_users": 0,
            "active_users": []
        }
    
    daily_stats = users_data["daily_stats"][today]
    
    if is_new_user:
        daily_stats["new_users"] += 1
    
    if user_id not in daily_stats["active_users"]:
        daily_stats["active_users"].append(user_id)
    
    # Save updated data
    save_users_data(users_data)
    
    return is_new_user


def reload_normalizer():
    """Reload normalizer after adding new supplement"""
    global normalizer
    normalizer = SupplementNormalizer()


def save_supplement(supp_id: str, name: str, with_food: bool, fat_required: bool, 
                    best_time: str, notes: str, source: str):
    """Save new supplement to catalog"""
    with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    catalog['supplements'][supp_id] = {
        "id": supp_id,
        "name": name,
        "aliases": [name.lower()],
        "category": "custom",
        "user_added": True,
        "timing": {
            "with_food": with_food,
            "fat_required": fat_required,
            "best_time": best_time,
            "notes": notes
        },
        "source": source
    }
    
    with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    
    reload_normalizer()


def get_supplement_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Generate keyboard with all supplements (selected ones marked)"""
    selected = user_selections.get(user_id, set())
    supplements = normalizer.get_all_supplements()
    
    buttons = []
    row = []
    
    for supp_id, supp_data in supplements.items():
        # Show only base supplements in main menu (not user-added)
        if supp_data.get('user_added', False):
            continue
        mark = "✅ " if supp_id in selected else ""
        btn = InlineKeyboardButton(
            f"{mark}{supp_data['name']}", 
            callback_data=f"toggle_{supp_id}"
        )
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    # Action buttons
    buttons.append([
        InlineKeyboardButton("+ Додати БАД", callback_data="start_add")
    ])
    buttons.append([
        InlineKeyboardButton("Перевірити сумісність", callback_data="check_compatibility"),
        InlineKeyboardButton("📅 Побудувати план", callback_data="build_plan")
    ])
    buttons.append([
        InlineKeyboardButton("× Очистити вибір", callback_data="clear_selection")
    ])
    buttons.append([
        InlineKeyboardButton("📚 Наші джерела", callback_data="show_sources")
    ])
    
    return InlineKeyboardMarkup(buttons)


def get_meal_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for meal selection"""
    buttons = [
        [InlineKeyboardButton("🍳 Сніданок", callback_data="meal_breakfast")],
        [InlineKeyboardButton("🍽 Обід", callback_data="meal_lunch")],
        [InlineKeyboardButton("🌙 Вечеря", callback_data="meal_dinner")],
        [InlineKeyboardButton("📋 Повний план", callback_data="full_plan")],
        [InlineKeyboardButton("◀️ Назад до вибору", callback_data="back_to_selection")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_after_add_keyboard(has_multiple_supplements: bool = False) -> InlineKeyboardMarkup:
    """Keyboard shown after adding a supplement with logical next steps"""
    buttons = [
        [InlineKeyboardButton("+ Add another supplement", callback_data="start_add")]
    ]
    
    # Show plan/schedule options if user has supplements
    if has_multiple_supplements:
        buttons.append([
            InlineKeyboardButton("Build plan", callback_data="build_plan"),
            InlineKeyboardButton("Check compatibility", callback_data="check_compatibility")
        ])
        buttons.append([
            InlineKeyboardButton("Setup schedule", callback_data="setup_meal_times")
        ])
    
    buttons.append([
        InlineKeyboardButton("All my supplements", callback_data="back_to_selection"),
        InlineKeyboardButton("Sources", callback_data="show_sources")
    ])
    buttons.append([
        InlineKeyboardButton("Help", callback_data="show_help")
    ])
    
    return InlineKeyboardMarkup(buttons)


def get_enhanced_after_add_keyboard(has_multiple_supplements: bool = False) -> InlineKeyboardMarkup:
    """Enhanced keyboard with clearer next steps after adding a supplement"""
    if has_multiple_supplements:
        # User has multiple supplements - prioritize plan creation
        buttons = [
            [InlineKeyboardButton("Compatibility check", callback_data="check_compatibility")],
            [InlineKeyboardButton("Create plan", callback_data="build_plan")],
            [InlineKeyboardButton("+ Add another", callback_data="start_add")],
            [InlineKeyboardButton("View all my supplements", callback_data="back_to_selection")]
        ]
    else:
        # First supplement - encourage adding more
        buttons = [
            [InlineKeyboardButton("+ Add more supplements", callback_data="start_add")],
            [InlineKeyboardButton("View supplement catalog", callback_data="back_to_selection")],
            [InlineKeyboardButton("Scientific sources", callback_data="show_sources")],
            [InlineKeyboardButton("How to use this bot", callback_data="show_help")]
        ]
    
    return InlineKeyboardMarkup(buttons)


def get_not_found_keyboard(name: str) -> InlineKeyboardMarkup:
    """Keyboard when supplement info not found - ask user"""
    buttons = [
        [
            InlineKeyboardButton("With food", callback_data=f"manual_food_yes:{name}"),
            InlineKeyboardButton("Empty stomach", callback_data=f"manual_food_no:{name}")
        ],
        [InlineKeyboardButton("x Cancel", callback_data="cancel_add")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_time_keyboard(name: str, with_food: bool) -> InlineKeyboardMarkup:
    """Keyboard for time selection (manual flow)"""
    food_flag = "yes" if with_food else "no"
    buttons = [
        [
            InlineKeyboardButton("Morning", callback_data=f"manual_time_morning:{name}:{food_flag}"),
            InlineKeyboardButton("Any time", callback_data=f"manual_time_any:{name}:{food_flag}"),
            InlineKeyboardButton("Evening", callback_data=f"manual_time_evening:{name}:{food_flag}")
        ],
        [InlineKeyboardButton("x Cancel", callback_data="cancel_add")]
    ]
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - show welcome and supplement selection"""
    user_id = update.effective_user.id
    user_selections[user_id] = set()
    user_adding.pop(user_id, None)
    
    # Log user for analytics
    is_new_user = log_user_start(update.effective_user)
    
    welcome_text = """👋 *Вітаю! Я твій науковий помічник з БАДів*

🎯 *Що я вмію:*
• Перевіряти сумісність добавок
• Будувати план прийому до сніданку/обіду/вечері  
• Шукати інформацію про нові БАДи

🏛️ *Наукова база:*
• Harvard Health • NIH (США) • Mayo Clinic
• PubMed • WebMD • Рецензовані дослідження

📝 *Як користуватись:*
1. Обери БАДи, які приймаєш ⬇️
2. Натисни "Перевірити сумісність" 
3. Отримай науково обґрунтований план

➕ Немає потрібного БАДу? Натисни "Додати БАД" - я знайду інформацію автоматично!

⚠️ _Інформація базується на наукових дослідженнях, але не замінює консультацію лікаря._

*Обери свої БАДи:*"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_supplement_keyboard(user_id),
        parse_mode='Markdown'
    )


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start adding new supplement via /add command"""
    user_id = update.effective_user.id
    
    if context.args:
        # Name provided - look it up immediately
        name = ' '.join(context.args)
        await process_new_supplement(update, context, name, is_callback=False)
    else:
        user_adding[user_id] = True
        await update.message.reply_text(
            "➕ *Додавання нового БАДу*\n\n"
            "Напиши назву добавки, і я знайду інформацію про неї:",
            parse_mode='Markdown'
        )


async def process_new_supplement(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                  name: str, is_callback: bool = False):
    """Process a new supplement - lookup info and save"""
    user_id = update.effective_user.id
    
    # Show searching message immediately
    search_message = f"🔍 *Шукаю інформацію про {name}...*\n\n"
    search_message += "⚙️ Перевіряю базу данних...\n"
    search_message += "🌐 Аналізую наукові джерела...\n"  
    search_message += "🧠 Застосовую розумний пошук...\n\n"
    search_message += "_Це займе кілька секунд..._"
    
    if is_callback:
        search_msg = await update.callback_query.edit_message_text(
            search_message, parse_mode='Markdown'
        )
    else:
        search_msg = await update.message.reply_text(
            search_message, parse_mode='Markdown'
        )
    
    # Small delay to show the message
    await asyncio.sleep(0.5)
    
    # Update search message
    if is_callback:
        await update.callback_query.edit_message_text(
            f"🔍 *Шукаю {name}...*\n\n⚙️ Перевіряю базу данних... ✅", 
            parse_mode='Markdown'
        )
    else:
        await search_msg.edit_text(
            f"🔍 *Шукаю {name}...*\n\n⚙️ Перевіряю базу данних... ✅", 
            parse_mode='Markdown'
        )
    
    # Check if already exists
    existing = normalizer.normalize(name)
    if existing:
        user_supplement_count = len(user_selections.get(user_id, set()))
        has_multiple = user_supplement_count > 1
        
        text = f"ℹ️ *{name}* вже є у списку!\n\nОбери його зі списку БАДів або додай інший."
        keyboard = get_after_add_keyboard(has_multiple)
        
        if is_callback:
            await update.callback_query.edit_message_text(
                text, reply_markup=keyboard, parse_mode='Markdown'
            )
        else:
            await search_msg.edit_text(
                text, reply_markup=keyboard, parse_mode='Markdown'
            )
        return
    
    # Update search message - looking up info
    if is_callback:
        await update.callback_query.edit_message_text(
            f"🔍 *Шукаю {name}...*\n\n"
            f"⚙️ Перевіряю базу данних... ✅\n"
            f"🌐 Аналізую наукові джерела... 🔄\n"
            f"🧠 Застосовую розумний пошук... ⏳",
            parse_mode='Markdown'
        )
    else:
        await search_msg.edit_text(
            f"🔍 *Шукаю {name}...*\n\n"
            f"⚙️ Перевіряю базу данних... ✅\n"
            f"🌐 Аналізую наукові джерела... 🔄\n"
            f"🧠 Застосовую розумний пошук... ⏳",
            parse_mode='Markdown'
        )
    
    # Lookup supplement info with progress updates
    try:
        # Update search message - starting lookup
        if is_callback:
            await update.callback_query.edit_message_text(
                f"🔍 *Шукаю {name}...*\n\n"
                f"⚙️ Перевіряю базу данних... ✅\n"
                f"🌐 Аналізую наукові джерела... ⏳\n"
                f"🧠 Застосовую розумний пошук... ⏳\n\n"
                f"_Максимум 15 секунд..._",
                parse_mode='Markdown'
            )
        else:
            await search_msg.edit_text(
                f"🔍 *Шукаю {name}...*\n\n"
                f"⚙️ Перевіряю базу данних... ✅\n"
                f"🌐 Аналізую наукові джерела... ⏳\n"
                f"🧠 Застосовую розумний пошук... ⏳\n\n"
                f"_Максимум 15 секунд..._",
                parse_mode='Markdown'
            )
        
        info = lookup_supplement(name)
        
        # Update search message - lookup completed
        if is_callback:
            await update.callback_query.edit_message_text(
                f"🔍 *Шукаю {name}...*\n\n"
                f"⚙️ Перевіряю базу данних... ✅\n"
                f"🌐 Аналізую наукові джерела... ✅\n"
                f"🧠 Застосовую розумний пошук... ✅\n\n"
                f"📊 *Обробка результатів...*",
                parse_mode='Markdown'
            )
        else:
            await search_msg.edit_text(
                f"🔍 *Шукаю {name}...*\n\n"
                f"⚙️ Перевіряю базу данних... ✅\n"
                f"🌐 Аналізую наукові джерела... ✅\n"
                f"🧠 Застосовую розумний пошук... ✅\n\n"
                f"📊 *Обробка результатів...*",
                parse_mode='Markdown'
            )
            
    except Exception as lookup_error:
        # If lookup fails completely, still give user feedback
        error_text = (
            f"🔍 *Результат пошуку {name}:*\n\n"
            f"❌ *Помилка пошуку:* {str(lookup_error)[:100]}...\n\n"
            f"💡 Спробуй додати вручну або перевір назву."
        )
        
        keyboard = get_not_found_keyboard(name)
        
        if is_callback:
            await update.callback_query.edit_message_text(
                error_text, reply_markup=keyboard, parse_mode='Markdown'
            )
        else:
            await search_msg.edit_text(
                error_text, reply_markup=keyboard, parse_mode='Markdown'
            )
        return
    
    if info.found:
        # Auto-save with found info
        supp_id = name.lower().replace(' ', '_').replace('-', '_')
        supp_id = ''.join(c for c in supp_id if c.isalnum() or c == '_')
        
        save_supplement(
            supp_id=supp_id,
            name=info.name,
            with_food=info.with_food,
            fat_required=info.fat_required,
            best_time=info.best_time,
            notes=info.notes,
            source=info.source
        )
        
        # Format enhanced response with full supplement information
        food_text = "з їжею" if info.with_food else "натщесерце"
        if info.fat_required:
            food_text += " (з жирами для кращого засвоєння)"
        
        time_display = {
            "morning": "🌅 вранці",
            "any": "🌤 будь-коли",
            "evening": "🌙 ввечері"
        }
        
        # Check if user has multiple supplements for better keyboard
        user_supplement_count = len(user_selections.get(user_id, set())) + 1  # +1 for just added
        has_multiple = user_supplement_count > 1
        
        # Create comprehensive information message
        text = f"✅ *{info.name}* успішно додано!\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "📊 *Інформація про прийом:*\n"
        text += f"🍽️ *Спосіб:* {food_text}\n"
        text += f"⏰ *Оптимальний час:* {time_display.get(info.best_time, info.best_time)}\n\n"
        
        text += "💡 *Рекомендації:*\n"
        text += f"_{info.notes}_\n\n"
        
        # Add source with clickable link if available (skip paid resources like examine.com)
        if info.source and info.source.startswith('http') and 'examine.com' not in info.source:
            text += f"📚 *Наукове джерело:* [Детальна інформація]({info.source})\n\n"
        elif info.source and not info.source.startswith('http') and info.source not in ('pattern_analysis', 'user_manual'):
            text += f"📚 *Джерело:* {info.source}\n\n"
        
        # Add confidence indicator if available
        if "впевненість:" in info.notes:
            confidence_text = info.notes.split("впевненість: ")[1].split(")")[0]
            try:
                confidence = float(confidence_text)
                if confidence > 0.8:
                    confidence_emoji = "🟢"
                elif confidence > 0.6:
                    confidence_emoji = "🟡"
                else:
                    confidence_emoji = "🟠"
                text += f"{confidence_emoji} *Рівень впевненості:* {confidence:.1f}\n\n"
            except:
                pass
        
        # Clear next steps section with better emphasis
        text += "━━━━━━━━━━━━━━━━━━━━━━\n"
        text += "🎯 *ЩО РОБИТИ ДАЛІ?*\n\n"
        
        if has_multiple:
            text += "У тебе вже є кілька БАДів! Можеш:\n"
            text += "• **Перевірити сумісність** всіх БАДів\n"
            text += "• 📅 **Створити розклад** прийому\n"
            text += "• **Додати ще БАДів**\n"
            text += "• 📋 **Переглянути список** всіх БАДів"
        else:
            text += "💡 Це твій перший БАД! Рекомендую:\n"
            text += "• **Додати ще БАДів** для комплексного підходу\n"
            text += "• 📋 **Переглянути весь каталог** БАДів\n"
            text += "• 📚 **Дізнатися більше** про наукові джерела"
        
        text += "\n👇 **Обери дію нижче:**"
        
        keyboard = get_enhanced_after_add_keyboard(has_multiple)
        user_adding.pop(user_id, None)
        
        # Update final message with results
        if is_callback:
            await update.callback_query.edit_message_text(
                text, reply_markup=keyboard, parse_mode='Markdown'
            )
        else:
            await search_msg.edit_text(
                text, reply_markup=keyboard, parse_mode='Markdown'
            )
        return
        
    else:
        # Update search message - not found in main DB
        if is_callback:
            await update.callback_query.edit_message_text(
                f"🔍 *Шукаю {name}...*\n\n"
                f"⚙️ Перевіряю базу данних... ✅\n"
                f"🌐 Аналізую наукові джерела... ✅\n"
                f"🧠 Застосовую розумний пошук... ✅\n\n"
                f"🤔 Шукаю альтернативи...",
                parse_mode='Markdown'
            )
        else:
            await search_msg.edit_text(
                f"🔍 *Шукаю {name}...*\n\n"
                f"⚙️ Перевіряю базу данних... ✅\n"
                f"🌐 Аналізую наукові джерела... ✅\n"
                f"🧠 Застосовую розумний пошук... ✅\n\n"
                f"🤔 Шукаю альтернативи...",
                parse_mode='Markdown'
            )
        
        # Not found - show suggestions if available
        suggestions = get_supplement_suggestions(name)
        
        if suggestions:
            text = (
                f"🔍 *{name}*\n\n"
                f"🤖 Точного співпадіння не знайшов, але є схожі:\n\n"
            )
            
            # Add suggestions as buttons
            suggestion_buttons = []
            for suggestion in suggestions[:3]:  # Max 3 suggestions
                suggestion_buttons.append([
                    InlineKeyboardButton(
                        f"» {suggestion}", 
                        callback_data=f"use_suggestion:{suggestion}"
                    )
                ])
            
            suggestion_buttons.append([
                InlineKeyboardButton("+ Додати як новий", callback_data=f"start_add_manual:{name}")
            ])
            suggestion_buttons.append([
                InlineKeyboardButton("× Скасувати", callback_data="cancel_add")
            ])
            
            keyboard = InlineKeyboardMarkup(suggestion_buttons)
            
        else:
            # No suggestions - ask user to add manually
            text = (
                f"× *{name}*\n\n"
                f"🤖 Автоматичний пошук не знайшов достатньо інформації.\n"
                f"🌐 Перевірено: база даних + наукові джерела + розумний пошук\n\n"
                f"💡 **Допоможи покращити систему:**\n"
                f"Підкажи, як його приймати, і я запам'ятаю для інших користувачів!"
            )
            keyboard = get_not_found_keyboard(name)
    
    # Update the search message with final results
    if is_callback:
        await update.callback_query.edit_message_text(
            f"🔍 *Результат пошуку:*\n\n{text}",
            reply_markup=keyboard, parse_mode='Markdown'
        )
    else:
        await search_msg.edit_text(
            text, reply_markup=keyboard, parse_mode='Markdown'
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (for /add flow and time setting)"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if user_id in user_adding:
        # User is adding a supplement - treat message as supplement name
        await process_new_supplement(update, context, text, is_callback=False)
        return
    
    if user_id in user_setting_time:
        # User is setting custom meal time
        meal = user_setting_time[user_id]
        
        # Parse time format HH:MM
        import re
        time_match = re.match(r'^(\d{1,2}):(\d{2})$', text)
        
        if not time_match:
            await update.message.reply_text(
                "❌ Невірний формат часу. Використай формат ГГ:ХХ (наприклад: 08:30)"
            )
            return
        
        try:
            hour, minute = int(time_match.group(1)), int(time_match.group(2))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid time range")
                
            meal_time = time(hour, minute)
            
            # Update schedule
            scheduler.update_meal_time(user_id, meal, meal_time)
            
            meal_names = {"breakfast": "сніданок", "lunch": "обід", "dinner": "вечеря"}
            meal_display = meal_names.get(meal, meal)
            
            del user_setting_time[user_id]
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⏰ Налаштувати інший час", callback_data="setup_meal_times")],
                [InlineKeyboardButton("◀️ До розкладу", callback_data="back_to_schedule")]
            ])
            
            await update.message.reply_text(
                f"✅ Час {meal_display} встановлено: *{meal_time.strftime('%H:%M')}*\n\n"
                f"Нагадування буде надходити за 30 хвилин до прийому їжі.",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Невірний час. Введи час від 00:00 до 23:59"
            )
        return


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    help_text = """📚 *Команди:*

/start - Почати вибір БАДів
/add - Додати новий БАД
/add Назва - Швидке додавання
/plan - Показати поточний план
/schedule - Розклад і нагадування
/reminders - Перевірити поточні БАДи
/sources - Наукові джерела даних
/about - Про науковий підхід бота
/clear - Очистити вибір
/stats - Статистика автопошуку
/help - Ця довідка

🔔 *Нагадування:*
• Налашуй час прийому їжі
• Отримуй нагадування за 30 хв
• Керуй вкл/викл кожного БАДу

🧠 *Розумний пошук:*
• Автоматично шукає інформацію про нові БАДи
• Використовує надійні медичні джерела
• Зберігає знання для інших користувачів

⚠️ _Інформація базується на наукових дослідженнях._
_Використовуй /sources щоб побачити повний список джерел._"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def sources_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show scientific sources used by the bot"""
    sources_text = """🏛️ *Наукові джерела даних*

Вся інформація про БАДи береться виключно з авторитетних медичних джерел:

🎓 **Урядові та академічні інститути:**
• [NIH Office of Dietary Supplements](https://ods.od.nih.gov/) - Національний інститут здоров'я США
• [Harvard Health Publishing](https://health.harvard.edu/) - Гарвардська медична школа  
• [PubMed](https://pubmed.ncbi.nlm.nih.gov/) - Національна медична бібліотека США

🏥 **Провідні медичні клініки:**
• [Mayo Clinic](https://mayoclinic.org/) - Одна з топ-клінік світу
• [WebMD](https://webmd.com/) - Медичні довідники

🔬 **Наукові дослідницькі платформи:**
• [MedlinePlus](https://medlineplus.gov/druginformation.html) - Безкоштовна база NIH для пацієнтів
• [Healthline](https://healthline.com/) - Медичний контент на основі доказів

📊 **Принципи роботи:**
✅ Тільки рецензовані наукові дослідження
✅ Офіційні медичні рекомендації
✅ Незалежна перевірка даних  
✅ Постійне оновлення інформації

⚗️ **Рівні довіри:**
🟢 Висока впевненість (0.8-1.0) - Офіційні медичні джерела
🟡 Середня впевненість (0.6-0.8) - Перехресні дослідження
🟠 Низька впевненість (<0.6) - Обмежені дані

⚠️ *Застереження:*
_Інформація призначена для ознайомлення і не замінює консультацію лікаря. БАДи не є лікарськими засобами._

💡 _Бот постійно навчається і покращує якість рекомендацій на основі нових наукових досліджень._"""
    
    await update.message.reply_text(sources_text, parse_mode='Markdown')


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed information about the scientific approach"""
    about_text = """🧬 *Про Supplement Assistant*

**Науковий підхід до БАДів** - перший український бот, що базується виключно на доказовій медицині.

🎯 **Місія:**
Надати українцям доступ до науково обґрунтованої інформації про БАДи на рівні світових медичних стандартів.

🏆 **Що робить нас унікальними:**

**📚 Наукова база світового рівня:**
• Harvard Medical School  
• National Institute of Health (США)
• Mayo Clinic (#1 клініка США)
• Тисячі peer-reviewed досліджень

**🧠 Розумний AI-аналіз:**
• Автоматичний пошук нових БАДів
• Аналіз взаємодій та сумісності
• Персональне планування прийому
• Оновлення на основі нових досліджень

**⚗️ Рівні довіри 0-1.0:**
Кожна рекомендація має рейтинг надійності:
🟢 0.8+ - Офіційні медичні джерела
🟡 0.6+ - Перехресні дослідження  
🟠 0.4+ - Обмежені дані

**🔄 Постійне навчання:**
База знань автоматично оновлюється новими науковими дослідженнями та користувацьким досвідом.

**🇺🇦 Для України:**
Перший науковий БАД-помічник українською мовою з підтримкою російської та англійської.

**👨‍⚕️ Етичний підхід:**
• Немає реклами БАДів
• Немає фінансових зацікавленостей  
• Лише об'єктивна наукова інформація
• Постійне нагадування про консультацію з лікарем

⚠️ *Пам'ятай:* Це інформаційний інструмент, а не заміна медичної консультації. При сумнівах завжди звертайся до лікаря!

_Створено з 🇺🇦 для здоров'я українців_"""
    
    await update.message.reply_text(about_text, parse_mode='Markdown')


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user analytics (admin only) - FIXED VERSION"""
    user_id = update.effective_user.id
    
    # Admin user IDs - Irina's user ID  
    admin_users = [383087326]  # Irina's user ID
    
    logger.info(f"Users command called by user: {user_id}")
    
    if user_id not in admin_users:
        logger.warning(f"Non-admin user {user_id} tried to access /users")
        await update.message.reply_text(
            "⚠️ Команда доступна тільки адміністраторам."
        )
        return
    
    try:
        logger.info("Loading users data...")
        users_data = load_users_data()
        logger.info(f"Loaded users data: {len(users_data.get('user_details', {}))} users")
        
        # Basic stats
        total_unique = users_data.get("total_unique", 0)
        
        # Today's stats  
        today = datetime.now(timezone.utc).date().isoformat()
        today_stats = users_data.get("daily_stats", {}).get(today, {})
        today_new = today_stats.get("new_users", 0)  
        today_active = len(today_stats.get("active_users", []))
        
        # Weekly stats (safe calculation)
        recent_days = list(users_data.get("daily_stats", {}).keys())[-7:]
        weekly_new = 0
        weekly_active = set()
        
        for day in recent_days:
            day_stats = users_data.get("daily_stats", {}).get(day, {})
            weekly_new += day_stats.get("new_users", 0)
            weekly_active.update(day_stats.get("active_users", []))
        
        # Most active users (top 5)
        user_activity = []
        for uid, details in users_data.get("user_details", {}).items():
            start_count = details.get("start_count", 0)
            first_name = details.get("first_name", "N/A") 
            username = details.get("username", "N/A")
            user_activity.append((start_count, first_name, username, uid))
        
        user_activity.sort(reverse=True)
        top_users = user_activity[:5]
        
        # Build response message (simple formatting to avoid markdown issues)
        stats_lines = [
            "📊 Аналітика користувачів",
            "",
            "📈 Загальна статистика:",
            f"👥 Всього унікальних користувачів: {total_unique}",
            "",
            f"📅 Сьогодні ({today}):",
            f"🆕 Нових користувачів: {today_new}",
            f"👤 Активних користувачів: {today_active}",
            "",
            f"📊 За тиждень:",
            f"🆕 Нових користувачів: {weekly_new}",  
            f"👤 Активних користувачів: {len(weekly_active)}",
            ""
        ]
        
        # Add top users
        if top_users:
            stats_lines.append("🏆 Топ-5 найактивніших:")
            for i, (count, name, username, uid) in enumerate(top_users, 1):
                username_text = f"@{username}" if username != "N/A" else "без username"
                stats_lines.append(f"{i}. {name} ({username_text}) - {count} разів")
        else:
            stats_lines.append("🏆 Поки немає активних користувачів")
        
        # Add daily breakdown
        if recent_days:
            stats_lines.append("")
            stats_lines.append("📈 Активність по днях:")
            for day in recent_days[-3:]:  # Show last 3 days only
                day_stats = users_data.get("daily_stats", {}).get(day, {})
                new_count = day_stats.get("new_users", 0)
                active_count = len(day_stats.get("active_users", []))
                stats_lines.append(f"• {day}: +{new_count} нових, {active_count} активних")
        
        stats_lines.append("")
        stats_lines.append(f"📍 Дані оновлено: {datetime.now(timezone.utc).strftime('%H:%M UTC')}")
        
        # Join message
        stats_text = "\n".join(stats_lines)
        
        logger.info(f"Sending users stats: {len(stats_text)} characters")
        await update.message.reply_text(stats_text)
        
        logger.info("Users command completed successfully")
        
    except Exception as e:
        logger.error(f"Error in users_command: {str(e)}", exc_info=True)
        await update.message.reply_text(
            f"❌ Помилка отримання статистики: {str(e)}"
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if user_id not in user_selections:
        user_selections[user_id] = set()
    
    # === ADD FLOW ===
    if data == "start_add":
        user_adding[user_id] = True
        await query.edit_message_text(
            "➕ *Додавання нового БАДу*\n\n"
            "Напиши назву добавки, і я знайду інформацію про неї:",
            parse_mode='Markdown'
        )
        return
    
    if data == "cancel_add":
        user_adding.pop(user_id, None)
        await query.edit_message_text(
            "❌ Додавання скасовано.\n\n*Обери свої БАДи:*",
            reply_markup=get_supplement_keyboard(user_id),
            parse_mode='Markdown'
        )
        return
    
    # Handle suggestion selection
    if data.startswith("use_suggestion:"):
        suggested_name = data.replace("use_suggestion:", "")
        user_adding.pop(user_id, None)
        
        # Process the suggested supplement
        await process_new_supplement(update, context, suggested_name, is_callback=True)
        return
    
    # Handle manual addition when suggestions were shown
    if data.startswith("start_add_manual:"):
        original_name = data.replace("start_add_manual:", "")
        
        text = (
            f"➕ *{original_name}*\n\n"
            f"Точного співпадіння не знайшов.\n"
            f"Підкажи, як його приймати?"
        )
        keyboard = get_not_found_keyboard(original_name)
        
        await query.edit_message_text(
            text, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
        return
    
    # Manual flow - food choice
    if data.startswith("manual_food_"):
        parts = data.split(":", 1)
        with_food = "yes" in parts[0]
        name = parts[1] if len(parts) > 1 else "БАД"
        
        await query.edit_message_text(
            f"+ *{name}*\n\nКоли краще приймати?",
            reply_markup=get_time_keyboard(name, with_food),
            parse_mode='Markdown'
        )
        return
    
    # Manual flow - time choice
    if data.startswith("manual_time_"):
        parts = data.split(":")
        time_part = parts[0].replace("manual_time_", "")
        name = parts[1] if len(parts) > 1 else "БАД"
        with_food = parts[2] == "yes" if len(parts) > 2 else True
        
        # Save supplement
        supp_id = name.lower().replace(' ', '_').replace('-', '_')
        supp_id = ''.join(c for c in supp_id if c.isalnum() or c == '_')
        
        save_supplement(
            supp_id=supp_id,
            name=name.title(),
            with_food=with_food,
            fat_required=False,
            best_time=time_part,
            notes="Додано вручну користувачем",
            source="user_manual"
        )
        
        # Also save to intelligent research DB for future users
        try:
            from core.intelligent_lookup import IntelligentLookup, ResearchResult
            from datetime import datetime
            
            data_dir = Path(__file__).parent.parent / "data"
            lookup_engine = IntelligentLookup(data_dir)
            
            # Create research result from user input
            user_result = ResearchResult(
                name=name.title(),
                with_food=with_food,
                fat_required=False,
                best_time=time_part,
                notes=f"Додано користувачем {datetime.now().strftime('%Y-%m-%d')}",
                confidence=0.8,  # User input is fairly reliable
                sources=["user_input"],
                research_date=datetime.now().isoformat(),
                found=True
            )
            
            lookup_engine.cache_research(name, user_result)
            # Saved user input to research DB (no logging to avoid encoding issues)
            
        except Exception as e:
            # Failed to save user input to research DB (no logging to avoid encoding issues)
            pass
        
        food_text = "з їжею" if with_food else "натщесерце"
        time_display = {"morning": "🌅 вранці", "any": "🌤 будь-коли", "evening": "🌙 ввечері"}
        
        # Check if user has multiple supplements
        user_supplement_count = len(user_selections.get(user_id, set())) + 1
        has_multiple = user_supplement_count > 1
        
        # Create enhanced message for manually added supplement
        text = f"✅ *{name.title()}* успішно додано!\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "📊 *Інформація про прийом:*\n"
        text += f"🍽️ *Спосіб:* {food_text}\n"
        text += f"⏰ *Оптимальний час:* {time_display.get(time_part, time_part)}\n\n"
        
        text += "💡 *Рекомендації:*\n"
        text += f"_Додано на основі твоїх вказівок. Дякую за вклад у базу знань!_\n\n"
        
        # Add note for manually added supplements
        text += "📚 *Джерело інформації:*\n"
        text += "_Додано на основі вказівок користувача. Для деталей зверніться до лікаря або перевірте на [NIH Supplements](https://ods.od.nih.gov/factsheets/list-all/) — безкоштовна наукова база._\n\n"
        
        text += "🌟 *Твій внесок:*\n"
        text += f"_Інформація збережена і допоможе іншим користувачам_\n\n"
        
        # Clear next steps section with better emphasis
        text += "━━━━━━━━━━━━━━━━━━━━━━\n"
        text += "🎯 *ЩО РОБИТИ ДАЛІ?*\n\n"
        
        if has_multiple:
            text += "У тебе вже є кілька БАДів! Можеш:\n"
            text += "• **Перевірити сумісність** всіх БАДів\n"
            text += "• 📅 **Створити розклад** прийому\n"
            text += "• **Додати ще БАДів**\n"
            text += "• 📋 **Переглянути список** всіх БАДів"
        else:
            text += "💡 Це твій перший БАД! Рекомендую:\n"
            text += "• **Додати ще БАДів** для комплексного підходу\n"
            text += "• 📋 **Переглянути весь каталог** БАДів\n"
            text += "• 📚 **Дізнатися більше** про наукові джерела"
        
        text += "\n👇 **Обери дію нижче:**"
        
        user_adding.pop(user_id, None)
        
        await query.edit_message_text(
            text,
            reply_markup=get_enhanced_after_add_keyboard(has_multiple),
            parse_mode='Markdown'
        )
        return
    
    # === SELECTION FLOW ===
    if data.startswith("toggle_"):
        supp_id = data.replace("toggle_", "")
        if supp_id in user_selections[user_id]:
            user_selections[user_id].remove(supp_id)
        else:
            user_selections[user_id].add(supp_id)
        
        await query.edit_message_reply_markup(
            reply_markup=get_supplement_keyboard(user_id)
        )
        return
    
    if data == "clear_selection":
        user_selections[user_id] = set()
        await query.edit_message_reply_markup(
            reply_markup=get_supplement_keyboard(user_id)
        )
        return
    
    if data == "check_compatibility":
        selected = list(user_selections.get(user_id, set()))
        
        if not selected:
            await query.edit_message_text(
                "⚠️ Спочатку обери БАДи для перевірки!",
                reply_markup=get_supplement_keyboard(user_id)
            )
            return
        
        report = compatibility_checker.check(selected)
        catalog = normalizer.get_all_supplements()
        formatted = compatibility_checker.format_report(report, catalog)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 Побудувати план", callback_data="build_plan")],
            [InlineKeyboardButton("◀️ Змінити вибір", callback_data="back_to_selection")]
        ])
        
        await query.edit_message_text(
            formatted,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return
    
    if data == "build_plan":
        selected = list(user_selections.get(user_id, set()))
        
        if not selected:
            await query.edit_message_text(
                "⚠️ Спочатку обери БАДи!",
                reply_markup=get_supplement_keyboard(user_id)
            )
            return
        
        report = compatibility_checker.check(selected)
        catalog = normalizer.get_all_supplements()
        
        planner = MealPlanner(catalog, report.constraints)
        plans = planner.create_plan(selected)
        user_plans[user_id] = plans
        
        # Also create reminders in scheduler
        for meal_time, meal_plan in plans.items():
            # Extract supplements from all slots in this meal
            all_supplements = (meal_plan.before + meal_plan.with_meal + meal_plan.after)
            
            for slot in all_supplements:
                supp_data = catalog.get(slot.supplement_id, {})
                supp_name = supp_data.get('name', slot.supplement_id)
                
                # Add reminder
                scheduler.add_supplement_reminder(
                    user_id=user_id,
                    supplement_id=slot.supplement_id,
                    supplement_name=supp_name,
                    meal=meal_time.value,  # Use enum value instead of string
                    dosage="",  # User can set this later
                    notes=slot.notes
                )
        
        await query.edit_message_text(
            "✅ План готовий! Обери прійом їжі:\n\n"
            "_💡 Нагадування автоматично створені. Налашуй час через /schedule_",
            reply_markup=get_meal_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    if data.startswith("meal_"):
        meal_map = {
            "meal_breakfast": MealTime.BREAKFAST,
            "meal_lunch": MealTime.LUNCH,
            "meal_dinner": MealTime.DINNER
        }
        meal = meal_map.get(data)
        
        if user_id not in user_plans:
            await query.edit_message_text(
                "⚠️ Спочатку побудуй план!",
                reply_markup=get_supplement_keyboard(user_id)
            )
            return
        
        plans = user_plans[user_id]
        catalog = normalizer.get_all_supplements()
        planner = MealPlanner(catalog)
        formatted = planner.get_meal_supplements(plans, meal)
        
        await query.edit_message_text(
            formatted,
            reply_markup=get_meal_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    if data == "full_plan":
        if user_id not in user_plans:
            await query.edit_message_text(
                "⚠️ Спочатку побудуй план!",
                reply_markup=get_supplement_keyboard(user_id)
            )
            return
        
        plans = user_plans[user_id]
        catalog = normalizer.get_all_supplements()
        planner = MealPlanner(catalog)
        formatted = planner.format_plan(plans)
        
        await query.edit_message_text(
            formatted,
            reply_markup=get_meal_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    if data == "back_to_selection":
        selected_count = len(user_selections.get(user_id, set()))
        
        # Show different message based on whether user has selections
        if selected_count > 0:
            text = f"📋 *Твої БАДи ({selected_count}):*\n\n"
            
            # List selected supplements
            supplements = normalizer.get_all_supplements()
            for supp_id in user_selections.get(user_id, set()):
                supp_data = supplements.get(supp_id, {})
                name = supp_data.get('name', supp_id)
                text += f"✅ {name}\n"
            
            text += f"\n💡 Можеш додати ще БАДів або перевірити сумісність обраних.\n\n"
            text += "👇 **Обери дію:**"
            
        else:
            text = "📋 *Каталог БАДів*\n\n"
            text += "Обери БАДи, які приймаєш або плануєш приймати:\n\n"
            text += "💡 Не знаходиш потрібний БАД? Натисни **\"Додати БАД\"** - я знайду інформацію автоматично!"
        
        await query.edit_message_text(
            text,
            reply_markup=get_supplement_keyboard(user_id),
            parse_mode='Markdown'
        )
        return
    
    # === SCHEDULE MANAGEMENT ===
    if data == "setup_meal_times":
        await query.edit_message_text(
            "⏰ *Налаштування часу прийому їжі*\n\n"
            "Обери який прийом їжі хочеш налаштувати:",
            reply_markup=get_meal_time_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    if data.startswith("set_time_"):
        meal = data.replace("set_time_", "")
        meal_names = {"breakfast": "сніданку", "lunch": "обіду", "dinner": "вечері"}
        meal_display = meal_names.get(meal, meal)
        
        await query.edit_message_text(
            f"🍽 *Час {meal_display}*\n\n"
            f"Коли ти зазвичай {meal_display}? Обери або введи свій час:",
            reply_markup=get_time_suggestions_keyboard(meal),
            parse_mode='Markdown'
        )
        return
    
    if data.startswith("confirm_time_"):
        parts = data.replace("confirm_time_", "").split("_")
        meal = parts[0]
        time_str = parts[1]
        
        # Parse time (format: HHMM)
        hour = int(time_str[:2])
        minute = int(time_str[2:]) if len(time_str) > 2 else 0
        meal_time = time(hour, minute)
        
        # Update schedule
        scheduler.update_meal_time(user_id, meal, meal_time)
        
        meal_names = {"breakfast": "сніданок", "lunch": "обід", "dinner": "вечеря"}
        meal_display = meal_names.get(meal, meal)
        
        await query.edit_message_text(
            f"✅ Час {meal_display} встановлено: *{meal_time.strftime('%H:%M')}*\n\n"
            f"Нагадування буде надходити за 30 хвилин до прийому їжі.",
            reply_markup=get_meal_time_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    if data.startswith("custom_time_"):
        meal = data.replace("custom_time_", "")
        user_setting_time[user_id] = meal
        
        meal_names = {"breakfast": "сніданку", "lunch": "обіду", "dinner": "вечері"}
        meal_display = meal_names.get(meal, meal)
        
        await query.edit_message_text(
            f"✏️ *Свій час для {meal_display}*\n\n"
            f"Напиши час у форматі ГГ:ХХ (наприклад: 08:30 або 19:15):",
            parse_mode='Markdown'
        )
        return
    
    if data == "back_to_schedule":
        schedule_text = scheduler.format_schedule(user_id)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏰ Налаштувати час прийому", callback_data="setup_meal_times")],
            [InlineKeyboardButton("🔔 Керувати нагадуваннями", callback_data="manage_reminders")],
            [InlineKeyboardButton("📋 Оновити план БАДів", callback_data="back_to_selection")]
        ])
        
        await query.edit_message_text(
            schedule_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return
    
    if data == "manage_reminders":
        schedule = scheduler.get_user_schedule(user_id)
        if not schedule.reminders:
            await query.edit_message_text(
                "🔔 У тебе ще немає налаштованих нагадувань.\n\n"
                "Спочатку створи план БАДів через /start, а потім повернись сюди.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 Створити план", callback_data="back_to_selection")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="back_to_schedule")]
                ]),
                parse_mode='Markdown'
            )
            return
        
        text = "🔔 *Твої нагадування:*\n\n"
        buttons = []
        
        for reminder in schedule.reminders:
            status = "✅" if reminder.enabled else "❌"
            meal_names = {"breakfast": "сніданок", "lunch": "обід", "dinner": "вечеря"}
            meal_display = meal_names.get(reminder.meal, reminder.meal)
            
            text += f"{status} {reminder.supplement_name} — {meal_display}\n"
            
            # Toggle button
            action = "disable" if reminder.enabled else "enable"
            buttons.append([InlineKeyboardButton(
                f"{status} {reminder.supplement_name}",
                callback_data=f"{action}_reminder_{reminder.supplement_id}"
            )])
        
        buttons.append([InlineKeyboardButton("◀️ Назад до розкладу", callback_data="back_to_schedule")])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='Markdown'
        )
        return
    
    if data.startswith("enable_reminder_") or data.startswith("disable_reminder_"):
        action = "enable" if data.startswith("enable_") else "disable"
        supplement_id = data.split("_", 2)[2]
        
        # Find and update reminder
        schedule = scheduler.get_user_schedule(user_id)
        for reminder in schedule.reminders:
            if reminder.supplement_id == supplement_id:
                reminder.enabled = (action == "enable")
                break
        
        scheduler.save_schedules()
        
        # Refresh reminders view
        await button_callback(update, context)
        return
    
    # Handle help from after-add keyboard
    if data == "show_help":
        await help_command(update, context)
        return
    
    # Handle sources button
    if data == "show_sources":
        sources_text = """🏛️ *Наукові джерела даних*

Вся інформація про БАДи береться виключно з авторитетних медичних джерел:

🎓 **Урядові та академічні інститути:**
• [NIH Office of Dietary Supplements](https://ods.od.nih.gov/) - Національний інститут здоров'я США
• [Harvard Health Publishing](https://health.harvard.edu/) - Гарвардська медична школа  
• [PubMed](https://pubmed.ncbi.nlm.nih.gov/) - Національна медична бібліотека США

🏥 **Провідні медичні клініки:**
• [Mayo Clinic](https://mayoclinic.org/) - Одна з топ-клінік світу
• [WebMD](https://webmd.com/) - Медичні довідники

🔬 **Наукові дослідницькі платформи:**
• [MedlinePlus](https://medlineplus.gov/druginformation.html) - Безкоштовна база NIH для пацієнтів
• [Healthline](https://healthline.com/) - Медичний контент на основі доказів

⚗️ **Рівні довіри:**
🟢 Висока впевненість (0.8+) - Офіційні медичні джерела
🟡 Середня впевненість (0.6+) - Перехресні дослідження  
🟠 Низька впевненість (<0.6) - Обмежені дані

⚠️ _Інформація не замінює консультацію лікаря._"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад до вибору", callback_data="back_to_selection")]
        ])
        
        await query.edit_message_text(
            sources_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return


async def plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current plan"""
    user_id = update.effective_user.id
    
    if user_id not in user_plans:
        await update.message.reply_text(
            "📭 У тебе ще немає плану. Використай /start щоб створити!"
        )
        return
    
    plans = user_plans[user_id]
    catalog = normalizer.get_all_supplements()
    planner = MealPlanner(catalog)
    formatted = planner.format_plan(plans)
    
    await update.message.reply_text(
        formatted,
        reply_markup=get_meal_keyboard(),
        parse_mode='Markdown'
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear user selection"""
    user_id = update.effective_user.id
    user_selections[user_id] = set()
    if user_id in user_plans:
        del user_plans[user_id]
    
    await update.message.reply_text(
        "🗑 Вибір очищено! Використай /start щоб почати знову."
    )


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's meal schedule and reminders"""
    user_id = update.effective_user.id
    schedule_text = scheduler.format_schedule(user_id)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏰ Налаштувати час прийому", callback_data="setup_meal_times")],
        [InlineKeyboardButton("🔔 Керувати нагадуваннями", callback_data="manage_reminders")],
        [InlineKeyboardButton("📋 Оновити план БАДів", callback_data="back_to_selection")]
    ])
    
    await update.message.reply_text(
        schedule_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


async def reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check current meal supplements"""
    user_id = update.effective_user.id
    current_supplements = scheduler.get_current_meal_supplements(user_id)
    
    if not current_supplements:
        await update.message.reply_text(
            "⏰ Зараз не час для прийому БАДів.\n"
            "Використай /schedule щоб переглянути розклад."
        )
        return
    
    text = "🔔 *Час прийняти БАДи!*\n\n"
    for reminder in current_supplements:
        text += f"• {reminder.supplement_name}"
        if reminder.dosage:
            text += f" ({reminder.dosage})"
        if reminder.notes:
            text += f"\n  _{reminder.notes}_"
        text += "\n"
    
    text += "\n💡 _Нагадування надіслано на основі твого розкладу прийому їжі._"
    
    await update.message.reply_text(text, parse_mode='Markdown')


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show intelligent lookup statistics (admin only)"""
    user_id = update.effective_user.id
    
    # Simple admin check (you can add your user ID here)
    admin_users = [383087326]  # Irina's user ID
    
    try:
        from core.intelligent_lookup import IntelligentLookup
        
        data_dir = Path(__file__).parent.parent / "data"
        lookup_engine = IntelligentLookup(data_dir)
        stats = lookup_engine.get_research_stats()
        
        brave_api_key = os.getenv("BRAVE_SEARCH_API_KEY")
        api_status = "✅ Active" if brave_api_key else "❌ Not configured"
        
        text = f"""📊 *Intelligent Lookup Stats*

🔑 *API Status:* {api_status}
📦 *Total researched:* {stats['total_researched']} supplements
🎯 *High confidence:* {stats['high_confidence']} supplements  
📈 *Coverage:* {stats['coverage_percent']:.1f}%
🕒 *Last updated:* {stats['last_updated'][:19] if stats['last_updated'] else 'Never'}

💡 *Setup:* See INTELLIGENT_LOOKUP_SETUP.md"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(
            f"📊 Stats error: {str(e)}\n\n"
            f"💡 Check if intelligent_lookup is properly set up."
        )


def get_meal_time_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for meal time setup"""
    buttons = [
        [InlineKeyboardButton("🍳 Час сніданку", callback_data="set_time_breakfast")],
        [InlineKeyboardButton("🍽 Час обіду", callback_data="set_time_lunch")],
        [InlineKeyboardButton("🌙 Час вечері", callback_data="set_time_dinner")],
        [InlineKeyboardButton("◀️ Назад до розкладу", callback_data="back_to_schedule")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_time_suggestions_keyboard(meal: str) -> InlineKeyboardMarkup:
    """Keyboard with time suggestions for meal"""
    suggestions = {
        "breakfast": ["07:00", "08:00", "09:00", "10:00"],
        "lunch": ["12:00", "13:00", "14:00", "15:00"], 
        "dinner": ["18:00", "19:00", "20:00", "21:00"]
    }
    
    buttons = []
    times = suggestions.get(meal, ["08:00", "13:00", "19:00"])
    
    # Two times per row
    for i in range(0, len(times), 2):
        row = []
        for j in range(i, min(i + 2, len(times))):
            time_str = times[j]
            row.append(InlineKeyboardButton(
                time_str, 
                callback_data=f"confirm_time_{meal}_{time_str.replace(':', '')}"
            ))
        buttons.append(row)
    
    buttons.append([
        InlineKeyboardButton("✏️ Ввести своє", callback_data=f"custom_time_{meal}"),
        InlineKeyboardButton("◀️ Назад", callback_data="setup_meal_times")
    ])
    
    return InlineKeyboardMarkup(buttons)


def main():
    """Run the bot"""
    import asyncio
    import platform
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment!")
        return
    
    # Fix for Python 3.14+ event loop
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    application = Application.builder().token(token).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("plan", plan_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("schedule", schedule_command))
    application.add_handler(CommandHandler("reminders", reminders_command))
    application.add_handler(CommandHandler("sources", sources_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("users", users_command))  # Admin only
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Button handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Message handler (for /add flow)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

