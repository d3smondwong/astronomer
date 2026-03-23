"""
Cycle-to-Cycle Pairwise Interactions
======================================

Detects and priority-resolves all interactions between two external cycle pillars
(e.g., 大运 vs 流年, 流年 vs 流月, 大运 vs 流月). Generic: only labels differ;
the same engine handles any cycle pair.

Public API
----------
    get_pairwise_cycle_interactions(
        cycle_a_stem, cycle_a_branch,
        cycle_b_stem, cycle_b_branch,
        day_stem,
        cycle_a_label, cycle_b_label,
        cycle_a_xk_str, cycle_b_xk_str,
    )
        Returns dict under "岁运作用":
            "关系总览" — list of active interaction labels (强势主流 / 显著影响 only)
            "互动列表" — flat list of resolved interaction dicts
            "根基"     — per-pillar 4-tier rooting summary (from compute_pillar_rooting)

Priority Architecture
---------------------
Reuses CYCLE_PRIORITY_RULE_TABLE (checked first) then PRIORITY_RULE_TABLE (fallback).
Downgrades only — never upgrades via the rule table.

    Pre-pass  : 反吟 / 伏吟 absorb implied sub-interactions (消融吸收)
    Stem lock : 天干合 > 天干克 > 天干冲   → losers downgraded via rule table
    Branch lock: 六合 > 六冲/开库          → losers downgraded via rule table
    Cross-actor: stem/branch locks → 干支透合 suppressed (贪合)
    Kaiku pass: 开库 resolved (free / fully_trapped) → 强度 + 库藏释放 populated
    Defaults  : remaining items get PAIRWISE_BASE_STRENGTH (all treated as adjacent)
    Pass S    : _pass_stem_rooting modulates 天干合/克/冲 by 通根 tier

Remark lookup: CYCLE_REMARKS first, then STRENGTH_REMARKS.

Stem Interaction Field Schema
------------------------------
All 天干合/克/冲 items carry:
    - 紧贴: True  (all pairwise interactions are adjacent — no distance penalty)
    - 主动方: "相互" for 天干合/冲; controlling pillar label for 天干克
    - 根基: {a_lbl: tier_a, b_lbl: tier_b}  (4-tier per stem)

六害/六破 主动方 convention: a_lbl (the pillar whose branch appears in the map key
generates the force; b_lbl is the receiving side).

Interaction Tier Classification
---------------------------------
    第一梯队 (纲领层): 反吟, 伏吟, 六冲, 开库, 六合
    第二梯队 (气势层): 半合, 比和, 天干合, 天干克, 天干冲
    第三梯队 (琐碎层): 无恩之刑, 恃势之刑, 无礼之刑, 自刑, 六害, 六破, 暗合, 干支透合

Section Map
-----------
    SECTION 1 — Imports & Pairwise Constants
    SECTION 2 — Detection Helpers
    SECTION 3 — Priority Filter
    SECTION 4 — Xun Kong Pass
    SECTION 5 — Output Assembly
    SECTION 6 — Orchestrator  (get_pairwise_cycle_interactions)
"""

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Imports & Pairwise Constants
# ══════════════════════════════════════════════════════════════════════════════

from lunar_python.util import LunarUtil

from src.astronomer_calculations.natal_interactions import (
    # Branch maps
    branch_elements,
    six_he_map,
    six_he_element_map,
    clash_map,
    harm_map,
    break_map,
    hidden_stem_he,
    triple_he,
    # Stem maps
    stem_combines,
    stem_clashes,
    stem_controls,
    _STEM_COMBINE_ELEMENT,
    # Helper functions
    get_status,
    is_valid_punishment,
    is_valid_peer_combination,
    _get_shi_shen_for_stem_pair,
    # Priority & strength tables
    STRENGTH_ORDER,
    PRIORITY_RULE_TABLE,
    STRENGTH_REMARKS,
    DEFAULT_STRENGTH,
    compute_pillar_rooting,
    get_stem_root_tier,
    stem_elements,
    _pass_stem_rooting,
    _PT_KEY_MAP,
)

from src.astronomer_calculations.cycle_interactions import (
    # Cycle-specific priority & remark tables
    CYCLE_PRIORITY_RULE_TABLE,
    CYCLE_REMARKS,
    # 开库 constants
    TOMB_HIDDEN_STEMS,
    _TOMB_BRANCHES,
    KAIKU_STRENGTH,
    KAIKU_RELEASE_STRENGTH,
    KAIKU_RELEASE_NATURE,
    # 墓库境况 helpers
    _determine_lib_type,
    _determine_kai_ku_influence,
    _generate_kai_ku_remark,
    # XK constants — all defined in cycle_interactions (single source of truth)
    _XK_HE_TYPES,
    _XK_CHONG_TYPES,
    _XK_XING_TYPES,
    _XK_HAI_PO_TYPES,
    _XK_MISC_TYPES,
    _XK_STEM_ONLY,
    # XK helpers — use cycle_interactions versions so _XK_REMARKS is resolved
    # from the same module as the constants, eliminating any cross-module drift
    _check_branch_rooting,
    _is_cycle_branch_void,
    _downgrade_by_one_tier_xk,
    _build_xk_remark,
    _append_remark_xk,
)

# ── Pairwise tier order (subset: excludes multi-branch types 三会/三合/共拱/拱会/残会) ──
PAIRWISE_TIER_ORDER: dict[str, int] = {
    "反吟": 0,
    "伏吟": 1,
    "六冲": 2,
    "开库": 2,
    "六合": 3,
    "半合": 4,
    "比和": 5,
    "天干合": 6,
    "天干克": 7,
    "天干冲": 8,
    "无恩之刑": 9,
    "恃势之刑": 9,
    "无礼之刑": 9,
    "自刑": 10,
    "六害": 11,
    "六破": 12,
    "暗合": 13,
    "干支透合": 13,
}

