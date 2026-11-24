"""
Applies classical BaZi texts to a cycle pillar (大运 / 流年) — the cycle counterpart of
interaction_natal_chart.py.

The cycle modules beside this one (cycle_interactions, cycle_shen_sha, cycle_wu_xing,
sui_yun) compute FACTS about a transiting pillar. This module READS those facts against
encoded classical rules and emits 古籍解读, exactly as interaction_natal_chart.py does for
the natal chart.

Separate engine, shared definitions
-----------------------------------
Rules use the SAME schema as the natal rules (逻辑名称 / 判定模式 / 判定逻辑 / 断语 /
现代解读) and are evaluated by the natal engine's own `evaluate_rule` and
CONDITION_EVALUATORS. Nothing is redefined here. What this module adds:

* A ChartContext whose `pillars` carries the four natal pillars PLUS
  ``运柱`` (the pillar being analysed) and, for a 流年, ``大运`` (its enclosing decade).
  ``全局`` still resolves to the four natal pillars only (``_ALL_PILLARS``), so a natal
  condition never accidentally matches the transiting pillar — a rule must name 运柱 /
  大运 explicitly. Same opt-in pattern the natal engine uses for 胎元.
* Three cycle-only rule fields:
    适用周期 (required) — ["大运"], ["流年"] or both; a rule outside its period is skipped.
    来源     (required) — the chapter the rule encodes, e.g. "卷一·纳音取象".
    依据     (optional) — the classical sentence that licenses applying the rule to a
                          cycle (e.g. 「此金体薄……限运同论」); emitted with the match.
    标注     (optional) — severity metadata, e.g. "条件触发·非定论" on verdicts such as
                          夭, which are kept verbatim and never softened.

What the context carries
------------------------
* Natal pillars from NatalContext.rule_si_zhu — the natal pipeline's 七杀→偏官 /
  食神→伤官 relabels applied, so natal-side ten-god matching follows bazi-natal.md
  (natal 煞 rules list ["七杀", "偏官"]). natal_si_zhu stays raw for 制化.
* The 运柱 (and a 流年's 大运): 天干 / 地支 with 五行, RAW ten gods (天干 + 藏干 tiers —
  a transiting pillar has no adjacency, so it is never relabelled), 十二长生
  {日干, 自坐} and 纳音.
* The 运柱's 神煞 (ctx.shen_sha["运柱"]) and its interactions (ctx.interactions), passed
  in from the already-computed cycle layers, with the pillar's own label in 组合明细
  (and as a directional item's 主动方) renamed to 运柱 so the natal 交互 evaluator can
  address it. ctx.interactions holds ONLY the 运柱's interactions, so a 交互 condition
  scoped to a natal pillar reads "between the 运柱 and that pillar" (交互 @日柱 = 岁/运 vs 日).
* 日主强弱 from NatalContext.dm_strength.

CYCLE_POSITION_TYPES / NATAL_POSITION_TYPES whitelist the condition types a rule may
use on each side; tests/test_cycle_interpretation.py enforces them.

Public gateway: get_cycle_interpretations(ctx, cycle_stem, cycle_branch, cycle_label,
                                          companion=None, shen_sha=None,
                                          interactions=None) -> dict
"""

from __future__ import annotations

from lunar_python.util import LunarUtil

from apps.backend.astronomer_logic.cycles.cycle_pillars import NatalContext
from apps.backend.astronomer_logic.day_master_strength import get_stem_element
from apps.backend.astronomer_logic.interaction_natal_chart import (
    ChartContext,
    evaluate_rule,
)
from apps.backend.astronomer_logic.natal_interactions import branch_elements
from apps.backend.astronomer_logic.twelve_life_stages import _self_seated_stage
from apps.backend.data.san_ming_tong_hui_v1 import (
    volume_1_60_jia_zi_cycle_predictions,
    volume_1_nayin_ge_ju_cycle_predictions,
)
from apps.backend.data.san_ming_tong_hui_v2 import (
    volume_2_da_yun_cycle_predictions,
    volume_2_gan_zhi_cycle_predictions,
    volume_2_tai_sui_cycle_predictions,
)

CYCLE_PILLAR = "运柱"
COMPANION_PILLAR = "大运"
# 限 (限运 / 限数) means a 运 period — 大运 and 小运 — so 卷一's 限 rules list both. 流年 is a
# valid period for rules that name the 太岁; none in 卷一 do.
CYCLE_PERIODS = frozenset({"大运", "流年", "小运"})

