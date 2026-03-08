#!/usr/bin/env python3
"""
Simple deployment readiness check
"""
import os
import sys
from pathlib import Path

def check_files():
    """Check if all required files exist"""
    required_files = [
        "bot/telegram_bot.py",
        "requirements.txt", 
        "Procfile",
        "railway.toml",
        "runtime.txt",
        ".env"
    ]
    
    print("Checking required files...")
    all_good = True
    
    for file in required_files:
        if Path(file).exists():
            print(f"   OK: {file}")
        else:
            print(f"   MISSING: {file}")
            all_good = False
    
    return all_good

def check_env_vars():
    """Check environment variables"""
    print("\nChecking environment variables...")
    
    # Load .env file if exists
    if Path('.env').exists():
        from dotenv import load_dotenv
        load_dotenv()
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token:
        masked_token = f"{token[:10]}...{token[-4:]}" if len(token) > 14 else "***"
        print(f"   OK: TELEGRAM_BOT_TOKEN = {masked_token}")
        return True
    else:
        print("   MISSING: TELEGRAM_BOT_TOKEN")
        return False

def test_bot_imports():
    """Test if bot modules can be imported"""
    print("\nTesting bot imports...")
    
    try:
        # Add project to path
        sys.path.insert(0, str(Path('.').absolute()))
        
        # Try importing main modules
        from bot.telegram_bot import main
        from core.normalizer import SupplementNormalizer  
        from core.compatibility import CompatibilityChecker
        
        print("   OK: All bot modules import successfully")
        
        # Try creating instances
        normalizer = SupplementNormalizer()
        checker = CompatibilityChecker()
        
        print("   OK: Core components initialize successfully")
        return True
        
    except Exception as e:
        print(f"   ERROR: Bot startup test failed: {str(e)}")
        return False

def check_git_status():
    """Check git status"""
    print("\nChecking git status...")
    
    if Path('.git').exists():
        print("   OK: Git repository exists")
        return True
    else:
        print("   WARNING: No git repository (manual deployment needed)")
        return True  # Not critical

def main():
    print("SUPPLEMENT ASSISTANT - DEPLOY READINESS CHECK")
    print("=" * 50)
    
    checks = [
        check_files(),
        check_env_vars(), 
        test_bot_imports(),
        check_git_status()
    ]
    
    print("\n" + "=" * 50)
    
    if all(checks):
        print("ALL CHECKS PASSED! Ready for deployment!")
        print("\nNext steps:")
        print("   1. Push to GitHub (if using git)")
        print("   2. Deploy to Railway/Heroku")
        print("   3. Set TELEGRAM_BOT_TOKEN in cloud environment")
        print("   4. Test bot with /start")
        return True
    else:
        print("Some checks failed. Fix issues before deployment.")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)