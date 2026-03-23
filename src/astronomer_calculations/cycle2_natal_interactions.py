"""
Cross-Cycle Natal Interactions
================================

Detects structural formations that span BOTH cycle pillars AND the natal chart —
formations no existing engine can see, because the 1×4 scan in cycle_interactions.py
considers only one cycle pillar at a time.

Detection scope
---------------
Two categories of formations are detected:

  Full cross-cycle (2 cycle + 1 natal branch):
      三合  — complete elemental triple combination
      三会  — complete directional triple combination (higher priority than 三合)
      三刑  — complete punishment triad (无恩之刑 / 恃势之刑 only; 自刑 excluded)

  Dual-cycle partials (only the two cycle branches; no natal required):
      半合  — 2/3 of a triple_he; carries 邀出 (missing branch)
      拱会  — 2/3 of a directional_he WITH the cardinal branch present; carries 犹出
      残会  — 2/3 of a directional_he WITHOUT the cardinal branch; carries 待会

Guard rule
----------
At least 2 of the 3 participating branches must come from the two cycle pillars.
This prevents duplication with the individual 1×4 cycle-natal scans.

Public API
----------
    get_cross_cycle_interactions(
        cycle_a_stem, cycle_a_branch,
        cycle_b_stem, cycle_b_branch,
        natal_chart, day_stem,
        cycle_a_label, cycle_b_label,
        cycle_a_xk_str, cycle_b_xk_str, natal_xk,
    )
        Returns dict under "跨运作用":
            "关系总览" — list of active interaction labels (强势主流 / 显著影响 only)
            "跨运结构" — list of resolved cross-cycle interaction dicts
            "根基"     — per-pillar 4-tier rooting (natal + cycle; compute_pillar_rooting)

Priority Architecture
---------------------
    Pass 1: Structural competition — 三会 > 三合; winner suppresses dual-cycle partials
    Pass 2: Structural → 三刑 suppression (if full structure present)
    Pass 3: Defaults — CROSS_CYCLE_BASE_STRENGTH per type

    Rule table lookup: CYCLE_PRIORITY_RULE_TABLE first, then PRIORITY_RULE_TABLE.
    Remark lookup:     CYCLE_REMARKS first, then STRENGTH_REMARKS.

Output field schema
-------------------
All full cross-cycle items carry:
    分类, 组合, 组合明细, 组合来源, 元素 (and 方位 for 三会)
    三刑 items additionally carry 状态 (from get_status)

Partial items carry:
    分类, 组合, 组合明细, 元素 (and 方位 for 拱会/残会)
    半合: 邀出 — the missing triple_he branch
    拱会: 犹出 — the cardinal is present; missing branch is the emanation target
    残会: 待会 — cardinal absent; waiting for the missing branch to complete

Section Map
-----------
    SECTION 1 — Imports & Constants
    SECTION 2 — Cross-Cycle Detection Helpers
    SECTION 3 — Priority Filter
    SECTION 4 — Xun Kong Pass
    SECTION 5 — Output Assembly
    SECTION 6 — Orchestrator  (get_cross_cycle_interactions)
"""

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Imports & Constants
# ══════════════════════════════════════════════════════════════════════════════

from src.astronomer_calculations.natal_interactions import (
    branch_elements,
    triple_he,
    cardinal_branches,
    SAN_HUI_DIRECTION,
    STRENGTH_ORDER,
    PRIORITY_RULE_TABLE,
    STRENGTH_REMARKS,
    DEFAULT_STRENGTH,
    compute_pillar_rooting,
    get_status,
    _PT_KEY_MAP,
)

from src.astronomer_calculations.cycle_interactions import (
    CYCLE_PRIORITY_RULE_TABLE,
    CYCLE_REMARKS,
    # XK constants & helpers — single source of truth from cycle_interactions
    _XK_HE_TYPES,
    _XK_XING_TYPES,
    _is_cycle_branch_void,
    _is_natal_branch_void,
    _downgrade_by_one_tier_xk,
    _build_xk_remark,
)

