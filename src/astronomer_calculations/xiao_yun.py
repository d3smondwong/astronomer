"""
Xiao Yun (小运 - Small Luck Cycles) Calculation Module

This module calculates the Small Luck Cycles (Xiao Yun) for a given lunar birthday and gender.
Each Xiao Yun cycle lasts 1 year and represents the annual fortune before 起运 (luck cycle start).

Unlike 大运 (Da Yun - Big Luck Cycles that start after 起运), 小运 covers the pre-luck period
from birth through the year when 起运 begins. This provides annual insight into the formative years
before the major 10-year luck cycles commence.

Structure mirrors 大运:
1. 序号 (Sequence Number): Annual index from birth
2. 干支 (Heavenly Stem & Earthly Branch): Year's sexagenary pair
3. 旬/旬空 (Sexagenary Cycle & Void Days): Based on stem-branch pair
4. 五行 (Five Elements): Year stem and branch elements with polarity (阳/阴)
5. 纳音 (Nayin - Harmonic Resonance Element): Descriptive element for stem-branch pair
6. 地势 (Life Stage): 12-stage positional strength from 长生十二宫 system
7. 十神 (Ten Gods): Primary theme (Year Stem) + Hidden themes (Hidden Stems in Branch)
8. 作用 (Interactions): Branch and Stem interactions with birth chart using 1×4 scan
   Detects 16 interaction types across tiers 0-14 (Tiers 0-14):
   - Tier 0-3: Structural harmonies (三会, 三合, 六冲, 六合)
   - Tier 4-10: Dynamics (共拱, 比和, 拱会, 残会, 半合, 天干合, 天干克, 天干冲)
   - Tier 11-14: Details (三刑, 六害, 六破, 暗合)

   All branch-pair interactions include 紧贴 (adjacency) field for distance semantics:
   - 紧贴: true = Adjacent pillars (正X) → Full-force status
   - 紧贴: false = Distant pillars (遥X) → Attenuated status

   Includes 开库 sub-type for 六冲 with Earth tomb pairs (辰↔戌, 丑↔未)

Key Function:
    get_xiao_yun(lunar_birthday, gender): Calculates annual Small Luck Cycles analysis.

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male

    Returns:
        dict: Comprehensive Xiao Yun analysis in JSON format with:
        - 小运 metadata: birth date, 起运 timing, gender, cycle count
        - 小运周期: array of N annual cycles, each containing:
            * 序号: annual index (1-based)
            * 干支: year stem-branch pair
            * 旬/旬空: sexagenary and void information
            * 五行: year stem and branch five elements with polarity
            * 纳音: nayin descriptive element name
            * 地势: life stage
            * 十神: primary theme + hidden stem analysis
            * 作用: all detected interactions with birth chart (16 types, tiers 0-14)
            * Calendar year and age data

Output Format:
    All dictionary keys and values use Chinese characters for consistency.
    Integrates lunar-python library data for accuracy and reliability.
    Interactions include 紧贴 field for distance semantics (adjacent vs distant).
    Interactions are actionable event alerts for each annual period.
"""

from lunar_python import Lunar, Solar
from lunar_python.util import LunarUtil
from lunar_python.EightChar import EightChar
from datetime import datetime

# Import shared maps, functions, and constants from da_yun module
from src.astronomer_calculations.da_yun import (
    # Interaction maps
    clash_map,
    harm_map,
    six_he_map,
    triple_he,
    cardinal_branches,
    directional_he,
    break_map,
    hidden_stem_he,
    stem_combines,
    stem_clashes,
    pillar_names,
    # Helper functions
    _get_stem_wu_xing,
    _get_branch_wu_xing,
    _get_nayin,
    _get_di_shi,
    _get_shi_shen_for_stem_pair,
    _get_hidden_stems_shi_shen,
    _detect_da_yun_interactions,
    _detect_global_triple_combinations,
    DI_SHI_TABLE,
    STR_STEM,
    STR_BRANCH,
)

from src.astronomer_calculations.wu_xing import (
    Pillar,
    Stem,
    Branch,
)


# ============================================================================
# SEXAGENARY PROGRESSION (干支循环) - Year Index to Stem-Branch Mapping
# ============================================================================


def _get_xun_and_xun_kong_from_object(xiao_yun_obj) -> tuple:
    """
    Get Xun (旬) and Xun Kong (旬空) from a Xiao Yun object.

    Args:
        xiao_yun_obj: Xiao Yun object from lunar-python library

    Returns:
        tuple: (xun_name: str, xun_kong_pair: str)
    """
    try:
        xun = xiao_yun_obj.getXun() if hasattr(xiao_yun_obj, "getXun") else "Unknown"
        xun_kong = (
            xiao_yun_obj.getXunKong()
            if hasattr(xiao_yun_obj, "getXunKong")
            else "Unknown"
        )
        return (xun, xun_kong)
    except Exception:
        return ("Unknown", "Unknown")


