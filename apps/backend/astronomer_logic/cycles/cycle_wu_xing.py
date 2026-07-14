"""
岁运五行动态 Cycle Pillar Five-Elements Dynamics — combined reclassification.

Unlike the natal five-elements layer (which classifies the 4 birth pillars), a
大运/流年 pillar is a *transiting* input: it adds qi to the chart and can form
三合/三会/合化 that shift the whole picture. So this module re-runs
`QualitativeFiveElementsClassifier` over the birth pillars PLUS the transiting
pillar(s) (season stays anchored to the natal 月令 — a 大运 shifts ambient qi, it
does NOT re-anchor 旺衰) to produce a real 旺相休囚死 verdict for the period:
  • 大运 → natal-4 + 大运 (5 pillars).
  • 流年 → natal-4 + 大运 + 流年 (6 pillars): a year's 旺衰 is 岁运并临, read inside
    its decade, so the enclosing 大运 is folded in.

Each element reports:
  状态  — combined-period state (月令-capped classical 旺相休囚死).
  本命  — natal (birth-chart) state, a stable anchor.
  运基  — (流年 only) the enclosing 大运's state, so the reader sees natal → decade → year.
  变化  — 大升/升/持平/降/大降, graded on the pre-cap 力量 (raw strength), NOT the capped
          状态. The cap pins a 失令 element at 相, so a genuine 行运 gain (金 in a 酉 metal
          cycle) is invisible on 状态 but shows as 变化=升. Baseline is 本命 for 大运, the
          decade level for 流年 (so 变化 isolates the year's own push). |Δ力量|≥2 → 大.
  十神  — the element's ten-god category for the day master (财星/官杀/印星/食伤/比劫):
          the life-domain each element governs, fixed per chart.

Output (Chinese-keyed):
    {
      "五行": { "木": {"状态","本命","变化","十神"[,"运基"]}, "火": {...}, "土", "金", "水" },
      "对日主": { "天干": {关系,方向}, "地支本气": {关系,方向}, "结合日主强弱": "…" },
      "引动": [ {类型, 元素, 状态, 说明}, … ],
    }
"""

from lunar_python.util import LunarUtil

from apps.backend.astronomer_logic.cycles.cycle_pillars import (
    _HIDE_TIERS,
    _NATAL_PILLAR_KEYS,
    NatalContext,
)
from apps.backend.astronomer_logic.day_master_strength import (
    BRANCH_HIDDEN_STEM_ROOTING,
    get_stem_element,
)
from apps.backend.astronomer_logic.natal_five_elements import (
    ELEMENTS,
    QualitativeFiveElementsClassifier,
)
from apps.backend.astronomer_logic.wu_xing_relations import (
    CONTROLS as _CONTROLS,
    element_ten_god_class,
)

_STRONG_VERDICTS = frozenset({"极旺", "旺"})
_WEAK_VERDICTS = frozenset({"极弱", "弱"})


# 地支本气五行 — each branch's dominant element. Only used by the 运势 fallback, where
# a chart has no curated 方位表 and the verdict must come off the branch's own qi.
_BRANCH_MAIN_ELEMENT = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

_RATING_BY_YONG_SHEN = {"喜": "喜运", "忌": "忌运"}

_STEM_ELEMENT = LunarUtil.WU_XING_GAN

# 运看地支为重，天干为辅 — the stem moves the branch's verdict by exactly ONE step, never more.
_UPGRADE = {"忌运": "平运", "平运": "喜运", "喜运": "喜运"}
_DOWNGRADE = {"喜运": "平运", "平运": "忌运", "忌运": "忌运"}