# ── Natal pillar names and natal_chart keys ──
_PILLAR_NAMES = ["年柱", "月柱", "日柱", "时柱"]
_NATAL_KEYS = ["year", "month", "day", "hour"]

# ── Cross-cycle tier order ──
CROSS_CYCLE_TIER_ORDER: dict[str, int] = {
    "三会": 0,
    "三合": 1,
    "拱会": 2,
    "残会": 3,
    "半合": 4,
    "无恩之刑": 5,
    "恃势之刑": 5,
}

# ── Base strength for cross-cycle formations ──
CROSS_CYCLE_BASE_STRENGTH: dict[str, str] = {
    "三合": "强势主流",
    "三会": "强势主流",
    "无恩之刑": "强势主流",
    "恃势之刑": "强势主流",
    "半合": "显著影响",  # dual-cycle only — arching toward missing branch
    "拱会": "显著影响",  # dual-cycle directional partial with cardinal
    "残会": "中等衰减",  # dual-cycle directional partial without cardinal
}


# ── Punishment universes ──
_UNGRATEFUL_UNIV = frozenset({"寅", "巳", "申"})  # 无恩之刑
_BULLYING_UNIV = frozenset({"丑", "未", "戌"})  # 恃势之刑

# ── Direction → element (for 拱会/残会 元素 field) ──
_DIRECTION_TO_ELEMENT: dict[str, str] = {
    "东": "木",
    "南": "火",
    "西": "金",
    "北": "水",
}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Cross-Cycle Detection Helpers
# ══════════════════════════════════════════════════════════════════════════════


def _natal_pillar_branches(natal_chart: dict) -> list[tuple[str, str]]:
    """
    Return [(pillar_name, branch), …] for the four natal pillars in 年→月→日→时 order.
    Pillars with an empty or missing branch are excluded.
    """
    result = []
    for key, name in zip(_NATAL_KEYS, _PILLAR_NAMES):
        pillar = natal_chart.get(key, {})
        branch = pillar.get("branch", "")
        if branch:
            result.append((name, branch))
    return result


def _detect_cross_san_he(
    a_branch: str,
    b_branch: str,
    a_lbl: str,
    b_lbl: str,
    natal_chart: dict,
) -> list[dict]:
    """
    Detect full cross-cycle 三合: cycle_a + cycle_b + 1 natal branch = complete triple_he.

    Guard: both cycle branches must belong to the same triple_he group (cycle_pair ⊆ group).
    For each matching group, scans all natal pillars for the one missing branch.
    Can emit multiple entries if the missing branch appears in more than one natal pillar.

    Output fields: 类型, 分类, 组合, 组合明细, 组合来源, 元素,
                   _struct_type ("STRUCTURAL_三合"), _natal_pillar (stripped at output).
    """
    results = []
    cycle_pair = {a_branch, b_branch}
    if len(cycle_pair) < 2:
        return results

    for elem, group in triple_he.items():
        if not cycle_pair.issubset(group):
            continue
        needed = group - cycle_pair
        for pillar_name, nb in _natal_pillar_branches(natal_chart):
            if nb in needed:
                combo = f"{a_lbl}-{b_lbl}-{pillar_name}"
                results.append(
                    {
                        "类型": "三合",
                        "分类": "跨运三合",
                        "组合": combo,
                        "组合明细": {
                            f"{a_lbl}支": a_branch,
                            f"{b_lbl}支": b_branch,
                            f"{pillar_name}支": nb,
                        },
                        "组合来源": {
                            a_lbl: a_branch,
                            b_lbl: b_branch,
                            f"命盘{pillar_name}": nb,
                        },
                        "元素": elem,
                        "_struct_type": "STRUCTURAL_三合",
                        "_natal_pillar": pillar_name,
                    }
                )
    return results


