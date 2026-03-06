"""
Wu Xing (五行) - Five Elements Calculation Module

This module extracts and analyzes the Five Elements (Wu Xing) composition from a BaZi chart,
applying the Ming Dynasty Imperial Qi Dynamics (明代帝王氣動法) calculation system with
professional-grade climate influence and branch relationship modifiers.

Core Architecture:
    - Hidden Stem Analysis: Extracts buried elemental stems from branches with depth weighting
    - Heavenly Stem Scoring: Position-weighted visible stem contributions with seasonal floors
    - Climate Modulation: 5-category temperature system (very_cold, cold, neutral, warm, hot)
      with element-specific sensitivity multipliers
    - Branch Relationships: 三合 (three-harmony), 六合 (six-harmony), 冲 (clash), 刑 (punishment)
      and 害 (harm) combinations and reductions

Weight Architecture (~1.10 total scale):
    Branch hidden stems:  year=0.15, month=0.45, day=0.25, hour=0.15 (sum=1.00)
    Heavenly stems:       year=0.015, month=0.045, day=0.025, hour=0.015 (sum=0.10)
    Combinations:         additive bonuses (small)

Key Functions:
    get_wu_xing(lunar_birthday): Extracts Five Elements with professional analysis.

    Returns:
        dict: Professional LLM-ready JSON structure:
        {
            "年柱": {"五行": {"天干五行": "...", "地支五行": "..."}, "藏干": [...]},
            "月柱": {...}, "日柱": {...}, "时柱": {...},
            "五行力量": {
                "基本信息": {
                    "日主": "戊土 (阳土)",
                    "出生季节": "孟冬 (水旺之季)"
                },
                "五行力量分析": {
                    "木": {"百分比": 15.5, "旺衰": "相 (次强)"},
                    "火": {...}, "土": {...}, "金": {...}, "水": {...}
                },
                "气候": {"分类": "neutral", "加权平均分": -0.25},
                "组合加成": ["木", "水"],           # Three-harmony bonuses
                "六合加成": ["火"],                 # Six-harmony bonuses
                "相冲减损": ["午"],                 # Clashed branches
                "刑减损": ["开"],                   # Punished branches
                "害减损": ["戌"],                   # Harmed branches
                "天干透出系数": [                  # Visible stem seasonal protection (ordered: year, month, day, hour)
                    {"柱": "年", "天干": "乙", "季节状态": "死 (极弱)", "是否托底": true},
                    {"柱": "月", "天干": "丁", "季节状态": "囚 (受克)", "是否托底": true},
                    {"柱": "日", "天干": "戊", "季节状态": "相 (次强)", "是否托底": false},
                    {"柱": "时", "天干": "庚", "季节状态": "囚 (受克)", "是否托底": true}
                ]
            }
        }

The Five Elements:
    - 木 (Wood): Growth, expansion, flexibility
    - 火 (Fire): Passion, activity, transformation
    - 土 (Earth): Stability, nurture, balance
    - 金 (Metal): Strength, discipline, precision
    - 水 (Water): Flow, wisdom, flexibility

Climate System:
    5-category weighted average from branch temperature qualities with position weights.
    Fire/Water: ±24% inverse sensitivity | Wood/Metal/Earth: ±12% moderate sensitivity

This data is LLM-ready with transparent calculations for professional practitioners.
"""

from lunar_python import Lunar
from datetime import datetime
from collections import Counter
from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


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