# ============================================================================
# XIAO YUN INTERACTIONS - Adapted from Da Yun Logic
# ============================================================================


def _detect_xiao_yun_interactions(
    xiao_yun_stem: str, xiao_yun_branch: str, birth_chart: dict
) -> dict:
    """
    Detect Xiao Yun interactions with birth chart using same 1×4 scan as Da Yun.

    The Xiao Yun pillar (annual cycle) acts as an External Trigger entering the birth chart system.
    Uses the same Tier-based priority checks (16 interaction types, tiers 0-14) and Key vs Lock logic for 开库 scenarios.

    Comprehensive interaction types detected:
    - Structural: 三会, 三合, 六冲, 六合
    - Dynamics: 共拱, 比和, 拱会, 残会, 半合, 天干合, 天干克, 天干冲
    - Details: 三刑, 六害, 六破, 暗合

    All branch-pair interactions include 紧贴 field:
    - 紧贴: true = adjacent pillars (正X, full-force)
    - 紧贴: false = distant pillars (遥X, attenuated)

    Args:
        xiao_yun_stem (str): Xiao Yun heavenly stem (year stem)
        xiao_yun_branch (str): Xiao Yun earthly branch (year branch)
        birth_chart (dict): Birth chart with keys "year", "month", "day", "hour"

    Returns:
        dict: Organized interactions by pillar and tier
    """
    # Leverage the existing Da Yun interaction detection function
    # Pass "小运" as pillar_prefix to replace "大运" in the output
    return _detect_da_yun_interactions(
        xiao_yun_stem, xiao_yun_branch, birth_chart, pillar_prefix="小运"
    )


# ============================================================================
# MAIN XIAO YUN CALCULATION
# ============================================================================