# ── Base strength for pairwise (no distance semantics → treat all as adjacent) ──
PAIRWISE_BASE_STRENGTH: dict[str, str] = {
    "反吟": "强势主流",
    "伏吟": "强势主流",
    "六冲": "强势主流",
    "开库": "强势主流",  # overridden by KAIKU_STRENGTH after trapped_state resolved
    "六合": "强势主流",
    "半合": "强势主流",  # no distance penalty → adjacent strength
    "比和": "显著影响",
    "天干合": "强势主流",
    "天干克": "强势主流",
    "天干冲": "强势主流",
    "无恩之刑": "强势主流",
    "恃势之刑": "强势主流",
    "无礼之刑": "强势主流",
    "自刑": "强势主流",
    "六害": "显著影响",
    "六破": "显著影响",
    "暗合": "显著影响",
    "干支透合": "显著影响",
}


_STEM_TYPES = frozenset({"天干合", "天干克", "天干冲"})

# Sentinel for unresolved 开库 state
_PENDING = "pending"

_HIDDEN_LABELS: tuple[str, ...] = ("本气", "中气", "余气")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Detection Helpers
# ══════════════════════════════════════════════════════════════════════════════


def _detect_pairwise_fanyin_fuyin(
    a_stem: str,
    a_branch: str,
    b_stem: str,
    b_branch: str,
    a_lbl: str,
    b_lbl: str,
) -> list[dict]:
    """
    Detect 反吟 (reversal) and 伏吟 (stagnation) between two cycle pillars.

    反吟: stem clash AND branch clash simultaneously (干支皆反). Both pillars are
         completely opposed — stem clashes via stem_clashes, branch via clash_map.
    伏吟: exact stem AND branch match (干支皆同). Both pillars are identical —
         total stagnation / repetition energy.

    Both are 主动方: "相互" (mutual). The pre-pass later uses these flags to absorb
    implied sub-interactions (反吟 → 六冲/天干冲 消融吸收; 伏吟 → 比和/干支透合).
    """
    results = []
    combo = f"{a_lbl}-{b_lbl}"

    # 反吟: stem clash AND branch clash
    if stem_clashes.get(a_stem) == b_stem and clash_map.get(a_branch) == b_branch:
        results.append(
            {
                "类型": "反吟",
                "组合": combo,
                "组合明细": {
                    f"{a_lbl}干": a_stem,
                    f"{a_lbl}支": a_branch,
                    f"{b_lbl}干": b_stem,
                    f"{b_lbl}支": b_branch,
                },
                "状态": "干支皆反",
                "主动方": "相互",
            }
        )

    # 伏吟: exact match (stem AND branch identical)
    if a_stem == b_stem and a_branch == b_branch:
        results.append(
            {
                "类型": "伏吟",
                "组合": combo,
                "组合明细": {
                    f"{a_lbl}干": a_stem,
                    f"{a_lbl}支": a_branch,
                    f"{b_lbl}干": b_stem,
                    f"{b_lbl}支": b_branch,
                },
                "状态": "干支皆同",
                "主动方": "相互",
            }
        )

    return results


