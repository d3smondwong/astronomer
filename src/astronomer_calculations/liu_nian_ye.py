"""
Liu Nian & Liu Yue (流年 & 流月 - Annual & Monthly Luck Cycles) Calculation Module

This module calculates the Annual Luck Cycles (Liu Nian) and Monthly Luck Cycles (Liu Yue)
for a given lunar birthday and gender.

Each Liu Nian cycle lasts 1 year and represents annual fortune during a 大运 (Da Yun) period.
Liu Yue cycles last 1 month and represent monthly fortune within each Liu Nian.

Structure mirrors 大运 and 小运:
1. 序号 (Sequence Number): Annual/Monthly index
2. 干支 (Heavenly Stem & Earthly Branch): Year/Month's sexagenary pair
3. 旬/旬空 (Sexagenary Cycle & Void Days): Based on stem-branch pair
4. 五行 (Five Elements): Stem and branch elements with polarity (阳/阴)
5. 纳音 (Nayin - Harmonic Resonance Element): Descriptive element for stem-branch pair
6. 地势 (Life Stage): 12-stage positional strength from 长生十二宫 system
7. 十神 (Ten Gods): Primary theme (Year/Month Stem) + Hidden themes (Hidden Stems in Branch)
8. 作用 (Interactions): Branch and Stem interactions with birth chart (1x4 scan)

Key Functions:
    get_liu_nian(lunar_birthday, gender, start_year=None, num_years=10):
        Calculates Annual Luck Cycles analysis.

    get_liu_yue(lunar_birthday, gender, year_index=0):
        Calculates Monthly Luck Cycles for a specific annual period.

    get_liu_nian_ye(lunar_birthday, gender, start_year=None, num_years=10):
        Calculates complete Liu Nian and Liu Yue combined analysis.

Output Format:
    All dictionary keys and values use Chinese characters for consistency.
    Integrates lunar-python library data for accuracy and reliability.
    Interactions are actionable event alerts for each period.
"""

from lunar_python import Lunar, Solar
from lunar_python.util import LunarUtil
from lunar_python.EightChar import EightChar
from datetime import datetime, timedelta