def get_xiao_yun(lunar_birthday: Lunar, gender: int) -> dict:
    """
    Calculate Small Luck Cycles (Xiao Yun) from lunar birthday and gender.

    Calculates annual cycles from birth through the year 起运 (luck cycle start) begins.

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male

    Returns:
        dict: Structured JSON with Xiao Yun cycles and timing information
    """
    # Get the EightChar (八字) object
    bazi = lunar_birthday.getEightChar()

    # Get the Day Stem (日干) - this is the reference for all Ten Gods calculations
    day_stem = bazi.getDayGan()

    # Extract birth chart pillars for interaction detection
    birth_chart = {
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

    # Calculate 起运 (start of luck cycle) based on gender
    yun = bazi.getYun(gender)
    qi_yun_date = yun.getStartSolar()
    qi_yun_start_year = yun.getStartYear()
    qiyun_calendar_year = (
        qi_yun_date.getYear()
    )  # Get the actual calendar year when 起运 occurs

    # Get all Da Yun cycles and extract Xiao Yun from the first one
    # Xiao Yun cycles represent the years from birth until 起运 (inclusive)
    da_yun_array = yun.getDaYun()

    if not da_yun_array or len(da_yun_array) == 0:
        # No Da Yun data, return empty result
        return {
            "小运": {
                "起运前": {
                    "性别": "男" if gender == 1 else "女",
                    "阳历生日": lunar_birthday.getSolar().toYmdHms(),
                    "农历生日": f"{lunar_birthday.getYear()}-{lunar_birthday.getMonth():02d}-{lunar_birthday.getDay():02d} {lunar_birthday.getHour():02d}:{lunar_birthday.getMinute():02d}:{lunar_birthday.getSecond():02d}",
                    "起运时间": qi_yun_date.toYmdHms(),
                    "起运年份": qi_yun_start_year,
                    "顺逆": "顺推" if yun.isForward() else "逆推",
                    "小运周期数": 0,
                },
                "小运周期": [],
            }
        }

    # Get Xiao Yun array from the first Da Yun object using lunar-python's built-in method
    xiao_yun_array = da_yun_array[0].getXiaoYun()

    # Process each 小运 (year) from birth to 起运
    xiao_yun_data = []

    for i, xiao_yun_obj in enumerate(xiao_yun_array):
        # Get data from the Xiao Yun object (lunar-python library methods)
        gan_zhi = xiao_yun_obj.getGanZhi()
        calendar_year = xiao_yun_obj.getYear()
        age = xiao_yun_obj.getAge()

        if gan_zhi == "Unknown" or len(gan_zhi) < 2:
            continue

        # Stop including 小运 cycles once we've passed the 起运年份 (inclusive)
        # We want to include cycles UP TO and INCLUDING the 起运 year
        if calendar_year > qiyun_calendar_year:
            break

        xiao_yun_stem = gan_zhi[0]
        xiao_yun_branch = gan_zhi[1]

        # Calculate Ten Gods for this 小运
        # Stem Ten God (天干十神) - the primary life theme for this year
        stem_shi_shen = _get_shi_shen_for_stem_pair(day_stem, xiao_yun_stem)

        # Branch Ten Gods (地支十神) - hidden themes from hidden stems
        branch_shi_shen = _get_hidden_stems_shi_shen(day_stem, xiao_yun_branch)

        # Life Stage (地势) for the Xiao Yun branch using birth day stem as reference
        di_shi = _get_di_shi(day_stem, xiao_yun_branch)

        # Five Elements (五行) for Stem and Branch
        stem_wu_xing = _get_stem_wu_xing(xiao_yun_stem)
        branch_wu_xing = _get_branch_wu_xing(xiao_yun_branch)

        # Nayin (纳音) for the Xiao Yun stem-branch pair
        nayin = _get_nayin(xiao_yun_stem, xiao_yun_branch)

        # Get Xun (旬) and Xun Kong (旬空) from the Xiao Yun object
        xun, xun_kong = _get_xun_and_xun_kong_from_object(xiao_yun_obj)

        # Detect interactions (作用) with birth chart using 1x4 scan
        interactions_result = _detect_xiao_yun_interactions(
            xiao_yun_stem, xiao_yun_branch, birth_chart
        )
        interactions = interactions_result.get("作用", [])

        xiao_yun_info = {
            "序号": i + 1,  # 1-based sequence number
            "干支": gan_zhi,  # Gan-Zhi (stem-branch pair)
            "旬": xun,  # Xun (10-day cycle)
            "旬空": xun_kong,  # Xun Kong (void periods)
            "五行": {
                "干": stem_wu_xing,  # Stem Five Element and Polarity
                "支": branch_wu_xing,  # Branch Five Element and Polarity
            },
            "纳音": nayin,  # Nayin element (harmonic resonance)
            "地势": di_shi,  # Life Stage (长生十二神)
            "十神": {
                "主题": stem_shi_shen,  # Primary life theme (Year Stem Ten God)
                "天干十神": stem_shi_shen,  # Year Stem Ten God (for clarity)
                "地支十神": branch_shi_shen,  # Hidden themes (Main/Middle/Residual)
            },
            "作用": interactions,  # Branch and Stem interactions with birth chart
            "日历年份": calendar_year,  # Calendar year
            "年龄": age,  # Age at start of year (from library)
        }
        xiao_yun_data.append(xiao_yun_info)

    # Compile the complete xiao_yun structure
    return {
        "小运": {
            "起运前": {
                "性别": "男" if gender == 1 else "女",
                "出生阳历": lunar_birthday.getSolar().toYmdHms(),
                "出生农历": f"{lunar_birthday.getYear()}-{lunar_birthday.getMonth():02d}-{lunar_birthday.getDay():02d} {lunar_birthday.getHour():02d}:{lunar_birthday.getMinute():02d}:{lunar_birthday.getSecond():02d}",
                "起运时间": qi_yun_date.toYmdHms(),
                "起运年份": qi_yun_start_year,
                "顺逆": "顺推" if yun.isForward() else "逆推",
                "小运周期数": len(xiao_yun_data),
            },
            "小运周期": xiao_yun_data,
        }
    }


# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    import json
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
    from src.astronomer_calculations.bazi_pillars import get_bazi_pillars

    # python -m src.astronomer_calculations.xiao_yun

    # Desmond's birthday example - Female test
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)
    tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)

    # Corinne's birthday example
    # solar_birthday = Solar.fromYmdHms(1987, 6, 3, 12, 6, 0)
    # tst_birthday, inputs_report = get_true_solar_time(
    #     datetime(1987, 6, 3, 12, 6, 0), 1.4759, 103.808053
    # )
    # lunar_birthday = tst_birthday.getLunar()

    # Lara's birthday example
    # solar_birthday = Solar.fromYmdHms(2025, 7, 31, 9, 10, 0)
    # tst_birthday, inputs_report = get_true_solar_time(
    #     datetime(2025, 7, 31, 9, 10, 0), 1.4759, 103.808053
    # )
    lunar_birthday = tst_birthday.getLunar()

    print("八字")
    bazi_json = get_bazi_pillars(tst_birthday.getLunar())
    print(f"八字: {bazi_json}")

    # print("\n=== Xiao Yun (Female, Gender=0) ===")
    # result = get_xiao_yun(lunar_birthday, gender=0)
    # print(json.dumps(result, ensure_ascii=False, indent=2))

    # print("\n=== Xiao Yun (Male, Gender=1) ===")
    result = get_xiao_yun(lunar_birthday, gender=1)
    print(json.dumps(result, ensure_ascii=False, indent=2))
