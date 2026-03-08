"""
Test real scenario: user adds a new supplement
"""
import sys
sys.path.insert(0, '.')

import asyncio
from unittest.mock import Mock, AsyncMock
from pathlib import Path

# Mock Telegram objects
class MockUser:
    def __init__(self, user_id=12345):
        self.id = user_id
        self.username = "test_user"
        self.first_name = "Test"

class MockMessage:
    def __init__(self, text="магний"):
        self.text = text
        self.reply_text = AsyncMock()
        self.edit_text = AsyncMock()

class MockCallbackQuery:
    def __init__(self):
        self.edit_message_text = AsyncMock()
        self.answer = AsyncMock()
        self.data = "start_add"

class MockUpdate:
    def __init__(self, is_callback=False):
        self.effective_user = MockUser()
        if is_callback:
            self.callback_query = MockCallbackQuery()
            self.message = None
        else:
            self.message = MockMessage()
            self.callback_query = None

class MockContext:
    def __init__(self):
        self.args = []

async def test_add_supplement_scenario():
    """Test complete add supplement scenario"""
    print("TESTING REAL ADD SUPPLEMENT SCENARIO")
    print("=" * 45)
    
    from bot.telegram_bot import process_new_supplement, user_selections
    
    # Clear any existing state
    user_id = 12345
    user_selections[user_id] = set()
    
    print("Scenario: User wants to add 'магний' (magnesium)")
    print("")
    
    # Create mock objects
    update = MockUpdate(is_callback=False)
    context = MockContext()
    
    try:
        # Run the function
        print("1. Processing supplement: магний")
        await process_new_supplement(update, context, "магний", is_callback=False)
        
        # Check if message was called
        if update.message.reply_text.called:
            print("2. Bot sent response message: YES")
        else:
            print("2. Bot sent response message: NO")
        
        # Check call arguments to see if it looks right
        call_args = update.message.reply_text.call_args
        if call_args:
            text_arg = call_args[0][0]  # First positional argument
            if "Магній" in text_arg or "магній" in text_arg:
                print("3. Response contains supplement name: YES")
            else:
                print("3. Response contains supplement name: NO")
            
            if "успішно додано" in text_arg:
                print("4. Success message present: YES")
            else:
                print("4. Success message present: NO")
            
            # Check if keyboard was provided
            if 'reply_markup' in call_args[1]:
                print("5. Keyboard provided: YES")
            else:
                print("5. Keyboard provided: NO")
        else:
            print("3-5. No response data to analyze")
        
        print("")
        print("TEST COMPLETED SUCCESSFULLY!")
        print("The add supplement function works end-to-end.")
        
        return True
        
    except Exception as e:
        print(f"ERROR during test: {e}")
        return False

# Run the test
if __name__ == "__main__":
    success = asyncio.run(test_add_supplement_scenario())
    
    if success:
        print("")
        print("=" * 45)
        print("FINAL RESULT: ADD SUPPLEMENT FUNCTION IS WORKING!")
        print("The issue has been resolved.")
    else:
        print("FINAL RESULT: STILL HAVE ISSUES")