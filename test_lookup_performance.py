#!/usr/bin/env python3
"""
Test lookup performance and debugging
"""
import time
import os
from pathlib import Path
from core.supplement_lookup import lookup_supplement

def test_supplement_lookup():
    """Test different supplement lookups to identify performance issues"""
    
    test_cases = [
        # Known supplements (should be fast)
        "magnesium",
        "vitamin d", 
        "omega 3",
        
        # Ukrainian/Russian (should be corrected)
        "магній",
        "вітамін д",
        "омега 3",
        
        # Typos (should be corrected)  
        "vitamine d",
        "omega3",
        "melotonin",
        
        # Unknown supplements (will trigger intelligent lookup)
        "rhodiola rosea",
        "ashwagandha", 
        "completely_unknown_supplement_xyz123"
    ]
    
    print("Testing Supplement Lookup Performance")
    print("=" * 50)
    
    for name in test_cases:
        print(f"\nTesting: '{name}'")
        start_time = time.time()
        
        try:
            result = lookup_supplement(name)
            end_time = time.time()
            duration = end_time - start_time
            
            status = "[FOUND]" if result.found else "[NOT FOUND]"
            print(f"   {status} in {duration:.2f}s")
            print(f"   Name: {result.name}")
            print(f"   Notes: {result.notes[:80]}...")
            
            if duration > 10:
                print(f"   [WARNING] SLOW LOOKUP (>{duration:.1f}s)")
                
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            print(f"   [ERROR] in {duration:.2f}s: {str(e)[:100]}...")
            
    print("\n" + "=" * 50)
    print("Test completed!")

def test_with_api():
    """Test with Brave API if available"""
    api_key = os.getenv("BRAVE_SEARCH_API_KEY")
    if api_key:
        print(f"Brave API: Available ({api_key[:10]}...)")
    else:
        print("Brave API: Not configured")
        
def main():
    test_with_api()
    test_supplement_lookup()

if __name__ == "__main__":
    main()