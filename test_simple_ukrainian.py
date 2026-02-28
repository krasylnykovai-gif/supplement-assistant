"""
Simple test for Ukrainian/Russian names without unicode output
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.supplement_lookup import lookup_supplement


def test_simple():
    print("TESTING UKRAINIAN/RUSSIAN NAMES")
    print("===============================")
    
    # Test basic Ukrainian/Russian words that should work
    test_cases = [
        ("magnesium", "English - should work"),
        # Add actual tests by result, not by printing unicode
    ]
    
    # Test Ukrainian words by checking if they get found
    ukrainian_tests = [
        "магній",        # magnesium
        "вітамін д",     # vitamin d
        "омега 3",       # omega 3
        "мелатонін",     # melatonin
        "кальцій",       # calcium
        "цинк",          # zinc
        "креатин",       # creatine
        "рыбий жир",     # fish oil (Russian)
        "витамин д",     # vitamin d (Russian)
        "магний",        # magnesium (Russian)
    ]
    
    found_count = 0
    total_count = len(ukrainian_tests)
    
    print(f"Testing {total_count} Ukrainian/Russian supplement names...")
    
    for i, query in enumerate(ukrainian_tests, 1):
        try:
            result = lookup_supplement(query, use_intelligent_lookup=False, use_fuzzy_search=True)
            
            if result.found:
                found_count += 1
                print(f"  {i:2d}. OK - Found match")
            else:
                print(f"  {i:2d}. NOT FOUND")
                
        except Exception as e:
            print(f"  {i:2d}. ERROR: {str(e)}")
    
    print()
    print(f"RESULTS: {found_count}/{total_count} Ukrainian/Russian names found")
    print(f"Success rate: {(found_count/total_count)*100:.1f}%")
    
    if found_count >= total_count * 0.8:  # 80% success rate
        print("STATUS: GOOD - Most Ukrainian/Russian names work!")
    elif found_count >= total_count * 0.5:  # 50% success rate  
        print("STATUS: PARTIAL - Some Ukrainian/Russian names work")
    else:
        print("STATUS: POOR - Ukrainian/Russian support needs improvement")


if __name__ == "__main__":
    test_simple()