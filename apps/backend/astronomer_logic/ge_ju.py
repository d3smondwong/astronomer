"""
格局 (Chart Structure) — 正格 / 从格 / 专旺格 / 化气格.

The 用神 layer needs to know WHICH KIND of chart it is looking at before it can say
what the chart wants. A 正格 chart with a weak day master wants 印比 (support); a 从格
chart with a weak day master wants the OPPOSITE — 印比 there revive a root the chart
has already surrendered, and 破格 (shatter the structure). Same 强弱 verdict, inverted
喜忌. Without this layer the engine silently mis-reads every 从格 chart.

Note 强弱 ≠ 格局. 强弱 is a 5-point scale (极弱…极旺); 格局 is the structural class.
"极弱" alone does NOT mean 从格: a chart with a trace root is 极弱 but still 正格 (it
wants support). The discriminator is the three foundations, not the score.

Detection reads the three foundations already computed by day_master_strength:
    得令 — seasonal command (月令)      graded 旺4 相3 休1.5 囚1 死0 (+1 得生)
    得地 — rooting (通根), already net  分数 0 | 1 | 2 | 4   ← 无根 after 冲/空亡 removal
    得势 — 印比 support in the stems     分数 0 | 1 | 2 | 4
All three at zero = the day master has nothing to stand on and must follow (从).
All three at maximum, unopposed = the day master IS the chart (专旺).

Precedence (first match wins):
    1. 化气格  — the DM's element literally changed (真化 only; see 假化 below).
    2. 从弱格  — 从财 / 从杀 / 从儿 / 从势.
    3. 专旺格  — the strong-side mirror (曲直/炎上/稼穑/从革/润下).
    4. 正格    — default.

真 vs 假:
  • 假从 keeps the 从格 用神 DIRECTION, flagged fragile. Treating it as "正格 with a weak
    DM" would flip 印比 from 忌 to 喜 — precisely backwards: in 假从 the 印比 运 revives
    the trace root and shatters the structure, so it is MORE dangerous, not less.
  • 假化 does NOT get 化气格 用神, and this is forced, not stylistic: ten_gods.py applies
    the DM element change for 形态 == "化气格" ONLY ("假化 / 合绊 / 遥合 — no change").
    If 用神 treated 假化 as transformed, the 十神 layer would label every god against the
    ORIGINAL day master while 用神 reasoned about the 化神 — the two layers would disagree
    about what the day master IS. So 假化 falls through to normal detection and carries an
    advisory instead.

Output — see detect_ge_ju().
"""

from lunar_python.util import LunarUtil

from apps.backend.astronomer_logic.wu_xing_relations import (
    CONTROLS as _CONTROLS,
    ELEMENTS,
    GENERATES as _GENERATES,
    element_ten_god_class,
)

_STEM_ELEMENT = LunarUtil.WU_XING_GAN

# 专旺格 names, per element — the classical 一行得气 structures.
_ZHUAN_WANG_NAMES = {
    "木": "曲直格",
    "火": "炎上格",
    "土": "稼穑格",
    "金": "从革格",
    "水": "润下格",
}

