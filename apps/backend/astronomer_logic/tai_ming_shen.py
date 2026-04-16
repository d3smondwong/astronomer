"""
Three Palaces (胎命身) Calculation Module

This module calculates the Three Palaces (胎命身) for BaZi charts.

Core Concepts:
    - 胎命身 (Tai Ming Shen): Three Palaces representing key life areas

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
    Extract Three Palaces (胎命身) for a given lunar birthday.

    Calculates the Conception, Life, and Body Palaces along with their
    Na Yin (Five Elements) classifications.

    Args:
        lunar_birthday: Lunar object from lunar_python library

    Returns:
        Dictionary with three palaces data in professional BaZi format:
        {
            "胎命身": {
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
        "胎命身": {
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


