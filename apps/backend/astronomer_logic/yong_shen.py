"""
用神 (Favorable Gods) — the two canonical 子平 methods, combined per element.

Two mainstream 用神 systems, each contributing what it legitimately owns:

  • 调候用神 (climate adjustment) — from CLIMATE_DATA[日干+月支], both the 喜 stems (what
    the chart NEEDS) and the 忌 stems (what damages it). All 120 entries carry both.

  • 扶抑用神 (support / suppress) — from the 日主强弱 verdict. A weak day master
    favors 印/比 (support) and is burdened by 财/官/食; a strong one is the reverse.
    This is where a principled 忌 legitimately comes from — it is textbook 扶抑, not
    a fabricated rule.

So 喜 = 调候喜 ∪ 扶抑喜; 忌 = 调候忌 ∪ 扶抑忌. Nothing is conjured — both systems state
only what their source states. Where they disagree on an element, 调候 leads and the
element carries a 争 note; the 经典 prose is the right place to adjudicate that tension,
not a hard engine rule.

调候忌 matters most for a 中和 chart: 扶抑 is 平 across the board when the day master is
balanced, so without it such a chart would have NO 忌 at all — and ~24% of charts are
中和. That is not "nothing to avoid"; it is a missing input.

五神 — 仇神 and 闲神 complete the set
------------------------------------
喜/忌 name only three of the classical five gods (用神, 喜神, 忌神). The remaining two are
NOT a further verdict: they are a SPLIT of the 平 leftovers.

  • 仇神 = 生忌神者 — an element that is neither wanted nor feared in itself, but FEEDS one
    the chart fears (金生水 when 水 is 忌 → 金 is 仇).
  • 闲神 = the genuine idlers.

喜/忌 always win the label. That precedence is load-bearing, not tidiness: 喜用/忌 are SETS
(调候 ∪ 扶抑, or structure-derived), so an element that generates a 忌 element can already be
喜用 — a weak 戊 fearing 金 still has 土生金, yet 土 is its 用神. Classically 仇神 is by
definition neither 用 nor 忌, so the split runs as a second pass over the 平 bucket only.

The 克喜用神者 formulation is deliberately NOT encoded: under 扶抑, whatever attacks the 用神
is already tagged 忌, so that rule would mostly restate a verdict we hold anyway.

Consequence: on a 弱/旺 正格 chart 仇 and 闲 are BOTH empty — 扶抑 tags all five elements 喜 or
忌 and nothing is left idle. 仇神 can only fire where the 平 bucket exists: 中和 charts (~24%,
where only 调候 speaks) and 非正格 charts whose 十神 category is in neither PATTERN_MAPPING
list. An empty 仇 on a weak chart is the right answer, not a gap.

Output (Chinese-keyed) — see get_yong_shen.
"""

from lunar_python.util import LunarUtil

from apps.backend.astronomer_logic.ge_ju import detect_ge_ju
from apps.backend.astronomer_logic.wu_xing_relations import (
    ELEMENTS,
    GENERATES,
    element_ten_god_class,
)
from apps.backend.data.climate_data import CLIMATE_DATA

_STEM_ELEMENT = LunarUtil.WU_XING_GAN

_WEAK = frozenset({"极弱", "弱"})
_STRONG = frozenset({"极旺", "旺"})

# ten-god categories that SUPPORT the day master (帮身/生身)
_SUPPORTIVE = frozenset({"印星", "比劫"})

# Preference order for the SINGLE primary 用神 when 扶抑 is decisive (弱/旺 正格) and the two
# systems (调候 ∩ 扶抑) do not already agree on one element. Classical default, not a hard
# rule — it only ranks WITHIN the 扶抑-喜 categories, never invents a verdict:
#   weak DM  → 印 (continuous 生身) before 比 (帮身).
#   strong DM → 泄 (食伤, 秀气流行) before 耗 (财) before 克 (官杀).
_WEAK_PRIMARY_PREF = ("印星", "比劫")
_STRONG_PRIMARY_PREF = ("食伤", "财星", "官杀")


