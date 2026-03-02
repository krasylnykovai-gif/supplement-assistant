#!/usr/bin/env python3
"""Test /users command functionality"""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add bot to path  
sys.path.insert(0, str(Path('.').absolute()))
from bot.telegram_bot import load_users_data, save_users_data, log_user_start

class MockUser:
    """Mock telegram user"""
    def __init__(self, user_id, username, first_name):
        self.id = user_id
        self.username = username
        self.first_name = first_name

def simulate_users_command():
    """Simulate what /users command would show"""
    print("=== SIMULATION: /users COMMAND ===")
    
    # Load current data (should be empty after reset)
    users_data = load_users_data()
    print(f"Current data: {users_data}")
    
    # Simulate admin user using the bot
    admin_user = MockUser(383087326, "irina_username", "Irina")
    print(f"Simulating admin user: {admin_user.first_name} (ID: {admin_user.id})")
    
    # Log admin start 
    is_new = log_user_start(admin_user)
    print(f"Admin logged as: {'NEW' if is_new else 'RETURNING'}")
    
    # Now simulate /users command response
    users_data = load_users_data()
    
    # Basic stats
    total_unique = users_data.get("total_unique", 0)
    
    # Today's stats
    today = datetime.now(timezone.utc).date().isoformat()
    today_stats = users_data.get("daily_stats", {}).get(today, {})
    today_new = today_stats.get("new_users", 0)
    today_active = len(today_stats.get("active_users", []))
    
    # Format like real bot response
    stats_text = f"""[ANALYTICS] User Statistics

[TOTAL STATS]
Total unique users: {total_unique}

[TODAY] ({today}):
New users: {today_new}
Active users: {today_active}

[TOP-5 MOST ACTIVE]:"""

    # Most active users
    for uid, details in users_data.get("user_details", {}).items():
        start_count = details.get("start_count", 0)
        first_name = details.get("first_name", "N/A")
        username = details.get("username", "N/A")
        username_text = f"@{username}" if username != "N/A" else "no username"
        stats_text += f"\n1. {first_name} ({username_text}) - {start_count} times"

    stats_text += f"\n\nData updated: {datetime.now(timezone.utc).strftime('%H:%M UTC')}"
    
    print("\n" + "="*50)
    print("BOT RESPONSE TO /users:")
    print("="*50)
    print(stats_text)
    print("="*50)
    
    return users_data

if __name__ == "__main__":
    result = simulate_users_command()