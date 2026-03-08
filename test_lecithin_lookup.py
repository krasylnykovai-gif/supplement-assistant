"""
Test lecithin lookup specifically
"""
import sys
sys.path.insert(0, '.')

def test_lecithin_lookup():
    """Test the specific supplement that user tried"""
    from core.supplement_lookup import lookup_supplement
    
    test_names = ['лецитин', 'lecithin', 'Лецитин']
    
    for name in test_names:
        try:
            result = lookup_supplement(name, use_intelligent_lookup=False, use_fuzzy_search=False)
            print(f"Testing: '{name}'")
            print(f"  Found: {result.found}")
            if result.found:
                print(f"  Has name: {bool(result.name)}")
                print(f"  Has notes: {bool(result.notes)}")
                print(f"  Has source: {bool(result.source)}")
                print(f"  With food: {result.with_food}")
                print(f"  Best time: {result.best_time}")
            print()
        except Exception as e:
            print(f"Testing: '{name}' - ERROR: {e}")
            print()

def test_supplement_save():
    """Test if we can save a supplement"""
    try:
        from bot.telegram_bot import save_supplement
        
        save_supplement(
            supp_id="test_lecithin",
            name="Test Lecithin", 
            with_food=True,
            fat_required=False,
            best_time="any",
            notes="Test notes",
            source="test"
        )
        print("Save supplement: SUCCESS")
    except Exception as e:
        print(f"Save supplement: ERROR - {e}")

def test_keyboard_creation():
    """Test keyboard creation"""
    try:
        from bot.telegram_bot import get_enhanced_after_add_keyboard
        
        keyboard = get_enhanced_after_add_keyboard(has_multiple_supplements=True)
        print(f"Keyboard creation: SUCCESS - {len(keyboard.inline_keyboard)} rows")
    except Exception as e:
        print(f"Keyboard creation: ERROR - {e}")

if __name__ == "__main__":
    print("TESTING LECITHIN LOOKUP ISSUE")
    print("=" * 40)
    test_lecithin_lookup()
    test_supplement_save()
    test_keyboard_creation()
    print("=" * 40)