def _apply_stem(
    rating: str, reason: str, cycle_stem: str, cycle_branch: str, yong_shen: dict
) -> tuple[str, str]:
    """Adjust a BRANCH-derived 运势 by the cycle STEM — via 盖头 / 截脚.

    A 大运 is a 干支 pair and BOTH act (运以支为重，天干为辅; many read it 上五年看天干，
    下五年看地支). The 金不换 方位表 is branch-indexed because 方位 (寅卯辰 = 东方木) IS a branch
    concept — it has nothing to SAY about stems. Treating that silence as "stems are
    irrelevant" left half the 运柱 unread.

    But a flat "忌 stem → downgrade" is far too crude, because a stem's POWER depends on the
    branch it sits on:

        盖头 — the stem 克s its own branch. The stem is potent AND smothers the branch.
        截脚 — the branch 克s the stem. The stem is cut off at the root: it CANNOT act.

    The following example is the proof. His three 南方火 decades all carry a 忌 stem, and a flat rule
    downgraded all three — wrecking the curated 方位 judgment:

        癸未  未土 克 癸水  → 截脚. The 忌 水 is defanged; 未's warmth survives.   → stays 喜运
        辛巳  巳火 克 辛金  → 截脚. Same.                                          → stays 喜运
        壬午  壬水 克 午火  → 盖头. The 忌 水 SMOTHERS the 喜 火.                   → genuinely damaged

    Only 壬午 is truly compromised. 盖头/截脚 is what tells them apart.

    So: a stem that is 截脚'd cannot move the verdict at all — friendly or hostile, it is
    powerless. Otherwise it moves the branch's verdict one step, and no further: the branch
    always dominates.

    NOT applied to a structural 破格 (化气 复根) — a shattered structure is not repaired by a
    friendly stem, so that verdict stays absolute.
    """
    stem_el = _STEM_ELEMENT.get(cycle_stem, "") if cycle_stem else ""
    branch_el = _BRANCH_MAIN_ELEMENT.get(cycle_branch, "")
    if not stem_el:
        return rating, reason

    verdict = yong_shen.get("五行", {}).get(stem_el, {}).get("综合", "平")
    if verdict == "平":
        return rating, reason

    # 截脚 — the branch controls the stem, so the stem has no legs to stand on.
    if branch_el and _CONTROLS.get(branch_el) == stem_el:
        return rating, reason + f"；运干{cycle_stem}({stem_el}·{verdict})为支所克，截脚无力，不改其断"

    gai_tou = bool(branch_el and _CONTROLS.get(stem_el) == branch_el)
    if verdict == "忌":
        note = "盖头克支" if gai_tou else "透干为忌"
        return _DOWNGRADE[rating], reason + f"；运干{cycle_stem}({stem_el}){note}，降一等"
    return _UPGRADE[rating], reason + f"；运干{cycle_stem}({stem_el})为用神所喜，升一等"

# 藏干 tiers, in table order — 本气 / 中气 / 余气.
_ROOT_TIERS = ("本气", "中气", "余气")


def _substantive_root(branch: str, element: str) -> tuple[str, str] | None:
    """Does `branch` give `element` a root strong enough to matter → (stem, tier) or None.

    本气/中气 count. 余气 does NOT — and that exclusion is load-bearing, not a shortcut.

    A 余气 root is a 墓库 root: 墓库根，如物之入库，虽存而无力 — it exists but cannot act. This
    is the same principle that discounts 冻土 in day_master_strength.earth_root_factor: root
    QUALITY, not mere presence.

    Counting 余气 here produced absurd verdicts. A 戊化火 chart rates 巳 (丙0.6 庚0.3 戊0.1) as
    破格 — even though 巳's 本气 IS 丙火, the 化神 itself, so the branch overwhelmingly FEEDS
    the structure. It was being shattered by a 0.1 residue. Likewise 甲化土 vs 未 (本气 己土 =
    the 化神, broken by a 0.1 乙). Eight verdicts were wrong this way, several of them the 化神's
    OWN branches.

    Nothing real is lost: for 辛化水 the genuine threats all survive — 酉 (辛 本气), 申 (庚 本气),
    巳 (庚 中气), 戌 (辛 中气). Only 丑 drops out, and 丑's 本气 土 克s the 化神 anyway, so it is
    still 忌运 — now for the correct reason.
    """
    for idx, (stem, _weight) in enumerate(BRANCH_HIDDEN_STEM_ROOTING.get(branch, [])):
        if idx >= 2:  # 余气 — stored qi, powerless to revive the day master
            break
        if get_stem_element(stem) == element:
            return stem, _ROOT_TIERS[idx]
    return None


