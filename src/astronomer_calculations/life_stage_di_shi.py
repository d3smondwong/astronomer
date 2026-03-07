"""
Di Shi (地势) Earthly Position Module. Also known as 12 Life Stages (十二长生)

This module calculates the Di Shi (地势) Earthly Position/Situation for each pillar in a BaZi chart.
Di Shi represents the earthly position and strength of each pillar in the BaZi configuration.
"""

from lunar_python import Lunar


def get_di_shi(lunar_birthday: Lunar) -> dict:
    """
    Extract Di Shi (地势) Earthly Position for each pillar (Year, Month, Day, Hour).

    Args:
        lunar_birthday (Lunar): Lunar calendar object

    Returns:
        dict: Di Shi Earthly Position organized by pillar in Chinese:
        {
            "地势": {
                "年柱": "...",
                "月柱": "...",
                "日柱": "...",
                "时柱": "..."
            }
        }
    """
    # Get the EightChar object
    bazi = lunar_birthday.getEightChar()

    # Extract Di Shi (地势) for each pillar
    year_di_shi = bazi.getYearDiShi()
    month_di_shi = bazi.getMonthDiShi()
    day_di_shi = bazi.getDayDiShi()
    time_di_shi = bazi.getTimeDiShi()

    return {
        "地势": {
            "年柱": year_di_shi,
            "月柱": month_di_shi,
            "日柱": day_di_shi,
            "时柱": time_di_shi,
        }
    }


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from datetime import datetime
    from lunar_python import Solar
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time

    # python -m src.astronomer_calculations.12_life_stage_di_shi

    # Desmond's birthday example
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    tst_birthday, _ = get_true_solar_time(
        datetime_birthday, 1.3253, 103.808053
    )  # Get true solar time

    print("阳历生日: " + solar_birthday.toYmdHms())
    print("真太阳时生日: " + tst_birthday.toYmdHms())

    lunar_birthday = tst_birthday.getLunar()  # Convert to lunar calendar

    # Get Di Shi in LLM-ready JSON format
    result = get_di_shi(lunar_birthday)

    print(f"\n--- JSON Output for LLM ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))