# Import shared maps, functions, and constants from da_yun module
from src.astronomer_calculations.da_yun import (
    # Helper functions
    _get_stem_wu_xing,
    _get_branch_wu_xing,
    _get_nayin,
    _get_di_shi,
    _get_shi_shen_for_stem_pair,
    _get_hidden_stems_shi_shen,
    _detect_da_yun_interactions,
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
# HELPER FUNCTIONS
# ============================================================================


def _get_current_date_range_liu_nian(reference_date: datetime = None) -> tuple:
    """
    Calculate date range for Liu Nian: 5 years past + 5 years future from reference date.

    Args:
        reference_date (datetime): Reference date (default: today)

    Returns:
        tuple: (start_year, num_years) where num_years = 10 (5 past + 5 future)
    """
    if reference_date is None:
        reference_date = datetime.now()

    current_year = reference_date.year
    start_year = current_year - 5  # 5 years in the past
    num_years = 10  # 5 past + 5 future (current year is year 5)

    return (start_year, num_years)


def _filter_liu_yue_by_date_range(
    liu_yue_array: list, reference_date: datetime = None
) -> list:
    """
    Filter Liu Yue to include past 12 months + next 24 months from reference date.

    Args:
        liu_yue_array (list): Array of Liu Yue cycle data dicts
        reference_date (datetime): Reference date (default: today)

    Returns:
        list: Filtered Liu Yue array
    """
    if reference_date is None:
        reference_date = datetime.now()

    # Calculate date boundaries
    past_12_months = reference_date - timedelta(days=365)
    next_24_months = reference_date + timedelta(days=730)

    # Filter cycles (this is a simple filter; if actual month dates are needed,
    # they would need to be extracted from liu_yue_obj)
    # For now, we'll include all cycles and let the caller handle date filtering
    # if they have actual liu_yue dates available
    return liu_yue_array


def _get_xun_and_xun_kong_from_object(liu_yun_obj) -> tuple:
    """
    Get Xun (旬) and Xun Kong (旬空) from a Liu Yun object.

    Args:
        liu_yun_obj: Liu Yun object (Liu Nian or Liu Yue) from lunar-python library

    Returns:
        tuple: (xun_name: str, xun_kong_pair: str)
    """
    try:
        xun = liu_yun_obj.getXun() if hasattr(liu_yun_obj, "getXun") else "Unknown"
        xun_kong = (
            liu_yun_obj.getXunKong()
            if hasattr(liu_yun_obj, "getXunKong")
            else "Unknown"
        )
        return (xun, xun_kong)
    except Exception:
        return ("Unknown", "Unknown")


def _detect_liu_nian_interactions(
    liu_nian_stem: str, liu_nian_branch: str, birth_chart: dict
) -> dict:
    """
    Detect Liu Nian interactions with birth chart using same 1x4 scan as Da Yun.

    The Liu Nian pillar acts as an External Trigger entering the birth chart system.
    Uses the same Tier-based priority checks and Key vs Lock logic.

    Args:
        liu_nian_stem (str): Liu Nian heavenly stem (year stem)
        liu_nian_branch (str): Liu Nian earthly branch (year branch)
        birth_chart (dict): Birth chart with keys "year", "month", "day", "hour"

    Returns:
        dict: Organized interactions by pillar and tier
    """
    # Leverage the existing Da Yun interaction detection function
    return _detect_da_yun_interactions(liu_nian_stem, liu_nian_branch, birth_chart)


def _detect_liu_yue_interactions(
    liu_yue_stem: str, liu_yue_branch: str, birth_chart: dict
) -> dict:
    """
    Detect Liu Yue interactions with birth chart using same 1x4 scan as Da Yun.

    The Liu Yue pillar acts as an External Trigger entering the birth chart system.
    Uses the same Tier-based priority checks and Key vs Lock logic.

    Args:
        liu_yue_stem (str): Liu Yue heavenly stem (month stem)
        liu_yue_branch (str): Liu Yue earthly branch (month branch)
        birth_chart (dict): Birth chart with keys "year", "month", "day", "hour"

    Returns:
        dict: Organized interactions by pillar and tier
    """
    # Leverage the existing Da Yun interaction detection function
    return _detect_da_yun_interactions(liu_yue_stem, liu_yue_branch, birth_chart)


# ============================================================================
# MAIN LIU NIAN CALCULATION
# ============================================================================


def get_liu_nian(
    lunar_birthday: Lunar,
    gender: int,
    start_year: int = None,
    num_years: int = None,
    reference_date: datetime = None,
) -> dict:
    """
    Calculate Annual Luck Cycles (Liu Nian) from lunar birthday and gender.

    If start_year and num_years are both None, uses reference_date to calculate
    a 10-year range (5 years past + 5 years future).

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male
        start_year (int): Optional calendar year to start from. If None, auto-calculated.
        num_years (int): Number of years to calculate. If None, auto-calculated.
        reference_date (datetime): Reference date for auto-calculation (default: today)

    Returns:
        dict: Structured JSON with Liu Nian cycles and timing information
    """
    # Auto-calculate date range if not provided
    if start_year is None and num_years is None:
        start_year, num_years = _get_current_date_range_liu_nian(reference_date)
    elif reference_date is not None:
        # If start_year is provided but num_years is not, still respect start_year
        if num_years is None:
            num_years = 10
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

    # Determine starting year for Liu Nian calculation
    if start_year is None:
        start_year = qi_yun_start_year

    # Get all Liu Nian cycles starting from the specified year
    # We need to use the Da Yun object to access Liu Nian
    da_yun_array = yun.getDaYun()

    if not da_yun_array or len(da_yun_array) == 0:
        return {
            "流年": {
                "元信息": {
                    "性别": "男" if gender == 1 else "女",
                    "出生阳历": lunar_birthday.getSolar().toYmdHms(),
                    "出生农历": f"{lunar_birthday.getYear()}-{lunar_birthday.getMonth()}-{lunar_birthday.getDay()}",
                    "起运时间": qi_yun_date.toYmdHms(),
                    "起运年份": qi_yun_start_year,
                    "顺逆": "顺推" if yun.isForward() else "逆推",
                    "开始年份": start_year,
                    "计算年数": num_years,
                },
                "流年周期": [],
            }
        }

    # Collect Liu Nian data from all Da Yun cycles
    liu_nian_data = []
    total_liu_nian_count = 0

    for da_yun_obj in da_yun_array:
        liu_nian_array = da_yun_obj.getLiuNian()

        if not liu_nian_array:
            continue

        for i, liu_nian_obj in enumerate(liu_nian_array):
            gan_zhi = liu_nian_obj.getGanZhi()
            calendar_year = liu_nian_obj.getYear()
            age = liu_nian_obj.getAge()

            if gan_zhi == "Unknown" or len(gan_zhi) < 2:
                continue

            # Skip years before our start_year or after our range
            if calendar_year < start_year or total_liu_nian_count >= num_years:
                if calendar_year < start_year:
                    continue
                else:
                    break

            liu_nian_stem = gan_zhi[0]
            liu_nian_branch = gan_zhi[1]

            # Calculate Ten Gods for this 流年
            stem_shi_shen = _get_shi_shen_for_stem_pair(day_stem, liu_nian_stem)
            branch_shi_shen = _get_hidden_stems_shi_shen(day_stem, liu_nian_branch)

            # Life Stage (地势) for the Liu Nian branch using birth day stem as reference
            di_shi = _get_di_shi(day_stem, liu_nian_branch)

            # Five Elements (五行) for Stem and Branch
            stem_wu_xing = _get_stem_wu_xing(liu_nian_stem)
            branch_wu_xing = _get_branch_wu_xing(liu_nian_branch)

            # Nayin (纳音) for the Liu Nian stem-branch pair
            nayin = _get_nayin(liu_nian_stem, liu_nian_branch)

            # Get Xun (旬) and Xun Kong (旬空)
            xun, xun_kong = _get_xun_and_xun_kong_from_object(liu_nian_obj)

            # Detect interactions (作用) with birth chart
            interactions_result = _detect_liu_nian_interactions(
                liu_nian_stem, liu_nian_branch, birth_chart
            )
            interactions = interactions_result.get("作用", [])

            liu_nian_info = {
                "日历年份": calendar_year,  # Calendar year
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
                "年龄": age,  # Age at start of year (from library)
            }
            liu_nian_data.append(liu_nian_info)
            total_liu_nian_count += 1

        # Stop if we've collected enough years
        if total_liu_nian_count >= num_years:
            break

    # Compile the complete liu_nian structure
    return {
        "流年": {
            "元信息": {
                "性别": "男" if gender == 1 else "女",
                "出生阳历": lunar_birthday.getSolar().toYmdHms(),
                "出生农历": f"{lunar_birthday.getYear()}-{lunar_birthday.getMonth()}-{lunar_birthday.getDay()}",
                "起运时间": qi_yun_date.toYmdHms(),
                "起运年份": qi_yun_start_year,
                "顺逆": "顺推" if yun.isForward() else "逆推",
                "开始年份": start_year,
                "计算年数": num_years,
                "流年周期数": len(liu_nian_data),
            },
            "流年周期": liu_nian_data,
        }
    }


# ============================================================================
# MAIN LIU YUE CALCULATION
# ============================================================================


def get_liu_yue(
    lunar_birthday: Lunar,
    gender: int,
    year_index: int = None,
    reference_date: datetime = None,
) -> dict:
    """
    Calculate Monthly Luck Cycles (Liu Yue) for a specific annual period.

    When used within get_liu_nian_ye(), months are automatically filtered to include
    only those within the past 12 months + next 24 months range from reference_date.

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male
        year_index (int): Which year within the Liu Nian cycles to get monthly for (0-based)
        reference_date (datetime): Reference date for month range filtering (default: today)

    Returns:
        dict: Structured JSON with Liu Yue cycles for the specified range
    """
    if reference_date is None:
        reference_date = datetime.now()
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

    # Get all Da Yun cycles and find the Liu Nian at year_index
    da_yun_array = yun.getDaYun()

    if not da_yun_array or len(da_yun_array) == 0:
        return {
            "流月": {
                "元信息": {
                    "性别": "男" if gender == 1 else "女",
                    "出生阳历": lunar_birthday.getSolar().toYmdHms(),
                    "出生农历": f"{lunar_birthday.getYear()}-{lunar_birthday.getMonth()}-{lunar_birthday.getDay()}",
                    "起运时间": qi_yun_date.toYmdHms(),
                    "起运年份": qi_yun_start_year,
                    "顺逆": "顺推" if yun.isForward() else "逆推",
                    "年份索引": year_index if year_index is not None else "自动",
                    "流月周期数": 0,
                },
                "流月周期": [],
            }
        }

    # Use year_index=0 as default if not provided
    if year_index is None:
        year_index = 0

    # Flatten all Liu Nian and find the one at year_index
    total_liu_nian_count = 0
    target_liu_nian_obj = None
    target_calendar_year = None
    target_age = None

    for da_yun_obj in da_yun_array:
        liu_nian_array = da_yun_obj.getLiuNian()

        if not liu_nian_array:
            continue

        for liu_nian_obj in liu_nian_array:
            if total_liu_nian_count == year_index:
                target_liu_nian_obj = liu_nian_obj
                target_calendar_year = liu_nian_obj.getYear()
                target_age = liu_nian_obj.getAge()
                break

            total_liu_nian_count += 1

        if target_liu_nian_obj:
            break

    if not target_liu_nian_obj:
        return {
            "流月": {
                "元信息": {
                    "性别": "男" if gender == 1 else "女",
                    "出生阳历": lunar_birthday.getSolar().toYmdHms(),
                    "出生农历": f"{lunar_birthday.getYear()}-{lunar_birthday.getMonth()}-{lunar_birthday.getDay()}",
                    "起运时间": qi_yun_date.toYmdHms(),
                    "起运年份": qi_yun_start_year,
                    "顺逆": "顺推" if yun.isForward() else "逆推",
                    "年份索引": year_index,
                    "流月周期数": 0,
                    "错误": f"无法找到第 {year_index} 个流年",
                },
                "流月周期": [],
            }
        }

    # Get Liu Yue array for this Liu Nian
    liu_yue_array = target_liu_nian_obj.getLiuYue()

    if not liu_yue_array:
        return {
            "流月": {
                "元信息": {
                    "性别": "男" if gender == 1 else "女",
                    "出生阳历": lunar_birthday.getSolar().toYmdHms(),
                    "出生农历": f"{lunar_birthday.getYear()}-{lunar_birthday.getMonth()}-{lunar_birthday.getDay()}",
                    "起运时间": qi_yun_date.toYmdHms(),
                    "起运年份": qi_yun_start_year,
                    "顺逆": "顺推" if yun.isForward() else "逆推",
                    "年份索引": year_index,
                    "流年": f"{target_calendar_year}年 ({target_age}岁)",
                    "流月周期数": 0,
                },
                "流月周期": [],
            }
        }

    # Calculate date boundaries for month filtering (past 12 months + next 24 months)
    past_12_months = reference_date - timedelta(days=365)
    next_24_months = reference_date + timedelta(days=730)

    # Process each 流月 (month) within this year
    liu_yue_data = []

    for i, liu_yue_obj in enumerate(liu_yue_array):
        gan_zhi = liu_yue_obj.getGanZhi()

        if gan_zhi == "Unknown" or len(gan_zhi) < 2:
            continue

        # Try to get the month number from the Liu Yue object
        # The month is typically the index i (0-11 for Jan-Dec)
        month_num = i + 1  # 1-based month number

        # Create a date representation for filtering
        # Use the target year and the month number
        try:
            month_date = datetime(target_calendar_year, month_num, 1)
        except ValueError:
            # If month_num is invalid, skip this entry
            continue

        # Filter: only include months within past 12 months + next 24 months
        if month_date < past_12_months or month_date > next_24_months:
            continue

        liu_yue_stem = gan_zhi[0]
        liu_yue_branch = gan_zhi[1]

        # Calculate Ten Gods for this 流月
        stem_shi_shen = _get_shi_shen_for_stem_pair(day_stem, liu_yue_stem)
        branch_shi_shen = _get_hidden_stems_shi_shen(day_stem, liu_yue_branch)

        # Life Stage (地势) for the Liu Yue branch using birth day stem as reference
        di_shi = _get_di_shi(day_stem, liu_yue_branch)

        # Five Elements (五行) for Stem and Branch
        stem_wu_xing = _get_stem_wu_xing(liu_yue_stem)
        branch_wu_xing = _get_branch_wu_xing(liu_yue_branch)

        # Nayin (纳音) for the Liu Yue stem-branch pair
        nayin = _get_nayin(liu_yue_stem, liu_yue_branch)

        # Get Xun (旬) and Xun Kong (旬空)
        xun, xun_kong = _get_xun_and_xun_kong_from_object(liu_yue_obj)

        # Detect interactions (作用) with birth chart
        interactions_result = _detect_liu_yue_interactions(
            liu_yue_stem, liu_yue_branch, birth_chart
        )
        interactions = interactions_result.get("作用", [])

        # Get month info
        month_name = (
            liu_yue_obj.getMonthInChinese()
            if hasattr(liu_yue_obj, "getMonthInChinese")
            else f"第{i+1}个月"
        )

        liu_yue_info = {
            "月份": month_name,  # Month name in Chinese
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
                "主题": stem_shi_shen,  # Primary life theme (Month Stem Ten God)
                "天干十神": stem_shi_shen,  # Month Stem Ten God (for clarity)
                "地支十神": branch_shi_shen,  # Hidden themes (Main/Middle/Residual)
            },
            "作用": interactions,  # Branch and Stem interactions with birth chart
        }
        liu_yue_data.append(liu_yue_info)

    # Compile the complete liu_yue structure
    return {
        "流月": {
            "元信息": {
                "性别": "男" if gender == 1 else "女",
                "出生阳历": lunar_birthday.getSolar().toYmdHms(),
                "出生农历": f"{lunar_birthday.getYear()}-{lunar_birthday.getMonth()}-{lunar_birthday.getDay()}",
                "起运时间": qi_yun_date.toYmdHms(),
                "起运年份": qi_yun_start_year,
                "顺逆": "顺推" if yun.isForward() else "逆推",
                "年份索引": year_index,
                "流年": f"{target_calendar_year}年 ({target_age}岁)",
                "流月周期数": len(liu_yue_data),
            },
            "流月周期": liu_yue_data,
        }
    }


