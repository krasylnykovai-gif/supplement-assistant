#!/usr/bin/env python3
"""Check bot status and deployment"""
import requests
import os
from dotenv import load_dotenv
from pathlib import Path

def check_bot_status():
    """Check if bot token is valid and bot is accessible"""
    print("=== SUPPLEMENT ASSISTANT BOT - STATUS CHECK ===")
    
    # Load environment
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN not found in .env")
        return
    
    print(f"Bot token: {token[:15]}...{token[-4:]}")
    
    # Check bot via Telegram API
    try:
        response = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=10)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info['ok']:
                result = bot_info['result']
                print("[OK] Bot token is VALID!")
                print(f"Bot name: {result['first_name']}")
                print(f"Bot username: @{result['username']}")
                print(f"Bot ID: {result['id']}")
                
                # Check if bot is running (webhook or polling)
                webhook_response = requests.get(f'https://api.telegram.org/bot{token}/getWebhookInfo', timeout=10)
                if webhook_response.status_code == 200:
                    webhook_info = webhook_response.json()
                    if webhook_info['ok']:
                        webhook_url = webhook_info['result'].get('url', '')
                        if webhook_url:
                            print(f"[WEBHOOK] Bot deployed at: {webhook_url}")
                            print("[STATUS] Bot is DEPLOYED and running via webhook")
                        else:
                            print("[WEBHOOK] No webhook set - bot running via polling or not deployed")
                            print("[ACTION] Bot needs to be running locally or deployed to cloud")
                            
                return True
            else:
                print("[ERROR] Bot API error:", bot_info)
                return False
        else:
            print(f"[ERROR] API request failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    check_bot_status()