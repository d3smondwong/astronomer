"""
Day Master (日主) Module

Standalone calculation module for BaZi Day Master analysis.
Also serves as the canonical source for shared BaZi constants (enums, tables,
seasonal logic) imported by wu_xing.py and natal_interactions.py.

Key Exports (shared constants):
    Element, Stem, Branch               — Five Elements and Stem/Branch enums
    STEM_ELEMENT, SHENG_WANG_TABLE      — stem-element and life-cycle tables
    STATE_MULT, VISIBLE_STEM_MULT       — seasonal multiplier tables
    SeasonalFactors, get_seasonal_factors() — seasonal strength system
    BRANCH_HIDDEN_ROOTING               — hidden stem weight table (single source of truth)
    stem_elements                       — plain-string stem → element mapping
    get_stem_root_tier()                — element rooting tier across branches
    get_shi_shen_for_stem_pair()        — ten-god label for any stem pair

Main Function:
    get_day_master(lunar_birthday) → dict:
        Returns day master analysis with 得令/得地/得势 (no 强弱 verdict).

Output structure:
    {
        "日主": {
            "天干": "戊", "五行": "土", "阴阳": "阳",
            "十二长生": "帝旺",
            "得令": { "得令": True, "状态": "旺 (最强)" },
            "得地": {
                "得地": True,
                "通根": "深根",
                "详情": {
                    "年柱": "本气根"|"中气根"|"余气根"|"无根",
                    "月柱": ..., "日柱": ..., "时柱": ...
                }
            },
            "得势": {
                "得势": True,
                "支持天干": [{ "天干": "戊", "十神": "比肩" }],
                "中性天干": [{ "天干": "庚", "十神": "食神" }],
                "反对天干": [{ "天干": "甲", "十神": "七杀" }],
            },
            "得地": { "通根": "深根"|"中根"|"浅根"|"无根", ... }
        }
    }

Strength Logic (classical: 得地胜过得令 — rooting outweighs season):
    身旺: 深根 alone, OR 得令+中根, OR 得令+2支持, OR 中根+2支持
    身弱: (失令+浅根/无根+≤1支持) OR (得令+无根+≤1支持, i.e. 虚浮)
    中和: all other cases
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List
from lunar_python import Lunar


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
# Stem / branch lookup tables
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
    Stem.YI: {
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
    Stem.WU: {
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
    Stem.JI: {
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

# ─────────────────────────────────────────────
# Hidden stems — single source of truth
# Derived from 三命通会; wu_xing.py derives its Enum-keyed BRANCH_HIDDEN from this.
# ─────────────────────────────────────────────

BRANCH_HIDDEN_ROOTING: dict[str, list[tuple[str, float]]] = {
    "子": [("癸", 1.0)],
    "丑": [("己", 0.6), ("癸", 0.3), ("辛", 0.1)],
    "寅": [("甲", 0.6), ("丙", 0.3), ("戊", 0.1)],
    "卯": [("乙", 1.0)],
    "辰": [("戊", 0.6), ("乙", 0.3), ("癸", 0.1)],
    "巳": [("丙", 0.6), ("庚", 0.3), ("戊", 0.1)],
    "午": [("丁", 0.7), ("己", 0.3)],
    "未": [("己", 0.6), ("丁", 0.3), ("乙", 0.1)],
    "申": [("庚", 0.6), ("壬", 0.3), ("戊", 0.1)],
    "酉": [("辛", 1.0)],
    "戌": [("戊", 0.6), ("辛", 0.3), ("丁", 0.1)],
    "亥": [("壬", 0.7), ("甲", 0.3)],
}

# Plain-string stem → element mapping (used by get_stem_root_tier and get_shi_shen_for_stem_pair)
stem_elements: dict[str, str] = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

_ROOT_DEPTH_LABELS: list[str] = ["本气根", "中气根", "余气根"]

_YANG_STEMS: frozenset = frozenset({"甲", "丙", "戊", "庚", "壬"})

_STATE_DESCRIPTIONS: dict = {
    "旺": "旺 (最强)",
    "相": "相 (次强)",
    "囚": "囚 (弱)",
    "休": "休 (气弱)",
    "死": "死 (极弱)",
}

# ─────────────────────────────────────────────
# Seasonal factors
# ─────────────────────────────────────────────

STATE_MULT: Dict[str, float] = {
    "旺": 1.00,
    "相": 0.80,
    "休": 0.60,
    "囚": 0.40,
    "死": 0.20,
}

VISIBLE_STEM_MULT: Dict[str, float] = {
    "旺": 1.00,
    "相": 0.80,
    "休": 0.60,
    "囚": 0.50,
    "死": 0.40,
}

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

_SPRING_BRANCHES = frozenset({Branch.YIN, Branch.MAO, Branch.CHEN})
_SUMMER_BRANCHES = frozenset({Branch.SI, Branch.WU, Branch.WEI})
_AUTUMN_BRANCHES = frozenset({Branch.SHEN, Branch.YOU, Branch.XU})


@dataclass
class SeasonalFactors:
    season: str
    states: Dict[Element, str]

    def mult(self, element: Element) -> float:
        """Seasonal multiplier for hidden stems — full range 0.20 to 1.00."""
        return STATE_MULT.get(self.states.get(element, "囚"), 0.40)

    def mult_visible(self, element: Element) -> float:
        """Seasonal multiplier for a visible (transparent) heavenly stem."""
        return VISIBLE_STEM_MULT.get(self.states.get(element, "囚"), 0.50)


def get_seasonal_factors(month_branch: Branch) -> SeasonalFactors:
    """
    Map month branch → SeasonalFactors for all five elements.
    Seasons: 春(寅卯辰) 夏(巳午未) 秋(申酉戌) 冬(亥子丑)
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
# Shared helper functions
# ─────────────────────────────────────────────


