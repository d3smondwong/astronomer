"""
岁运 — the classical reading of 流年 vs 大运.

cycle_interactions.py DETECTS the 流年-大运 relations (it scans the year against the
decade as a fifth opponent). This module READS them: it names the classical
configurations, and — the part no detector can supply — works out **whether the 大运
can still act on the 命局 this year**.

That second job is the whole point. The 大运's 柱位动态 are computed ONCE per decade,
against the natal chart. But classically the year meets its decade first, and only what
survives that meeting reaches the 命局: a 大运 whose branch is bound by the 流年
(合绊) does not deliver its 冲 to the 日支 that year, however強 the decade-level analysis
rated it. So each 流年 re-resolves its decade's actions under the 岁运 locks and reports
what changed.

The 合/冲 asymmetry is the load-bearing rule and the easiest thing to get backwards:

    合 BINDS   — a 大运 tied up by the year is 绊住; its other business is suspended.
                 This DOWNGRADES the decade's actions (贪合忘冲).
    冲 AGITATES — 岁冲运 destabilises the decade, it does not tie it down. 冲则动:
                 the 大运 still acts on the 命局, more violently if anything. This
                 downgrades NOTHING.

Reading 冲 as suppression would silence exactly the years the classics call the loudest.

Each lock here behaves EXACTLY as the same lock behaves inside the engine's own
resolution passes — PRIMARY_六合 reaches the branch layer, STEM_天干合 the stem layer,
STRUCTURAL_三合/三会 the branch and pillar layers, and 交战 (岁运并临/反吟) spans
everything, mirroring the engine's own 反吟/伏吟 pre-pass. Same locks, same tables, same
meaning — applied to the decade's items instead of the year's.

Output is a compact DELTA, not a re-issued copy of the decade's list: only the items whose
强度 actually moved, each carrying its own identity and a complete 说明 sentence so a
downstream reader (LLM or human) never has to join back to the decade entry. `大运态` is
ALWAYS present — an empty 大运制约 must read as "the decade acts normally", never as
"we did not compute it".
"""

from copy import deepcopy

from apps.backend.astronomer_logic.cycles.cycle_interactions import (
    apply_lock,
    cap,
    rank,
)
from apps.backend.astronomer_logic.cycles.cycle_pillars import NatalContext
from apps.backend.astronomer_logic.day_master_strength import get_stem_element
from apps.backend.astronomer_logic.natal_interactions import branch_elements

_DA_YUN = "大运"
_LIU_NIAN = "流年"

# The engine strips its internal _layer handle at output(), so the decade's items arrive
# here as plain dicts. Re-derive the layer from 类型 — the same partition the engine uses.
_STEM_TYPES = frozenset({"天干合", "天干冲", "天干克", "干支透合"})
_PILLAR_TYPES = frozenset({"反吟", "伏吟"})

# 大运态 severity, worst first. A decade locked in 岁运反吟 is not merely 被合绊.
_STATE_ORDER = ("交战", "入局", "被合绊", "受冲", "常态")

# 交战 (岁运并临 / 岁运反吟) has no lock-table row of its own — the two transiting pillars
# are wholly at odds, so every decade action is read inside that turbulence. Mirrors the
# engine's own PREPASS fallback ceiling.
_TURBULENCE_CEILING = "中等衰减"


def _layer_of(itype: str) -> str:
    if itype in _STEM_TYPES:
        return "stem"
    if itype in _PILLAR_TYPES:
        return "pillar"
    return "branch"


def _verdict(element: str, ctx: NatalContext) -> str:
    """喜 / 忌 / 平 for an element, per the chart's 用神."""
    return ctx.yong_shen.get("五行", {}).get(element, {}).get("综合", "平")


def _joined(detail: dict) -> str:
    return "".join(f"{k}{v}" for k, v in detail.items())


def _is_sui_yun(item: dict) -> bool:
    return _DA_YUN in item.get("组合明细", {})


# ── (b) naming the classical configurations ──────────────────────────────────