def get_cycle_yun_shi(
    cycle_branch: str, yong_shen: dict, cycle_stem: str = ""
) -> dict:
    """运势 — the holistic 喜运/平运/忌运 verdict for ONE 大运/流年 pillar.

    This is the headline the per-element 五行动态 breakdown cannot give: five elements
    each move their own way, so "is this decade good?" needs a single call. It is a
    complement to 五行动态, not a replacement — the two reinforce each other.

    Primary source — the curated 大运喜/大运忌 branch table (金不换). These are hand-
    picked *directions* (e.g. 戊亥 → 大运喜 巳午未, the 南方火运 that warms a cold winter
    戊). They are deliberately NOT derived from 喜用: mechanically expanding 喜用 五行 to
    branches would flag ~7 of 12 branches as favorable, which says nothing.
        运支 ∈ 大运喜 → 喜运 · ∈ 大运忌 → 忌运 · 表中皆无 → 平运.

    Fallback — when a chart has NO curated table at all (both lists empty; 15 of the 240
    lists are uncurated), degrade gracefully to the branch's 本气 element read against the
    chart's 用神 verdict, and say so in 来源 so the caller can tell the two apart.

    非正格 charts BYPASS the table entirely. The 金不换 方位表 is authored for 正格 charts —
    it assumes the day master stands and must be balanced. For a 从格/专旺格/化气格 the 喜忌
    are inverted by the structure, so the table's directions are not merely unhelpful but
    backwards. (This is exactly how 癸午's 从格-conditional 忌申 came to rate the chart's own
    用神 as 忌运.) Those charts read off the structure-derived 用神 instead.

    cycle_stem — consulted for 非正格 charts ONLY, and only to DOWNGRADE.

    A 运柱 has two characters, and 破格 carries 位置: "天干或地支". The 地支 half (日主复根)
    is handled below; this is the 天干 half, which was declared and never checked. A 化火格
    meeting a 壬午 decade has its 化神 attacked by the visible 壬水 even though 午 IS the 化神 —
    branch-only, that rated 喜运 while a stem openly 克s the structure.

    The branch keeps the direction (运看地支为重) and the stem can only pull it down a step:
    喜运 → 平运 → 忌运. It never pulls UP — which is exactly what the 辛化水 caveat says
    ("金生化神，天干透之则助化"): a friendly stem helps, but it is the branch that decides
    whether the chart stands. 正格 charts stay branch-only by design — the 金不换 表 is a
    方位 (direction) table, and directions are branches; reading stems into it would invent
    data the table does not have.
    """
    ge_ju = yong_shen.get("格局", "正格")
    if ge_ju != "正格":
        detail = yong_shen.get("格局详情", {})
        name = detail.get("名称", ge_ju)

        # 化气格 · 日主复根 — a POSITIONAL override that the element verdict cannot express.
        #
        # A 化气格 requires 日主无根 at birth, so the day master can only regain a root via a
        # 运. If the cycle BRANCH hides the original day-master element, the day master
        # re-roots, reverts to what it was, and the 化 shatters (反化).
        #
        # This must override the element reading, because for 辛化水 / 壬化木 the original
        # element is ALSO the 生化神者 — 金生水, 水生木 — and therefore rates 喜. A floating
        # 天干 庚/辛 genuinely does feed the 化神; a 申/酉 BRANCH gives 辛 a root and breaks
        # the whole structure. Same element, opposite effect, decided purely by position.
        # Without this check those decades would be rated 喜运 while actually 破格.
        orig = detail.get("原五行")
        if detail.get("格局") == "化气格" and orig:
            rooting = _substantive_root(cycle_branch, orig)
            if rooting:
                stem, tier = rooting
                return {
                    "评级": "忌运",
                    "依据": (
                        f"{name}：运支{cycle_branch}藏{stem}({orig}·{tier})，"
                        f"日元复根，化神反化破格"
                    ),
                    "来源": "化气破格",
                }

        element = _BRANCH_MAIN_ELEMENT.get(cycle_branch, "")
        combined = yong_shen.get("五行", {}).get(element, {}).get("综合", "平")
        rating = _RATING_BY_YONG_SHEN.get(combined, "平运")
        reason = f"{name}不取方位表，依运支{cycle_branch}本气{element}为格局所{combined}"
        rating, reason = _apply_stem(rating, reason, cycle_stem, cycle_branch, yong_shen)
        return {"评级": rating, "依据": reason, "来源": "从格用神"}

    xi = yong_shen.get("大运喜", [])
    ji = yong_shen.get("大运忌", [])

    if xi or ji:  # chart is curated — the table owns the BRANCH direction
        if cycle_branch in xi:
            rating, reason = "喜运", f"运支{cycle_branch}属大运喜用方位"
        elif cycle_branch in ji:
            rating, reason = "忌运", f"运支{cycle_branch}属大运忌避方位"
        else:
            rating, reason = "平运", f"运支{cycle_branch}不在大运喜忌方位之内"
        # …and the STEM is judged against the 用神. The 方位表 is silent on stems because 方位
        # IS a branch concept — but a 大运 is a 干支 pair and both act (运以支为重，天干为辅).
        # Treating the table's silence as "stems are irrelevant" left half the pillar unread.
        rating, reason = _apply_stem(rating, reason, cycle_stem, cycle_branch, yong_shen)
        return {"评级": rating, "依据": reason, "来源": "金不换"}

    # Uncurated chart — read the branch's own qi against the chart-fixed 用神.
    element = _BRANCH_MAIN_ELEMENT.get(cycle_branch, "")
    combined = yong_shen.get("五行", {}).get(element, {}).get("综合", "平")
    rating = _RATING_BY_YONG_SHEN.get(combined, "平运")
    reason = f"方位表未载，依运支{cycle_branch}本气{element}为用神所{combined}"
    rating, reason = _apply_stem(rating, reason, cycle_stem, cycle_branch, yong_shen)
    return {"评级": rating, "依据": reason, "来源": "用神五行"}