def _detect_cross_san_hui(
    a_branch: str,
    b_branch: str,
    a_lbl: str,
    b_lbl: str,
    natal_chart: dict,
) -> list[dict]:
    """
    Detect full cross-cycle 三会: cycle_a + cycle_b + 1 natal branch = complete directional_he.

    Guard: both cycle branches must belong to the same directional group (cycle_pair ⊆ group).
    For each matching direction, scans all natal pillars for the one missing branch.
    Can emit multiple entries if the missing branch appears in more than one natal pillar.

    Output fields: 类型, 分类, 组合, 组合明细, 组合来源, 方位, 元素,
                   _struct_type ("STRUCTURAL_三会"), _natal_pillar (stripped at output).
    """
    results = []
    cycle_pair = {a_branch, b_branch}
    if len(cycle_pair) < 2:
        return results

    for direction_frozenset, dir_name in SAN_HUI_DIRECTION.items():
        direction_set = set(direction_frozenset)
        if not cycle_pair.issubset(direction_set):
            continue
        needed = direction_set - cycle_pair
        elem = _DIRECTION_TO_ELEMENT.get(dir_name, "")
        for pillar_name, nb in _natal_pillar_branches(natal_chart):
            if nb in needed:
                combo = f"{a_lbl}-{b_lbl}-{pillar_name}"
                results.append(
                    {
                        "类型": "三会",
                        "分类": "跨运三会",
                        "组合": combo,
                        "组合明细": {
                            f"{a_lbl}支": a_branch,
                            f"{b_lbl}支": b_branch,
                            f"{pillar_name}支": nb,
                        },
                        "组合来源": {
                            a_lbl: a_branch,
                            b_lbl: b_branch,
                            f"命盘{pillar_name}": nb,
                        },
                        "方位": dir_name,
                        "元素": elem,
                        "_struct_type": "STRUCTURAL_三会",
                        "_natal_pillar": pillar_name,
                    }
                )
    return results


def _detect_cross_san_xing(
    a_branch: str,
    b_branch: str,
    a_lbl: str,
    b_lbl: str,
    natal_chart: dict,
) -> list[dict]:
    """
    Detect full cross-cycle 三刑 (无恩之刑 / 恃势之刑).

    Covers the two three-branch punishment universes:
        无恩之刑: {寅, 巳, 申}
        恃势之刑: {丑, 未, 戌}
    (自刑 is a single-branch self-punishment — cannot span two cycle pillars.)

    Guard: both cycle branches must belong to the same punishment universe.
    Scans natal pillars for the one missing branch to complete the triad.

    Output fields: 类型, 分类, 组合, 组合明细, 组合来源, 状态 (from get_status),
                   _natal_pillar (stripped at output).
    """
    results = []
    cycle_pair = {a_branch, b_branch}
    if len(cycle_pair) < 2:
        return results

    for univ, xing_type in (
        (_UNGRATEFUL_UNIV, "无恩之刑"),
        (_BULLYING_UNIV, "恃势之刑"),
    ):
        if not cycle_pair.issubset(univ):
            continue
        needed = univ - cycle_pair
        for pillar_name, nb in _natal_pillar_branches(natal_chart):
            if nb in needed:
                combo = f"{a_lbl}-{b_lbl}-{pillar_name}"
                results.append(
                    {
                        "类型": xing_type,
                        "分类": f"跨运{xing_type}",
                        "组合": combo,
                        "组合明细": {
                            f"{a_lbl}支": a_branch,
                            f"{b_lbl}支": b_branch,
                            f"{pillar_name}支": nb,
                        },
                        "组合来源": {
                            a_lbl: a_branch,
                            b_lbl: b_branch,
                            f"命盘{pillar_name}": nb,
                        },
                        "状态": get_status(
                            "三刑",
                            {
                                "punishment_type": _PT_KEY_MAP.get(xing_type, "ungrateful"),
                                "is_full": True,
                                "is_adjacent": True,
                            },
                        ),
                        "_natal_pillar": pillar_name,
                    }
                )
    return results


