"""
Test truly new/unknown supplements
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.supplement_lookup import lookup_supplement


def test_new_supplements():
    print("TESTING NEW/UNKNOWN SUPPLEMENTS")
    print("===============================")
    
    # Test supplements that should NOT be in our basic database
    new_supplements = [
        "rhodiola rosea",
        "bacopa monnieri", 
        "lion's mane",
        "cordyceps",
        "reishi mushroom",
        "milk thistle",
        "saw palmetto",
        "ginkgo biloba",
        "st john's wort",
        "valerian root",
        "passionflower",
        "lemon balm",
        "unknown supplement xyz",
    ]
    
    found_count = 0
    intelligent_count = 0
    suggested_count = 0
    
    print(f"Testing {len(new_supplements)} potentially new supplements...")
    print()
    
    for i, supplement in enumerate(new_supplements, 1):
        print(f"{i:2d}. Testing: '{supplement}'")
        
        try:
            # Test with intelligent lookup enabled
            result = lookup_supplement(supplement, use_intelligent_lookup=True, use_fuzzy_search=True)
            
            if result.found:
                found_count += 1
                
                if "automatically" in result.notes.lower() or "research" in result.notes.lower():
                    intelligent_count += 1
                    print(f"    OK: Found via INTELLIGENT LOOKUP")
                else:
                    print(f"    OK: Found via existing database")
            else:
                # Check suggestions
                from core.supplement_lookup import get_supplement_suggestions
                suggestions = get_supplement_suggestions(supplement)
                if suggestions:
                    suggested_count += 1
                    print(f"    SUGGESTIONS: {len(suggestions)} found")
                else:
                    print(f"    NOT FOUND: No suggestions")
                    
        except Exception as e:
            print(f"    ERROR: {str(e)}")
        
        print()
    
    print("="*50)
    print("RESULTS:")
    print(f"Total tested: {len(new_supplements)}")
    print(f"Found: {found_count}")
    print(f"Via intelligent lookup: {intelligent_count}")
    print(f"With suggestions: {suggested_count}")
    print(f"No help at all: {len(new_supplements) - found_count - suggested_count}")
    
    if intelligent_count > 0:
        print("\nSTATUS: Intelligent lookup is WORKING!")
    elif suggested_count > len(new_supplements) * 0.5:
        print("\nSTATUS: Suggestions working, but intelligent lookup needs fix")
    else:
        print("\nSTATUS: New supplement discovery is BROKEN")


if __name__ == "__main__":
    test_new_supplements()