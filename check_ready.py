#!/usr/bin/env python3
"""
Check deployment readiness for Supplement Assistant
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
            print(f"   [OK] {file}")
        else:
            print(f"   [MISSING] {file}")
            all_good = False
    
    return all_good

def check_env_vars():
    """Check environment variables"""
    print("\nChecking environment variables...")
    
    # Load .env file if exists
    if Path('.env').exists():
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            print("   [WARNING] python-dotenv not installed, reading .env manually")
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
    
    required_vars = ["TELEGRAM_BOT_TOKEN"]
    optional_vars = ["BRAVE_SEARCH_API_KEY", "OPENAI_API_KEY"]
    
    all_good = True
    
    for var in required_vars:
        if os.getenv(var):
            token = os.getenv(var)
            masked_token = f"{token[:10]}...{token[-4:]}" if len(token) > 14 else "***"
            print(f"   [OK] {var} = {masked_token}")
        else:
            print(f"   [ERROR] {var} - NOT SET!")
            all_good = False
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"   [OPTIONAL] {var} = configured")
        else:
            print(f"   [OPTIONAL] {var} = not set")
    
    return all_good

def check_dependencies():
    """Check if all dependencies can be imported"""
    print("\nChecking dependencies...")
    
    required_modules = [
        ("telegram", "python-telegram-bot"),
        ("requests", "requests")
    ]
    
    optional_modules = [
        ("dotenv", "python-dotenv"), 
        ("aiohttp", "aiohttp"),
        ("openai", "openai")
    ]
    
    all_good = True
    
    for module, package in required_modules:
        try:
            __import__(module)
            print(f"   [OK] {package}")
        except ImportError:
            print(f"   [ERROR] {package} - NOT INSTALLED!")
            all_good = False
    
    for module, package in optional_modules:
        try:
            __import__(module) 
            print(f"   [OPTIONAL] {package}")
        except ImportError:
            print(f"   [OPTIONAL] {package} - not installed")
    
    return all_good

def test_bot_startup():
    """Test if bot can start without errors"""
    print("\nTesting bot startup...")
    
    try:
        # Add project to path
        sys.path.insert(0, str(Path('.').absolute()))
        
        # Try importing main modules
        from core.normalizer import SupplementNormalizer  
        from core.compatibility import CompatibilityChecker
        
        print("   [OK] Core modules import successfully")
        
        # Try creating instances
        normalizer = SupplementNormalizer()
        checker = CompatibilityChecker()
        
        print("   [OK] Core components initialize successfully")
        return True
        
    except Exception as e:
        print(f"   [ERROR] Bot startup test failed: {str(e)}")
        return False

def main():
    print("SUPPLEMENT ASSISTANT - DEPLOY READINESS CHECK")
    print("=" * 50)
    
    checks = [
        check_files(),
        check_env_vars(), 
        check_dependencies(),
        test_bot_startup()
    ]
    
    print("\n" + "=" * 50)
    
    if all(checks):
        print("[SUCCESS] ALL CHECKS PASSED! Ready for deployment!")
        print("\nNext steps:")
        print("   1. Push to GitHub")
        print("   2. Deploy to Railway/Heroku")
        print("   3. Set TELEGRAM_BOT_TOKEN in cloud environment")
        print("   4. Test bot with /start")
        return 0
    else:
        print("[FAILED] Some checks failed. Fix issues before deployment.")
        print("\nCheck the output above and fix missing components.")
        return 1

if __name__ == "__main__":
    sys.exit(main())