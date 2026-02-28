"""
Test truly unknown supplements that should trigger basic research
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.supplement_lookup import lookup_supplement


def test_unknown():
    print("TESTING TRULY UNKNOWN SUPPLEMENTS")
    print("=================================")
    
    # Test supplements that definitely should NOT be in database
    # but should be categorized by basic research
    unknown_supplements = [
        # Should be recognized as herbs
        "echinacea extract",
        "gotu kola", 
        "he shou wu",
        "schisandra berry",
        "astragalus root",
        
        # Should be recognized as vitamins
        "vitamin k2 mk-7",
        "methylfolate",
        "pyridoxal 5 phosphate",
        
        # Should be recognized as minerals  
        "magnesium bisglycinate",
        "zinc picolinate",
        "chromium picolinate",
        
        # Should be recognized as amino acids
        "l-ornithine",
        "l-lysine", 
        "taurine",
        
        # Should be recognized as mushrooms
        "chaga mushroom extract",
        "turkey tail mushroom",
        
        # Should be recognized as oils
        "evening primrose oil",
        "borage oil",
        
        # Should get basic defaults
        "completely unknown supplement 12345",
        "fake supplement name xyz",
    ]
    
    found_count = 0
    pattern_recognition_count = 0
    
    print(f"Testing {len(unknown_supplements)} truly unknown supplements...")
    print()
    
    for i, supplement in enumerate(unknown_supplements, 1):
        print(f"{i:2d}. Testing: '{supplement}'")
        
        try:
            result = lookup_supplement(supplement, use_intelligent_lookup=False, use_fuzzy_search=True)
            
            if result.found:
                found_count += 1
                
                if "pattern" in result.notes.lower() or "category" in result.notes.lower():
                    pattern_recognition_count += 1
                    print(f"    OK: Found via PATTERN RECOGNITION")
                    print(f"        Time: {result.best_time}, Food: {result.with_food}")
                else:
                    print(f"    OK: Found via database (unexpected)")
            else:
                print(f"    NOT FOUND")
                
        except Exception as e:
            print(f"    ERROR: {str(e)}")
        
        print()
    
    print("="*50)
    print("RESULTS:")
    print(f"Total tested: {len(unknown_supplements)}")
    print(f"Found: {found_count}")
    print(f"Via pattern recognition: {pattern_recognition_count}")
    print(f"Not found at all: {len(unknown_supplements) - found_count}")
    
    success_rate = (found_count / len(unknown_supplements)) * 100
    pattern_rate = (pattern_recognition_count / len(unknown_supplements)) * 100
    
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Pattern recognition rate: {pattern_rate:.1f}%")
    
    if pattern_rate > 70:
        print("\nSTATUS: EXCELLENT - Pattern recognition working well!")
    elif pattern_rate > 50:
        print("\nSTATUS: GOOD - Most unknown supplements handled")
    elif pattern_rate > 30:
        print("\nSTATUS: PARTIAL - Some pattern recognition working")
    else:
        print("\nSTATUS: POOR - Pattern recognition needs improvement")


if __name__ == "__main__":
    test_unknown()