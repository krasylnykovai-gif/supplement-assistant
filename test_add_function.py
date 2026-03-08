"""
Test the add supplement function to find the issue
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up environment
from dotenv import load_dotenv
load_dotenv()

from core.supplement_lookup import lookup_supplement
from bot.telegram_bot import get_enhanced_after_add_keyboard, get_after_add_keyboard

def test_lookup():
    """Test the supplement lookup function"""
    print("=== Testing supplement lookup ===")
    
    # Test known supplement
    try:
        result = lookup_supplement('magnesium')
        print(f"1. Known supplement (magnesium):")
        print(f"   - Found: {result.found}")
        print(f"   - Name: {result.name}")  
        print(f"   - With food: {result.with_food}")
        print(f"   - Best time: {result.best_time}")
        print(f"   - Source: {result.source}")
        print()
    except Exception as e:
        print(f"Error testing magnesium: {e}")
    
    # Test unknown supplement
    try:
        result2 = lookup_supplement('unknown supplement xyz')
        print(f"2. Unknown supplement:")
        print(f"   - Found: {result2.found}")
        print(f"   - Name: {result2.name}")
        print(f"   - With food: {result2.with_food}")
        print(f"   - Best time: {result2.best_time}")
        print(f"   - Notes: {result2.notes}")
        print()
    except Exception as e:
        print(f"Error testing unknown supplement: {e}")

def test_keyboards():
    """Test keyboard generation"""
    print("=== Testing keyboards ===")
    
    try:
        # Test enhanced keyboard with multiple supplements
        keyboard1 = get_enhanced_after_add_keyboard(has_multiple_supplements=True)
        print(f"1. Keyboard with multiple supplements: {len(keyboard1.inline_keyboard)} rows")
        for i, row in enumerate(keyboard1.inline_keyboard):
            print(f"   Row {i}: {[btn.text for btn in row]}")
        print()
        
        # Test enhanced keyboard with single supplement
        keyboard2 = get_enhanced_after_add_keyboard(has_multiple_supplements=False)
        print(f"2. Keyboard with single supplement: {len(keyboard2.inline_keyboard)} rows")
        for i, row in enumerate(keyboard2.inline_keyboard):
            print(f"   Row {i}: {[btn.text for btn in row]}")
        print()
        
        # Test regular after-add keyboard
        keyboard3 = get_after_add_keyboard(has_multiple_supplements=True)
        print(f"3. Regular after-add keyboard: {len(keyboard3.inline_keyboard)} rows")
        for i, row in enumerate(keyboard3.inline_keyboard):
            print(f"   Row {i}: {[btn.text for btn in row]}")
        print()
        
    except Exception as e:
        print(f"Error testing keyboards: {e}")

def test_save_supplement():
    """Test the save supplement function"""
    print("=== Testing save supplement ===")
    
    try:
        from bot.telegram_bot import save_supplement
        
        # Test saving a new supplement
        save_supplement(
            supp_id="test_supplement",
            name="Test Supplement",
            with_food=True,
            fat_required=False,
            best_time="morning",
            notes="Test notes",
            source="test_source"
        )
        print("Successfully saved test supplement")
        
        # Check if it was saved
        from core.normalizer import SupplementNormalizer
        normalizer = SupplementNormalizer()
        all_supplements = normalizer.get_all_supplements()
        
        if 'test_supplement' in all_supplements:
            print("Test supplement found in catalog!")
            supp_data = all_supplements['test_supplement']
            print(f"   - Name: {supp_data.get('name')}")
            print(f"   - Category: {supp_data.get('category')}")
            print(f"   - With food: {supp_data.get('timing', {}).get('with_food')}")
            print(f"   - Best time: {supp_data.get('timing', {}).get('best_time')}")
            print(f"   - Source: {supp_data.get('source')}")
        else:
            print("Test supplement NOT found in catalog")
        
    except Exception as e:
        print(f"Error testing save supplement: {e}")

if __name__ == "__main__":
    test_lookup()
    test_keyboards()
    test_save_supplement()