def _name_configurations(
    items: list[dict],
    liu_nian_gz: str,
    da_yun_gz: str,
    ctx: NatalContext,
) -> list[dict]:
    """特殊组合 — the named 岁运 patterns, each {名称, 级别, 说明}.

    级别: 重 (a genuine event trigger) | 中 | 轻. Severity is NOT read off the pattern
    alone — 岁运并临 is gated on 喜忌, because a decade and year that repeat a 喜用 干支
    double a favourable force rather than doubling a calamity.
    """
    specials: list[dict] = []
    by_type: dict[str, list[dict]] = {}
    for it in items:
        by_type.setdefault(it["类型"], []).append(it)

    # 岁运并临 — 流年干支 == 大运干支. 《三命通会》「岁运并临，灾殃立至」, but the classics are
    # describing a 忌神 doubling itself. Same 干支, inverted verdict, depending on 喜忌.
    if by_type.get("伏吟"):
        stem_el = get_stem_element(da_yun_gz[0])
        branch_el = branch_elements.get(da_yun_gz[1], "")
        verdicts = {_verdict(e, ctx) for e in (stem_el, branch_el) if e}
        if "忌" in verdicts:
            specials.append({
                "名称": "岁运并临",
                "级别": "重",
                "说明": (
                    f"流年{liu_nian_gz}与大运{da_yun_gz}干支全同，岁运并临。"
                    f"所临{stem_el}{branch_el}为命局忌神，忌神叠加而力倍，"
                    f"古谓「岁运并临，灾殃立至」，主此年事机剧烈，宜守不宜进"
                ),
            })
        else:
            specials.append({
                "名称": "岁运并临",
                "级别": "中",
                "说明": (
                    f"流年{liu_nian_gz}与大运{da_yun_gz}干支全同，岁运并临。"
                    f"所临{stem_el}{branch_el}非忌，喜用叠临则力量倍增，"
                    f"不作灾咎论 — 惟其气过专，成败皆速"
                ),
            })

    # 岁运反吟 — 天克地冲. 「岁运交战，凡事不宁」.
    if by_type.get("反吟"):
        specials.append({
            "名称": "岁运反吟",
            "级别": "重",
            "说明": (
                f"流年{liu_nian_gz}与大运{da_yun_gz}天克地冲，岁运反吟。"
                f"岁运交战，凡事不宁，主此年变动剧烈、旧局崩解"
            ),
        })

    # 岁运双合 — 天合地合. The strongest bind: both halves of the decade are tied up.
    stem_he = [it for it in by_type.get("天干合", []) if _is_sui_yun(it)]
    branch_he = [it for it in by_type.get("六合", []) if _is_sui_yun(it)]
    if stem_he and branch_he:
        specials.append({
            "名称": "岁运双合",
            "级别": "中",
            "说明": (
                f"流年{liu_nian_gz}与大运{da_yun_gz}天合地合，双合羁绊。"
                f"大运干支尽为流年所系，本年大运难以施力于命局，主牵绊、迁延、事多受制于人"
            ),
        })

    # 岁运相冲 — 支冲 without the stem half (a full 天克地冲 is 反吟, named above).
    # 「岁运冲战」: the decade's branch and the year's are at odds. A major trigger in its
    # own right — but note it BINDS nothing (see _derive_locks).
    if by_type.get("六冲") and not by_type.get("反吟"):
        specials.append({
            "名称": "岁运相冲",
            "级别": "中",
            "说明": (
                f"流年支{liu_nian_gz[1]}与大运支{da_yun_gz[1]}相冲，岁运冲战。"
                f"冲则动 — 主此年动荡、迁移、变革，旧事被冲开；"
                f"惟冲而不绊，大运作用于命局如常"
            ),
        })

    # 君臣 — 太岁为君，大运为臣。方向定其轻重，主动方 already carries it.
    #
    # A 克 the engine has already absorbed (消融吸收) is a 克 that does not happen: the two
    # stems are bound by a 合 (戊癸合 → 戊 bonds with 癸, it does not strike it), and
    # _pass4_stem_lock has said so. Naming it 运犯岁君 would resurrect an attack the
    # resolution already ruled out.
    for it in by_type.get("天干克", []):
        if it.get("强度") == "消融吸收":
            continue
        actor = it.get("主动方")
        if actor == _DA_YUN:
            specials.append({
                "名称": "运犯岁君",
                "级别": "重",
                "说明": (
                    f"大运干{da_yun_gz[0]}克流年干{liu_nian_gz[0]}，臣犯君。"
                    f"古谓「运犯岁君，灾殃必重」，主此年触犯时势、逆势而动者受挫"
                ),
            })
        elif actor == _LIU_NIAN:
            specials.append({
                "名称": "岁君伏运",
                "级别": "轻",
                "说明": (
                    f"流年干{liu_nian_gz[0]}克大运干{da_yun_gz[0]}，君临臣。"
                    f"岁能伤运，运不能伤岁 — 此为顺，其咎轻，主时势压人而非人犯时势"
                ),
            })

    # 天比地比 — 岁运同气增力 (branch 比和 + same-element stems, but NOT 伏吟, which is
    # the identical-干支 case already named above).
    if not by_type.get("伏吟"):
        peer_branch = [it for it in by_type.get("比和", []) if _is_sui_yun(it)]
        same_stem_el = get_stem_element(liu_nian_gz[0]) == get_stem_element(da_yun_gz[0])
        if peer_branch and same_stem_el:
            element = peer_branch[0].get("元素", "")
            specials.append({
                "名称": "天比地比",
                "级别": "轻",
                "说明": (
                    f"流年{liu_nian_gz}与大运{da_yun_gz}天比地比，{element}气同类叠加。"
                    f"岁运同气，其力专而不杂，{element}之事本年格外显著"
                ),
            })

    return specials


