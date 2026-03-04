"""
Three Palaces (三垣) Calculation Module

This module calculates the Three Palaces (三垣) for BaZi charts.

Core Concepts:
    - 三垣 (San Yuan): Three Palaces representing key life areas

    The Three Palaces are:
    1. 胎元 (Tai Yuan - Conception Palace): Represents one's conception and gestation
       - Derived from month pillar and hour pillar
       - Used for fortune during early childhood and family influence
       - Shows ancestral karma and inherited destiny

    2. 命宫 (Ming Gong - Life Palace): Represents one's overall life destiny
       - Derived from the hour pillar
       - Most important palace in Four Pillars system
       - Shows personality, career path, and major life direction

    3. 身宫 (Shen Gong - Body/Action Palace): Represents one's immediate circumstances
       - Derived from day pillar
       - Shows physical health and day-to-day experiences
       - Reflects how destiny is actively manifested

Each palace has:
    - 干支 (Gan Zhi): Heavenly Stem and Earthly Branch combination
    - 纳音 (Na Yin): Five Elements classification of the palace

Professional Applications:
    - Timing of significant life events
    - Determining favorable periods for major decisions
    - Assessing family legacy and childhood influences
    - Understanding physical health and vitality
"""

from lunar_python import Lunar


def get_san_yuan(lunar_birthday: Lunar):
    """
    Extract Three Palaces (三垣) for a given lunar birthday.

    Calculates the Conception, Life, and Body Palaces along with their
    Na Yin (Five Elements) classifications.

    Args:
        lunar_birthday: Lunar object from lunar_python library

    Returns:
        Dictionary with three palaces data in professional BaZi format:
        {
            "三垣": {
                "胎元": {"干支": "...", "纳音": "..."},
                "命宫": {"干支": "...", "纳音": "..."},
                "身宫": {"干支": "...", "纳音": "..."}
            }
        }
    """

    baZi = lunar_birthday.getEightChar()

    # Extract three palaces and their na yin
    tai_yuan = baZi.getTaiYuan()
    tai_yuan_na_yin = baZi.getTaiYuanNaYin()

    ming_gong = baZi.getMingGong()
    ming_gong_na_yin = baZi.getMingGongNaYin()

    shen_gong = baZi.getShenGong()
    shen_gong_na_yin = baZi.getShenGongNaYin()

    # Build structured result
    result = {
        "三垣": {
            "胎元": {
                "干支": tai_yuan,
                "纳音": tai_yuan_na_yin,
            },
            "命宫": {
                "干支": ming_gong,
                "纳音": ming_gong_na_yin,
            },
            "身宫": {
                "干支": shen_gong,
                "纳音": shen_gong_na_yin,
            },
        }
    }

    return result


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from src.astronomer_calculations.bazi_pillars import get_bazi_pillars
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
    from datetime import datetime
    from lunar_python import Solar

    # python -m src.astronomer_calculations.three_palace_san_yuan

    # Desmond's birthday example
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)

    # Sample birthday example
    # solar_birthday = Solar.fromYmdHms(1990, 1, 30, 4, 0, 0)
    # datetime_birthday = datetime(1990, 1, 30, 4, 0, 0)
    # tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)

    print("=" * 60)
    print("阳历生日: " + solar_birthday.toYmdHms())
    print("真太阳时生日: " + tst_birthday.toYmdHms())
    print("=" * 60)

    print("")
    print("八字")
    bazi_json = get_bazi_pillars(tst_birthday.getLunar())
    print(f"八字: {bazi_json}")

    lunar_birthday = tst_birthday.getLunar()
    result = get_san_yuan(lunar_birthday)

    # Print JSON output
    print("\n```json")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("```\n")