# 十神 → (关系, 十神类, 方向). The DM-relative 生克 axis is already fully encoded by the
# ten god that build_cycle_pillar computes — and more precisely (keeps 正/偏 polarity) —
# so we derive the axis from it rather than recomputing element 生克.
_TEN_GOD_AXIS: dict[str, tuple[str, str, str]] = {
    "比肩": ("同我", "比劫", "助身"),
    "劫财": ("同我", "比劫", "助身"),
    "正印": ("生我", "印星", "助身"),
    "偏印": ("生我", "印星", "助身"),
    "食神": ("我生", "食伤", "泄身"),
    "伤官": ("我生", "食伤", "泄身"),
    "正财": ("我克", "财星", "耗身"),
    "偏财": ("我克", "财星", "耗身"),
    "正官": ("克我", "官杀", "抑身"),
    "七杀": ("克我", "官杀", "抑身"),
    "偏官": ("克我", "官杀", "抑身"),
}


def _god_axis(ten_god: str) -> tuple[str, str, str]:
    """(关系, 十神类, 方向) for a ten god, e.g. 七杀 → ("克我", "官杀", "抑身")."""
    return _TEN_GOD_AXIS.get(ten_god, ("", "", ""))


def _strength_verdict(direction: str, ten_god_class: str, dm_strength: str) -> str:
    """One-line cross-reference of the cycle branch qi's push vs DM strength."""
    if dm_strength in _STRONG_VERDICTS:
        if direction == "助身":
            return f"日主本旺，再得{ten_god_class}生扶，旺上加旺，防过刚易折"
        return f"日主偏旺，{ten_god_class}泄耗制衡，流通有情"
    if dm_strength in _WEAK_VERDICTS:
        if direction == "助身":
            return f"日主偏弱，得{ten_god_class}帮扶，运势得力"
        if direction == "抑身":
            return f"日主偏弱，{ten_god_class}加压，负重之运"
        return f"日主偏弱，{ten_god_class}泄耗，谨防力不从心"
    return f"日主中和，{ten_god_class}随运流转，平稳应对"