def _detect_cross_ban_he(
    a_branch: str,
    b_branch: str,
    a_lbl: str,
    b_lbl: str,
) -> list[dict]:
    """
    Detect dual-cycle partial formations (both cycle branches only; no natal required).

    半合: the two cycle branches form 2/3 of a triple_he group.
         carries 邀出 — the missing branch being invited to complete the triple.

    拱会 / 残会: the two cycle branches form 2/3 of a directional_he group.
         拱会: one of the cycle branches IS the cardinal branch (东寅/南午/西申/北子).
               carries 犹出 — the cardinal is present; missing branch is the emanation target.
         残会: neither cycle branch is the cardinal.
               carries 待会 — cardinal absent; waiting for the missing branch.

    At most one 半合 and one 拱会/残会 can be emitted per call (break after first match).
    """
    results = []
    cycle_pair = {a_branch, b_branch}
    if len(cycle_pair) < 2:
        return results

    combo = f"{a_lbl}-{b_lbl}"
    detail = {f"{a_lbl}支": a_branch, f"{b_lbl}支": b_branch}

    # ── 半合 ──
    for elem, group in triple_he.items():
        if cycle_pair.issubset(group):
            missing = (group - cycle_pair).pop()
            results.append(
                {
                    "类型": "半合",
                    "分类": "岁运半合",
                    "组合": combo,
                    "组合明细": dict(detail),
                    "元素": elem,
                    "邀出": missing,
                }
            )
            break

    # ── 拱会 / 残会 ──
    for direction_frozenset, dir_name in SAN_HUI_DIRECTION.items():
        direction_set = set(direction_frozenset)
        if not cycle_pair.issubset(direction_set):
            continue
        missing = (direction_set - cycle_pair).pop()
        elem = _DIRECTION_TO_ELEMENT.get(dir_name, "")
        # cardinal_branches is keyed by element (木/火/金/水) → cardinal branch
        cardinal = cardinal_branches.get(elem, "")
        # 拱会 if cardinal branch is present in the cycle pair; 残会 otherwise
        itype = "拱会" if (cardinal and cardinal in cycle_pair) else "残会"
        entry: dict = {
            "类型": itype,
            "分类": f"岁运{itype}",
            "组合": combo,
            "组合明细": dict(detail),
            "方位": dir_name,
            "元素": elem,
        }
        if itype == "拱会":
            entry["犹出"] = missing   # cardinal present → emanating toward missing branch
        else:
            entry["待会"] = missing   # cardinal absent → waiting for missing branch
        results.append(entry)
        break

    return results


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Priority Filter
# ══════════════════════════════════════════════════════════════════════════════


def _lookup_rule(lock_type: str, itype: str) -> str | None:
    """Check CYCLE_PRIORITY_RULE_TABLE first, fall back to PRIORITY_RULE_TABLE.
    Returns target 强度 string or None if no rule applies."""
    strength = CYCLE_PRIORITY_RULE_TABLE.get((lock_type, itype))
    if strength is None:
        strength = PRIORITY_RULE_TABLE.get((lock_type, itype))
    return strength


def _lookup_remark(lock_type: str, itype: str, **fmt_kw) -> str:
    """Check CYCLE_REMARKS first, fall back to STRENGTH_REMARKS.
    Formats with provided kwargs; returns empty string if no remark."""
    template = CYCLE_REMARKS.get((lock_type, itype)) or STRENGTH_REMARKS.get(
        (lock_type, itype), ""
    )
    if template and fmt_kw:
        try:
            return template.format(**fmt_kw)
        except (KeyError, IndexError):
            pass
    return template


def _apply_downgrade(item: dict, lock_type: str, **fmt_kw) -> bool:
    """Apply a priority-rule downgrade to item. Only downgrades; never upgrades.
    Writes the first causal remark (subsequent calls are no-ops for 备注).
    Returns True if a rule was matched in either table."""
    itype = item.get("类型", "")
    strength = _lookup_rule(lock_type, itype)
    if strength is None:
        return False
    current_rank = STRENGTH_ORDER.get(item.get("强度", "强势主流"), 0)
    new_rank = STRENGTH_ORDER.get(strength, 0)
    if new_rank > current_rank:
        item["强度"] = strength
    remark = _lookup_remark(lock_type, itype, **fmt_kw)
    if remark and not item.get("备注"):
        item["备注"] = remark
    return True


