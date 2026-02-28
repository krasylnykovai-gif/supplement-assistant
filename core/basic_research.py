"""
Basic supplement research without external APIs
Uses pattern matching and common knowledge to provide basic info
"""
from typing import Optional
from dataclasses import dataclass


@dataclass
class BasicSupplementInfo:
    name: str
    with_food: bool
    fat_required: bool
    best_time: str
    notes: str
    confidence: float  # 0-1


def basic_supplement_research(name: str) -> Optional[BasicSupplementInfo]:
    """
    Provide basic supplement info based on patterns and common knowledge
    No external API needed - uses built-in rules
    """
    name_lower = name.lower().strip()
    
    # Mushroom supplements - common patterns
    mushroom_keywords = ["mushroom", "cordyceps", "shiitake", "maitake", "chaga", "turkey tail"]
    if any(keyword in name_lower for keyword in mushroom_keywords):
        return BasicSupplementInfo(
            name=name.title(),
            with_food=True,
            fat_required=False,
            best_time="morning" if "cordyceps" in name_lower else "any",
            notes="Mushroom supplement. Generally taken with meals.",
            confidence=0.7
        )
    
    # Herbal adaptogens - energizing
    energizing_herbs = ["rhodiola", "ginseng", "schisandra", "eleuthero"]
    if any(herb in name_lower for herb in energizing_herbs):
        return BasicSupplementInfo(
            name=name.title(),
            with_food=True,
            fat_required=False,
            best_time="morning",
            notes="Energizing adaptogen. Best taken in morning to avoid sleep issues.",
            confidence=0.8
        )
    
    # Calming herbs
    calming_herbs = ["valerian", "passionflower", "chamomile", "lemon balm", "lavender"]
    if any(herb in name_lower for herb in calming_herbs):
        return BasicSupplementInfo(
            name=name.title(),
            with_food=True,
            fat_required=False,
            best_time="evening",
            notes="Calming herb. Best taken in evening, 30-60 minutes before bed.",
            confidence=0.8
        )
    
    # Vitamins (fat-soluble)
    fat_soluble_vitamins = ["vitamin a", "vitamin d", "vitamin e", "vitamin k"]
    if any(vit in name_lower for vit in fat_soluble_vitamins):
        return BasicSupplementInfo(
            name=name.title(),
            with_food=True,
            fat_required=True,
            best_time="morning",
            notes="Fat-soluble vitamin. Take with meals containing fats for better absorption.",
            confidence=0.9
        )
    
    # Water-soluble vitamins
    water_soluble = ["vitamin b", "vitamin c", "b12", "b6", "folate", "biotin"]
    if any(vit in name_lower for vit in water_soluble):
        return BasicSupplementInfo(
            name=name.title(),
            with_food=True,
            fat_required=False,
            best_time="morning",
            notes="Water-soluble vitamin. Take with food to reduce stomach upset.",
            confidence=0.9
        )
    
    # Minerals
    minerals = ["calcium", "magnesium", "zinc", "iron", "copper", "selenium"]
    if any(mineral in name_lower for mineral in minerals):
        with_food = True
        best_time = "evening" if "magnesium" in name_lower else "morning" if "iron" in name_lower else "any"
        notes = "Mineral supplement. Take with food to improve absorption and reduce stomach upset."
        
        return BasicSupplementInfo(
            name=name.title(),
            with_food=with_food,
            fat_required=False,
            best_time=best_time,
            notes=notes,
            confidence=0.8
        )
    
    # Amino acids
    amino_acids = ["l-theanine", "l-carnitine", "l-arginine", "l-citrulline", "taurine", "glycine"]
    if any(amino in name_lower for amino in amino_acids):
        # Glycine and theanine are calming
        if "glycine" in name_lower or "theanine" in name_lower:
            best_time = "evening"
            notes = "Calming amino acid. Can be taken in evening."
        else:
            best_time = "morning"
            notes = "Amino acid supplement. Often taken on empty stomach for better absorption."
        
        return BasicSupplementInfo(
            name=name.title(),
            with_food=False,
            fat_required=False,
            best_time=best_time,
            notes=notes,
            confidence=0.8
        )
    
    # Oils and fatty acids
    oils = ["fish oil", "krill oil", "flax oil", "omega", "dha", "epa"]
    if any(oil in name_lower for oil in oils):
        return BasicSupplementInfo(
            name=name.title(),
            with_food=True,
            fat_required=True,
            best_time="any",
            notes="Fatty acid supplement. Take with meals to improve absorption and reduce fishy taste.",
            confidence=0.9
        )
    
    # Protein supplements
    proteins = ["protein", "whey", "casein", "collagen", "peptides"]
    if any(protein in name_lower for protein in proteins):
        return BasicSupplementInfo(
            name=name.title(),
            with_food=False,
            fat_required=False,
            best_time="any",
            notes="Protein supplement. Can be taken anytime, often mixed with liquids.",
            confidence=0.8
        )
    
    # Enzyme supplements
    enzymes = ["enzyme", "protease", "amylase", "lipase", "bromelain", "papain"]
    if any(enzyme in name_lower for enzyme in enzymes):
        return BasicSupplementInfo(
            name=name.title(),
            with_food=True,
            fat_required=False,
            best_time="any",
            notes="Digestive enzyme. Take with meals for best effect.",
            confidence=0.7
        )
    
    # Probiotics
    if "probiotic" in name_lower or "lactobacillus" in name_lower or "bifidobacterium" in name_lower:
        return BasicSupplementInfo(
            name=name.title(),
            with_food=False,
            fat_required=False,
            best_time="morning",
            notes="Probiotic supplement. Often best taken on empty stomach, 30 minutes before meals.",
            confidence=0.8
        )
    
    # Antioxidants
    antioxidants = ["antioxidant", "resveratrol", "quercetin", "curcumin", "green tea", "grape seed"]
    if any(antioxidant in name_lower for antioxidant in antioxidants):
        return BasicSupplementInfo(
            name=name.title(),
            with_food=True,
            fat_required=True if "curcumin" in name_lower else False,
            best_time="any",
            notes="Antioxidant supplement. Take with meals for better absorption.",
            confidence=0.7
        )
    
    # More herb patterns
    herb_keywords = ["extract", "root", "leaf", "bark", "berry", "flower", "herb"]
    if any(keyword in name_lower for keyword in herb_keywords):
        return BasicSupplementInfo(
            name=name.title(),
            with_food=True,
            fat_required=False,
            best_time="any",
            notes="Herbal supplement. Take with meals to reduce stomach upset.",
            confidence=0.5
        )
    
    # Amino acid patterns (more comprehensive)
    if name_lower.startswith("l-") or "amino" in name_lower:
        return BasicSupplementInfo(
            name=name.title(),
            with_food=False,
            fat_required=False,
            best_time="morning",
            notes="Amino acid supplement. Often better on empty stomach.",
            confidence=0.6
        )
    
    # Oil patterns
    oil_keywords = ["oil", "fatty acid", "oleic", "linoleic"]
    if any(keyword in name_lower for keyword in oil_keywords):
        return BasicSupplementInfo(
            name=name.title(),
            with_food=True,
            fat_required=True,
            best_time="any",
            notes="Oil supplement. Take with meals for better absorption.",
            confidence=0.6
        )
    
    # Complex/specialized forms
    specialized_forms = ["picolinate", "bisglycinate", "citrate", "malate", "gluconate", "chelate"]
    if any(form in name_lower for form in specialized_forms):
        return BasicSupplementInfo(
            name=name.title(),
            with_food=True,
            fat_required=False,
            best_time="any",
            notes="Specialized supplement form. Take with meals for best absorption.",
            confidence=0.5
        )
    
    # If it contains numbers or chemical-sounding names
    if any(char.isdigit() for char in name) or len(name.split()) > 3:
        return BasicSupplementInfo(
            name=name.title(),
            with_food=True,
            fat_required=False,
            best_time="any",
            notes="Specialized supplement. Take with meals for safety.",
            confidence=0.4
        )
    
    # Default for completely unknown supplements
    return BasicSupplementInfo(
        name=name.title(),
        with_food=True,  # Safe default
        fat_required=False,
        best_time="any",
        notes="Unknown supplement. Safe recommendation: take with food to reduce stomach upset.",
        confidence=0.3
    )


if __name__ == "__main__":
    # Test
    test_supplements = [
        "reishi mushroom",
        "rhodiola rosea", 
        "valerian root",
        "vitamin d3",
        "magnesium glycinate",
        "l-theanine",
        "fish oil",
        "whey protein",
        "unknown supplement"
    ]
    
    for supplement in test_supplements:
        result = basic_supplement_research(supplement)
        if result:
            print(f"{supplement}: {result.name} - {result.best_time}, confidence: {result.confidence}")
        else:
            print(f"{supplement}: No info found")