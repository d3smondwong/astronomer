"""
Wu Xing (五行) - Five Elements Calculation Module

This module extracts and analyzes the Five Elements (Wu Xing) composition from a BaZi chart,
as well as the Hidden Stems (藏干) contained within each Earthly Branch.

Professional Scoring System:
This implementation uses a weighted scoring system (targeting 10.0 total points) based on
professional Bazi (Zi Ping) methodology:

1. Heavenly Stems: 1.0 point each (4 stems = 4.0 total)
2. Regular Branches: [Main (本气): 0.7, Secondary (中气): 0.2, Tertiary (余气): 0.1] per branch
3. Month Branch: [Main (本气): 2.0, Secondary (中气): 0.6, Tertiary (余气): 0.4] (acts as "Commander")

Total Scale: ~10.0 points
This preserves the relative weight of each element for LLM interpretation.

Key Functions:
    get_wu_xing(lunar_birthday): Extracts Wu Xing composition, Hidden Stems, and professional scores.

    Returns:
        dict: Structured JSON with Five Elements data organized by pillar:
        {
            "年柱": {
                "五行": {"天干五行": "...", "地支五行": "..."},
                "藏干": [...]
            },
            "月柱": {...},
            "日柱": {...},
            "时柱": {...},
            "五行力量": {
                "木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0  # Raw weighted scores
            }
        }

The Five Elements:
- 木 (Wood): Growth, expansion, flexibility
- 火 (Fire): Passion, activity, transformation
- 土 (Earth): Stability, nurture, balance
- 金 (Metal): Strength, discipline, precision
- 水 (Water): Flow, wisdom, flexibility

This data is LLM-ready and professional practitioners can immediately recognize the scoring logic.
"""

from lunar_python import Lunar
from datetime import datetime
from collections import Counter
from src.astronomer_calculations.solar_lunar_time import get_true_solar_time


def get_wu_xing(lunar_birthday: Lunar) -> dict:
    """
    Extract Five Elements (Wu Xing) from lunar birthday and return as JSON format (Chinese keys).

    Args:
        lunar_birthday (Lunar): Lunar calendar object

    Returns:
        dict: Five Elements composition by pillar with 天干五行 (Stem Element) and 地支五行 (Branch Element)
    """
    # Get the EightChar object
    bazi = lunar_birthday.getEightChar()

    # Extract Five Elements (Wu Xing) for each pillar
    # Each pillar's Wu Xing is a string like "木土" (stem element + branch element)
    year_wu_xing = bazi.getYearWuXing()
    month_wu_xing = bazi.getMonthWuXing()
    day_wu_xing = bazi.getDayWuXing()
    hour_wu_xing = bazi.getTimeWuXing()

    # Extract Hidden Stems (Hidden Gan) for each pillar
    year_hide_gan = bazi.getYearHideGan()
    month_hide_gan = bazi.getMonthHideGan()
    day_hide_gan = bazi.getDayHideGan()
    hour_hide_gan = bazi.getTimeHideGan()

    # Calculate Wu Xing strength using professional weighted scoring
    wu_xing_strength = calculate_wu_xing_strength_professional(
        year_wu_xing,
        month_wu_xing,
        day_wu_xing,
        hour_wu_xing,
        year_hide_gan,
        month_hide_gan,
        day_hide_gan,
        hour_hide_gan,
    )

    return {
        "年柱": {
            "五行": parse_wu_xing(year_wu_xing),
            "藏干": year_hide_gan,
        },
        "月柱": {
            "五行": parse_wu_xing(month_wu_xing),
            "藏干": month_hide_gan,
        },
        "日柱": {
            "五行": parse_wu_xing(day_wu_xing),
            "藏干": day_hide_gan,
        },
        "时柱": {
            "五行": parse_wu_xing(hour_wu_xing),
            "藏干": hour_hide_gan,
        },
        "五行力量": wu_xing_strength,
    }