def _detect_pairwise_branch(
    a_stem: str,
    a_branch: str,
    b_stem: str,
    b_branch: str,
    a_lbl: str,
    b_lbl: str,
    day_stem: str,
    tong_gen: str = "中根",
) -> list[dict]:
    """
    Detect all branch interactions between two cycle pillars.

    Interaction types detected (in check order):
        六合  — bilateral bond; 主动方: "相互"; carries 元素
        六冲/开库 — clash; uses SEPARATE if-checks (not elif) so that dual-tomb clashes
                   (辰-戌, 丑-未) generate TWO 开库 entries simultaneously. Pure 六冲
                   fallback fires only when neither branch is a tomb (辰戌丑未).
        六害  — 主动方: a_lbl  (a_branch is the harm-generating side per harm_map key)
        六破  — 主动方: a_lbl  (a_branch is the break-generating side per break_map key)
        三刑  — skipped when a_stem==b_stem AND a_branch==b_branch (伏吟 guard)
        暗合  — hidden stem harmony; 主动方: b_lbl (b_branch contains the hidden stem)
        比和  — peer element resonance; carries 元素
        半合  — 2/3 of a triple_he group; carries 元素 and 邀出 (missing branch)

    开库 field schema:
        根基强度 / 根基说明 — rooting of the KEY pillar's stem in its own branch
                             (_check_branch_rooting(key_stem, key_branch))
        钥匙受困 / 释放性质 / 受阻 — resolved later by _pairwise_pass_kaiku
    """
    results = []
    combo = f"{a_lbl}-{b_lbl}"
    detail = {f"{a_lbl}支": a_branch, f"{b_lbl}支": b_branch}

    # ── 六合 ──
    if six_he_map.get(a_branch) == b_branch:
        sorted_pair = sorted([a_branch, b_branch])
        pair: tuple[str, str] = (sorted_pair[0], sorted_pair[1])
        elem = six_he_element_map.get(pair, {}).get("primary", "")
        results.append(
            {
                "类型": "六合",
                "组合": combo,
                "组合明细": dict(detail),
                "元素": elem,
                "主动方": "相互",
                "状态": get_status("六合", {"key": "adjacent"}),
            }
        )

    # ── 六冲 / 开库 ──
    # Use separate if checks (not if/elif) so that dual-tomb clashes (辰-戌, 丑-未)
    # generate TWO 开库 entries — one for each tomb opening simultaneously.
    if clash_map.get(a_branch) == b_branch:
        kaiku_detected = False

        if b_branch in _TOMB_BRANCHES:
            # a_branch is the key opening b_branch's tomb
            kaiku_detected = True
            rooting = _check_branch_rooting(a_stem, a_branch)
            hidden_data = TOMB_HIDDEN_STEMS[b_branch]
            ku_cang = []
            for stem, ceng in hidden_data:
                entry: dict = {
                    "天干": stem,
                    "十神": _get_shi_shen_for_stem_pair(day_stem, stem),
                    "层次": ceng,
                    "释放性质": _PENDING,
                    "受阻": _PENDING,
                }
                combine_target = stem_combines.get(stem)
                if combine_target == a_stem:
                    entry["干合"] = {
                        "合化方": a_stem,
                        "来源": f"{a_lbl}干",
                        "合化五行": _STEM_COMBINE_ELEMENT.get(stem, ""),
                    }
                elif combine_target == b_stem:
                    entry["干合"] = {
                        "合化方": b_stem,
                        "来源": f"{b_lbl}干",
                        "合化五行": _STEM_COMBINE_ELEMENT.get(stem, ""),
                    }
                ku_cang.append(entry)
            _released_gods_b = [e["十神"] for e in ku_cang]
            _day_elem_b = stem_elements.get(day_stem, "")
            _lib_type_b = _determine_lib_type(b_branch, _day_elem_b)
            results.append(
                {
                    "类型": "开库",
                    "组合": combo,
                    "组合明细": dict(detail),
                    "主动方": a_lbl,
                    "库体": {
                        "库支": b_branch,
                        "钥匙": a_branch,
                        "钥匙受困": _PENDING,
                    },
                    "库藏释放": ku_cang,
                    "根基强度": rooting["strength"],
                    "根基说明": rooting["interpretation"],
                    "墓库境况": {
                        "类型": _lib_type_b,
                        "影响": _determine_kai_ku_influence(
                            tong_gen, _lib_type_b, _released_gods_b
                        ),
                        "说明": _generate_kai_ku_remark(
                            tong_gen, _lib_type_b, _released_gods_b
                        ),
                    },
                }
            )

        if a_branch in _TOMB_BRANCHES:
            # b_branch is the key opening a_branch's tomb
            kaiku_detected = True
            rooting = _check_branch_rooting(b_stem, b_branch)
            hidden_data = TOMB_HIDDEN_STEMS[a_branch]
            ku_cang = []
            for stem, ceng in hidden_data:
                entry = {
                    "天干": stem,
                    "十神": _get_shi_shen_for_stem_pair(day_stem, stem),
                    "层次": ceng,
                    "释放性质": _PENDING,
                    "受阻": _PENDING,
                }
                combine_target = stem_combines.get(stem)
                if combine_target == a_stem:
                    entry["干合"] = {
                        "合化方": a_stem,
                        "来源": f"{a_lbl}干",
                        "合化五行": _STEM_COMBINE_ELEMENT.get(stem, ""),
                    }
                elif combine_target == b_stem:
                    entry["干合"] = {
                        "合化方": b_stem,
                        "来源": f"{b_lbl}干",
                        "合化五行": _STEM_COMBINE_ELEMENT.get(stem, ""),
                    }
                ku_cang.append(entry)
            _released_gods_a = [e["十神"] for e in ku_cang]
            _day_elem_a = stem_elements.get(day_stem, "")
            _lib_type_a = _determine_lib_type(a_branch, _day_elem_a)
            results.append(
                {
                    "类型": "开库",
                    "组合": combo,
                    "组合明细": dict(detail),
                    "主动方": b_lbl,
                    "库体": {
                        "库支": a_branch,
                        "钥匙": b_branch,
                        "钥匙受困": _PENDING,
                    },
                    "库藏释放": ku_cang,
                    "根基强度": rooting["strength"],
                    "根基说明": rooting["interpretation"],
                    "墓库境况": {
                        "类型": _lib_type_a,
                        "影响": _determine_kai_ku_influence(
                            tong_gen, _lib_type_a, _released_gods_a
                        ),
                        "说明": _generate_kai_ku_remark(
                            tong_gen, _lib_type_a, _released_gods_a
                        ),
                    },
                }
            )

        if not kaiku_detected:
            results.append(
                {
                    "类型": "六冲",
                    "组合": combo,
                    "组合明细": dict(detail),
                    "主动方": "相互",
                    "状态": get_status("六冲", {"key": "adjacent"}),
                }
            )

    # ── 六害 ──
    if harm_map.get(a_branch) == b_branch:
        results.append(
            {
                "类型": "六害",
                "组合": combo,
                "组合明细": dict(detail),
                "主动方": a_lbl,
                "状态": get_status("六害", {"key": "adjacent"}),
            }
        )

    # ── 六破 ──
    if break_map.get(a_branch) == b_branch:
        results.append(
            {
                "类型": "六破",
                "组合": combo,
                "组合明细": dict(detail),
                "主动方": a_lbl,
                "状态": get_status("六破", {"key": "adjacent"}),
            }
        )

    # ── 三刑 (skip exact 伏吟) ──
    is_fuyin = a_stem == b_stem and a_branch == b_branch
    if not is_fuyin:
        punishment = is_valid_punishment(a_branch, b_branch)
        if punishment:
            pt = punishment["type"]
            results.append(
                {
                    "类型": pt,
                    "组合": combo,
                    "组合明细": dict(detail),
                    "主动方": "相互",
                    "状态": get_status(
                        "三刑",
                        {
                            "punishment_type": _PT_KEY_MAP.get(pt, "unknown"),
                            "is_full": punishment["is_full"],
                            "is_adjacent": True,
                        },
                    ),
                }
            )

    # ── 暗合 ──
    if b_branch in hidden_stem_he.get(a_branch, set()):
        results.append(
            {
                "类型": "暗合",
                "组合": combo,
                "组合明细": dict(detail),
                "主动方": b_lbl,
                "状态": get_status("暗合"),
            }
        )

    # ── 比和 ──
    peer = is_valid_peer_combination(a_branch, b_branch)
    if peer:
        results.append(
            {
                "类型": "比和",
                "组合": combo,
                "组合明细": dict(detail),
                "元素": peer["element"],
                "主动方": b_lbl,
                "状态": get_status("比和", {"key": "adjacent"}),
            }
        )

    # ── 半合: two branches form 2/3 of a triple_he group ──
    branch_pair = {a_branch, b_branch}
    if len(branch_pair) == 2:  # guard against self-pair
        for elem, group in triple_he.items():
            if branch_pair.issubset(group):
                missing = (group - branch_pair).pop()
                results.append(
                    {
                        "类型": "半合",
                        "组合": combo,
                        "组合明细": dict(detail),
                        "元素": elem,
                        "邀出": missing,
                        "主动方": "相互",
                        "状态": "拱",
                    }
                )
                break

    return results