# ============================================================================
# COMBINED LIU NIAN & LIU YUE
# ============================================================================


def get_liu_nian_ye(
    lunar_birthday: Lunar,
    gender: int,
    start_year: int = None,
    num_years: int = None,
    reference_date: datetime = None,
) -> dict:
    """
    Calculate complete Liu Nian (Annual Luck) and Liu Yue (Monthly Luck) combined analysis.

    If start_year and num_years are both None, uses reference_date to calculate
    a 10-year range (5 years past + 5 years future).
    For each Liu Nian year, includes its Liu Yue (monthly cycles).

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male
        start_year (int): Optional calendar year to start from
        num_years (int): Number of years to calculate
        reference_date (datetime): Reference date for auto-calculation (default: today)

    Returns:
        dict: Structured JSON with Liu Nian cycles, each containing Liu Yue data
    """
    if reference_date is None:
        reference_date = datetime.now()

    # First get Liu Nian data with date awareness
    liu_nian_result = get_liu_nian(
        lunar_birthday, gender, start_year, num_years, reference_date
    )

    # Now add Liu Yue data for each Liu Nian
    liu_nian_cycles = liu_nian_result["流年"]["流年周期"]

    for idx, liu_nian_cycle in enumerate(liu_nian_cycles):
        # Get Liu Yue data for this year
        liu_yue_result = get_liu_yue(lunar_birthday, gender, idx, reference_date)
        liu_nian_cycle["流月周期"] = liu_yue_result["流月"]["流月周期"]

    return liu_nian_result