# ── (c) the 绊 pass: what the 大运 can still do to the 命局 this year ──────────


def _derive_locks(items: list[dict]) -> tuple[str, list[tuple[str, str, dict]]]:
    """→ (大运态, [(lock_type, layer_scope, causing_item), ...]).

    layer_scope names which of the decade's layers a lock reaches — the SAME scope
    that lock has inside the engine's own passes. "*" is the 交战 blanket.
    """
    locks: list[tuple[str, str, dict]] = []
    states: set[str] = set()

    for it in items:
        itype = it["类型"]

        # 交战 — the decade and the year are wholly at odds. Spans every layer, exactly
        # as the engine's own 反吟/伏吟 pre-pass does.
        if itype in ("伏吟", "反吟"):
            locks.append((f"PREPASS_{itype}", "*", it))
            states.add("交战")

        # 入局 — the 大运 branch is drawn into a bureau with the year; its qi belongs to
        # the frame now, and it forgets its business elsewhere (贪会忘冲).
        elif itype in ("三合", "三会"):
            locks.append((f"STRUCTURAL_{itype}", "branch|pillar", it))
            states.add("入局")

        # 被合绊 — 合 binds. Branch half (贪合忘冲) and stem half are tied separately.
        elif itype == "六合":
            locks.append(("PRIMARY_六合", "branch", it))
            states.add("被合绊")
        elif itype == "天干合":
            locks.append(("STEM_天干合", "stem", it))
            states.add("被合绊")

        # 受冲 — 冲 agitates but does NOT bind. No lock: the decade still acts on the
        # 命局, and arguably harder. Recording the state (with no downgrade) is the point.
        elif itype == "六冲":
            states.add("受冲")

    state = next((s for s in _STATE_ORDER if s in states), "常态")
    return state, locks


def _in_scope(item: dict, scope: str) -> bool:
    """Is this decade item within the lock's reach?

    Layer scope, plus one refinement the layer alone cannot express: STEM_天干合 binds the
    大运's STEM, so it only reaches decade items the 大运 stem actually acts in. A decade
    干支透合 of 形态 命局引动 is a NATAL stem reaching into the 大运's BRANCH — the bound
    stem is not an actor in it, and it goes on happening. (The engine's own _pass4_stem_lock
    makes the same distinction from the other side.)
    """
    if scope != "*" and _layer_of(item["类型"]) not in scope.split("|"):
        return False
    if (
        scope == "stem"
        and item["类型"] == "干支透合"
        and item.get("形态") == "命局引动"
    ):
        return False
    return True


def _explain(item: dict, before: str, after: str, cause: dict, da_yun_gz: str) -> str:
    """A complete, self-contained sentence — the reader must never need the decade entry."""
    targets = [f"{k}{v}" for k, v in item["组合明细"].items() if k != _DA_YUN]
    target = "、".join(targets) if targets else "命局"
    return (
        f"大运{da_yun_gz}受{cause['类型']}（{_joined(cause['组合明细'])}）牵制，"
        f"本年对{target}的{item['类型']}之力由{before}降至{after}"
    )


