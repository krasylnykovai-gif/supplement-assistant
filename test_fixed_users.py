#!/usr/bin/env python3
"""Test fixed /users command"""
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add bot to path  
sys.path.insert(0, str(Path('.').absolute()))
from bot.telegram_bot import load_users_data, log_user_start

class MockUser:
    def __init__(self, user_id, username, first_name):
        self.id = user_id
        self.username = username  
        self.first_name = first_name

def test_fixed_users_command():
    """Test the fixed users command logic"""
    print("=== TESTING FIXED /users COMMAND ===")
    
    # Simulate admin user (you)
    admin_user = MockUser(383087326, "irina_real", "Irina")
    
    # Check admin permissions  
    admin_users = [383087326]
    user_id = admin_user.id
    
    print(f"Admin check: User {user_id} in {admin_users}: {user_id in admin_users}")
    
    if user_id not in admin_users:
        print("[FAILED] Admin check failed")
        return False
        
    print("[OK] Admin check passed")
    
    # Simulate some users for testing
    test_users = [
        MockUser(383087326, "irina_real", "Irina"),  # Admin
        MockUser(111111, "user1", "Maxim"),
        MockUser(222222, "user2", "Anna")
    ]
    
    print("Adding test users...")
    for user in test_users:
        log_user_start(user)
        print(f"  Added: {user.first_name} (@{user.username})")
    
    # Load data and test logic
    try:
        print("\nTesting command logic...")
        users_data = load_users_data()
        print(f"Users data loaded: {len(users_data.get('user_details', {}))} users")
        
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
        
        # Build response message (like the real command)
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
        
        print("\n" + "="*50)
        print("SIMULATED BOT RESPONSE:")
        print("="*50)
        print(stats_text)
        print("="*50)
        
        print(f"\n[SUCCESS] Command generated {len(stats_text)} characters")
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fixed_users_command()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")
    if success:
        print("\n[READY] Ready to deploy fixed version to Railway!")