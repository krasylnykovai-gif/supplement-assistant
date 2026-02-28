"""
Check what keys are in KNOWN_SUPPLEMENTS
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.supplement_lookup import KNOWN_SUPPLEMENTS


def check_keys():
    print("=== KNOWN_SUPPLEMENTS KEYS ===")
    print(f"Total: {len(KNOWN_SUPPLEMENTS)}")
    print()
    
    # Try to print keys safely
    for i, key in enumerate(KNOWN_SUPPLEMENTS.keys(), 1):
        try:
            print(f"{i:2d}. '{key}'")
        except UnicodeEncodeError:
            print(f"{i:2d}. [unicode key]")
    
    print()
    
    # Test some specific keys
    test_keys = ["magnesium", "vitamin d", "coq10", "melatonin"]
    print("Testing specific keys:")
    for key in test_keys:
        exists = key in KNOWN_SUPPLEMENTS
        print(f"  '{key}': {'EXISTS' if exists else 'NOT FOUND'}")


if __name__ == "__main__":
    check_keys()