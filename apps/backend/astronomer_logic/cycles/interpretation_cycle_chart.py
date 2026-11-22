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

Supported condition types
-------------------------
The transiting pillar entry carries 天干 / 地支 / 纳音 only (no ten gods, 藏干, 神煞),
so only condition types that read those fields may target 运柱 / 大运 — see
CYCLE_POSITION_TYPES. Natal-side conditions (全局, 年柱 …) may use the natal
evaluators that read 天干 / 地支 / 纳音 / counts; anything needing natal ten gods is
deferred: this context is built from NatalContext, whose ten gods are deliberately RAW
(no 七杀→偏官 relabel), so ten-god matching on the natal side would break the
「natal-side matching requires 偏官」 rule. tests/test_cycle_interpretation.py enforces
both whitelists.

Public gateway: get_cycle_interpretations(ctx, cycle_stem, cycle_branch, cycle_label,
                                          companion=None) -> dict
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
from apps.backend.data.san_ming_tong_hui_v1 import (
    volume_1_60_jia_zi_cycle_predictions,
    volume_1_nayin_ge_ju_cycle_predictions,
)

CYCLE_PILLAR = "运柱"
COMPANION_PILLAR = "大运"
# 限 (限运 / 限数) means a 运 period — 大运 and 小运 — so 卷一's 限 rules list both. 流年 is a
# valid period for rules that name the 太岁; none in 卷一 do.
CYCLE_PERIODS = frozenset({"大运", "流年", "小运"})

# Condition types whose evaluator reads only 天干 / 地支 / 纳音 from the named pillar,
# and therefore works on the slim transiting-pillar entry built below.
CYCLE_POSITION_TYPES = frozenset({"特定组合", "天干值", "地支值", "纳音五行"})

# Natal-side condition types usable from a cycle rule: they read natal 天干 / 地支 / 纳音
# (or counts over them), which NatalContext carries faithfully.
NATAL_POSITION_TYPES = frozenset({"特定组合", "天干值", "地支值", "纳音五行", "计数_纳音五行"})


def _transiting_pillar(stem: str, branch: str) -> dict:
    """A cycle pillar in the natal 四柱实体 shape, limited to what the whitelisted
    evaluators read (天干.天干 / 地支.地支 / 纳音)."""
    return {
        "天干": {"天干": stem, "五行": get_stem_element(stem)},
        "地支": {"地支": branch, "五行": branch_elements.get(branch, "")},
        "纳音": LunarUtil.NAYIN.get(stem + branch, ""),
    }


def build_cycle_chart_context(
    ctx: NatalContext,
    cycle_stem: str,
    cycle_branch: str,
    companion: tuple[str, str] | None = None,
) -> ChartContext:
    """Natal pillars + 运柱 (+ 大运 for a 流年) in one ChartContext.

    Args:
        ctx:          the request's NatalContext.
        cycle_stem/cycle_branch: the pillar being analysed.
        companion:    (stem, branch) of the enclosing 大运 when the pillar is a 流年;
                      None for a 大运 (a decade has no enclosing pillar).
    """
    pillars = dict(ctx.natal_si_zhu)
    pillars[CYCLE_PILLAR] = _transiting_pillar(cycle_stem, cycle_branch)
    if companion is not None:
        pillars[COMPANION_PILLAR] = _transiting_pillar(*companion)
    return ChartContext(
        gender="男" if ctx.gender == 1 else "女",
        pillars=pillars,
        shen_sha={},
        interactions=[],
        five_elements=ctx.natal_five_elements,
        day_master={},
        lunar_birthday=ctx.lunar_birthday,
    )


def _format_cycle_match(rule: dict, evidence: dict | list[dict]) -> dict:
    entry: dict = {
        "逻辑名称": rule["逻辑名称"],
        "来源": rule["来源"],
        "结论": rule["断语"],
        "证据": evidence,
    }
    for optional in ("现代解读", "依据", "标注"):
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
            matched.append(_format_cycle_match(rule, evidence))
    return matched


# (output group, rule list). Adding a chapter = one line here + its rule list.
CYCLE_ANALYZERS: list[tuple[str, list[dict]]] = [
    ("释六十甲子", volume_1_60_jia_zi_cycle_predictions),
    ("纳音格局", volume_1_nayin_ge_ju_cycle_predictions),
]


def get_cycle_interpretations(
    ctx: NatalContext,
    cycle_stem: str,
    cycle_branch: str,
    cycle_label: str,
    companion: tuple[str, str] | None = None,
) -> dict:
    """Classical-text readings for one cycle pillar.

    Args:
        ctx:          the request's NatalContext.
        cycle_stem/cycle_branch: the pillar being analysed.
        cycle_label:  "大运", "流年" or "小运" — filters rules by 适用周期.
        companion:    (stem, branch) of the enclosing 大运 for a 流年, else None.

    Returns:
        {group: [match, ...]} holding only groups with at least one match. An empty dict
        means "evaluated, nothing fired" — the key is always present on the entry.
    """
    if cycle_label not in CYCLE_PERIODS:
        raise ValueError(f"cycle_label must be one of {sorted(CYCLE_PERIODS)}, got {cycle_label!r}")
    context = build_cycle_chart_context(ctx, cycle_stem, cycle_branch, companion)
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