def _delta(combined_strength: int, baseline_strength: int) -> str:
    """大升 / 升 / 持平 / 降 / 大降 — graded on the pre-cap 力量, NOT the capped 状态.

    The seasonal cap pins the displayed 状态 (a 失令 element maxes at 相), so a real
    行运 strength shift would be invisible if we diffed 状态. Diffing 力量 surfaces it:
    金 in a 酉 (metal) cycle reads 状态=相 but 变化=升. The magnitude is the number of
    net supporting factors gained/lost — ≥2 is a decisive swing (大升/大降).
    """
    diff = combined_strength - baseline_strength
    if diff >= 2:
        return "大升"
    if diff == 1:
        return "升"
    if diff == 0:
        return "持平"
    if diff == -1:
        return "降"
    return "大降"


_MOVE_PHRASE = {
    "大升": "力量大增", "升": "力量渐增", "持平": "力量持平",
    "降": "力量渐弱", "大降": "力量大减",
}
def _element_reading(
    element: str, ten_god: str, state: str, change: str, role: str,
    note: str, cycle_label: str,
) -> str:
    """One-line LLM-facing reading fusing 用神(角色) × movement × domain.

    The 角色 (喜用神/忌神/仇神/闲神) is chart-fixed and comes from get_yong_shen — this module
    must NOT re-derive it from 综合, or the role vocabulary would exist in two places and
    could diverge. The movement (变化) is this period's.

    A 喜神 strengthening is auspicious; a 忌神 strengthening is a caution — that
    cross-reference is the interpretive judgment the model should not have to guess.

    The 仇神 arm is why the role must be a real field rather than a 综合 lookup: a 仇神 is
    still 综合 == "平", so deriving the role from 综合 would call it 闲神 and report a rising
    one as 「平和应对」 — harmless — when it is in fact feeding the 忌神 the chart fears.
    """
    move = _MOVE_PHRASE.get(change, "力量持平")
    rising = change in ("大升", "升")
    falling = change in ("大降", "降")

    if role == "喜用神":
        verdict = (
            "喜神得势，运势得力，为吉" if rising
            else "喜神受挫，助力转弱，宜固本培元" if falling
            else "喜神平稳，得其滋养"
        )
    elif role == "忌神":
        verdict = (
            "忌神增势，压力渐显，宜谨慎防范" if rising
            else "忌神退避，反为吉兆" if falling
            else "忌神平稳，尚无大碍"
        )
    elif role == "仇神":
        verdict = (
            "仇神得势，暗助忌神，其党益盛，宜防" if rising
            else "仇神退避，忌神失其所生，反为吉兆" if falling
            else "仇神平稳，助忌之力未显"
        )
    else:
        verdict = "闲神随运流转，平和应对"

    reading = f"{ten_god}（{element}）为{role}，本{cycle_label}居{state}、{move}，{verdict}。"
    if note:
        reading += f"（{note}）"
    return reading


def _cycle_pillar_block(stem: str, branch: str) -> dict:
    """Minimal transiting-pillar block in the classifier's expected shape.

    空亡 is left empty on purpose: 岁运临空 is 填实 (an annotation), not a strength
    downgrade, so a transiting pillar must never contribute a void penalty.
    """
    hide = list(LunarUtil.ZHI_HIDE_GAN.get(branch, []))
    return {
        "天干": {"天干": stem},
        "地支": {"地支": branch},
        "藏干": {tier: {"天干": s} for tier, s in zip(_HIDE_TIERS, hide)},
        "空亡": {},
    }


