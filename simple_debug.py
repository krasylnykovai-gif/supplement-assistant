"""
Simple debug to find search issues
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.supplement_lookup import lookup_supplement, KNOWN_SUPPLEMENTS


def simple_test():
    print("=== SIMPLE SEARCH DEBUG ===")
    print(f"Known supplements: {len(KNOWN_SUPPLEMENTS)}")
    
    # Test simple English queries
    test_queries = ["magnesium", "vitamin d", "coq10", "melatonin", "omega 3"]
    
    for query in test_queries:
        print(f"\nTesting: '{query}'")
        
        # Check if in KNOWN_SUPPLEMENTS
        normalized = query.lower().strip()
        if normalized in KNOWN_SUPPLEMENTS:
            print(f"  FOUND in database: {KNOWN_SUPPLEMENTS[normalized].name}")
            continue
        
        # Check partial matches
        partial_found = False
        for key in KNOWN_SUPPLEMENTS.keys():
            if normalized in key or key in normalized:
                print(f"  PARTIAL match: '{key}' -> {KNOWN_SUPPLEMENTS[key].name}")
                partial_found = True
                break
        
        if partial_found:
            continue
            
        # Test full lookup
        try:
            result = lookup_supplement(query, use_intelligent_lookup=False, use_fuzzy_search=True)
            if result.found:
                print(f"  LOOKUP FOUND: {result.name}")
            else:
                print(f"  LOOKUP NOT FOUND")
        except Exception as e:
            print(f"  LOOKUP ERROR: {e}")


if __name__ == "__main__":
    simple_test()