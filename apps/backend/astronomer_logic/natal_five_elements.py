"""
Natal Five Elements Qualifier — 五行旺衰 (旺/相/休/囚/死)

Classifies the qualitative seasonal state of each of the five elements (木火土金水)
for a natal BaZi chart using classical rule-based logic.

Pipeline (QualitativeFiveElementsClassifier):
  1. Determine the birth season from the month branch (MONTH_SEASON).
  2. Check whether the birth date falls within the 土旺用事 window (last 18 days of
     an Earth month 辰/未/戌/丑, using lunar_python's solar-term table).
  3. Look up the seasonal base state from SEASONAL_BASE (or EARTH_SEASONAL_BASE during
     the 土旺用事 window).
  4. Apply upgrades: ≥2 root branches (+1), 本气 root (+1), visible branch (+1),
     combination boost at ≥0.75 strength (+1).
  5. Apply downgrades: stem-without-root (−1), net clash on dominant root (−1),
     void-pillar penalty when void tier > non-void tier (−1).
  6. Cap non-ruling elements at min(base_idx + 2, 3) unless a full 三合/三会 is present.

Output shape (from classify_all):
  {
    "五行": {
      "木": { "状态": "相" },
      "火": { "状态": "旺" },
      "土": { "状态": "死" },
      "金": { "状态": "休" },
      "水": { "状态": "囚" },
    }
  }

Per-pillar element assignments (from get_pillar_five_elements):
  {
    "年柱": { "天干五行": "木", "地支五行": "水", "藏干五行": { "本气": "水", "中气": "金" } },
    ...
  }

Debugging:
  Uncomment the "依据" block inside _classify_one to emit a per-element audit dict
  showing every factor that influenced the final state.
"""

from typing import Dict, List, Tuple, Set, Any, Optional
from dataclasses import dataclass
from datetime import date
from lunar_python.util import LunarUtil

# ----------------------------------------------------------------------
# 1. Constants and mappings
# ----------------------------------------------------------------------

ELEMENTS = ["木", "火", "土", "金", "水"]
STEM_ELEMENT   = LunarUtil.WU_XING_GAN   # {stem → element}
BRANCH_ELEMENT = LunarUtil.WU_XING_ZHI   # {branch → element}

MONTH_SEASON: Dict[str, str] = {
    "寅": "春", "卯": "春", "辰": "春",
    "巳": "夏", "午": "夏", "未": "夏",
    "申": "秋", "酉": "秋", "戌": "秋",
    "亥": "冬", "子": "冬", "丑": "冬",
}

STRENGTH_WEIGHTS: Dict[str, float] = {
    "强势主流": 1.0,
    "显著影响": 0.75,
    "中等衰减": 0.50,
    "大幅衰减": 0.25,
    "消融吸收": 0.0,
}

_ROOT_RANK: Dict[str, int] = {"深根": 3, "中根": 2, "浅根": 1, "无根": 0}
_PILLAR_ORDER = ("年柱", "月柱", "日柱", "时柱")

_EARTH_BRANCH_END_JIEQI: Dict[str, str] = {
    "辰": "立夏",
    "未": "立秋",
    "戌": "立冬",
    "丑": "立春",
}

# ----------------------------------------------------------------------
# 2. Data structures
# ----------------------------------------------------------------------

@dataclass
class Interaction:
    type: str
    form: str
    pillars: List[str]
    element: str
    interaction_strength: float                   # 0.0–1.0 from STRENGTH_WEIGHTS
    root_strength: Optional[Tuple[str, str]] = None  # (weaker, stronger) for 六冲/天克地冲

# ----------------------------------------------------------------------
# 3. Qualitative classifier (旺 / 相 / 休 / 囚 / 死)
# ----------------------------------------------------------------------

# Classical seasonal base.
# Winter row (火囚/土死) diverges intentionally from day_master_strength._SEASONAL_TABLE
# (火死/土囚). Day-master scoring still uses that table; this one governs five-elements verdict.
SEASONAL_BASE: Dict[str, Dict[str, str]] = {
    "春": {"木": "旺", "火": "相", "土": "死", "金": "囚", "水": "休"},
    "夏": {"火": "旺", "土": "相", "木": "休", "金": "死", "水": "囚"},
    "秋": {"金": "旺", "水": "相", "土": "休", "木": "囚", "火": "死"},
    "冬": {"水": "旺", "木": "相", "金": "休", "火": "囚", "土": "死"},
}