# Per-格局 喜忌 in ten-god CATEGORY space (polarity-free: 比劫/印星/食伤/财星/官杀).
# Confirmed against 子平 mainstream — do not edit without a methodology decision.
#   从财 — 财 is followed; 食伤 feeds it, 官杀 continues the flow. 印生身/比劫夺财 破格.
#   从杀 — 官杀 followed; 财 feeds it. 食伤 CLASHES the 杀 (克官杀) → 破格, hence 忌.
#   从儿 — 食伤 followed; 财 drains it onward; 比劫 GENERATES it → 喜 ("从儿不忌比劫").
#   从势 — no single dominant force; 财 is the mediator/bridge (食伤生财, 财生杀), so the
#          whole 财-食伤-官杀 flow is 喜 and only 印比 (which restore the DM) are 忌.
#   专旺 — the DM's own element IS the chart; 食伤 洩秀 goes WITH the grain (顺势), while
#          官杀 fights the 旺神 (逆其性) and 财 provokes it.
PATTERN_MAPPING: dict[str, dict] = {
    "从财格": {"喜用": ["财星", "食伤", "官杀"], "忌": ["印星", "比劫"], "主导": "财星"},
    "从杀格": {"喜用": ["官杀", "财星"], "忌": ["印星", "比劫", "食伤"], "主导": "官杀"},
    "从儿格": {"喜用": ["食伤", "财星", "比劫"], "忌": ["印星", "官杀"], "主导": "食伤"},
    "从势格": {"喜用": ["财星", "食伤", "官杀"], "忌": ["印星", "比劫"], "主导": "财星"},
    "专旺格": {"喜用": ["比劫", "印星", "食伤"], "忌": ["官杀", "财星"], "主导": "比劫"},
}

# The 从弱 subtype implied by whichever force dominates.
_CONG_BY_DOMINANT = {"财星": "从财格", "官杀": "从杀格", "食伤": "从儿格"}

# A 从弱 subtype is only named when the leading force clears the runner-up by this factor;
# otherwise no single force owns the chart and it is 从势 (follow the general trend).
_DOMINANCE_MARGIN = 1.5

# 全局无生扶 — the condition that separates a true 从格 from a merely weak 正格.
#
# The three foundations are NOT sufficient on their own. Track what each actually covers:
#   得地 — the DM's own 比劫 rooting, and it is ALREADY clash-aware (a root killed by 六冲
#          or 空亡 reports 无根). So "得地 == 无根" means there is no usable 比劫 root.
#   得势 — 印比 appearing in the STEMS.
#   ⇒ the one channel neither sees is 印星 buried in the BRANCHES. A chart can be 无根,
#     失令, 无势 and still have strong 印 hidden in its branches — which can revive the day
#     master. That chart is weak-but-rescuable (正格), and inverting its 喜忌 would be a
#     serious misread. Measured on real charts, the foundations alone fire on ~9%, and most
#     of those still have live 印 to lean on.
#
# So the gate is 印星 力量 ALONE. Adding 比劫 力量 would double-count the very roots 得地 has
# already ruled dead — e.g. 甲寅 丁卯 辛酉 丙申, where 卯酉冲 + 寅申冲 destroy both of 辛's
# metal roots: 得地 correctly says 无根, yet 金 still carries raw 力量. That is a genuine
# 弃命从财 and must not be rejected for roots it cannot use.
#
# This also gives 真/假 a principled meaning instead of an arbitrary cutoff:
#   真从 — nothing anywhere can revive the day master (印星 ≈ 0).       → ~2% of charts
#   假从 — a TRACE of 印 survives. That residue is exactly why 假从 is fragile: a 印比 运
#          re-animates it and 破格. Above the trace the DM has a real prop → 正格.  → ~3% total
_NO_SUPPORT_POWER = 0.0
_TRACE_SUPPORT_POWER = 1.0

# 旺相休囚死 — the seasonal states in which the month does NOT back the day master.
# 格局 keys 失令 on this, never on 得令.分数: the score is a calibration knob, the state is
# a fact about the season. (Before the graded scale, 休/囚/死 all scored 0, so testing the
# score happened to work. Grading them non-zero would have silently killed 从格 detection.)
_OUT_OF_SEASON = frozenset({"休", "囚", "死"})


