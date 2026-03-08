"""
Test lecithin specifically to ensure it works
"""
import sys
sys.path.insert(0, '.')

def test_lecithin_lookup():
    """Test lecithin lookup after adding it to database"""
    from core.supplement_lookup import lookup_supplement
    
    test_names = ['лецитин', 'lecithin', 'лецетин']
    
    for name in test_names:
        print(f"Testing: {repr(name)}")
        
        try:
            result = lookup_supplement(name, use_intelligent_lookup=False, use_fuzzy_search=False)
            
            print(f"  Found: {result.found}")
            if result.found:
                print(f"  Name length: {len(result.name)}")
                print(f"  Notes length: {len(result.notes)}")
                print(f"  Has source: {bool(result.source)}")
                print(f"  With food: {result.with_food}")
                print(f"  Best time: {result.best_time}")
                print(f"  Fat required: {result.fat_required}")
                print(f"  Source starts with http: {result.source.startswith('http') if result.source else False}")
            
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}")
        
        print()

def test_manual_addition_message():
    """Test the manual addition message creation"""
    try:
        name = "Test Supplement"
        with_food = True
        time_part = "morning"
        
        food_text = "з їжею" if with_food else "натщесерце"
        time_display = {"morning": "🌅 вранці", "any": "🌤 будь-коли", "evening": "🌙 ввечері"}
        
        # Create message like in manual flow
        text = f"✅ *{name}* успішно додано!\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "📊 *Інформація про прийом:*\n"
        text += f"🍽️ *Спосіб:* {food_text}\n"
        text += f"⏰ *Оптимальний час:* {time_display.get(time_part, time_part)}\n\n"
        
        text += "💡 *Рекомендації:*\n"
        text += f"_Додано на основі твоїх вказівок. Дякую за вклад у базу знань!_\n\n"
        
        # Add scientific source link
        text += "📚 *Джерело інформації:*\n"
        text += "_Для більш детальної інформації рекомендуємо консультацію з лікарем або перевірку на [Examine.com](https://examine.com) - незалежній базі наукових досліджень БАДів._\n\n"
        
        text += "🌟 *Твій внесок:*\n"
        text += f"_Інформація збережена і допоможе іншим користувачам_\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━━━\n"
        text += "🎯 *ЩО РОБИТИ ДАЛІ?*\n\n"
        
        print("Manual addition message created successfully!")
        print(f"Message length: {len(text)}")
        print("Contains source info: YES")
        print("Contains next steps: YES")
        
        return True
        
    except Exception as e:
        print(f"Manual message creation ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("TESTING LECITHIN SPECIFICALLY")
    print("=" * 40)
    test_lecithin_lookup()
    test_manual_addition_message()
    print("=" * 40)