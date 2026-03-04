"""
Embryonic Breath (胎息) Calculation Module

This module calculates the Embryonic Breath (胎息) for BaZi charts.

Core Concepts:
    - 胎息 (Tai Xi - Embryonic Breath): An esoteric concept in BaZi that represents
      the subtle energetic state at conception/gestation

    Key Information:
    - Derived from the Day Stem and Day Branch (日柱)
    - Uses the harmonies (五合) and hexagrams (六合) systems
    - Related to fetal astrology and early life influences
    - Complementary to 胎元 (Tai Yuan - Conception Palace)

    The Embryonic Breath contains:
    - 干支 (Gan Zhi): The Heavenly Stem and Earthly Branch combination
    - 纳音 (Na Yin): Five Elements classification representing elemental energy

    Distinguished from 胎元 (Tai Yuan):
    - Tai Xi uses harmonized stems and branches (HE_GAN, HE_ZHI)
    - Tai Yuan uses direct calculations from month and hour pillars
    - Tai Xi is more subtle and relates to inner energetic state
    - Tai Yuan is more concrete and relates to conception timing

Professional Applications:
    - Understanding fetal health and early childhood development
    - Determining prenatal influences and inherited conditions
    - Assessing mother-child relationship karma
    - Timing of early life transformations
"""

from lunar_python import Lunar


def get_tai_xi(lunar_birthday: Lunar) -> dict:
    """
    Extract Embryonic Breath (胎息) for a given lunar birthday.

    Calculates the Embryonic Breath along with its Na Yin (Five Elements)
    classification using the harmonized stems and branches.

    Args:
        lunar_birthday: Lunar object from lunar_python library

    Returns:
        Dictionary with embryonic breath data in professional BaZi format:
        {
            "胎息": {
                "干支": "...",
                "纳音": "..."
            }
        }
    """

    baZi = lunar_birthday.getEightChar()

    # Extract Embryonic Breath and its na yin
    tai_xi = baZi.getTaiXi()
    tai_xi_na_yin = baZi.getTaiXiNaYin()

    # Build structured result
    result = {
        "胎息": {
            "干支": tai_xi,
            "纳音": tai_xi_na_yin,
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

    # python -m src.astronomer_calculations.embryonic_breath_tai_xi

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
    result = get_tai_xi(lunar_birthday)

    # Print JSON output
    print("\n```json")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("```\n")
