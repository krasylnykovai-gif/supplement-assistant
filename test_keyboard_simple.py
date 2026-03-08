"""
Simple keyboard test to isolate the encoding issue
"""
import sys
sys.path.insert(0, '.')

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def test_basic_keyboard():
    """Test basic keyboard without complex formatting"""
    print("Testing basic keyboard...")
    
    try:
        button1 = InlineKeyboardButton("Test Button 1", callback_data="test1")
        print("Basic button 1: OK")
    except Exception as e:
        print(f"Basic button 1 error: {e}")
        
    try:
        button2 = InlineKeyboardButton("Перевірити сумісність", callback_data="test2")
        print("Basic button 2: OK")
    except Exception as e:
        print(f"Basic button 2 error: {e}")
    
    try:
        button3 = InlineKeyboardButton("📅 Plan", callback_data="test3")
        print("Basic button 3 (with emoji): OK")
    except Exception as e:
        print(f"Basic button 3 error: {e}")
    
    try:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Simple test", callback_data="simple")]
        ])
        print("Simple keyboard: OK")
    except Exception as e:
        print(f"Simple keyboard error: {e}")

def test_problematic_text():
    """Test specific text that might be causing issues"""
    problematic_texts = [
        "Перевірити сумісність БАДів",
        "📅 Створити план прийому", 
        "+ Додати ще один БАД",
        "📋 Переглянути всі мої БАДи",
        "+ Додати ще БАДів",
        "📚 Наукові джерела",
        "Як користуватися ботом"
    ]
    
    for i, text in enumerate(problematic_texts):
        try:
            button = InlineKeyboardButton(text, callback_data=f"test{i}")
            print(f"Text {i}: '{text}' - OK")
        except Exception as e:
            print(f"Text {i}: '{text}' - ERROR: {e}")

if __name__ == "__main__":
    test_basic_keyboard()
    print("="*50)
    test_problematic_text()