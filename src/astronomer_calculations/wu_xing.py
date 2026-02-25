"""
Wu Xing (五行) - Five Elements Calculation Module

This module extracts and analyzes the Five Elements (Wu Xing) composition from a BaZi chart.
The Five Elements (Wood, Fire, Earth, Metal, Water) are fundamental to Chinese metaphysics
and represent the balance of energies across the Four Pillars.

Each pillar contains two Wu Xing components:
- 天干五行 (Heavenly Stem Element): Represents the outward, active energy
- 地支五行 (Earthly Branch Element): Represents the hidden, passive energy

Key Function:
    get_wu_xing(lunar_birthday): Extracts Wu Xing composition for each pillar.

    Returns:
        dict: Structured JSON with Five Elements data organized by pillar:
        {
            "五行": {
                "年柱五行": {"天干五行": "...", "地支五行": "..."},
                "月柱五行": {"天干五行": "...", "地支五行": "..."},
                "日柱五行": {"天干五行": "...", "地支五行": "..."},
                "时柱五行": {"天干五行": "...", "地支五行": "..."}
            }
        }

The Five Elements:
- 木 (Wood): Growth, expansion, flexibility
- 火 (Fire): Passion, activity, transformation
- 土 (Earth): Stability, nurture, balance
- 金 (Metal): Strength, discipline, precision
- 水 (Water): Flow, wisdom, flexibility

This data is LLM-ready and can be fed directly to language models for interpretation.
"""

from lunar_python import Lunar
from datetime import datetime
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
    eight_char = lunar_birthday.getEightChar()

    # Extract Five Elements (Wu Xing) for each pillar
    # Each pillar's Wu Xing is a string like "木土" (stem element + branch element)
    year_wu_xing = eight_char.getYearWuXing()
    month_wu_xing = eight_char.getMonthWuXing()
    day_wu_xing = eight_char.getDayWuXing()
    hour_wu_xing = eight_char.getTimeWuXing()

    return {
        "五行": {
            "年柱五行": parse_wu_xing(year_wu_xing),
            "月柱五行": parse_wu_xing(month_wu_xing),
            "日柱五行": parse_wu_xing(day_wu_xing),
            "时柱五行": parse_wu_xing(hour_wu_xing),
        }
    }


# Parse each Wu Xing string into stem and branch elements
def parse_wu_xing(wu_xing_str: str) -> dict:
    """Split Wu Xing string (e.g., '木土') into stem and branch elements"""
    if len(wu_xing_str) >= 2:
        return {"天干五行": wu_xing_str[0], "地支五行": wu_xing_str[1]}
    return {"天干五行": "", "地支五行": ""}


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from lunar_python import Solar

    # python -m src.astronomer_calculations.wu_xin

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