# Condition types that may target the 运柱 / 大运 — each reads only fields the transiting
# entry carries (天干/地支/五行/十神/藏干/十二长生/纳音), or its 神煞 / interactions.
# 计数_神煞 counts the 运柱's own stars (「诸凶煞并临」); 交互 may filter by 主动方 (运克岁).
CYCLE_POSITION_TYPES = frozenset({
    "特定组合", "天干值", "地支值", "纳音五行", "五行", "十神", "十二长生", "神煞", "计数_神煞",
    "交互",
})

# Natal-side condition types usable from a cycle rule. Ten gods read rule_si_zhu (偏官-aware).
NATAL_POSITION_TYPES = frozenset({
    "特定组合", "天干值", "地支值", "纳音五行", "计数_纳音五行", "五行", "计数_五行",
    "十神", "十神_无", "日主强弱",
})

# Natal strength floor for interactions, as the natal engine applies (轻微/极弱 excluded).
_MATERIAL_STRENGTH = frozenset({"强势主流", "显著影响", "中等衰减"})


_HIDE_TIERS = ("本气", "中气", "余气")


def _transiting_pillar(stem: str, branch: str, ctx: NatalContext) -> dict:
    """A cycle pillar in the natal 四柱实体 shape.

    Ten gods are RAW (LunarUtil.SHI_SHEN against the effective day stem, as
    build_cycle_pillar does): the 七杀→偏官 / 食神→伤官 relabels are adjacency-based and a
    transiting pillar has no adjacency. 十二长生.日干 uses the RAW day stem, matching
    build_cycle_pillar.
    """
    day = ctx.effective_day_stem
    hidden = {
        tier: {
            "天干": h,
            "十神": LunarUtil.SHI_SHEN.get(day + h, "无"),
            "五行": get_stem_element(h),
        }
        for tier, h in zip(_HIDE_TIERS, LunarUtil.ZHI_HIDE_GAN.get(branch, []))
    }
    return {
        "天干": {
            "天干": stem,
            "五行": get_stem_element(stem),
            "十神": LunarUtil.SHI_SHEN.get(day + stem, "无"),
        },
        "地支": {"地支": branch, "五行": branch_elements.get(branch, "")},
        "藏干": hidden,
        "十二长生": {
            "日干": _self_seated_stage(ctx.day_stem, branch),
            "自坐": _self_seated_stage(stem, branch),
        },
        "纳音": LunarUtil.NAYIN.get(stem + branch, ""),
    }


def _as_rule_interactions(interactions: list[dict], cycle_label: str) -> list[dict]:
    """The pillar's own 柱位动态, re-keyed for the natal 交互 evaluator.

    The cycle engine keys the analysed pillar by its period (大运/流年/小运); rules address
    it as 运柱. A 流年's companion keeps its 大运 key, which is also its position name here.
    """
    out = []
    for item in interactions:
        if item.get("强度") not in _MATERIAL_STRENGTH:
            continue
        combo = {
            (CYCLE_PILLAR if k == cycle_label else k): v
            for k, v in item.get("组合明细", {}).items()
        }
        renamed = {**item, "组合明细": combo}
        if item.get("主动方") == cycle_label:  # a directional item's actor is a position too
            renamed["主动方"] = CYCLE_PILLAR
        out.append(renamed)
    return out


def build_cycle_chart_context(
    ctx: NatalContext,
    cycle_stem: str,
    cycle_branch: str,
    companion: tuple[str, str] | None = None,
    shen_sha: list[dict] | None = None,
    interactions: list[dict] | None = None,
    cycle_label: str = "大运",
) -> ChartContext:
    """Natal pillars + 运柱 (+ 大运 for a 流年) in one ChartContext.

    Args:
        ctx:          the request's NatalContext (needs rule_si_zhu).
        cycle_stem/cycle_branch: the pillar being analysed.
        companion:    (stem, branch) of the enclosing 大运 when the pillar is a 流年;
                      None for a 大运 or 小运.
        shen_sha:     the pillar's computed 神煞 ([{名称, 来源}, …]), if any.
        interactions: the pillar's computed 柱位动态, if any.
        cycle_label:  the pillar's period — its 组合明细 key is renamed to 运柱.
    """
    if ctx.rule_si_zhu is None:
        raise ValueError("NatalContext.rule_si_zhu is required for classical cycle rules")
    pillars = dict(ctx.rule_si_zhu)
    pillars[CYCLE_PILLAR] = _transiting_pillar(cycle_stem, cycle_branch, ctx)
    if companion is not None:
        pillars[COMPANION_PILLAR] = _transiting_pillar(*companion, ctx)
    return ChartContext(
        gender="男" if ctx.gender == 1 else "女",
        pillars=pillars,
        shen_sha={CYCLE_PILLAR: list(shen_sha or [])},
        interactions=_as_rule_interactions(interactions or [], cycle_label),
        five_elements=ctx.natal_five_elements,
        day_master={"强弱": ctx.dm_strength},
        lunar_birthday=ctx.lunar_birthday,
    )