# Parse each Wu Xing string into stem and branch elements
def parse_wu_xing(wu_xing_str: str) -> dict:
    """Split Wu Xing string (e.g., '木土') into stem and branch elements"""
    if len(wu_xing_str) >= 2:
        return {"天干五行": wu_xing_str[0], "地支五行": wu_xing_str[1]}
    return {"天干五行": "", "地支五行": ""}


def calculate_wu_xing_strength_professional(
    year_wu_xing: str,
    month_wu_xing: str,
    day_wu_xing: str,
    hour_wu_xing: str,
    year_hide: list,
    month_hide: list,
    day_hide: list,
    hour_hide: list,
) -> dict:
    """
    Calculate Wu Xing strength using professional weighted scoring (Zi Ping method).

    This implements a 10-point scale system:
    - Heavenly Stems: 1.0 point each (4 stems = 4.0 total)
    - Regular Branches: [0.7, 0.2, 0.1] for [Main, Secondary, Tertiary] hidden stems
    - Month Branch (Commander): [2.0, 0.6, 0.4] for [Main, Secondary, Tertiary] hidden stems

    Args:
        *_wu_xing: Wu Xing strings for each pillar (e.g., '木土')
        *_hide: Hidden stems lists for each pillar

    Returns:
        dict: Weighted scores for each element (木, 火, 土, 金, 水) with raw point values
    """
    # Mapping of stems to their Wu Xing elements
    stem_to_wu_xing = {
        "甲": "木",
        "乙": "木",  # Wood
        "丙": "火",
        "丁": "火",  # Fire
        "戊": "土",
        "己": "土",  # Earth
        "庚": "金",
        "辛": "金",  # Metal
        "壬": "水",
        "癸": "水",  # Water
    }

    # Initialize scores
    scores = {
        "木": 0.0,
        "火": 0.0,
        "土": 0.0,
        "金": 0.0,
        "水": 0.0,
    }

    # === PART 1: Score Heavenly Stems (1.0 point each) ===
    # Each stem in the Wu Xing string is the heavenly stem element
    for wu_xing in [year_wu_xing, month_wu_xing, day_wu_xing, hour_wu_xing]:
        if wu_xing:  # First character is the Heavenly Stem's Wu Xing
            stem_element = wu_xing[0]
            if stem_element in scores:
                scores[stem_element] += 1.0

    # === PART 2: Score Branches via Hidden Stems ===
    # Weight multipliers for each branch type
    # [Primary (本气), Secondary (中气), Tertiary (余气)]
    regular_branch_weights = [0.7, 0.2, 0.1]
    month_branch_weights = [2.0, 0.6, 0.4]

    # Process each branch
    branches = [
        (year_hide, False),  # Year Branch (regular)
        (month_hide, True),  # Month Branch (commander)
        (day_hide, False),  # Day Branch (regular)
        (hour_hide, False),  # Hour Branch (regular)
    ]

    for hide_stems, is_month_branch in branches:
        weights = month_branch_weights if is_month_branch else regular_branch_weights

        for index, hide_stem in enumerate(hide_stems):
            if hide_stem in stem_to_wu_xing:
                element = stem_to_wu_xing[hide_stem]
                weight = weights[index] if index < len(weights) else 0.0
                scores[element] += weight

    # Round to 2 decimal places for cleaner display
    return {element: round(score, 2) for element, score in scores.items()}


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from lunar_python import Solar

    # python -m src.astronomer_calculations.wu_xing

    # Desmond's birthday example
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    tst_birthday, _ = get_true_solar_time(
        datetime_birthday, 1.3253, 103.808053
    )  # Get true solar time

    print("阳历生日: " + solar_birthday.toYmdHms())
    print("真太阳时生日: " + tst_birthday.toYmdHms())

    lunar_birthday = tst_birthday.getLunar()  # Convert to lunar calendar

    # Get Wu Xing in LLM-ready JSON format
    result = get_wu_xing(lunar_birthday)

    print(f"\n--- JSON Output for LLM ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))
