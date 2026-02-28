"""
Debug supplement search system
Find out why fuzzy search doesn't work
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.supplement_lookup import lookup_supplement, KNOWN_SUPPLEMENTS
from core.fuzzy_search import FuzzySupplementSearch


def debug_search_step_by_step(query):
    """Debug search process step by step"""
    print(f"=== DEBUGGING SEARCH FOR: '{query}' ===")
    
    # Step 1: Check exact match
    normalized = query.lower().strip()
    print(f"1. Normalized query: '{normalized}'")
    
    if normalized in KNOWN_SUPPLEMENTS:
        print(f"   OK FOUND exact match in KNOWN_SUPPLEMENTS")
        return
    else:
        print(f"   NO exact match in KNOWN_SUPPLEMENTS")
    
    # Step 2: Check partial matches
    partial_matches = []
    for key, info in KNOWN_SUPPLEMENTS.items():
        if normalized in key or key in normalized:
            partial_matches.append((key, info.name))
    
    if partial_matches:
        print(f"   OK Found {len(partial_matches)} partial matches:")
        for key, name in partial_matches:
            print(f"      - '{key}' -> {name}")
        return
    else:
        print(f"   NO partial matches found")
    
    # Step 3: Test fuzzy search
    print(f"3. Testing fuzzy search...")
    try:
        data_dir = Path(__file__).parent / "data"
        research_db_path = data_dir / "research_database.json"
        
        fuzzy = FuzzySupplementSearch(KNOWN_SUPPLEMENTS, research_db_path)
        print(f"   OK Fuzzy search initialized")
        print(f"   Search database size: {len(fuzzy.search_db)}")
        
        # Test similarity with some known supplements
        test_against = ["magnesium", "vitamin d", "omega 3", "melatonin"]
        print(f"   Testing similarity against known supplements:")
        
        for test_supp in test_against:
            similarity = fuzzy.calculate_similarity(query, test_supp)
            print(f"      '{query}' vs '{test_supp}': {similarity:.2f}")
        
        # Get fuzzy search results
        results = fuzzy.search(query, min_similarity=0.3)  # Lower threshold for debug
        print(f"   Fuzzy search results (min_similarity=0.3):")
        
        if results:
            for supp_id, name, score, source in results:
                print(f"      - {name} (score: {score:.2f}, source: {source}, id: {supp_id})")
        else:
            print(f"      NO fuzzy search results")
        
        # Test best match
        best_match = fuzzy.find_best_match(query)
        if best_match:
            supp_id, matched_name, score = best_match
            print(f"   Best match: '{matched_name}' (score: {score:.2f}, id: {supp_id})")
        else:
            print(f"   NO best match found")
            
    except Exception as e:
        print(f"   Fuzzy search error: {e}")
    
    # Step 4: Test full lookup
    print(f"4. Testing full lookup...")
    try:
        result = lookup_supplement(query, use_intelligent_lookup=False, use_fuzzy_search=True)
        print(f"   Result found: {result.found}")
        print(f"   Name: {result.name}")
        print(f"   Notes: {result.notes}")
    except Exception as e:
        print(f"   Lookup error: {e}")
    
    print()


def main():
    print("DEBUGGING SUPPLEMENT SEARCH SYSTEM")
    print("=====================================")
    print()
    
    print(f"Known supplements database: {len(KNOWN_SUPPLEMENTS)} entries")
    print("First 10 keys:")
    for i, key in enumerate(list(KNOWN_SUPPLEMENTS.keys())[:10]):
        try:
            supp = KNOWN_SUPPLEMENTS[key]
            print(f"  {i+1}. '{key}' -> {supp.name}")
        except UnicodeEncodeError:
            print(f"  {i+1}. '{key}' -> [unicode name]")
    print()
    
    # Test queries that should work
    test_queries = [
        "magnesium",     # Should be exact match 
        "vitamin d",     # Should be partial match
        "coq10",        # Should be exact match
        "melatonin",    # Should be exact match
        "omega 3",      # Should be fuzzy match
        "unknown",      # Should not match
    ]
    
    for query in test_queries:
        debug_search_step_by_step(query)


if __name__ == "__main__":
    main()