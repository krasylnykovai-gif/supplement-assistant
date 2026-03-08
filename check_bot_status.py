#!/usr/bin/env python3
"""
Quick bot status check via Telegram API
"""
import os
import sys
import requests
from pathlib import Path

def load_env():
    """Load environment variables"""
    if Path('.env').exists():
        from dotenv import load_dotenv
        load_dotenv()
    
    return os.getenv('TELEGRAM_BOT_TOKEN')

def check_bot_status(token):
    """Check bot status via getMe API"""
    print("Checking bot status...")
    
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print("   OK: Bot is ACTIVE and responding!")
                print(f"   Bot name: {bot_info.get('first_name')}")
                print(f"   Username: @{bot_info.get('username')}")
                print(f"   Bot ID: {bot_info.get('id')}")
                return True
            else:
                print(f"   ERROR: API returned error: {data}")
                return False
        else:
            print(f"   ERROR: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ERROR: Request timeout (bot may be starting up)")
        return False
    except Exception as e:
        print(f"   ERROR: {str(e)}")
        return False

def check_webhook_status(token):
    """Check webhook status"""
    print("\nChecking webhook status...")
    
    try:
        url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data.get('result', {})
                webhook_url = webhook_info.get('url', '')
                
                if webhook_url:
                    print(f"   Webhook URL: {webhook_url}")
                    print(f"   Pending updates: {webhook_info.get('pending_update_count', 0)}")
                else:
                    print("   Using polling mode (no webhook)")
                
                return True
            else:
                print(f"   ERROR: {data}")
                return False
        else:
            print(f"   ERROR: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ERROR: {str(e)}")
        return False

def test_bot_command(token):
    """Test sending a command to bot"""
    print("\nTesting bot response (if you have chat_id)...")
    
    # This would require chat_id, so just show the curl command
    print("   To test manually, send this message:")
    print("   1. Open https://t.me/med11007_bot")
    print("   2. Send: /start")
    print("   3. Check if bot responds with supplement keyboard")
    
    return True

def main():
    print("BOT STATUS CHECK - @med11007_bot")
    print("=" * 40)
    
    token = load_env()
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN not found in .env")
        return False
    
    # Mask token for security
    masked_token = f"{token[:10]}...{token[-4:]}"
    print(f"Using token: {masked_token}")
    print()
    
    checks = [
        check_bot_status(token),
        check_webhook_status(token),
        test_bot_command(token)
    ]
    
    print("\n" + "=" * 40)
    
    if all(checks):
        print("STATUS: BOT IS ONLINE AND READY!")
        print("\nNext step: Test in Telegram:")
        print("   https://t.me/med11007_bot")
        return True
    else:
        print("STATUS: Some issues found")
        print("Check Railway/Heroku logs for details")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)