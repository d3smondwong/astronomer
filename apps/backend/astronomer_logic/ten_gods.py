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


def apply_qi_sha_transformation(
    ten_gods: dict,
    si_zhu: dict,
    day_master_data: dict,
) -> tuple[dict, dict]:
    """
    七杀 → 偏官: transforms all 七杀 occurrences when any classical condition is met.

    Conditions (any one suffices, checked in priority order):
      1. 食神克七杀 — any 食神 exists anywhere (heavenly or hidden stem)
      2. 印化杀     — any 正印 or 偏印 exists anywhere (heavenly or hidden stem)
      3. 阳刃合杀   — Yang DM only: a 劫财 heavenly stem + a 七杀 heavenly stem form a 天干五合
      4. 身旺制煞   — DM strength ∈ {旺, 极旺}, exactly 1 七杀 total, 七杀 not month 本气

    Updates both ten_gods and si_zhu (deep-copied internally).
    Stores '七杀化偏官' metadata on each pillar where a 七杀 was changed.
    """
    # ── Conditions 1 & 2: scan all ten gods (heavenly + hidden) ──────────────
    all_gods: set[str] = {ten_gods[p]["天干十神"] for p in _PILLAR_KEYS}
    for p in _PILLAR_KEYS:
        all_gods.update(ten_gods[p]["藏干十神"].values())

    has_shi_shen = "食神" in all_gods
    has_yin      = bool({"正印", "偏印"} & all_gods)

    # ── Condition 3: Yang DM + 劫财/七杀 heavenly-stem 五合 ──────────────────
    dm_stem    = si_zhu["日柱"]["天干"]["天干"]
    is_yang_dm = dm_stem in _YANG_STEMS

    heavenly  = [(si_zhu[p]["天干"]["天干"], ten_gods[p]["天干十神"]) for p in _PILLAR_KEYS]
    jie_cai   = [s for s, g in heavenly if g == "劫财"]
    qi_sha_hs = [s for s, g in heavenly if g == "七杀"]

    has_yang_ren_he = is_yang_dm and any(
        frozenset({jc, qs}) in _WU_HE_PAIRS
        for jc in jie_cai
        for qs in qi_sha_hs
    )

    # ── Condition 4: strong DM, single 七杀, not month 本气 ──────────────────
    dm_strength = day_master_data.get("日主", {}).get("强弱", "")

    qi_sha_count = sum(
        1
        for p in _PILLAR_KEYS
        for god in ([ten_gods[p]["天干十神"]] + list(ten_gods[p]["藏干十神"].values()))
        if god == "七杀"
    )
    month_ben_qi = ten_gods["月柱"]["藏干十神"].get("本气", "")

    has_strong_dm = (
        dm_strength in ("旺", "极旺")
        and qi_sha_count == 1
        and month_ben_qi != "七杀"
    )

    # ── Determine trigger ─────────────────────────────────────────────────────
    trigger = (
        "食神克七杀" if has_shi_shen    else
        "印化杀"     if has_yin         else
        "阳刃合杀"   if has_yang_ren_he else
        "身旺制煞"   if has_strong_dm   else
        None
    )
    if not trigger:
        return ten_gods, si_zhu

    # ── Transform all 七杀 → 偏官 ─────────────────────────────────────────────
    ten_gods = copy.deepcopy(ten_gods)
    si_zhu   = copy.deepcopy(si_zhu)

    for pillar in _PILLAR_KEYS:
        changed = False
        if ten_gods[pillar]["天干十神"] == "七杀":
            ten_gods[pillar]["天干十神"]   = "偏官"
            si_zhu[pillar]["天干"]["十神"] = "偏官"
            changed = True
        for tier in ("本气", "中气", "余气"):
            if ten_gods[pillar]["藏干十神"].get(tier) == "七杀":
                ten_gods[pillar]["藏干十神"][tier] = "偏官"
            if tier in si_zhu[pillar]["藏干"] and si_zhu[pillar]["藏干"][tier].get("十神") == "七杀":
                si_zhu[pillar]["藏干"][tier]["十神"] = "偏官"
                changed = True
        if changed:
            si_zhu[pillar]["七杀化偏官"] = {"触发条件": trigger}

    return ten_gods, si_zhu
