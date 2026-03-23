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
from src.astronomer_calculations.cycle_wu_xing import CycleWuXingDynamics
from src.astronomer_calculations.cycle_interactions import get_cycle_interactions
from src.astronomer_calculations.day_master import get_day_master
from src.astronomer_calculations.cycle_shen_sha import get_cycle_shen_sha
from src.astronomer_calculations.void_xun_kong import get_xun_kong
# Local pillar names
pillar_names = ["年柱", "月柱", "日柱", "时柱"]

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

    # Compute natal xun kong internally
    natal_xk = get_xun_kong(lunar_birthday).get("旬空", {})

    # Day master strength — used to contextualise 开库 墓库境况
    day_strength = get_day_master(lunar_birthday).get("日主", {}).get("强弱", "中和")

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
    da_yun_list = yun.getDaYun()

    # Get Xiao Yun array from the first Da Yun object using lunar-python's built-in method
    xiao_yun_array = da_yun_list[0].getXiaoYun()

    # Process each 小运 (year) from birth to 起运
    xiao_yun_data = []

    for i, xiao_yun in enumerate(xiao_yun_array):
        # Get data from the Xiao Yun object (lunar-python library methods)
        gan_zhi = xiao_yun.getGanZhi()
        calendar_year = xiao_yun.getYear()
        age = xiao_yun.getAge()

        if gan_zhi == "Unknown" or len(gan_zhi) < 2:
            continue

        # Stop including 小运 cycles once we've passed the 起运年份 (inclusive)
        # We want to include cycles UP TO and INCLUDING the 起运 year
        if calendar_year > qiyun_calendar_year:
            break

        xiao_yun_stem = gan_zhi[0]
        xiao_yun_branch = gan_zhi[1]

        cycle_xk_str = xiao_yun.getXunKong()
        # Detect interactions (作用) with birth chart using 1x4 scan
        cycle_interactions_result = get_cycle_interactions(
            xiao_yun_stem, xiao_yun_branch, birth_chart, cycle_label="小运",
            cycle_xk_str=cycle_xk_str,
            natal_xk=natal_xk,
            day_strength=day_strength,
        )
        cycle_interactions = cycle_interactions_result.get("作用", [])

        # Five Elements dynamics: enriched cycle pillar info + combined natal+cycle 五行力量
        cycle_wu_xing_info = CycleWuXingDynamics().calculate_cycle_interaction(
            xiao_yun, lunar_birthday,
            priority_list=cycle_interactions_result.get("_raw_priority_list", []),
            cycle_type="小运",
            xun_kong_data=natal_xk,
            cycle_xk_str=cycle_xk_str,
        )
        cycle_pillar_info = cycle_wu_xing_info.pop("小运柱", {})
        cycle_wu_xing_result = cycle_wu_xing_info.get("五行力量分析", "无数据")

        # Extract Shen Sha (神煞) for this cycle
        cycle_shen_sha = get_cycle_shen_sha(xiao_yun_stem, xiao_yun_branch, birth_chart, gender)

        xiao_yun_info = {
            # "序号": i + 1,  # 1-based sequence number
            "日历年份": calendar_year,  # Calendar year
            "年龄": age,  # Age at start of year (from library)
            "运柱": cycle_pillar_info,  # Enriched cycle pillar: 五行, 十神, 通根, 藏干, 季节状态, 地势, 纳音, 旬, 旬空
            "五行力量": cycle_wu_xing_result,  # Combined natal+cycle 五行力量分析
            "神煞": cycle_shen_sha,  # Shen Sha stars for this cycle
            "作用": cycle_interactions,  # Branch and Stem interactions with birth chart
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
    from src.utils.logging import configure_logging, get_logger

    # Configure logging system (creates logs in logs/YYYY-MM-DD/HH-MM-SS/app.log)
    configure_logging()
    logger = get_logger(__name__)

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

    bazi_json = get_bazi_pillars(tst_birthday.getLunar())
    logger.info(f"八字: {bazi_json}")

    # logger.info("=== Xiao Yun (Female, Gender=0) ===")
    # result = get_xiao_yun(lunar_birthday, gender=0)
    # logger.info(json.dumps(result, ensure_ascii=False, indent=2))

    logger.info("=== Xiao Yun (Male, Gender=1) ===")
    result = get_xiao_yun(lunar_birthday, gender=1)
    logger.info(json.dumps(result, ensure_ascii=False, indent=2))
