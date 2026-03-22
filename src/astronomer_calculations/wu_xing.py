"""
Wu Xing (五行) - Five Elements Calculation Module

This module extracts and analyzes the Five Elements (五行) composition from a BaZi chart
using the WuXingDynamicsCalculator engine. It follows 三命通会 classical methodology for
hidden stem ordering, with position-weighted scoring, climate modulation, and full
priority-resolved interaction bonuses and reductions.

Core Architecture:
    - Hidden Stem Analysis: Extracts buried elemental stems from branches with depth weighting
      (三命通会 ordering: e.g. 巳 → 丙(本气), 庚(中气), 戊(余气))
    - Heavenly Stem Scoring: Position-weighted visible stem contributions with seasonal floors,
      further amplified by 通根 rooting tier (深根/中根/浅根/无根 → ×1.30/1.18/1.08/1.00)
    - Climate Modulation: 5-category temperature system (very_cold, cold, neutral, warm, hot)
      with element-specific sensitivity multipliers
    - Interaction Scoring: 13 of 16 interaction types scored; 3 excluded by classical methodology.
      All bonuses and reductions are priority-resolved (from apply_bazi_master_priority) before
      numeric conversion, ensuring 贪合忘冲, 三会>三合, and 消融吸收 semantics are respected.
    - 天干合 Rooting Modulation: combo_factor = min(r_mults) / r_深根 scales the transformation
      bonus by the weaker stem's rooting. Per-stem retention slides from 0.70 (深根, fully
      committed) to 1.00 (无根, bond doesn't hold) — compounding with Pass S 强度 downgrade.
    - 干支透合 uses a dedicated base constant (_BASE_GAN_ZHI_HE = 0.10) weaker than direct
      天干合 (_BASE_TIAN_GAN_HE = 0.25), reflecting the covert nature of the bond.

Weight Architecture (~1.10 total scale):
    Branch hidden stems:  year=0.15, month=0.45, day=0.25, hour=0.15 (sum=1.00)
    Heavenly stems:       year=0.015, month=0.045, day=0.025, hour=0.015 (sum=0.10)
    Combinations:         additive bonuses (small)

Key Functions:
    get_wu_xing(lunar_birthday, priority_list): Extracts Five Elements with professional analysis.

    Returns:
        dict: LLM-ready JSON structure:
        {
            "五行力量": {
                "基本信息": {
                    "日主": {
                        "显示名称": "戊土 (阳土)",
                        "天干": "戊", "五行": "土", "阴阳": "阳",
                        "旺衰": "旺 (最强)", "十二长生": "帝旺",
                        "通根": {"月": "本气根"}   # dict of pillar→root, or "无根"
                    },
                    "出生季节": "仲冬 (水旺之季)"  # precise 孟/仲/季 sub-season
                },
                "四柱": {
                    "年柱": {
                        "天干": "乙", "地支": "亥",
                        "季节状态": "相 (次强)", "十二长生": "死",
                        "通根": {"年": "本气根"},  # dict of pillar→root, or "无根"
                        "干支五行": {"天干五行": "木", "地支五行": "水",
                                  "主导气势": "截脚 (水克木)"},
                        "藏干": [{"干": "壬", "强度": "本气根"}, ...]
                    },
                    "月柱": {...}, "日柱": {...}, "时柱": {...}
                },
                "五行力量分析": {
                    "木": {"百分比": 15.5, "旺衰": "相 (次强)", "能级": {...}},
                    "火": {...}, "土": {...}, "金": {...}, "水": {...}
                },
                "组合加成": [...],  # 三合/三会/半合/天干合 etc. (priority-resolved)
                "六合加成": [...],  # 六合 pairs
                "相冲减损": [...],  # 六冲 clashes
                "刑减损":   [...],  # 三刑/无礼之刑/自刑
                "害减损":   [...],  # 六害
                "破减损":   [...]   # 六破
            },
            "五行相位动力": {        # Reference tier table for all seven strength levels
                "缺失": {...}, "极弱": {...}, "偏弱": {...}, "中和": {...},
                "偏旺": {...}, "极旺": {...}, "极亢": {...}
            }
        }

The Five Elements:
    - 木 (Wood): Growth, expansion, flexibility
    - 火 (Fire): Passion, activity, transformation
    - 土 (Earth): Stability, nurture, balance
    - 金 (Metal): Strength, discipline, precision
    - 水 (Water): Flow, wisdom, flexibility

Interaction Scoring Coverage (16 types total):
    SCORED (13 types):
        TIER 1 (Structural): 三会, 三合, 六冲, 六合
        TIER 2 (Operational): 共拱, 比和, 拱会, 残会, 半合, 天干合, 干支透合
        TIER 3 (Frictional): 三刑, 无礼之刑, 自刑, 六害, 六破

    NOT SCORED (3 types) — By Classical BaZi Methodology:
        • 暗合 (An He / Secret Harmony): Hidden stem resonance; no elemental synthesis
        • 天干克 (Tian Gan Ke / Stem Control): Control direction only; no power transform
        • 天干冲 (Tian Gan Chong / Stem Clash): Pure opposition; no synthesis
    → These three are contextually informative but do NOT change elemental composition.
      They are correctly excluded from 五行力量 scoring per classical methodology.
      Their rooting-based 强度 downgrade (Pass S) still propagates via the multiplier if
      they were scored — the exclusion is deliberate, not an omission.

    See _score_priority_results() docstring for detailed implementation.

Climate System:
    5-category weighted average from branch temperature qualities with position weights.
    Fire/Water: ±30% inverse sensitivity | Wood/Metal/Earth: ±8% moderate sensitivity
"""

from datetime import datetime
from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
from src.astronomer_calculations.void_xun_kong import get_xun_kong
from src.astronomer_calculations.natal_interactions import BRANCH_HIDDEN_ROOTING, get_stem_root_tier
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────


class Element(Enum):
    WOOD = "木"
    FIRE = "火"
    EARTH = "土"
    METAL = "金"
    WATER = "水"


class Stem(Enum):
    JIA = "甲"
    YI = "乙"
    BING = "丙"
    DING = "丁"
    WU = "戊"
    JI = "己"
    GENG = "庚"
    XIN = "辛"
    REN = "壬"
    GUI = "癸"


class Branch(Enum):
    ZI = "子"
    CHOU = "丑"
    YIN = "寅"
    MAO = "卯"
    CHEN = "辰"
    SI = "巳"
    WU = "午"
    WEI = "未"
    SHEN = "申"
    YOU = "酉"
    XU = "戌"
    HAI = "亥"


# ─────────────────────────────────────────────
# Static lookup tables
# ─────────────────────────────────────────────

STEM_ELEMENT: Dict[Stem, Element] = {
    Stem.JIA: Element.WOOD,
    Stem.YI: Element.WOOD,
    Stem.BING: Element.FIRE,
    Stem.DING: Element.FIRE,
    Stem.WU: Element.EARTH,
    Stem.JI: Element.EARTH,
    Stem.GENG: Element.METAL,
    Stem.XIN: Element.METAL,
    Stem.REN: Element.WATER,
    Stem.GUI: Element.WATER,
}

BRANCH_ELEMENT: Dict[Branch, Element] = {
    Branch.ZI: Element.WATER,
    Branch.HAI: Element.WATER,
    Branch.YIN: Element.WOOD,
    Branch.MAO: Element.WOOD,
    Branch.SI: Element.FIRE,
    Branch.WU: Element.FIRE,
    Branch.SHEN: Element.METAL,
    Branch.YOU: Element.METAL,
    Branch.CHEN: Element.EARTH,
    Branch.XU: Element.EARTH,
    Branch.CHOU: Element.EARTH,
    Branch.WEI: Element.EARTH,
}

# 天干合 transformation element lookup: 甲己→土, 乙庚→金, 丙辛→水, 丁壬→木, 戊癸→火
STEM_COMBINE_ELEMENT: Dict[str, Element] = {
    "甲": Element.EARTH,
    "己": Element.EARTH,
    "乙": Element.METAL,
    "庚": Element.METAL,
    "丙": Element.WATER,
    "辛": Element.WATER,
    "丁": Element.WOOD,
    "壬": Element.WOOD,
    "戊": Element.FIRE,
    "癸": Element.FIRE,
}

# Strength-to-multiplier mapping for priority-filtered interactions
# Maps 强度 (strength level from apply_bazi_master_priority) to numeric multiplier
INTERACTION_STRENGTH_MULTIPLIER: Dict[str, float] = {
    "强势主流": 1.00,  # Full force
    "显著影响": 0.75,  # Weakened but influential
    "中等衰减": 0.50,  # Moderately suppressed
    "大幅衰减": 0.20,  # Heavily suppressed
    "消融吸收": 0.00,  # Fully absorbed/neutralised
}

