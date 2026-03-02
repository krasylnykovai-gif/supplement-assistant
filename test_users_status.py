#!/usr/bin/env python3
"""Test current users status"""
import sys
from pathlib import Path

# Add bot to path
sys.path.insert(0, str(Path('.').absolute()))
from bot.telegram_bot import load_users_data

def check_users_status():
    """Check current users statistics"""
    print("=== SUPPLEMENT ASSISTANT BOT - USER STATISTICS ===")
    
    data = load_users_data()
    
    print(f"Total unique users: {data.get('total_unique', 0)}")
    print(f"User records: {len(data.get('user_details', {}))}")
    print(f"Days with activity: {len(data.get('daily_stats', {}))}")
    
    if data.get('user_details'):
        print("\nUser details:")
        for uid, details in data['user_details'].items():
            username = details.get('username', 'N/A')
            first_name = details.get('first_name', 'N/A') 
            start_count = details.get('start_count', 0)
            print(f"  {first_name} (@{username}) - {start_count} times")
    else:
        print("\nNo users found - data has been reset to collect real stats.")
    
    print(f"\nAdmin user ID in code: 383087326")
    print("Make sure this matches your Telegram user ID for /users command access.")

if __name__ == "__main__":
    check_users_status()