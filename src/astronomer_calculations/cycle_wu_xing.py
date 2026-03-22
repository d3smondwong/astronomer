"""
Cycle 五行力量 (Five Elements Strength Dynamics) Calculator
===========================================================

Calculates how a BaZi cycle pillar (运柱) modulates the natal chart's 五行力量,
using the same Ming Dynasty Imperial Qi Dynamics engine as wu_xing.py.

Supported cycle types
---------------------
- 大运 (Da Yun)   — 10-year luck pillars
- 小运 (Xiao Yun) — annual pre-luck pillars (before 大运 starts)
- 流年 (Liu Nian) — annual pillars during 大运
- 流月 (Liu Yue)  — monthly pillars during 流年

Architecture
------------
CycleWuXingDynamics wraps WuXingDynamicsCalculator and handles the cycle-specific
concerns before delegating to the core engine:

  1. Pillar weight adjustment
     Cycle pillar receives `cycle_weight` (default 0.20).
     Natal pillars are rescaled proportionally: adjustment_ratio = (1 - cycle_weight) / Σnatal_weights.
     Cycle stem_weight = cycle_weight × 0.1 (same ratio as natal pillars in wu_xing.py).

  2. Seasonal anchoring
     Seasonal factors (旺/相/囚/休/死) are always derived from the natal month branch,
     not the cycle pillar's branch. This keeps the birth chart's elemental season as the
     fixed reference; the cycle pillar acts as a temporary overlay.

  3. 旬空 reductions
     _compute_xk_reductions() merges natal 旬空 (from get_xun_kong()) and the cycle
     pillar's own 旬空 (from getXunKong()) into a per-branch reduction map applied before
     scoring. Skipped if neither source is provided.

  4. Interaction scoring
     The caller must pre-compute get_cycle_interactions() and pass its _raw_priority_list.
     This list drives 天干合/克/冲 and branch interaction bonuses in _score_priority_results().
     Passing the list avoids recomputing interactions inside this class.

  5. 通根 (Tong Gen)
     _compute_tong_gen() checks the cycle stem against all active branches — both natal
     and cycle — giving a true rooting depth for the cycle pillar in context.

Output
------
calculate_cycle_interaction() returns the full wu_xing.calculate() dict with:
  - 基本信息 and 四柱 sections stripped (natal-only; not meaningful in cycle context)
  - A "{cycle_type}柱" key prepended with enriched cycle pillar metadata
    (天干, 地支, 季节状态, 通根, 旬, 旬空, 五行, 藏干, 十神, 纳音, 地势, 运干十二长生)

Utility functions
-----------------
get_stem_wu_xing(stem)   — standalone 五行+阴阳 lookup for a heavenly stem character
get_branch_wu_xing(branch) — standalone 五行+阴阳 lookup for an earthly branch character

Exports
-------
  get_stem_wu_xing, get_branch_wu_xing, CycleWuXingDynamics
"""
from lunar_python.util import LunarUtil
from lunar_python import Lunar
from typing import Dict, List
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
    _compute_xk_reductions,
    STR_STEM,
    STR_BRANCH,
    _YANG_STEMS,
    _STATE_DESCRIPTIONS,
    _ROOT_LABELS,
)
from src.astronomer_calculations.cycle_shi_shen import (
    get_shi_shen_for_stem_pair,
    get_hidden_stems_shi_shen,
)
from src.astronomer_calculations.cycle_di_shi import get_di_shi
from src.astronomer_calculations.cycle_na_yin import get_nayin


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
    Five Elements dynamics calculator for BaZi cycle pillars.

    Wraps WuXingDynamicsCalculator to add cycle-specific setup:
    - Proportional weight redistribution (natal pillars scaled down to make room
      for the cycle pillar; default cycle_weight = 0.20)
    - Seasonal factors anchored to the natal month branch (birth chart season,
      not the cycle pillar's own branch)
    - Optional 旬空 reductions from natal and cycle pillar sources
    - Enriched cycle pillar metadata block prepended to every result

    Usage::

        interactions = get_cycle_interactions(cycle_stem, cycle_branch, natal_pillars)
        result = CycleWuXingDynamics().calculate_cycle_interaction(
            cycle_object,
            lunar_birthday,
            priority_list=interactions["_raw_priority_list"],
            cycle_type="大运",
        )
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
                          automatically. Must also implement getXun() and getXunKong() for
                          旬/旬空 output.
            day_master_stem: Day master heavenly stem character (e.g. "甲"). Used as
                             reference point for 十神 and 地势 calculations.
            seasonal: SeasonalFactors object from get_seasonal_factors(). Provides
                      elemental state (旺/相/囚/休/死) per element. If None, all
                      elements default to "囚".
            pillars: All pillars in scope (natal + cycle for interactive mode, or just the
                     cycle pillar for isolated mode). Used by 通根 to check all branches.

        Returns dict with: 天干, 地支, 显示名称, 季节状态, 纳音, 地势, 运干十二长生,
                           通根, 旬, 旬空, 五行, 藏干, 十神
        """
        gan_zhi = cycle_object.getGanZhi()
        cycle_stem = gan_zhi[0] if len(gan_zhi) > 0 else ""
        cycle_branch = gan_zhi[1] if len(gan_zhi) > 1 else ""

        stem_enum = STR_STEM.get(cycle_stem)
        branch_enum = STR_BRANCH.get(cycle_branch)

        if not stem_enum or not branch_enum:
            return {}

        # Basic info
        stem_elem = STEM_ELEMENT[stem_enum]
        branch_elem = BRANCH_ELEMENT.get(branch_enum)

        # 显示名称
        yang_yin = "阳" if cycle_stem in _YANG_STEMS else "阴"
        display_name = f"{cycle_stem}{stem_elem.value} ({yang_yin}{stem_elem.value})"

        # 季节状态
        state = seasonal.states.get(stem_elem, "囚") if seasonal else "囚"
        state_desc = _STATE_DESCRIPTIONS.get(state, state)

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
        cang_gan = []
        if branch_enum:
            for idx, (hs, _) in enumerate(BRANCH_HIDDEN.get(branch_enum, [])):
                strength = _ROOT_LABELS[idx] if idx < len(_ROOT_LABELS) else "未知"
                cang_gan.append({"干": hs.value, "强度": strength})

        # 十神: both for stem and for hidden stems in branch
        shi_shen = {}

        # Stem 十神
        if day_master_stem:
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
        xun_kong_data: dict | None = None,
        cycle_xk_str: str | None = None,
    ) -> Dict:
        """
        Calculate 五行力量 for a cycle pillar interacting with the natal chart.

        Combines the cycle pillar with natal pillars to show how the cycle's elemental
        composition modulates the natal chart's 五行力量. The caller must pre-compute
        get_cycle_interactions() and pass its _raw_priority_list — this avoids
        recomputing interactions here and lets the caller display the full interaction
        result alongside the wu_xing output.

        Weight mechanics:
            adjustment_ratio = (1.0 - cycle_weight) / Σ natal_position_weights
            natal_pillar.position_weight *= adjustment_ratio  (for each natal pillar)
            cycle stem_weight = cycle_weight * 0.1

        Seasonal anchoring:
            Seasonal factors are derived from the natal month branch, not the cycle
            branch. This keeps the birth chart's elemental season as the fixed base;
            the cycle pillar acts as a temporary overlay.

        Args:
            cycle_object: A cycle object (e.g. DaYun, XiaoYun, LiuNian) with
                          getGanZhi() → two-character stem-branch string (e.g. "戊子"),
                          getXun(), and getXunKong(). Stem and branch extracted automatically.
            lunar_birthday: Lunar birthday object. Provides the four natal pillars via
                            getEightChar() and the day master stem for metadata.
            priority_list: Priority-resolved interaction list from get_cycle_interactions()
                           (_raw_priority_list key). Drives 天干合/克/冲 and branch
                           interaction bonuses in WuXingDynamicsCalculator._score_priority_results().
            cycle_type: Cycle label (e.g. "大运", "流年"). Names the metadata key in the
                        output (e.g. "大运柱"). Has no effect on scoring.
            cycle_weight: Fractional weight for the cycle pillar (default 0.20).
                          Must be in (0.0, 1.0) exclusive.
            xun_kong_data: Natal 旬空 dict from get_xun_kong(), keyed by branch character.
                           Merged with cycle_xk_str to compute per-branch reductions.
            cycle_xk_str: Cycle pillar's own 旬空 string from getXunKong() (e.g. "子丑").
                          If neither xun_kong_data nor cycle_xk_str is provided,
                          旬空 reductions are skipped entirely.

        Returns:
            dict: {"{cycle_type}柱": <cycle pillar metadata>, **五行力量分析}.
                  基本信息 and 四柱 sections are stripped (natal-only; not meaningful
                  in cycle context).

        Raises:
            ValueError: If cycle stem/branch cannot be parsed, or cycle_weight is
                        outside (0.0, 1.0).
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
                STR_STEM.get(bazi.getYearGan()),
                STR_BRANCH.get(bazi.getYearZhi()),
            ),
            Pillar(
                "month",
                "月",
                0.45,
                0.045,
                STR_STEM.get(bazi.getMonthGan()),
                STR_BRANCH.get(bazi.getMonthZhi()),
            ),
            Pillar(
                "day",
                "日",
                0.25,
                0.025,
                STR_STEM.get(bazi.getDayGan()),
                STR_BRANCH.get(bazi.getDayZhi()),
            ),
            Pillar(
                "hour",
                "时",
                0.15,
                0.015,
                STR_STEM.get(bazi.getTimeGan()),
                STR_BRANCH.get(bazi.getTimeZhi()),
            ),
        ]

        # Create cycle pillar
        cycle_stem_enum = STR_STEM.get(cycle_stem)
        cycle_branch_enum = STR_BRANCH.get(cycle_branch)

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

        xk_red = (
            _compute_xk_reductions(
                adjusted_pillars,
                xun_kong_data or {},
                cycle_xk_str or "",
            )
            if (xun_kong_data or cycle_xk_str)
            else None
        )
        result = self.calculator.calculate(
            adjusted_pillars,
            priority_list=priority_list,
            seasonal=natal_seasonal,
            xun_kong_reductions=xk_red,
        )

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
     # Compute natal xun kong from birth chart
    from src.astronomer_calculations.void_xun_kong import get_xun_kong

    natal_xun_kong_result = get_xun_kong(tst_birthday.getLunar())
    natal_xk = natal_xun_kong_result.get("旬空", {})

    cycle_label = "大运"

    # Use index 1 (first actual 大运 cycle) as example
    yun = bazi.getYun(gender)
    da_yun = yun.getDaYun()[1]
    da_yun_stem = da_yun.getGanZhi()[0]
    da_yun_branch = da_yun.getGanZhi()[1]

    # Compute cycle pillar's own xun kong
    cycle_xk_str = da_yun.getXunKong()

    interactions = get_cycle_interactions(da_yun_stem, da_yun_branch, {
        "year":  {"stem": bazi.getYearGan(),  "branch": bazi.getYearZhi()},
        "month": {"stem": bazi.getMonthGan(), "branch": bazi.getMonthZhi()},
        "day":   {"stem": bazi.getDayGan(),   "branch": bazi.getDayZhi()},
        "hour":  {"stem": bazi.getTimeGan(),  "branch": bazi.getTimeZhi()},
    },
        cycle_xk_str=cycle_xk_str,
        natal_xk=natal_xk,
    )

    result = CycleWuXingDynamics().calculate_cycle_interaction(
        da_yun, lunar_birthday,
        priority_list=interactions.get("_raw_priority_list", []),
        cycle_type="大运",
        xun_kong_data=natal_xk,
        cycle_xk_str=cycle_xk_str,
    )

    logger.info(f"\n--- JSON Output for LLM ---")
    logger.info(json.dumps(result, ensure_ascii=False, indent=2))