# Hidden stems: (primary, secondary, residual) with depth ratios.
# Derived from natal_interactions canonical plain-string table — single source of truth.
BRANCH_HIDDEN: Dict[Branch, List[Tuple[Stem, float]]] = {
    Branch(branch_str): [(Stem(stem_str), depth) for stem_str, depth in stems]
    for branch_str, stems in BRANCH_HIDDEN_ROOTING.items()
}

# ─────────────────────────────────────────────
# 十二长生 (12-stage life cycle) for heavenly stems
# ─────────────────────────────────────────────
# Stages in branch order starting from 子:
#   子 丑 寅 卯 辰 巳 午 未 申 酉 戌 亥
# For Yang stems the cycle goes forward; for Yin stems backward.
# Power multipliers per stage:
SHENG_WANG_MULT: Dict[str, float] = {
    "长生": 1.20,  # Birth — strong growth
    "沐浴": 0.90,  # Bath — unstable
    "冠带": 1.05,  # Dressing — maturing
    "临官": 1.15,  # Official — near peak
    "帝旺": 1.30,  # Emperor — absolute peak
    "衰": 0.85,  # Decline
    "病": 0.75,  # Illness
    "死": 0.65,  # Death
    "墓": 0.80,  # Tomb/storage — hidden power
    "绝": 0.60,  # Void
    "胎": 0.70,  # Embryo
    "养": 0.85,  # Nurture
}

# Full 十二长生 table: stem → branch → stage name
# Built from classical texts (淵海子平, 三命通會)
SHENG_WANG_TABLE: Dict[Stem, Dict[Branch, str]] = {
    Stem.JIA: {
        Branch.HAI: "长生",
        Branch.ZI: "沐浴",
        Branch.CHOU: "冠带",
        Branch.YIN: "临官",
        Branch.MAO: "帝旺",
        Branch.CHEN: "衰",
        Branch.SI: "病",
        Branch.WU: "死",
        Branch.WEI: "墓",
        Branch.SHEN: "绝",
        Branch.YOU: "胎",
        Branch.XU: "养",
    },
    Stem.YI: {  # Yin Wood — counterclockwise from 午 (reverse of 甲)
        Branch.WU: "长生",
        Branch.SI: "沐浴",
        Branch.CHEN: "冠带",
        Branch.MAO: "临官",
        Branch.YIN: "帝旺",
        Branch.CHOU: "衰",
        Branch.ZI: "病",
        Branch.HAI: "死",
        Branch.XU: "墓",
        Branch.YOU: "绝",
        Branch.SHEN: "胎",
        Branch.WEI: "养",
    },
    Stem.BING: {
        Branch.YIN: "长生",
        Branch.MAO: "沐浴",
        Branch.CHEN: "冠带",
        Branch.SI: "临官",
        Branch.WU: "帝旺",
        Branch.WEI: "衰",
        Branch.SHEN: "病",
        Branch.YOU: "死",
        Branch.XU: "墓",
        Branch.HAI: "绝",
        Branch.ZI: "胎",
        Branch.CHOU: "养",
    },
    Stem.DING: {
        Branch.YOU: "长生",
        Branch.SHEN: "沐浴",
        Branch.WEI: "冠带",
        Branch.WU: "临官",
        Branch.SI: "帝旺",
        Branch.CHEN: "衰",
        Branch.MAO: "病",
        Branch.YIN: "死",
        Branch.CHOU: "墓",
        Branch.ZI: "绝",
        Branch.HAI: "胎",
        Branch.XU: "养",
    },
    Stem.WU: {  # Yang Earth — same 长生 positions as 丙 per 三命通会
        Branch.YIN: "长生",
        Branch.MAO: "沐浴",
        Branch.CHEN: "冠带",
        Branch.SI: "临官",
        Branch.WU: "帝旺",
        Branch.WEI: "衰",
        Branch.SHEN: "病",
        Branch.YOU: "死",
        Branch.XU: "墓",
        Branch.HAI: "绝",
        Branch.ZI: "胎",
        Branch.CHOU: "养",
    },
    Stem.JI: {  # Yin Earth — same 长生 positions as 丁 per 三命通会
        Branch.YOU: "长生",
        Branch.SHEN: "沐浴",
        Branch.WEI: "冠带",
        Branch.WU: "临官",
        Branch.SI: "帝旺",
        Branch.CHEN: "衰",
        Branch.MAO: "病",
        Branch.YIN: "死",
        Branch.CHOU: "墓",
        Branch.ZI: "绝",
        Branch.HAI: "胎",
        Branch.XU: "养",
    },
    Stem.GENG: {
        Branch.SI: "长生",
        Branch.WU: "沐浴",
        Branch.WEI: "冠带",
        Branch.SHEN: "临官",
        Branch.YOU: "帝旺",
        Branch.XU: "衰",
        Branch.HAI: "病",
        Branch.ZI: "死",
        Branch.CHOU: "墓",
        Branch.YIN: "绝",
        Branch.MAO: "胎",
        Branch.CHEN: "养",
    },
    Stem.XIN: {
        Branch.ZI: "长生",
        Branch.HAI: "沐浴",
        Branch.XU: "冠带",
        Branch.YOU: "临官",
        Branch.SHEN: "帝旺",
        Branch.WEI: "衰",
        Branch.WU: "病",
        Branch.SI: "死",
        Branch.CHEN: "墓",
        Branch.MAO: "绝",
        Branch.YIN: "胎",
        Branch.CHOU: "养",
    },
    Stem.REN: {
        Branch.SHEN: "长生",
        Branch.YOU: "沐浴",
        Branch.XU: "冠带",
        Branch.HAI: "临官",
        Branch.ZI: "帝旺",
        Branch.CHOU: "衰",
        Branch.YIN: "病",
        Branch.MAO: "死",
        Branch.CHEN: "墓",
        Branch.SI: "绝",
        Branch.WU: "胎",
        Branch.WEI: "养",
    },
    Stem.GUI: {
        Branch.MAO: "长生",
        Branch.YIN: "沐浴",
        Branch.CHOU: "冠带",
        Branch.ZI: "临官",
        Branch.HAI: "帝旺",
        Branch.XU: "衰",
        Branch.YOU: "病",
        Branch.SHEN: "死",
        Branch.WEI: "墓",
        Branch.WU: "绝",
        Branch.SI: "胎",
        Branch.CHEN: "养",
    },
}


def get_shengwang_mult(stem: Stem, branch: Branch) -> float:
    """Return the 十二长生 power multiplier for a stem in a given branch."""
    stage = SHENG_WANG_TABLE.get(stem, {}).get(branch)
    if stage is None:
        return 1.0  # fallback
    return SHENG_WANG_MULT[stage]


# ─────────────────────────────────────────────
# Seasonal factors
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# Seasonal multiplier tables — module-level constants
# Defined at module level for efficiency and consistency across calculations
# ─────────────────────────────────────────────

# Hidden stem multipliers: full suppression range for buried stems in branches
STATE_MULT: Dict[str, float] = {
    "旺": 1.00,
    "相": 0.80,
    "休": 0.60,
    "囚": 0.40,
    "死": 0.20,
}

# Visible (transparent) heavenly stem multipliers: raised floors for 囚 and 死.
# 死 means "weakened", not "eliminated" — a transparent stem retains minimum
# presence regardless of season. Hierarchy strictly preserved:
#   旺 1.00 > 相 0.80 > 休 0.60 > 囚 0.50 > 死 0.40
VISIBLE_STEM_MULT: Dict[str, float] = {
    "旺": 1.00,
    "相": 0.80,
    "休": 0.60,
    "囚": 0.50,
    "死": 0.40,
}


@dataclass
class SeasonalFactors:
    season: str
    states: Dict[Element, str]

    def mult(self, element: Element) -> float:
        """Seasonal multiplier for hidden stems — full range 0.20 to 1.00."""
        return STATE_MULT.get(self.states.get(element, "囚"), 0.40)

    def mult_visible(self, element: Element) -> float:
        """
        Seasonal multiplier for a *visible* (transparent) heavenly stem.
        Uses raised floors for 死 (0.40) and 囚 (0.50) to prevent near-elimination
        of a stem that is explicitly present in the heavenly position.
        """
        return VISIBLE_STEM_MULT.get(self.states.get(element, "囚"), 0.50)


_SPRING_BRANCHES = frozenset({Branch.YIN, Branch.MAO, Branch.CHEN})
_SUMMER_BRANCHES = frozenset({Branch.SI, Branch.WU, Branch.WEI})
_AUTUMN_BRANCHES = frozenset({Branch.SHEN, Branch.YOU, Branch.XU})


