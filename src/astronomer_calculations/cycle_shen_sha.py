"""
Cycle Shen Sha (神煞) Calculation Module

This module calculates Shen Sha stars for cycle pillars (Da Yun, Xiao Yun, Liu Nian, Liu Yue).
It delegates to the ShenShaCalculator class to maintain shared lookup logic.

Key Functions:
    get_cycle_shen_sha(cycle_stem, cycle_branch, natal_chart, gender):
        Compute categorized shen sha for a single cycle pillar against the natal chart.
        Returns: {"日系": [...], "年系": [...], "月系": [...], "杂项": [...]}
"""

from src.astronomer_calculations.shen_sha import ShenShaCalculator


def get_cycle_shen_sha(cycle_stem: str, cycle_branch: str, natal_chart: dict, gender: int) -> dict:
    """
    Compute shen sha stars for a single cycle pillar.

    Delegates to ShenShaCalculator.get_cycle_shen_sha() to reuse lookup logic
    and avoid code duplication.

    Args:
        cycle_stem (str): Cycle pillar stem (e.g., "甲")
        cycle_branch (str): Cycle pillar branch (e.g., "寅")
        natal_chart (dict): Native birth chart structure:
            {
                "year": {"stem": str, "branch": str},
                "month": {"stem": str, "branch": str},
                "day": {"stem": str, "branch": str},
                "hour": {"stem": str, "branch": str},
            }
        gender (int): 0 for Female, 1 for Male

    Returns:
        dict: {
            "日系": [...],   # Day-branch/stem derived stars
            "年系": [...],   # Year-branch derived stars
            "月系": [...],   # Month-branch & virtue stars
            "杂项": [...],   # Pillar, seasonal, void stars
        }
    """
    # Construct calculator from pre-parsed natal_chart dict
    calculator = ShenShaCalculator._from_natal_dict(natal_chart, gender)

    # Compute and return categorized cycle shens
    return calculator.get_cycle_shen_sha(cycle_stem, cycle_branch)

# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    from src.utils.logging import configure_logging, get_logger
    from src.astronomer_calculations.bazi_pillars import get_bazi_pillars
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
    from lunar_python import Solar
    from datetime import datetime
    import json

    # python -m src.astronomer_calculations.cycle_shen_sha

    # Initialize logging
    logger = configure_logging()
    log = get_logger(__name__)

    # Example: Desmond's birth chart (1985-11-25, 17:07)
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)
    tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)

    log.info("=" * 60)
    log.info("阳历生日: " + solar_birthday.toYmdHms())
    log.info("真太阳时生日: " + tst_birthday.toYmdHms())
    log.info("=" * 60)

    lunar_birthday = tst_birthday.getLunar()

    # Get the EightChar (八字) object
    bazi = lunar_birthday.getEightChar()

    # Extract natal chart pillars for interaction detection
    natal_chart = {
        "year": {
            "stem": bazi.getYearGan(),
            "branch": bazi.getYearZhi(),
        },
        "month": {
            "stem": bazi.getMonthGan(),
            "branch": bazi.getMonthZhi(),
        },
        "day": {
            "stem": bazi.getDayGan(),
            "branch": bazi.getDayZhi(),
        },
        "hour": {
            "stem": bazi.getTimeGan(),
            "branch": bazi.getTimeZhi(),
        },
    }

    bazi_json = get_bazi_pillars(tst_birthday.getLunar())
    logger.info(f"八字: {bazi_json}")

    # Test cycle shens
    log.info("\n[Da Yun Test - 甲子 cycle]")
    cycle_result = get_cycle_shen_sha("甲", "子", natal_chart, gender=1)
    log.info(json.dumps(cycle_result, ensure_ascii=False, indent=2))