# Hidden stems: (primary, secondary, residual) with depth ratios.
# Format: [(stem, depth), ...]. All depths sum to 1.0 per branch.
BRANCH_HIDDEN: Dict[Branch, List[Tuple[Stem, float]]] = {
    Branch.ZI: [(Stem.GUI, 1.0)],
    Branch.CHOU: [(Stem.JI, 0.6), (Stem.GUI, 0.3), (Stem.XIN, 0.1)],
    Branch.YIN: [(Stem.JIA, 0.6), (Stem.BING, 0.3), (Stem.WU, 0.1)],  # 渊海子平: 甲0.7
    Branch.MAO: [(Stem.YI, 1.0)],
    Branch.CHEN: [(Stem.WU, 0.6), (Stem.YI, 0.3), (Stem.GUI, 0.1)],
    Branch.SI: [(Stem.BING, 0.7), (Stem.WU, 0.2), (Stem.GENG, 0.1)],
    Branch.WU: [(Stem.DING, 0.7), (Stem.JI, 0.3)],
    Branch.WEI: [(Stem.JI, 0.6), (Stem.DING, 0.3), (Stem.YI, 0.1)],
    Branch.SHEN: [(Stem.GENG, 0.6), (Stem.REN, 0.3), (Stem.WU, 0.1)],  # 渊海子平: 庚0.7
    Branch.YOU: [(Stem.XIN, 1.0)],
    Branch.XU: [(Stem.WU, 0.6), (Stem.XIN, 0.3), (Stem.DING, 0.1)],
    Branch.HAI: [(Stem.REN, 0.7), (Stem.JIA, 0.3)],
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
    Stem.YI: {  # Yin Wood — mirrors Yang Metal (庚) cycle, reversed direction
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
    Stem.WU: {  # Yang Earth — mirrors Yang Fire (丙) cycle, same direction
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
    Stem.JI: {  # Yin Earth — mirrors Yang Fire (丙) cycle, reversed direction
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


def get_seasonal_factors(month_branch: Branch) -> SeasonalFactors:
    """Map month branch → seasonal states for all five elements."""
    table = {
        "spring": {  # 寅卯辰
            Element.WOOD: "旺",
            Element.FIRE: "相",
            Element.EARTH: "死",
            Element.METAL: "囚",
            Element.WATER: "休",
        },
        "summer": {  # 巳午未
            Element.WOOD: "休",
            Element.FIRE: "旺",
            Element.EARTH: "相",
            Element.METAL: "死",
            Element.WATER: "囚",
        },
        "autumn": {  # 申酉戌
            Element.WOOD: "死",
            Element.FIRE: "囚",
            Element.EARTH: "休",
            Element.METAL: "旺",
            Element.WATER: "相",
        },
        "winter": {  # 亥子丑
            Element.WOOD: "相",
            Element.FIRE: "死",
            Element.EARTH: "囚",
            Element.METAL: "休",
            Element.WATER: "旺",
        },
    }
    spring = {Branch.YIN, Branch.MAO, Branch.CHEN}
    summer = {Branch.SI, Branch.WU, Branch.WEI}
    autumn = {Branch.SHEN, Branch.YOU, Branch.XU}

    if month_branch in spring:
        season = "spring"
    elif month_branch in summer:
        season = "summer"
    elif month_branch in autumn:
        season = "autumn"
    else:
        season = "winter"

    return SeasonalFactors(season=season, states=table[season])


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
    elif avg <= 2.0:
        return "hot", round(avg, 2)
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


# Precomputed 主导气势 lookup for fast direct mapping in parse_wu_xing. Not utilised but can be used in future.
ZHU_DAO_QI_SHI_LOOKUP: Dict[Tuple[str, str], str] = {
    ("木", "木"): "比和 (木行纯粹)",
    ("木", "火"): "天生地 (木生火)",
    ("木", "土"): "盖头 (木克土)",
    ("木", "金"): "截脚 (金克木)",
    ("木", "水"): "地生天 (水生木)",
    ("火", "木"): "地生天 (木生火)",
    ("火", "火"): "比和 (火行纯粹)",
    ("火", "土"): "天生地 (火生土)",
    ("火", "金"): "盖头 (火克金)",
    ("火", "水"): "截脚 (水克火)",
    ("土", "木"): "截脚 (木克土)",
    ("土", "火"): "地生天 (火生土)",
    ("土", "土"): "比和 (土行纯粹)",
    ("土", "金"): "天生地 (土生金)",
    ("土", "水"): "盖头 (土克水)",
    ("金", "木"): "盖头 (金克木)",
    ("金", "火"): "截脚 (火克金)",
    ("金", "土"): "地生天 (土生金)",
    ("金", "金"): "比和 (金行纯粹)",
    ("金", "水"): "天生地 (金生水)",
    ("水", "木"): "天生地 (水生木)",
    ("水", "火"): "盖头 (水克火)",
    ("水", "土"): "截脚 (土克水)",
    ("水", "金"): "地生天 (金生水)",
    ("水", "水"): "比和 (水行纯粹)",
}


# ─────────────────────────────────────────────
# Pillar dataclass
# ─────────────────────────────────────────────


@dataclass
class Pillar:
    position: str  # "year" | "month" | "day" | "hour"
    position_weight: float
    stem: Optional[Stem]
    branch: Optional[Branch]


# ─────────────────────────────────────────────
# String → Enum helpers
# ─────────────────────────────────────────────

STR_STEM = {s.value: s for s in Stem}
STR_BRANCH = {b.value: b for b in Branch}


# ─────────────────────────────────────────────
# Main calculator
# ─────────────────────────────────────────────
class MingQiDynamicsCalculator:
    """
    Ming Dynasty Imperial Qi Dynamics (明代帝王氣動法).

    Weight architecture (total ~1.10):
      Branch hidden stems: year=0.15, month=0.45, day=0.25, hour=0.15  (sum=1.00)
      Heavenly stems:      year=0.015, month=0.045, day=0.025, hour=0.015 (sum=0.10)
      Combinations:        additive bonus on top (small)

    Stem weights mirror branch weight ratios so that the month stem (月干)
    carries proportionally more authority than year/hour stems, consistent
    with classical 月令 doctrine.
    """

    # Single source of truth for all positional weights
    POSITION_WEIGHTS = {"year": 0.15, "month": 0.45, "day": 0.25, "hour": 0.15}

    # Heavenly stem weights mirror branch positional weights to reflect their authority
    # Month stem (月干) carries greater weight closer to 月令 (Seasonal Command)
    # Ratio: year:month:day:hour = 0.15:0.45:0.25:0.15 → scaled to sum=0.10
    STEM_WEIGHTS = {"year": 0.015, "month": 0.045, "day": 0.025, "hour": 0.015}

    # Three-harmony (三合) frames: hub branch → (frame element, [all three])
    THREE_HARMONY = {
        Element.WATER: (Branch.ZI, [Branch.SHEN, Branch.ZI, Branch.CHEN]),
        Element.WOOD: (Branch.MAO, [Branch.HAI, Branch.MAO, Branch.WEI]),
        Element.FIRE: (Branch.WU, [Branch.YIN, Branch.WU, Branch.XU]),
        Element.METAL: (Branch.YOU, [Branch.SI, Branch.YOU, Branch.CHOU]),
    }

    # Half-combo pair strengths: (b1, b2) → (element, strength_with_hub, strength_no_hub)
    # Distinguishes strength when hub branch is present vs absent (拱合 without hub)
    HALF_COMBOS: Dict[Tuple[Branch, Branch], Tuple[Element, float, float]] = {
        (Branch.SHEN, Branch.ZI): (Element.WATER, 0.15, 0.08),
        (Branch.ZI, Branch.CHEN): (Element.WATER, 0.15, 0.08),
        (Branch.SHEN, Branch.CHEN): (Element.WATER, 0.08, 0.04),  # no hub = 拱合
        (Branch.HAI, Branch.MAO): (Element.WOOD, 0.15, 0.08),
        (Branch.MAO, Branch.WEI): (Element.WOOD, 0.15, 0.08),
        (Branch.HAI, Branch.WEI): (Element.WOOD, 0.08, 0.04),
        (Branch.YIN, Branch.WU): (Element.FIRE, 0.15, 0.08),
        (Branch.WU, Branch.XU): (Element.FIRE, 0.15, 0.08),
        (Branch.YIN, Branch.XU): (Element.FIRE, 0.08, 0.04),
        (Branch.SI, Branch.YOU): (Element.METAL, 0.15, 0.08),
        (Branch.YOU, Branch.CHOU): (Element.METAL, 0.15, 0.08),
        (Branch.SI, Branch.CHOU): (Element.METAL, 0.08, 0.04),
    }

    CLASH_PAIRS = [
        (Branch.ZI, Branch.WU),
        (Branch.CHOU, Branch.WEI),
        (Branch.YIN, Branch.SHEN),
        (Branch.MAO, Branch.YOU),
        (Branch.CHEN, Branch.XU),
        (Branch.SI, Branch.HAI),
    ]

    FULL_TRIPLET_BONUS = 0.20

    # 六合 (Six Branch Harmonies): Each pair merges into a new element
    # Strength coefficient applied as additive bonus scaled by pillar weights × 0.06
    # Weaker than 三合 (which uses 0.08–0.15) — simpler, less powerful pairing
    # 午未合 uses Fire (the primary outcome in classical texts)
    SIX_HARMONIES: Dict[Tuple[Branch, Branch], Element] = {
        (Branch.ZI, Branch.CHOU): Element.EARTH,
        (Branch.YIN, Branch.HAI): Element.WOOD,
        (Branch.MAO, Branch.XU): Element.FIRE,
        (Branch.CHEN, Branch.YOU): Element.METAL,
        (Branch.SI, Branch.SHEN): Element.WATER,
        (Branch.WU, Branch.WEI): Element.FIRE,
    }
    SIX_HARMONY_STRENGTH = 0.06  # weaker than 三合 adjacent pairs (0.08–0.15)

    # 刑 (Punishments): Three types affecting branch power
    #   三刑 (triple punishment): 寅巳申 or 丑戌未 cycles
    #   相刑 (mutual punishment): 子卯 bidirectional
    #   自刑 (self-punishment): skipped for standard 4-pillar charts
    # Effect: reduced by ×0.85–×0.75 depending on severity (lighter than 冲 clashes)
    XING_TRIPLETS: List[List[Branch]] = [
        [Branch.YIN, Branch.SI, Branch.SHEN],  # 寅巳申 三刑
        [Branch.CHOU, Branch.XU, Branch.WEI],  # 丑戌未 三刑
    ]
    XING_MUTUAL: List[Tuple[Branch, Branch]] = [
        (Branch.ZI, Branch.MAO),  # 子卯 相刑
    ]

    # 害 (Harms): Six branch harm pairs affecting specific relationships
    # Weaker than 冲 (clashes), lighter reduction ×0.90
    HAI_PAIRS: List[Tuple[Branch, Branch]] = [
        (Branch.ZI, Branch.WEI),
        (Branch.CHOU, Branch.WU),
        (Branch.YIN, Branch.SI),
        (Branch.MAO, Branch.CHEN),
        (Branch.SHEN, Branch.HAI),
        (Branch.YOU, Branch.XU),
    ]

    def calculate(self, pillars: List[Pillar]) -> Dict:
        """Main entry point — returns full result dict."""
        # Validate
        month_pillar = next((p for p in pillars if p.position == "month"), None)
        if not month_pillar or not month_pillar.branch:
            raise ValueError("Month pillar with branch is required.")

        seasonal = get_seasonal_factors(month_pillar.branch)
        climate, climate_score = get_chart_climate(pillars)
        clash_reductions = self._check_clashes(pillars)
        xing_reductions = self._check_xing(pillars)
        hai_reductions = self._check_hai(pillars)
        combo_bonus = self._check_combinations(pillars)
        six_harmony_bonus = self._check_six_harmonies(pillars)

        power = {e: 0.0 for e in Element}

        # ── STEP 1: Branch hidden stems ──────────────────────────────────
        for p in pillars:
            if not p.branch:
                continue
            # Compound all branch-level reductions: 冲, 刑, 害
            reduction = (
                clash_reductions.get(p.branch, 1.0)
                * xing_reductions.get(p.branch, 1.0)
                * hai_reductions.get(p.branch, 1.0)
            )
            base_w = p.position_weight * reduction

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
            pen_bonus = self._penetration_bonus(p, pillars)
            stem_w = self.STEM_WEIGHTS[p.position]

            stem_power = stem_w * s_mult * c_mult * sw_mult + pen_bonus
            power[elem] += stem_power

        # ── STEP 3: Combination bonuses ─────────────────────────────────
        for elem, bonus in combo_bonus.items():
            power[elem] += bonus
        for elem, bonus in six_harmony_bonus.items():
            power[elem] += bonus

        # Seasonal floor for visible stems is applied via mult_visible() multiplier

        # ── STEP 4: Percentages ──────────────────────────────────────────
        total = sum(power.values())
        percentages = {e.value: round(v / total * 100, 2) for e, v in power.items()}

        # Map seasonal states to their descriptions
        state_descriptions = {
            "旺": "旺 (最强)",
            "相": "相 (次强)",
            "囚": "囚 (受克)",
            "休": "休 (气弱)",
            "死": "死 (极弱)",
        }

        # Building 基本信息 (Basic Information)
        day_pillar = next((p for p in pillars if p.position == "day"), None)
        day_master = ""
        if day_pillar and day_pillar.stem:
            stem_val = day_pillar.stem.value
            elem = STEM_ELEMENT[day_pillar.stem]
            # Determine if stem is Yang (甲丙戊庚壬) or Yin (乙丁己辛癸)
            yang_stems = {"甲", "丙", "戊", "庚", "壬"}
            yang_yin = "阳" if stem_val in yang_stems else "阴"
            day_master = f"{stem_val}{elem.value} ({yang_yin}{elem.value})"

        # Map season to Chinese season name
        season_names = {
            "spring": "孟春 (木旺之季)",
            "summer": "孟夏 (火旺之季)",
            "autumn": "孟秋 (金旺之季)",
            "winter": "孟冬 (水旺之季)",
        }
        birth_season = season_names.get(seasonal.season, "")

        # Climate characteristics description
        climate_descriptions = {
            "very_cold": "极寒",
            "cold": "寒冷",
            "neutral": "常温",
            "warm": "温暖",
            "hot": "炎热",
        }
        climate_char = climate_descriptions.get(climate, climate)

        # Assemble the final result structure. Commented out climate characteristics for now, can be re-enabled if needed.
        basic_info = {
            "日主": day_master,
            "出生季节": birth_season,
            # "气候特征": climate_char,
        }

        # Expose visible-stem seasonal multipliers so callers can inspect the floor effect
        # Preserve all stems in order (year, month, day, hour), including duplicates
        visible_stem_mults = []
        pillar_positions = {"year": "年", "month": "月", "day": "日", "hour": "时"}
        for p in pillars:
            if p.stem:
                elem = STEM_ELEMENT[p.stem]
                state = seasonal.states.get(elem, "囚")
                raw = STATE_MULT.get(state, 0.40)
                floored = VISIBLE_STEM_MULT.get(state, 0.50)
                state_desc = state_descriptions.get(state, state)
                visible_stem_mults.append(
                    {
                        "柱": pillar_positions[p.position],
                        "天干": p.stem.value,
                        "季节状态": state_desc,
                        "是否托底": floored != raw,
                    }
                )

        # Build the new "五行力量分析" structure
        wu_xing_analysis = {}
        for elem in Element:
            elem_name = elem.value
            pct = percentages.get(elem_name, 0)
            state = seasonal.states.get(elem, "囚")
            state_desc = state_descriptions.get(state, state)
            wu_xing_analysis[elem_name] = {
                "百分比": round(pct, 2) if isinstance(pct, (int, float)) else pct,
                "旺衰": state_desc,
            }

        return {
            "基本信息": basic_info,
            "五行力量分析": wu_xing_analysis,
            "组合加成": [e.value for e, v in combo_bonus.items() if v > 0],
            "六合加成": [e.value for e, v in six_harmony_bonus.items() if v > 0],
            "相冲减损": [b.value for b in clash_reductions.keys()],
            "刑减损": [b.value for b in xing_reductions.keys()],
            "害减损": [b.value for b in hai_reductions.keys()],
            "天干透出系数": visible_stem_mults,
        }

    # ─── helpers ──────────────────────────────────────────────

    def _check_clashes(self, pillars: List[Pillar]) -> Dict[Branch, float]:
        """
        Branch clash resolution based on relative strength dynamics.

        Classical principle: the stronger branch (旺相 in season, heavier
        position weight) damages the weaker branch more severely.

        Strength score per branch = position_weight × seasonal_branch_mult,
        where seasonal_branch_mult is the primary hidden stem's seasonal state.

        Reduction applied:
          Stronger branch: ×0.80 (minor damage — it overpowers the clash)
          Weaker branch:   ×0.40 (severe damage — heavily constrained)
          Equal strength:  both ×0.65 (symmetric clash)
        """
        # Need seasonal factors to determine branch strength
        month_pillar = next((p for p in pillars if p.position == "month"), None)
        if not month_pillar or not month_pillar.branch:
            return {}
        seasonal = get_seasonal_factors(month_pillar.branch)

        def branch_strength(p: Pillar) -> float:
            if not p.branch:
                return 0.0
            primary_stem = BRANCH_HIDDEN[p.branch][0][0]
            elem = STEM_ELEMENT[primary_stem]
            return p.position_weight * seasonal.mult(elem)

        reductions: Dict[Branch, float] = {}
        branches = [p for p in pillars if p.branch]

        for i, p1 in enumerate(branches):
            for p2 in branches[i + 1 :]:
                for b1, b2 in self.CLASH_PAIRS:
                    if {p1.branch, p2.branch} == {b1, b2}:
                        s1 = branch_strength(p1)
                        s2 = branch_strength(p2)
                        ratio = s1 / s2 if s2 > 0 else 1.0

                        if ratio > 1.20:  # p1 clearly stronger
                            r1, r2 = 0.80, 0.40
                        elif ratio < 0.833:  # p2 clearly stronger
                            r1, r2 = 0.40, 0.80
                        else:  # roughly equal
                            r1, r2 = 0.65, 0.65

                        reductions[p1.branch] = reductions.get(p1.branch, 1.0) * r1
                        reductions[p2.branch] = reductions.get(p2.branch, 1.0) * r2

        return reductions

    def _check_combinations(self, pillars: List[Pillar]) -> Dict[Element, float]:
        combo: Dict[Element, float] = {e: 0.0 for e in Element}
        branch_list = [(p.branch, p.position_weight) for p in pillars if p.branch]
        branch_set = {b for b, _ in branch_list}

        for i, (b1, w1) in enumerate(branch_list):
            for b2, w2 in branch_list[i + 1 :]:
                key1 = (b1, b2)
                key2 = (b2, b1)
                entry = self.HALF_COMBOS.get(key1) or self.HALF_COMBOS.get(key2)
                if not entry:
                    continue
                elem, str_hub, str_no_hub = entry

                # Determine if hub is present
                hub_branch = self.THREE_HARMONY[elem][0]
                hub_present = hub_branch in branch_set
                strength = str_hub if hub_present else str_no_hub

                pair_power = (w1 + w2) * strength
                combo[elem] += pair_power

        # Full triplet bonus: checked once per frame AFTER all pairs are counted,
        # not inside the pair loop — otherwise it fires once per matching pair (3×
        # overcounting when all three branches are present).
        for elem, (hub, triplet) in self.THREE_HARMONY.items():
            if all(b in branch_set for b in triplet):
                combo[elem] += self.FULL_TRIPLET_BONUS

        return combo

    def _check_six_harmonies(self, pillars: List[Pillar]) -> Dict[Element, float]:
        """
        六合 (Six Branch Harmonies): Weaker than 三合 but meaningful shaping.
        Each harmony pair transforms into a single element with modest bonuses.

        Each matching pair adds a small bonus to the merged element,
        scaled by (weight1 + weight2) × SIX_HARMONY_STRENGTH.
        Weaker than 三合 adjacent pairs — 六合 is a simple binary bond,
        not a directional frame with a hub.

        Note: if a pair is ALSO in a 冲 relationship, 六合 is neutralised
        (they cannot harmonise and clash simultaneously). We skip the bonus
        when either branch already has a clash reduction.
        """
        bonus: Dict[Element, float] = {e: 0.0 for e in Element}
        branch_list = [(p.branch, p.position_weight) for p in pillars if p.branch]
        clash_branches = set(self._check_clashes(pillars).keys())

        for i, (b1, w1) in enumerate(branch_list):
            for b2, w2 in branch_list[i + 1 :]:
                elem = self.SIX_HARMONIES.get((b1, b2)) or self.SIX_HARMONIES.get(
                    (b2, b1)
                )
                if elem is None:
                    continue
                # Skip if either branch is clashing — 冲 breaks 合
                if b1 in clash_branches or b2 in clash_branches:
                    continue
                bonus[elem] += (w1 + w2) * self.SIX_HARMONY_STRENGTH

        return bonus

    def _check_xing(self, pillars: List[Pillar]) -> Dict[Branch, float]:
        """
        刑 (Punishments): Reduce branch power in interpersonal conflict patterns.
        Lighter effect than 冲 (clashes), distinguishes between triplet cycles
        and mutual punishments.

        三刑 (triple punishment triplets: 寅巳申, 丑戌未):
          - Two members present  → each gets ×0.85
          - All three present    → each gets ×0.75
        相刑 (mutual punishment: 子卯):
          - Both present         → each gets ×0.85
        自刑 (self-punishment: 辰午酉亥) — impossible in a standard 4-pillar
          chart since each branch appears at most once, so skipped.
        """
        reductions: Dict[Branch, float] = {}
        branch_set = {p.branch for p in pillars if p.branch}

        # 三刑
        for triplet in self.XING_TRIPLETS:
            present = [b for b in triplet if b in branch_set]
            if len(present) == 3:
                r = 0.75
            elif len(present) == 2:
                r = 0.85
            else:
                continue
            for b in present:
                reductions[b] = reductions.get(b, 1.0) * r

        # 相刑
        for b1, b2 in self.XING_MUTUAL:
            if b1 in branch_set and b2 in branch_set:
                reductions[b1] = reductions.get(b1, 1.0) * 0.85
                reductions[b2] = reductions.get(b2, 1.0) * 0.85

        return reductions

    def _check_hai(self, pillars: List[Pillar]) -> Dict[Branch, float]:
        """
        害 (Harms): Six specific branch interference patterns.
        Weaker than 冲 clashes, applied as multiplicative reduction (×0.90).

        六害 pairs arises classically when a 六合 bond is broken by a 冲.
        We implement the harm pairs directly without requiring the
        full 合→冲 chain, which is the standard simplified approach.
        """
        reductions: Dict[Branch, float] = {}
        branch_set = {p.branch for p in pillars if p.branch}

        for b1, b2 in self.HAI_PAIRS:
            if b1 in branch_set and b2 in branch_set:
                reductions[b1] = reductions.get(b1, 1.0) * 0.90
                reductions[b2] = reductions.get(b2, 1.0) * 0.90

        return reductions

    def _penetration_bonus(
        self,
        pillar: Pillar,
        all_pillars: List[Pillar],
    ) -> float:
        """
        Calculate penetration bonus for a heavenly stem from adjacent branch hidden stems.

        Rules:
          - Only adjacent pillars (distance=1) contribute to penetration.
          - Pure Pillar RECEIVING: if this stem's own pillar is pure
            (stem element == primary branch element), reduce bonus by ×0.5.
            The branch already provides strong root support, so additional
            penetration from outside risks double-counting that root energy.
          - Pure Pillar SENDING: if the hidden stem found in an adjacent branch
            is the PRIMARY stem of that branch AND that branch's pillar is also
            pure (same stem visible there too), reduce its contribution by ×0.5.
            Its energy is already fully expressed through its own visible stem.
        """
        bonus = 0.0
        elem = STEM_ELEMENT[pillar.stem]
        order = ["year", "month", "day", "hour"]

        # Is this pillar itself a Pure Pillar? (stem elem == primary branch elem)
        primary_branch_elem = (
            STEM_ELEMENT[BRANCH_HIDDEN[pillar.branch][0][0]] if pillar.branch else None
        )
        receiving_pure = primary_branch_elem == elem

        # Build a lookup: branch → its pillar (for sender-side pure check)
        branch_to_pillar = {p.branch: p for p in all_pillars if p.branch}

        for other in all_pillars:
            if other is pillar or not other.branch:
                continue
            dist = abs(order.index(pillar.position) - order.index(other.position))
            if dist > 1:
                continue

            for i, (hidden_stem, depth) in enumerate(BRANCH_HIDDEN[other.branch]):
                if STEM_ELEMENT[hidden_stem] != elem:
                    continue

                contribution = 0.006 * depth

                # Sender-side pure pillar reduction:
                # If this hidden stem is the PRIMARY stem (i==0) of the other branch,
                # and that branch's visible stem is the same element (pure pillar),
                # its energy is already fully expressed — reduce contribution.
                if i == 0 and other.stem:
                    sender_pure = STEM_ELEMENT[other.stem] == elem
                    if sender_pure:
                        contribution *= 0.5

                # Receiver-side pure pillar reduction:
                # This stem's own branch already provides strong root — halve bonus.
                if receiving_pure:
                    contribution *= 0.5

                bonus += contribution

        return min(bonus, 0.01)  # cap at 0.01


# ─────────────────────────────────────────────
# Execution function
# ─────────────────────────────────────────────


def parse_wu_xing(wu_xing_str: str) -> Dict:
    """
    Split a Wu Xing string (e.g. '木土') into stem and branch elements.

    Args:
        wu_xing_str: Wu Xing string with stem and branch (e.g. '木土')

    Returns:
        dict: Structure with 天干五行 and 地支五行
    """
    if len(wu_xing_str) >= 2:
        return {"天干五行": wu_xing_str[0], "地支五行": wu_xing_str[1]}
    return {"天干五行": "", "地支五行": ""}




def get_wu_xing(lunar_birthday) -> Dict:
    """
    Extract Five Elements (Wu Xing) from a lunar_python Lunar object and
    calculate 五行力量 using the Ming Dynasty Qi Dynamics engine.

    Args:
        lunar_birthday: lunar_python Lunar calendar object

    Returns:
        dict with keys 年柱, 月柱, 日柱, 时柱, 五行力量
    """
    bazi = lunar_birthday.getEightChar()

    # Wu Xing strings per pillar (e.g. "木土")
    year_wu_xing = bazi.getYearWuXing()
    month_wu_xing = bazi.getMonthWuXing()
    day_wu_xing = bazi.getDayWuXing()
    hour_wu_xing = bazi.getTimeWuXing()

    # Hidden stems per pillar
    year_hide_gan = bazi.getYearHideGan()
    month_hide_gan = bazi.getMonthHideGan()
    day_hide_gan = bazi.getDayHideGan()
    hour_hide_gan = bazi.getTimeHideGan()

    # Full pillar strings (e.g. "戊辰") → split into stem + branch characters
    year_pillar_str = bazi.getYear()
    month_pillar_str = bazi.getMonth()
    day_pillar_str = bazi.getDay()
    hour_pillar_str = bazi.getTime()

    def _split(s: str) -> tuple:
        return (s[0] if s else None, s[1] if len(s) > 1 else None)

    year_stem, year_branch = _split(year_pillar_str)
    month_stem, month_branch = _split(month_pillar_str)
    day_stem, day_branch = _split(day_pillar_str)
    hour_stem, hour_branch = _split(hour_pillar_str)

    # Build pillars and run the calculator in one step
    calc = MingQiDynamicsCalculator()
    pillars = [
        Pillar(
            "year",
            calc.POSITION_WEIGHTS["year"],
            STR_STEM.get(year_stem),
            STR_BRANCH.get(year_branch),
        ),
        Pillar(
            "month",
            calc.POSITION_WEIGHTS["month"],
            STR_STEM.get(month_stem),
            STR_BRANCH.get(month_branch),
        ),
        Pillar(
            "day",
            calc.POSITION_WEIGHTS["day"],
            STR_STEM.get(day_stem),
            STR_BRANCH.get(day_branch),
        ),
        Pillar(
            "hour",
            calc.POSITION_WEIGHTS["hour"],
            STR_STEM.get(hour_stem),
            STR_BRANCH.get(hour_branch),
        ),
    ]

    # Organize pillar data: (name, wu_xing_string, hide_gan)
    pillar_data = [
        ("年柱", year_wu_xing, year_hide_gan),
        ("月柱", month_wu_xing, month_hide_gan),
        ("日柱", day_wu_xing, day_hide_gan),
        ("时柱", hour_wu_xing, hour_hide_gan),
    ]

    result = {
        "五行力量": calc.calculate(pillars),
    }

    # Mapping from string to Element enum
    STR_ELEMENT = {e.value: e for e in Element}

    for pillar_name, wu_xing_str, hide_gan in pillar_data:
        wu_xing_dict = parse_wu_xing(wu_xing_str)
        stem_elem_str = wu_xing_dict.get("天干五行", "")
        branch_elem_str = wu_xing_dict.get("地支五行", "")
        stem_elem = STR_ELEMENT.get(stem_elem_str)
        branch_elem = STR_ELEMENT.get(branch_elem_str)
        zhu_dao_qi_shi = (
            get_zhu_dao_qi_shi(stem_elem, branch_elem)
            if stem_elem and branch_elem else "未知关系"
        )
        wu_xing_dict["主导气势"] = zhu_dao_qi_shi
        result[pillar_name] = {
            "五行": wu_xing_dict,
            "藏干": hide_gan,
        }

    return result


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from src.astronomer_calculations.bazi_pillars import get_bazi_pillars
    from lunar_python import Solar

    # python -m src.astronomer_calculations.wu_xing

    # # Desmond's birthday example
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

    print("阳历生日: " + solar_birthday.toYmdHms())
    print("真太阳时生日: " + tst_birthday.toYmdHms())

    lunar_birthday = tst_birthday.getLunar()  # Convert to lunar calendar

    bazi = lunar_birthday.getEightChar()
    print(
        f"\nBaZi: {bazi.getYear()}, {bazi.getMonth()}, {bazi.getDay()}, {bazi.getTime()}"
    )

    # Get Wu Xing in LLM-ready JSON format
    result = get_wu_xing(lunar_birthday)

    print(f"\n--- JSON Output for LLM ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))