def get_seasonal_factors(month_branch: Branch) -> SeasonalFactors:
    """
    Map month branch → SeasonalFactors for all five elements.

    Seasons are determined by frozenset membership:
      春 (spring): 寅卯辰  夏 (summer): 巳午未
      秋 (autumn): 申酉戌  冬 (winter): 亥子丑
    Returns a SeasonalFactors with the season name and the element-state dict
    drawn from _SEASONAL_TABLE, used by both hidden-stem (mult) and visible-stem
    (mult_visible) scoring paths.
    """
    if month_branch in _SPRING_BRANCHES:
        season = "spring"
    elif month_branch in _SUMMER_BRANCHES:
        season = "summer"
    elif month_branch in _AUTUMN_BRANCHES:
        season = "autumn"
    else:
        season = "winter"
    return SeasonalFactors(season=season, states=_SEASONAL_TABLE[season])


# ─────────────────────────────────────────────
# Climate temperature buckets for branch-level categorization
# ─────────────────────────────────────────────

# Branch temperature tendency (qualitative)
# Standardized to 5 categories: very_cold, cold, neutral, warm, hot
BRANCH_TEMP_QUAL = {
    Branch.ZI: "very_cold",  # Water, mid-winter
    Branch.HAI: "cold",  # Water, late autumn (cooler but not as cold as Zi)
    Branch.CHOU: "neutral",  # Earth, late winter (transitional)
    Branch.YIN: "warm",  # Wood, early spring
    Branch.MAO: "warm",  # Wood, spring equinox
    Branch.CHEN: "neutral",  # Earth, late spring
    Branch.SI: "warm",  # Fire, early summer (though sometimes considered hot)
    Branch.WU: "hot",  # Fire, midsummer
    Branch.WEI: "neutral",  # Earth, late summer
    Branch.SHEN: "cold",  # Metal, early autumn
    Branch.YOU: "cold",  # Metal, autumn equinox
    Branch.XU: "neutral",  # Earth, late autumn
}

# Sub-season labels: month branch → precise 孟/仲/季 term
SUB_SEASON: Dict[Branch, str] = {
    Branch.YIN: "孟春 (木旺之季)",
    Branch.MAO: "仲春 (木旺之季)",
    Branch.CHEN: "季春 (木旺之季)",
    Branch.SI: "孟夏 (火旺之季)",
    Branch.WU: "仲夏 (火旺之季)",
    Branch.WEI: "季夏 (火旺之季)",
    Branch.SHEN: "孟秋 (金旺之季)",
    Branch.YOU: "仲秋 (金旺之季)",
    Branch.XU: "季秋 (金旺之季)",
    Branch.HAI: "孟冬 (水旺之季)",
    Branch.ZI: "仲冬 (水旺之季)",
    Branch.CHOU: "季冬 (水旺之季)",
}

TEMP_SCORE = {
    "very_cold": -2.0,
    "cold": -0.75,
    "neutral": 0,
    "warm": 0.75,
    "hot": 2.0,
}

# Discrete climate multiplier tables per element
# Index: chart temperature score bucket
# Consistent ±8% range for Fire/Water (inverse sensitivity)
# Consistent ±4% range for Wood/Metal/Earth (moderate sensitivity)
CLIMATE_MULT: Dict[Element, Dict[str, float]] = {
    Element.FIRE: {
        "very_cold": 0.70,
        "cold": 0.85,
        "neutral": 1.00,
        "warm": 1.15,
        "hot": 1.30,
    },
    Element.WATER: {
        "very_cold": 1.30,
        "cold": 1.15,
        "neutral": 1.00,
        "warm": 0.85,
        "hot": 0.70,
    },
    Element.WOOD: {
        "very_cold": 0.92,
        "cold": 0.96,
        "neutral": 1.00,
        "warm": 1.04,
        "hot": 1.08,
    },
    Element.METAL: {
        "very_cold": 1.08,
        "cold": 1.04,
        "neutral": 1.00,
        "warm": 0.96,
        "hot": 0.92,
    },
    Element.EARTH: {
        "very_cold": 0.92,
        "cold": 0.96,
        "neutral": 1.00,
        "warm": 1.04,
        "hot": 1.08,
    },
}


def get_chart_climate(pillars: List["Pillar"]) -> Tuple[str, float]:
    """Compute weighted average temperature score and return (category, score)."""
    total_score = 0.0
    total_weight = 0.0
    for p in pillars:
        if p.branch:
            q = BRANCH_TEMP_QUAL.get(p.branch, "neutral")
            total_score += TEMP_SCORE[q] * p.position_weight
            total_weight += p.position_weight
    avg = total_score / total_weight if total_weight else 0
    if avg <= -2.0:
        return "very_cold", round(avg, 2)
    elif avg <= -0.75:
        return "cold", round(avg, 2)
    elif avg <= 0:
        return "neutral", round(avg, 2)
    elif avg <= 0.75:
        return "warm", round(avg, 2)
    else:
        return "hot", round(avg, 2)


def climate_mult(element: Element, climate: str) -> float:
    return CLIMATE_MULT[element][climate]


# ─────────────────────────────────────────────
# Dominant Qi Momentum (主导气势) calculation
# ─────────────────────────────────────────────

# Five Elements generating cycle (生):
# Wood → Fire → Earth → Metal → Water → Wood
ELEMENT_GENERATES: Dict[Element, Element] = {
    Element.WOOD: Element.FIRE,
    Element.FIRE: Element.EARTH,
    Element.EARTH: Element.METAL,
    Element.METAL: Element.WATER,
    Element.WATER: Element.WOOD,
}

# Five Elements overcoming cycle (克):
# Wood ⊕ Earth, Fire ⊕ Metal, Earth ⊕ Water, Metal ⊕ Wood, Water ⊕ Fire
ELEMENT_OVERCOMES: Dict[Element, Element] = {
    Element.WOOD: Element.EARTH,
    Element.FIRE: Element.METAL,
    Element.EARTH: Element.WATER,
    Element.METAL: Element.WOOD,
    Element.WATER: Element.FIRE,
}


def get_zhu_dao_qi_shi(stem_element: Element, branch_element: Element) -> str:
    """
    Calculate 主导气势 (Dominant Qi Momentum) based on stem-branch elemental relationship.

    The relationship can be one of five types:
        - 比和 (Bǐ Hé): Stem and branch are the same element (Pure, concentrated energy)
        - 盖头 (Gài Tóu): Stem overcomes branch (Top controls Bottom)
        - 截脚 (Jié Jiǎo): Branch overcomes stem (Bottom destabilizes Top)
        - 天生地 (Tiān Shēng Dì): Stem generates branch (Energy leaks downward)
        - 地生天 (Dì Shēng Tiān): Branch generates stem (Strong foundation)

    Args:
        stem_element: Element enum for the heavenly stem
        branch_element: Element enum for the earthly branch

    Returns:
        str: Description of the relationship, e.g., "盖头 (木克土)"
    """
    # Same element
    if stem_element == branch_element:
        return f"比和 ({stem_element.value}气通根)"

    # Stem generates branch
    if ELEMENT_GENERATES.get(stem_element) == branch_element:
        return f"天生地 ({stem_element.value}生{branch_element.value})"

    # Branch generates stem
    if ELEMENT_GENERATES.get(branch_element) == stem_element:
        return f"地生天 ({branch_element.value}生{stem_element.value})"

    # Stem overcomes branch
    if ELEMENT_OVERCOMES.get(stem_element) == branch_element:
        return f"盖头 ({stem_element.value}克{branch_element.value})"

    # Branch overcomes stem
    if ELEMENT_OVERCOMES.get(branch_element) == stem_element:
        return f"截脚 ({branch_element.value}克{stem_element.value})"

    return "未知关系"