def _get_structural_winner_lock(full_structures: list[dict]) -> str | None:
    """
    Return the winning structural lock key based on which full structure types are present.
        "STRUCTURAL_三会" if any 三会 present  (三会 beats 三合)
        "STRUCTURAL_三合" if any 三合 present and no 三会
        None             if no full structure present
    """
    if any(it.get("类型") == "三会" for it in full_structures):
        return "STRUCTURAL_三会"
    if any(it.get("类型") == "三合" for it in full_structures):
        return "STRUCTURAL_三合"
    return None


def _cross_pass_structural(items: list[dict]) -> None:
    """
    Pass 1: Structural competition — full structures suppress partials.

    三会 vs 三合: for each 三会 item, downgrades all 三合 items via STRUCTURAL_三会
    rule (→ 消融吸收). The full structural winner then suppresses dual-cycle partials
    (半合/拱会/残会) via the same rule table.

    Winner priority: 三会 > 三合. Uses _get_structural_winner_lock() for the
    partial-suppression lock key to avoid duplicating that logic.
    """
    full_structures = [it for it in items if it.get("类型") in ("三合", "三会")]
    partial_items = [it for it in items if it.get("类型") in ("半合", "拱会", "残会")]

    # 三会 vs 三合 competition
    for san_hui in [it for it in full_structures if it.get("类型") == "三会"]:
        struct_type = san_hui.get("_struct_type", "STRUCTURAL_三会")
        for san_he in [it for it in full_structures if it.get("类型") == "三合"]:
            _apply_downgrade(san_he, struct_type)

    winner_lock = _get_structural_winner_lock(full_structures)
    if winner_lock is not None:
        for item in partial_items:
            _apply_downgrade(item, winner_lock)


def _cross_pass_xing(items: list[dict]) -> None:
    """
    Pass 2: Full structural → 三刑 suppression.

    If any full structure (三会 or 三合) and any 三刑 (无恩之刑 / 恃势之刑) are both
    present, the structural winner downgrades all 三刑 items via the rule table.
    Skipped early if either group is empty.
    """
    full_structures = [it for it in items if it.get("类型") in ("三合", "三会")]
    xing_items = [it for it in items if it.get("类型") in ("无恩之刑", "恃势之刑")]
    if not full_structures or not xing_items:
        return

    winner_lock = _get_structural_winner_lock(full_structures)
    if winner_lock is not None:
        for item in xing_items:
            _apply_downgrade(item, winner_lock)


def _cross_pass_defaults(items: list[dict]) -> None:
    """
    Pass 3: Assign default 强度 to any item not yet strength-resolved.

    CROSS_CYCLE_BASE_STRENGTH is checked first; falls back to DEFAULT_STRENGTH
    [(itype, True)] for unknown types. Items already carrying a 强度 are skipped.
    """
    for item in items:
        if item.get("强度"):
            continue
        itype = item.get("类型", "")
        item["强度"] = CROSS_CYCLE_BASE_STRENGTH.get(
            itype,
            DEFAULT_STRENGTH.get((itype, True), "强势主流"),
        )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Xun Kong Pass
# ══════════════════════════════════════════════════════════════════════════════