def _detect_pairwise_stem(
    a_stem: str,
    a_branch: str,
    b_stem: str,
    b_branch: str,
    a_lbl: str,
    b_lbl: str,
) -> list[dict]:
    """
    Detect stem interactions: 天干合, 天干克 (bidirectional), 天干冲.

    Rooting is computed once for both stems against the two active branches
    [a_branch, b_branch] via get_stem_root_tier(), producing root_detail:
        {a_lbl: tier_a, b_lbl: tier_b}  — 4-tier (深根/中根/浅根/无根)

    Output field schema (all three types):
        紧贴: True        — all pairwise interactions are adjacent; no distance penalty
        主动方: "相互"    — for 天干合 and 天干冲 (mutual)
                a_lbl or b_lbl — for 天干克 (controlling side)
        根基: root_detail — 4-tier rooting dict; consumed by _pass_stem_rooting (Pass S)
        克向              — 天干克 only: directional string (e.g., "大运克流年")
    """
    results = []
    combo = f"{a_lbl}-{b_lbl}"
    detail_stem = {f"{a_lbl}干": a_stem, f"{b_lbl}干": b_stem}

    all_zhis = [a_branch, b_branch]
    tier_a = get_stem_root_tier(stem_elements.get(a_stem, ""), all_zhis)
    tier_b = get_stem_root_tier(stem_elements.get(b_stem, ""), all_zhis)
    root_detail = {a_lbl: tier_a, b_lbl: tier_b}

    # ── 天干合 ──
    if stem_combines.get(a_stem) == b_stem:
        results.append(
            {
                "类型": "天干合",
                "组合": combo,
                "组合明细": dict(detail_stem),
                "元素": _STEM_COMBINE_ELEMENT.get(a_stem, ""),
                "主动方": "相互",
                "状态": get_status("天干合"),
                "紧贴": True,
                "根基": root_detail,
            }
        )

    # ── 天干冲 ──
    if stem_clashes.get(a_stem) == b_stem:
        results.append(
            {
                "类型": "天干冲",
                "组合": combo,
                "组合明细": dict(detail_stem),
                "主动方": "相互",
                "状态": get_status("天干冲", {"key": "adjacent"}),
                "紧贴": True,
                "根基": root_detail,
            }
        )

    # ── 天干克 (bidirectional; controlling side is the active party) ──
    ke_a_to_b = (a_stem, b_stem) in stem_controls
    ke_b_to_a = (b_stem, a_stem) in stem_controls
    if ke_a_to_b or ke_b_to_a:
        active = a_lbl if ke_a_to_b else b_lbl
        ke_dir = f"{a_lbl}克{b_lbl}" if ke_a_to_b else f"{b_lbl}克{a_lbl}"
        results.append(
            {
                "类型": "天干克",
                "组合": combo,
                "组合明细": dict(detail_stem),
                "克向": ke_dir,
                "主动方": active,
                "状态": get_status("天干克", {"key": "adjacent"}),
                "紧贴": True,
                "根基": root_detail,
            }
        )

    return results


def _detect_pairwise_ganzhitouhe(
    a_stem: str,
    a_branch: str,
    b_stem: str,
    b_branch: str,
    a_lbl: str,
    b_lbl: str,
    day_stem: str,
) -> list[dict]:
    """
    Detect 干支透合 (stem-branch hidden combine) — checked bidirectionally.

    Direction 1 (a→b): a_stem combines with a hidden stem inside b_branch
    Direction 2 (b→a): b_stem combines with a hidden stem inside a_branch

    Each direction stops at the first hidden-stem match (one entry per direction max).
    藏干层 uses module-level _HIDDEN_LABELS = ("本气", "中气", "余气").

    Internal `_direction` field ("a_to_b" / "b_to_a") is retained until output
    assembly so that _pairwise_pass_cross_actor can build the correct remark fmt
    kwargs (贪合 direction). Stripped from output by _build_pairwise_output.
    """
    results = []
    combo = f"{a_lbl}-{b_lbl}"

    # Direction 1: a_stem → hidden stem inside b_branch
    for hi, hs in enumerate(LunarUtil.ZHI_HIDE_GAN.get(b_branch, [])):
        if stem_combines.get(a_stem) == hs:
            results.append(
                {
                    "类型": "干支透合",
                    "组合": combo,
                    "组合明细": {
                        f"{a_lbl}干": a_stem,
                        f"{b_lbl}支": b_branch,
                        "藏干": hs,
                        "藏干层": _HIDDEN_LABELS[hi] if hi < 3 else "余气",
                        "藏干十神": _get_shi_shen_for_stem_pair(day_stem, hs),
                        "合化五行": _STEM_COMBINE_ELEMENT.get(a_stem, ""),
                    },
                    "主动方": a_lbl,
                    "状态": get_status("干支透合"),
                    "_direction": "a_to_b",
                }
            )
            break  # one match per direction

    # Direction 2: b_stem → hidden stem inside a_branch
    for hi, hs in enumerate(LunarUtil.ZHI_HIDE_GAN.get(a_branch, [])):
        if stem_combines.get(b_stem) == hs:
            results.append(
                {
                    "类型": "干支透合",
                    "组合": combo,
                    "组合明细": {
                        f"{b_lbl}干": b_stem,
                        f"{a_lbl}支": a_branch,
                        "藏干": hs,
                        "藏干层": _HIDDEN_LABELS[hi] if hi < 3 else "余气",
                        "藏干十神": _get_shi_shen_for_stem_pair(day_stem, hs),
                        "合化五行": _STEM_COMBINE_ELEMENT.get(b_stem, ""),
                    },
                    "主动方": b_lbl,
                    "状态": get_status("干支透合"),
                    "_direction": "b_to_a",
                }
            )
            break

    return results


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Priority Filter
# ══════════════════════════════════════════════════════════════════════════════


