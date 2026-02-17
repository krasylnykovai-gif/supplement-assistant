"""
Telegram Bot for Supplement Assistant
Event-driven: user selects supplements → compatibility check → meal-based plan
"""
import os
import json
import logging
from pathlib import Path
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
from core.supplement_lookup import lookup_supplement

# Paths
CATALOG_PATH = Path(__file__).parent.parent / "data" / "supplement_catalog.json"

# Initialize components
normalizer = SupplementNormalizer()
compatibility_checker = CompatibilityChecker()

# User state storage
user_selections = {}  # user_id -> set of supplement_ids
user_plans = {}       # user_id -> generated plan
user_adding = {}      # user_id -> True if in adding mode


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
        InlineKeyboardButton("➕ Додати БАД", callback_data="start_add")
    ])
    buttons.append([
        InlineKeyboardButton("🔍 Перевірити сумісність", callback_data="check_compatibility"),
        InlineKeyboardButton("📅 Побудувати план", callback_data="build_plan")
    ])
    buttons.append([
        InlineKeyboardButton("🗑 Очистити вибір", callback_data="clear_selection")
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


def get_after_add_keyboard() -> InlineKeyboardMarkup:
    """Keyboard shown after adding a supplement"""
    buttons = [
        [InlineKeyboardButton("➕ Додати ще один", callback_data="start_add")],
        [InlineKeyboardButton("◀️ До списку БАДів", callback_data="back_to_selection")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_not_found_keyboard(name: str) -> InlineKeyboardMarkup:
    """Keyboard when supplement info not found - ask user"""
    buttons = [
        [
            InlineKeyboardButton("🍽 З їжею", callback_data=f"manual_food_yes:{name}"),
            InlineKeyboardButton("⏰ Натщесерце", callback_data=f"manual_food_no:{name}")
        ],
        [InlineKeyboardButton("❌ Скасувати", callback_data="cancel_add")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_time_keyboard(name: str, with_food: bool) -> InlineKeyboardMarkup:
    """Keyboard for time selection (manual flow)"""
    food_flag = "yes" if with_food else "no"
    buttons = [
        [
            InlineKeyboardButton("🌅 Ранок", callback_data=f"manual_time_morning:{name}:{food_flag}"),
            InlineKeyboardButton("🌤 Будь-коли", callback_data=f"manual_time_any:{name}:{food_flag}"),
            InlineKeyboardButton("🌙 Вечір", callback_data=f"manual_time_evening:{name}:{food_flag}")
        ],
        [InlineKeyboardButton("❌ Скасувати", callback_data="cancel_add")]
    ]
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - show welcome and supplement selection"""
    user_id = update.effective_user.id
    user_selections[user_id] = set()
    user_adding.pop(user_id, None)
    
    welcome_text = """👋 *Вітаю! Я твій помічник з БАДів*

🎯 *Що я вмію:*
• Перевіряти сумісність добавок
• Будувати план прийому до сніданку/обіду/вечері
• Шукати інформацію про нові БАДи

📝 *Як користуватись:*
1. Обери БАДи, які приймаєш ⬇️
2. Натисни "Перевірити сумісність"
3. Отримай план прийому

➕ Немає потрібного БАДу? Натисни "Додати БАД"!

⚠️ _Це не медична порада. При сумнівах консультуйся з лікарем._

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
    
    # Check if already exists
    existing = normalizer.normalize(name)
    if existing:
        text = f"ℹ️ *{name}* вже є у списку!\n\nОбери його зі списку БАДів."
        keyboard = get_after_add_keyboard()
        
        if is_callback:
            await update.callback_query.edit_message_text(
                text, reply_markup=keyboard, parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text, reply_markup=keyboard, parse_mode='Markdown'
            )
        return
    
    # Lookup supplement info
    info = lookup_supplement(name)
    
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
        
        # Format response
        food_text = "з їжею" if info.with_food else "натщесерце"
        if info.fat_required:
            food_text += " (потребує жирів)"
        
        time_display = {
            "morning": "🌅 ранок",
            "any": "🌤 будь-коли",
            "evening": "🌙 вечір"
        }
        
        text = (
            f"✅ *{info.name}* додано!\n\n"
            f"📋 *Прийом:* {food_text}\n"
            f"⏰ *Час:* {time_display.get(info.best_time, info.best_time)}\n"
            f"💡 *Примітка:* {info.notes}\n"
        )
        if info.source:
            text += f"📚 *Джерело:* {info.source}\n"
        
        keyboard = get_after_add_keyboard()
        user_adding.pop(user_id, None)
        
    else:
        # Not found - ask user
        text = (
            f"🔍 *{name}*\n\n"
            f"Не знайшов автоматично інформацію про цей БАД.\n"
            f"Підкажи, як його приймати?"
        )
        keyboard = get_not_found_keyboard(name)
    
    if is_callback:
        await update.callback_query.edit_message_text(
            text, reply_markup=keyboard, parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text, reply_markup=keyboard, parse_mode='Markdown'
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (for /add flow)"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if user_id in user_adding:
        # User is adding a supplement - treat message as supplement name
        await process_new_supplement(update, context, text, is_callback=False)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    help_text = """📚 *Команди:*

/start - Почати вибір БАДів
/add - Додати новий БАД
/add Назва - Швидке додавання
/plan - Показати поточний план
/clear - Очистити вибір
/help - Ця довідка

*Джерела даних:*
• NIH Office of Dietary Supplements
• Examine.com
• PubMed

⚠️ _Інформація базується на наукових дослідженнях._"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


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
    
    # Manual flow - food choice
    if data.startswith("manual_food_"):
        parts = data.split(":", 1)
        with_food = "yes" in parts[0]
        name = parts[1] if len(parts) > 1 else "БАД"
        
        await query.edit_message_text(
            f"➕ *{name}*\n\nКоли краще приймати?",
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
            notes="Додано вручну",
            source="user_manual"
        )
        
        food_text = "з їжею" if with_food else "натщесерце"
        time_display = {"morning": "🌅 ранок", "any": "🌤 будь-коли", "evening": "🌙 вечір"}
        
        user_adding.pop(user_id, None)
        
        await query.edit_message_text(
            f"✅ *{name.title()}* додано!\n\n"
            f"📋 *Прийом:* {food_text}\n"
            f"⏰ *Час:* {time_display.get(time_part, time_part)}\n",
            reply_markup=get_after_add_keyboard(),
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
        
        await query.edit_message_text(
            "✅ План готовий! Обери прийом їжі:",
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
        text = f"*Обрано БАДів: {selected_count}*\n\nОбери або зміни вибір:"
        
        await query.edit_message_text(
            text,
            reply_markup=get_supplement_keyboard(user_id),
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


def main():
    """Run the bot"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment!")
        return
    
    application = Application.builder().token(token).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("plan", plan_command))
    application.add_handler(CommandHandler("clear", clear_command))
    
    # Button handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Message handler (for /add flow)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