def _cross_xun_kong_pass(
    items: list[dict],
    a_lbl: str,
    b_lbl: str,
    a_xk_str: str | None,
    b_xk_str: str | None,
    natal_xk: dict | None,
) -> None:
    """
    Post-filter: downgrade cross-cycle interactions involving void (旬空) branches.

    Each branch is checked against its own void source:
        Cycle A branch — checked against a_xk_str via _is_cycle_branch_void
        Cycle B branch — checked against b_xk_str via _is_cycle_branch_void
        Natal branches — checked against natal_xk via _is_natal_branch_void,
                         identified by the "{pillar_name}支" key pattern in 组合明细
                         (e.g. "月柱支"); validated against _PILLAR_NAMES guard.

    Void branch effect by type:
        合 types (三合/三会/半合/拱会/残会): one-tier downgrade
        刑 types (无恩之刑/恃势之刑):       one-tier downgrade

    旬空涉及 field is set on affected items listing the void label(s).
    """
    a_key = f"{a_lbl}支"
    b_key = f"{b_lbl}支"

    for item in items:
        itype = item.get("类型", "")
        detail = item.get("组合明细", {})
        void_parts: list[str] = []
        total_branch_count = 0

        for key, val in detail.items():
            if not isinstance(val, str) or len(val) != 1:
                continue
            if val not in branch_elements:
                continue

            total_branch_count += 1

            if key == a_key:
                if a_xk_str and _is_cycle_branch_void(val, a_xk_str):
                    void_parts.append(a_lbl)
            elif key == b_key:
                if b_xk_str and _is_cycle_branch_void(val, b_xk_str):
                    void_parts.append(b_lbl)
            elif natal_xk and key.endswith("支"):
                pillar_name = key[:-1]  # "月柱支" → "月柱"
                if pillar_name in _PILLAR_NAMES:
                    if _is_natal_branch_void(val, pillar_name, natal_xk):
                        void_parts.append(pillar_name)

        if not total_branch_count or not void_parts:
            continue

        if itype in _XK_HE_TYPES:
            _downgrade_by_one_tier_xk(item, _build_xk_remark(void_parts, "合_single"))
            item["旬空涉及"] = void_parts
        elif itype in _XK_XING_TYPES:
            _downgrade_by_one_tier_xk(item, _build_xk_remark(void_parts, "刑_single"))
            item["旬空涉及"] = void_parts


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Output Assembly
# ══════════════════════════════════════════════════════════════════════════════

_STRIP_KEYS = {"_struct_type", "_natal_pillar", "_synthetic"}