def _lookup_rule(lock_type: str, itype: str) -> str | None:
    """
    Check CYCLE_PRIORITY_RULE_TABLE first, fall back to PRIORITY_RULE_TABLE.
    Returns target 强度 string or None if no rule applies.
    """
    strength = CYCLE_PRIORITY_RULE_TABLE.get((lock_type, itype))
    if strength is None:
        strength = PRIORITY_RULE_TABLE.get((lock_type, itype))
    return strength


def _lookup_remark(lock_type: str, itype: str, **fmt_kw) -> str:
    """
    Check CYCLE_REMARKS first, fall back to STRENGTH_REMARKS.
    Formats with provided kwargs; returns empty string if no remark.
    """
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
    """
    Apply a priority-rule downgrade to item. Only downgrades; never upgrades.
    Writes first causal remark. Returns True if a rule was matched.
    """
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


def _pairwise_pre_pass(items: list[dict], a_lbl: str, b_lbl: str) -> tuple[bool, bool]:
    """
    Pre-pass: assign 强势主流 to 反吟/伏吟 and absorb implied sub-interactions.

    反吟 absorbs 六冲 and 天干冲 directly (set to 消融吸收) because those interactions
    are already implied by the complete dry+branch clash that defines 反吟.

    伏吟 absorbs 比和 and 干支透合 via CYCLE_PRIORITY_RULE_TABLE PREPASS_伏吟 entries
    (table-driven downgrade; remark written by _apply_downgrade).

    Returns:
        (has_fanyin, has_fuyin): booleans indicating which types were detected,
        used by the orchestrator to decide whether further passes are relevant.
    """
    has_fanyin = False
    has_fuyin = False
    fuyin_items = []

    for item in items:
        itype = item.get("类型")
        if itype == "反吟":
            item["强度"] = "强势主流"
            d = item.get("组合明细", {})
            cs, cb = d.get(f"{a_lbl}干", ""), d.get(f"{a_lbl}支", "")
            item.setdefault(
                "备注",
                f"反吟：干支皆反，{a_lbl}（{cs}{cb}）与{b_lbl}完全对冲，极度动荡",
            )
            has_fanyin = True
        elif itype == "伏吟":
            item["强度"] = "强势主流"
            d = item.get("组合明细", {})
            cs, cb = d.get(f"{a_lbl}干", ""), d.get(f"{a_lbl}支", "")
            item.setdefault(
                "备注",
                f"伏吟：干支皆同，{a_lbl}（{cs}{cb}）与{b_lbl}完全重叠，停滞呻吟",
            )
            has_fuyin = True
            fuyin_items.append(item)

    # 反吟 absorbs 六冲 + 天干冲 (already implied in 反吟 definition)
    if has_fanyin:
        for item in items:
            itype = item.get("类型")
            if itype in ("六冲", "天干冲"):
                item["强度"] = "消融吸收"
                item.setdefault("备注", f"反吟已含{itype}，干支皆反已论，消融吸收")

    # 伏吟 absorbs 比和 + 干支透合 (via CYCLE_PRIORITY_RULE_TABLE PREPASS_伏吟 entries)
    if has_fuyin:
        for item in items:
            itype = item.get("类型")
            if itype in ("比和", "干支透合"):
                _apply_downgrade(item, "PREPASS_伏吟")

    return has_fanyin, has_fuyin


def _pairwise_pass_stem(items: list[dict], a_lbl: str) -> str | None:
    """
    Stem priority lock: 天干合 > 天干克 > 天干冲.

    Identifies the highest-priority stem interaction as winner. All other stem
    interactions are downgraded via _apply_downgrade(lock_type, cycle=a_lbl).
    Winner strength is NOT assigned here — left to _pairwise_pass_defaults and
    then modulated by _pass_stem_rooting (Pass S).

    Returns:
        lock_type string (e.g. "STEM_天干合") used by _pairwise_pass_cross_actor,
        or None if no stem interactions exist.
    """
    stem_items = [it for it in items if it.get("类型") in _STEM_TYPES]
    if not stem_items:
        return None

    he = [it for it in stem_items if it.get("类型") == "天干合"]
    ke = [it for it in stem_items if it.get("类型") == "天干克"]
    chong = [it for it in stem_items if it.get("类型") == "天干冲"]

    winner, lock_type = None, None
    if he:
        winner, lock_type = he[0], "STEM_天干合"
    elif ke:
        winner, lock_type = ke[0], "STEM_天干克"
    elif chong:
        winner, lock_type = chong[0], "STEM_天干冲"

    if winner is None:
        return None

    for item in stem_items:
        if item is winner:
            continue
        _apply_downgrade(item, lock_type, cycle=a_lbl)

    return lock_type


def _pairwise_pass_branch(
    items: list[dict],
    a_lbl: str,
    b_lbl: str,
    a_branch: str,
    b_branch: str,
) -> str | None:
    """
    Branch priority lock: 六合 > 六冲/开库.

    Scope: branch_items excludes stem types (天干合/克/冲) and 反吟/伏吟 — those are
    handled by their own passes. The winner is the first 六合 or 六冲/开库 item.
    All other branch items are downgraded via _apply_downgrade(lock_type, **fmt).

    Note: when a dual-tomb clash produces two 开库 entries (辰-戌, 丑-未), the second
    entry receives a downgrade remark from this pass, but its 强度 is subsequently
    overwritten by _pairwise_pass_kaiku, which sets all 开库 items to the same
    KAIKU_STRENGTH value. The remark from this pass does not affect final strength.

    Returns:
        lock_type string (e.g. "PRIMARY_六合") used by _pairwise_pass_kaiku and
        _pairwise_pass_cross_actor, or None if no branch lock winner exists.
    """
    skip_types = _STEM_TYPES | {"反吟", "伏吟"}
    branch_items = [it for it in items if it.get("类型") not in skip_types]
    if not branch_items:
        return None

    liu_he = [it for it in branch_items if it.get("类型") == "六合"]
    liu_chong = [it for it in branch_items if it.get("类型") in ("六冲", "开库")]

    winner, lock_type = None, None
    if liu_he:
        winner, lock_type = liu_he[0], "PRIMARY_六合"
    elif liu_chong:
        winner, lock_type = liu_chong[0], "PRIMARY_六冲"

    if winner is None:
        return None

    fmt = dict(cycle=a_lbl, cb=a_branch, pillar=b_lbl, lock_nb=b_branch)

    for item in branch_items:
        if item is winner:
            continue
        _apply_downgrade(item, lock_type, **fmt)

    return lock_type


