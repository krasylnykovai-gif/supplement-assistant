"""
Normalizer: converts user input (synonyms) to canonical supplement IDs
"""
import json
from pathlib import Path
from typing import Optional, List, Dict

class SupplementNormalizer:
    def __init__(self, catalog_path: str = None):
        if catalog_path is None:
            catalog_path = Path(__file__).parent.parent / "data" / "supplement_catalog.json"
        
        with open(catalog_path, 'r', encoding='utf-8') as f:
            self.catalog = json.load(f)
        
        # Build reverse lookup: alias -> canonical_id
        self.alias_map = {}
        for supp_id, supp_data in self.catalog['supplements'].items():
            # Map the canonical name
            self.alias_map[supp_data['name'].lower()] = supp_id
            self.alias_map[supp_id.lower()] = supp_id
            # Map all aliases
            for alias in supp_data.get('aliases', []):
                self.alias_map[alias.lower()] = supp_id
    
    def normalize(self, user_input: str) -> Optional[str]:
        """Convert user input to canonical supplement ID"""
        normalized = user_input.lower().strip()
        return self.alias_map.get(normalized)
    
    def normalize_many(self, inputs: List[str]) -> Dict[str, Optional[str]]:
        """Normalize multiple inputs, return dict of input -> canonical_id"""
        return {inp: self.normalize(inp) for inp in inputs}
    
    def get_supplement_info(self, supp_id: str) -> Optional[dict]:
        """Get full supplement info by canonical ID"""
        return self.catalog['supplements'].get(supp_id)
    
    def get_all_supplements(self) -> Dict[str, dict]:
        """Get all supplements from catalog"""
        return self.catalog['supplements']
    
    def search(self, query: str) -> List[str]:
        """Search for supplements matching query"""
        query = query.lower().strip()
        results = []
        for alias, supp_id in self.alias_map.items():
            if query in alias and supp_id not in results:
                results.append(supp_id)
        return results


if __name__ == "__main__":
    # Test
    normalizer = SupplementNormalizer()
    print(normalizer.normalize("вітамін д"))  # -> vitamin_d
    print(normalizer.normalize("fish oil"))   # -> omega_3
    print(normalizer.normalize("барберін"))   # -> berberine
