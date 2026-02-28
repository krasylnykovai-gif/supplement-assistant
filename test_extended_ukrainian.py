"""
Test extended Ukrainian/Russian support
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.supplement_lookup import lookup_supplement


def test_extended():
    print("EXTENDED UKRAINIAN/RUSSIAN TEST")
    print("==============================")
    
    # More comprehensive test
    extended_tests = [
        # Basic Ukrainian
        "магній", "вітамін д", "омега 3", "мелатонін", "кальцій",
        
        # Basic Russian
        "магний", "витамин д", "рыбий жир", "креатин", "цинк",
        
        # Alternative spellings
        "магнезій", "рыбьий жир", "витамин ц", "коензим ку10",
        
        # Additional names
        "залізо", "пробіотики", "ашваганда", "л-карнітин", "гліцин",
    ]
    
    found_count = 0
    total_count = len(extended_tests)
    
    print(f"Testing {total_count} Ukrainian/Russian names...")
    
    for i, query in enumerate(extended_tests, 1):
        try:
            result = lookup_supplement(query, use_intelligent_lookup=False, use_fuzzy_search=True)
            
            if result.found:
                found_count += 1
                status = "OK"
            else:
                status = "NOT FOUND"
                
            print(f"  {i:2d}. {status}")
                
        except Exception as e:
            print(f"  {i:2d}. ERROR")
    
    print()
    print(f"FINAL RESULTS:")
    print(f"Found: {found_count}/{total_count}")
    print(f"Success Rate: {(found_count/total_count)*100:.1f}%")
    
    if found_count >= total_count * 0.9:  # 90% success rate
        print("STATUS: EXCELLENT - Ukrainian/Russian support works great!")
    elif found_count >= total_count * 0.7:  # 70% success rate  
        print("STATUS: GOOD - Most Ukrainian/Russian names work")
    elif found_count >= total_count * 0.5:  # 50% success rate
        print("STATUS: PARTIAL - Some improvement needed")
    else:
        print("STATUS: POOR - Needs significant improvement")


if __name__ == "__main__":
    test_extended()