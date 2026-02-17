"""
Supplement Lookup: searches for supplement info from reliable sources
Uses web search to find timing, dosage, and interaction info
"""
import re
import requests
from typing import Optional, Dict
from dataclasses import dataclass


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


def lookup_supplement(name: str) -> SupplementInfo:
    """
    Look up supplement information.
    First checks local database, then could extend to web search.
    """
    normalized = name.lower().strip()
    
    # Check known supplements
    if normalized in KNOWN_SUPPLEMENTS:
        info = KNOWN_SUPPLEMENTS[normalized]
        # Return a copy with the user's original name capitalized
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


if __name__ == "__main__":
    # Test
    print(lookup_supplement("Коензим Q10"))
    print(lookup_supplement("ашваганда"))
    print(lookup_supplement("невідомий бад"))
