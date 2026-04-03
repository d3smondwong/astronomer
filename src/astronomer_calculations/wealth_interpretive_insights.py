"""
Wealth Interpretive Insights

Pre-computes structural wealth patterns from raw aggregator data and returns
labeled facts for LLM injection. Eliminates the need for the LLM to re-derive
wealth signals from raw pillars under token constraints.

Usage:
    from src.services.wealth_interpretive_insights import extract_wealth_insights
    wealth_insights = extract_wealth_insights(raw_data)
"""

# ── Constants ──────────────────────────────────────────────────────────────────

WEALTH_STARS = {"正财", "偏财"}
FOOD_HURT = {"食神", "伤官"}
YIN_STARS = {"正印", "偏印"}
TOMB_BRANCHES = {"辰", "戌", "丑", "未"}
PILLARS = ["年柱", "月柱", "日柱", "时柱"]
BRANCH_TIERS = ["本气", "中气", "余气"]
SAN_XING_TYPES = {"无恩之刑", "恃势之刑", "无礼之刑", "自刑"}
ACTIVE_STRENGTHS = {"强势主流", "显著影响", "中等影响"}

# Used only by _pattern_virtual_bureau — structural formation, not explicit star check
WEALTH_ELEMENT_MAP = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
STRENGTH_RANK = ["强势主流", "显著影响", "中等影响", "大幅衰减", "中等衰减", "消融吸收"]

# Maps branch label → pillar name for interactions lookup
BRANCH_LABEL_TO_PILLAR = {"年支": "年柱", "月支": "月柱", "日支": "日柱", "时支": "时柱"}


# ── Shared helpers ─────────────────────────────────────────────────────────────


def _get_wealth_positions(shi_shen: dict) -> dict:
    """
    Scans shi_shen["十神"] for 正财/偏财 appearances across all four pillars.
    Returns:
      {
        "in_stems":    ["年干", ...],       # pillars where 天干十神 is a wealth star
        "in_branches": ["年支本气", ...],   # branch tier positions with wealth star
        "all":         [...combined...]
      }
    """
    in_stems, in_branches = [], []
    for pillar in PILLARS:
        p = shi_shen.get(pillar, {})
        if p.get("天干十神") in WEALTH_STARS:
            in_stems.append(pillar[:1] + "干")           # e.g. "年干", "月干"
        for tier in BRANCH_TIERS:
            if p.get("地支十神", {}).get(tier) in WEALTH_STARS:
                in_branches.append(pillar[:1] + "支" + tier)   # e.g. "年支中气"
    return {"in_stems": in_stems, "in_branches": in_branches, "all": in_stems + in_branches}


def _dm_strength_score(ri_zhu: dict) -> int:
    """
    Scores DM strength 0–3, one point per classical factor:
      得令: ri_zhu["得令"]["得令"] is True
      得地: ri_zhu["得地"]["通根"] in {"深根", "中根"}
      得势: len(ri_zhu["得势"]["支持天干"]) >= 2
    >= 2 → not weak (passes majority of the three pillars)
    <= 1 → weak
    """
    de_ling = int(ri_zhu["得令"]["得令"])
    de_di = int(ri_zhu["得地"]["通根"] in {"深根", "中根"})
    de_shi = int(len(ri_zhu["得势"]["支持天干"]) >= 2)
    return de_ling + de_di + de_shi


def _get_branch_chars(bazi: dict) -> dict:
    """Returns {"年支": "丑", "月支": "亥", "日支": "辰", "时支": "申"}"""
    ba_zi = bazi["八字"]
    return {
        "年支": ba_zi["年柱"]["地支"],
        "月支": ba_zi["月柱"]["地支"],
        "日支": ba_zi["日柱"]["地支"],
        "时支": ba_zi["时柱"]["地支"],
    }


def _has_chong_xing_on_pillar(pillar_name: str, interactions: dict) -> bool:
    """Return True if the pillar has an active 六冲 or 三刑 (strength in ACTIVE_STRENGTHS)."""
    pillar_data = interactions["作用"]["柱位动态"].get(pillar_name, {})
    for tier_items in pillar_data.values():
        for item in tier_items:
            if item.get("类型") in {"六冲"} | SAN_XING_TYPES:
                if item.get("强度") in ACTIVE_STRENGTHS:
                    return True
    return False