def get_stem_root_tier(elem: str, zhis: list[str]) -> str:
    """
    Returns rooting tier for an element string across given branch strings.
    Canonical location — imported by wu_xing.py and natal_interactions.py.

    Args:
        elem: element string e.g. "木", "火"
        zhis: list of branch strings e.g. ["寅", "午", "子", "亥"]

    Returns:
        "深根" | "中根" | "浅根" | "无根"
    """
    best_idx = len(_ROOT_DEPTH_LABELS)
    for zhi in zhis:
        for idx, (hidden_stem, _) in enumerate(BRANCH_HIDDEN_ROOTING.get(zhi, [])):
            if stem_elements.get(hidden_stem) == elem:
                if idx < best_idx:
                    best_idx = idx
                break
    return ["深根", "中根", "浅根", "无根"][min(best_idx, 3)]


def get_shi_shen_for_stem_pair(day_stem: str, other_stem: str) -> str:
    """
    Compute the ten-god (十神) relationship of other_stem relative to day_stem.
    Canonical location — natal_interactions.py imports this back.

    Returns one of: 比肩/劫财/食神/伤官/偏财/正财/七杀/正官/偏印/正印
    """
    day_elem = stem_elements.get(day_stem, "无")
    other_elem = stem_elements.get(other_stem, "无")
    day_yin = day_stem in "乙丁己辛癸"
    other_yin = other_stem in "乙丁己辛癸"
    same_polarity = day_yin == other_yin
    _generates = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    _controls = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
    if other_elem == day_elem:
        return "比肩" if same_polarity else "劫财"
    if _generates.get(day_elem) == other_elem:
        return "食神" if same_polarity else "伤官"
    if _generates.get(other_elem) == day_elem:
        return "正印" if same_polarity else "偏印"
    if _controls.get(day_elem) == other_elem:
        return "偏财" if same_polarity else "正财"
    if _controls.get(other_elem) == day_elem:
        return "七杀" if same_polarity else "正官"
    return "未知"


# ─────────────────────────────────────────────
# Day master calculation functions
# ─────────────────────────────────────────────

_PILLAR_LABELS = ["年柱", "月柱", "日柱", "时柱"]
_SUPPORTING_GODS = {"比肩", "劫财", "偏印", "正印"}
_OPPOSING_GODS = {"正官", "七杀"}


def compute_de_ling(day_elem: str, month_branch: str) -> dict:
    """
    得令: Does the day master's element gain seasonal advantage?
    旺/相 = in season (得令 = True).

    Args:
        day_elem: day master element string e.g. "土"
        month_branch: month branch string e.g. "亥"

    Returns:
        { "得令": bool, "状态": "旺 (最强)"|... }
    """
    branch_enum = Branch(month_branch)
    seasonal = get_seasonal_factors(branch_enum)
    elem_enum = next((e for e in Element if e.value == day_elem), None)
    state = seasonal.states.get(elem_enum, "囚")
    return {
        "得令": state in ("旺", "相"),
        "状态": _STATE_DESCRIPTIONS.get(state, state),
    }