def get_wu_xing_tier(percentage: float) -> Dict[str, str]:
    """
    Categorize Five Elements percentage into a tier with contextual description.

    Tiers (ordered by energy intensity):
    - 缺失 (Absent): 0%
    - 极弱 (Critical Deficit): 0.1% - 10%
    - 偏弱 (Subdued): 10.1% - 20%
    - 中和 (Balanced): 20.1% - 35%
    - 偏旺 (Robust): 35.1% - 50%
    - 极旺 (Overwhelming): 50.1% - 70%
    - 极亢 (Absolute Monopoly): > 70%

    Args:
        percentage: Float value representing the element's percentage of total power

    Returns:
        dict: Tier information with name, range, state description, and core advice
    """
    if percentage == 0:
        return {
            "名称": "缺失",
            "范围": "0%",
            "状态描述": "绝对真空，物质缺失。该谱线能量在系统演化中完全缺失，缺乏相应的物理机制支持。",
            "核心建议": '外部引力，人工介入。本系统无法自发产生此项能量。需通过外部环境的"引力摄动"或特定的后天参数注入，方能补足该维度的缺失。',
        }
    elif percentage <= 10:
        return {
            "名称": "极弱",
            "范围": "0.01% - 10%",
            "状态描述": "热寂边缘，能量脉冲微弱。能量丰度极低，处于核聚变熄灭的边缘，极易被主星风暴吞噬。",
            "核心建议": '精密维护，防止坍缩。此为系统中最脆弱的反馈回路。必须严格限制外界对该能量的消耗（克泄），通过低熵环境进行定向"光泵浦"增益，维系其微弱的运行。',
        }
    elif percentage <= 20:
        return {
            "名称": "偏弱",
            "范围": "10.01% - 20%",
            "状态描述": "轨道不稳，能量辐射受限。虽有物质基础，但质量不足以形成稳恒的自持反应，处于系统的边缘地带。",
            "核心建议": "轨道提升，质能累积。不建议承担高强度的系统负荷。需通过同频率的能量共振（生扶）来增加其质量密度，逐步将其推向核心环绕轨道。",
        }
    elif percentage <= 35:
        return {
            "名称": "中和",
            "范围": "20.01% - 35%",
            "状态描述": "稳恒态演化，动态平衡。系统熵增率处于理想区间，能量转换效率极高且具备极强的自修复能力。",
            "核心建议": "参数锁死，惯性运行。这是系统演化的最佳黄金期。避免大幅度的参数扰动，维持现有的动态平衡，确保系统的长周期稳定运行。",
        }
    elif percentage <= 50:
        return {
            "名称": "偏旺",
            "范围": "35.01% - 50%",
            "状态描述": "活跃恒星，热核反应激增。该项能量已成为系统的主要引力源，释放出强烈的能量辐射，并开始干扰其他弱能级轨道。",
            "核心建议": "能量泄压，负载均衡。系统输出已过载。宜通过高效的能量转换界面（泄）或逆向热力学补偿（耗）来分散其压力，防止核心因能量过剩导致热失控。",
        }
    elif percentage <= 70:
        return {
            "名称": "极旺",
            "范围": "50.01% - 70%",
            "状态描述": "引力坍缩，黑洞效应初现。能量丰度已达到临界点，形成极强的引力陷阱，系统正被该单一变量强行锁定，面临失衡风险。",
            "核心建议": "紧急降维，广域排干。严禁任何形式的能量注资。必须建立大容量的泄流管道，将过剩的能量强行传导至外部耗散层，以缓解核心区域巨大的压强。",
        }
    else:
        return {
            "名称": "极亢",
            "范围": "> 70%",
            "状态描述": "奇点降临，时空曲率极限。该能量已彻底统治整个物理场。系统规律已被重写，传统力学平衡逻辑彻底失效。",
            "核心建议": '顺应奇点，整体同步。当能量达到绝对垄断时，任何对抗尝试都会导致系统瞬间瓦解。最优策略是顺从该能量的流动矢向，让系统整体进入"单极演化"模式。',
        }


def get_all_wu_xing_tiers() -> Dict[str, Dict[str, str]]:
    """
    Return all seven tiers of the Wu Xing contextual system as a reference.

    Representative percentages are chosen from the middle of each tier's range
    to generate tier information for all seven tiers:
    - 缺失:  0%
    - 极弱:  0.1% - 10%   (representative: 5%)
    - 偏弱:  10.1% - 20%  (representative: 15%)
    - 中和:  20.1% - 35%  (representative: 25%)
    - 偏旺:  35.1% - 50%  (representative: 40%)
    - 极旺:  50.1% - 70%  (representative: 60%)
    - 极亢:  > 70%        (representative: 75%)

    Returns:
        dict: Dictionary of all tiers keyed by tier name, with full tier information
    """
    tiers = {}
    # Use representative percentages from the middle of each tier's range
    tier_specs = [
        0,  # 缺失: 0%
        5,  # 极弱: 0.1% - 10%
        15,  # 偏弱: 10.1% - 20%
        25,  # 中和: 20.1% - 35%
        40,  # 偏旺: 35.1% - 50%
        60,  # 极旺: 50.1% - 70%
        75,  # 极亢: > 70%
    ]
    for pct in tier_specs:
        tier_info = get_wu_xing_tier(pct)
        tiers[tier_info["名称"]] = tier_info
    return tiers




# ─────────────────────────────────────────────
# Pillar dataclass
# ─────────────────────────────────────────────


@dataclass
class Pillar:
    position: str  # "year" | "month" | "day" | "hour"
    label: str  # Chinese display label: "年" | "月" | "日" | "时"
    position_weight: float
    stem_weight: float
    stem: Optional[Stem]
    branch: Optional[Branch]


# ─────────────────────────────────────────────
# String → Enum helpers
# ─────────────────────────────────────────────

STR_STEM = {s.value: s for s in Stem}
STR_BRANCH = {b.value: b for b in Branch}

_YANG_STEMS: frozenset = frozenset({"甲", "丙", "戊", "庚", "壬"})

_STATE_DESCRIPTIONS: dict = {
    "旺": "旺 (最强)",
    "相": "相 (次强)",
    "囚": "囚 (弱)",
    "休": "休 (气弱)",
    "死": "死 (极弱)",
}

_CLIMATE_DESCRIPTIONS: dict = {
    "very_cold": "极寒",
    "cold": "寒冷",
    "neutral": "常温",
    "warm": "温暖",
    "hot": "炎热",
}

_ROOT_LABELS: tuple = ("本气根", "中气根", "余气根")

_STR_TO_ELEM: dict = {e.value: e for e in Element}

_SEASONAL_TABLE: dict = {
    "spring": {
        Element.WOOD: "旺",
        Element.FIRE: "相",
        Element.EARTH: "死",
        Element.METAL: "囚",
        Element.WATER: "休",
    },
    "summer": {
        Element.WOOD: "休",
        Element.FIRE: "旺",
        Element.EARTH: "相",
        Element.METAL: "死",
        Element.WATER: "囚",
    },
    "autumn": {
        Element.WOOD: "死",
        Element.FIRE: "囚",
        Element.EARTH: "休",
        Element.METAL: "旺",
        Element.WATER: "相",
    },
    "winter": {
        Element.WOOD: "相",
        Element.FIRE: "死",
        Element.EARTH: "囚",
        Element.METAL: "休",
        Element.WATER: "旺",
    },
}