def _select_yong_shen(
    ge_ju: dict,
    dm_element: str,
    dm_strength: str,
    climate_elements: list[str],
    per_element: dict[str, dict],
    favorable: list[str],
) -> str:
    """Pick the SINGLE primary 用神 element — the chart's most critical remedy.

    Purely additive over the set-based 喜用: this only names WHICH element of 喜用 leads.
    It never re-derives 忌/仇/闲 — those stay day-master-anchored sets (see module docstring).
    The returned element is always a member of `favorable`, except the degenerate case of a
    chart with no favourable element at all (中和 with no 调候 table), where it is "".

    Priority:
      • 化气格 → the 化神.
      • 从格 / 专旺格 → the 主导 force's element.
      • 正格 弱/旺 → the 扶抑 winner; when 调候 concurs on one of those elements it leads
        (both systems agree → strongest primary), else classical preference within the
        扶抑-喜 categories.
      • 正格 中和 → 调候喜[0] (the climate table is priority-ordered).
    """
    if ge_ju["格局"] == "化气格":
        return ge_ju.get("化神") or (favorable[0] if favorable else "")
    if ge_ju["格局"] != "正格":
        dominant = ge_ju.get("主导")
        for el in ELEMENTS:
            if element_ten_god_class(el, dm_element) == dominant:
                return el
        return favorable[0] if favorable else ""

    # 正格. When 强弱 is decisive, 扶抑 owns the primary; when 中和, 扶抑 is silent and 调候 leads.
    if dm_strength in _WEAK or dm_strength in _STRONG:
        fu_yi_xi = [el for el in favorable if per_element[el]["扶抑"] == "喜"]
        # both systems concur on an element → strongest possible primary
        for el in climate_elements:
            if el in fu_yi_xi:
                return el
        # else rank within the 扶抑-喜 categories by classical preference
        pref = _WEAK_PRIMARY_PREF if dm_strength in _WEAK else _STRONG_PRIMARY_PREF
        for cat in pref:
            for el in fu_yi_xi:
                if per_element[el]["十神"] == cat:
                    return el
        if fu_yi_xi:
            return fu_yi_xi[0]

    # 中和 (or no 扶抑 winner survived): 调候 leads, in its priority order.
    for el in climate_elements:
        if el in favorable:
            return el
    return favorable[0] if favorable else ""


def _fu_yi_stance(ten_god_class: str, dm_strength: str) -> str:
    """扶抑 stance for an element's ten-god category vs the day master strength.

    正格 ONLY. A 从格 day master has surrendered, so "support the weak / drain the strong"
    no longer applies — there 印比 are 忌 precisely BECAUSE they would support. That
    inversion is owned by ge_ju.PATTERN_MAPPING, not by this function.

    Returns 喜 / 忌 / 平.
    """
    supportive = ten_god_class in _SUPPORTIVE
    if dm_strength in _WEAK:
        return "喜" if supportive else "忌"
    if dm_strength in _STRONG:
        return "忌" if supportive else "喜"
    return "平"  # 中和 — no strong 扶抑 preference


