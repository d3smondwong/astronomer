from lunar_python.util import LunarUtil
from lunar_python import Lunar
from typing import Dict, List, Optional
from src.astronomer_calculations.wu_xing import (
    WuXingDynamicsCalculator,
    Pillar,
    Stem,
    Branch,
    get_wu_xing_tier,
    STEM_ELEMENT,
    BRANCH_ELEMENT,
    BRANCH_HIDDEN,
    SHENG_WANG_TABLE,
    get_seasonal_factors,
    get_zhu_dao_qi_shi,
    Element,
)
from src.astronomer_calculations.cycle_shi_shen import (
    get_shi_shen_for_stem_pair,
    get_hidden_stems_shi_shen,
)
from src.astronomer_calculations.cycle_di_shi import get_di_shi
from src.astronomer_calculations.cycle_na_yin import get_nayin

# ─────────────────────────────────────────────
# String-to-Enum conversion functions
# ─────────────────────────────────────────────

def string_to_stem(stem_str: str) -> Optional[Stem]:
    """Convert Chinese stem character to Stem enum."""
    stem_map = {
        "甲": Stem.JIA,
        "乙": Stem.YI,
        "丙": Stem.BING,
        "丁": Stem.DING,
        "戊": Stem.WU,
        "己": Stem.JI,
        "庚": Stem.GENG,
        "辛": Stem.XIN,
        "壬": Stem.REN,
        "癸": Stem.GUI,
    }
    return stem_map.get(stem_str)


def string_to_branch(branch_str: str) -> Optional[Branch]:
    """Convert Chinese branch character to Branch enum."""
    branch_map = {
        "子": Branch.ZI,
        "丑": Branch.CHOU,
        "寅": Branch.YIN,
        "卯": Branch.MAO,
        "辰": Branch.CHEN,
        "巳": Branch.SI,
        "午": Branch.WU,
        "未": Branch.WEI,
        "申": Branch.SHEN,
        "酉": Branch.YOU,
        "戌": Branch.XU,
        "亥": Branch.HAI,
    }
    return branch_map.get(branch_str)


def get_stem_wu_xing(cycle_stem: str) -> dict:
    """
    Get Five Element (五行) info for a Heavenly Stem (天干).

    Uses lunar_python library data which maps stems to elements.
    Polarity (阳/阴) is derived from the stem's index position:
    - Even indices (甲丙戊庚壬) = 阳 (Yang)
    - Odd indices (乙丁己辛癸) = 阴 (Yin)

    Args:
        cycle_stem (str): Heavenly Stem (e.g., "甲", "乙", etc.)

    Returns:
        dict: {"五行": "木/火/土/金/水", "阴阳": "阳/阴"}
    """
    element = LunarUtil.WU_XING_GAN.get(cycle_stem, "Unknown")

    if element == "Unknown":
        return {"五行": "Unknown", "阴阳": "Unknown"}

    # Find index to determine polarity (even=Yang, odd=Yin)
    try:
        index = LunarUtil.GAN.index(cycle_stem)
        polarity = "阳" if index % 2 == 0 else "阴"
    except ValueError:
        polarity = "Unknown"

    return {"五行": element, "阴阳": polarity}


def get_branch_wu_xing(cycle_branch: str) -> dict:
    """
    Get Five Element (五行) info for an Earthly Branch (地支).

    Uses lunar_python library data which maps branches to elements.
    Polarity (阳/阴) is derived from the branch's index position:
    - Even indices (子寅辰午申戌) = 阳 (Yang)
    - Odd indices (丑卯巳未酉亥) = 阴 (Yin)

    Args:
        cycle_branch (str): Earthly Branch (e.g., "子", "丑", etc.)

    Returns:
        dict: {"五行": "木/火/土/金/水", "阴阳": "阳/阴"}
    """
    element = LunarUtil.WU_XING_ZHI.get(cycle_branch, "Unknown")

    if element == "Unknown":
        return {"五行": "Unknown", "阴阳": "Unknown"}

    # Find index to determine polarity. ZHI is 0-indexed starting with 子 (Yang),
    # so even indices = 阳, odd indices = 阴.
    try:
        index = LunarUtil.ZHI.index(cycle_branch)
        polarity = "阳" if index % 2 == 0 else "阴"
    except ValueError:
        polarity = "Unknown"

    return {"五行": element, "阴阳": polarity}


