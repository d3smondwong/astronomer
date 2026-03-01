"""
Ten Gods Shi Shen (十神) Calculation Module

This module calculates the Ten Gods (十神) for each pillar in a BaZi chart.
The Ten Gods represent the relationships between the Day Stem (日干) and other stems:
- 比肩 (Bi Jian): Competitor
- 劫财 (Jie Cai): Robber of Wealth
- 食神 (Shi Shen): Eating God
- 伤官 (Shang Guan): Hurting Officer
- 偏财 (Pian Cai): Indirect Wealth
- 正财 (Zheng Cai): Direct Wealth
- 偏官 (Pian Guan): Indirect Officer
- 正官 (Zheng Guan): Direct Officer
- 偏印 (Pian Yin): Indirect Resource
- 正印 (Zheng Yin): Direct Resource
"""

from lunar_python import Lunar


def get_shi_shen(lunar_birthday: Lunar) -> dict:
    """
    Extract Ten Gods (十神) for each pillar (Year, Month, Day, Hour).

    Args:
        lunar_birthday (Lunar): Lunar calendar object

    Returns:
        dict: Ten Gods organized by pillar in Chinese with 天干十神:
        {
            "十神": {
                "年干十神": "...",
                "月干十神": "...",
                "日干十神": "...",
                "时干十神": "..."
            }
        }
    """
    # Get the EightChar object
    bazi = lunar_birthday.getEightChar()

    # Extract Shi Shen for each pillar stem
    year_shi_shen = bazi.getYearShiShenGan()
    month_shi_shen = bazi.getMonthShiShenGan()
    day_shi_shen = bazi.getDayShiShenGan()
    time_shi_shen = bazi.getTimeShiShenGan()

    return {
        "十神": {
            "年干十神": year_shi_shen,
            "月干十神": month_shi_shen,
            "日干十神": day_shi_shen,
            "时干十神": time_shi_shen,
        }
    }


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from datetime import datetime
    from lunar_python import Solar
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time

    # python -m src.astronomer_calculations.ten_gods_shi_shen

    # Desmond's birthday example
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    tst_birthday, _ = get_true_solar_time(
        datetime_birthday, 1.3253, 103.808053
    )  # Get true solar time

    print("阳历生日: " + solar_birthday.toYmdHms())
    print("真太阳时生日: " + tst_birthday.toYmdHms())

    lunar_birthday = tst_birthday.getLunar()  # Convert to lunar calendar

    # Get Shi Shen in LLM-ready JSON format
    result = get_shi_shen(lunar_birthday)

    print(f"\n--- Ten Gods (十神) ---")
    print(f"年干十神: {result['十神']['年干十神']}")
    print(f"月干十神: {result['十神']['月干十神']}")
    print(f"日干十神: {result['十神']['日干十神']}")
    print(f"时干十神: {result['十神']['时干十神']}")

    print(f"\n--- JSON Output for LLM ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))
