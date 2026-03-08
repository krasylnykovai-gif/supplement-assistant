"""
Debug what happens with lecithin lookup specifically
"""
import sys
sys.path.insert(0, '.')

def debug_lecithin_lookup():
    """Debug the exact issue with lecithin"""
    from core.supplement_lookup import lookup_supplement, KNOWN_SUPPLEMENTS
    
    test_names = ['лецитин', 'lecithin', 'Лецитин']
    
    for name in test_names:
        print(f"\n=== Testing: {name} ===")
        
        # First check if it's in KNOWN_SUPPLEMENTS
        name_lower = name.lower().strip()
        if name_lower in KNOWN_SUPPLEMENTS:
            print(f"Found in KNOWN_SUPPLEMENTS: YES")
            info = KNOWN_SUPPLEMENTS[name_lower]
            print(f"  Name: {len(info.name)} chars")
            print(f"  Notes: {len(info.notes)} chars") 
            print(f"  Source: {len(info.source)} chars")
            print(f"  With food: {info.with_food}")
            print(f"  Best time: {info.best_time}")
        else:
            print(f"Found in KNOWN_SUPPLEMENTS: NO")
        
        # Now test lookup function
        try:
            result = lookup_supplement(name, use_intelligent_lookup=False, use_fuzzy_search=False)
            print(f"Lookup result found: {result.found}")
            if result.found:
                print(f"  Result name: {len(result.name)} chars")
                print(f"  Result notes: {len(result.notes)} chars")
                print(f"  Result source: {len(result.source)} chars")
                print(f"  Has HTTP source: {result.source.startswith('http') if result.source else False}")
            else:
                print(f"  Not found - notes: {result.notes[:50]}...")
        except Exception as e:
            print(f"Lookup ERROR: {type(e).__name__}: {str(e)[:100]}")
            import traceback
            traceback.print_exc()

def test_process_new_supplement_mock():
    """Test the core logic without Telegram objects"""
    from core.supplement_lookup import lookup_supplement
    from bot.telegram_bot import save_supplement, get_enhanced_after_add_keyboard
    
    name = "лецитин"
    user_id = 12345
    
    print(f"\n=== MOCK PROCESS NEW SUPPLEMENT: {name} ===")
    
    try:
        # Step 1: Lookup
        print("Step 1: Looking up supplement...")
        info = lookup_supplement(name)
        print(f"  Found: {info.found}")
        
        if not info.found:
            print("  PROBLEM: Supplement not found - would show manual input")
            return False
        
        # Step 2: Save
        print("Step 2: Saving supplement...")
        supp_id = name.lower().replace(' ', '_').replace('-', '_')
        supp_id = ''.join(c for c in supp_id if c.isalnum() or c == '_')
        
        save_supplement(
            supp_id=supp_id,
            name=info.name,
            with_food=info.with_food,
            fat_required=info.fat_required,
            best_time=info.best_time,
            notes=info.notes,
            source=info.source
        )
        print("  Saved successfully")
        
        # Step 3: Create message
        print("Step 3: Creating success message...")
        food_text = "з їжею" if info.with_food else "натщесерце"
        if info.fat_required:
            food_text += " (з жирами для кращого засвоєння)"
        
        time_display = {
            "morning": "🌅 вранці",
            "any": "🌤 будь-коли", 
            "evening": "🌙 ввечері"
        }
        
        # Create message
        text = f"✅ *{info.name}* успішно додано!\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        text += "📊 *Інформація про прийом:*\n"
        text += f"🍽️ *Спосіб:* {food_text}\n"
        text += f"⏰ *Оптимальний час:* {time_display.get(info.best_time, info.best_time)}\n\n"
        text += "💡 *Рекомендації:*\n"
        text += f"_{info.notes}_\n\n"
        
        # Add source with clickable link
        if info.source and info.source.startswith('http'):
            text += f"📚 *Наукове джерело:* [Детальна інформація]({info.source})\n\n"
        elif info.source:
            text += f"📚 *Джерело:* {info.source}\n\n"
        
        print(f"  Message created: {len(text)} chars")
        
        # Step 4: Create keyboard
        print("Step 4: Creating keyboard...")
        keyboard = get_enhanced_after_add_keyboard(has_multiple_supplements=False)
        print(f"  Keyboard created: {len(keyboard.inline_keyboard)} rows")
        
        print("SUCCESS: All steps completed!")
        print(f"Final message length: {len(text)}")
        print(f"Has source link: {info.source.startswith('http') if info.source else False}")
        
        return True
        
    except Exception as e:
        print(f"ERROR in step: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_lecithin_lookup()
    test_process_new_supplement_mock()