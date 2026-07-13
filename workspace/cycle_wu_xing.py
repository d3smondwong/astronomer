"""
岁运五行动态 Cycle Pillar Elemental Dynamics — qualitative.

Classifies what the transiting pillar's elements do to the day master, in the
context of the natal season (the chart's climate anchor never changes — a
大运 shifts the ambient qi, it does not re-anchor 旺衰) and the natal DM
strength verdict, and folds in the elemental shifts triggered by the cycle's
interactions (合化/三合/三会/开库/干支透合 → 引动).

Qualitative by design: the backend's five-element layer is the qualitative
classifier (natal_five_elements), not the legacy quantitative score engine,
and day_master_strength exposes no 喜用神 — so this module reports the 生克
axis + strength cross-reference and leaves scoring/用神 as a future additive
seam (a "五行力量" key can be added without changing existing keys).
"""

from lunar_python.util import LunarUtil

from apps.backend.astronomer_logic.cycles.cycle_pillars import NatalContext
from apps.backend.astronomer_logic.day_master_strength import (
    _STATE_DESCRIPTIONS,
    get_stem_element,
)

_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CONTROLS = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}

_STRONG_VERDICTS = frozenset({"极旺", "旺"})
_WEAK_VERDICTS = frozenset({"极弱", "弱"})

# Interaction types whose formation shifts elemental balance during the period
_TRIGGER_FRAME_TYPES = frozenset({"三合", "三会"})


def _dm_axis(element: str, dm_element: str) -> tuple[str, str, str]:
    """Classify `element` on the 生克 axis relative to the day master.

    Returns (关系, 十神类, 方向): e.g. ("克我", "官杀", "抑身").
    """
    if element == dm_element:
        return "同我", "比劫", "助身"
    if _GENERATES.get(element) == dm_element:
        return "生我", "印星", "助身"
    if _GENERATES.get(dm_element) == element:
        return "我生", "食伤", "泄身"
    if _CONTROLS.get(element) == dm_element:
        return "克我", "官杀", "抑身"
    return "我克", "财星", "耗身"


def _strength_verdict(direction: str, ten_god_class: str, dm_strength: str) -> str:
    """One-line cross-reference of the cycle element's push vs DM strength."""
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


def get_cycle_wu_xing(
    cycle_stem: str,
    cycle_branch: str,
    ctx: NatalContext,
    interactions: dict,
    cycle_label: str = "大运",
) -> dict:
    """
    Qualitative elemental dynamics of one cycle pillar.

    Args:
        cycle_stem/cycle_branch: the transiting pillar.
        ctx:          NatalContext (seasonal anchor, DM strength verdict).
        interactions: output of get_cycle_interactions() — its 柱位动态 feed
                      the 引动 list (frames, 合化, 开库, 干支透合).
        cycle_label:  "大运" | "流年" — used in 引动 descriptions.

    Returns:
        {"五行构成", "季节状态", "对日主", "引动"} — Chinese-keyed.
    """
    stem_element = LunarUtil.WU_XING_GAN.get(cycle_stem, "无")
    branch_element = LunarUtil.WU_XING_ZHI.get(cycle_branch, "无")
    hidden_elements = [
        LunarUtil.WU_XING_GAN.get(h, "无")
        for h in LunarUtil.ZHI_HIDE_GAN.get(cycle_branch, [])
    ]
    dm_element = get_stem_element(ctx.effective_day_stem)

    stem_rel, stem_class, stem_dir = _dm_axis(stem_element, dm_element)
    branch_rel, branch_class, branch_dir = _dm_axis(branch_element, dm_element)

    # 引动 — elemental events the cycle pillar sets off in the natal chart
    triggers: list[dict] = []
    for item in interactions.get("柱位动态", []):
        if item.get("强度") == "消融吸收":
            continue  # fully absorbed events trigger nothing
        itype = item.get("类型", "")
        if itype in _TRIGGER_FRAME_TYPES:
            elem = item.get("元素", "")
            triggers.append({
                "类型": itype,
                "元素": elem,
                "说明": f"{cycle_label}支引动{itype}{elem}局，{elem}势大增",
            })
        elif itype == "六合" and item.get("形态") == "合化":
            elem = item.get("元素", "")
            triggers.append({
                "类型": "六合合化",
                "元素": elem,
                "说明": f"{cycle_label}支六合化{elem}，{elem}气得令而旺",
            })
        elif itype == "六冲" and item.get("子类型") == "开库":
            vault = item.get("开库详情", {})
            triggers.append({
                "类型": "冲开库",
                "元素": LunarUtil.WU_XING_GAN.get(vault.get("透出藏干", ""), ""),
                "说明": item.get("备注", f"{cycle_label}冲开{vault.get('库', '')}"),
            })
        elif itype == "干支透合":
            detail = item.get("藏干详情", {})
            triggers.append({
                "类型": "干支透合",
                "元素": LunarUtil.WU_XING_GAN.get(detail.get("藏干", ""), ""),
                "说明": item.get("引动藏干", ""),
            })

    return {
        "五行构成": {
            "天干": stem_element,
            "地支本气": branch_element,
            "藏干五行": hidden_elements,
        },
        # Seasonal state vs the NATAL month — the chart's climate anchor.
        "季节状态": {
            "天干": _STATE_DESCRIPTIONS.get(ctx.seasonal.states.get(stem_element, "囚")),
            "地支本气": _STATE_DESCRIPTIONS.get(
                ctx.seasonal.states.get(branch_element, "囚")
            ),
        },
        "对日主": {
            "天干": {
                "关系": f"{stem_rel}({stem_class})",
                "方向": stem_dir,
            },
            "地支本气": {
                "关系": f"{branch_rel}({branch_class})",
                "方向": branch_dir,
            },
            # Branch qi is the period's dominant current — it carries the verdict.
            "结合日主强弱": _strength_verdict(branch_dir, branch_class, ctx.dm_strength),
        },
        "引动": triggers,
    }
