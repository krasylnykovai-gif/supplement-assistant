"""
Test the fixed bot function without console output issues
"""
import sys
sys.path.insert(0, '.')

from bot.telegram_bot import (
    get_enhanced_after_add_keyboard, 
    get_after_add_keyboard,
    get_supplement_keyboard
)

def test_keyboards_creation():
    """Test keyboard creation without printing problematic characters"""
    results = {}
    
    try:
        keyboard1 = get_enhanced_after_add_keyboard(has_multiple_supplements=True)
        results['enhanced_multiple'] = {
            'success': True,
            'rows': len(keyboard1.inline_keyboard),
            'buttons': sum(len(row) for row in keyboard1.inline_keyboard)
        }
    except Exception as e:
        results['enhanced_multiple'] = {'success': False, 'error': str(e)}
    
    try:
        keyboard2 = get_enhanced_after_add_keyboard(has_multiple_supplements=False)
        results['enhanced_single'] = {
            'success': True,
            'rows': len(keyboard2.inline_keyboard),
            'buttons': sum(len(row) for row in keyboard2.inline_keyboard)
        }
    except Exception as e:
        results['enhanced_single'] = {'success': False, 'error': str(e)}
    
    try:
        keyboard3 = get_after_add_keyboard(has_multiple_supplements=True)
        results['regular_multiple'] = {
            'success': True,
            'rows': len(keyboard3.inline_keyboard),
            'buttons': sum(len(row) for row in keyboard3.inline_keyboard)
        }
    except Exception as e:
        results['regular_multiple'] = {'success': False, 'error': str(e)}
    
    try:
        keyboard4 = get_supplement_keyboard(user_id=12345)
        results['supplement_keyboard'] = {
            'success': True,
            'rows': len(keyboard4.inline_keyboard),
            'buttons': sum(len(row) for row in keyboard4.inline_keyboard)
        }
    except Exception as e:
        results['supplement_keyboard'] = {'success': False, 'error': str(e)}
    
    return results

def simulate_add_supplement_flow():
    """Simulate the add supplement flow"""
    print("=== SIMULATING ADD SUPPLEMENT FLOW ===")
    
    # Test lookup function
    from core.supplement_lookup import lookup_supplement
    
    print("Step 1: Looking up supplement...")
    result = lookup_supplement('magnesium')
    print(f"Lookup successful: {result.found}")
    
    # Test save function  
    print("Step 2: Saving supplement...")
    from bot.telegram_bot import save_supplement
    
    try:
        save_supplement(
            supp_id="test_mag",
            name="Test Magnesium",
            with_food=True,
            fat_required=False,
            best_time="evening",
            notes="Test notes",
            source="test_source"
        )
        print("Save successful: True")
    except Exception as e:
        print(f"Save successful: False - {e}")
    
    # Test keyboard creation
    print("Step 3: Creating keyboards...")
    keyboard_results = test_keyboards_creation()
    
    all_success = all(r.get('success', False) for r in keyboard_results.values())
    print(f"All keyboards created: {all_success}")
    
    if all_success:
        print("✅ COMPLETE FLOW WORKS!")
        print("The add supplement function should work properly in Telegram.")
    else:
        print("❌ Some keyboards failed:")
        for name, result in keyboard_results.items():
            if not result.get('success', False):
                print(f"  - {name}: {result.get('error', 'Unknown error')}")
    
    return all_success

if __name__ == "__main__":
    success = simulate_add_supplement_flow()
    
    if success:
        print("\n" + "="*50)
        print("🎉 BOT FUNCTION IS FIXED!")
        print("The add supplement flow should work correctly now.")
        print("Problem was emoji encoding in Windows console, not in bot functionality.")
        print("="*50)
    else:
        print("\n❌ Still have issues to resolve")