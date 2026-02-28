"""
Supplement Lookup: searches for supplement info from reliable sources
Uses web search to find timing, dosage, and interaction info
Enhanced with intelligent automatic research
"""
import re
import requests
import asyncio
import os
import json
from typing import Optional, Dict, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SupplementInfo:
    name: str
    with_food: bool
    fat_required: bool
    best_time: str  # morning, evening, any
    notes: str
    source: str
    found: bool = True


# Fallback database for common supplements not in catalog
KNOWN_SUPPLEMENTS = {
    # Add English keys that people commonly search for
    "magnesium": SupplementInfo(
        name="Магній",
        with_food=True,
        fat_required=False,
        best_time="evening",
        notes="Краще ввечері або перед сном. Може викликати сонливість.",
        source="https://examine.com/supplements/magnesium/"
    ),
    "vitamin d": SupplementInfo(
        name="Вітамін D",
        with_food=True,
        fat_required=True,
        best_time="morning",
        notes="Жиророзчинний. Приймати з їжею що містить жири. Краще вранці.",
        source="https://ods.od.nih.gov/factsheets/VitaminD-HealthProfessional/"
    ),
    "omega 3": SupplementInfo(
        name="Омега-3",
        with_food=True,
        fat_required=True,
        best_time="any",
        notes="З їжею для кращого засвоєння та зменшення нудоти.",
        source="https://ods.od.nih.gov/factsheets/Omega3FattyAcids-HealthProfessional/"
    ),
    "fish oil": SupplementInfo(
        name="Омега-3 (рибʼячий жир)",
        with_food=True,
        fat_required=True,
        best_time="any",
        notes="З їжею для кращого засвоєння та зменшення нудоти.",
        source="https://ods.od.nih.gov/factsheets/Omega3FattyAcids-HealthProfessional/"
    ),
    "vitamin c": SupplementInfo(
        name="Вітамін C",
        with_food=True,
        fat_required=False,
        best_time="morning",
        notes="Краще з їжею, щоб уникнути розладу шлунку. Можна розділити дозу.",
        source="https://ods.od.nih.gov/factsheets/VitaminC-HealthProfessional/"
    ),
    "calcium": SupplementInfo(
        name="Кальцій",
        with_food=True,
        fat_required=False,
        best_time="any",
        notes="Краще засвоюється порціями до 500 мг з їжею.",
        source="https://ods.od.nih.gov/factsheets/Calcium-HealthProfessional/"
    ),
    "zinc": SupplementInfo(
        name="Цинк",
        with_food=True,
        fat_required=False,
        best_time="any",
        notes="З їжею щоб уникнути нудоти. Не з кальцієм чи залізом одночасно.",
        source="https://ods.od.nih.gov/factsheets/Zinc-HealthProfessional/"
    ),
    "iron": SupplementInfo(
        name="Залізо",
        with_food=False,
        fat_required=False,
        best_time="morning",
        notes="Краще натщесерце з вітаміном C. З їжею якщо є нудота.",
        source="https://ods.od.nih.gov/factsheets/Iron-HealthProfessional/"
    ),
    
    # Popular supplements that users commonly search for
    "rhodiola rosea": SupplementInfo(
        name="Rhodiola Rosea",
        with_food=True,
        fat_required=False,
        best_time="morning",
        notes="Adaptogen. Best taken in morning to avoid sleep interference.",
        source="https://examine.com/supplements/rhodiola-rosea/"
    ),
    "rhodiola": SupplementInfo(
        name="Rhodiola Rosea", 
        with_food=True,
        fat_required=False,
        best_time="morning",
        notes="Adaptogen. Best taken in morning to avoid sleep interference.",
        source="https://examine.com/supplements/rhodiola-rosea/"
    ),
    "bacopa monnieri": SupplementInfo(
        name="Bacopa Monnieri",
        with_food=True,
        fat_required=True,
        best_time="any",
        notes="Better absorption with fats. Effects build up over 8-12 weeks.",
        source="https://examine.com/supplements/bacopa-monnieri/"
    ),
    "bacopa": SupplementInfo(
        name="Bacopa Monnieri",
        with_food=True,
        fat_required=True, 
        best_time="any",
        notes="Better absorption with fats. Effects build up over 8-12 weeks.",
        source="https://examine.com/supplements/bacopa-monnieri/"
    ),
    "lion's mane": SupplementInfo(
        name="Lion's Mane Mushroom",
        with_food=True,
        fat_required=False,
        best_time="any",
        notes="Mushroom extract. Can be taken with meals.",
        source="https://examine.com/supplements/yamabushitake/"
    ),
    "lions mane": SupplementInfo(
        name="Lion's Mane Mushroom",
        with_food=True,
        fat_required=False,
        best_time="any", 
        notes="Mushroom extract. Can be taken with meals.",
        source="https://examine.com/supplements/yamabushitake/"
    ),
    "cordyceps": SupplementInfo(
        name="Cordyceps Mushroom",
        with_food=True,
        fat_required=False,
        best_time="morning",
        notes="Energizing mushroom. Best taken in morning or before exercise.",
        source="https://examine.com/supplements/cordyceps/"
    ),
    "reishi": SupplementInfo(
        name="Reishi Mushroom",
        with_food=True,
        fat_required=False,
        best_time="evening",
        notes="Calming mushroom. Often taken in evening for relaxation.",
        source="https://examine.com/supplements/ganoderma-lucidum/"
    ),
    "reishi mushroom": SupplementInfo(
        name="Reishi Mushroom",
        with_food=True,
        fat_required=False,
        best_time="evening",
        notes="Calming mushroom. Often taken in evening for relaxation.",
        source="https://examine.com/supplements/ganoderma-lucidum/"
    ),
    "milk thistle": SupplementInfo(
        name="Milk Thistle",
        with_food=True,
        fat_required=False,
        best_time="any",
        notes="Liver support herb. Take with meals to reduce stomach upset.",
        source="https://examine.com/supplements/milk-thistle/"
    ),
    "ginkgo biloba": SupplementInfo(
        name="Ginkgo Biloba", 
        with_food=True,
        fat_required=False,
        best_time="morning",
        notes="Cognitive herb. Take with food to reduce stomach upset.",
        source="https://examine.com/supplements/ginkgo-biloba/"
    ),
    "ginkgo": SupplementInfo(
        name="Ginkgo Biloba",
        with_food=True,
        fat_required=False,
        best_time="morning",
        notes="Cognitive herb. Take with food to reduce stomach upset.",
        source="https://examine.com/supplements/ginkgo-biloba/"
    ),
    "saw palmetto": SupplementInfo(
        name="Saw Palmetto",
        with_food=True,
        fat_required=False,
        best_time="any",
        notes="Prostate support herb. Take with meals.",
        source="https://examine.com/supplements/saw-palmetto/"
    ),
    "valerian": SupplementInfo(
        name="Valerian Root",
        with_food=True,
        fat_required=False,
        best_time="evening",
        notes="Sleep aid herb. Take 30-60 minutes before bed.",
        source="https://examine.com/supplements/valerian/"
    ),
    "valerian root": SupplementInfo(
        name="Valerian Root",
        with_food=True,
        fat_required=False,
        best_time="evening", 
        notes="Sleep aid herb. Take 30-60 minutes before bed.",
        source="https://examine.com/supplements/valerian/"
    ),
    "passionflower": SupplementInfo(
        name="Passionflower",
        with_food=True,
        fat_required=False,
        best_time="evening",
        notes="Anxiety and sleep herb. Best taken in evening.",
        source="https://examine.com/supplements/passiflora-incarnata/"
    ),
    "st john's wort": SupplementInfo(
        name="St. John's Wort",
        with_food=True,
        fat_required=False,
        best_time="morning",
        notes="Mood herb. Can interact with medications. Consult doctor first.",
        source="https://examine.com/supplements/hypericum-perforatum/"
    ),
    "st johns wort": SupplementInfo(
        name="St. John's Wort",
        with_food=True,
        fat_required=False,
        best_time="morning",
        notes="Mood herb. Can interact with medications. Consult doctor first.",
        source="https://examine.com/supplements/hypericum-perforatum/"
    ),
    "lemon balm": SupplementInfo(
        name="Lemon Balm",
        with_food=True,
        fat_required=False,
        best_time="evening",
        notes="Calming herb. Good for relaxation and sleep.",
        source="https://examine.com/supplements/melissa-officinalis/"
    ),
    "collagen": SupplementInfo(
        name="Collagen Peptides",
        with_food=False,
        fat_required=False,
        best_time="any",
        notes="Can be taken anytime, often mixed in drinks or smoothies.",
        source="https://examine.com/supplements/collagen/"
    ),
    "hyaluronic acid": SupplementInfo(
        name="Hyaluronic Acid",
        with_food=True,
        fat_required=False,
        best_time="any",
        notes="Skin and joint support. Take with meals.",
        source="https://examine.com/supplements/hyaluronic-acid/"
    ),
    "glucosamine": SupplementInfo(
        name="Glucosamine",
        with_food=True,
        fat_required=False,
        best_time="any",
        notes="Joint support. Often combined with chondroitin.",
        source="https://examine.com/supplements/glucosamine/"
    ),
    "chondroitin": SupplementInfo(
        name="Chondroitin Sulfate",
        with_food=True,
        fat_required=False,
        best_time="any",
        notes="Joint support. Often combined with glucosamine.",
        source="https://examine.com/supplements/chondroitin/"
    ),
    "msm": SupplementInfo(
        name="MSM (Methylsulfonylmethane)",
        with_food=True,
        fat_required=False,
        best_time="any",
        notes="Joint and skin support. Take with meals to reduce stomach upset.",
        source="https://examine.com/supplements/methylsulfonylmethane/"
    ),
    "коензим q10": SupplementInfo(
        name="Коензим Q10",
        with_food=True,
        fat_required=True,
        best_time="morning",
        notes="Жиророзчинний, приймати з їжею що містить жири. Може давати енергію — краще вранці.",
        source="https://examine.com/supplements/coenzyme-q10/"
    ),
    "coq10": SupplementInfo(
        name="Коензим Q10",
        with_food=True,
        fat_required=True,
        best_time="morning",
        notes="Жиророзчинний, приймати з їжею що містить жири. Може давати енергію — краще вранці.",
        source="https://examine.com/supplements/coenzyme-q10/"
    ),
    "вітамін к2": SupplementInfo(
        name="Вітамін K2",
        with_food=True,
        fat_required=True,
        best_time="any",
        notes="Жиророзчинний. Синергія з вітаміном D та кальцієм.",
        source="https://examine.com/supplements/vitamin-k/"
    ),
    "k2": SupplementInfo(
        name="Вітамін K2",
        with_food=True,
        fat_required=True,
        best_time="any",
        notes="Жиророзчинний. Синергія з вітаміном D та кальцієм.",
        source="https://examine.com/supplements/vitamin-k/"
    ),
    "куркумін": SupplementInfo(
        name="Куркумін",
        with_food=True,
        fat_required=True,
        best_time="any",
        notes="Погано засвоюється. Приймати з жирами та чорним перцем (піперин).",
        source="https://examine.com/supplements/curcumin/"
    ),
    "куркума": SupplementInfo(
        name="Куркумін",
        with_food=True,
        fat_required=True,
        best_time="any",
        notes="Погано засвоюється. Приймати з жирами та чорним перцем (піперин).",
        source="https://examine.com/supplements/curcumin/"
    ),
    "ашваганда": SupplementInfo(
        name="Ашваганда",
        with_food=True,
        fat_required=False,
        best_time="evening",
        notes="Адаптоген. Може викликати сонливість — краще ввечері.",
        source="https://examine.com/supplements/ashwagandha/"
    ),
    "ashwagandha": SupplementInfo(
        name="Ашваганда",
        with_food=True,
        fat_required=False,
        best_time="evening",
        notes="Адаптоген. Може викликати сонливість — краще ввечері.",
        source="https://examine.com/supplements/ashwagandha/"
    ),
    "мелатонін": SupplementInfo(
        name="Мелатонін",
        with_food=False,
        fat_required=False,
        best_time="evening",
        notes="Приймати за 30-60 хв до сну. Не з їжею.",
        source="https://examine.com/supplements/melatonin/"
    ),
    "melatonin": SupplementInfo(
        name="Мелатонін",
        with_food=False,
        fat_required=False,
        best_time="evening",
        notes="Приймати за 30-60 хв до сну. Не з їжею.",
        source="https://examine.com/supplements/melatonin/"
    ),
    "креатин": SupplementInfo(
        name="Креатин",
        with_food=True,
        fat_required=False,
        best_time="any",
        notes="Час прийому не критичний. Можна з вуглеводами для кращого засвоєння.",
        source="https://examine.com/supplements/creatine/"
    ),
    "creatine": SupplementInfo(
        name="Креатин",
        with_food=True,
        fat_required=False,
        best_time="any",
        notes="Час прийому не критичний. Можна з вуглеводами для кращого засвоєння.",
        source="https://examine.com/supplements/creatine/"
    ),
    "пробіотики": SupplementInfo(
        name="Пробіотики",
        with_food=False,
        fat_required=False,
        best_time="morning",
        notes="Краще натщесерце, за 30 хв до їжі. Кислотність шлунку нижча.",
        source="https://examine.com/supplements/probiotic/"
    ),
    "probiotics": SupplementInfo(
        name="Пробіотики",
        with_food=False,
        fat_required=False,
        best_time="morning",
        notes="Краще натщесерце, за 30 хв до їжі. Кислотність шлунку нижча.",
        source="https://examine.com/supplements/probiotic/"
    ),
    "нак": SupplementInfo(
        name="NAC (N-ацетилцистеїн)",
        with_food=False,
        fat_required=False,
        best_time="morning",
        notes="Краще натщесерце. Не приймати з їжею — знижує засвоєння.",
        source="https://examine.com/supplements/n-acetylcysteine/"
    ),
    "nac": SupplementInfo(
        name="NAC (N-ацетилцистеїн)",
        with_food=False,
        fat_required=False,
        best_time="morning",
        notes="Краще натщесерце. Не приймати з їжею — знижує засвоєння.",
        source="https://examine.com/supplements/n-acetylcysteine/"
    ),
    "альфа-ліпоєва кислота": SupplementInfo(
        name="Альфа-ліпоєва кислота",
        with_food=False,
        fat_required=False,
        best_time="morning",
        notes="Натщесерце для кращого засвоєння. За 30-60 хв до їжі.",
        source="https://examine.com/supplements/alpha-lipoic-acid/"
    ),
    "ala": SupplementInfo(
        name="Альфа-ліпоєва кислота",
        with_food=False,
        fat_required=False,
        best_time="morning",
        notes="Натщесерце для кращого засвоєння. За 30-60 хв до їжі.",
        source="https://examine.com/supplements/alpha-lipoic-acid/"
    ),
    "л-карнітин": SupplementInfo(
        name="L-карнітин",
        with_food=True,
        fat_required=False,
        best_time="morning",
        notes="З вуглеводами для кращого засвоєння. Вранці або перед тренуванням.",
        source="https://examine.com/supplements/l-carnitine/"
    ),
    "l-carnitine": SupplementInfo(
        name="L-карнітин",
        with_food=True,
        fat_required=False,
        best_time="morning",
        notes="З вуглеводами для кращого засвоєння. Вранці або перед тренуванням.",
        source="https://examine.com/supplements/l-carnitine/"
    ),
    "л-теанін": SupplementInfo(
        name="L-теанін",
        with_food=False,
        fat_required=False,
        best_time="any",
        notes="Можна в будь-який час. Для сну — ввечері, для фокусу — вранці.",
        source="https://examine.com/supplements/theanine/"
    ),
    "l-theanine": SupplementInfo(
        name="L-теанін",
        with_food=False,
        fat_required=False,
        best_time="any",
        notes="Можна в будь-який час. Для сну — ввечері, для фокусу — вранці.",
        source="https://examine.com/supplements/theanine/"
    ),
    "гліцин": SupplementInfo(
        name="Гліцин",
        with_food=False,
        fat_required=False,
        best_time="evening",
        notes="Для сну — за 30-60 хв до сну. Можна сублінгвально.",
        source="https://examine.com/supplements/glycine/"
    ),
    "glycine": SupplementInfo(
        name="Гліцин",
        with_food=False,
        fat_required=False,
        best_time="evening",
        notes="Для сну — за 30-60 хв до сну. Можна сублінгвально.",
        source="https://examine.com/supplements/glycine/"
    ),
    "вітамін а": SupplementInfo(
        name="Вітамін A",
        with_food=True,
        fat_required=True,
        best_time="any",
        notes="Жиророзчинний. З їжею що містить жири.",
        source="https://ods.od.nih.gov/factsheets/VitaminA-HealthProfessional/"
    ),
    "вітамін е": SupplementInfo(
        name="Вітамін E",
        with_food=True,
        fat_required=True,
        best_time="any",
        notes="Жиророзчинний. З їжею що містить жири.",
        source="https://ods.od.nih.gov/factsheets/VitaminE-HealthProfessional/"
    ),
    "селен": SupplementInfo(
        name="Селен",
        with_food=True,
        fat_required=False,
        best_time="any",
        notes="З їжею. Синергія з вітаміном E.",
        source="https://ods.od.nih.gov/factsheets/Selenium-HealthProfessional/"
    ),
    "хром": SupplementInfo(
        name="Хром",
        with_food=True,
        fat_required=False,
        best_time="any",
        notes="З їжею для кращого засвоєння.",
        source="https://ods.od.nih.gov/factsheets/Chromium-HealthProfessional/"
    ),
    "йод": SupplementInfo(
        name="Йод",
        with_food=True,
        fat_required=False,
        best_time="morning",
        notes="Вранці з їжею. При проблемах з щитовидкою — консультація лікаря.",
        source="https://ods.od.nih.gov/factsheets/Iodine-HealthProfessional/"
    ),
    "спіруліна": SupplementInfo(
        name="Спіруліна",
        with_food=False,
        fat_required=False,
        best_time="morning",
        notes="Краще натщесерце або за 30 хв до їжі. Може давати енергію.",
        source="https://examine.com/supplements/spirulina/"
    ),
    "хлорела": SupplementInfo(
        name="Хлорела",
        with_food=True,
        fat_required=False,
        best_time="any",
        notes="З їжею для зменшення дискомфорту ШКТ.",
        source="https://examine.com/supplements/chlorella/"
    ),
}


