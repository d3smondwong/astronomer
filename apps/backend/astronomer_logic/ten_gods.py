"""
十神 Ten Gods (Shi Shen)

Returns the Ten God relationship for each stem position across the Four Pillars
(年柱, 月柱, 日柱, 时柱). Each pillar contains:
  - heavenly_stem_ten_god — Ten God of the 天干
  - primary_qi_ten_god    — Ten God of the 本气 hidden stem (or None)
  - middle_qi_ten_god     — Ten God of the 中气 hidden stem (or None)
  - residual_qi_ten_god   — Ten God of the 余气 hidden stem (or None)

The 日柱 天干 is always "日主" (Day Master — the self reference).
"""

import copy

from lunar_python.util import LunarUtil
from apps.backend.astronomer_logic.bazi_pillars import _YANG_STEMS, compute_single_stem_rooting
_ELEMENT_YANG_STEM: dict[str, str] = {"木": "甲", "火": "丙", "土": "戊", "金": "庚", "水": "壬"}
_ELEMENT_YIN_STEM:  dict[str, str] = {"木": "乙", "火": "丁", "土": "己", "金": "辛", "水": "癸"}

_PILLAR_KEYS = ["年柱", "月柱", "日柱", "时柱"]

# 天干五合 pairs — 甲己, 乙庚, 丙辛, 丁壬, 戊癸
_WU_HE_PAIRS: frozenset = frozenset({
    frozenset({"甲", "己"}),
    frozenset({"乙", "庚"}),
    frozenset({"丙", "辛"}),
    frozenset({"丁", "壬"}),
    frozenset({"戊", "癸"}),
})


def _ten_god_for_transformed(original_stem: str, transformed_element: str, dm_stem: str) -> str:
    """Ten god for a stem whose element has transformed to transformed_element, relative to dm_stem.

    Preserves the original stem's yin/yang polarity when selecting the effective stem.
    Uses LunarUtil.SHI_SHEN for the final lookup.
    """
    effective_stem = (
        _ELEMENT_YANG_STEM[transformed_element]
        if original_stem in _YANG_STEMS
        else _ELEMENT_YIN_STEM[transformed_element]
    )
    return LunarUtil.SHI_SHEN.get(dm_stem + effective_stem, "无")


def _hidden_ten_gods(shi_shen_zhi: list) -> tuple:
    """Unpack up to 3 Ten Gods for the hidden stems (本气, 中气, 余气), padding with "无"."""
    gods = list(shi_shen_zhi) + ["无", "无", "无"]
    return gods[0] or "无", gods[1] or "无", gods[2] or "无"


def get_ten_gods(bazi) -> dict:
    """
    Return the Ten Gods for each of the Four Pillars.

    Args:
        bazi: EightChar object from lunar_birthday.getEightChar()

    Returns:
        dict keyed by 年柱, 月柱, 日柱, 时柱.
        Each pillar contains: heavenly_stem_ten_god, primary_qi_ten_god,
                              middle_qi_ten_god, residual_qi_ten_god.
        Hidden stem Ten Gods that are not present are returned as "无".
    """
    def make_pillar(heavenly_stem_ten_god: str, zhi_gods_fn) -> dict:
        primary_qi_ten_god, middle_qi_ten_god, residual_qi_ten_god = _hidden_ten_gods(zhi_gods_fn())
        return {
            "天干十神": heavenly_stem_ten_god,
            "藏干十神": {
                "本气": primary_qi_ten_god,
                "中气": middle_qi_ten_god,
                "余气": residual_qi_ten_god,
            },
        }

    return {
        "年柱": make_pillar(bazi.getYearShiShenGan(),  bazi.getYearShiShenZhi),
        "月柱": make_pillar(bazi.getMonthShiShenGan(), bazi.getMonthShiShenZhi),
        "日柱": make_pillar("日主",                     bazi.getDayShiShenZhi),
        "时柱": make_pillar(bazi.getTimeShiShenGan(),  bazi.getTimeShiShenZhi),
    }


