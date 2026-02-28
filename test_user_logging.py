#!/usr/bin/env python3
"""
Test user logging functionality
"""
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project to path
sys.path.insert(0, str(Path('.').absolute()))

from bot.telegram_bot import log_user_start, load_users_data, save_users_data

class MockUser:
    """Mock telegram user for testing"""
    def __init__(self, user_id, username, first_name):
        self.id = user_id
        self.username = username
        self.first_name = first_name

def test_user_logging():
    """Test the user logging system"""
    print("Testing User Logging System")
    print("=" * 40)
    
    # Create mock users
    test_users = [
        MockUser(12345, "test_user_1", "Alice"),
        MockUser(67890, "test_user_2", "Bob"), 
        MockUser(12345, "test_user_1", "Alice"),  # Same user again
        MockUser(11111, None, "Charlie"),  # No username
        MockUser(22222, "test_user_4", None),  # No first name
    ]
    
    print("Testing with mock users:")
    for user in test_users:
        print(f"  ID: {user.id}, @{user.username}, {user.first_name}")
    
    print("\nProcessing users...")
    
    for user in test_users:
        is_new = log_user_start(user)
        status = "NEW" if is_new else "RETURNING"
        print(f"  {status}: {user.first_name} (@{user.username}) ID:{user.id}")
    
    print("\nFinal statistics:")
    users_data = load_users_data()
    
    print(f"  Total unique users: {users_data['total_unique']}")
    print(f"  Users in list: {len(users_data['unique_users'])}")
    
    today = datetime.now(timezone.utc).date().isoformat()
    today_stats = users_data.get("daily_stats", {}).get(today, {})
    print(f"  New users today: {today_stats.get('new_users', 0)}")
    print(f"  Active users today: {len(today_stats.get('active_users', []))}")
    
    print("\nUser details:")
    for user_id, details in users_data["user_details"].items():
        print(f"  {details['first_name']} (@{details['username']}) - {details['start_count']} times")
    
    print("\nUser logging test completed!")
    print(f"Data saved to: {Path('data/users.json').absolute()}")

if __name__ == "__main__":
    test_user_logging()