def compute_de_di(day_elem: str, all_branches: list[str]) -> dict:
    """
    得地: Does the day master root in any of the four branches?
    Returns overall rooting tier and per-branch detail.

    Args:
        day_elem: day master element string e.g. "土"
        all_branches: 4 branch strings in order [year, month, day, hour]

    Returns:
        {
            "得地": bool,
            "通根": "深根"|"中根"|"浅根"|"无根",
            "详情": { "年柱": ..., "月柱": ..., "日柱": ..., "时柱": ... }
        }
    """
    best_idx = len(_ROOT_DEPTH_LABELS)
    detail = {}
    for branch_str, label in zip(all_branches, _PILLAR_LABELS):
        found = "无根"
        for idx, (hidden_stem, _) in enumerate(BRANCH_HIDDEN_ROOTING.get(branch_str, [])):
            if stem_elements.get(hidden_stem) == day_elem and idx < len(_ROOT_DEPTH_LABELS):
                found = _ROOT_DEPTH_LABELS[idx]
                if idx < best_idx:
                    best_idx = idx
                break
        detail[label] = found
    tier = ["深根", "中根", "浅根", "无根"][min(best_idx, 3)]
    return {
        "得地": tier in ("深根", "中根"),
        "通根": tier,
        "详情": detail,
    }


def compute_de_shi(day_stem: str, all_stems: list[str]) -> dict:
    """
    得势: Categorise all other stems by ten-god relationship to day master.

    Args:
        day_stem: day master stem string e.g. "戊"
        all_stems: all 4 pillar stems; day_stem itself is skipped in output lists

    Returns:
        {
            "得势": bool,  (True if 支持天干 count >= 2)
            "支持天干": [{ "天干": "戊", "十神": "比肩" }, ...],
            "中性天干": [{ "天干": "庚", "十神": "食神" }, ...],
            "反对天干": [{ "天干": "甲", "十神": "七杀" }, ...],
        }
    """
    supporting = []
    neutral = []
    opposing = []
    for stem in all_stems:
        if stem == day_stem:
            continue
        god = get_shi_shen_for_stem_pair(day_stem, stem)
        entry = {"天干": stem, "十神": god}
        if god in _SUPPORTING_GODS:
            supporting.append(entry)
        elif god in _OPPOSING_GODS:
            opposing.append(entry)
        else:
            neutral.append(entry)
    return {
        "得势": len(supporting) >= 2,
        "支持天干": supporting,
        "中性天干": neutral,
        "反对天干": opposing,
    }


def get_day_master(lunar_birthday: Lunar) -> dict:
    """
    Main entry point. Computes full day master analysis from a BaZi chart.

    Args:
        lunar_birthday: Lunar object from lunar_python

    Returns:
        { "日主": { "天干", "五行", "阴阳", "十二长生", "得令", "得地", "得势" } }

    Note: No single 强弱 verdict is emitted. Downstream modules use 得地.通根
    (深根/中根/浅根/无根) directly as the rooting-strength proxy. Presenting
    the three raw factors (得令, 得地, 得势) avoids contested single-verdict
    methodology — e.g. 深根 alone does not guarantee 身旺 across all schools
    when 失令 and 失势 coincide with a dominant controlling element.
    """
    gans = [
        lunar_birthday.getYearGan(),
        lunar_birthday.getMonthGan(),
        lunar_birthday.getDayGan(),
        lunar_birthday.getTimeGan(),
    ]
    zhis = [
        lunar_birthday.getYearZhi(),
        lunar_birthday.getMonthZhi(),
        lunar_birthday.getDayZhi(),
        lunar_birthday.getTimeZhi(),
    ]

    day_stem = gans[2]
    day_branch = zhis[2]
    month_branch = zhis[1]

    day_stem_enum = Stem(day_stem)
    day_branch_enum = Branch(day_branch)
    day_elem = STEM_ELEMENT[day_stem_enum].value

    yang_yin = "阳" if day_stem in _YANG_STEMS else "阴"
    sheng_wang_stage = SHENG_WANG_TABLE.get(day_stem_enum, {}).get(day_branch_enum)

    de_ling = compute_de_ling(day_elem, month_branch)
    de_di = compute_de_di(day_elem, zhis)
    de_shi = compute_de_shi(day_stem, gans)

    _root_map = {"深根": 2, "中根": 1, "浅根": 0, "无根": 0}
    strength_score = (
        int(de_ling["得令"])
        + _root_map.get(de_di["通根"], 0)
        + min(len(de_shi["支持天干"]), 2)
    )

    return {
        "日主": {
            "天干": day_stem,
            "五行": day_elem,
            "阴阳": yang_yin,
            "十二长生": sheng_wang_stage,
            "得令": de_ling,
            "得地": de_di,
            "得势": de_shi,
            "强弱分数": strength_score,  # 0–5; >=3 strong, 2 moderate, <=1 weak
        }
    }


if __name__ == "__main__":
    import json
    from lunar_python import Solar
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
    from src.utils.logging import configure_logging, get_logger
    from datetime import datetime

    # python -m src.astronomer_calculations.day_master

    configure_logging()
    logger = get_logger(__name__)

    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)
    tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)
    lunar_birthday = tst_birthday.getLunar()

    result = get_day_master(lunar_birthday)
    logger.info(json.dumps(result, ensure_ascii=False, indent=2))