# ============================================================================
# CONVENIENCE FUNCTIONS - DATE-FOCUSED ANALYSIS
# ============================================================================


def get_liu_nian_current_focus(lunar_birthday: Lunar, gender: int) -> dict:
    """
    Get Liu Nian focused on current date: 5 years past + 5 years future.

    Convenience wrapper around get_liu_nian() with automatic date range calculation.

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male

    Returns:
        dict: Liu Nian cycles for the current date-focused range
    """
    return get_liu_nian(lunar_birthday, gender, reference_date=datetime.now())


def get_liu_yue_current_focus(
    lunar_birthday: Lunar, gender: int, year_index: int = 0
) -> dict:
    """
    Get Liu Yue for a specific year with current date context.

    Convenience wrapper around get_liu_yue() with automatic date reference.

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male
        year_index (int): Which year to analyze (0-based)

    Returns:
        dict: Liu Yue cycles for that year
    """
    return get_liu_yue(
        lunar_birthday, gender, year_index, reference_date=datetime.now()
    )


def get_liu_nian_ye_current_focus(lunar_birthday: Lunar, gender: int) -> dict:
    """
    Get complete Liu Nian & Liu Yue analysis focused on current date.

    Convenience wrapper for comprehensive analysis with automatic date range.
    - Liu Nian: 5 years past + 5 years future from today
    - Liu Yue: All months for those years

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male

    Returns:
        dict: Combined Liu Nian + Liu Yue cycles with current date focus
    """
    return get_liu_nian_ye(lunar_birthday, gender, reference_date=datetime.now())


# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    import json
    import sys
    from io import StringIO
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
    from src.astronomer_calculations.bazi_pillars import get_bazi_pillars

    # python -m src.astronomer_calculations.liu_nian_ye

    # Set encoding to UTF-8 for proper Chinese character output
    if sys.stdout.encoding != "utf-8":
        sys.stdout = StringIO() if sys.platform == "win32" else sys.stdout

    # Get current datetime
    now = datetime.now()
    print(f"当前日期时间: {now.strftime('%Y-%m-%d %H:%M:%S')}", file=sys.stderr)

    # Example: Lara's birthday
    solar_birthday = Solar.fromYmdHms(2025, 7, 31, 9, 10, 0)
    tst_birthday, inputs_report = get_true_solar_time(
        datetime(2025, 7, 31, 9, 10, 0), 1.4759, 103.808053
    )
    lunar_birthday = tst_birthday.getLunar()

    print("八字", file=sys.stderr)
    bazi_json = get_bazi_pillars(lunar_birthday)
    print(f"八字: {bazi_json}", file=sys.stderr)

    print(
        f"\n=== 流年 5年过去 + 5年未来 (今日: {now.year}-{now.month}-{now.day}) ===",
        file=sys.stderr,
    )
    result = get_liu_nian(lunar_birthday, gender=0, reference_date=now)
    print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)

    print(f"\n=== 流月 第1个年份 (女, Gender=0) ===", file=sys.stderr)
    result = get_liu_yue(lunar_birthday, gender=0, year_index=0, reference_date=now)
    print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)

    print(
        f"\n=== 流年 & 流月 组合分析 (女, Gender=0) - 自动日期范围 ===", file=sys.stderr
    )
    result = get_liu_nian_ye(lunar_birthday, gender=0, reference_date=now)
    print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
