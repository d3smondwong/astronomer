"""
Day Master Strength (日主 strength) Module

Standalone calculation module for BaZi Day Master analysis.
Also serves as the canonical source for shared BaZi constants (enums, tables,
seasonal logic) imported by wu_xing.py and natal_interactions.py.

Key Exports (shared constants):
    STATE_MULT, VISIBLE_STEM_MULT       — seasonal multiplier tables
    SeasonalFactors, get_seasonal_factors() — seasonal strength system
    BRANCH_HIDDEN_ROOTING               — hidden stem weight table (single source of truth)
    get_stem_element()                  — delegates to LunarUtil.WU_XING_GAN

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

Note: SHENG_WANG_TABLE has been eliminated; getDayDiShi() from lunar-python EightChar is used instead.
Stem element lookups now delegate to LunarUtil.WU_XING_GAN for consistency with lunar-python.
"""

from dataclasses import dataclass
from typing import Dict, List
from lunar_python import Lunar
from lunar_python.util import LunarUtil


# ─────────────────────────────────────────────
# Hidden stems — single source of truth
# Derived from 三命通会
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


# Plain-string stem → element mapping (delegates to lunar-python library)
def get_stem_element(stem: str) -> str:
    """Get element for a heavenly stem using lunar-python library."""
    return LunarUtil.WU_XING_GAN.get(stem, "无")


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
        "木": "旺",
        "火": "相",
        "土": "死",
        "金": "囚",
        "水": "休",
    },
    "summer": {
        "木": "休",
        "火": "旺",
        "土": "相",
        "金": "死",
        "水": "囚",
    },
    "autumn": {
        "木": "死",
        "火": "囚",
        "土": "休",
        "金": "旺",
        "水": "相",
    },
    "winter": {
        "木": "相",
        "火": "死",
        "土": "囚",
        "金": "休",
        "水": "旺",
    },
}

_SPRING_BRANCHES = frozenset({"寅", "卯", "辰"})
_SUMMER_BRANCHES = frozenset({"巳", "午", "未"})
_AUTUMN_BRANCHES = frozenset({"申", "酉", "戌"})


@dataclass
class SeasonalFactors:
    season: str
    states: Dict[str, str]

    def mult(self, element: str) -> float:
        """Seasonal multiplier for hidden stems — full range 0.20 to 1.00."""
        return STATE_MULT.get(self.states.get(element, "囚"), 0.40)

    def mult_visible(self, element: str) -> float:
        """Seasonal multiplier for a visible (transparent) heavenly stem."""
        return VISIBLE_STEM_MULT.get(self.states.get(element, "囚"), 0.50)


def get_seasonal_factors(month_branch: str) -> SeasonalFactors:
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
    seasonal = get_seasonal_factors(month_branch)
    state = seasonal.states.get(day_elem, "囚")
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
        for idx, (hidden_stem, _) in enumerate(
            BRANCH_HIDDEN_ROOTING.get(branch_str, [])
        ):
            if get_stem_element(hidden_stem) == day_elem and idx < len(
                _ROOT_DEPTH_LABELS
            ):
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
    # Internal helper to compute ten-god relationship
    def _get_shi_shen(stem1: str, stem2: str) -> str:
        elem1 = get_stem_element(stem1)
        elem2 = get_stem_element(stem2)
        yin1 = stem1 in "乙丁己辛癸"
        yin2 = stem2 in "乙丁己辛癸"
        same_polarity = yin1 == yin2
        _generates = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
        _controls = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
        if elem2 == elem1:
            return "比肩" if same_polarity else "劫财"
        if _generates.get(elem1) == elem2:
            return "食神" if same_polarity else "伤官"
        if _generates.get(elem2) == elem1:
            return "正印" if same_polarity else "偏印"
        if _controls.get(elem1) == elem2:
            return "偏财" if same_polarity else "正财"
        if _controls.get(elem2) == elem1:
            return "七杀" if same_polarity else "正官"
        return "未知"

    supporting = []
    neutral = []
    opposing = []
    for stem in all_stems:
        if stem == day_stem:
            continue
        god = _get_shi_shen(day_stem, stem)
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
    bazi = lunar_birthday.getEightChar()

    gans = [
        bazi.getYearGan(),
        bazi.getMonthGan(),
        bazi.getDayGan(),
        bazi.getTimeGan(),
    ]
    zhis = [
        bazi.getYearZhi(),
        bazi.getMonthZhi(),
        bazi.getDayZhi(),
        bazi.getTimeZhi(),
    ]

    day_stem = gans[2]
    day_branch = zhis[2]
    month_branch = zhis[1]

    day_elem = LunarUtil.WU_XING_GAN.get(day_stem, "无")

    yang_yin = "阳" if day_stem in _YANG_STEMS else "阴"
    # Use lunar-python's getDayDiShi() instead of table lookup
    sheng_wang_stage = bazi.getDayDiShi()

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
