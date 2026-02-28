"""
Quick test for common typo corrections
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.supplement_lookup import lookup_supplement


def quick_test():
    print("QUICK TYPO CORRECTION TEST")
    print("==========================")
    
    typos_to_test = [
        "vitamine d",
        "omega3", 
        "melotonin",
        "ashwaganda",
        "magnesium"  # This should work
    ]
    
    for typo in typos_to_test:
        print(f"\nTesting: '{typo}'")
        
        try:
            result = lookup_supplement(typo, use_intelligent_lookup=False, use_fuzzy_search=True)
            
            if result.found:
                print(f"  OK: Found as '{result.name.encode('ascii', 'ignore').decode()}'")
                print(f"  Time: {result.best_time}")
                print(f"  Food: {result.with_food}")
                
                if "Corrected from" in result.notes:
                    print(f"  Method: Simple correction")
                elif "similarity" in result.notes:
                    print(f"  Method: Fuzzy search")
                else:
                    print(f"  Method: Direct match")
            else:
                print(f"  NOT FOUND")
                
        except Exception as e:
            print(f"  ERROR: {str(e)}")


if __name__ == "__main__":
    quick_test()