def _wealth_in_tomb_list(shi_shen: dict, branch_chars: dict) -> list:
    """
    Returns labels like "年支(辰)" for each pillar where a wealth star sits
    inside a tomb branch (辰/戌/丑/未).
    """
    result = []
    for pillar in PILLARS:
        branch_key = pillar[:1] + "支"    # e.g. "年支", "月支"
        branch_char = branch_chars.get(branch_key, "")
        if branch_char in TOMB_BRANCHES:
            for tier in BRANCH_TIERS:
                if shi_shen.get(pillar, {}).get("地支十神", {}).get(tier) in WEALTH_STARS:
                    result.append(f"{branch_key}({branch_char})")
                    break
    return result


def _get_current_decade(da_yun: dict) -> dict | None:
    """Return the decade dict with 当运 == True, or None if not found."""
    cycles = da_yun.get("大运", {}).get("大运周期", [])
    for cycle in cycles[1:]:    # skip index 0 — placeholder "未行大运"
        if cycle.get("当运"):
            return cycle
    return None


def _decade_has_wealth(decade: dict) -> bool:
    """True if the decade's 运柱 contains 正财/偏财 in stem or any branch hidden tier."""
    run_zhu = decade.get("运柱", {})
    if not isinstance(run_zhu, dict):
        return False
    shi_shen = run_zhu.get("十神", {})
    if shi_shen.get("天干", {}).get("十神") in WEALTH_STARS:
        return True
    for tier in BRANCH_TIERS:
        tier_data = shi_shen.get(tier)
        if isinstance(tier_data, dict) and tier_data.get("十神") in WEALTH_STARS:
            return True
    return False


# ── Pattern functions ─────────────────────────────────────────────────────────
# All return: {"matched": bool, "confidence": str, "verdict": str, "evidence": str}
# evidence is "" when matched == False.


# ── Category 1: Visibility ────────────────────────────────────────────────────


def _pattern_hidden_wealth(wp: dict) -> dict:
    matched = len(wp["in_stems"]) == 0 and len(wp["in_branches"]) > 0
    return {
        "matched": matched,
        "confidence": "high",
        "verdict": "Wealth is real and present, but not externally visible — this person possesses money without displaying it.",
        "evidence": f"Wealth in: {wp['in_branches']}; no wealth in any heavenly stem" if matched else "",
    }


def _pattern_visible_wealth(wp: dict) -> dict:
    matched = len(wp["in_stems"]) > 0 and len(wp["in_branches"]) == 0
    return {
        "matched": matched,
        "confidence": "high",
        "verdict": "Wealth energy is openly expressed — financial activity and resources are visible to others.",
        "evidence": f"Wealth stems: {wp['in_stems']}" if matched else "",
    }


def _pattern_mixed_visibility(wp: dict) -> dict:
    matched = len(wp["in_stems"]) > 0 and len(wp["in_branches"]) > 0
    return {
        "matched": matched,
        "confidence": "high",
        "verdict": "Wealth has both visible and hidden aspects — some resources are public, others kept private.",
        "evidence": f"Stems: {wp['in_stems']}; Branches: {wp['in_branches']}" if matched else "",
    }


# ── Category 2: Source / Origin ───────────────────────────────────────────────


def _pattern_self_generated_wealth(shi_shen: dict, wp: dict) -> dict:
    no_wealth = len(wp["all"]) == 0
    has_food = any(
        shi_shen.get(pl, {}).get("天干十神") in FOOD_HURT
        or any(shi_shen.get(pl, {}).get("地支十神", {}).get(t) in FOOD_HURT for t in BRANCH_TIERS)
        for pl in PILLARS
    )
    matched = no_wealth and has_food
    return {
        "matched": matched,
        "confidence": "medium",
        "verdict": "Wealth is generated through personal skill, creativity, or output — not inherited or passively received.",
        "evidence": "No wealth stars; 食伤 present" if matched else "",
    }


def _pattern_inherited_wealth(wp: dict) -> dict:
    matched = any("年" in pos for pos in wp["all"])
    return {
        "matched": matched,
        "confidence": "high",
        "verdict": "Family resources or inheritance play a significant role in wealth foundation.",
        "evidence": f"Wealth in year pillar: {[p for p in wp['all'] if '年' in p]}" if matched else "",
    }


def _pattern_spousal_wealth(wp: dict) -> dict:
    matched = any("日支" in pos for pos in wp["in_branches"])
    return {
        "matched": matched,
        "confidence": "high",
        "verdict": "Wealth is connected to spouse or close business partner — joint resources or marriage brings financial benefit.",
        "evidence": f"Wealth in day branch: {[p for p in wp['in_branches'] if '日支' in p]}" if matched else "",
    }


# ── Category 3: Tomb Patterns ─────────────────────────────────────────────────