def classify_with_transiting(
    ctx: NatalContext,
    transiting: tuple[tuple[str, str, str], ...],
    extra_dynamics: tuple = (),
) -> dict:
    """Reclassify the five elements over natal-4 + the given transiting pillars.

    transiting: ordered ((stem, branch, label), …) — e.g. just the 大运, or 大运+流年.
    extra_dynamics: cycle 柱位动态 (大运/流年-vs-natal) to merge with the natal ones.
    Season stays anchored to the natal 月令. Returns {element: {状态, 力量}}.
    """
    si_zhu = dict(ctx.natal_si_zhu)
    for stem, branch, label in transiting:
        si_zhu[label] = _cycle_pillar_block(stem, branch)
    dynamics = (
        list(ctx.natal_interactions.get("作用", {}).get("柱位动态", []))
        + list(extra_dynamics)
    )
    pillar_order = tuple(_NATAL_PILLAR_KEYS) + tuple(label for _, _, label in transiting)
    return QualitativeFiveElementsClassifier(
        si_zhu,
        {"作用": {"柱位动态": dynamics}},
        lunar_birthday=ctx.lunar_birthday,
        pillar_order=pillar_order,
    ).classify_all(include_strength=True)["五行"]


def _build_triggers(interactions: dict, five: dict, cycle_label: str) -> list[dict]:
    """引动 — elemental events the cycle pillar sets off, tagged with the resulting state.

    Each item's 元素 is looked up in the reclassified `five` map so the narrative reads
    against the actual period verdict instead of asserting strength blindly.
    """

    def state_of(elem: str) -> str:
        return five[elem]["状态"] if elem in five else ""

    def state_suffix(elem: str, st: str) -> str:
        return f"（值此{cycle_label}{elem}为{st}）" if elem and st else ""

    triggers: list[dict] = []
    for item in interactions.get("柱位动态", []):
        if item.get("强度") == "消融吸收":
            continue  # fully absorbed events trigger nothing
        itype = item.get("类型", "")

        # (label, element, base 说明) per trigger type. The base is the engine's own
        # 备注 — it is already worded correctly for each sub-case (e.g. 三合 增力 vs
        # 引动成局), so we don't re-describe it here.
        if itype in ("三合", "三会"):
            label, elem, base = itype, item.get("元素", ""), item.get("备注", "")
        elif itype == "六合" and item.get("形态") == "合化":
            label, elem, base = "六合合化", item.get("元素", ""), item.get("备注", "")
        elif itype == "六冲" and item.get("子类型") == "开库":
            label = "冲开库"
            elem = LunarUtil.WU_XING_GAN.get(item.get("开库详情", {}).get("透出藏干", ""), "")
            base = item.get("备注", "")
        elif itype == "干支透合":
            label = "干支透合"
            elem = LunarUtil.WU_XING_GAN.get(item.get("藏干详情", {}).get("藏干", ""), "")
            base = item.get("引动藏干", "")  # names the pillars — richer than 备注 here
        else:
            continue

        st = state_of(elem)
        triggers.append({
            "类型": label,
            "元素": elem,
            "状态": st,
            "说明": f"{base}{state_suffix(elem, st)}",
        })

    return triggers


