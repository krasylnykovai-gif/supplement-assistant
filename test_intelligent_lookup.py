"""
Test intelligent lookup system
Run this to see how automatic supplement research works
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from core.supplement_lookup import lookup_supplement
from core.intelligent_lookup import IntelligentLookup


async def test_intelligent_lookup():
    """Test the intelligent lookup system"""
    print("Testing Intelligent Supplement Lookup\n")
    
    # Check if we have API key
    brave_api_key = os.getenv("BRAVE_SEARCH_API_KEY")
    if not brave_api_key:
        print("WARNING: No BRAVE_SEARCH_API_KEY found in .env")
        print("To enable intelligent lookup:")
        print("   1. Get free API key: https://brave.com/search/api/")
        print("   2. Add to .env: BRAVE_SEARCH_API_KEY=your_key")
        print("   3. Run this test again\n")
        print("Testing with local database only...\n")
    else:
        print(f"OK Found Brave Search API key: {brave_api_key[:10]}...\n")
    
    # Test supplements
    test_supplements = [
        "Magnesium",  # Should find in local DB
        "Rhodiola Rosea",  # Should trigger intelligent lookup
        "Lion's Mane",  # Should research
        "NAD+",  # Complex supplement
        "Green Tea Extract"  # Green tea extract
    ]
    
    print("Testing supplement lookups:\n")
    
    for supplement in test_supplements:
        print(f"Researching: {supplement}")
        
        try:
            result = lookup_supplement(supplement, use_intelligent_lookup=True)
            
            print(f"   OK Found: {result.name}")
            print(f"   With food: {'Yes' if result.with_food else 'No'}")
            print(f"   Best time: {result.best_time}")
            print(f"   Notes: {result.notes}")
            print(f"   Source: {result.source[:50]}..." if len(result.source) > 50 else f"   Source: {result.source}")
            print(f"   Confidence: {'High' if 'впевненість: 0.' in result.notes and float(result.notes.split('впевненість: ')[1].split(')')[0]) > 0.7 else 'Medium' if 'впевненість:' in result.notes else 'Local DB'}")
            
        except Exception as e:
            print(f"   ERROR: {e}")
        
        print()
    
    # Show database stats if intelligent lookup was used
    if brave_api_key:
        try:
            data_dir = Path(__file__).parent / "data"
            lookup_engine = IntelligentLookup(data_dir, brave_api_key)
            stats = lookup_engine.get_research_stats()
            
            print("Research Database Stats:")
            print(f"   Total researched: {stats['total_researched']}")
            print(f"   High confidence: {stats['high_confidence']}")
            print(f"   Coverage: {stats['coverage_percent']:.1f}%")
            print(f"   Last updated: {stats['last_updated']}")
            
        except Exception as e:
            print(f"Stats error: {e}")


def test_sync():
    """Test synchronous lookup (what the bot actually uses)"""
    print("\n" + "="*50)
    print("Testing Bot Integration (Synchronous)")
    print("="*50 + "\n")
    
    # Test unknown supplement
    unknown_supplement = "Bacopa Monnieri"  # Should trigger research
    
    print(f"Bot testing: {unknown_supplement}")
    result = lookup_supplement(unknown_supplement)
    
    print(f"Result: {result.name}")
    print(f"With food: {'Yes' if result.with_food else 'No'}")
    print(f"Best time: {result.best_time}")
    print(f"Notes: {result.notes}")
    print(f"Found: {result.found}")


if __name__ == "__main__":
    # Run async test
    asyncio.run(test_intelligent_lookup())
    
    # Run sync test (what bot uses)
    test_sync()