def _pairwise_pass_cross_actor(
    items: list[dict],
    stem_lock: str | None,
    branch_lock: str | None,
    a_lbl: str,
    b_lbl: str,
    a_stem: str,
    b_stem: str,
) -> None:
    """
    Cross-actor suppression: stem lock and/or branch lock → downgrade 干支透合.

    A 干支透合 whose initiating stem is already locked into a 天干合/克/冲 or whose
    branch side is locked by 六合/六冲 is suppressed (贪合 — the stem is "distracted"
    by the primary interaction).

    The `_direction` field on each 干支透合 item identifies which pillar initiated it,
    so the remark fmt kwargs (cycle, cs, pillar, lock_ns) correctly name the locked
    stem and its label. Both stem_lock and branch_lock are applied independently.
    """
    for item in items:
        if item.get("类型") != "干支透合":
            continue

        # Determine which pillar initiated this 干支透合 so the remark
        # can name the correct stem/label pair (贪合 direction).
        direction = item.get("_direction", "a_to_b")
        if direction == "a_to_b":
            fmt = dict(cycle=a_lbl, cs=a_stem, pillar=b_lbl, lock_ns=b_stem)
        else:
            fmt = dict(cycle=b_lbl, cs=b_stem, pillar=a_lbl, lock_ns=a_stem)

        if stem_lock is not None:
            _apply_downgrade(item, stem_lock, **fmt)
        if branch_lock is not None:
            _apply_downgrade(item, branch_lock, **fmt)


def _pairwise_pass_kaiku(items: list[dict], branch_lock: str | None) -> None:
    """
    Resolve 开库 钥匙受困 and populate 库藏释放 fields.

    In a 1×1 pairwise context only two trapped states are possible:
      - fully_trapped: branch_lock == "PRIMARY_六合" — the key branch is bilaterally
                       bonded by 六合, immobilising it and preventing the tomb opening.
      - free:          all other cases — the key branch is unobstructed.

    For each 开库 item still holding the _PENDING sentinel:
        钥匙受困 ← trapped_state
        强度     ← KAIKU_STRENGTH[trapped_state]  (overwrites any prior downgrade)

    For each entry in 库藏释放:
        释放强度 ← KAIKU_RELEASE_STRENGTH[(trapped_state, 层次)]
        受阻     ← True if fully_trapped
        释放性质 ← base_nature from KAIKU_RELEASE_NATURE, OR overridden to
                   "合化{elem}（{干}{合化方}合，{来源}捕获）" if the released stem
                   is immediately captured by a combining cycle stem (贪合吸收).
    """
    trapped_state = "fully_trapped" if branch_lock == "PRIMARY_六合" else "free"

    for item in items:
        if item.get("类型") != "开库":
            continue
        ku_ti = item.get("库体", {})
        if ku_ti.get("钥匙受困") != _PENDING:
            continue

        ku_ti["钥匙受困"] = trapped_state
        item["强度"] = KAIKU_STRENGTH.get(trapped_state, "强势主流")

        for entry in item.get("库藏释放", []):
            ceng = entry.get("层次", "余气")
            base_nature = KAIKU_RELEASE_NATURE.get((trapped_state, ceng), "受阻封印")
            entry["释放强度"] = KAIKU_RELEASE_STRENGTH.get(
                (trapped_state, ceng), "消融吸收"
            )
            entry["受阻"] = trapped_state == "fully_trapped"
            # If the released stem is immediately captured by a cycle stem combine,
            # override 释放性质 to reflect the combine event (贪合吸收).
            if "干合" in entry:
                gan_he = entry["干合"]
                elem = gan_he.get("合化五行", "")
                entry["释放性质"] = (
                    f"合化{elem}（{entry['天干']}{gan_he['合化方']}合，{gan_he['来源']}捕获）"
                )
            else:
                entry["释放性质"] = base_nature


def _pairwise_pass_defaults(items: list[dict]) -> None:
    """
    Assign default 强度 to any item not yet strength-resolved.

    PAIRWISE_BASE_STRENGTH is used first (all interactions treated as adjacent —
    no distance penalty applies in a 1×1 cycle-to-cycle context). Falls back to
    DEFAULT_STRENGTH[(itype, True)] for any type not in the pairwise table.
    Items that already have a 强度 (set by priority or kaiku passes) are skipped.
    """
    for item in items:
        if item.get("强度"):
            continue
        itype = item.get("类型", "")
        item["强度"] = PAIRWISE_BASE_STRENGTH.get(
            itype,
            DEFAULT_STRENGTH.get((itype, True), "强势主流"),
        )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Xun Kong Pass
# ══════════════════════════════════════════════════════════════════════════════