def _name_the_period(evidence, cycle_label: str):
    """Replace the position name 运柱 with the period it stood for (大运 / 流年 / 小运).

    运柱 is how a RULE addresses "the pillar under analysis" — one rule serves several
    periods. In the OUTPUT that indirection only obscures: a reader (human or LLM) seeing an
    evidence item on its own should read 宫位: 小运, not 宫位: 运柱. Values only; the
    companion's 大运 label is already concrete and passes through unchanged.
    """
    if isinstance(evidence, dict):
        return {
            (cycle_label if k == CYCLE_PILLAR else k): _name_the_period(v, cycle_label)
            for k, v in evidence.items()
        }
    if isinstance(evidence, list):
        return [_name_the_period(v, cycle_label) for v in evidence]
    return cycle_label if evidence == CYCLE_PILLAR else evidence


def _format_cycle_match(rule: dict, evidence: dict | list[dict], cycle_label: str) -> dict:
    entry: dict = {
        "逻辑名称": rule["逻辑名称"],
        "来源": rule["来源"],
        "结论": rule["断语"],
        "证据": _name_the_period(evidence, cycle_label),
    }
    for optional in ("现代解读", "依据", "标注", "编码说明"):
        if optional in rule:
            entry[optional] = rule[optional]
    return entry


def _run(rules: list[dict], context: ChartContext, cycle_label: str) -> list[dict]:
    matched = []
    for rule in rules:
        if cycle_label not in rule["适用周期"]:
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_cycle_match(rule, evidence, cycle_label))
    return matched


# (output group, rule list). Adding a chapter = one line here + its rule list.
CYCLE_ANALYZERS: list[tuple[str, list[dict]]] = [
    ("释六十甲子", volume_1_60_jia_zi_cycle_predictions),
    ("纳音格局", volume_1_nayin_ge_ju_cycle_predictions),
    ("论大运", volume_2_da_yun_cycle_predictions),
    ("论干支", volume_2_gan_zhi_cycle_predictions),
    ("论太岁", volume_2_tai_sui_cycle_predictions),  # 论太岁 + 总论岁运 (each rule names its 来源)
]


def get_cycle_interpretations(
    ctx: NatalContext,
    cycle_stem: str,
    cycle_branch: str,
    cycle_label: str,
    companion: tuple[str, str] | None = None,
    shen_sha: list[dict] | None = None,
    interactions: list[dict] | None = None,
) -> dict:
    """Classical-text readings for one cycle pillar.

    Args:
        ctx:          the request's NatalContext.
        cycle_stem/cycle_branch: the pillar being analysed.
        cycle_label:  "大运", "流年" or "小运" — filters rules by 适用周期.
        companion:    (stem, branch) of the enclosing 大运 for a 流年, else None.
        shen_sha:     the pillar's computed 神煞 entries ({名称, 来源}), if any.
        interactions: the pillar's computed 柱位动态 (作用), if any.

    Returns:
        {group: [match, ...]} holding only groups with at least one match. An empty dict
        means "evaluated, nothing fired" — the key is always present on the entry.
    """
    if cycle_label not in CYCLE_PERIODS:
        raise ValueError(f"cycle_label must be one of {sorted(CYCLE_PERIODS)}, got {cycle_label!r}")
    context = build_cycle_chart_context(
        ctx, cycle_stem, cycle_branch, companion, shen_sha, interactions, cycle_label
    )
    result: dict[str, list[dict]] = {}
    for group, rules in CYCLE_ANALYZERS:
        matched = _run(rules, context, cycle_label)
        if matched:
            result[group] = matched
    return result


__all__: list[str] = [
    "CYCLE_ANALYZERS",
    "CYCLE_POSITION_TYPES",
    "NATAL_POSITION_TYPES",
    "build_cycle_chart_context",
    "get_cycle_interpretations",
]
