"""
Na Yin (纳音) Five Elements Module

This module calculates the Na Yin (纳音) Five Elements for each pillar in a BaZi chart.
Na Yin represents the Five Elements (五行) associated with each Heavenly Stem and Earthly Branch pair:
- 木 (Wood)
- 火 (Fire)
- 土 (Earth)
- 金 (Metal)
- 水 (Water)
"""

from lunar_python import Lunar


def get_na_yin(lunar_birthday: Lunar) -> dict:
    """
    Extract Na Yin (纳音) Five Elements for each pillar (Year, Month, Day, Hour).

    Args:
        lunar_birthday (Lunar): Lunar calendar object

    Returns:
        dict: Na Yin Five Elements organized by pillar in Chinese:
        {
            "纳音": {
                "年": "...",
                "月": "...",
                "日": "...",
                "时": "..."
            }
        }
    """
    # Get the EightChar object
    bazi = lunar_birthday.getEightChar()

    # Extract Na Yin (纳音) for each pillar
    year_na_yin = bazi.getYearNaYin()
    month_na_yin = bazi.getMonthNaYin()
    day_na_yin = bazi.getDayNaYin()
    time_na_yin = bazi.getTimeNaYin()

    return {
        "纳音": {
            "年": year_na_yin,
            "月": month_na_yin,
            "日": day_na_yin,
            "时": time_na_yin,
        }
    }


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from datetime import datetime
    from lunar_python import Solar
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time

    # python -m src.astronomer_calculations.na_yin

    # Desmond's birthday example
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    tst_birthday, _ = get_true_solar_time(
        datetime_birthday, 1.3253, 103.808053
    )  # Get true solar time

    print("阳历生日: " + solar_birthday.toYmdHms())
    print("真太阳时生日: " + tst_birthday.toYmdHms())

    lunar_birthday = tst_birthday.getLunar()  # Convert to lunar calendar

    # Get Na Yin in LLM-ready JSON format
    result = get_na_yin(lunar_birthday)

    print(f"\n--- JSON Output for LLM ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))