# ─────────────────────────────────────────────
# Cycle Wu Xing Dynamics Calculator
# ─────────────────────────────────────────────


class CycleWuXingDynamics:
    """
    Calculates 五行力量 (Five Elements Strength Dynamics) for different BaZi cycles
    using the Ming Dynasty Imperial Qi Dynamics system.

    Supports interactive analysis:
    - 大运 (Da Yun): 10-year cycles
    - 小运 (Xiao Yun): Annual pre-luck cycles
    - 流年 (Liu Nian): Annual cycles during da_yun
    - 流月 (Liu Yue): Monthly cycles during liu_nian

    Interactive mode combines the cycle pillar with natal pillars to show how
    the cycle's elemental composition modulates the birth chart's 五行力量.
    """

    def __init__(self):
        """Initialize the calculator with WuXingDynamicsCalculator."""
        self.calculator = WuXingDynamicsCalculator()

    def _build_cycle_pillar_info(
        self,
        cycle_object,
        day_master_stem: str,
        seasonal,
        pillars: "List[Pillar]",
    ) -> dict:
        """
        Build enriched cycle pillar (运柱) info structure with all metadata.

        Args:
            cycle_object: A cycle object with getGanZhi() returning a two-character
                          stem-branch string (e.g. "戊子"). Stem and branch are extracted
                          automatically.
            pillars: All pillars in scope (natal + cycle for interactive mode, or just the
                     cycle pillar for isolated mode). Used by 通根 to check all branches.

        Returns dict with: 天干, 地支, 显示名称, 季节状态, 十二长生, 通根, 五行, 藏干, 十神
        """
        gan_zhi = cycle_object.getGanZhi()
        cycle_stem = gan_zhi[0] if len(gan_zhi) > 0 else ""
        cycle_branch = gan_zhi[1] if len(gan_zhi) > 1 else ""

        stem_enum = string_to_stem(cycle_stem)
        branch_enum = string_to_branch(cycle_branch)

        if not stem_enum or not branch_enum:
            return {}

        # Basic info
        stem_elem = STEM_ELEMENT[stem_enum]
        branch_elem = BRANCH_ELEMENT.get(branch_enum)

        # 显示名称
        yang_stems = {"甲", "丙", "戊", "庚", "壬"}
        yang_yin = "阳" if cycle_stem in yang_stems else "阴"
        display_name = f"{cycle_stem}{stem_elem.value} ({yang_yin}{stem_elem.value})"

        # 季节状态 and state description
        state_descriptions = {
            "旺": "旺 (最强)",
            "相": "相 (次强)",
            "囚": "囚 (弱)",
            "休": "休 (气弱)",
            "死": "死 (极弱)",
        }
        state = seasonal.states.get(stem_elem, "囚") if seasonal else "囚"
        state_desc = state_descriptions.get(state, state)

        # Life Stage (地势) for the cycle branch using birth day stem as reference
        di_shi = get_di_shi(day_master_stem, cycle_branch)

        # Nayin (纳音) for the cycle stem-branch pair
        nayin = get_nayin(cycle_stem, cycle_branch)

        # 十二长生
        sheng_wang_stage = SHENG_WANG_TABLE.get(stem_enum, {}).get(branch_enum)

        # 通根: check all branches in scope (natal + cycle for interactive, cycle-only for isolated)
        tong_gen = WuXingDynamicsCalculator._compute_tong_gen(stem_elem, pillars)

        # 五行 info
        wu_xing_info = {
            "天干五行": stem_elem.value,
            "地支五行": branch_elem.value if branch_elem else None,
            "主导气势": get_zhu_dao_qi_shi(stem_elem, branch_elem) if branch_elem else None,
        }

        # 藏干: hidden stems with strength category
        root_labels = ["本气根", "中气根", "余气根"]
        cang_gan = []
        if branch_enum:
            for idx, (hs, _) in enumerate(BRANCH_HIDDEN.get(branch_enum, [])):
                strength = root_labels[idx] if idx < len(root_labels) else "未知"
                cang_gan.append({"干": hs.value, "强度": strength})

        # 十神: both for stem and for hidden stems in branch
        day_master_stem_enum = string_to_stem(day_master_stem)
        shi_shen = {}

        # Stem 十神
        if day_master_stem_enum:
            shi_shen_stem = get_shi_shen_for_stem_pair(day_master_stem, cycle_stem)
            shi_shen["天干"] = {
                "天干": cycle_stem,
                "十神": shi_shen_stem
            }

        # Branch hidden stem 十神: include all present tiers (本气, 中气, 余气)
        if branch_enum:
            hidden_stems_shi_shen = get_hidden_stems_shi_shen(day_master_stem, cycle_branch)
            for tier in ("本气", "中气", "余气"):
                if tier in hidden_stems_shi_shen:
                    shi_shen[tier] = hidden_stems_shi_shen[tier]

        return {
            "天干": cycle_stem,
            "地支": cycle_branch,
            "显示名称": display_name,
            "季节状态": state_desc,
            "纳音": nayin,
            "地势": di_shi,
            "运干十二长生": sheng_wang_stage,
            "通根": tong_gen,
            "旬": cycle_object.getXun(),
            "旬空": cycle_object.getXunKong(),
            "五行": wu_xing_info,
            "藏干": cang_gan,
            "十神": shi_shen,
        }

    def calculate_cycle_interaction(
        self,
        cycle_object,
        lunar_birthday: Lunar,
        priority_list: list,
        cycle_type: str = "大运",
        cycle_weight: float = 0.20,
    ) -> Dict:
        """
        Calculate 五行力量 for a cycle pillar interaction with the natal chart.

        Combines the cycle pillar with natal pillars to show how the cycle's
        elemental composition interacts with and modulates the natal chart's 五行力量.

        The caller is responsible for running get_cycle_interactions() first and
        passing its _raw_priority_list here. This allows the caller to reuse the
        full interaction result for display without recomputing it here.

        Args:
            cycle_object: A cycle object (e.g. DaYun, XiaoYun, LiuNian) with a
                          getGanZhi() method returning a two-character stem-branch string
                          (e.g. "戊子"). The stem and branch are extracted automatically.
            lunar_birthday: Lunar birthday object (for natal pillars)
            priority_list: Priority-resolved interaction list from get_cycle_interactions()
                           (_raw_priority_list key). Drives combination and clash scoring.
            cycle_type: Label identifying the cycle (e.g. "大运", "流年").
                        Used only to name the output key (e.g. "大运柱"). Does not affect scoring.
            cycle_weight: Weight assigned to the cycle pillar (default 0.20 = 20%).
                         Remaining weight distributed proportionally to natal pillars.

        Returns:
            dict: Combined 五行力量分析 showing cycle + natal interaction
        """
        gan_zhi = cycle_object.getGanZhi()
        cycle_stem = gan_zhi[0] if len(gan_zhi) > 0 else ""
        cycle_branch = gan_zhi[1] if len(gan_zhi) > 1 else ""
        # Get natal pillars
        bazi = lunar_birthday.getEightChar()

        natal_pillars = [
            Pillar(
                "year",
                "年",
                0.15,
                0.015,
                string_to_stem(bazi.getYearGan()),
                string_to_branch(bazi.getYearZhi()),
            ),
            Pillar(
                "month",
                "月",
                0.45,
                0.045,
                string_to_stem(bazi.getMonthGan()),
                string_to_branch(bazi.getMonthZhi()),
            ),
            Pillar(
                "day",
                "日",
                0.25,
                0.025,
                string_to_stem(bazi.getDayGan()),
                string_to_branch(bazi.getDayZhi()),
            ),
            Pillar(
                "hour",
                "时",
                0.15,
                0.015,
                string_to_stem(bazi.getTimeGan()),
                string_to_branch(bazi.getTimeZhi()),
            ),
        ]

        # Create cycle pillar
        cycle_stem_enum = string_to_stem(cycle_stem)
        cycle_branch_enum = string_to_branch(cycle_branch)

        if not cycle_stem_enum or not cycle_branch_enum:
            raise ValueError(f"Invalid stem '{cycle_stem}' or branch '{cycle_branch}'")

        if not (0.0 < cycle_weight < 1.0):
            raise ValueError(f"cycle_weight must be between 0 and 1 exclusive, got {cycle_weight}")

        cycle_pillar = Pillar(
            position="cycle",
            position_weight=cycle_weight,
            stem_weight=cycle_weight * 0.1,
            label="运",
            stem=cycle_stem_enum,
            branch=cycle_branch_enum,
        )

        # Adjust natal pillar weights proportionally
        total_natal_weight = sum(p.position_weight for p in natal_pillars)
        adjustment_ratio = (1.0 - cycle_weight) / total_natal_weight

        adjusted_pillars = [
            Pillar(p.position, p.label, p.position_weight * adjustment_ratio, p.stem_weight * adjustment_ratio, p.stem, p.branch)
            for p in natal_pillars
        ] + [cycle_pillar]

        # Use natal month's seasonal factors so clash resolution always reflects the
        # birth chart's elemental season, not the cycle pillar's branch.
        natal_month_p = next((p for p in natal_pillars if p.position == "month"), None)
        natal_seasonal = get_seasonal_factors(natal_month_p.branch) if natal_month_p and natal_month_p.branch else None

        result = self.calculator.calculate(adjusted_pillars, priority_list=priority_list, seasonal=natal_seasonal)

        # Remove natal-chart-specific sections — not meaningful in cycle context
        result.pop("基本信息", None)
        result.pop("四柱", None)

        # Build cycle pillar info and place it first in the returned dict
        day_master_stem = bazi.getDayGan()
        cycle_label = cycle_type + "柱"
        cycle_pillar_info = self._build_cycle_pillar_info(
            cycle_object, day_master_stem, natal_seasonal, adjusted_pillars
        )

        return {cycle_label: cycle_pillar_info, **result}



# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from lunar_python import Solar
    from datetime import datetime
    from src.utils.logging import configure_logging, get_logger
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time

    logging = configure_logging()
    logger = get_logger(__name__)

    # python -m src.astronomer_calculations.cycle_wu_xing

    # # Desmond's birthday example
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    tst_birthday, _ = get_true_solar_time(
        datetime_birthday, 1.3253, 103.808053
    )  # Get true solar time
    gender = 0

    # # Corinne's birthday example
    # solar_birthday= Solar.fromYmdHms(1987, 6, 3, 12, 6, 0)  # Create solar date June 3, 1987 at 12:06 PM
    # tst_birthday, inputs_report = get_true_solar_time(datetime(1987, 6, 3, 12, 6, 0), 1.4759, 103.808053)  # Get true solar time for the birthday

    # # Lara's birthday example
    # solar_birthday = Solar.fromYmdHms(
    #     2025, 7, 31, 9, 10, 0
    # )  # Create solar date June 3, 1987 at 12:06 PM
    # tst_birthday, inputs_report = get_true_solar_time(
    #     datetime(2025, 7, 31, 9, 10, 0), 1.3253, 103.808053
    # )

    logger.info("阳历生日: " + solar_birthday.toYmdHms())
    logger.info("真太阳时生日: " + tst_birthday.toYmdHms())

    lunar_birthday = tst_birthday.getLunar()  # Convert to lunar calendar

    bazi = lunar_birthday.getEightChar()
    logger.info(
        f"\nBaZi: {bazi.getYear()}, {bazi.getMonth()}, {bazi.getDay()}, {bazi.getTime()}"
    )

    from src.astronomer_calculations.cycle_interactions import get_cycle_interactions

    # Use index 1 (first actual 大运 cycle) as example
    yun = bazi.getYun(gender)
    da_yun = yun.getDaYun()[1]
    da_yun_stem = da_yun.getGanZhi()[0]
    da_yun_branch = da_yun.getGanZhi()[1]

    interactions = get_cycle_interactions(da_yun_stem, da_yun_branch, {
        "year":  {"stem": bazi.getYearGan(),  "branch": bazi.getYearZhi()},
        "month": {"stem": bazi.getMonthGan(), "branch": bazi.getMonthZhi()},
        "day":   {"stem": bazi.getDayGan(),   "branch": bazi.getDayZhi()},
        "hour":  {"stem": bazi.getTimeGan(),  "branch": bazi.getTimeZhi()},
    })

    result = CycleWuXingDynamics().calculate_cycle_interaction(
        da_yun, lunar_birthday,
        priority_list=interactions.get("_raw_priority_list", []),
        cycle_type="大运",
    )

    logger.info(f"\n--- JSON Output for LLM ---")
    logger.info(json.dumps(result, ensure_ascii=False, indent=2))
