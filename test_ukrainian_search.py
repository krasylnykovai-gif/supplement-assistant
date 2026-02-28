"""
Test Ukrainian and Russian supplement search
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.supplement_lookup import lookup_supplement


def test_ukrainian_russian():
    print("TESTING UKRAINIAN AND RUSSIAN SEARCH")
    print("====================================")
    
    # Test Ukrainian and Russian names
    test_queries = [
        # Ukrainian
        ("магній", "Should find magnesium"),
        ("вітамін д", "Should find vitamin d"), 
        ("омега 3", "Should find omega 3"),
        ("мелатонін", "Should find melatonin"),
        ("коензим q10", "Should find coq10"),
        
        # Russian
        ("магний", "Should find magnesium"),
        ("витамин д", "Should find vitamin d"),
        ("омега 3", "Should find omega 3"),
        ("мелатонин", "Should find melatonin"),
        ("рыбий жир", "Should find fish oil"),
        
        # Mixed/partial
        ("креатин", "Should find creatine"),
        ("цинк", "Should find zinc"),
        ("кальцій", "Should find calcium"),
        ("пробіотики", "Should find probiotics"),
        
        # Typos in Ukrainian/Russian
        ("вітамин ц", "Ukrainian vitamin c"),
        ("магнезій", "Alternative magnesium spelling"),
    ]
    
    for query, expected in test_queries:
        print(f"\nTesting: '{query}'")
        print(f"Expected: {expected}")
        
        try:
            result = lookup_supplement(query, use_intelligent_lookup=False, use_fuzzy_search=True)
            
            if result.found:
                # Try to display name safely
                try:
                    display_name = result.name.encode('ascii', 'ignore').decode()
                    if not display_name:
                        display_name = "[non-ascii name]"
                except:
                    display_name = "[name display error]"
                
                print(f"  OK: Found as '{display_name}'")
                print(f"  Time: {result.best_time}")
                print(f"  Food: {result.with_food}")
                
                if "Corrected" in result.notes or "corrected" in result.notes:
                    print(f"  Method: Typo correction")
                elif "similarity" in result.notes or "схожістю" in result.notes:
                    print(f"  Method: Fuzzy search")
                else:
                    print(f"  Method: Direct match")
            else:
                print(f"  NOT FOUND")
                
                # Try suggestions
                from core.supplement_lookup import get_supplement_suggestions
                suggestions = get_supplement_suggestions(query)
                if suggestions:
                    safe_suggestions = []
                    for sugg in suggestions[:3]:
                        try:
                            safe_sugg = sugg.encode('ascii', 'ignore').decode()
                            if safe_sugg:
                                safe_suggestions.append(safe_sugg)
                        except:
                            safe_suggestions.append("[suggestion]")
                    
                    if safe_suggestions:
                        print(f"  Suggestions: {', '.join(safe_suggestions)}")
                else:
                    print(f"  No suggestions")
                
        except Exception as e:
            print(f"  ERROR: {str(e)}")


if __name__ == "__main__":
    test_ukrainian_russian()