# ─────────────────────────────────────────────
# Main calculator
# ─────────────────────────────────────────────
class WuXingDynamicsCalculator:
    """
    Five Elements dynamics calculator following 三命通会 classical methodology.

    Weight architecture (total ~1.10):
      Branch hidden stems: year=0.15, month=0.45, day=0.25, hour=0.15  (sum=1.00)
      Heavenly stems:      year=0.015, month=0.045, day=0.025, hour=0.015 (sum=0.10)
      Combinations:        additive bonus on top (small)

    Stem weights mirror branch weight ratios so that the month stem (月干)
    carries proportionally more authority than year/hour stems, consistent
    with classical 月令 doctrine.

    Interaction base constants (scaled by total_w × multiplier):
      _BASE_TIAN_GAN_HE = 0.25  — direct 天干合 transformation bonus
      _BASE_GAN_ZHI_HE  = 0.10  — 干支透合 covert bond (weaker; stem bonds with
                                   hidden stem rather than another visible stem)
      Other constants (_BASE_SAN_HUI, _BASE_SAN_HE, etc.) follow classical calibration
      so that a month-inclusive triplet (total_w ≈ 0.85) reproduces reference values.

    天干合 rooting modulation (see _score_priority_results):
      combo_factor = min(r_mults) / r_深根   — scales bonus by weaker stem's rooting
      per_stem_retain = 0.70 + 0.30*(1-commitment)
        深根 (commitment=1.0) → retain=0.70 (fully bound; largest power reduction)
        无根 (commitment=0.0) → retain=1.00 (bond doesn't hold; no reduction)
      This compounds with Pass S 强度 downgrade from natal/cycle_interactions.

    通根 rooting multipliers (STEP 2 heavenly stems only):
      深根→×1.30, 中根→×1.18, 浅根→×1.08, 无根→×1.00
      Precomputed once per distinct element via tong_gen_cache in calculate().
    """

    # Single source of truth for all positional weights
    POSITION_WEIGHTS = {"year": 0.15, "month": 0.45, "day": 0.25, "hour": 0.15}

    # Xun kong void factor: void branch hidden stems retain 50% power
    _XUN_KONG_VOID_FACTOR = 0.50

    # Heavenly stem weights mirror branch positional weights to reflect their authority
    # Month stem (月干) carries greater weight closer to 月令 (Seasonal Command)
    # Ratio: year:month:day:hour = 0.15:0.45:0.25:0.15 → scaled to sum=0.10
    STEM_WEIGHTS = {"year": 0.015, "month": 0.045, "day": 0.025, "hour": 0.015}

    # ── Additive bonus base factors ───────────────────────────────────────────
    # Used in _score_priority_results. All scaled by total_w (sum of participating
    # pillar weights) and the priority multiplier, so heavy-pillar combinations
    # earn proportionally more bonus.
    # 三会/三合 calibrated so a month-inclusive triplet (total_w ≈ 0.85) reproduces
    # the classical reference values (三会 ≈ 0.25, 三合 ≈ 0.20).
    _BASE_SAN_HUI = 0.30  # 三会  directional combination
    _BASE_SAN_HE = 0.24  # 三合  three-harmony full triplet
    _BASE_BAN_HE_HUB = 0.15  # 半合  with hub branch present
    _BASE_BAN_HE_NO_HUB = 0.08  # 半合  without hub (拱合 style)
    _BASE_LIU_HE = 0.06  # 六合  branch-pair combination
    _BASE_BI_HE = 0.03  # 比和  same-element pairing
    _BASE_GONG = 0.04  # 共拱/拱会/残会  indirect harmonies
    _BASE_TIAN_GAN_HE = 0.25  # 天干合  transformed-element bonus
    _BASE_GAN_ZHI_HE = 0.10  # 干支透合 covert bond — weaker than direct 天干合

    # ── 天干合 stem binding ────────────────────────────────────────────────────
    # Bound stems are preoccupied (合而不化) and output only this fraction of
    # their original elemental power. At multiplier=0 (消融吸收) the formula
    # 1-(1-RETAIN)*0 = 1.0 means no reduction, modelling 贪合忘冲 correctly.
    _RETAIN_TIAN_GAN_HE = 0.70

    # ── Branch reduction base factors ─────────────────────────────────────────
    # All reductions follow: actual_factor = 1 - (1 - base) * multiplier.
    # At multiplier=0 (消融吸收) no reduction is applied regardless of base.
    _REDUCE_CLASH_DOMINANT = 0.80  # 六冲: stronger branch (ratio > _RATIO_CLASH_HIGH)
    _REDUCE_CLASH_SUBDUED = 0.40  # 六冲: weaker branch
    _REDUCE_CLASH_BALANCED = 0.65  # 六冲: balanced clash (both sides equal)
    _RATIO_CLASH_HIGH = 1.20  # strength ratio above this → asymmetric clash
    _RATIO_CLASH_LOW = 0.833  # reciprocal of HIGH; below → reversed asymmetric
    _REDUCE_SAN_XING_FULL = 0.75  # 三刑: all three branches present
    _REDUCE_SAN_XING_PARTIAL = 0.85  # 三刑: only two of three present
    _REDUCE_XIANG_XING = 0.85  # 相刑/无礼之刑 (子卯)
    _REDUCE_ZI_XING = 0.92  # 自刑: same branch repeated — mildest punishment
    _REDUCE_LIU_PO = 0.88  # 六破
    _REDUCE_LIU_HAI = 0.90  # 六害

    # ── 通根 rooting multipliers (applied to stem STEP 2 only) ────────────────
    _ROOTING_MULTIPLIERS: Dict[str, float] = {
        "深根": 1.30,
        "中根": 1.18,
        "浅根": 1.08,
        "无根": 1.00,
    }

    @staticmethod
    def _compute_tong_gen(
        stem_elem: Element,
        pillars: List[Pillar],
    ) -> Union[Dict[str, str], str]:
        """
        Compute 通根 for a stem element across all four pillar branches.

        Matching is element-level (e.g. 甲 roots wherever 木 is present, including 乙
        hidden stems), consistent with classical 通根 doctrine.

        Returns a dict mapping pillar labels → root strength label
        (e.g. {"月": "本气根", "时": "余气根"}), or the string "无根" if no
        root is found in any branch.
        """
        results: Dict[str, str] = {}
        for p in pillars:
            if p.branch:
                for idx, (hidden_stem, _) in enumerate(BRANCH_HIDDEN.get(p.branch, [])):
                    if STEM_ELEMENT[hidden_stem] == stem_elem and idx < len(
                        _ROOT_LABELS
                    ):
                        results[p.label] = _ROOT_LABELS[idx]
                        break
        return results if results else "无根"

    def calculate(
        self,
        pillars: List[Pillar],
        priority_list: list,
        seasonal: Optional["SeasonalFactors"] = None,
        xun_kong_reductions: dict | None = None,
    ) -> Dict:
        """
        Compute Five Elements dynamics and return a structured result dict.

        Args:
            pillars: Four BaZi Pillar objects (year, month, day, hour). In cycle
                overlay mode callers may pass natal + cycle pillars.
            priority_list: Priority-resolved interaction list from
                apply_bazi_master_priority() (or apply_cycle_master_priority()).
                Ensures correct priority logic (贪合忘冲, 三会>三合, etc.) before
                numeric scoring.
            seasonal: Pre-computed SeasonalFactors. If omitted, derived from the
                month-position pillar in ``pillars`` (natal-only case). Callers
                such as cycle_wu_xing should pass the *natal* month's seasonal
                factors explicitly so that elemental season is anchored to the
                birth chart, not the cycle pillar's branch.

        Returns:
            dict with keys:
                "基本信息"       — 日主 details (stem, element, yin/yang, 旺衰,
                                   十二长生, 通根) and 出生季节 sub-season label
                "四柱"           — per-pillar details (天干, 地支, 季节状态,
                                   十二长生, 通根, 干支五行, 藏干)
                "五行力量分析"   — per-element dict with 百分比, 旺衰, 能级 tier
                "组合加成"       — combination bonus interactions (三会/三合/半合 etc.)
                "六合加成"       — 六合 pair interactions
                "相冲减损"       — 六冲 clash interactions
                "刑减损"         — 三刑/无礼之刑/自刑 interactions
                "害减损"         — 六害 interactions
                "破减损"         — 六破 interactions

        Implementation notes:
            - 通根 is precomputed once per distinct element via tong_gen_cache before
              building 基本信息 and 四柱, avoiding redundant branch searches when
              multiple pillars share the same stem element.
            - 旬空 reductions (xun_kong_reductions) are applied multiplicatively to
              branch hidden stem power in STEP 1 only; stem power (STEP 2) is unaffected.

        Raises:
            ValueError: if seasonal is not provided and no month pillar with a
                branch is found in pillars.
        """
        month_pillar = next((p for p in pillars if p.position == "month"), None)
        if seasonal is None:
            if not month_pillar or not month_pillar.branch:
                raise ValueError("Month pillar with branch is required.")
            seasonal = get_seasonal_factors(month_pillar.branch)

        climate, climate_score = get_chart_climate(pillars)

        combo_bonus, branch_reductions, stem_reductions = self._score_priority_results(
            priority_list, pillars, seasonal
        )

        power = {e: 0.0 for e in Element}

        # ── Rooting tiers (通根) — delegates to natal_interactions ────────
        _zhis = [q.branch.value for q in pillars if q.branch]
        rooting_tiers: Dict[str, str] = {
            p.label: get_stem_root_tier(STEM_ELEMENT[p.stem].value, _zhis)
            for p in pillars if p.stem
        }

        # ── STEP 1: Branch hidden stems ──────────────────────────────────
        for p in pillars:
            if not p.branch:
                continue
            reduction = branch_reductions.get(p.branch, 1.0)
            xk_factor = (
                xun_kong_reductions.get(p.position, 1.0) if xun_kong_reductions else 1.0
            )
            base_w = p.position_weight * reduction * xk_factor

            for hidden_stem, depth in BRANCH_HIDDEN[p.branch]:
                elem = STEM_ELEMENT[hidden_stem]
                s_mult = seasonal.mult(elem)
                c_mult = climate_mult(elem, climate)
                # Apply 十二长生 (12-stage life cycle) to every hidden stem
                sw_mult = get_shengwang_mult(hidden_stem, p.branch)

                hidden_power = base_w * depth * s_mult * c_mult * sw_mult
                power[elem] += hidden_power

        # ── STEP 2: Heavenly stems ───────────────────────────────────────
        # Visible (transparent) stems use mult_visible() which applies a seasonal floor
        # to ensure weak elements retain minimum presence. Position-sensitive weights
        # reflect the month stem’s greater authority near the 月令 (Seasonal Command).

        for p in pillars:
            if not p.stem:
                continue
            elem = STEM_ELEMENT[p.stem]
            s_mult = seasonal.mult_visible(elem)
            c_mult = climate_mult(elem, climate)
            sw_mult = get_shengwang_mult(p.stem, p.branch) if p.branch else 1.0
            stem_w = p.stem_weight
            stem_reduction = stem_reductions.get(p.stem, 1.0)
            r_mult = self._ROOTING_MULTIPLIERS.get(rooting_tiers.get(p.label, "无根"), 1.00)

            stem_power = stem_w * s_mult * c_mult * sw_mult * stem_reduction * r_mult
            power[elem] += stem_power

        # ── STEP 3: Combination bonuses ─────────────────────────────────
        for elem, bonus in combo_bonus.items():
            power[elem] += bonus

        # Seasonal floor for visible stems is applied via mult_visible() multiplier

        # ── STEP 4: Percentages ──────────────────────────────────────────
        total = sum(power.values())
        percentages = (
            {e.value: round(v / total * 100, 2) for e, v in power.items()}
            if total
            else {e.value: 0.0 for e in Element}
        )

        # Precompute 通根 once per distinct element — reused for 日主 and all si_zhu pillars
        tong_gen_cache = {
            STEM_ELEMENT[p.stem]: self._compute_tong_gen(STEM_ELEMENT[p.stem], pillars)
            for p in pillars if p.stem
        }

        # Building 基本信息 (Basic Information)
        day_pillar = next((p for p in pillars if p.position == "day"), None)
        day_master = ""
        if day_pillar and day_pillar.stem:
            stem_val = day_pillar.stem.value
            elem = STEM_ELEMENT[day_pillar.stem]
            # Determine if stem is Yang (甲丙戊庚壬) or Yin (乙丁己辛癸)
            yang_yin = "阳" if stem_val in _YANG_STEMS else "阴"

            # Calculate 旺衰 (seasonal strength)
            dm_state = _STATE_DESCRIPTIONS.get(seasonal.states.get(elem, "囚"), "未知")

            # Calculate 十二长生 (12-stage life cycle)
            dm_stage = (
                SHENG_WANG_TABLE.get(day_pillar.stem, {}).get(day_pillar.branch)
                if day_pillar.branch
                else None
            )

            # Calculate 通根 (root connection) — element-level search across all branches
            tong_gen = tong_gen_cache[elem]

            day_master = {
                "显示名称": f"{stem_val}{elem.value} ({yang_yin}{elem.value})",
                "天干": stem_val,
                "五行": elem.value,
                "阴阳": yang_yin,
                "旺衰": dm_state,
                "十二长生": dm_stage,
                "通根": tong_gen,
            }

        # Map month branch to precise sub-season term (孟/仲/季)
        birth_season = (
            SUB_SEASON.get(month_pillar.branch, "")
            if month_pillar and month_pillar.branch
            else ""
        )

        # Assemble the final result structure. Commented out climate characteristics for now, can be re-enabled if needed.
        basic_info = {
            "日主": day_master,
            "出生季节": birth_season,
            # "气候特征": _CLIMATE_DESCRIPTIONS.get(climate, climate),
        }

        # Build unified pillar dict: 年柱/月柱/日柱/时柱
        si_zhu = {}
        for p in pillars:
            pillar_key = _POSITION_TO_PILLAR_CN.get(p.position)
            if not pillar_key or not p.stem:
                continue
            stem_elem = STEM_ELEMENT[p.stem]
            state = seasonal.states.get(stem_elem, "囚")
            state_desc = _STATE_DESCRIPTIONS.get(state, state)
            sheng_wang_stage = (
                SHENG_WANG_TABLE.get(p.stem, {}).get(p.branch) if p.branch else None
            )

            # 通根: element-level search across all branches
            tong_gen = tong_gen_cache[stem_elem]

            # 干支五行
            branch_elem = BRANCH_ELEMENT.get(p.branch) if p.branch else None
            wu_xing_info = {
                "天干五行": stem_elem.value,
                "地支五行": branch_elem.value if branch_elem else None,
                "主导气势": (
                    get_zhu_dao_qi_shi(stem_elem, branch_elem) if branch_elem else None
                ),
            }

            # 藏干: hidden stems with strength category
            cang_gan = []
            if p.branch:
                for idx, (hs, _) in enumerate(BRANCH_HIDDEN.get(p.branch, [])):
                    strength = _ROOT_LABELS[idx] if idx < len(_ROOT_LABELS) else "未知"
                    cang_gan.append({"干": hs.value, "强度": strength})

            si_zhu[pillar_key] = {
                "天干": p.stem.value,
                "地支": p.branch.value if p.branch else None,
                "季节状态": state_desc,
                "十二长生": sheng_wang_stage,
                "通根": tong_gen,
                "干支五行": wu_xing_info,
                "藏干": cang_gan,
            }

        # Build the new "五行力量分析" structure with tiered context
        wu_xing_analysis = {}
        for elem in Element:
            elem_name = elem.value
            pct = percentages.get(elem_name, 0)
            state = seasonal.states.get(elem, "囚")
            state_desc = _STATE_DESCRIPTIONS.get(state, state)
            tier_info = get_wu_xing_tier(pct)
            wu_xing_analysis[elem_name] = {
                "百分比": round(pct, 2) if isinstance(pct, (int, float)) else pct,
                "旺衰": state_desc,
                "能级": tier_info,
            }

        interactions_display = self._build_interactions_display(priority_list)

        return {
            "基本信息": basic_info,
            "四柱": si_zhu,
            "五行力量分析": wu_xing_analysis,
            **interactions_display,
        }

    # ─── helpers ──────────────────────────────────────────────

    # ─── priority-list-based scoring ─────────────────────────────

    def _score_priority_results(
        self,
        priority_list: list,
        pillars: List[Pillar],
        seasonal: Optional["SeasonalFactors"],
    ) -> Tuple[Dict[Element, float], Dict[Branch, float], Dict["Stem", float]]:
        """
        Convert a priority-resolved interaction list into numeric scoring.

        This method processes all 16 interaction types, with 13 actively scored and 3 excluded:

        SCORED INTERACTIONS (13 types):
        ─────────────────────────────
        TIER 1 (Structural):
            • 三会 (三-meet): Directional element bonus (方位 → element)
            • 三合 (三-harmony): Elemental triad bonus (元素)
            • 六冲 (六-clash): Strength-ratio based reduction (dominant/balanced/subdued)
            • 六合 (六-harmony): Synthesis element bonus (元素)

        TIER 2 (Operational):
            • 共拱 (co-arching): Element bonus (元素) — merged with 拱会/残会 branch
            • 比和 (peer): Peer element bonus (元素)
            • 拱会 (structural arch): Inherited element from 三会 (元素)
            • 残会 (residual): Direction-based bonus from 三会 (方位)
            • 半合 (half-harmony): Conditional element bonus with 邀出 logic (元素)
            • 天干合 (stem combine): Rooting-scaled bonus + per-stem retention:
                combo_factor = min(r_mults) / r_深根   — weaker stem limits the bond
                per_stem_retain = 0.70 + 0.30*(1−commitment)
                  深根→0.70 (fully committed), 无根→1.00 (bond doesn't hold)
                combo_bonus[elem] += total_stem_w × _BASE_TIAN_GAN_HE × multiplier × combo_factor
            • 干支透合 (stem-branch transparency): Covert bond bonus via _BASE_GAN_ZHI_HE=0.10
                combo_bonus[elem] += total_w × _BASE_GAN_ZHI_HE × multiplier
                Source stem gets fixed retention=0.70 (贪合忘冲; no rooting modulation)

        TIER 3 (Frictional):
            • 三刑 (三-punishment): Full/partial penalty reduction
            • 无礼之刑 (uncivilized): Mutual harm reduction
            • 自刑 (self-punishment): Mild reduction
            • 六害 (六-harm): Harm relationship reduction
            • 六破 (六-break): Break relationship reduction

        NOT SCORED (3 types) — By Classical BaZi Methodology:
        ─────────────────────────────────────────────────
            • 暗合 (secret harmony): Hidden stem harmony; no elemental synthesis
              → Contextually informative only; does NOT change elemental composition
            • 天干克 (stem control): Control direction only (顺克/逆克); no power transform
              → Directional indicator only; does NOT contribute to 五行力量
            • 天干冲 (stem clash): Pure opposition; no elemental synthesis
              → Informational only; does NOT alter elemental balance

        Returns:
            combo_bonus       — additive element bonuses (Dict[Element, float])
            branch_reductions — multiplicative reduction factors per branch (Dict[Branch, float])
                                贪合忘冲: 消融吸收 multiplier=0 → factor=1.0, no reduction applied
            stem_reductions   — multiplicative reduction factors per stem (Dict[Stem, float])
                                天干合/干支透合 bind stems, weakening their original element output.
                                For 天干合: factor varies by rooting (深根→larger reduction,
                                无根→no reduction). For 干支透合: fixed retention=0.70.
        """
        # Build branch-value → (Branch enum, position_weight) lookup.
        # Using branch values (not position names) makes this work for both natal
        # charts ("年柱"/"月柱"/…) and cycle interactions ("大运柱"/"流年柱"/…).
        branch_val_map: Dict[str, Tuple["Branch", float]] = {}
        stem_val_map: Dict[str, float] = {}  # stem char → position_weight
        for p in pillars:
            if p.branch:
                val = p.branch.value
                existing_w = branch_val_map[val][1] if val in branch_val_map else 0.0
                branch_val_map[val] = (p.branch, existing_w + p.position_weight)
            if p.stem:
                val = p.stem.value
                stem_val_map[val] = stem_val_map.get(val, 0.0) + p.position_weight

        def branch_strength(b: "Branch") -> float:
            if seasonal is None:
                return 0.0
            total_w = sum(x.position_weight for x in pillars if x.branch == b)
            if total_w == 0.0:
                return 0.0
            weighted_seasonal = sum(
                depth * seasonal.mult(STEM_ELEMENT[stem]) * get_shengwang_mult(stem, b)
                for stem, depth in BRANCH_HIDDEN[b]
            )
            return total_w * weighted_seasonal

        combo_bonus: Dict[Element, float] = {e: 0.0 for e in Element}
        branch_reductions: Dict[Branch, float] = {}
        stem_reductions: Dict[Stem, float] = {}

        for item in priority_list:
            itype: str = item.get("类型", "")
            strength_label: str = item.get("强度", "强势主流")
            multiplier: float = INTERACTION_STRENGTH_MULTIPLIER.get(
                strength_label, 1.00
            )

            # Resolve participating branches and total positional weight via branch value matching.
            # This is position-name-agnostic: works for natal ("年柱") and cycle ("大运柱") alike.
            combo_detail: dict = item.get("组合明细", {})
            participating: List[Tuple["Branch", float]] = []
            seen_branches: set = set()
            for branch_val in combo_detail.values():
                entry = branch_val_map.get(branch_val)
                if (
                    entry and entry[0] not in seen_branches
                ):  # Avoid duplicates (e.g., 自刑: 午午)
                    participating.append(entry)
                    seen_branches.add(entry[0])
            total_w = sum(w for _, w in participating)
            branches_present = [b for b, _ in participating]

            # ── Additive bonuses ──────────────────────────────────
            if itype == "三会":
                elem = _STR_TO_ELEM.get(item.get("元素", ""))
                if elem and total_w > 0:
                    combo_bonus[elem] += total_w * self._BASE_SAN_HUI * multiplier

            elif itype == "三合":
                elem = _STR_TO_ELEM.get(item.get("元素", ""))
                if elem and total_w > 0:
                    combo_bonus[elem] += total_w * self._BASE_SAN_HE * multiplier

            elif itype == "半合":
                elem = _STR_TO_ELEM.get(item.get("元素", ""))
                if elem:
                    # 邀出 == "无" means cardinal hub branch IS present → stronger half-harmony
                    base = (
                        self._BASE_BAN_HE_HUB
                        if item.get("邀出") == "无"
                        else self._BASE_BAN_HE_NO_HUB
                    )
                    combo_bonus[elem] += total_w * base * multiplier

            elif itype == "六合":
                elem = _STR_TO_ELEM.get(item.get("元素", ""))
                if elem:
                    combo_bonus[elem] += total_w * self._BASE_LIU_HE * multiplier

            elif itype == "比和":
                elem = _STR_TO_ELEM.get(item.get("元素", ""))
                if elem:
                    combo_bonus[elem] += total_w * self._BASE_BI_HE * multiplier

            elif itype in ("共拱", "拱会", "残会"):
                elem = _STR_TO_ELEM.get(item.get("元素", ""))
                if elem:
                    combo_bonus[elem] += total_w * self._BASE_GONG * multiplier

            elif itype == "天干合":
                # 组合明细 contains stem characters, not branch characters.
                # Resolve weights from stem_val_map and transformed element from STEM_COMBINE_ELEMENT.
                stem_chars = list(combo_detail.values())
                total_stem_w = sum(stem_val_map.get(s, 0.0) for s in stem_chars)
                elem = STEM_COMBINE_ELEMENT.get(stem_chars[0]) if stem_chars else None

                # ── Rooting factor: scales transformation bonus by stem commitment ──
                # 根基 keys match 组合明细 keys (pillar labels → rooting tier).
                rooting = item.get("根基", {})
                r_mults = [
                    self._ROOTING_MULTIPLIERS.get(rooting.get(k, "无根"), 1.00)
                    for k in combo_detail.keys()
                ]
                # combo_factor: scales transformation bonus by the weaker stem's rooting
                combo_factor = min(r_mults) / self._ROOTING_MULTIPLIERS["深根"]

                if elem and total_stem_w > 0:
                    combo_bonus[elem] += (
                        total_stem_w * self._BASE_TIAN_GAN_HE * multiplier * combo_factor
                    )

                # ── Per-stem retention: more rooted → more committed → stronger reduction ──
                # commitment = (r - 1.0) / 0.30  → [0.0 (无根), 1.0 (深根)]
                # per_stem_retain = 0.70 + 0.30 * (1 - commitment)
                #   深根: retain=0.70 (fully committed, same as before)
                #   无根: retain=1.00 (not committed — bond doesn't hold)
                for k, s_char in combo_detail.items():
                    stem_enum = STR_STEM.get(s_char)
                    if stem_enum:
                        r = self._ROOTING_MULTIPLIERS.get(rooting.get(k, "无根"), 1.00)
                        commitment = (r - 1.00) / 0.30
                        per_stem_retain = self._RETAIN_TIAN_GAN_HE + (1.0 - self._RETAIN_TIAN_GAN_HE) * (1.0 - commitment)
                        f = 1.0 - (1.0 - per_stem_retain) * multiplier
                        stem_reductions[stem_enum] = (
                            stem_reductions.get(stem_enum, 1.0) * f
                        )

            elif itype == "干支透合":
                # Stem-branch covert combine — stem from one pillar bonds with hidden stem in another.
                # Provides a combine element bonus (合化五行), similar to 天干合.
                result_elem = item.get("合化五行", "")
                elem = _STR_TO_ELEM.get(result_elem) if result_elem else None
                if elem and total_w > 0:
                    combo_bonus[elem] += total_w * self._BASE_GAN_ZHI_HE * multiplier
                # Source stem is preoccupied (贪合忘冲) — apply same retention as 天干合.
                f = 1.0 - (1.0 - self._RETAIN_TIAN_GAN_HE) * multiplier
                for k, v in combo_detail.items():
                    if k.endswith("干"):
                        stem_enum = STR_STEM.get(v)
                        if stem_enum:
                            stem_reductions[stem_enum] = (
                                stem_reductions.get(stem_enum, 1.0) * f
                            )
                        break

            # ── Reductive factors ─────────────────────────────────
            # actual_factor = 1 - (1 - base_factor) × multiplier
            # When multiplier=0.00 (消融吸收): factor=1.0 → no reduction (贪合忘冲)

            elif itype == "六冲":
                if len(branches_present) == 2:
                    b1, b2 = branches_present[0], branches_present[1]
                    s1, s2 = branch_strength(b1), branch_strength(b2)
                    ratio = s1 / s2 if s2 > 0 else 1.0
                    if ratio > self._RATIO_CLASH_HIGH:
                        base_r1, base_r2 = (
                            self._REDUCE_CLASH_DOMINANT,
                            self._REDUCE_CLASH_SUBDUED,
                        )
                    elif ratio < self._RATIO_CLASH_LOW:
                        base_r1, base_r2 = (
                            self._REDUCE_CLASH_SUBDUED,
                            self._REDUCE_CLASH_DOMINANT,
                        )
                    else:
                        base_r1, base_r2 = (
                            self._REDUCE_CLASH_BALANCED,
                            self._REDUCE_CLASH_BALANCED,
                        )
                    f1 = 1.0 - (1.0 - base_r1) * multiplier
                    f2 = 1.0 - (1.0 - base_r2) * multiplier
                    branch_reductions[b1] = branch_reductions.get(b1, 1.0) * f1
                    branch_reductions[b2] = branch_reductions.get(b2, 1.0) * f2

            elif itype in ("无恩之刑", "恃势之刑"):
                n = len(branches_present)
                base_factor = (
                    self._REDUCE_SAN_XING_FULL
                    if n >= 3
                    else self._REDUCE_SAN_XING_PARTIAL
                )
                f = 1.0 - (1.0 - base_factor) * multiplier
                for b in branches_present:
                    branch_reductions[b] = branch_reductions.get(b, 1.0) * f

            elif itype == "无礼之刑":
                # Uncivilized punishment (子卯) — mutual harm pattern.
                f = 1.0 - (1.0 - self._REDUCE_XIANG_XING) * multiplier
                for b in branches_present:
                    branch_reductions[b] = branch_reductions.get(b, 1.0) * f

            elif itype == "自刑":
                # Same branch appearing twice (辰辰/午午/酉酉/亥亥); mildest punishment.
                # Deduplication in weight extraction prevents double-counting of the same branch.
                f = 1.0 - (1.0 - self._REDUCE_ZI_XING) * multiplier
                for b in branches_present:
                    branch_reductions[b] = branch_reductions.get(b, 1.0) * f

            elif itype == "六害":
                f = 1.0 - (1.0 - self._REDUCE_LIU_HAI) * multiplier
                for b in branches_present:
                    branch_reductions[b] = branch_reductions.get(b, 1.0) * f

            elif itype == "六破":
                f = 1.0 - (1.0 - self._REDUCE_LIU_PO) * multiplier
                for b in branches_present:
                    branch_reductions[b] = branch_reductions.get(b, 1.0) * f

        return combo_bonus, branch_reductions, stem_reductions

    _INTERACTION_BUCKETS: Dict[str, str] = {
        "三会": "组合加成",
        "三合": "组合加成",
        "半合": "组合加成",
        "拱会": "组合加成",
        "残会": "组合加成",
        "共拱": "组合加成",
        "比和": "组合加成",
        "天干合": "组合加成",
        "干支透合": "组合加成",
        "六合": "六合加成",
        "六冲": "相冲减损",
        "无恩之刑": "刑减损",
        "恃势之刑": "刑减损",
        "无礼之刑": "刑减损",
        "自刑": "刑减损",
        "六害": "害减损",
        "六破": "破减损",
    }

    def _build_interactions_display(self, priority_list: list) -> Dict[str, list]:
        """
        Partition priority-resolved interaction items by type into six display buckets:
        组合加成, 六合加成, 相冲减损, 刑减损, 害减损, 破减损.
        All scoring is driven by the priority_list from apply_bazi_master_priority().
        """
        result: Dict[str, list] = {
            "组合加成": [],
            "六合加成": [],
            "相冲减损": [],
            "刑减损": [],
            "害减损": [],
            "破减损": [],
        }
        for item in priority_list:
            bucket = self._INTERACTION_BUCKETS.get(item.get("类型", ""))
            if bucket:
                result[bucket].append(item)
        return result