def apply_heavenlystem_tranformation_tengods(
    ten_gods: dict,
    si_zhu: dict,
    interactions_data: dict,
    day_master_stem: str,
) -> tuple[dict, dict]:
    """
    Returns (updated_ten_gods, updated_si_zhu) with 合化/化气格 ten god overrides applied.

    合化  — update 天干十神 for the two affected pillars only; 藏干十神 unchanged
            (DM and hidden stems are both unaffected, so their relationship is the same).
    化气格 — DM element changes; recalculate 天干十神 + 藏干十神 for ALL non-DM pillars.
    假化 / 合绊 / 遥合 — no change.
    """
    ten_gods = copy.deepcopy(ten_gods)
    si_zhu   = copy.deepcopy(si_zhu)

    _PILLAR_ORDER = ("年柱", "月柱", "日柱", "时柱")
    _zhis  = [si_zhu[p]["地支"]["地支"] for p in _PILLAR_ORDER]
    _hides = [
        [si_zhu[p]["藏干"].get(t, {}).get("天干", "无") for t in ("本气", "中气", "余气")]
        for p in _PILLAR_ORDER
    ]
    _pillar_cn: list[str] = list(_PILLAR_ORDER)

    for interaction in interactions_data["作用"]["柱位动态"]:
        if interaction.get("类型") != "天干合":
            continue
        形态 = interaction.get("形态")
        if 形态 != "化气格":
            continue

        transformed_element = interaction["合化条件"]["合化元素"]

        # DM transforms → derive the new effective DM stem (same polarity, new element)
        new_dm_stem = (
            _ELEMENT_YANG_STEM[transformed_element]
            if day_master_stem in _YANG_STEMS
            else _ELEMENT_YIN_STEM[transformed_element]
        )
        original_dm_element = LunarUtil.WU_XING_GAN.get(day_master_stem, "无")
        si_zhu["日柱"]["化气格信息"] = {"类型": "化气格", "原五行": original_dm_element, "现五行": transformed_element}
        si_zhu["日柱"]["天干"]["五行"] = transformed_element
        new_rooting = compute_single_stem_rooting(transformed_element, _zhis, _hides, _pillar_cn)
        si_zhu["日柱"]["天干"]["根基强度"] = new_rooting["根基强度"]
        si_zhu["日柱"]["天干"]["通根于"]   = new_rooting["通根于"]
        for partner in interaction["组合明细"]:
            if partner == "日柱":
                continue
            original_partner_element = si_zhu[partner]["天干"].get("五行", "无")
            si_zhu[partner]["化气格信息"]       = {"类型": "化气格", "原五行": original_partner_element, "现五行": transformed_element}
            si_zhu[partner]["天干"]["五行"]      = transformed_element
            si_zhu[partner]["天干"]["根基强度"]  = new_rooting["根基强度"]
            si_zhu[partner]["天干"]["通根于"]    = new_rooting["通根于"]

        for pillar in ("年柱", "月柱", "日柱", "时柱"):
            original_visible_stem_tengod = ten_gods[pillar]["天干十神"]
            original_hidden_stem_tengod  = dict(ten_gods[pillar]["藏干十神"])

            if pillar != "日柱":
                stem = si_zhu[pillar]["天干"]["天干"]
                new_visible_stem_tengod = LunarUtil.SHI_SHEN.get(new_dm_stem + stem, "无")
                ten_gods[pillar]["天干十神"] = new_visible_stem_tengod
                si_zhu[pillar]["天干"]["十神"] = new_visible_stem_tengod

            for tier, tier_info in si_zhu[pillar]["藏干"].items():
                hidden_stem = tier_info.get("天干", "无")
                if hidden_stem and hidden_stem != "无":
                    new_hidden_stem_tengod = LunarUtil.SHI_SHEN.get(new_dm_stem + hidden_stem, "无")
                    ten_gods[pillar]["藏干十神"][tier] = new_hidden_stem_tengod
                    tier_info["十神"] = new_hidden_stem_tengod

            if original_visible_stem_tengod != ten_gods[pillar]["天干十神"] or original_hidden_stem_tengod != ten_gods[pillar]["藏干十神"]:
                si_zhu[pillar]["化气格变化"] = {
                    "原天干十神": original_visible_stem_tengod,
                    "原藏干十神": original_hidden_stem_tengod,
                }

    return ten_gods, si_zhu


_ADJACENT_PILLAR_PAIRS: list[tuple[str, str]] = [
    ("年柱", "月柱"),
    ("月柱", "日柱"),
    ("日柱", "时柱"),
]

_ROOTED_TIERS = ("中根", "深根")


def _pillar_gods(ten_gods: dict, pillar: str) -> set[str]:
    """All Ten God labels (heavenly stem + hidden tiers) present in one pillar."""
    gods = {ten_gods[pillar]["天干十神"]}
    gods.update(ten_gods[pillar]["藏干十神"].values())
    return gods


def _adjacent_pillars(pillar: str) -> list[str]:
    return [
        other
        for p1, p2 in _ADJACENT_PILLAR_PAIRS
        for other in ((p2,) if p1 == pillar else (p1,) if p2 == pillar else ())
    ]


def _ten_god_occurrences(ten_gods: dict, god: str) -> list[tuple[str, str]]:
    """Every (pillar, position) holding the given Ten God label; position is '天干' or a 藏干 tier."""
    occurrences = []
    for p in _PILLAR_KEYS:
        if ten_gods[p]["天干十神"] == god:
            occurrences.append((p, "天干"))
        for tier, tier_god in ten_gods[p]["藏干十神"].items():
            if tier_god == god:
                occurrences.append((p, tier))
    return occurrences