def _pairwise_xun_kong_pass(
    items: list[dict],
    a_lbl: str,
    b_lbl: str,
    a_branch: str,
    b_branch: str,
    a_xk_str: str | None,
    b_xk_str: str | None,
) -> None:
    """
    Post-filter: downgrade interactions involving void (旬空) branches.

    Each cycle branch is checked against its OWN xk_str — not cross-applied.
    Branches are identified by the `{lbl}支` key in 组合明细. Stem-only interaction
    types (_XK_STEM_ONLY) are skipped entirely.

    Void branch effect by interaction type:
        合 types (六合/半合/暗合/比和): one-tier downgrade regardless of which side is void
        冲/开库 types: dual-void → 双空相冲 (one-tier downgrade);
                       single-void → 冲开旬空 (remark appended, no strength change)
        刑 types:      one-tier downgrade
        害/破 types:   one-tier downgrade
        misc types:    one-tier downgrade

    旬空涉及 field is set on affected items listing the void cycle labels.
    """
    a_key = f"{a_lbl}支"
    b_key = f"{b_lbl}支"

    for item in items:
        itype = item.get("类型", "")
        if itype in _XK_STEM_ONLY:
            continue

        detail = item.get("组合明细", {})
        void_parts: list[str] = []
        total_branch_count = 0

        for key, val in detail.items():
            if not isinstance(val, str) or len(val) != 1:
                continue
            if val not in branch_elements:
                continue
            if key not in (a_key, b_key):
                continue

            total_branch_count += 1
            if key == a_key and a_xk_str and _is_cycle_branch_void(val, a_xk_str):
                void_parts.append(a_lbl)
            elif key == b_key and b_xk_str and _is_cycle_branch_void(val, b_xk_str):
                void_parts.append(b_lbl)

        if not total_branch_count or not void_parts:
            continue

        if itype in _XK_HE_TYPES:
            _downgrade_by_one_tier_xk(item, _build_xk_remark(void_parts, "合_single"))
            item["旬空涉及"] = void_parts
        elif itype in _XK_CHONG_TYPES or itype == "开库":
            if len(void_parts) == total_branch_count:
                _downgrade_by_one_tier_xk(
                    item, _build_xk_remark(void_parts, "双空相冲")
                )
                item["旬空涉及"] = void_parts
            else:
                _append_remark_xk(item, _build_xk_remark(void_parts, "冲开旬空"))
                item["旬空涉及"] = void_parts
        elif itype in _XK_XING_TYPES:
            _downgrade_by_one_tier_xk(item, _build_xk_remark(void_parts, "刑_single"))
            item["旬空涉及"] = void_parts
        elif itype in _XK_HAI_PO_TYPES:
            _downgrade_by_one_tier_xk(item, _build_xk_remark(void_parts, "害破_single"))
            item["旬空涉及"] = void_parts
        elif itype in _XK_MISC_TYPES:
            _downgrade_by_one_tier_xk(item, _build_xk_remark(void_parts, "misc_single"))
            item["旬空涉及"] = void_parts


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Output Assembly
# ══════════════════════════════════════════════════════════════════════════════

_STRIP_KEYS = {"_direction", "_synthetic"}


