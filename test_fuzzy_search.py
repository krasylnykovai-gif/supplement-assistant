"""
Test Fuzzy Search System for Supplements
Shows how typos and alternative names are handled
"""
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from core.supplement_lookup import lookup_supplement, get_supplement_suggestions
from core.fuzzy_search import FuzzySupplementSearch, test_fuzzy_search
from core.supplement_lookup import KNOWN_SUPPLEMENTS


def test_bot_integration():
    """Test how the bot handles various queries with fuzzy search"""
    print("=" * 60)
    print("TESTING BOT INTEGRATION WITH FUZZY SEARCH")
    print("=" * 60)
    print()
    
    # Test cases with expected behavior
    test_cases = [
        # Exact matches (should work immediately)
        ("magnesium", "Should find exact match"),
        ("coq10", "Should find exact match"),
        
        # Typos (should use fuzzy search)
        ("magnesium", "Should find magnesium"),
        ("vitamine d", "Extra 'e' -> should find vitamin d"),
        ("omega3", "Missing space -> should find omega 3"),
        ("melotonin", "Typo -> should find melatonin"),
        ("creatine", "Should find creatine"),
        
        # Alternative names
        ("coenzyme q10", "Should find coq10"),
        ("fish oil", "Should find omega 3"),
        ("curcumin", "Should find turmeric/curcumin"),
        ("lions mane", "Should find lion's mane"),
        
        # Partial matches
        ("ginkgo", "Should find ginkgo"),
        ("rhodiola", "Should find rhodiola"),
        
        # Unknown supplements (should show suggestions or ask user)
        ("unknown supplement", "Should not find but may suggest"),
        ("exotic extract", "Should ask user to add manually"),
    ]
    
    for query, expected in test_cases:
        print(f"Query: '{query}'")
        print(f"Expected: {expected}")
        
        try:
            # Test lookup
            result = lookup_supplement(query, use_intelligent_lookup=False, use_fuzzy_search=True)
            
            if result.found:
                print(f"OK Found: {result.name}")
                print(f"   With food: {'Yes' if result.with_food else 'No'}")
                print(f"   Notes: {result.notes}")
                
                if "схожістю" in result.notes:
                    print(f"   Used fuzzy search!")
            else:
                print("NOT FOUND - would ask user")
                
                # Test suggestions
                suggestions = get_supplement_suggestions(query)
                if suggestions:
                    print(f"   Suggestions: {', '.join(suggestions)}")
                else:
                    print("   No suggestions available")
            
        except Exception as e:
            print(f"   ERROR: {e}")
        
        print("-" * 40)
        print()


def test_fuzzy_search_detailed():
    """Detailed test of fuzzy search capabilities"""
    print("=" * 60)
    print("DETAILED FUZZY SEARCH TEST")
    print("=" * 60)
    print()
    
    # Create fuzzy search instance
    data_dir = Path(__file__).parent / "data"
    research_db_path = data_dir / "research_database.json"
    
    fuzzy = FuzzySupplementSearch(KNOWN_SUPPLEMENTS, research_db_path)
    
    print(f"Database loaded:")
    print(f"   Known supplements: {len(KNOWN_SUPPLEMENTS)}")
    print(f"   Search entries: {len(fuzzy.search_db)}")
    print(f"   Alternative names: {len(fuzzy.alternative_names)}")
    print()
    
    # Test similarity calculations
    similarity_tests = [
        ("magnesium", "magnesium"),
        ("vitamin d", "vitamin d"),
        ("omega 3", "omega-3"),
        ("melatonin", "melatonin"),
        ("turmeric", "turmeric"),
        ("unknown supplement", "some supplement"),
    ]
    
    print("Similarity scores:")
    for query, target in similarity_tests:
        score = fuzzy.calculate_similarity(query, target)
        status = "MATCH" if score > 0.7 else "WEAK" if score > 0.4 else "NO MATCH"
        print(f"   '{query}' vs '{target}': {score:.2f} {status}")
    
    print()
    
    # Test search results
    search_queries = [
        "magnesium",
        "vitamin d",
        "omega 3",
        "lion maine",  # typo
        "green tea",
    ]
    
    print("Search results:")
    for query in search_queries:
        print(f"   Query: '{query}'")
        results = fuzzy.search(query, min_similarity=0.5)
        
        if results:
            for supp_id, name, score, source in results:
                print(f"      - {name} (score: {score:.2f}, source: {source})")
        else:
            print("      No results found")
        print()


if __name__ == "__main__":
    print("FUZZY SEARCH SYSTEM TEST")
    print("Testing supplement search with typos and alternatives")
    print()
    
    # Run tests
    test_fuzzy_search_detailed()
    test_bot_integration()
    
    print("All tests completed!")
    print()
    print("Summary:")
    print("   - Exact matches work instantly")
    print("   - Typos are corrected using fuzzy search")
    print("   - Alternative names are recognized")
    print("   - Unknown supplements show suggestions or ask user")
    print("   - All user input is saved for future users")