def apply_qi_sha_transformation(
    ten_gods: dict,
    si_zhu: dict,
    day_master_data: dict,
) -> tuple[dict, dict]:
    """
    七杀 → 偏官: transforms individual 七杀 occurrences when a classical taming
    condition reaches them. Different 七杀 in the same chart can end up on
    different sides — one tamed, one not — depending on which condition is
    positionally in reach of each one.

    Conditions (checked per-occurrence, in priority order):
      1. 食神克七杀 — a 食神 (heavenly or hidden, any tier) sits on the same or
         an adjacent pillar to this 七杀.
      2. 印化杀     — a 正印/偏印 is available (revealed on a heavenly stem, or
         a branch's 本气) anywhere in the chart; no proximity needed since the
         Seal works through the Day Master. A rooted (中根+) or doubled-up
         Seal tames any number of 七杀. A weak, unrooted, single-occurrence
         Seal (浅根/无根) can only tame one — with 2+ 七杀 chart-wide it is
         overwhelmed (杀重印轻) and transforms none.
      3. 阳刃合杀   — Yang DM only: this 七杀's heavenly stem forms a 天干五合
         with a 劫财 heavenly stem on the adjacent pillar.
      4. 身旺制煞   — DM strength ∈ {旺, 极旺}, exactly 1 七杀 in the whole
         chart, and that 七杀 is not the month pillar's 本气.

    Updates both ten_gods and si_zhu (deep-copied internally).
    Stores '七杀化偏官' metadata per transformed position, e.g.
    si_zhu[pillar]["七杀化偏官"] = {"天干": "食神克七杀", "本气": "印化杀"}.
    """
    occurrences = _ten_god_occurrences(ten_gods, "七杀")
    if not occurrences:
        return ten_gods, si_zhu

    dm_stem      = si_zhu["日柱"]["天干"]["天干"]
    is_yang_dm   = dm_stem in _YANG_STEMS
    dm_strength  = day_master_data.get("日主", {}).get("强弱", "")
    month_ben_qi = ten_gods["月柱"]["藏干十神"].get("本气", "")

    # ── 印化杀 availability: stem-revealed or 本气 only ──────────────────────
    yin_occurrences = (
        [(p, "天干") for p in _PILLAR_KEYS if ten_gods[p]["天干十神"] in ("正印", "偏印")]
        + [(p, "本气") for p in _PILLAR_KEYS if ten_gods[p]["藏干十神"].get("本气") in ("正印", "偏印")]
    )
    yin_is_strong = len(yin_occurrences) >= 2 or any(
        position == "天干" and si_zhu[p]["天干"].get("根基强度") in _ROOTED_TIERS
        for p, position in yin_occurrences
    )
    yin_transforms_all = bool(yin_occurrences) and (yin_is_strong or len(occurrences) == 1)

    # ── 阳刃合杀: Yang DM heavenly-stem 五合 on adjacent pillars ─────────────
    heavenly = {p: (si_zhu[p]["天干"]["天干"], ten_gods[p]["天干十神"]) for p in _PILLAR_KEYS}
    yang_ren_he_pillars: set[str] = set()
    if is_yang_dm:
        for p1, p2 in _ADJACENT_PILLAR_PAIRS:
            s1, g1 = heavenly[p1]
            s2, g2 = heavenly[p2]
            if frozenset({s1, s2}) in _WU_HE_PAIRS:
                if g1 == "劫财" and g2 == "七杀":
                    yang_ren_he_pillars.add(p2)
                elif g2 == "劫财" and g1 == "七杀":
                    yang_ren_he_pillars.add(p1)

    # ── 身旺制煞: strong DM, sole 七杀 in chart, not month 本气 ───────────────
    has_strong_dm_single_sha = (
        dm_strength in ("旺", "极旺")
        and len(occurrences) == 1
        and month_ben_qi != "七杀"
    )

    def _trigger_for(pillar: str, position: str) -> str | None:
        reach = {pillar, *_adjacent_pillars(pillar)}
        if any("食神" in _pillar_gods(ten_gods, p) for p in reach):
            return "食神克七杀"
        if yin_transforms_all:
            return "印化杀"
        if position == "天干" and pillar in yang_ren_he_pillars:
            return "阳刃合杀"
        if has_strong_dm_single_sha:
            return "身旺制煞"
        return None

    triggers = {occ: _trigger_for(*occ) for occ in occurrences}
    if not any(triggers.values()):
        return ten_gods, si_zhu

    # ── Transform only the qualifying 七杀 occurrences → 偏官 ────────────────
    ten_gods = copy.deepcopy(ten_gods)
    si_zhu   = copy.deepcopy(si_zhu)

    for (pillar, position), trigger in triggers.items():
        if not trigger:
            continue
        if position == "天干":
            ten_gods[pillar]["天干十神"]   = "偏官"
            si_zhu[pillar]["天干"]["十神"] = "偏官"
        else:
            ten_gods[pillar]["藏干十神"][position]  = "偏官"
            si_zhu[pillar]["藏干"][position]["十神"] = "偏官"
        si_zhu[pillar].setdefault("七杀化偏官", {})[position] = trigger

    return ten_gods, si_zhu