def _build_pairwise_output(items: list[dict]) -> dict:
    """
    Sort by tier, build 关系总览, strip internal keys, assemble output dict.

    Sorting: PAIRWISE_TIER_ORDER; unknown types sort last (key 99).
    Summary: includes only items with 强势主流 or 显著影响 strength; de-duplicated
             by label string so the same type doesn't appear twice in the list.
    Stripped keys: _direction, _synthetic (internal sentinel fields).
    """
    items.sort(key=lambda it: PAIRWISE_TIER_ORDER.get(it.get("类型", ""), 99))

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
        "岁运作用": {
            "关系总览": summary,
            "互动列表": items,
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Orchestrator
# ══════════════════════════════════════════════════════════════════════════════


def get_pairwise_cycle_interactions(
    cycle_a_stem: str,
    cycle_a_branch: str,
    cycle_b_stem: str,
    cycle_b_branch: str,
    day_stem: str,
    cycle_a_label: str = "大运",
    cycle_b_label: str = "流年",
    cycle_a_xk_str: str | None = None,
    cycle_b_xk_str: str | None = None,
    tong_gen: str = "中根",
) -> dict:
    """
    Detect and priority-resolve all interactions between two cycle pillars.

    Processing pipeline:
        Step 1 — Detection: 反吟/伏吟, branch, stem, 干支透合 (four helpers)
        Step 2 — Priority filter:
                   pre-pass   → 反吟/伏吟 absorb implied sub-interactions
                   stem pass  → 天干合 > 天干克 > 天干冲; returns stem_lock
                   branch pass→ 六合 > 六冲/开库; returns branch_lock
                   cross-actor→ stem/branch locks suppress 干支透合
                   kaiku pass → resolves 开库 trapped state + 库藏释放 fields
                   defaults   → assign PAIRWISE_BASE_STRENGTH to unresolved items
                   Pass S     → _pass_stem_rooting modulates 天干合/克/冲 by 通根 tier
        Step 3 — Xun Kong pass (skipped if no xk strings provided)
        Step 4 — Output assembly: sort, build summary, append 根基

    If no interactions are detected, returns the empty-list output with 根基 only.

    Args:
        cycle_a_stem / cycle_a_branch: First cycle pillar stem and branch characters.
        cycle_b_stem / cycle_b_branch: Second cycle pillar stem and branch characters.
        day_stem: Birth Day Stem (日元) — used for 十神 resolution in 开库 and 干支透合.
        cycle_a_label: Display label for the first cycle (default "大运").
        cycle_b_label: Display label for the second cycle (default "流年").
        cycle_a_xk_str: Xun Kong string for cycle A from getXunKong() (e.g. "午未").
                        If None, cycle A's branches are not void-checked.
        cycle_b_xk_str: Xun Kong string for cycle B from getXunKong().
                        If None, cycle B's branches are not void-checked.

    Returns:
        dict: {"岁运作用": {"关系总览": [...], "互动列表": [...], "根基": {...}}}
    """
    a_s, a_b = cycle_a_stem, cycle_a_branch
    b_s, b_b = cycle_b_stem, cycle_b_branch
    a_lbl, b_lbl = cycle_a_label, cycle_b_label

    # ── Step 1: Detection ────────────────────────────────────────────────────
    all_items: list[dict] = []
    all_items.extend(_detect_pairwise_fanyin_fuyin(a_s, a_b, b_s, b_b, a_lbl, b_lbl))
    all_items.extend(
        _detect_pairwise_branch(a_s, a_b, b_s, b_b, a_lbl, b_lbl, day_stem, tong_gen)
    )
    all_items.extend(_detect_pairwise_stem(a_s, a_b, b_s, b_b, a_lbl, b_lbl))
    all_items.extend(
        _detect_pairwise_ganzhitouhe(a_s, a_b, b_s, b_b, a_lbl, b_lbl, day_stem)
    )

    if not all_items:
        result = _build_pairwise_output([])
        result["岁运作用"]["根基"] = compute_pillar_rooting(
            [a_s, b_s], [a_b, b_b], [a_lbl + "柱", b_lbl + "柱"]
        )
        return result

    # ── Step 2: Priority Filter ──────────────────────────────────────────────
    _pairwise_pre_pass(all_items, a_lbl, b_lbl)
    stem_lock = _pairwise_pass_stem(all_items, a_lbl)
    branch_lock = _pairwise_pass_branch(all_items, a_lbl, b_lbl, a_b, b_b)
    _pairwise_pass_cross_actor(
        all_items, stem_lock, branch_lock, a_lbl, b_lbl, a_s, b_s
    )
    _pairwise_pass_kaiku(all_items, branch_lock)
    _pairwise_pass_defaults(all_items)
    _pass_stem_rooting(all_items)

    # ── Step 3: Xun Kong Pass ────────────────────────────────────────────────
    if cycle_a_xk_str or cycle_b_xk_str:
        _pairwise_xun_kong_pass(
            all_items,
            a_lbl,
            b_lbl,
            a_b,
            b_b,
            cycle_a_xk_str,
            cycle_b_xk_str,
        )

    # ── Step 4: Output Assembly ──────────────────────────────────────────────
    result = _build_pairwise_output(all_items)
    rooting = compute_pillar_rooting(
        [a_s, b_s],
        [a_b, b_b],
        [a_lbl + "柱", b_lbl + "柱"],
    )
    result["岁运作用"]["根基"] = rooting
    return result


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from datetime import datetime
    from src.utils.logging import configure_logging, get_logger
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
    from src.astronomer_calculations.void_xun_kong import get_xun_kong
    from src.astronomer_calculations.cycle2_natal_interactions import (
        get_cross_cycle_interactions,
    )

    # python -m src.astronomer_calculations.cycle_to_cycle_interactions

    configure_logging()
    logger = get_logger(__name__)

    # --- Birthday (uncomment one) ---

    # Desmond
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)
    tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)
    gender = 0  # male

    # Corinne
    # datetime_birthday = datetime(1987, 6, 3, 12, 6, 0)
    # tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.4759, 103.808053)
    # gender = 1  # female

    lunar = tst_birthday.getLunar()
    bazi = lunar.getEightChar()
    day_stem = bazi.getDayGan()

    logger.info(f"真太阳时: {tst_birthday.toYmdHms()}")
    logger.info(
        f"八字: {bazi.getYear()} {bazi.getMonth()} {bazi.getDay()} {bazi.getTime()}"
    )
    logger.info(f"日元: {day_stem}")

    # --- Birth chart & natal xun kong ---
    natal_chart = {
        "year": {"stem": bazi.getYearGan(), "branch": bazi.getYearZhi()},
        "month": {"stem": bazi.getMonthGan(), "branch": bazi.getMonthZhi()},
        "day": {"stem": bazi.getDayGan(), "branch": bazi.getDayZhi()},
        "hour": {"stem": bazi.getTimeGan(), "branch": bazi.getTimeZhi()},
    }
    natal_xk = get_xun_kong(lunar).get("旬空", {})

    # --- Pick one Da Yun + one Liu Nian within it ---
    yun = bazi.getYun(gender)
    da_yun = yun.getDaYun()[2]  # index 2 = third active 大运
    liu_nian = da_yun.getLiuNian()[5]  # fifth 流年 inside that 大运

    da_yun_gz = da_yun.getGanZhi()
    liu_nian_gz = liu_nian.getGanZhi()

    da_yun_stem, da_yun_branch = da_yun_gz[0], da_yun_gz[1]
    liu_nian_stem, liu_nian_branch = liu_nian_gz[0], liu_nian_gz[1]

    da_yun_xk_str = da_yun.getXunKong() if hasattr(da_yun, "getXunKong") else None
    liu_nian_xk_str = liu_nian.getXunKong() if hasattr(liu_nian, "getXunKong") else None

    # Fan Yin (反吟) combined with a Tomb/Storage Clash (辰戌冲) test case
    # da_yun_stem,   da_yun_branch   = "甲", "辰"
    # liu_nian_stem, liu_nian_branch = "庚", "戌"

    # da_yun_xk_str   = None
    # liu_nian_xk_str = None

    logger.info(
        f"\n大运: {da_yun_stem}{da_yun_branch}  |  流年: {liu_nian_stem}{liu_nian_branch}  (年份 {liu_nian.getYear()})"
    )

    # --- 岁运作用: pairwise Da Yun ↔ Liu Nian ---
    pairwise = get_pairwise_cycle_interactions(
        da_yun_stem,
        da_yun_branch,
        liu_nian_stem,
        liu_nian_branch,
        day_stem,
        cycle_a_xk_str=da_yun_xk_str,
        cycle_b_xk_str=liu_nian_xk_str,
    )
    logger.info("\n--- 岁运作用 (大运 ↔ 流年 pairwise) ---")
    logger.info(json.dumps(pairwise, ensure_ascii=False, indent=2))

    # --- 跨运作用: cross-cycle structures (natal + Da Yun + Liu Nian) ---
    cross = get_cross_cycle_interactions(
        da_yun_stem,
        da_yun_branch,
        liu_nian_stem,
        liu_nian_branch,
        natal_chart,
        day_stem=day_stem,
        cycle_a_xk_str=da_yun_xk_str,
        cycle_b_xk_str=liu_nian_xk_str,
        natal_xk=natal_xk,
    )
    logger.info("\n--- 跨运作用 (命盘 + 大运 + 流年 cross-cycle) ---")
    logger.info(json.dumps(cross, ensure_ascii=False, indent=2))