def _support_tier(support: float) -> str:
    """印星生扶 as a qualitative tier — 无 / 余气 / 有力.

    Derived from 力量, i.e. the SAME quantity the 从格 gate tests, and banded on the gate's
    own thresholds. So the label can never contradict the verdict it explains:
        无   ≤ 0.0  → nothing can revive the DM        → 真从
        余气 ≤ 1.0  → a trace survives (fragile)        → 假从
        有力 > 1.0  → a real prop; the DM can be saved  → 正格

    Deliberately NOT the element's 状态 (旺相休囚死): the classifier caps 状态 at 相 for
    non-ruling elements while 力量 is the raw pre-cap value, so the two diverge on ~20% of
    charts. A 印星 that reads 死 on 状态 can still carry 力量 well above the gate — using
    状态 here would print "印星死，然尚可生扶", the explanation fighting the decision.
    """
    if support <= _NO_SUPPORT_POWER:
        return "无"
    if support <= _TRACE_SUPPORT_POWER:
        return "余气"
    return "有力"


def _category_power(five_elements: dict, dm_element: str) -> dict[str, float]:
    """Aggregate the five elements' 力量 into the five ten-god categories."""
    power: dict[str, float] = {
        "比劫": 0.0, "印星": 0.0, "食伤": 0.0, "财星": 0.0, "官杀": 0.0
    }
    for el in ELEMENTS:
        cat = element_ten_god_class(el, dm_element)
        power[cat] += float(five_elements.get(el, {}).get("力量", 0.0))
    return power


def _hua_qi_form(interactions: dict) -> tuple[str, str, str] | None:
    """The 天干合 form involving the DAY pillar: ("化气格"|"假化", 合化元素, 日主原始天干).

    The RAW day stem is returned because detect_ge_ju only ever sees the TRANSFORMED
    element — and the original one is needed: 日主复根 (the day master regaining a root in
    the element it used to be) is one of the two ways a 化气格 shatters.

    Returns None when the day master is not party to a transforming 天干合.
    """
    for item in interactions.get("作用", {}).get("柱位动态", []):
        if item.get("类型") != "天干合":
            continue
        combo = item.get("组合明细", {})
        raw_dm_stem = combo.get("日柱", "")
        if not raw_dm_stem:
            continue
        form = item.get("形态")
        if form in ("化气格", "假化"):
            element = item.get("合化条件", {}).get("合化元素", "")
            if element:
                return form, element, raw_dm_stem
    return None


def _dominant_cong_subtype(power: dict[str, float]) -> tuple[str, str]:
    """Which 从弱 structure the chart follows → (格局 name, 主导 category).

    The DM has surrendered, so only the three DRAINING forces can be followed; 印比 are
    by definition absent. If no one force clears the field, the chart follows the
    combined trend (从势格) rather than being forced into a subtype it doesn't have.
    """
    candidates = sorted(
        (("财星", power["财星"]), ("官杀", power["官杀"]), ("食伤", power["食伤"])),
        key=lambda kv: kv[1],
        reverse=True,
    )
    (top_cat, top_val), (_, second_val) = candidates[0], candidates[1]
    if top_val <= 0:
        return "从势格", "财星"
    if second_val <= 0 or top_val >= second_val * _DOMINANCE_MARGIN:
        return _CONG_BY_DOMINANT[top_cat], top_cat
    return "从势格", "财星"  # mediator — 财 bridges 食伤 → 官杀