def _pattern_wealth_in_tomb(shi_shen: dict, bazi: dict) -> dict:
    branch_chars = _get_branch_chars(bazi)
    tomb_list = _wealth_in_tomb_list(shi_shen, branch_chars)
    matched = len(tomb_list) > 0
    return {
        "matched": matched,
        "confidence": "high",
        "verdict": "Wealth is stored or locked away — potential exists but requires a trigger (time, event, or person) to access.",
        "evidence": f"Wealth in tomb branches: {tomb_list}" if matched else "",
    }


def _pattern_tomb_opened(shi_shen: dict, bazi: dict, interactions: dict) -> dict:
    branch_chars = _get_branch_chars(bazi)
    tomb_list = _wealth_in_tomb_list(shi_shen, branch_chars)
    opened = [
        entry for entry in tomb_list
        if _has_chong_xing_on_pillar(BRANCH_LABEL_TO_PILLAR[entry[:2]], interactions)
    ]
    matched = len(opened) > 0
    return {
        "matched": matched,
        "confidence": "high",
        "verdict": "Wealth locked in a tomb branch is triggered by a natal 六冲 or 三刑 — the seal is already broken; resources are accessible.",
        "evidence": f"Opened tomb branches: {opened}" if matched else "",
    }


def _pattern_tomb_closed(shi_shen: dict, bazi: dict, interactions: dict) -> dict:
    branch_chars = _get_branch_chars(bazi)
    tomb_list = _wealth_in_tomb_list(shi_shen, branch_chars)
    if not tomb_list:
        return {
            "matched": False,
            "confidence": "high",
            "verdict": "Wealth stored in tomb with no natal trigger — potential exists but requires external event to unlock.",
            "evidence": "",
        }
    closed = [
        entry for entry in tomb_list
        if not _has_chong_xing_on_pillar(BRANCH_LABEL_TO_PILLAR[entry[:2]], interactions)
    ]
    matched = len(closed) > 0
    return {
        "matched": matched,
        "confidence": "high",
        "verdict": "Wealth stored in a tomb branch has no natal trigger — the potential is real but may lie dormant until the right luck cycle or event arrives.",
        "evidence": f"Sealed tomb branches: {closed}" if matched else "",
    }


# ── Category 4: Day Master Interaction ───────────────────────────────────────


def _pattern_wealth_combined_with_dm(shi_shen: dict, interactions: dict) -> dict:
    """
    天干合 where the Day Master stem combines with a 正财/偏财 stem.
    Uses natal shi_shen["十神"][pillar]["天干十神"] for the explicit ten-god check.
    """
    day_pillar = interactions["作用"]["柱位动态"].get("日柱", {})
    combined = []
    for item in day_pillar.get("第二梯队_气势层", []):
        if item.get("类型") == "天干合" and item.get("强度") in ACTIVE_STRENGTHS:
            for pillar, stem in item.get("组合明细", {}).items():
                if pillar != "日柱":
                    ten_god = shi_shen.get(pillar, {}).get("天干十神", "")
                    if ten_god in WEALTH_STARS:
                        combined.append(f"{pillar}({stem}/{ten_god})")
    matched = len(combined) > 0
    return {
        "matched": matched,
        "confidence": "high",
        "verdict": "The Day Master directly combines with a wealth star — wealth tends to come through personal connection, partnership, or timing rather than effort alone.",
        "evidence": f"天干合 with wealth stem: {combined}" if matched else "",
    }


def _pattern_wealth_clashed(shi_shen: dict, bazi: dict, interactions: dict, wp: dict) -> dict:
    """A branch carrying a wealth star has active 六冲 or 三刑 in the natal chart."""
    if not wp["in_branches"]:
        return {
            "matched": False,
            "confidence": "high",
            "verdict": "Wealth energy is disrupted — financial resources exist but can be unstable or damaged at key moments.",
            "evidence": "",
        }
    clashed = [
        pos for pos in wp["in_branches"]
        if _has_chong_xing_on_pillar(BRANCH_LABEL_TO_PILLAR[pos[:2]], interactions)
    ]
    matched = len(clashed) > 0
    return {
        "matched": matched,
        "confidence": "high",
        "verdict": "Wealth energy is disrupted — financial resources exist but can be unstable or damaged at key moments.",
        "evidence": f"Wealth in clashed/punished branches: {clashed}" if matched else "",
    }


