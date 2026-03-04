"""
Void & Xun Kong (旬空) Calculation Module

This module calculates Xun (旬) and Xun Kong (旬空) for BaZi charts.

Core Concepts:
    - Xun (旬): A 10-day cycle of Heavenly Stems (甲-癸 repeats)
    - Xun Kong (旬空): The two Earthly Branches that are "void" or "empty" during each xun
    - Void branches indicate periods where certain luck or fortune is unavailable

    For example:
    - 甲子旬: Stems are 甲-癸 (day 1-10), Void branches = 戌亥 (not present in cycle)
    - If your pillar falls on a void branch, that luck is suspended

Method Variants Reference:

    **YEAR PILLAR:**
    - getYearXun(): Uses lunar year start (正月初一 - 1st day 1st month)
    - getYearXunByLiChun(): Uses Li Chun day (立春当天 - solar term day boundary)
    - getYearXunExact() ✓ RECOMMENDED: Uses Li Chun exact moment (立春交接时刻)
      → Most astronomically precise; aligns with actual solar term transition

    **MONTH PILLAR:**
    - getMonthXun(): Uses solar term day boundary (节交接当天)
    - getMonthXunExact() ✓ RECOMMENDED: Uses solar term exact moment (节交接时刻)
      → Most precise; triggers at exact astronomical transition time

    **DAY PILLAR:**
    - getDayXun(): Uses solar term day boundary (节交接当天起算)
    - getDayXunExact() ✓ RECOMMENDED: Late Zi hour (23:00-01:00) counts as NEXT day
      → Standard BaZi convention; matches astronomical precision
    - getDayXunExact2(): Late Zi hour counts as SAME day (less common)
      → Older, more traditional method; less precise

    **HOUR PILLAR:**
    - getTimeXun() ✓ RECOMMENDED: Only standard method available
      → Directly uses hour's gan-zhi without astronomical refinements

Professional BaZi Standard:
    Use all "Exact" variants for consistent astronomical precision across all pillars.
    This ensures pillar boundaries align with actual solar term moments, not just
    calendar day changes. For Day pillar, "Exact" includes the critical late Zi hour rule.

Return Format:
    JSON structure with nested pillar data (年柱, 月柱, 日柱, 时柱)
    Each pillar contains:
    - 旬: The xun cycle (e.g., "甲子旬")
    - 旬空: The two void branches (e.g., "戌亥")
"""

from lunar_python import Lunar, Solar


def get_xun_kong(lunar_birthday: Lunar):
    """
    Extract Xun (旬) and Xun Kong (旬空) for all four pillars.

    Xun (旬): A 10-day cycle of stems in the BaZi system
    Xun Kong (旬空): The "void" or "empty" branches during each xun cycle

    Args:
        lunar_birthday: Lunar object from lunar_python library

    Returns:
        Dictionary with xun and xun kong data for year, month, day, and hour pillars
        using professional-grade "Exact" methods for astronomical precision.
    """

    # Extract xun and xun kong for each pillar
    year_xun = lunar_birthday.getYearXunExact()
    year_xun_kong = lunar_birthday.getYearXunKongExact()

    month_xun = lunar_birthday.getMonthXunExact()
    month_xun_kong = lunar_birthday.getMonthXunKongExact()

    day_xun = lunar_birthday.getDayXunExact()
    day_xun_kong = lunar_birthday.getDayXunKongExact()

    hour_xun = lunar_birthday.getTimeXun()
    hour_xun_kong = lunar_birthday.getTimeXunKong()

    # Build structured result
    result = {
        "旬空": {
            "年柱": {
                "旬": year_xun,
                "旬空": year_xun_kong,
            },
            "月柱": {
                "旬": month_xun,
                "旬空": month_xun_kong,
            },
            "日柱": {
                "旬": day_xun,
                "旬空": day_xun_kong,
            },
            "时柱": {
                "旬": hour_xun,
                "旬空": hour_xun_kong,
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

    # python -m src.astronomer_calculations.void_xun_kong

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
    result = get_xun_kong(lunar_birthday)

    # Print JSON output
    print("\n```json")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("```\n")