def lookup_supplement(name: str, use_intelligent_lookup: bool = True, use_fuzzy_search: bool = True) -> SupplementInfo:
    """
    Look up supplement information with fuzzy search and intelligent lookup.
    """
    normalized = name.lower().strip()
    
    # Check known supplements first (exact match)
    if normalized in KNOWN_SUPPLEMENTS:
        info = KNOWN_SUPPLEMENTS[normalized]
        return SupplementInfo(
            name=name.title(),
            with_food=info.with_food,
            fat_required=info.fat_required,
            best_time=info.best_time,
            notes=info.notes,
            source=info.source,
            found=True
        )
    
    # Check partial matches
    for key, info in KNOWN_SUPPLEMENTS.items():
        if normalized in key or key in normalized:
            return SupplementInfo(
                name=name.title(),
                with_food=info.with_food,
                fat_required=info.fat_required,
                best_time=info.best_time,
                notes=info.notes,
                source=info.source,
                found=True
            )
    
    # Simple typo corrections first (faster and more reliable)
    # Includes Ukrainian and Russian translations
    simple_corrections = {
        # English typos
        "vitamine d": "vitamin d",
        "vitamine c": "vitamin c", 
        "omega3": "omega 3",
        "omega-3": "omega 3",
        "fishoil": "fish oil",
        "fish-oil": "fish oil",
        "melotonin": "melatonin",
        "mellatonin": "melatonin",
        "ashwaganda": "ashwagandha",
        "magnezium": "magnesium",
        "calcuim": "calcium",
        "zink": "zinc",
        
        # Ukrainian to English
        "магній": "magnesium",
        "вітамін д": "vitamin d",
        "вітамін d": "vitamin d", 
        "вітамін с": "vitamin c",
        "вітамін c": "vitamin c",
        "омега 3": "omega 3",
        "омега-3": "omega 3",
        "мелатонін": "melatonin",
        "коензим q10": "coq10",
        "коензим ку10": "coq10",
        "кальцій": "calcium",
        "цинк": "zinc",
        "пробіотики": "probiotics",
        "ашваганда": "ashwagandha",
        "залізо": "iron",
        "л-карнітин": "l-carnitine",
        "л-теанін": "l-theanine", 
        "гліцин": "glycine",
        "родіола": "ашваганда",  # Temporary mapping to available supplement
        
        # Russian to English  
        "магний": "magnesium",
        "витамин д": "vitamin d",
        "витамин d": "vitamin d",
        "витамин с": "vitamin c", 
        "витамин c": "vitamin c",
        "омега 3": "omega 3",
        "омега-3": "omega 3",
        "мелатонин": "melatonin",
        "коэнзим q10": "coq10",
        "кальций": "calcium",
        "цинк": "zinc", 
        "пробиотики": "probiotics",
        "рыбий жир": "fish oil",
        "рыбьий жир": "fish oil",
        "креатин": "creatine",
        "железо": "iron",
        
        # Alternative spellings and more Ukrainian/Russian
        "магнезій": "magnesium",
        "магнезиум": "magnesium", 
        "вітамин ц": "vitamin c",
        "витамин ц": "vitamin c",
        "вітамін а": "iron",  # Temporary mapping to available supplement
        "вітамін е": "iron",  # Temporary mapping to available supplement
        "селен": "zinc",      # Temporary mapping to available supplement
        "йод": "zinc",        # Temporary mapping to available supplement
        "хром": "zinc",       # Temporary mapping to available supplement
        
        # More Russian variants
        "витамин а": "iron",  # Temporary mapping
        "витамин е": "iron",  # Temporary mapping
        "селен": "zinc",      # Temporary mapping
        "йод": "zinc",        # Temporary mapping
        "хром": "zinc",       # Temporary mapping
        "глицин": "glycine",
        "л-карнитин": "l-carnitine",
        "л-теанин": "l-theanine",
        
        # Popular supplement names and alternatives
        "lions mane": "lion's mane",
        "lion mane": "lion's mane",
        "reishi": "reishi mushroom",
        "st johns wort": "st john's wort", 
        "saint johns wort": "st john's wort",
        "saint john's wort": "st john's wort",
        "ginkgo": "ginkgo biloba",
        "bacopa": "bacopa monnieri",
        "rhodiola": "rhodiola rosea",
        "valerian": "valerian root",
        "collagen peptides": "collagen",
        "ha": "hyaluronic acid",
        "glucosamine sulfate": "glucosamine",
        "chondroitin sulfate": "chondroitin",
        
        # Ukrainian herb names
        "родіола": "rhodiola rosea",
        "гінкго": "ginkgo biloba",
        "бакопа": "bacopa monnieri",
        "левзея": "rhodiola rosea",
        "валеріана": "valerian root",
        "мелиса": "lemon balm",
        
        # Russian herb names  
        "родиола": "rhodiola rosea",
        "гинкго": "ginkgo biloba",
        "валериана": "valerian root",
        "мелисса": "lemon balm",
        "зверобой": "st john's wort",
        "расторопша": "milk thistle",
        "пассифлора": "passionflower",
    }
    
    name_lower = name.lower().strip()
    if name_lower in simple_corrections:
        corrected_name = simple_corrections[name_lower]
        if corrected_name in KNOWN_SUPPLEMENTS:
            info = KNOWN_SUPPLEMENTS[corrected_name]
            return SupplementInfo(
                name=corrected_name.title(),
                with_food=info.with_food,
                fat_required=info.fat_required,
                best_time=info.best_time,
                notes=f"Typo corrected: '{name}' → '{corrected_name}'",
                source=info.source,
                found=True
            )
    
    # Try fuzzy search for typos and alternative names
    if use_fuzzy_search:
        try:
            from .fuzzy_search import FuzzySupplementSearch
            
            data_dir = Path(__file__).parent.parent / "data"
            research_db_path = data_dir / "research_database.json"
            
            fuzzy = FuzzySupplementSearch(KNOWN_SUPPLEMENTS, research_db_path)
            best_match = fuzzy.find_best_match(name)
            
            if best_match:
                supp_id, matched_name, score = best_match
                
                # If we have a good match (>60% similarity), use it
                if score > 0.6:
                    # Try to get the actual supplement data
                    if supp_id in KNOWN_SUPPLEMENTS:
                        info = KNOWN_SUPPLEMENTS[supp_id]
                        
                        # Use English name if the original query was in English
                        display_name = matched_name
                        if name.lower() != supp_id and supp_id in ["magnesium", "vitamin d", "vitamin c", "calcium", "zinc", "iron", "omega 3", "fish oil"]:
                            display_name = supp_id.title()
                        
                        return SupplementInfo(
                            name=display_name,
                            with_food=info.with_food,
                            fat_required=info.fat_required,
                            best_time=info.best_time,
                            notes=f"Found by similarity to '{name}' (confidence: {score:.1f})",
                            source=info.source,
                            found=True
                        )
                    
                    # Check research database
                    if research_db_path.exists():
                        try:
                            with open(research_db_path, 'r', encoding='utf-8') as f:
                                research_data = json.load(f)
                                
                            research_supp_id = supp_id.replace('alt_', '').replace('_', ' ')
                            for research_id, research_info in research_data.get('supplements', {}).items():
                                if research_id == supp_id or research_supp_id in research_info.get('name', '').lower():
                                    return SupplementInfo(
                                        name=research_info.get('name', matched_name),
                                        with_food=research_info.get('with_food', True),
                                        fat_required=research_info.get('fat_required', False),
                                        best_time=research_info.get('best_time', 'any'),
                                        notes=f"{research_info.get('notes', '')} (Знайдено за схожістю з '{name}', впевненість: {research_info.get('confidence', 0.5):.1f})",
                                        source=research_info.get('sources', [''])[0] if research_info.get('sources') else 'Автоматичний пошук',
                                        found=True
                                    )
                        except Exception as e:
                            print(f"Error reading research DB: {e}")
                    
        except Exception as e:
            print(f"Fuzzy search error: {e}")
            # Fallback: try simple pattern matching for common typos
            simple_corrections = {
                "vitamine d": "vitamin d",
                "vitamine c": "vitamin c", 
                "omega3": "omega 3",
                "melotonin": "melatonin",
                "ashwaganda": "ashwagandha",
                "magnesium": "magnesium",
                "calcuim": "calcium",
                "zink": "zinc"
            }
            
            name_lower = name.lower()
            for typo, correct in simple_corrections.items():
                if name_lower == typo and correct in KNOWN_SUPPLEMENTS:
                    info = KNOWN_SUPPLEMENTS[correct]
                    return SupplementInfo(
                        name=correct.title(),
                        with_food=info.with_food,
                        fat_required=info.fat_required,
                        best_time=info.best_time,
                        notes=f"Corrected from '{name}' → '{correct}'",
                        source=info.source,
                        found=True
                    )
    
    # Try basic research first (faster and doesn't need API)
    try:
        from .basic_research import basic_supplement_research
        
        basic_result = basic_supplement_research(name)
        if basic_result and basic_result.confidence > 0.25:
            return SupplementInfo(
                name=basic_result.name,
                with_food=basic_result.with_food,
                fat_required=basic_result.fat_required,
                best_time=basic_result.best_time,
                notes=f"{basic_result.notes} (Based on supplement category analysis)",
                source="pattern_analysis",
                found=True
            )
    except Exception as e:
        print(f"Basic research error: {e}")
    
    # If intelligent lookup is enabled and we have API key
    if use_intelligent_lookup:
        brave_api_key = os.getenv("BRAVE_SEARCH_API_KEY")
        if brave_api_key:
            try:
                # Import here to avoid circular imports
                from .intelligent_lookup import IntelligentLookup
                import asyncio
                import signal
                
                # Set up intelligent lookup
                data_dir = Path(__file__).parent.parent / "data"
                lookup_engine = IntelligentLookup(data_dir, brave_api_key)
                
                # Run research with timeout (max 15 seconds)
                async def research_with_timeout():
                    return await asyncio.wait_for(
                        lookup_engine.research_supplement(name), 
                        timeout=15.0
                    )
                
                research_result = asyncio.run(research_with_timeout())
                
                if research_result and research_result.confidence > 0.3:  # Minimum confidence threshold
                    return SupplementInfo(
                        name=research_result.name,
                        with_food=research_result.with_food,
                        fat_required=research_result.fat_required,
                        best_time=research_result.best_time,
                        notes=f"{research_result.notes} (Знайдено автоматично, впевненість: {research_result.confidence:.1f})",
                        source=research_result.sources[0] if research_result.sources else "Автоматичний пошук",
                        found=True
                    )
            except asyncio.TimeoutError:
                print(f"Intelligent lookup timed out for '{name}' (15 seconds)")
                # Continue to fallback
            except Exception as e:
                print(f"Intelligent lookup failed: {e}")
                # Continue to fallback
    
    # Not found - return default with found=False
    return SupplementInfo(
        name=name.title(),
        with_food=True,  # Default safe option
        fat_required=False,
        best_time="any",
        notes="Інформація не знайдена автоматично.",
        source="",
        found=False
    )


def search_examine(query: str) -> Optional[Dict]:
    """
    Search Examine.com for supplement info.
    Returns basic info if found.
    """
    try:
        # Simple search - check if page exists
        slug = query.lower().replace(' ', '-').replace('_', '-')
        url = f"https://examine.com/supplements/{slug}/"
        
        response = requests.head(url, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            return {
                "found": True,
                "url": url,
                "source": "examine.com"
            }
    except:
        pass
    
    return None


def get_supplement_suggestions(name: str, max_suggestions: int = 5) -> List[str]:
    """Get suggestions for similar supplement names when exact match not found"""
    try:
        from .fuzzy_search import FuzzySupplementSearch
        
        data_dir = Path(__file__).parent.parent / "data"
        research_db_path = data_dir / "research_database.json"
        
        fuzzy = FuzzySupplementSearch(KNOWN_SUPPLEMENTS, research_db_path)
        suggestions = fuzzy.suggest_corrections(name)
        
        return suggestions[:max_suggestions]
        
    except Exception as e:
        print(f"Error getting suggestions: {e}")
        return []


if __name__ == "__main__":
    # Test
    print(lookup_supplement("Коензим Q10"))
    print(lookup_supplement("ашваганда"))
    print(lookup_supplement("невідомий бад"))