def _constrain_decade(
    decade_dynamics: tuple,
    state: str,
    locks: list[tuple[str, str, dict]],
    da_yun_gz: str,
) -> tuple[tuple, list[dict]]:
    """Re-resolve the decade's actions under the 岁运 locks.

    Returns (this year's decade dynamics, the delta). The re-resolved list — not the raw
    one — is what the year's 五行 layer must read: if the 岁运 layer says a bound 大运
    cannot 冲 the 日支, the elements must not move as though it did.
    """
    if not locks:
        return tuple(decade_dynamics), []

    resolved = [deepcopy(it) for it in decade_dynamics]
    before = [it["强度"] for it in resolved]
    causes: dict[int, dict] = {}

    for idx, item in enumerate(resolved):
        for lock_type, scope, cause in locks:
            if not _in_scope(item, scope):
                continue
            prior = item["强度"]
            if state == "交战" and scope == "*":
                cap(item, _TURBULENCE_CEILING, f"岁运{cause['类型']}，大运诸作用皆受牵制")
            else:
                apply_lock(item, lock_type)
            if rank(item["强度"]) > rank(prior):
                causes[idx] = cause  # last lock that actually moved it owns the 说明

    delta = [
        {
            "类型": item["类型"],
            "组合明细": item["组合明细"],
            "原强度": before[idx],
            "本年强度": item["强度"],
            "起因": {
                "类型": causes[idx]["类型"],
                "组合明细": causes[idx]["组合明细"],
            },
            "说明": _explain(
                item, before[idx], item["强度"], causes[idx], da_yun_gz
            ),
        }
        for idx, item in enumerate(resolved)
        if idx in causes
    ]
    return tuple(resolved), delta


def _state_remark(state: str, liu_nian_gz: str, da_yun_gz: str) -> str:
    if state == "交战":
        return (
            f"大运{da_yun_gz}与流年{liu_nian_gz}交战，本年大运施于命局之力全面受牵，"
            f"吉凶皆不能尽其功"
        )
    if state == "入局":
        return (
            f"大运{da_yun_gz}与流年{liu_nian_gz}会合成局，运支之气尽归局中，"
            f"本年对命局别处之冲刑消减"
        )
    if state == "被合绊":
        return (
            f"大运{da_yun_gz}为流年{liu_nian_gz}所合，绊而不发，"
            f"本年难以施力于命局（合则不冲）"
        )
    if state == "受冲":
        return (
            f"流年{liu_nian_gz}冲大运{da_yun_gz}，运局动荡。冲则动而不绊 —"
            f"大运作用于命局如常，且更形激烈"
        )
    return f"大运{da_yun_gz}不受流年{liu_nian_gz}羁绊，本年照常作用于命局"


def analyse_sui_yun(
    liu_nian_stem: str,
    liu_nian_branch: str,
    da_yun_stem: str,
    da_yun_branch: str,
    interactions: dict,
    decade_dynamics: tuple,
    ctx: NatalContext,
) -> tuple[dict, tuple]:
    """
    Read the 流年-大运 relationship and its consequences for the decade.

    Args:
        liu_nian_stem/branch: the year.
        da_yun_stem/branch:   the enclosing decade.
        interactions:         the year's 1×5 output from get_cycle_interactions
                              (must have been run WITH a CompanionPillar).
        decade_dynamics:      the decade's 柱位动态 (decade-level, vs the natal chart).
        ctx:                  NatalContext — supplies 用神 for the 喜忌 gate.

    Returns:
        (岁运 block, this year's re-resolved decade dynamics).

        The 岁运 block is {关系总览, 特殊组合, 大运态, 大运态说明, 大运制约, 警示}.
        The second element must be passed to the year's 五行 layer in place of the raw
        decade dynamics, so the two layers agree on whether the 大运 actually acted.
    """
    liu_nian_gz = f"{liu_nian_stem}{liu_nian_branch}"
    da_yun_gz = f"{da_yun_stem}{da_yun_branch}"

    sui_yun_items = [it for it in interactions["柱位动态"] if _is_sui_yun(it)]

    specials = _name_configurations(sui_yun_items, liu_nian_gz, da_yun_gz, ctx)
    state, locks = _derive_locks(sui_yun_items)
    constrained, delta = _constrain_decade(decade_dynamics, state, locks, da_yun_gz)

    block = {
        "关系总览": [
            f"{it['类型']}({_joined(it['组合明细'])})" for it in sui_yun_items
        ],
        "特殊组合": specials,
        "大运态": state,
        "大运态说明": _state_remark(state, liu_nian_gz, da_yun_gz),
        "大运制约": delta,
        # Flattened for the 运势 advisory — 评级 stays a 五行-favourability verdict; this
        # is intensity and delivery, an orthogonal axis that must not collapse into it.
        "警示": [
            f"{s['名称']}（{s['级别']}）：{s['说明']}"
            for s in specials
            if s["级别"] == "重"
        ],
    }
    return block, constrained
