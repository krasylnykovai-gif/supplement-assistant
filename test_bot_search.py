"""
Test bot search without unicode output issues
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.supplement_lookup import lookup_supplement, KNOWN_SUPPLEMENTS


def test_bot_search():
    print("TESTING BOT SEARCH FUNCTIONALITY")
    print("=================================")
    
    test_queries = [
        # Exact matches
        "magnesium", "vitamin d", "coq10", "melatonin", "omega 3",
        
        # Typos that should be corrected by fuzzy search
        "magnesium", "vitamine d", "omega3", "melotonin", "ashwaganda",
        
        # Alternative names
        "fish oil", "vitamin c", "calcium",
        
        # Unknown
        "unknown supplement"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        
        try:
            result = lookup_supplement(query, use_intelligent_lookup=False, use_fuzzy_search=True)
            
            if result.found:
                print(f"  Status: FOUND")
                print(f"  With food: {result.with_food}")
                print(f"  Best time: {result.best_time}")
                
                # Check if fuzzy search was used
                if "схожістю" in result.notes:
                    print(f"  Used: FUZZY SEARCH")
                else:
                    print(f"  Used: EXACT/PARTIAL MATCH")
            else:
                print(f"  Status: NOT FOUND")
                
                # Test suggestions
                from core.supplement_lookup import get_supplement_suggestions
                suggestions = get_supplement_suggestions(query)
                if suggestions:
                    print(f"  Suggestions: {', '.join(suggestions[:3])}")
                else:
                    print(f"  Suggestions: None")
                    
        except Exception as e:
            print(f"  ERROR: {e}")


if __name__ == "__main__":
    test_bot_search()