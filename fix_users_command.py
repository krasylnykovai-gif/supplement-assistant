#!/usr/bin/env python3
"""Fix /users command - improved version with better error handling"""

# This is the FIXED version of users_command function
# Copy this to replace the original function in bot/telegram_bot.py

FIXED_USERS_COMMAND = '''
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
        stats_text = "\\n".join(stats_lines)
        
        logger.info(f"Sending users stats: {len(stats_text)} characters")
        await update.message.reply_text(stats_text)
        
        logger.info("Users command completed successfully")
        
    except Exception as e:
        logger.error(f"Error in users_command: {str(e)}", exc_info=True)
        await update.message.reply_text(
            f"❌ Помилка отримання статистики: {str(e)}"
        )
'''

if __name__ == "__main__":
    print("=== FIXED /users COMMAND ===")
    print("Copy the function above to replace users_command in bot/telegram_bot.py")
    print("Key improvements:")
    print("- Better error handling and logging")
    print("- Simplified text formatting (no markdown)")
    print("- Safe data processing") 
    print("- More detailed debug output")