# Occurs when it is the last 18 days of an Earth month (辰, 未, 戌, 丑)
EARTH_SEASONAL_BASE = {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"}

STATE_ORDER = ["死", "囚", "休", "相", "旺"]  # idx 0..4

# The excluded interaction types (残会, 暗合, 天干克, 天干冲, 伏吟, 比和) do not directly alter an element’s seasonal state in classical Bazi theory. They either have too weak an effect, are already represented by other factors (roots, visible branches), or are processed separately (天干合).
_ASYMMETRIC_CLASH_TYPES  = {"六冲", "天克地冲"}
_SYMMETRIC_CLASH_TYPES   = {"六害", "六破", "自刑", "无恩之刑", "恃势之刑", "无礼之刑"}
_COMBO_BOOST_BRANCH_TYPES = {"三会", "三合", "半合", "六合", "拱合", "拱会", "干支透合"}



class QualitativeFiveElementsClassifier:
    """Classical five-element state classifier for a natal BaZi chart.

    Emits one of 旺/相/休/囚/死 per element by applying seasonal base states,
    upgrades (roots, visible branch, combinations), downgrades (clash, void,
    stem-without-root), seasonal caps, and the 土旺用事 override.

    Args:
        si_zhu:                 Four-pillar dict keyed by 年柱/月柱/日柱/时柱.
                                Each pillar must contain 天干, 地支, 藏干, 空亡.
        natal_interactions_data: Raw output from get_natal_interactions; used to
                                extract typed Interaction objects.
        lunar_birthday:         lunar_python Lunar object for the birth date.
                                Required for 土旺用事 detection; pass None to skip.

    Usage:
        result = QualitativeFiveElementsClassifier(si_zhu, interactions, lunar_birthday=lb).classify_all()
    """

    def __init__(
        self,
        si_zhu: Dict[str, Any],
        natal_interactions_data: Dict[str, Any],
        lunar_birthday=None,
    ):
        self.si_zhu = si_zhu
        self.season = MONTH_SEASON[si_zhu["月柱"]["地支"]["地支"]]
        self.void_map = {
            key: any(
                v != "无"
                for k, v in (si_zhu[key].get("空亡", {}) or {}).items()
                if k != "本柱旬空"
            )
            for key in _PILLAR_ORDER
        }
        self.interactions = self._convert_interactions(natal_interactions_data)
        self.stem_transform, self.stem_cancelled = self._build_stem_overrides()
        self.earth_wang = self._check_earth_18_days(lunar_birthday)

    # ------------------------------------------------------------------
    # Interaction parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _convert_interactions(natal_interactions_data: Dict[str, Any]) -> List[Interaction]:
        """Parse 柱位动态 list into typed Interaction objects; skips 消融吸收 (strength=0)."""
        result: List[Interaction] = []
        for item in natal_interactions_data.get("作用", {}).get("柱位动态", []):
            raw_strength = item.get("强度", "强势主流")
            if raw_strength not in STRENGTH_WEIGHTS:
                raise ValueError(f"Unknown interaction strength label '{raw_strength}' in item: {item}")
            interaction_strength = STRENGTH_WEIGHTS[raw_strength]
            if interaction_strength == 0.0:
                continue
            type_ = item.get("类型", "")
            if not type_:
                raise ValueError(f"Interaction item is missing '类型': {item}")
            pillars = list(item.get("组合明细", {}).keys())
            root_strength: Optional[Tuple[str, str]] = None
            if type_ in ("六冲", "天克地冲") and len(pillars) == 2:
                根基 = item.get("根基", {})
                if 根基:
                    ranks = {p: _ROOT_RANK.get(根基.get(p, "无根"), 0) for p in pillars}
                    if ranks[pillars[0]] != ranks[pillars[1]]:
                        weaker   = min(pillars, key=lambda p: ranks[p])
                        stronger = max(pillars, key=lambda p: ranks[p])
                        root_strength = (weaker, stronger)
            result.append(Interaction(
                type=type_,
                form=item.get("形态", ""),
                pillars=pillars,
                element=item.get("元素", ""),
                interaction_strength=interaction_strength,
                root_strength=root_strength,
            ))
        return result

    # ------------------------------------------------------------------
    # Stem transformation pre-pass
    # ------------------------------------------------------------------

    def _build_stem_overrides(self) -> Tuple[Dict[str, str], Set[str]]:
        """Return (stem_transform, stem_cancelled) maps from 天干合 interactions.

        stem_transform: pillar → transformed element (合化/化气格 at ≥0.75 strength).
        stem_cancelled: pillars whose stems are neutralised (合绊).
        """
        transform: Dict[str, str] = {}
        cancelled: Set[str] = set()
        for inter in self.interactions:
            if inter.type != "天干合":
                continue
            if inter.form in ("合化", "化气格") and inter.element \
                    and inter.interaction_strength >= 0.75:
                for p in inter.pillars:
                    transform[p] = inter.element
            elif inter.form == "合绊":
                for p in inter.pillars:
                    cancelled.add(p)
            # 假化 / 遥合: stems retain original element — no override
        return transform, cancelled

    def _check_earth_18_days(self, lunar_birthday) -> bool:
        """Return True if the birth date falls within the 土旺用事 window.

        The window is the last 18 calendar days of an Earth month (辰/未/戌/丑),
        defined as 1 ≤ (end_of_season_term − birth_date).days ≤ 18.
        Born on the solar term itself (delta=0) is excluded — that day starts the next season.
        """
        month_branch = self.si_zhu["月柱"]["地支"]["地支"]
        if month_branch not in _EARTH_BRANCH_END_JIEQI or lunar_birthday is None:
            return False
        end_solar = lunar_birthday.getJieQiTable().get(_EARTH_BRANCH_END_JIEQI[month_branch])
        if end_solar is None:
            return False
        birth_solar = lunar_birthday.getSolar()
        end_date   = date(end_solar.getYear(),   end_solar.getMonth(),   end_solar.getDay())
        birth_date = date(birth_solar.getYear(), birth_solar.getMonth(), birth_solar.getDay())
        delta = (end_date - birth_date).days
        return 1 <= delta <= 18

    def _effective_stem_element(self, pillar: str) -> Optional[str]:
        """Return the element the pillar's stem represents after 天干合 transforms/cancellations."""
        if pillar in self.stem_cancelled:
            return None
        if pillar in self.stem_transform:
            return self.stem_transform[pillar]
        stem = self.si_zhu[pillar]["天干"]["天干"]
        element = STEM_ELEMENT.get(stem)
        if element is None:
            raise ValueError(f"Unknown stem '{stem}' in pillar {pillar}")
        return element

    # ------------------------------------------------------------------
    # Per-element factor extraction
    # ------------------------------------------------------------------

    def _hidden_stems_for_pillar(self, pillar: str) -> List[Tuple[str, str]]:
        """Return [(hidden_stem, depth_label)] from si_zhu['藏干']."""
        zang = self.si_zhu[pillar].get("藏干", {}) or {}
        return [
            (info["天干"], depth)
            for depth, info in zang.items()
        ]

    def _pillars_holding_element(self, element: str) -> Set[str]:
        """Return pillar keys where the element appears via effective stem, branch, or any hidden stem."""
        held: Set[str] = set()
        for p in _PILLAR_ORDER:
            if self._effective_stem_element(p) == element:
                held.add(p)
                continue
            branch = self.si_zhu[p]["地支"]["地支"]
            branch_el = BRANCH_ELEMENT.get(branch)
            if branch_el is None:
                raise ValueError(f"Unknown branch '{branch}' in pillar {p}")
            if branch_el == element:
                held.add(p)
                continue
            for hidden_stem, _ in self._hidden_stems_for_pillar(p):
                hs_el = STEM_ELEMENT.get(hidden_stem)
                if hs_el is None:
                    raise ValueError(f"Unknown hidden stem '{hidden_stem}' in pillar {p}")
                if hs_el == element:
                    held.add(p)
                    break
        return held

    _DEPTH_TIER = {"本气": 3, "中气": 2, "余气": 1}

    def _pillar_root_tier(self, element: str, pillar: str) -> int:
        """Root depth tier for element in a single pillar: 3=本气, 2=中气, 1=余气 or floating stem, 0=absent."""
        tier = 0
        for hidden_stem, depth in self._hidden_stems_for_pillar(pillar):
            hs_el = STEM_ELEMENT.get(hidden_stem)
            if hs_el is None:
                raise ValueError(f"Unknown hidden stem '{hidden_stem}' in pillar {pillar}")
            if depth not in self._DEPTH_TIER:
                raise ValueError(f"Unknown hidden stem depth '{depth}' in pillar {pillar}")
            if hs_el == element:
                tier = max(tier, self._DEPTH_TIER[depth])
        if tier == 0 and self._effective_stem_element(pillar) == element:
            tier = 1  # floating stem — weak but non-zero
        return tier

    def _gather_factors(self, element: str) -> Dict[str, Any]:
        """Collect all upgrade/downgrade signals for one element across the four pillars.

        Returns a dict with keys:
            same_element_hidden_stem, same_element_hidden_stem_root_depth, same_element_root_labels — hidden-stem root presence per pillar.
            strong_root          — True if any root is 本气.
            has_visible_branch   — True if any pillar branch matches this element.
            has_effective_presence — True if the element exists anywhere (effective stem, branch, or hidden stem).
            has_combination_boost — True if a qualifying branch/stem combo targets this element.
            combo_descriptions   — human-readable combo labels for 依据 audit.
            is_clashed           — True if the element's dominant root is on the weak side of a clash.
            clash_descriptions   — clash labels that triggered the downgrade.
            absorbed_descriptions — clashes that were absorbed (weaker or equal root on clashed side).
            void_penalty         — True when max void-pillar root tier > max non-void-pillar root tier.
            has_stem_without_root — True if a visible stem carries this element but no hidden root exists.
        """
        same_element_hidden_stem: List[str] = []
        same_element_hidden_stem_root_depth: List[str]   = []
        same_element_root_labels: List[str]   = []
        for p in _PILLAR_ORDER:
            for hidden_stem, depth in self._hidden_stems_for_pillar(p):
                hs_el = STEM_ELEMENT.get(hidden_stem)
                if hs_el is None:
                    raise ValueError(f"Unknown hidden stem '{hidden_stem}' in pillar {p}")
                if hs_el == element:
                    same_element_hidden_stem.append(p)
                    same_element_hidden_stem_root_depth.append(depth)
                    same_element_root_labels.append(f"{p}({depth})")
        strong_root = "本气" in same_element_hidden_stem_root_depth

        has_visible_branch = False
        for p in _PILLAR_ORDER:
            branch = self.si_zhu[p]["地支"]["地支"]
            branch_el = BRANCH_ELEMENT.get(branch)
            if branch_el is None:
                raise ValueError(f"Unknown branch '{branch}' in pillar {p}")
            if branch_el == element:
                has_visible_branch = True
                break

        has_effective_presence = (
            any(self._effective_stem_element(p) == element for p in _PILLAR_ORDER)
            or has_visible_branch
            or bool(same_element_hidden_stem)
        )

        combo_descriptions: List[str] = []
        for inter in self.interactions:
            if inter.interaction_strength < 0.75 or inter.element != element:
                continue
            if inter.type in _COMBO_BOOST_BRANCH_TYPES:
                combo_descriptions.append(
                    f"{inter.type} {self._strength_label(inter.interaction_strength)}"
                )
            elif inter.type == "天干合" and inter.form in ("合化", "化气格"):
                combo_descriptions.append(f"天干合({inter.form})")
        has_combination_boost = bool(combo_descriptions)

        held_pillars = self._pillars_holding_element(element)
        clash_descriptions:    List[str] = []
        absorbed_descriptions: List[str] = []
        clashed_held: Set[str] = set()

        for inter in self.interactions:
            if inter.interaction_strength < 0.5:
                continue
            if inter.type in _ASYMMETRIC_CLASH_TYPES:
                weak_pillar, _ = inter.root_strength if inter.root_strength else (inter.pillars[0], None)
                affected = {weak_pillar}
            elif inter.type in _SYMMETRIC_CLASH_TYPES:
                affected = set(inter.pillars)
            else:
                continue
            hit = held_pillars & affected
            if not hit:
                continue
            label = f"{inter.type}({'/'.join(inter.pillars)})"
            max_clashed_tier   = max((self._pillar_root_tier(element, p) for p in hit), default=0)
            max_unclashed_tier = max(
                (self._pillar_root_tier(element, p) for p in (held_pillars - hit)), default=0
            )
            if max_clashed_tier > max_unclashed_tier:
                clash_descriptions.append(label)
                clashed_held |= hit
            else:
                absorbed_descriptions.append(label)
        is_clashed = bool(clash_descriptions)

        max_void_tier = max(
            (self._pillar_root_tier(element, p) for p in held_pillars if self.void_map.get(p, False)),
            default=0,
        )
        max_non_void_tier = max(
            (self._pillar_root_tier(element, p) for p in held_pillars if not self.void_map.get(p, False)),
            default=0,
        )
        void_penalty = max_void_tier > max_non_void_tier

        has_stem_without_root = (
            any(self._effective_stem_element(p) == element for p in _PILLAR_ORDER)
            and not same_element_hidden_stem
        )

        return {
            "same_element_hidden_stem":       same_element_hidden_stem,
            "same_element_hidden_stem_root_depth":         same_element_hidden_stem_root_depth,
            "same_element_root_labels":         same_element_root_labels,
            "strong_root":         strong_root,
            "has_visible_branch":  has_visible_branch,
            "has_effective_presence": has_effective_presence,
            "has_combination_boost": has_combination_boost,
            "combo_descriptions":  combo_descriptions,
            "is_clashed":          is_clashed,
            "clash_descriptions":  clash_descriptions,
            "absorbed_descriptions": absorbed_descriptions,
            "void_penalty":        void_penalty,
            "has_stem_without_root": has_stem_without_root,
        }

    @staticmethod
    def _strength_label(strength: float) -> str:
        """Convert numeric interaction strength back to its Chinese tier label for audit output."""
        if strength >= 1.0:  return "强势主流"
        if strength >= 0.75: return "显著影响"
        if strength >= 0.5:  return "中等衰减"
        if strength > 0.0:   return "大幅衰减"
        return "消融吸收"

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def _classify_one(self, element: str) -> Dict[str, Any]:
        """Compute the classical state (旺/相/休/囚/死) for a single element.

        Applies seasonal base → upgrades → downgrades → seasonal cap in order.
        Non-ruling elements are capped at min(base_idx + 2, 3) = max 相, unless a full
        三合/三会 at ≥0.75 strength is present (overrides the cap to allow 旺).

        Uncomment the 依据 block below to include a per-factor audit dict in the output.
        """
        base_state = EARTH_SEASONAL_BASE[element] if self.earth_wang else SEASONAL_BASE[self.season][element]
        idx = STATE_ORDER.index(base_state)
        f = self._gather_factors(element)

        # Upgrades
        if len(f["same_element_hidden_stem"]) >= 2: idx += 1
        if f["strong_root"]:             idx += 1
        if f["has_visible_branch"]:      idx += 1
        if f["has_combination_boost"]:   idx += 1

        # Downgrades
        if f["has_stem_without_root"]:   idx -= 1
        if f["is_clashed"]:              idx -= 1
        if f["void_penalty"]:            idx -= 1

        idx = max(0, min(4, idx))

        # Override: completely absent element cannot hold any active state
        if not f["has_effective_presence"]:
            idx = 0

        # Seasonal cap: only the ruling element may be 旺.
        # Non-ruling elements are capped at one step above their seasonal base,
        # ceiling 相. Exception: a full 三合/三会 at ≥ 0.75 overrides the cap.
        has_dominant_combo = any(
            inter.type in ("三合", "三会")
            and inter.element == element
            and inter.interaction_strength >= 0.75
            for inter in self.interactions
        )
        base_idx = STATE_ORDER.index(base_state)
        if base_idx < 4 and not has_dominant_combo:
            max_idx = min(base_idx + 2, 3)
            if idx > max_idx:
                idx = max_idx

        return {
            "状态": STATE_ORDER[idx],
            # For debugging and interpretability
            # "依据": {
            #     "季节基态": base_state,
            #     "土旺用事": self.earth_wang,
            #     "通根": f["same_element_root_labels"],
            #     "本气根": f["strong_root"],
            #     "见支": f["has_visible_branch"],
            #     "助合": "; ".join(f["combo_descriptions"]) if f["combo_descriptions"] else "",
            #     "受冲": "; ".join(f["clash_descriptions"]) if f["clash_descriptions"] else False,
            #     "受冲(吸收)": "; ".join(f["absorbed_descriptions"]) if f["absorbed_descriptions"] else False,
            #     "空亡": f["void_penalty"],
            #     "无根透干": f["has_stem_without_root"],
            #     "缺失": not f["has_effective_presence"],
            # },
        }

    def classify_all(self) -> Dict[str, Any]:
        """Classify all five elements and return the 五行 payload for the natal chart."""
        return {"五行": {element: self._classify_one(element) for element in ELEMENTS}}


def get_pillar_five_elements(pillars: Dict[str, Any]) -> Dict[str, Any]:
    """Return the five-element category for each component of all four pillars.

    Pure structural lookup — requires only the pillars dict, no interactions or classifier state.

    Returns:
        {
            "年柱": { "天干五行": "木", "地支五行": "水", "藏干五行": { "本气": "水", ... } },
            ...
        }
    """
    result: Dict[str, Any] = {}
    for key in _PILLAR_ORDER:
        p = pillars[key]
        stem = p["天干"]
        stem_el = STEM_ELEMENT.get(stem)
        if stem_el is None:
            raise ValueError(f"Unknown stem '{stem}' in pillar {key}")
        branch = p["地支"]
        branch_el = BRANCH_ELEMENT.get(branch)
        if branch_el is None:
            raise ValueError(f"Unknown branch '{branch}' in pillar {key}")
        zang_wu_xing: Dict[str, str] = {}
        for tier, info in p.get("藏干", {}).items():
            hs = info["天干"]
            hs_el = STEM_ELEMENT.get(hs)
            if hs_el is None:
                raise ValueError(f"Unknown hidden stem '{hs}' in pillar {key} tier {tier}")
            zang_wu_xing[tier] = hs_el
        result[key] = {
            "天干五行": stem_el,
            "地支五行": branch_el,
            "藏干五行": zang_wu_xing,
        }
    return result


# ============================================================================
# EXECUTION
# python -m apps.backend.astronomer_logic.natal_five_elements
# ============================================================================

if __name__ == "__main__":
    import json
    from datetime import datetime as dt
    from apps.backend.astronomer_logic.true_solar_time import get_true_solar_time
    from apps.backend.astronomer_logic.bazi_pillars import get_bazi_pillars
    from apps.backend.astronomer_logic.void_xun_kong import get_void_xun_kong, check_pillar_void_status
    from apps.backend.astronomer_logic.ten_gods import get_ten_gods
    from apps.backend.astronomer_logic.natal_interactions import get_natal_interactions
    from apps.utils.logging import configure_logging, get_logger

    configure_logging()
    logger = get_logger(__name__)

    subjects = {
        # "Desmond": (dt(1985, 11, 25, 17, 7, 0), 1.3253, 103.808053, 1),
        "Corinne": (dt(1987, 6, 3, 12, 6, 0), 1.4759, 103.808053, 0),
        # "Lara":    (dt(2025,  7, 31,  9, 10, 0), 1.3253,  103.808053, 0),
    }

    for name, (birthday, lat, lon, gender) in subjects.items():
        logger.info("=" * 60)
        logger.info("Subject: %s  (%s)", name, birthday.strftime("%Y-%m-%d %H:%M"))

        tst_birthday = get_true_solar_time(birthday, lat, lon)
        bazi = tst_birthday.getLunar().getEightChar()
        pillars = get_bazi_pillars(bazi)
        void = get_void_xun_kong(bazi)
        void_status = check_pillar_void_status(void, pillars)
        ten_gods = get_ten_gods(bazi)

        for k in ["年柱", "月柱", "日柱", "时柱"]:
            for tier, info in pillars[k]["藏干"].items():
                info["十神"] = ten_gods[k]["藏干十神"].get(tier, "无")
            pillars[k]["空亡"] = void_status[k]["空亡"]

        lunar_bday = tst_birthday.getLunar()
        interactions = get_natal_interactions(pillars, void)
        result = QualitativeFiveElementsClassifier(pillars, interactions, lunar_birthday=lunar_bday).classify_all()
        logger.info(json.dumps(result, ensure_ascii=False, indent=2))