def _pattern_wealth_supported_by_yin(shi_shen: dict, wp: dict, ri_zhu: dict) -> dict:
    has_wealth = len(wp["all"]) > 0
    has_yin = any(
        shi_shen.get(pl, {}).get("天干十神") in YIN_STARS
        or any(shi_shen.get(pl, {}).get("地支十神", {}).get(t) in YIN_STARS for t in BRANCH_TIERS)
        for pl in PILLARS
    )
    score = _dm_strength_score(ri_zhu)
    dm_not_weak = score >= 2
    matched = has_wealth and has_yin and dm_not_weak
    return {
        "matched": matched,
        "confidence": "medium",
        "verdict": "Wealth is stable because strong support (family, education, mentors) provides a safety net.",
        "evidence": f"财星 present; 印星 present; DM score {score}/3" if matched else "",
    }


# ── Category 5: Quantity / Magnitude ─────────────────────────────────────────


def _pattern_abundant_wealth(wp: dict) -> dict:
    matched = len(wp["all"]) >= 3
    return {
        "matched": matched,
        "confidence": "high",
        "verdict": "Multiple wealth signals — abundant financial opportunities and resources throughout life.",
        "evidence": f"{len(wp['all'])} wealth occurrences: {wp['all']}" if matched else "",
    }


def _pattern_single_wealth(wp: dict) -> dict:
    matched = len(wp["all"]) == 1
    return {
        "matched": matched,
        "confidence": "high",
        "verdict": "Wealth is focused in one area — often a single skill, source, or relationship that provides financial stability.",
        "evidence": f"One wealth occurrence: {wp['all']}" if matched else "",
    }


def _pattern_virtual_bureau(wu_xing: dict, dm_elem: str) -> dict:
    """
    Detects a structural elemental formation (共拱/三合/三会) of the wealth element.
    Uses WEALTH_ELEMENT_MAP because this pattern concerns formation energy, not explicit stars.
    """
    wealth_elem = WEALTH_ELEMENT_MAP.get(dm_elem)
    combos = wu_xing.get("组合加成", [])
    top = min(
        (c for c in combos if c.get("强度") in STRENGTH_RANK),
        key=lambda c: STRENGTH_RANK.index(c["强度"]),
        default=None,
    )
    matched = (
        top is not None
        and top.get("元素") == wealth_elem
        and top.get("强度") in {"显著影响", "强势主流"}
    )
    return {
        "matched": matched,
        "confidence": "high",
        "verdict": "The chart forms a hidden wealth reservoir — continuous, self-replenishing financial energy.",
        "evidence": f"{top.get('类型')} → {top.get('元素')} [{top.get('强度')}]" if matched else "",
    }


# ── Category 6: Timing ────────────────────────────────────────────────────────


def _pattern_wealth_activated_now(da_yun: dict, wp: dict) -> dict:
    decade = _get_current_decade(da_yun)
    if decade is None:
        return {
            "matched": False,
            "confidence": "medium",
            "verdict": "Wealth luck cycle is currently active — this is a window for financial growth and opportunity.",
            "evidence": "",
        }
    matched = _decade_has_wealth(decade)
    return {
        "matched": matched,
        "confidence": "medium",
        "verdict": "Wealth luck cycle is currently active — this is a window for financial growth and opportunity.",
        "evidence": f"Current decade {decade.get('周期')} has wealth star in 运柱" if matched else "",
    }


def _pattern_wealth_dormant_now(da_yun: dict, wp: dict) -> dict:
    if not wp["all"]:
        return {
            "matched": False,
            "confidence": "medium",
            "verdict": "Natal wealth exists but is not reinforced by the current luck cycle — financial progress is possible but requires more deliberate effort.",
            "evidence": "",
        }
    decade = _get_current_decade(da_yun)
    if decade is None:
        return {
            "matched": False,
            "confidence": "medium",
            "verdict": "Natal wealth exists but is not reinforced by the current luck cycle — financial progress is possible but requires more deliberate effort.",
            "evidence": "",
        }
    matched = bool(wp["all"]) and not _decade_has_wealth(decade)
    return {
        "matched": matched,
        "confidence": "medium",
        "verdict": "Natal wealth exists but is not reinforced by the current luck cycle — financial progress is possible but requires more deliberate effort.",
        "evidence": f"Natal wealth at {wp['all']}; current decade {decade.get('周期')} has no wealth star" if matched else "",
    }


def _pattern_wealth_arrives_late(wp: dict) -> dict:
    matched = len(wp["all"]) > 0 and all("时" in pos for pos in wp["all"])
    return {
        "matched": matched,
        "confidence": "medium",
        "verdict": "Wealth comes later in life — early years may be lean, but financial stability grows with age.",
        "evidence": f"Wealth only in hour pillar: {wp['all']}" if matched else "",
    }


