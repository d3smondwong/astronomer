"""
BaZi Pillars (八字) - Four Pillars of Destiny Calculation Module

This module extracts and structures the Four Pillars (Si Zhu) of a BaZi chart,
which form the foundation of Chinese astrology. Each pillar represents a different
temporal dimension and contains both a Heavenly Stem (天干) and an Earthly Branch (地支).

The Four Pillars:
1. 年柱 (Year Pillar): Represents ancestry, childhood, family background, early fortune
2. 月柱 (Month Pillar): Represents parents, siblings, middle age, public image
3. 日柱 (Day Pillar): Represents the self, marriage, health, core character (most important)
4. 时柱 (Hour Pillar): Represents children, later life, legacy

Each pillar contains:
- 天干 (Heavenly Stem): 10 stems (甲乙丙丁戊己庚辛壬癸)
  Represents the outer, active, and apparent characteristics
- 地支 (Earthly Branch): 12 branches (子丑寅卯辰巳午未申酉戌亥)
  Represents the inner, passive, and hidden characteristics

Key Function:
    get_bazi_pillars(lunar_birthday): Extracts the Four Pillars with their stems and branches.

    Returns:
        dict: Structured JSON with BaZi pillars organized hierarchically:
        {
            "八字": {
                "年柱": {"天干": "...", "地支": "..."},
                "月柱": {"天干": "...", "地支": "..."},
                "日柱": {"天干": "...", "地支": "..."},
                "时柱": {"天干": "...", "地支": "..."}
            }
        }

This foundational data serves as the basis for all other BaZi calculations including
Five Elements, Ten Gods, Shen Sha, and interactions. Output is LLM-ready for AI interpretation.
"""

from lunar_python import Lunar
from datetime import datetime
from lunar_python import Solar
from src.astronomer_calculations.solar_lunar_time import get_true_solar_time


def get_bazi_pillars(lunar_birthday: Lunar) -> dict:
    """
    Extract BaZi pillars from lunar birthday and return as JSON format (Chinese keys).

    Args:
        lunar_birthday (Lunar): Lunar calendar object

    Returns:
        dict: BaZi pillars with 天干 (Heavenly Stems) and 地支 (Earthly Branches)
    """
    # Get the EightChar object
    bazi = lunar_birthday.getEightChar()

    # Extract individual stems and branches using EightChar methods
    year_stem = bazi.getYearGan()
    year_branch = bazi.getYearZhi()
    month_stem = bazi.getMonthGan()
    month_branch = bazi.getMonthZhi()
    day_stem = bazi.getDayGan()
    day_branch = bazi.getDayZhi()
    hour_stem = bazi.getTimeGan()
    hour_branch = bazi.getTimeZhi()

    return {
        "八字": {
            "年柱": {
                "天干": year_stem,
                "地支": year_branch,
            },
            "月柱": {
                "天干": month_stem,
                "地支": month_branch,
            },
            "日柱": {
                "天干": day_stem,
                "地支": day_branch,
            },
            "时柱": {
                "天干": hour_stem,
                "地支": hour_branch,
            },
        }
    }


# --- EXECUTION ---

if __name__ == "__main__":
    import json

    # python -m src.astronomer_calculations.bazi_pillars

    # Desmond's birthday example
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    tst_birthday, _ = get_true_solar_time(
        datetime_birthday, 1.3253, 103.808053
    )  # Get true solar time

    print("阳历生日: " + solar_birthday.toYmdHms())
    print("真太阳时生日: " + tst_birthday.toYmdHms())

    lunar_birthday = tst_birthday.getLunar()  # Convert to lunar calendar

    # Get BaZi pillars in LLM-ready JSON format
    result = get_bazi_pillars(lunar_birthday)

    print(f"\n--- JSON Output for LLM ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))
