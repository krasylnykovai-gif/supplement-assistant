"""
Intelligent Supplement Lookup - automatic research and database building
Uses web search + AI analysis to find reliable supplement information
"""
import json
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
import requests
import time

# For AI analysis (you can replace with any AI API)
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class ResearchResult:
    """Result of automated supplement research"""
    name: str
    with_food: bool
    fat_required: bool
    best_time: str  # morning, evening, any
    notes: str
    confidence: float  # 0-1, how confident we are in the result
    sources: List[str]  # URLs where info was found
    research_date: str
    found: bool = True


class IntelligentLookup:
    """Intelligent supplement lookup with automatic research"""
    
    def __init__(self, data_dir: Path, brave_api_key: str = None, openai_api_key: str = None):
        self.data_dir = data_dir
        self.research_db_path = data_dir / "research_database.json"
        self.brave_api_key = brave_api_key
        self.openai_api_key = openai_api_key
        
        # Load existing research database
        self.research_db = self.load_research_db()
        
        # Reliable sources for supplement info (in order of preference)
        self.trusted_sources = [
            "examine.com",
            "ods.od.nih.gov",  # NIH Office of Dietary Supplements
            "pubmed.ncbi.nlm.nih.gov",
            "mayoclinic.org",
            "webmd.com",
            "healthline.com"
        ]
    
    def load_research_db(self) -> Dict:
        """Load research database from file"""
        if self.research_db_path.exists():
            try:
                with open(self.research_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading research DB: {e}")
        
        return {"supplements": {}, "last_updated": None}
    
    def save_research_db(self):
        """Save research database to file"""
        self.research_db["last_updated"] = datetime.now().isoformat()
        with open(self.research_db_path, 'w', encoding='utf-8') as f:
            json.dump(self.research_db, f, ensure_ascii=False, indent=2)
    
    def normalize_supplement_name(self, name: str) -> str:
        """Normalize supplement name for consistent lookup"""
        # Remove common variations
        normalized = name.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)  # Multiple spaces -> single
        normalized = re.sub(r'[^\w\s-]', '', normalized)  # Remove special chars except -
        
        # Common translations and aliases
        translations = {
            'вітамін': 'vitamin',
            'коензим': 'coenzyme',
            'омега': 'omega',
            'кальцій': 'calcium',
            'магній': 'magnesium',
            'цинк': 'zinc',
            'залізо': 'iron',
            'йод': 'iodine'
        }
        
        for uk, en in translations.items():
            normalized = normalized.replace(uk, en)
        
        return normalized
    
    def search_web_for_supplement(self, name: str) -> List[Dict]:
        """Search web for supplement information"""
        if not self.brave_api_key:
            return []
        
        query = f"{name} supplement dosage timing food interactions"
        search_url = "https://api.search.brave.com/res/v1/web/search"
        
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.brave_api_key
        }
        
        params = {
            "q": query,
            "count": 10,
            "search_lang": "en",
            "country": "US",
            "safesearch": "moderate"
        }
        
        try:
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for result in data.get("web", {}).get("results", []):
                # Prioritize trusted sources
                url = result.get("url", "")
                title = result.get("title", "")
                snippet = result.get("description", "")
                
                # Calculate trust score based on domain
                trust_score = 0
                for i, trusted_domain in enumerate(self.trusted_sources):
                    if trusted_domain in url:
                        trust_score = len(self.trusted_sources) - i
                        break
                
                if trust_score > 0 or any(domain in url for domain in ["wikipedia.org", "drugs.com"]):
                    results.append({
                        "url": url,
                        "title": title,
                        "snippet": snippet,
                        "trust_score": trust_score,
                        "content": f"{title} {snippet}"
                    })
            
            # Sort by trust score
            results.sort(key=lambda x: x["trust_score"], reverse=True)
            return results[:5]  # Top 5 most trusted results
            
        except Exception as e:
            print(f"Web search error: {e}")
            return []
    
    def extract_supplement_info_from_text(self, name: str, search_results: List[Dict]) -> Optional[ResearchResult]:
        """Extract supplement information from search results using pattern matching"""
        if not search_results:
            return None
        
        # Combine all text content
        combined_text = ""
        sources = []
        
        for result in search_results:
            combined_text += f"\n{result['content']}"
            sources.append(result['url'])
        
        # Pattern-based extraction (rules-based approach)
        info = {
            "with_food": None,
            "fat_required": None,
            "best_time": None,
            "notes": []
        }
        
        text_lower = combined_text.lower()
        
        # Food timing patterns
        if any(phrase in text_lower for phrase in ["take with food", "with meals", "after eating"]):
            info["with_food"] = True
        elif any(phrase in text_lower for phrase in ["empty stomach", "without food", "before eating"]):
            info["with_food"] = False
        
        # Fat requirement patterns
        if any(phrase in text_lower for phrase in ["fat soluble", "with fats", "fatty meal", "absorption fat"]):
            info["fat_required"] = True
            info["with_food"] = True  # Fat-soluble = with food
        
        # Time patterns
        if any(phrase in text_lower for phrase in ["morning", "breakfast", "early"]):
            info["best_time"] = "morning"
        elif any(phrase in text_lower for phrase in ["evening", "bedtime", "sleep", "night"]):
            info["best_time"] = "evening"
        else:
            info["best_time"] = "any"
        
        # Special cases and notes
        notes = []
        
        if "melatonin" in name.lower():
            info["with_food"] = False
            info["best_time"] = "evening"
            notes.append("За 30-60 хв до сну")
        
        if any(word in name.lower() for word in ["vitamin d", "вітамін d"]):
            info["with_food"] = True
            info["fat_required"] = True
            notes.append("Жиророзчинний, краще з жирною їжею")
        
        if any(word in name.lower() for word in ["probiotic", "пробіотик"]):
            info["with_food"] = False
            info["best_time"] = "morning"
            notes.append("Краще натщесерце за 30 хв до їжі")
        
        # Calculate confidence based on how much info we found
        confidence = 0.0
        if info["with_food"] is not None:
            confidence += 0.3
        if info["best_time"] != "any":
            confidence += 0.3
        if info["fat_required"] is not None:
            confidence += 0.2
        if notes:
            confidence += 0.2
        
        # Default fallbacks
        if info["with_food"] is None:
            info["with_food"] = True  # Safe default
            notes.append("Рекомендація за замовчуванням - з їжею")
        
        if info["fat_required"] is None:
            info["fat_required"] = False
        
        return ResearchResult(
            name=name.title(),
            with_food=info["with_food"],
            fat_required=info["fat_required"],
            best_time=info["best_time"],
            notes="; ".join(notes) if notes else "Базується на автоматичному пошуку",
            confidence=confidence,
            sources=sources,
            research_date=datetime.now().isoformat(),
            found=True
        )
    
    def get_cached_research(self, name: str) -> Optional[ResearchResult]:
        """Check if supplement research is already cached"""
        normalized = self.normalize_supplement_name(name)
        
        if normalized in self.research_db["supplements"]:
            data = self.research_db["supplements"][normalized]
            return ResearchResult(**data)
        
        return None
    
    def cache_research(self, name: str, result: ResearchResult):
        """Cache research result for future use"""
        normalized = self.normalize_supplement_name(name)
        self.research_db["supplements"][normalized] = asdict(result)
        self.save_research_db()
    
    async def research_supplement(self, name: str, use_cache: bool = True) -> ResearchResult:
        """Research supplement info automatically"""
        print(f"🔍 Researching {name}...")
        
        # Check cache first
        if use_cache:
            cached = self.get_cached_research(name)
            if cached and cached.confidence > 0.5:  # Use cached if confident
                print(f"✅ Found cached info for {name} (confidence: {cached.confidence:.1f})")
                return cached
        
        # Search the web
        search_results = self.search_web_for_supplement(name)
        
        if not search_results:
            # No results found - return default safe values
            result = ResearchResult(
                name=name.title(),
                with_food=True,  # Safe default
                fat_required=False,
                best_time="any",
                notes="Автоматичний пошук не знайшов інформацію. Рекомендація за замовчуванням.",
                confidence=0.1,
                sources=[],
                research_date=datetime.now().isoformat(),
                found=False
            )
        else:
            # Extract info from search results
            result = self.extract_supplement_info_from_text(name, search_results)
            
            if not result:
                # Extraction failed - return default
                result = ResearchResult(
                    name=name.title(),
                    with_food=True,
                    fat_required=False,
                    best_time="any",
                    notes="Не вдалося автоматично визначити параметри. Безпечна рекомендація.",
                    confidence=0.2,
                    sources=[url["url"] for url in search_results[:2]],
                    research_date=datetime.now().isoformat(),
                    found=False
                )
        
        # Cache the result
        self.cache_research(name, result)
        
        confidence_emoji = "🟢" if result.confidence > 0.7 else "🟡" if result.confidence > 0.4 else "🔴"
        print(f"{confidence_emoji} Research complete for {name} (confidence: {result.confidence:.1f})")
        
        return result
    
    def get_research_stats(self) -> Dict:
        """Get statistics about research database"""
        total_supplements = len(self.research_db["supplements"])
        high_confidence = sum(1 for supp in self.research_db["supplements"].values() 
                             if supp.get("confidence", 0) > 0.7)
        
        return {
            "total_researched": total_supplements,
            "high_confidence": high_confidence,
            "last_updated": self.research_db.get("last_updated"),
            "coverage_percent": (high_confidence / total_supplements * 100) if total_supplements > 0 else 0
        }


# Integration function for existing supplement_lookup.py
def create_intelligent_lookup_integration(data_dir: Path, brave_api_key: str = None):
    """Create intelligent lookup instance for integration"""
    return IntelligentLookup(data_dir, brave_api_key)


if __name__ == "__main__":
    # Test
    import asyncio
    from pathlib import Path
    
    async def test_lookup():
        # You need to provide your Brave Search API key
        lookup = IntelligentLookup(Path("../data"), brave_api_key="YOUR_BRAVE_API_KEY")
        
        # Test research
        result = await lookup.research_supplement("Rhodiola Rosea")
        print(f"Result: {result}")
        
        # Test stats
        stats = lookup.get_research_stats()
        print(f"Stats: {stats}")
    
    # asyncio.run(test_lookup())