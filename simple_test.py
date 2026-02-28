#!/usr/bin/env python3
import time
import os
from core.supplement_lookup import lookup_supplement

def test():
    test_cases = [
        "magnesium",
        "vitamin d", 
        "unknown_supplement_test"
    ]
    
    print("Testing lookup performance...")
    
    for name in test_cases:
        print(f"Testing: {name}")
        start = time.time()
        try:
            result = lookup_supplement(name)
            duration = time.time() - start
            status = "FOUND" if result.found else "NOT FOUND"
            print(f"  Result: {status} in {duration:.2f}s")
        except Exception as e:
            duration = time.time() - start
            print(f"  ERROR in {duration:.2f}s: {str(e)[:50]}...")
            
    # Test API status
    api_key = os.getenv("BRAVE_SEARCH_API_KEY")
    print(f"API configured: {'Yes' if api_key else 'No'}")

if __name__ == "__main__":
    test()