# Unified occurrence-strength scale — lower rank is stronger. Interleaves stem
# rooting depth with hidden-tier depth: a stem needs both 透干 (surfacing) and
# 通根 (rooting) to lead; a merely shallow-rooted stem is weaker than a
# branch's undisturbed 本气, and a wholly unrooted (无根) stem is the weakest
# occurrence of all — weaker even than a trace 余气.
_STRENGTH_RANK: dict[tuple[str, str], int] = {
    ("天干", "深根"): 1,
    ("天干", "中根"): 2,
    ("藏干", "本气"): 3,
    ("天干", "浅根"): 4,
    ("藏干", "中气"): 5,
    ("藏干", "余气"): 6,
    ("天干", "无根"): 7,
}


def _occurrence_rank(si_zhu: dict, pillar: str, position: str) -> int:
    """Lower is stronger. position is '天干' or a 藏干 tier."""
    if position == "天干":
        return _STRENGTH_RANK[("天干", si_zhu[pillar]["天干"].get("根基强度", "无根"))]
    return _STRENGTH_RANK[("藏干", position)]


def _has_wealth_rescue(ten_gods: dict, pillar: str) -> bool:
    """A 正财/偏财 on this pillar or an adjacent one restrains a 偏印 sitting here (财克印)."""
    reach = {pillar, *_adjacent_pillars(pillar)}
    return any({"正财", "偏财"} & _pillar_gods(ten_gods, p) for p in reach)


def apply_shi_shen_transformation(
    ten_gods: dict,
    si_zhu: dict,
) -> tuple[dict, dict]:
    """
    食神 → 伤官: transforms individual 食神 occurrences under two classical
    conditions, checked in priority order.

      1. 食神重逢 — 3+ 食神 chart-wide (heavenly stem + every hidden tier,
         counted individually). Global, no proximity or strength check: too
         much of a good thing tips every 食神 into 伤官.
      2. 枭神夺食 — a 偏印 on the same or an adjacent pillar strictly
         outranks this 食神 on the unified strength scale (see
         _STRENGTH_RANK). A 正财/偏财 on that 偏印's own pillar or an
         adjacent one restrains it (财克印), so a rescued 偏印 cannot trigger
         the transformation even if it would otherwise outrank the 食神.

    Note: 食神 meeting 七杀 does NOT transform the food god — that encounter
    is handled by apply_qi_sha_transformation, which tames the 七杀 into 偏官
    while the 食神 stays 食神 (食神制杀); transforming both sides of that
    encounter would be self-contradictory.

    Updates both ten_gods and si_zhu (deep-copied internally).
    Stores '食神化伤官' metadata per transformed position, e.g.
    si_zhu[pillar]["食神化伤官"] = {"天干": "食神重逢", "本气": "枭神夺食"}.
    """
    occurrences = _ten_god_occurrences(ten_gods, "食神")
    if not occurrences:
        return ten_gods, si_zhu

    is_excess = len(occurrences) >= 3
    pian_yin_occurrences = _ten_god_occurrences(ten_gods, "偏印")

    def _trigger_for(pillar: str, position: str) -> str | None:
        if is_excess:
            return "食神重逢"
        reach = {pillar, *_adjacent_pillars(pillar)}
        shi_shen_rank = _occurrence_rank(si_zhu, pillar, position)
        surviving_ranks = [
            _occurrence_rank(si_zhu, py_pillar, py_position)
            for py_pillar, py_position in pian_yin_occurrences
            if py_pillar in reach and not _has_wealth_rescue(ten_gods, py_pillar)
        ]
        if surviving_ranks and min(surviving_ranks) < shi_shen_rank:
            return "枭神夺食"
        return None

    triggers = {occ: _trigger_for(*occ) for occ in occurrences}
    if not any(triggers.values()):
        return ten_gods, si_zhu

    ten_gods = copy.deepcopy(ten_gods)
    si_zhu   = copy.deepcopy(si_zhu)

    for (pillar, position), trigger in triggers.items():
        if not trigger:
            continue
        if position == "天干":
            ten_gods[pillar]["天干十神"]   = "伤官"
            si_zhu[pillar]["天干"]["十神"] = "伤官"
        else:
            ten_gods[pillar]["藏干十神"][position]  = "伤官"
            si_zhu[pillar]["藏干"][position]["十神"] = "伤官"
        si_zhu[pillar].setdefault("食神化伤官", {})[position] = trigger

    return ten_gods, si_zhu
