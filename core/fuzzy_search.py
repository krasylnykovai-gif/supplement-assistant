"""
Fuzzy Search System for Supplements
Handles typos, alternative names, and suggests similar supplements
"""
import re
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher
import json
from pathlib import Path


class FuzzySupplementSearch:
    """Fuzzy search system for finding supplements with typos/alternative names"""
    
    def __init__(self, known_supplements: Dict, research_db_path: Optional[Path] = None):
        self.known_supplements = known_supplements
        self.research_db_path = research_db_path
        
        # Common alternative names and translations
        self.alternative_names = {
            # English <-> Ukrainian with common typos
            "vitamin d": ["vitamine d", "vitamin-d", "vit d", "cholecalciferol"],
            "vitamin c": ["vitamine c", "vitamin-c", "vit c", "ascorbic acid"],
            "vitamin b12": ["vitamine b12", "vitamin-b12", "vit b12", "cobalamin", "cyanocobalamin"],
            "magnesium": ["magnesium", "mag", "magnezium"],
            "calcium": ["calcium", "cal", "calci"],
            "zinc": ["zinc", "zn"],
            "iron": ["iron", "fe"],
            "omega 3": ["omega3", "omega-3", "omega 3", "fish oil", "fishoil"],
            "coenzyme q10": ["coenzyme q10", "coq10", "co-q10", "ubiquinone"],
            "melatonin": ["melatonin", "melotonin", "mellatonin", "melatonine"],
            "probiotics": ["probiotics", "probiotic", "pro-biotic"],
            "ashwagandha": ["ashwagandha", "ashwaganda", "ashwagandha", "withania"],
            "turmeric": ["turmeric", "tumeric", "curcumin", "curcomin"],
            "rhodiola": ["rhodiola", "rhodiola rosea", "golden root"],
            "ginkgo": ["ginkgo", "ginkgo biloba", "ginko", "gingko"],
            "bacopa": ["bacopa", "bacopa monnieri", "brahmi"],
            "lion's mane": ["lions mane", "lion mane", "lions-mane", "hericium"],
            "green tea": ["green tea", "greentea", "green-tea", "egcg"],
            "creatine": ["creatine", "creatine monohydrate", "creatin"],
            "whey protein": ["whey protein", "whey", "protein"],
            "collagen": ["collagen", "collegen", "collagen peptides"],
            "hyaluronic acid": ["hyaluronic acid", "ha", "hyaluronic"],
            "glucosamine": ["glucosamine", "glucosomine", "glucoseamine"],
            "chondroitin": ["chondroitin", "chondrotin", "chondroitin sulfate"],
        }
        
        # Common typos and misspellings
        self.typo_corrections = {
            "магний": ["магний", "магнезий", "магнезиум", "magnesium"],
            "омега": ["omega", "омега-3", "omega-3", "омега 3"],
            "витамин": ["вітамін", "vitamin"],
            "кальций": ["кальцій", "calcium"],
            "мелатонин": ["мелатонін", "melatonin"],
            "креатин": ["creatine"],
            "коллаген": ["колаген", "collagen"],
        }
        
        # Build searchable database after alternatives are defined
        self.search_db = self._build_search_database()
    
    def _build_search_database(self) -> List[Dict]:
        """Build searchable database with all names and alternatives"""
        search_entries = []
        
        # Add known supplements
        for supp_id, supp_data in self.known_supplements.items():
            # Handle both dict and SupplementInfo objects
            if hasattr(supp_data, 'name'):
                # SupplementInfo object
                main_name = supp_data.name
                aliases = getattr(supp_data, 'aliases', [])
            else:
                # Dictionary
                main_name = supp_data.get('name', supp_id)
                aliases = supp_data.get('aliases', [])
            
            # Add main entry
            search_entries.append({
                'id': supp_id,
                'name': main_name,
                'search_name': self._normalize_for_search(main_name),
                'source': 'known',
                'data': supp_data
            })
            
            # Add aliases
            for alias in aliases:
                search_entries.append({
                    'id': supp_id,
                    'name': main_name,
                    'search_name': self._normalize_for_search(alias),
                    'source': 'alias',
                    'data': supp_data
                })
        
        # Add research database if available
        if self.research_db_path and self.research_db_path.exists():
            try:
                with open(self.research_db_path, 'r', encoding='utf-8') as f:
                    research_data = json.load(f)
                    
                for supp_id, supp_data in research_data.get('supplements', {}).items():
                    search_entries.append({
                        'id': supp_id,
                        'name': supp_data.get('name', supp_id),
                        'search_name': self._normalize_for_search(supp_data.get('name', supp_id)),
                        'source': 'research',
                        'data': supp_data
                    })
            except Exception as e:
                print(f"Error loading research DB for search: {e}")
        
        # Add alternative names
        for main_name, alternatives in self.alternative_names.items():
            for alt_name in alternatives:
                search_entries.append({
                    'id': f"alt_{main_name.replace(' ', '_')}",
                    'name': main_name.title(),
                    'search_name': self._normalize_for_search(alt_name),
                    'source': 'alternative',
                    'data': {'name': main_name.title()}
                })
        
        return search_entries
    
    def _normalize_for_search(self, text: str) -> str:
        """Normalize text for fuzzy search"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep letters, numbers, spaces
        text = re.sub(r'[^\w\s-]', '', text)
        
        # Common substitutions for better matching
        substitutions = {
            'vitamin': 'vitamin',
            'вітамін': 'vitamin',
            'витамин': 'vitamin',
            'омега': 'omega',
            'коензим': 'coenzyme',
            'q10': 'q10',
            'coq10': 'coq10',
        }
        
        for old, new in substitutions.items():
            text = text.replace(old, new)
        
        return text
    
    def calculate_similarity(self, a: str, b: str) -> float:
        """Calculate similarity between two strings"""
        if not a or not b:
            return 0.0
        
        # Normalize both strings
        a_norm = self._normalize_for_search(a)
        b_norm = self._normalize_for_search(b)
        
        if a_norm == b_norm:
            return 1.0
        
        # Check if one contains the other
        if a_norm in b_norm or b_norm in a_norm:
            return 0.9
        
        # Use sequence matcher for fuzzy matching
        similarity = SequenceMatcher(None, a_norm, b_norm).ratio()
        
        # Bonus for word matches
        a_words = set(a_norm.split())
        b_words = set(b_norm.split())
        
        if a_words and b_words:
            word_overlap = len(a_words & b_words) / len(a_words | b_words)
            similarity = max(similarity, word_overlap * 0.8)
        
        return similarity
    
    def search(self, query: str, min_similarity: float = 0.6, max_results: int = 5) -> List[Tuple[str, str, float]]:
        """
        Search for supplements with fuzzy matching
        Returns list of (supplement_id, name, similarity_score)
        """
        if not query or len(query.strip()) < 2:
            return []
        
        results = []
        query_norm = self._normalize_for_search(query)
        
        # Search through all entries
        for entry in self.search_db:
            similarity = self.calculate_similarity(query, entry['search_name'])
            
            if similarity >= min_similarity:
                results.append((
                    entry['id'],
                    entry['name'],
                    similarity,
                    entry['source']
                ))
        
        # Sort by similarity (descending) and remove duplicates
        results.sort(key=lambda x: x[2], reverse=True)
        
        # Remove duplicate IDs, keeping highest scoring
        seen_ids = set()
        unique_results = []
        
        for result in results:
            supp_id = result[0]
            if supp_id not in seen_ids:
                seen_ids.add(supp_id)
                unique_results.append(result)
        
        return unique_results[:max_results]
    
    def suggest_corrections(self, query: str) -> List[str]:
        """Suggest possible corrections for typos"""
        suggestions = []
        
        # Check common typos
        query_lower = query.lower()
        for correct, typos in self.typo_corrections.items():
            for typo in typos:
                if self.calculate_similarity(query_lower, typo) > 0.7:
                    suggestions.append(correct.title())
        
        # Get fuzzy search results
        search_results = self.search(query, min_similarity=0.5, max_results=3)
        for _, name, score, _ in search_results:
            if name not in suggestions:
                suggestions.append(name)
        
        return suggestions[:5]
    
    def find_best_match(self, query: str) -> Optional[Tuple[str, str, float]]:
        """Find single best match for query"""
        results = self.search(query, min_similarity=0.7, max_results=1)
        
        if results:
            return results[0][:3]  # id, name, score
        
        return None


def test_fuzzy_search():
    """Test the fuzzy search system"""
    from supplement_lookup import KNOWN_SUPPLEMENTS
    
    fuzzy = FuzzySupplementSearch(KNOWN_SUPPLEMENTS)
    
    # Test queries with typos and alternatives
    test_queries = [
        "магний",  # Should find magnesium
        "vitamine d",  # Should find vitamin d
        "омга 3",  # Typo for omega 3
        "мелотанин",  # Typo for melatonin
        "коензим ку10",  # Alternative for coq10
        "lion maine",  # Typo for lion's mane
        "гинко",  # Short for ginkgo
        "витмин c",  # Typo for vitamin c
    ]
    
    print("🔍 Testing Fuzzy Search System\n")
    
    for query in test_queries:
        print(f"Query: '{query}'")
        
        results = fuzzy.search(query, min_similarity=0.5)
        if results:
            print("   Results:")
            for supp_id, name, score, source in results:
                print(f"   - {name} (score: {score:.2f}, source: {source})")
        else:
            print("   No matches found")
            
        # Test suggestions
        suggestions = fuzzy.suggest_corrections(query)
        if suggestions:
            print(f"   Suggestions: {', '.join(suggestions)}")
        
        print()


if __name__ == "__main__":
    test_fuzzy_search()