def get_yong_shen(
    day_stem: str,
    dm_element: str,
    month_branch: str,
    day_master_data: dict,
    five_elements: dict,
    interactions: dict,
) -> dict:
    """
    Compute the combined 用神 verdict for a chart, branching on its 格局.

    正格 → 调候 ∪ 扶抑 (the ordinary path).
    从格 / 专旺格 / 化气格 → the STRUCTURE dictates 喜忌, and 调候 is not applied: a chart
    that has surrendered follows its dominant force, not the season's climate need. This
    is the whole reason 格局 exists — for a 从格, 扶抑 would call 印比 "喜" (support the
    weak DM) when they are in fact 忌 (they 破格). See ge_ju.PATTERN_MAPPING.

    Args:
        day_stem:        the EFFECTIVE day-master stem — indexes the 调候 table. Equals the
                         raw 日干 on a 正格 chart; under a 化气格 it is the 化神's stem (癸→丁),
                         because the climate is experienced by the day master the chart HAS.
        dm_element:      the day master's effective 五行 (differs from day_stem's element
                         only under a true 化气格, where ten_gods transformed it upstream).
        month_branch:    the birth month branch (月令), e.g. "亥".
        day_master_data: get_day_master_strength() output — supplies 强弱 and the three
                         foundations (得令/得地/得势) that 格局 detection reads.
        five_elements:   natal 五行 map WITH 力量 (classify_all(include_strength=True)) —
                         used to find which force a surrendered chart follows.
        interactions:    get_natal_interactions() output — supplies the 天干合 形态
                         (化气格 / 假化).

    Returns (Chinese-keyed):
        {
          "强弱": "极旺|旺|中和|弱|极弱",   # the day-master STRENGTH verdict
          "格局": "正格|从财格|…|化气格",    # the chart's STRUCTURE (see ge_ju)
          "格局详情": {...},                # full ge_ju block (真假/主导/依据/破格/提示)
          "五神": {                        # classical Five Gods — ADDITIVE split of the sets
            "用神": "火",                  #   singular primary remedy ("" iff 喜用 is empty)
            "喜神": ["木"],                #   the rest of 喜用 (supporters), NOT 生用神
            "忌神": [...], "仇神": [...], "闲神": [...],  # == 忌 / 仇 / 闲 below, unchanged
          },
          "调候适用": bool,                # False for 从/专旺/化气 — context, not rules
          "调候用神": [stems],
          "调候忌神": [stems],
          "调候喜五行": [elements],
          "调候忌五行": [elements],
          "喜用": [elements],
          "忌": [elements],
          "仇": [elements],                # 生忌神者 — idle but feeds a 忌 (see module docstring)
          "闲": [elements],                # the genuine idlers
          "大运喜": [branches],             # 金不换 方位表 — 正格-authored (see 运势)
          "大运忌": [branches],
          "五行": { "火": {"十神","扶抑","调候","综合","角色","备注"}, ... },
          "经典": {...} | None,
        }

    角色 (喜用神/忌神/仇神/闲神) is the ROLE label; 综合 (喜/忌/平) is the FAVOURABILITY verdict.
    They are separate axes and must not be conflated — 仇神 and 闲神 are both 综合 == "平", so
    a 仇神 running in a 大运 is still 平运. Only 综合 may move 运势.评级.

    Note: 强弱 was previously (mis)named 格局. They are different things — 强弱 is a
    5-point scale, 格局 is the structural class. 极弱 does NOT imply 从格.

    Note: 大运喜/大运忌 are practitioner-curated *branch* directions (not derivable from
    喜用: mechanically expanding 喜用 to branches floods ~7 of 12 as "good"). They are
    authored for 正格 charts, so get_cycle_yun_shi ignores them when 格局 != 正格.
    """
    dm_strength = day_master_data["日主"]["强弱"]
    ge_ju = detect_ge_ju(day_master_data, five_elements, interactions, dm_element)
    is_zheng_ge = ge_ju["格局"] == "正格"

    entry = CLIMATE_DATA.get(f"{day_stem}{month_branch}", {})
    climate_stems = list(entry.get("喜", []))
    climate_ji_stems = list(entry.get("忌", []))

    def _elements_of(stems: list[str]) -> list[str]:
        """Stems → their elements, deduped, preserving priority order."""
        out: list[str] = []
        for stem in stems:
            el = _STEM_ELEMENT.get(stem)
            if el and el not in out:
                out.append(el)
        return out

    climate_elements = _elements_of(climate_stems)
    climate_set = set(climate_elements)

    # 调候忌 — the stems the climate table says to avoid. ALL 120 entries carry these and
    # they were previously unread: get_yong_shen consumed only entry["喜"], so the忌 side of
    # 调候 was silently discarded. That left 中和 charts with NO 忌 at all (扶抑 is 平 across
    # the board when the DM is balanced), which is both wrong and useless downstream — the
    # 五行动态 喜忌 tag and the 运势 fallback both go dead. e.g. 戊亥 lists 忌辛: 金 drains a
    # winter 戊 and muddies the 甲丙 it needs.
    climate_ji_elements = _elements_of(climate_ji_stems)
    climate_ji_set = set(climate_ji_elements) - climate_set  # 喜 wins any direct collision

    # 化气格 is keyed by ELEMENT (serve the 化神); 从/专旺 by ten-god CATEGORY.
    hua_xi = set(ge_ju.get("喜用五行", []))
    hua_ji = set(ge_ju.get("忌五行", []))
    cat_xi = set(ge_ju.get("喜用十神", []))
    cat_ji = set(ge_ju.get("忌十神", []))

    per_element: dict[str, dict] = {}
    favorable: list[str] = []
    unfavorable: list[str] = []
    for el in ELEMENTS:
        tg = element_ten_god_class(el, dm_element)
        fu_yi = _fu_yi_stance(tg, dm_strength)
        is_climate = el in climate_set

        is_climate_ji = el in climate_ji_set

        if is_zheng_ge:
            if is_climate:
                combined = "喜"  # the chart NEEDS this element (climate); 调候 leads
                note = "调候扶抑两宜" if fu_yi == "喜" else (
                    "调候所喜，然扶抑不宜，运需权衡" if fu_yi == "忌" else "调候所喜"
                )
            elif is_climate_ji:
                combined = "忌"  # the chart is DAMAGED by this element; 调候 leads, as above
                note = "调候扶抑两忌" if fu_yi == "忌" else (
                    "调候所忌，然扶抑有益，运需权衡" if fu_yi == "喜" else "调候所忌"
                )
            else:
                combined = fu_yi
                note = ""
            climate_applied = is_climate or is_climate_ji
        else:
            # Structure rules. 调候 is deliberately NOT applied — reported above for
            # reference only, so the note flags when the two would have disagreed.
            if ge_ju["格局"] == "化气格":
                combined = "喜" if el in hua_xi else ("忌" if el in hua_ji else "平")
            else:
                combined = "喜" if tg in cat_xi else ("忌" if tg in cat_ji else "平")
            note = f"{ge_ju['名称']}：从其气势而论，不取调候扶抑"
            if combined == "忌" and fu_yi == "喜":
                # The headline case: 扶抑 would have said 喜 (support the weak DM) but the
                # structure says this element 破格. Surfacing it makes the inversion auditable.
                note = f"{ge_ju['名称']}：{tg}破格，扶抑虽宜而实忌"
            climate_applied = False

        per_element[el] = {
            "十神": tg,
            "扶抑": fu_yi,
            "调候": climate_applied,
            "综合": combined,
            "备注": note,
        }
        if combined == "喜":
            favorable.append(el)
        elif combined == "忌":
            unfavorable.append(el)

    # 仇神 / 闲神 — the split of the 平 leftovers (see module docstring for the full rule).
    # Runs as a SECOND pass because 喜/忌 must win the label: 仇神 is by definition neither
    # 用 nor 忌, and with 喜用/忌 being sets, an element that generates a 忌 element can very
    # well be the 用神 itself (土生金 on a weak 戊 that fears 金).
    ji_set = set(unfavorable)
    chou: list[str] = []
    idle: list[str] = []
    for el in ELEMENTS:
        entry_el = per_element[el]
        if entry_el["综合"] != "平":
            entry_el["角色"] = "喜用神" if entry_el["综合"] == "喜" else "忌神"
            continue
        fed = GENERATES[el]
        if fed in ji_set:
            entry_el["角色"] = "仇神"
            chou.append(el)
            # Append — the 非正格 path already wrote a 格局 note here and it must survive.
            clause = f"闲神而生{fed}（忌），为仇神"
            entry_el["备注"] = f"{entry_el['备注']}；{clause}" if entry_el["备注"] else clause
        else:
            entry_el["角色"] = "闲神"
            idle.append(el)

    # 五神 — the classical Five Gods, as an ADDITIVE presentation split of the sets above,
    # NOT a re-derivation. 用神 names which element of 喜用 is primary; 喜神 is the rest of the
    # SAME 喜用 set (its supporters), never "生用神" — deriving 喜/忌/仇 off the 用神 via 生克
    # would re-anchor favourability on the 用神 and demote real day-master 忌 (e.g. 食伤 leaking
    # a weak DM) to 仇/闲. 忌神/仇神/闲神 are the sets computed above, unchanged. 综合/角色 remain
    # the authoritative axes read by cycle_wu_xing/评级; 五神 is a human/LLM-facing convenience.
    yong = _select_yong_shen(
        ge_ju, dm_element, dm_strength, climate_elements, per_element, favorable
    )
    wu_shen = {
        "用神": yong,                                  # singular primary remedy ("" iff 喜用 empty)
        "喜神": [el for el in favorable if el != yong],  # the rest of 喜用 — supporters of 用神
        "忌神": unfavorable,
        "仇神": chou,
        "闲神": idle,
    }

    return {
        "强弱": dm_strength,
        "格局": ge_ju["格局"],
        "格局详情": ge_ju,
        "五神": wu_shen,
        # 调候适用 — is the climate layer IN FORCE for this chart?
        #
        # False for 从格/专旺格/化气格: those follow 顺其势 (go with the dominant force), and
        # 调候 is a 正格 concept (restrain the excess). The fields below are still populated —
        # indexed on the EFFECTIVE day stem, so the 经典 prose describes the day master the
        # chart actually has — but they are CONTEXT, not rules, and 综合 above ignores them.
        #
        # This flag is load-bearing for consumers. A 化火格 legitimately reports
        # 调候忌五行 = [火] (any chart in 巳月 fears more fire) while 格局 makes 火 the 化神 and
        # 喜用. Without the flag an LLM or UI reading only the 调候 block would enforce the
        # exact opposite of the chart's verdict.
        "调候适用": is_zheng_ge,
        "调候用神": climate_stems,
        "调候忌神": climate_ji_stems,
        "调候喜五行": climate_elements,
        "调候忌五行": climate_ji_elements,
        "喜用": favorable,
        "忌": unfavorable,
        "仇": chou,
        "闲": idle,
        "大运喜": list(entry.get("大运喜", [])),
        "大运忌": list(entry.get("大运忌", [])),
        "五行": per_element,
        "经典": entry.get("经典"),
    }


# ============================================================================
# python -m apps.backend.astronomer_logic.yong_shen
# ============================================================================
if __name__ == "__main__":
    import json
    from datetime import datetime

    from apps.backend.orchestrator.astronomer_data_orchestrator import calculate_natal_chart

    # Desmond: 戊 day master, 亥 month, 弱 → expected 正格.
    chart, _ = calculate_natal_chart(
        datetime(1985, 11, 25, 17, 7, 0), 1.3253, 103.808053, gender=1
    )
    print(json.dumps(chart["用神"], ensure_ascii=False, indent=2))