def get_cycle_wu_xing(
    cycle_stem: str,
    cycle_branch: str,
    ctx: NatalContext,
    interactions: dict,
    pillar: dict,
    cycle_label: str = "大运",
    *,
    decade_pillar: tuple[str, str] | None = None,
    decade_dynamics: tuple = (),
    baseline: dict | None = None,
) -> dict:
    """
    Combined five-elements dynamics for one cycle pillar.

    大运 is a 4+1 reclassification (natal + 大运). 流年 is 4+2 (natal + 大运 + 流年):
    a year's 旺衰 is 岁运并临 — it must be read inside its decade — so pass the enclosing
    大运 via decade_pillar/decade_dynamics, and the decade's 五行 力量 as `baseline` so
    变化 isolates the year's own marginal push (vs the decade, not vs birth).

    Args:
        cycle_stem/cycle_branch: the transiting pillar.
        ctx:          NatalContext — natal si_zhu, natal interactions, lunar_birthday,
                      and the precomputed natal 五行 baseline (with 力量).
        interactions: output of get_cycle_interactions() ({"关系总览", "柱位动态"});
                      its 柱位动态 are merged into the reclassification and feed 引动.
        pillar:       the 运柱 block from build_cycle_pillar() — reused for its ten
                      gods (天干.十神 / 藏干.本气.十神) for the 对日主 axis.
        cycle_label:  "大运" | "流年" — the transiting pillar's key (matches
                      cycle_interactions' 组合明细) and 引动 label.
        decade_pillar:   (stem, branch) of the enclosing 大运 — set for 流年 only.
        decade_dynamics: that 大运's 柱位动态, merged in for 流年.
        baseline:     the 力量 map to diff 变化 against — the decade baseline for 流年,
                      or None to fall back to the natal baseline (大运 case).

    Returns:
        {"五行", "对日主", "引动"} — Chinese-keyed (see module docstring).
    """
    # 1. Reclassify over natal-4 + [大运] + this pillar. 变化 is measured on 力量 (pre-cap)
    #    against `baseline` (decade for 流年, natal for 大运); 本命 always shows the birth state.
    transiting: list[tuple[str, str, str]] = []
    if decade_pillar is not None:
        transiting.append((decade_pillar[0], decade_pillar[1], "大运"))
    transiting.append((cycle_stem, cycle_branch, cycle_label))
    extra_dynamics = list(decade_dynamics) + list(interactions.get("柱位动态", []))

    combined = classify_with_transiting(ctx, tuple(transiting), tuple(extra_dynamics))

    # 变化 is graded against `base_map` (decade for 流年, natal for 大运). 本命 always shows
    # the birth state; for 流年, 运基 also exposes the decade level so the reader sees the
    # natal → decade → year progression. 十神 tags each element's life-domain for the DM.
    dm_element = LunarUtil.WU_XING_GAN.get(ctx.effective_day_stem, "")
    base_map = baseline if baseline is not None else ctx.natal_five_elements
    ys = ctx.yong_shen["五行"]
    five = {}
    for el in ELEMENTS:
        change = _delta(combined[el]["力量"], base_map[el]["力量"])
        tg = element_ten_god_class(el, dm_element)
        yong_shen = ys[el]["综合"]           # 喜/忌/平 — chart-fixed favourability verdict
        role = ys[el]["角色"]                # 喜用神/忌神/仇神/闲神 — chart-fixed ROLE
        entry = {
            "状态": combined[el]["状态"],
            "本命": ctx.natal_five_elements[el]["状态"],
            "变化": change,
            "十神": tg,
            "喜忌": yong_shen,
            # 角色 splits the 平 bucket into 仇神 (feeds a 忌) and 闲神 (idle). Carried as
            # DATA, not only in the 解读 prose, so consumers need not parse the sentence.
            "角色": role,
            "解读": _element_reading(
                el, tg, combined[el]["状态"], change, role, ys[el]["备注"], cycle_label
            ),
        }
        if baseline is not None:  # 流年 only — the enclosing 大运's level for this element
            entry["运基"] = base_map[el]["状态"]
        five[el] = entry

    # 2. Day-master axis — derived from the pillar's ten gods (single source of truth).
    #    The branch's 本气 hidden stem carries the branch's dominant ten god.
    stem_god = pillar["天干"]["十神"]
    branch_god = pillar["藏干"].get("本气", {}).get("十神", "")
    stem_rel, _, stem_dir = _god_axis(stem_god)
    branch_rel, branch_class, branch_dir = _god_axis(branch_god)

    return {
        "五行": five,
        "对日主": {
            "天干": {"关系": f"{stem_rel}({stem_god})", "方向": stem_dir},
            "地支本气": {"关系": f"{branch_rel}({branch_god})", "方向": branch_dir},
            # Branch qi is the period's dominant current — it carries the verdict.
            "结合日主强弱": _strength_verdict(branch_dir, branch_class, ctx.dm_strength),
        },
        "引动": _build_triggers(interactions, five, cycle_label),
    }