# ── Category 7: Special ───────────────────────────────────────────────────────


def _pattern_wealth_without_star(shi_shen: dict, wp: dict, ri_zhu: dict) -> dict:
    no_wealth = len(wp["all"]) == 0
    has_food = any(
        shi_shen.get(pl, {}).get("天干十神") in FOOD_HURT
        or any(shi_shen.get(pl, {}).get("地支十神", {}).get(t) in FOOD_HURT for t in BRANCH_TIERS)
        for pl in PILLARS
    )
    dm_not_weak = _dm_strength_score(ri_zhu) >= 2
    matched = no_wealth and has_food and dm_not_weak
    return {
        "matched": matched,
        "confidence": "medium",
        "verdict": "Wealth is created entirely through personal effort, creativity, and output — not inherent but fully achievable.",
        "evidence": "No 财星; 食伤 present; DM not weak" if matched else "",
    }


# ── Public API ────────────────────────────────────────────────────────────────


def extract_wealth_insights(raw_data: dict) -> dict:
    """
    Pre-compute structural wealth patterns from raw aggregator output.

    Args:
        raw_data: Output of AstroDataAggregator.collect_data()

    Returns:
        {
            "patterns": list of all 19 pattern dicts (matched + unmatched),
            "active_patterns": list of pattern_ids where matched == True,
            "no_match_default": str | None  — fallback text when no pattern matched
        }
    """
    shi_shen = raw_data["shi_shen"]["十神"]
    ri_zhu = raw_data["day_master"]["日主"]
    bazi = raw_data["bazi"]
    wu_xing = raw_data["wu_xing"]["五行力量"]
    da_yun = raw_data["da_yun"]
    interactions = raw_data["interactions"]
    dm_elem = ri_zhu["五行"]

    wp = _get_wealth_positions(shi_shen)

    all_patterns = [
        ("hidden_wealth",           "Hidden Wealth",              _pattern_hidden_wealth(wp)),
        ("visible_wealth",          "Visible Wealth",             _pattern_visible_wealth(wp)),
        ("mixed_visibility",        "Mixed Visibility",           _pattern_mixed_visibility(wp)),
        ("self_generated_wealth",   "Self-Generated Wealth",      _pattern_self_generated_wealth(shi_shen, wp)),
        ("inherited_wealth",        "Inherited Wealth",           _pattern_inherited_wealth(wp)),
        ("spousal_wealth",          "Spousal Wealth",             _pattern_spousal_wealth(wp)),
        ("wealth_in_tomb",          "Wealth in Tomb",             _pattern_wealth_in_tomb(shi_shen, bazi)),
        ("tomb_opened",             "Wealth Tomb Opened",         _pattern_tomb_opened(shi_shen, bazi, interactions)),
        ("tomb_closed",             "Wealth Tomb Closed",         _pattern_tomb_closed(shi_shen, bazi, interactions)),
        ("wealth_combined_with_dm", "Wealth Combined with DM",    _pattern_wealth_combined_with_dm(shi_shen, interactions)),
        ("wealth_clashed",          "Wealth Clashed/Broken",      _pattern_wealth_clashed(shi_shen, bazi, interactions, wp)),
        ("wealth_supported_by_yin", "Wealth Supported by 印星",   _pattern_wealth_supported_by_yin(shi_shen, wp, ri_zhu)),
        ("abundant_wealth",         "Abundant Wealth",            _pattern_abundant_wealth(wp)),
        ("single_wealth",           "Single Wealth Star",         _pattern_single_wealth(wp)),
        ("virtual_bureau",          "Virtual Wealth Bureau",      _pattern_virtual_bureau(wu_xing, dm_elem)),
        ("wealth_activated_now",    "Wealth Activated Now",       _pattern_wealth_activated_now(da_yun, wp)),
        ("wealth_dormant_now",      "Wealth Dormant Now",         _pattern_wealth_dormant_now(da_yun, wp)),
        ("wealth_arrives_late",     "Wealth Arrives Late",        _pattern_wealth_arrives_late(wp)),
        ("wealth_without_star",     "Wealth Without Wealth Star", _pattern_wealth_without_star(shi_shen, wp, ri_zhu)),
    ]

    patterns_out, active = [], []
    for pid, name, result in all_patterns:
        patterns_out.append({"pattern_id": pid, "name": name, **result})
        if result["matched"]:
            active.append(pid)

    return {
        "patterns": patterns_out,
        "active_patterns": active,
        "no_match_default": (
            "Wealth energy exists without strong structural features — financial outcomes depend on luck cycles and effort."
            if not active
            else None
        ),
    }