def _build_cross_output(items: list[dict]) -> dict:
    """
    Sort by tier, build 关系总览, strip internal keys, assemble output dict.

    Sorting: CROSS_CYCLE_TIER_ORDER; unknown types sort last (key 99).
    Summary: includes only 强势主流 or 显著影响 items; de-duplicated by label string.
    Stripped keys: _struct_type, _natal_pillar, _synthetic (internal sentinel fields).
    """
    items.sort(key=lambda it: CROSS_CYCLE_TIER_ORDER.get(it.get("类型", ""), 99))

    summary: list[str] = []
    for item in items:
        strength = item.get("强度", "")
        if strength in ("强势主流", "显著影响"):
            label = f"{item.get('类型', '')}（{strength}）"
            if label not in summary:
                summary.append(label)

    for item in items:
        for k in _STRIP_KEYS:
            item.pop(k, None)

    return {
        "跨运作用": {
            "关系总览": summary,
            "跨运结构": items,
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Orchestrator
# ══════════════════════════════════════════════════════════════════════════════


def get_cross_cycle_interactions(
    cycle_a_stem: str,
    cycle_a_branch: str,
    cycle_b_stem: str,
    cycle_b_branch: str,
    natal_chart: dict,
    day_stem: str | None = None,
    cycle_a_label: str = "大运",
    cycle_b_label: str = "流年",
    cycle_a_xk_str: str | None = None,
    cycle_b_xk_str: str | None = None,
    natal_xk: dict | None = None,
) -> dict:
    """
    Detect cross-cycle structural formations spanning natal chart + two cycle pillars.

    Only detects formations where at least 2 of 3 participating branches come from
    the two cycle pillars — prevents duplication with individual 1×4 scans.

    Processing pipeline:
        Step 1 — Detection (四 helpers, in order):
                   _detect_cross_san_hui  (三会 first — higher priority)
                   _detect_cross_san_he   (三合)
                   _detect_cross_san_xing (三刑)
                   _detect_cross_ban_he   (半合 / 拱会 / 残会 — cycle-only partials)
        Step 2 — Priority filter:
                   Pass 1: structural competition (三会 > 三合 > partials)
                   Pass 2: structural → 三刑 suppression
                   Pass 3: CROSS_CYCLE_BASE_STRENGTH defaults
        Step 3 — Xun Kong pass (skipped if no xk sources provided)
        Step 4 — Output assembly: sort, build summary, append 根基

    If no formations are detected, returns the empty-list output with 根基 only.

    Args:
        cycle_a_stem / cycle_a_branch: First cycle pillar stem and branch characters.
        cycle_b_stem / cycle_b_branch: Second cycle pillar stem and branch characters.
        natal_chart: {"year": {"stem": str, "branch": str}, "month":…, "day":…, "hour":…}
        day_stem: Birth Day Stem — reserved for future 十神 annotation; unused currently.
        cycle_a_label: Display label for the first cycle (default "大运").
        cycle_b_label: Display label for the second cycle (default "流年").
        cycle_a_xk_str: Xun Kong string for cycle A from getXunKong() (e.g. "午未").
                        If None, cycle A's branch is not void-checked.
        cycle_b_xk_str: Xun Kong string for cycle B from getXunKong().
                        If None, cycle B's branch is not void-checked.
        natal_xk: Natal 旬空 dict from get_xun_kong(). If None, natal branches
                  are not void-checked.

    Returns:
        dict: {"跨运作用": {"关系总览": [...], "跨运结构": [...], "根基": {...}}}
              根基 covers all 6 pillars (4 natal + 2 cycle) via compute_pillar_rooting.
    """
    _ = (cycle_a_stem, cycle_b_stem, day_stem)  # reserved for future 十神 use
    a_b, b_b = cycle_a_branch, cycle_b_branch
    a_lbl, b_lbl = cycle_a_label, cycle_b_label

    # ── Step 1: Detection ────────────────────────────────────────────────────
    all_items: list[dict] = []

    # Full cross-cycle structures (2 cycle + 1 natal) — 三会 detected first (higher priority)
    all_items.extend(_detect_cross_san_hui(a_b, b_b, a_lbl, b_lbl, natal_chart))
    all_items.extend(_detect_cross_san_he(a_b, b_b, a_lbl, b_lbl, natal_chart))
    all_items.extend(_detect_cross_san_xing(a_b, b_b, a_lbl, b_lbl, natal_chart))

    # Dual-cycle partials (no natal completion required)
    all_items.extend(_detect_cross_ban_he(a_b, b_b, a_lbl, b_lbl))

    natal_gans = [natal_chart[k]["stem"] for k in _NATAL_KEYS]
    natal_zhis = [natal_chart[k]["branch"] for k in _NATAL_KEYS]

    if not all_items:
        result = _build_cross_output([])
        result["跨运作用"]["根基"] = compute_pillar_rooting(
            natal_gans + [cycle_a_stem, cycle_b_stem],
            natal_zhis + [a_b, b_b],
            _PILLAR_NAMES + [a_lbl + "柱", b_lbl + "柱"],
        )
        return result

    # ── Step 2: Priority Filter ──────────────────────────────────────────────
    _cross_pass_structural(all_items)
    _cross_pass_xing(all_items)
    _cross_pass_defaults(all_items)

    # ── Step 3: Xun Kong Pass ────────────────────────────────────────────────
    if cycle_a_xk_str or cycle_b_xk_str or natal_xk:
        _cross_xun_kong_pass(
            all_items,
            a_lbl,
            b_lbl,
            cycle_a_xk_str,
            cycle_b_xk_str,
            natal_xk,
        )

    # ── Step 4: Output Assembly ──────────────────────────────────────────────
    result = _build_cross_output(all_items)
    result["跨运作用"]["根基"] = compute_pillar_rooting(
        natal_gans + [cycle_a_stem, cycle_b_stem],
        natal_zhis + [a_b, b_b],
        _PILLAR_NAMES + [a_lbl + "柱", b_lbl + "柱"],
    )
    return result