# ─────────────────────────────────────────────
# Execution function
# ─────────────────────────────────────────────


_POSITION_TO_PILLAR_CN = {
    "year": "年柱",
    "month": "月柱",
    "day": "日柱",
    "hour": "时柱",
}


def _compute_xk_reductions(
    pillars: list,
    xun_kong_data: dict,
    cycle_xk_str: str = "",
) -> dict:
    """
    Return {position: factor} for each pillar whose branch is in void (旬空).

    Natal branches are checked against 日柱's void pair (day pillar anchors chart).
    The cycle pillar (position="cycle") is checked against cycle_xk_str.
    """
    # Day pillar void pair applies to all natal branches
    day_xk_str = xun_kong_data.get("日柱", {}).get("旬空", "")

    reductions = {}
    for p in pillars:
        if not p.branch:
            continue
        if p.position == "cycle":
            if cycle_xk_str and p.branch.value in cycle_xk_str:
                reductions["cycle"] = WuXingDynamicsCalculator._XUN_KONG_VOID_FACTOR
        else:
            if p.branch.value in day_xk_str:
                reductions[p.position] = WuXingDynamicsCalculator._XUN_KONG_VOID_FACTOR
    return reductions


def get_wu_xing(lunar_birthday, priority_list: list) -> Dict:
    """
    Extract Five Elements (Wu Xing) from a lunar_python Lunar object and
    calculate 五行力量 using the WuXingDynamicsCalculator engine.

    Args:
        lunar_birthday: lunar_python Lunar calendar object (from Lunar.fromSolar or
            Solar.getLunar()).
        priority_list: Priority-resolved interaction list from apply_bazi_master_priority().
            Must be pre-computed by the caller before passing here.

    Returns:
        dict with two top-level keys:
        {
            "五行力量": {
                "基本信息": {
                    "日主": {
                        "显示名称": "戊土 (阳土)",
                        "天干": "戊", "五行": "土", "阴阳": "阳",
                        "旺衰": "旺 (最强)", "十二长生": "帝旺",
                        "通根": {"月": "本气根", "日": "本气根"}  # or "无根"
                    },
                    "出生季节": "仲冬 (水旺之季)"
                },
                "四柱": {
                    "年柱": {
                        "天干": "乙", "地支": "亥",
                        "季节状态": "相 (次强)", "十二长生": "死",
                        "通根": {"年": "本气根"},  # or "无根"
                        "干支五行": {"天干五行": "木", "地支五行": "水",
                                  "主导气势": "截脚 (水克木)"},
                        "藏干": [{"干": "壬", "强度": "本气根"}, ...]
                    },
                    "月柱": {...}, "日柱": {...}, "时柱": {...}
                },
                "五行力量分析": {
                    "木": {"百分比": 15.5, "旺衰": "相 (次强)", "能级": {...}},
                    "火": {...}, "土": {...}, "金": {...}, "水": {...}
                },
                "组合加成": [...],   # 三会/三合/半合/天干合/共拱 etc.
                "六合加成": [...],   # 六合 pairs
                "相冲减损": [...],   # 六冲 clashes
                "刑减损":   [...],   # 三刑/无礼之刑/自刑
                "害减损":   [...],   # 六害
                "破减损":   [...]    # 六破
            },
            "五行相位动力": {
                "缺失": {...}, "极弱": {...}, "偏弱": {...}, "中和": {...},
                "偏旺": {...}, "极旺": {...}, "极亢": {...}
            }
        }
    """
    bazi = lunar_birthday.getEightChar()

    # Full pillar strings (e.g. "戊辰") → split into stem + branch characters
    year_pillar_str = bazi.getYear()
    month_pillar_str = bazi.getMonth()
    day_pillar_str = bazi.getDay()
    hour_pillar_str = bazi.getTime()

    year_stem,  year_branch  = (year_pillar_str[0]  if year_pillar_str  else None), (year_pillar_str[1]  if len(year_pillar_str)  > 1 else None)
    month_stem, month_branch = (month_pillar_str[0] if month_pillar_str else None), (month_pillar_str[1] if len(month_pillar_str) > 1 else None)
    day_stem,   day_branch   = (day_pillar_str[0]   if day_pillar_str   else None), (day_pillar_str[1]   if len(day_pillar_str)   > 1 else None)
    hour_stem,  hour_branch  = (hour_pillar_str[0]  if hour_pillar_str  else None), (hour_pillar_str[1]  if len(hour_pillar_str)  > 1 else None)

    # Build pillars and run the calculator in one step
    calc = WuXingDynamicsCalculator()
    pillars = [
        Pillar(
            "year",
            "年",
            calc.POSITION_WEIGHTS["year"],
            calc.STEM_WEIGHTS["year"],
            STR_STEM.get(year_stem or ""),
            STR_BRANCH.get(year_branch or ""),
        ),
        Pillar(
            "month",
            "月",
            calc.POSITION_WEIGHTS["month"],
            calc.STEM_WEIGHTS["month"],
            STR_STEM.get(month_stem or ""),
            STR_BRANCH.get(month_branch or ""),
        ),
        Pillar(
            "day",
            "日",
            calc.POSITION_WEIGHTS["day"],
            calc.STEM_WEIGHTS["day"],
            STR_STEM.get(day_stem or ""),
            STR_BRANCH.get(day_branch or ""),
        ),
        Pillar(
            "hour",
            "时",
            calc.POSITION_WEIGHTS["hour"],
            calc.STEM_WEIGHTS["hour"],
            STR_STEM.get(hour_stem or ""),
            STR_BRANCH.get(hour_branch or ""),
        ),
    ]

    # Compute natal xun kong internally
    xun_kong_data = get_xun_kong(lunar_birthday).get("旬空", {})

    # Organize pillar data: (name, wu_xing_string, hide_gan)
    xk_red = _compute_xk_reductions(pillars, xun_kong_data) if xun_kong_data else None
    result = {
        "五行力量": calc.calculate(
            pillars, priority_list=priority_list, xun_kong_reductions=xk_red
        ),
        "五行相位动力": get_all_wu_xing_tiers(),
    }

    return result


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from lunar_python import Solar
    from src.utils.logging import configure_logging, get_logger
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time

    logging = configure_logging()
    logger = get_logger(__name__)

    # python -m src.astronomer_calculations.wu_xing

    # # # Desmond's birthday example
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    tst_birthday, _ = get_true_solar_time(
        datetime_birthday, 1.3253, 103.808053
    )  # Get true solar time

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

    # Get Wu Xing in LLM-ready JSON format
    from src.astronomer_calculations.natal_interactions import get_interactions

    interactions_result = get_interactions(lunar_birthday)
    priority_list = interactions_result.get("_raw_priority_list", [])
    result = get_wu_xing(lunar_birthday, priority_list)

    logger.info(f"\n--- JSON Output for LLM ---")
    logger.info(json.dumps(result, ensure_ascii=False, indent=2))