def detect_ge_ju(
    day_master_data: dict,
    five_elements: dict,
    interactions: dict,
    dm_element: str,
) -> dict:
    """
    Determine the chart's structural class.

    Args:
        day_master_data: get_day_master_strength() output — read for its three
                         foundations (得令/得地/得势) and the 强弱 verdict.
        five_elements:   the natal 五行 map with 力量 (post-interaction), used to find
                         which force dominates a surrendered chart.
        interactions:    get_natal_interactions() output — supplies the 天干合 形态
                         (化气格 / 假化); this module never re-derives it.
        dm_element:      the EFFECTIVE day-master element (already the 化神 under a true
                         化气格, since ten_gods transformed it upstream).

    Returns (Chinese-keyed):
        {
          "格局":   "正格" | "从财格" | "从杀格" | "从儿格" | "从势格" | "专旺格" | "化气格",
          "名称":   display name (专旺格 resolves to 曲直/炎上/稼穑/从革/润下格),
          "真假":   "真从" | "假从" | "真化" | None,   # None for 正格
          "主导":   ten-god category the chart follows (None for 正格),
          "化神":   element (化气格 only),
          "原五行": element (化气格 only) — what the DM used to be; drives the 复根 破格 check.
          "喜用十神": [ten-god categories],  # empty for 正格 — 扶抑/调候 owns that path.
          "忌十神":   [ten-god categories],  # NAMED for their type: 用神.喜用 holds ELEMENTS.
          "生扶":   {"印星": "无|余气|有力", "力量": float},  # the quantity the 从格 gate turns
                    # on. The tier is what 依据 narrates; the raw 力量 is kept for audit only.
          "依据":   [reasons],
          "破格":   [{条件, 五行, 位置, 说明}],   # non-正格 only. 位置 matters:
                    # 化气格's 日主复根 is a 地支 condition (a floating 天干 of 原五行 may
                    # even HELP when it 生s the 化神; only a ROOT reverts the day master).
          "提示":   advisory | None,                # e.g. the 假化 note
        }
    """
    dm = day_master_data["日主"]
    di = float(dm["得地"]["分数"])
    shi = float(dm["得势"]["分数"])
    strength = dm["强弱"]
    root = dm["得地"]["通根"]

    # 失令 / 得令 are read from the STATE, never from 得令.分数.
    #
    # The score is a calibration knob and must not be load-bearing for a structural verdict.
    # Under the graded seasonal scale 休=1.5 and 囚=1.0 are non-zero, so the old test
    # (`分数 == 0`) would have quietly stopped firing for every 休/囚 chart — 从格 detection
    # would have died in silence, with no test failing, because the gate keyed on a number
    # whose meaning had changed underneath it. 失令 is a fact about the season, not a number.
    ling_state = dm["得令"]["状态"].split(" ")[0]   # "囚 (弱)" → "囚"
    shi_ling = ling_state in _OUT_OF_SEASON        # 休/囚/死 — the season does not back the DM
    de_ling = ling_state == "旺"                   # the DM itself commands the month

    advisory: str | None = None

    # 印星生扶 — the quantity the 从格 gate turns on, plus its qualitative band. Computed up
    # front so every branch can report it: it is the one engine measure that decides 格局 and
    # appears nowhere else in the response, so it must stay auditable.
    power = _category_power(five_elements, dm_element)
    support = power["印星"]
    tier = _support_tier(support)   # 无 / 余气 / 有力 — banded on the gate's own thresholds
    sheng_fu = {"印星": tier, "力量": round(support, 1)}

    # ── 1. 化气格 — the DM's element changed. Trust the interaction engine's 形态. ──
    hua = _hua_qi_form(interactions)
    if hua:
        form, hua_element, raw_dm_stem = hua
        if form == "化气格":
            sheng = next(e for e in ELEMENTS if _GENERATES[e] == hua_element)
            ke = next(e for e in ELEMENTS if _CONTROLS[e] == hua_element)
            # 原五行 — what the day master USED to be. Load-bearing: 日主复根 is one of the
            # two ways a 化气格 shatters, and it turns on the ORIGINAL element, not the 化神.
            orig = _STEM_ELEMENT.get(raw_dm_stem, "")

            xi = [hua_element, sheng]
            ji = [ke]
            caveat: str | None = None

            # Where does 原五行 sit relative to the 化神? Four possibilities, and the old code
            # handled only one of them:
            #   • orig IS the 化神      — no tension (己化土, 庚化金).
            #   • orig 克 the 化神      — already in 忌 (甲化土, 癸化火). ✓
            #   • orig 生 the 化神      — it genuinely FEEDS the structure (辛化水, 壬化木), so
            #                             it stays 喜. But its ROOTS revive the day master, so
            #                             the 破格 below is scoped to 地支 only. Same element,
            #                             two positions, opposite effects — which is why an
            #                             element-level 忌五行 cannot hold both.
            #   • orig neither 生 nor 克 — 乙化金, 丙化水, 丁化木, 戊化火. Its ONLY function in
            #                             the chart is to revive the day master and break the
            #                             化. It was rated 平. That was the bug.
            if orig and orig != hua_element:
                if orig == sheng:
                    caveat = (
                        f"{orig}生化神，天干透之则助化；然{orig}为原日主五行，"
                        f"通根地支则日元复根，反化破格。"
                    )
                elif orig != ke and orig not in ji:
                    ji.append(orig)

            return {
                "格局": "化气格",
                "名称": f"化{hua_element}格",
                "真假": "真化",
                "主导": None,
                "化神": hua_element,
                "原五行": orig,   # consumed by the cycle layer's 复根 check
                # 化气格 is element-keyed, not category-keyed: the chart serves the 化神.
                "喜用五行": xi,
                "忌五行": ji,
                "喜用十神": [],
                "忌十神": [],
                "生扶": sheng_fu,
                "依据": [f"日主与他干合化为{hua_element}，日元五行已变，从化神而论"],
                # 破格 carries POSITION. 日主复根 is a 地支 condition specifically: a floating
                # 天干 of 原五行 may even help (when it 生s the 化神), while a BRANCH that roots
                # the day master reverts it. And since 化气格 requires 日主无根 at birth, 复根
                # can only ever arrive via a 运 — so this is the cycle layer's business.
                "破格": [
                    {
                        "条件": "克化神",
                        "五行": ke,
                        "位置": "天干或地支",
                        "说明": f"{ke}克{hua_element}，化神受伤",
                    },
                    {
                        "条件": "日主复根",
                        "五行": orig,
                        "位置": "地支",
                        "说明": f"运支藏{orig}，日元复根，化神反化破格",
                    },
                ],
                "提示": caveat,
            }
        # 假化 — ten_gods did NOT transform the DM (形态 != "化气格"), so 用神 must not
        # either, or 十神 and 用神 would disagree about what the day master is. Fall
        # through to normal detection and carry the instability as an advisory.
        advisory = (
            f"假化({hua_element})：合而不化，日元五行未变，仍按本格论。"
            f"结构不稳，运助{hua_element}可假化转真，原五行复起则破。"
        )

    # ── 2. 从弱格 — nothing to stand on, so the DM follows the dominant force. ──
    # 失令 is read from the STATE (休/囚/死), not from 得令.分数 — see _OUT_OF_SEASON.
    # `support` (印星 力量) was computed above.
    foundations_zero = (di == 0.0 and shi_ling and shi == 0.0)

    if foundations_zero and support <= _TRACE_SUPPORT_POWER:
        name, dominant = _dominant_cong_subtype(power)
        spec = PATTERN_MAPPING[name]
        zhen = support <= _NO_SUPPORT_POWER
        zhen_jia = "真从" if zhen else "假从"
        reasons = [
            f"日主{root}、失令，全无印星生扶，日元无所依托" if zhen
            else f"日主{root}、失令，然印星尚存{tier}，从而不真",
            f"{dominant}当权，日元弃命相从",
        ]
        # 破格 is uniformly structured across all 格局 — see the 化气格 branch. For a 从格 the
        # shattering forces are ten-god categories and act from either half of the chart, so
        # 位置 is 天干或地支; only 化气格's 日主复根 is 地支-specific.
        yin_elem = next((e for e in ELEMENTS if _GENERATES[e] == dm_element), "")
        po_ge = [
            {"条件": "印星生身", "五行": yin_elem, "位置": "天干或地支", "说明": "印生日元，从格破"},
            {"条件": "比劫帮身", "五行": dm_element, "位置": "天干或地支", "说明": "比劫帮身，从格破"},
        ]
        if name == "从杀格":
            ke_elem = next((e for e in ELEMENTS if _GENERATES[dm_element] == e), "")
            po_ge.append(
                {"条件": "食伤克官杀", "五行": ke_elem, "位置": "天干或地支", "说明": "食伤克杀，所从之神受伤"}
            )
        if not zhen:
            po_ge.append(
                {"条件": "运扶残余印比", "五行": yin_elem, "位置": "天干或地支",
                 "说明": "假从：残余印比被运激起，从格崩溃"}
            )
            advisory = (
                (advisory + " ") if advisory else ""
            ) + (
                "假从：印比尚存一线余气，印比之运最凶——非但不助，反激起残根而破格。"
            )
        return {
            "格局": name,
            "名称": name,
            "真假": zhen_jia,
            "主导": dominant,
            "化神": None,
            "喜用十神": list(spec["喜用"]),
            "忌十神": list(spec["忌"]),
            "生扶": sheng_fu,
            "依据": reasons,
            "破格": po_ge,
            "提示": advisory,
        }

    # ── 3. 专旺格 — the DM's element IS the chart; 官杀 cannot restrain it. ──
    # 得令 here means the DM's element RULES the month (状态 == 旺), not merely that it scored
    # highly — again a fact about the season, not a threshold on a tunable score.
    unopposed = power["官杀"] <= 0.0
    if strength == "极旺" and de_ling and di >= 4.0 and unopposed:
        spec = PATTERN_MAPPING["专旺格"]
        return {
            "格局": "专旺格",
            "名称": _ZHUAN_WANG_NAMES.get(dm_element, "专旺格"),
            "真假": "真从",
            "主导": "比劫",
            "化神": None,
            "喜用十神": list(spec["喜用"]),
            "忌十神": list(spec["忌"]),
            "生扶": sheng_fu,
            "依据": [
                f"日主得令得地({root})，{dm_element}气专旺，全局无官杀克制",
                "一行得气，顺其势而不可逆",
            ],
            "破格": [
                {"条件": "官杀克旺神", "五行": next((e for e in ELEMENTS if _CONTROLS[e] == dm_element), ""),
                 "位置": "天干或地支", "说明": "官杀克旺神，逆其性则激之"},
                {"条件": "财星激旺神", "五行": _CONTROLS.get(dm_element, ""),
                 "位置": "天干或地支", "说明": "财星逆旺神，群比争财"},
            ],
            "提示": advisory,
        }

    # ── 4. 正格 — the ordinary case. 扶抑 + 调候 own the 用神 (see yong_shen). ──
    # 正格 — record WHY the chart is not 从格, which is the decision this field exists to
    # explain. Name the surviving prop: a usable root, or 印星 able to revive a rootless DM.
    #
    # 得令.状态 carries its own strength gloss ("囚 (弱)"), so use only the bare state name —
    # splicing the gloss in produces lines like "日主深根、旺 (最强)" sitting under
    # "强弱": "弱", which reads as a contradiction when the two legitimately disagree.
    # The 依据 speaks the domain's own qualitative language — 深根/囚/有力 — never raw scores.
    # Every engine measure already has a label (通根, 得令状态, 得势层级), and 印星生扶 now has
    # one too via _support_tier. The raw 力量 stays out of the prose and lives in 生扶.力量
    # below, where a number belongs: machine-readable, not narrated.
    shi_tier = dm["得势"]["得势层级"]
    if di > 0:
        why = f"日主{root}、月令{ling_state}，日元有根可依"
    elif support > _TRACE_SUPPORT_POWER:
        why = f"日主{root}、月令{ling_state}，然印星{tier}，尚可回生"
    else:
        why = f"日主{root}、月令{ling_state}，得势{shi_tier}，尚有依托"
    return {
        "格局": "正格",
        "名称": "正格",
        "真假": None,
        "主导": None,
        "化神": None,
        "喜用十神": [],
        "忌十神": [],
        "生扶": sheng_fu,
        "依据": [why, "不入从格，按扶抑调候论"],
        "破格": [],
        "提示": advisory,
    }
