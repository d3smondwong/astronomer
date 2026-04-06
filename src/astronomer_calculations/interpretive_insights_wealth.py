from datetime import date

"""
Wealth Interpretive Insights

Pre-computes structural wealth patterns from raw aggregator data and returns
labeled facts for LLM injection. Eliminates the need for the LLM to re-derive
wealth signals from raw pillars under token constraints.

Output structure:
    {
        "命盘财运格局": [...],   # natal structural facts — always true
        "大运财运动态": [...],   # temporal layer — only cycles with wealth effects
        "无格局提示":   str|None
    }

Natal patterns are organised in four tiers:
  Tier 1 — Positional facts   (visibility, quantity, source — no interactions needed)
  Tier 2 — Structural formations  (elemental relationships: 暗财局, 印财并存)
  Tier 3 — Natal interaction patterns  (六冲/天干合/三刑 on chart)
  Tier 4 — Cycle-relative timing  (read current 大运 only)

Cycle events are produced by four focused helpers called from _get_cycle_wealth_events.

Usage:
    from src.astronomer_calculations.interpretive_insights_wealth import extract_wealth_insights
    wealth_insights = extract_wealth_insights(raw_data)
"""

# ── Constants ──────────────────────────────────────────────────────────────────

WEALTH_STARS = {"正财", "偏财"}
FOOD_GOD_HURT_OFFICER = {"食神", "伤官"}
YIN_STARS = {"正印", "偏印"}
TOMB_BRANCHES = {"辰", "戌", "丑", "未"}
PILLARS = ["年柱", "月柱", "日柱", "时柱"]
BRANCH_TIERS = ["本气", "中气", "余气"]
SAN_XING_TYPES = {"无恩之刑", "恃势之刑", "无礼之刑", "自刑"}
ACTIVE_STRENGTHS = {"强势主流", "显著影响", "中等影响"}

# Used only by _pattern_virtual_bureau — structural formation, not explicit star check
WEALTH_ELEMENT_MAP = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
STRENGTH_RANK = ["强势主流", "显著影响", "中等影响", "大幅衰减", "中等衰减", "消融吸收"]

# DM element → 食伤 element (generation cycle one step ahead)
FOOD_GOD_HURT_OFFICER_ELEMENT_MAP = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
# 食伤 must meet this floor to meaningfully produce wealth
FOOD_GOD_HURT_OFFICER_STRONG_ENOUGH = {"中和", "偏旺", "极旺", "极亢"}
# 食伤 at these tiers overwhelms DM and leaks wealth (食伤过旺泄财 / 金多水浊)
FOOD_GOD_HURT_OFFICER_EXCESSIVE = {"极旺", "极亢"}

# DM element → 印星 element (generation cycle one step back)
YIN_ELEMENT_MAP = {"木": "水", "火": "木", "土": "火", "金": "土", "水": "金"}
# 印星 must meet this floor to meaningfully support wealth
YIN_STRONG_ENOUGH = {"中和", "偏旺", "极旺", "极亢"}
# If 印星 reaches these tiers, it fully suppresses 食伤 and buries wealth (印多埋财)
# 偏旺 excluded — strong but still coexists; only 极旺/极亢 truly smothers wealth
YIN_EXCESSIVE = {"极旺", "极亢"}

# Maps branch label → pillar name for interactions lookup
BRANCH_LABEL_TO_PILLAR = {"年支": "年柱", "月支": "月柱", "日支": "日柱", "时支": "时柱"}

# Four-tier 财多 spectrum (财多身弱 / 财重身轻 / 财身相停 / 身强驾财)
WEALTH_DOM_EXCESSIVE  = {"极旺", "极亢"}          # wealth crushes DM regardless of DM tier
WEALTH_DOM_DM_FLOOR   = {"偏旺", "极旺", "极亢"}  # DM element tiers that can command wealth
DM_STRUCTURALLY_WEAK  = {"偏弱", "极弱"}          # DM element too weak to hold abundant wealth
WEALTH_NEUTRAL_TIERS  = {"中和", "偏弱"}          # 偏弱 wealth treated equivalent to 中和 — does not burden DM

# Combined clash/punishment types — used in wealth disruption checks
CLASH_DISRUPT_TYPES = {"六冲"} | SAN_XING_TYPES

# Ten-god classification for _pattern_wealth_combined_away
_BI_JIE_STARS    = {"比肩", "劫财"}
_GUAN_SHA_STARS = {"正官", "七杀"}

# Synthesis taxonomy — classify fired patterns by structural role
PRIMARY_PATTERNS = {"abundant_wealth", "self_generated_wealth", "month_pillar_wealth"}
SUPPLEMENTARY_IDS = {
    "inherited_wealth", "spousal_wealth", "wealth_arrives_late",
    "virtual_bureau", "tomb_opened", "wealth_combined_with_dm",
    "wealth_supported_by_yin",
}
RISK_IDS = {
    "rivals_take_wealth", "wealth_leaked", "wealth_clashed",
    "wealth_void", "wealth_combined_away", "tomb_closed", "tomb_void",
}
# External-source supplementary names (passive reception, no DM strength needed)
_EXTERNAL_SUPP_NAMES = {"祖业财星", "配偶财星"}

# ── Synthesis template matrix ──────────────────────────────────────────────────
# Keys: (has_supp, has_risk) or (has_supp, has_risk, has_external)
# Lookup in _synthesize_wealth_patterns: 3-tuple checked first, 2-tuple fallback.
# Placeholders: {supp_str}, {risk_str}, {anchor_name}, {wealth_type_name}, {wealth_nature}
_SYNTH: dict[str | None, dict[tuple, str]] = {
    None: {
        (False, False): "命盘财运格局不显著，财运走向主要依赖大运与自身努力。",
        (True,  False): "无明显主格局；辅助财源（{supp_str}）有所助益。",
        (False, True):  "无明显主格局；风险因素（{risk_str}）需留意管理。",
        (True,  True):  "无明显主格局；辅助财源（{supp_str}）有所助益，风险因素（{risk_str}）需留意管理。",
    },
    "财多身弱": {
        # (supp, risk, external) — 3-tuple catches the external sub-cases
        (True,  False, True):  "财多身弱，日主难以主动驾驭财星；然{supp_str}入局，提供外来财源缓冲，宜守成依托，不宜强行主导。",
        (True,  False, False): "财多身弱，日主承压；{supp_str}提供结构缓冲，实际韧性优于纯身弱格局，财运需借助辅助渠道发挥。",
        (True,  False):        "财多身弱，日主承压；{supp_str}兼具外来与辅助来源，多元缓冲减轻压力，宜守成发挥外力，不宜单独冒进。",
        (False, True):         "财多身弱，结构性承压；{risk_str}进一步加重财运阻力，财来财去风险显著，需重点关注消耗与流失。",
        (True,  True,  True):  "财多身弱，{supp_str}提供外来缓冲，但{risk_str}同时带来阻力，外部支援与内部消耗并存，净效益有限。",
        (True,  True,  False): "财多身弱，{supp_str}提供结构缓冲，但{risk_str}同时带来阻力，整体财运复杂，需审慎管理。",
        (True,  True):         "财多身弱，{supp_str}提供部分缓冲，但{risk_str}同时带来阻力，整体财运复杂，净效益有限。",
        (False, False):        "财多身弱，日主难以驾驭多路财星，财来财去，难以积累，宜量力而行。",
    },
    "财重身轻": {
        (True,  False): "财重身轻，日主略感吃力；{supp_str}补充财源，整体压力稍获缓解，借助辅助渠道可稳步积累。",
        (False, True):  "财重身轻，结构性承压；{risk_str}叠加拖拽，管理负担高，需大运扶身方能有效驾驭财运。",
        (True,  True):  "财重身轻，{supp_str}部分抵销{risk_str}的拖拽，整体净压力仍偏高，财运需精细管理方能维持稳定。",
        (False, False): "财重身轻，财务机会多但压力大，需比劫大运扶身方能稳固积累。",
    },
    "财身相停": {
        (True,  False): "财身相停，财运稳健；{supp_str}进一步充实来源，整体财运结构均衡向好。",
        (False, True):  "财身相停，平衡局势；但{risk_str}构成威胁，需防止既有平衡被破坏，积累成果须主动守护。",
        (True,  True):  "财身相停，{supp_str}提供额外支撑，同时{risk_str}带来风险，整体维持中性平衡，主动管理是关键。",
        (False, False): "财身相停，日主与财星维持动态平衡，稳步积累，财运稳健。",
    },
    "身强驾财": {
        (True,  False):        "身强驾财，日主强健；{supp_str}拓宽财路，多元财源叠加，财运能量充足，积累潜力强劲。",
        (False, True):         "身强驾财，日主具备驾驭能力；然{risk_str}形成消耗，宜主动管理财务漏洞，避免得而复失。",
        (True,  True,  True):  "身强驾财，{supp_str}拓宽财路；然{risk_str}形成消耗，外部支援与内部消耗并存，需主动防漏。",
        (True,  True,  False): "身强驾财，{supp_str}扩展财源；同时需管理{risk_str}的消耗，整体财运积极，主动防漏则更佳。",
        (True,  True):         "身强驾财，{supp_str}扩展财源；同时需管理{risk_str}的消耗，整体财运积极，主动防漏则更佳。",
        (False, False):        "身强驾财，日主元气充足，驾驭多路财星，财运丰盛，积累有力。",
    },
    "月令财格": {
        (True,  False): "{wealth_type_name}立格，{wealth_nature}得令居月柱本气，为命盘核心结构；{supp_str}进一步强化财源层次，格局纯正而多元。",
        (False, True):  "{wealth_type_name}立格，{wealth_nature}得令；然{risk_str}构成制约，需防格局被破，宜主动守护核心财运结构。",
        (True,  True):  "{wealth_type_name}立格，{wealth_nature}得令；{supp_str}强化财源，然{risk_str}构成制约，纯正格局中存变数，需主动管理。",
        (False, False): "{wealth_type_name}立格，{wealth_nature}得令居月柱本气，为命盘核心结构；财运走势明确，一生财运骨架扎实。",
    },
    "食伤生财": {
        (True,  False): "食伤生财格局成立，主动创造为财运骨架；{supp_str}拓宽来源，多渠道叠加，财运结构立体。",
        (False, True):  "食伤生财格局成立；然{risk_str}干扰产出链，财运发挥受制，需维护食伤畅通方能持续生财。",
        (True,  True):  "食伤生财格局成立；{supp_str}提供助力，然{risk_str}干扰产出链，主动创造与外部风险并存，需平衡发挥。",
        (False, False): "食伤生财格局成立，凭才能与产出积累财富，越努力越有财。",
    },
}
# Fallback templates for any future primary patterns added beyond the above
_SYNTH_DEFAULT: dict[tuple, str] = {
    (True,  False): "{anchor_name}格局确立；{supp_str}进一步强化财运基础，整体财运结构扎实。",
    (False, True):  "{anchor_name}格局确立；但{risk_str}需留意，财运发挥可能受到制约。",
    (True,  True):  "{anchor_name}格局确立；{supp_str}提供助力，同时{risk_str}带来挑战，整体财运正面但需主动管理。",
    (False, False): "{anchor_name}格局确立，财运结构有利，依托命盘固有优势稳步积累。",
}


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



def _get_branch_chars(bazi: dict) -> dict:
    """Returns {"年支": "丑", "月支": "亥", "日支": "辰", "时支": "申"}"""
    ba_zi = bazi["八字"]
    return {
        "年支": ba_zi["年柱"]["地支"],
        "月支": ba_zi["月柱"]["地支"],
        "日支": ba_zi["日柱"]["地支"],
        "时支": ba_zi["时柱"]["地支"],
    }


def _void_branch_positions(branch_chars: dict, xun_kong: dict) -> set:
    """
    Returns the set of branch position keys (e.g. {"月支", "年支"}) where that
    pillar's branch falls in its own 旬空, using per-pillar void calculation.
    Aligns with how the interaction system flags 旬空 (e.g. "月柱支落旬空").
    """
    voided = set()
    for branch_key, branch_char in branch_chars.items():
        pillar_key = branch_key[:1] + "柱"   # "月支" → "月柱"
        xun_kong_str = xun_kong.get("旬空", {}).get(pillar_key, {}).get("旬空", "")
        if branch_char in xun_kong_str:
            voided.add(branch_key)
    return voided


def _has_chong_xing_on_pillar(pillar_name: str, interactions: dict) -> bool:
    """Return True if the pillar has an active 六冲 or 三刑 (strength in ACTIVE_STRENGTHS)."""
    pillar_data = interactions["作用"]["柱位动态"].get(pillar_name, {})
    for tier_items in pillar_data.values():
        for item in tier_items:
            if item.get("类型") in CLASH_DISRUPT_TYPES:
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


# ── Natal pattern functions ───────────────────────────────────────────────────
# All return {"解读": str, "依据": str} if matched, else None.


# ── Tier 1a: Visibility ───────────────────────────────────────────────────────


def _pattern_hidden_wealth(wp: dict) -> dict | None:
    if not (len(wp["in_stems"]) == 0 and len(wp["in_branches"]) > 0):
        return None
    return {
        "解读": "财运真实存在但不对外显露 — 此人拥有财富却不外露，内敛型财格。",
        "依据": f"财星藏于地支: {wp['in_branches']}；天干无财星",
    }


def _pattern_visible_wealth(wp: dict) -> dict | None:
    if not (len(wp["in_stems"]) > 0 and len(wp["in_branches"]) == 0):
        return None
    return {
        "解读": "财星透出天干，财运外显 — 财务活动与资源对外可见，财来财往较明显。",
        "依据": f"财星透干: {wp['in_stems']}",
    }


def _pattern_mixed_visibility(wp: dict) -> dict | None:
    if not (len(wp["in_stems"]) > 0 and len(wp["in_branches"]) > 0):
        return None
    return {
        "解读": "财运兼具显隐两面 — 部分资源公开可见，另有私下积累，财格层次丰富。",
        "依据": f"透干财星: {wp['in_stems']}；藏支财星: {wp['in_branches']}",
    }


# ── Tier 1b: Quantity ─────────────────────────────────────────────────────────


def _pattern_single_wealth(wp: dict) -> dict | None:
    if len(wp["all"]) != 1:
        return None
    return {
        "解读": "财星单一集中 — 财运往往来自一技之长、一段关系或一个稳定来源，专注则成。",
        "依据": f"财星仅一处: {wp['all']}",
    }


def _pattern_dual_wealth(wp: dict) -> dict | None:
    if len(wp["all"]) != 2:
        return None
    return {
        "解读": "财星适中，两路财源 — 动静皆宜，财运稳健而不失弹性，多元收入有迹可循。",
        "依据": f"财星两处: {wp['all']}",
    }


def _pattern_abundant_wealth(wp: dict, ri_zhu: dict, wu_xing: dict, dm_elem: str) -> dict | None:
    """
    Four-tier spectrum for ≥3 wealth stars:
      财多身弱  — DM cannot hold wealth (富屋贫人)
      财重身轻  — DM under strain, manageable with supportive cycles (虽富亦劳)
      财身相停  — Balanced, steady accumulation (财运稳健)
      身强驾财  — DM commands wealth comfortably (财多不压身)
    """
    if len(wp["all"]) < 3:
        return None
    score       = ri_zhu["强弱分数"]
    wealth_elem = WEALTH_ELEMENT_MAP[dm_elem]
    wealth_tier = wu_xing["五行力量分析"][wealth_elem]["能级"]["名称"]
    dm_tier     = wu_xing["五行力量分析"][dm_elem]["能级"]["名称"]
    base        = f"财星共{len(wp['all'])}处: {wp['all']}"
    ev_elem     = f"财元素({wealth_elem}): {wealth_tier}；日主元素({dm_elem}): {dm_tier}；日主得分 {score}/5"

    # ── 财多身弱 ─────────────────────────────────────────────────────────────
    # P1: DM element is 极弱 — no root can compensate
    if dm_tier == "极弱":
        return {
            "格局名称": "财多身弱",
            "解读": "财星多见，财多身弱（富屋贫人）— 日主元气极度不足，财大压身，财来财去，难以积累属于自己的财富。",
            "依据": f"{base}；{ev_elem} → 日主极弱",
        }
    # P2: DM element 偏弱 AND roots cannot compensate (score ≤ 2)
    if dm_tier == "偏弱" and score <= 2:
        return {
            "格局名称": "财多身弱",
            "解读": "财星多见，财多身弱（富屋贫人）— 日主元素偏弱且根基薄，财务机会虽多，驾驭能力不足，易有财来财去之象。",
            "依据": f"{base}；{ev_elem} → 日主偏弱且根基薄",
        }
    # P3: DM balanced but wealth is overwhelming
    if dm_tier == "中和" and wealth_tier in WEALTH_DOM_EXCESSIVE:
        return {
            "格局名称": "财多身弱",
            "解读": "财星多见，财多身弱（富屋贫人）— 财元素极度旺盛，日主虽平衡仍难抵御，财大压身，财运机遇看似丰富，实则难以留存。",
            "依据": f"{base}；{ev_elem} → 财元素过旺压制日主",
        }

    # ── 财重身轻 ─────────────────────────────────────────────────────────────
    # P4: DM element 偏弱 but roots provide partial compensation (score ≥ 3)
    if dm_tier == "偏弱" and score >= 3:
        return {
            "格局名称": "财重身轻",
            "解读": "财星多见，财重身轻（虽富亦劳）— 日主元素偏弱，但根基尚存，勉力驾财。财务机会多但压力大，需比劫大运扶身方能稳固积累。",
            "依据": f"{base}；{ev_elem} → 偏弱元素但根基补偿",
        }
    # P5: DM balanced but wealth is notably heavier (偏旺), score cannot compensate
    if dm_tier == "中和" and wealth_tier == "偏旺" and score <= 3:
        return {
            "格局名称": "财重身轻",
            "解读": "财星多见，财重身轻（虽富亦劳）— 财元素偏旺，日主虽平衡但略显吃力，管理大量资源而劳心费神。需顺运支撑方可充分发挥财运潜力。",
            "依据": f"{base}；{ev_elem} → 财偏旺而日主根基未达抗衡",
        }
    # P6: DM balanced, wealth neutral, but roots are thin (score ≤ 1)
    if dm_tier == "中和" and wealth_tier in WEALTH_NEUTRAL_TIERS and score <= 1:
        return {
            "格局名称": "财重身轻",
            "解读": "财星多见，财重身轻（虽富亦劳）— 日主虽元素平衡，但根基结构薄弱，财务压力明显，需借比劫大运扶身以稳固财运。",
            "依据": f"{base}；{ev_elem} → 元素平衡但根基薄弱",
        }

    # ── 身强驾财 ─────────────────────────────────────────────────────────────
    # P7: DM element is strong — commands wealth at elemental level
    if dm_tier in WEALTH_DOM_DM_FLOOR:
        return {
            "格局名称": "身强驾财",
            "解读": "财星多见，身强驾财 — 日主元素强健，足以驾驭多路财星，财务机会多元，积累能力强，财多不压身。",
            "依据": f"{base}；{ev_elem} → 日主元素强势",
        }
    # P8: DM balanced vs 偏旺 wealth, but score is maximum — roots override wealth heaviness
    if dm_tier == "中和" and wealth_tier == "偏旺" and score == 5:
        return {
            "格局名称": "身强驾财",
            "解读": "财星多见，身强驾财 — 日主根基极强，即使面对偏旺财力亦能从容驾驭，财运丰盛，积累有力。",
            "依据": f"{base}；{ev_elem} → 根基极强逆势驾财",
        }
    # P9: DM balanced vs neutral wealth, strong roots
    if dm_tier == "中和" and wealth_tier in WEALTH_NEUTRAL_TIERS and score >= 4:
        return {
            "格局名称": "身强驾财",
            "解读": "财星多见，身强驾财 — 日主根基强健，财身比例协调，能把握并积累多元财运机会，财来能留。",
            "依据": f"{base}；{ev_elem} → 根基强健驾财有力",
        }

    # ── 财身相停 ─────────────────────────────────────────────────────────────
    # P10: DM balanced vs 偏旺 wealth, strong roots create functional balance
    if dm_tier == "中和" and wealth_tier == "偏旺" and score == 4:
        return {
            "格局名称": "财身相停",
            "解读": "财身相停 — 日主根基强健，足以平衡偏旺的财力，财运稳健，积累有序，可把握多元机会。",
            "依据": f"{base}；{ev_elem} → 强根平衡偏旺财力",
        }
    # P11: DM balanced, wealth balanced, score moderate — strained variant
    if dm_tier == "中和" and wealth_tier == "中和" and score == 2:
        return {
            "格局名称": "财身相停",
            "解读": "财身相停 — 财运稳健，但根基尚浅，宜稳中求进，避免过度冒险分散财力。",
            "依据": f"{base}；{ev_elem} → 财身均衡但根基尚浅",
        }
    # P12–13: DM balanced, neutral wealth (中和 or 偏弱), score 2–3
    return {
        "格局名称": "财身相停",
        "解读": "财身相停 — 财运稳健，积累有序，日主与财星维持动态平衡，稳步向上。",
        "依据": f"{base}；{ev_elem} → 财身均衡",
    }


# ── Tier 1c: Source / Origin ──────────────────────────────────────────────────


def _pattern_inherited_wealth(wp: dict) -> dict | None:
    year_hits = [p for p in wp["all"] if "年" in p]
    if not year_hits:
        return None
    return {
        "解读": "家族资源或遗产在财富基础中占重要地位 — 年柱财星显示祖业或家庭财力的支撑。",
        "依据": f"年柱财星: {year_hits}",
    }


def _pattern_spousal_wealth(wp: dict) -> dict | None:
    day_hits = [p for p in wp["in_branches"] if "日支" in p]
    if not day_hits:
        return None
    return {
        "解读": "财与配偶或亲密合伙人紧密相连 — 婚姻或合作关系带来财务助力。",
        "依据": f"日支藏财: {day_hits}",
    }


def _pattern_month_pillar_wealth(shi_shen: dict) -> dict | None:
    """
    月令财格: month branch 本气 is a wealth star — the chart's primary structural classification.
    This is the strongest single natal wealth signal in classical BaZi.
    """
    month_benzhi = shi_shen.get("月柱", {}).get("地支十神", {}).get("本气")
    if month_benzhi not in WEALTH_STARS:
        return None
    wealth_type = "正财格" if month_benzhi == "正财" else "偏财格"
    return {
        "解读": f"命盘以{wealth_type}立格 — 月令本气为财星，财运为命盘核心结构，财星得时得令，一生财运走向明确。",
        "依据": f"月柱地支本气: {month_benzhi}",
    }


def _pattern_wealth_arrives_late(wp: dict) -> dict | None:
    if not (len(wp["all"]) > 0 and all("时" in pos for pos in wp["all"])):
        return None
    return {
        "解读": "命盘财星集中于时柱，原局结构偏晚发 — 早年财运较淡，财务基础随年岁渐长而稳固。若大运财运动态中有早期激活或开库，则可提前进入财运窗口。",
        "依据": f"财星仅见于时柱: {wp['all']}",
    }


def _pattern_self_generated_wealth(shi_shen: dict, wp: dict, ri_zhu: dict, wu_xing: dict, dm_elem: str) -> dict | None:
    """
    Fires when no wealth stars exist but a strong 食伤 channel is present.
    Verdict is graded by DM strength — covers weak DM (channel exists but laboured)
    through strong DM (sustained conversion of output into wealth).
    """
    if len(wp["all"]) > 0:
        return None
    has_food = any(
        shi_shen.get(pl, {}).get("天干十神") in FOOD_GOD_HURT_OFFICER
        or any(shi_shen.get(pl, {}).get("地支十神", {}).get(t) in FOOD_GOD_HURT_OFFICER for t in BRANCH_TIERS)
        for pl in PILLARS
    )
    if not has_food:
        return None
    food_elem = FOOD_GOD_HURT_OFFICER_ELEMENT_MAP[dm_elem]
    food_tier = wu_xing["五行力量分析"][food_elem]["能级"]["名称"]
    if food_tier not in FOOD_GOD_HURT_OFFICER_STRONG_ENOUGH:
        return None
    score = ri_zhu["强弱分数"]
    if score >= 3:
        jiedu = "财靠自力，食伤化财 — 强势日主驾驭食伤，将才华与输出持续转化为财富。"
    elif score == 2:
        jiedu = "财可自力而成，但需努力坚持 — 中等日主借食伤生财，顺运时成效尤为显著。"
    else:
        jiedu = "食伤生财渠道存在，但日主偏弱 — 创财有路，守财难，需借助外力与顺运方可有效积累。"
    return {
        "解读": jiedu,
        "依据": f"无财星；食伤({food_elem})旺度: {food_tier}；日主得分 {score}/5",
    }


# ── Tier 2: Structural Formations ────────────────────────────────────────────


def _pattern_virtual_bureau(wu_xing: dict, dm_elem: str) -> dict | None:
    """
    Detects a structural elemental formation (共拱/三合/三会) of the wealth element.
    Uses WEALTH_ELEMENT_MAP because this pattern concerns formation energy, not explicit stars.
    Filters to wealth-element formations first, then picks the strongest among them.
    """
    wealth_elem = WEALTH_ELEMENT_MAP.get(dm_elem)
    combos = wu_xing.get("组合加成", [])
    wealth_combos = [
        c for c in combos
        if c.get("元素") == wealth_elem and c.get("强度") in {"显著影响", "强势主流"}
    ]
    if not wealth_combos:
        return None
    top = min(wealth_combos, key=lambda c: STRENGTH_RANK.index(c["强度"]))
    return {
        "解读": "命盘形成暗财局 — 财元素在结构上持续自我补充，财运如暗流涌动，源源不断。",
        "依据": f"{top.get('类型')} → {top.get('元素')} [{top.get('强度')}]",
    }


def _pattern_wealth_supported_by_yin(shi_shen: dict, wp: dict, ri_zhu: dict, wu_xing: dict, dm_elem: str) -> dict | None:
    if not wp["all"]:
        return None
    has_yin = any(
        shi_shen.get(pl, {}).get("天干十神") in YIN_STARS
        or any(shi_shen.get(pl, {}).get("地支十神", {}).get(t) in YIN_STARS for t in BRANCH_TIERS)
        for pl in PILLARS
    )
    if not has_yin:
        return None
    yin_elem = YIN_ELEMENT_MAP[dm_elem]
    yin_tier = wu_xing["五行力量分析"][yin_elem]["能级"]["名称"]
    # Floor: 印星 element too weak to provide meaningful support
    if yin_tier not in YIN_STRONG_ENOUGH:
        return None
    # 印多埋财: fully excessive 印星 smothers 食伤 and buries wealth
    if yin_tier in YIN_EXCESSIVE:
        return None
    score = ri_zhu["强弱分数"]
    if score <= 1:
        return None
    # 偏旺 印星 — supportive but warrants a cautionary note
    if yin_tier == "偏旺":
        jiedu = "印星偏强，财运有一定保障，但须留意印星过旺时可能抑制食伤生财渠道 — 大运若再逢印，宜调整策略以免财路受阻。"
    elif score >= 3:
        jiedu = "财运有良好保障 — 强势日主配合印星，财富稳健积累，有家庭、教育或贵人撑腰。"
    else:
        jiedu = "财运有一定保障 — 印星提供安全网，但财务稳定性仍随运程起伏。"
    return {
        "解读": jiedu,
        "依据": f"财星存在；印星({yin_elem})旺度: {yin_tier}；日主得分 {score}/5",
    }


def _pattern_rivals_take_wealth(wp: dict, wu_xing: dict, ri_zhu: dict, dm_elem: str) -> dict | None:
    """
    比劫夺财: wealth exists but the 比劫 element (same as DM) is excessively strong,
    competing for and diverting the DM's wealth. Elemental-strength version of rival
    interference — distinct from _pattern_wealth_combined_away (which requires 天干合).
    """
    if not wp["all"]:
        return None
    bi_jie_tier = wu_xing["五行力量分析"][dm_elem]["能级"]["名称"]
    if bi_jie_tier not in {"偏旺", "极旺", "极亢"}:
        return None
    score = ri_zhu["强弱分数"]
    if score >= 3:
        jiedu = "比劫元素旺盛，日主强势尚可掌控财星 — 财运竞争激烈，善用合作与分工可化解。"
    elif score == 2:
        jiedu = "比劫偏旺，财运易受同侪分流 — 合伙需谨慎，独立经营或专注特定财源较宜。"
    else:
        jiedu = "比劫旺而日主弱，财易被他人夺取（财多身弱的竞争面）— 不宜轻易合伙或公开财务状况。"
    return {
        "解读": jiedu,
        "依据": f"比劫({dm_elem})旺度: {bi_jie_tier}；财星: {wp['all']}；日主得分 {score}/5",
    }


def _pattern_wealth_leaked(wp: dict, wu_xing: dict, ri_zhu: dict, dm_elem: str) -> dict | None:
    """
    Fires when wealth stars exist but the food/hurt element is excessively strong,
    overwhelming the DM and leaking wealth outward before it can be retained.
    Classical example: 金多水浊 (too much metal muddies the water) for a 土 DM.
    Symmetric counterpart to the 印多埋财 gate in _pattern_wealth_supported_by_yin.
    DM strength grading: a strong DM can better withstand excessive 食伤 drain.
    """
    if not wp["all"]:
        return None
    food_elem = FOOD_GOD_HURT_OFFICER_ELEMENT_MAP[dm_elem]
    food_tier = wu_xing["五行力量分析"][food_elem]["能级"]["名称"]
    if food_tier not in FOOD_GOD_HURT_OFFICER_EXCESSIVE:
        return None
    score = ri_zhu["强弱分数"]
    if score >= 3:
        jiedu = f"食伤({food_elem})过旺，日主虽强尚可承受，但持续耗泄仍会分散财气 — 宜聚焦核心财源，避免过度输出才华而忽略积累。"
    elif score == 2:
        jiedu = f"食伤({food_elem})过旺，日主中等，泄财风险明显 — 财到手难留，大运印星入局可抑食伤，方能蓄财。"
    else:
        jiedu = f"食伤({food_elem})过旺而日主弱，泄财严重 — 财星虽在却持续外流，不宜轻易消耗精力，需印星或比劫大运来稳固根基。"
    return {
        "解读": jiedu,
        "依据": f"食伤({food_elem})旺度: {food_tier}；财星: {wp['all']}；日主得分 {score}/5",
    }


def _pattern_wealth_void(wp: dict, xun_kong: dict, branch_chars: dict) -> dict | None:
    """
    财星落空: a branch position carrying a wealth star falls in its own pillar's 旬空.
    Uses per-pillar void calculation to align with the interaction system.
    """
    if not wp["in_branches"]:
        return None
    void_positions = _void_branch_positions(branch_chars, xun_kong)
    voided = [pos for pos in wp["in_branches"] if pos[:2] in void_positions]
    if not voided:
        return None
    return {
        "解读": "财星落旬空 — 财星虽存命盘，却地支落空，财运底气不足，财来易散，难以长期积累。",
        "依据": f"落空财星: {voided}",
    }


# ── Tier 3: Natal Interaction Patterns ───────────────────────────────────────


def _pattern_tomb_opened(tomb_list: list, interactions: dict) -> dict | None:
    opened = [
        entry for entry in tomb_list
        if _has_chong_xing_on_pillar(BRANCH_LABEL_TO_PILLAR[entry[:2]], interactions)
    ]
    if not opened:
        return None
    return {
        "解读": "财库地支受到命盘六冲或三刑触发 — 封印已开，财运可触及，无需等待外部时机。",
        "依据": f"已开财库: {opened}",
    }


def _pattern_tomb_closed(tomb_list: list, interactions: dict) -> dict | None:
    closed = [
        entry for entry in tomb_list
        if not _has_chong_xing_on_pillar(BRANCH_LABEL_TO_PILLAR[entry[:2]], interactions)
    ]
    if not closed:
        return None
    return {
        "解读": "财藏于库中，命盘无原局触发 — 财运潜力真实存在，但需大运或流年开库方可动用。详见大运财运动态。",
        "依据": f"未开财库: {closed}",
    }


def _pattern_tomb_void(tomb_list: list, xun_kong: dict, branch_chars: dict) -> dict | None:
    """
    财库落空: a tomb branch containing a wealth star falls in its own pillar's 旬空.
    Uses per-pillar void calculation to align with the interaction system.
    """
    void_positions = _void_branch_positions(branch_chars, xun_kong)
    voided = [entry for entry in tomb_list if entry[:2] in void_positions]
    if not voided:
        return None
    return {
        "解读": "财库落旬空 — 财星藏库但库位落空，财库形同虚设，即使大运开库，财也难以实现。",
        "依据": f"落空财库: {voided}",
    }


def _pattern_wealth_combined_with_dm(shi_shen: dict, interactions: dict) -> dict | None:
    """
    天干合 where the Day Master stem combines with a 正财/偏财 stem.
    Scans _raw_priority_list so that 天干合 recorded on either pillar's side is found.
    """
    combined = []
    for item in interactions.get("_raw_priority_list", []):
        if item.get("类型") != "天干合" or item.get("强度") not in ACTIVE_STRENGTHS:
            continue
        detail = item.get("组合明细", {})
        if "日柱" not in detail:
            continue
        for pillar, stem in detail.items():
            if pillar != "日柱":
                ten_god = shi_shen.get(pillar, {}).get("天干十神", "")
                if ten_god in WEALTH_STARS:
                    combined.append(f"{pillar}({stem}/{ten_god})")
    if not combined:
        return None
    return {
        "解读": "日主天干直接与财星天干相合 — 财运通过人际关系、合作或时机而来，非单靠努力所得。",
        "依据": f"日主合财: {combined}",
    }


def _pattern_wealth_combined_away(shi_shen: dict, interactions: dict) -> dict | None:
    """
    天干合 where a wealth star combines with a non-DM stem.
    Classified by the other party's ten-god:
      比劫  → wealth competed/shared away (negative)
      官杀  → wealth channeled into authority/career (mixed)
      other → wealth star occupied/tied up
    """
    combined = []
    for item in interactions.get("_raw_priority_list", []):
        if item.get("类型") != "天干合" or item.get("强度") not in ACTIVE_STRENGTHS:
            continue
        detail = item.get("组合明细", {})
        if "日柱" in detail:          # DM involvement handled by _pattern_wealth_combined_with_dm
            continue
        pillars = list(detail.keys())
        if len(pillars) != 2:
            continue
        wealth_pillar = next((p for p in pillars if shi_shen.get(p, {}).get("天干十神") in WEALTH_STARS), None)
        if wealth_pillar is None:
            continue
        other_pillar = next(p for p in pillars if p != wealth_pillar)
        other_ten_god = shi_shen.get(other_pillar, {}).get("天干十神", "")
        combined.append((wealth_pillar, other_pillar, other_ten_god))

    if not combined:
        return None

    all_ten_gods = [c[2] for c in combined]
    has_rival    = any(tg in _BI_JIE_STARS    for tg in all_ten_gods)
    has_official = any(tg in _GUAN_SHA_STARS for tg in all_ten_gods)

    if has_rival:
        jiedu = "财星与比劫天干相合 — 财运受同侪竞争或合伙分成牵制，独占财富的能力受限。"
    elif has_official:
        jiedu = "财星与官杀天干相合 — 财与仕途职权挂钩，财运往往通过职位晋升或权威背书而来，非纯商业财。"
    else:
        jiedu = "财星天干被合占 — 财星被其他星系牵引，财的流动性受限，难以完全为己所用。"

    details = [
        f"{w_pillar}财星 合 {op}({tg})" for w_pillar, op, tg in combined
    ]
    return {
        "解读": jiedu,
        "依据": f"财星被合: {'; '.join(details)}",
    }


def _pattern_wealth_clashed(shi_shen: dict, interactions: dict, wp: dict, ri_zhu: dict) -> dict | None:
    """A branch carrying a wealth star has active 六冲 or 三刑 in the natal chart."""
    clashed_detail = {}   # pos → list of interaction types
    clash_types = {"六冲"} | SAN_XING_TYPES
    for pos in wp["in_branches"]:
        pillar = BRANCH_LABEL_TO_PILLAR[pos[:2]]
        pillar_data = interactions["作用"]["柱位动态"].get(pillar, {})
        types_found = []
        for tier_items in pillar_data.values():
            for item in tier_items:
                if item.get("类型") in clash_types and item.get("强度") in ACTIVE_STRENGTHS:
                    types_found.append(item["类型"])
        if types_found:
            clashed_detail[pos] = types_found

    if not clashed_detail:
        return None

    score = ri_zhu["强弱分数"]
    if score >= 3:
        jiedu = "财星受命盘冲克，但日主够强，财务挫折可恢复 — 波折不影响整体财富积累。若大运财运动态中同柱出现激活（天干合或六合），冲力可被化解。"
    elif score == 2:
        jiedu = "财星受冲，日主中等，财务稳定性一般 — 需借助外部支撑与顺运方可守财。若大运财运动态中同柱出现激活，冲力可被阶段性化解。"
    else:
        jiedu = "财星受冲且日主偏弱，财务不稳属结构性问题 — 聚财难，守财更难。若大运财运动态中同柱出现激活，可争取阶段性财运窗口。"

    evidence_parts = [f"{pos}({'/'.join(types)})" for pos, types in clashed_detail.items()]
    return {
        "解读": jiedu,
        "依据": f"财星受冲地支: {evidence_parts}；日主得分 {score}/5",
    }


# ── Tier 4: Cycle-Relative Timing ────────────────────────────────────────────


def _pattern_wealth_activated_now(da_yun: dict, wp: dict) -> dict | None:
    decade = _get_current_decade(da_yun)
    if decade is None or not _decade_has_wealth(decade):
        return None
    return {
        "解读": "当前大运运柱带财星，财运大运正当其时 — 此为财运增长与机遇的窗口期。",
        "依据": f"当前大运 {decade.get('周期')} 运柱含财星",
    }


def _pattern_wealth_dormant_now(da_yun: dict, wp: dict) -> dict | None:
    if not wp["all"]:
        return None
    decade = _get_current_decade(da_yun)
    if decade is None or _decade_has_wealth(decade):
        return None
    return {
        "解读": "命盘有财星但当前大运未加持 — 财运可期但需主动经营，非自动丰盛期。",
        "依据": f"命盘财星: {wp['all']}；当前大运 {decade.get('周期')} 运柱无财星",
    }


# ── Cycle event helpers ───────────────────────────────────────────────────────


def _cycle_tomb_events(
    sealed_tomb_pillars: set,
    zhu_wei: dict,
) -> list[dict]:
    """
    Detects 开库 effects: cycle 六冲 or 开库 on a sealed natal tomb pillar.
    Takes priority — a sealed tomb hit by cycle 六冲 is classified here, not as 冲破.
    """
    effects = []
    for pillar in sealed_tomb_pillars:
        pillar_data = zhu_wei.get(pillar, {})
        for tier_items in pillar_data.values():
            for item in tier_items:
                itype = item.get("类型", "")
                strength = item.get("强度", "")
                if strength not in ACTIVE_STRENGTHS:
                    continue
                if itype in {"六冲", "开库"}:
                    effects.append({
                        "作用类型": "开库",
                        "互动类型": itype,
                        "涉及柱": pillar,
                        "强度": strength,
                        "解读": f"大运支与{pillar}财库形成{itype}，封存财运得以开启，资源可触及",
                    })
    return effects


def _cycle_activating_events(
    stem_wealth_pillars: set,
    branch_wealth_pillars: set,
    zhu_wei: dict,
) -> list[dict]:
    """
    Detects 激活 effects:
      - 天干合 on a natal stem-wealth pillar
      - 六合/三合/三会 on a natal branch-wealth pillar
    """
    effects = []
    for pillar in stem_wealth_pillars:
        pillar_data = zhu_wei.get(pillar, {})
        for tier_items in pillar_data.values():
            for item in tier_items:
                if item.get("类型") == "天干合" and item.get("强度") in ACTIVE_STRENGTHS:
                    effects.append({
                        "作用类型": "激活",
                        "互动类型": "天干合",
                        "涉及柱": pillar,
                        "强度": item["强度"],
                        "解读": f"大运天干与{pillar}财星天干相合，财星被合出，财运获得激活",
                    })
    for pillar in branch_wealth_pillars:
        pillar_data = zhu_wei.get(pillar, {})
        for tier_items in pillar_data.values():
            for item in tier_items:
                itype = item.get("类型", "")
                if itype in {"六合", "三合", "三会"} and item.get("强度") in ACTIVE_STRENGTHS:
                    effects.append({
                        "作用类型": "激活",
                        "互动类型": itype,
                        "涉及柱": pillar,
                        "强度": item["强度"],
                        "解读": f"大运支与{pillar}财星地支形成{itype}，隐藏财运得到激发",
                    })
    return effects


def _cycle_disrupting_events(
    all_wealth_pillars: set,
    sealed_tomb_pillars: set,
    zhu_wei: dict,
) -> list[dict]:
    """
    Detects 冲破 effects: cycle 六冲 or 三刑 on a non-tomb wealth pillar.
    Excludes sealed tomb pillars — those are handled by _cycle_tomb_events.
    """
    effects = []
    for pillar in all_wealth_pillars - sealed_tomb_pillars:
        pillar_data = zhu_wei.get(pillar, {})
        for tier_items in pillar_data.values():
            for item in tier_items:
                itype = item.get("类型", "")
                if itype in CLASH_DISRUPT_TYPES and item.get("强度") in ACTIVE_STRENGTHS:
                    effects.append({
                        "作用类型": "冲破",
                        "互动类型": itype,
                        "涉及柱": pillar,
                        "强度": item["强度"],
                        "解读": f"大运{itype}{pillar}财星，财运受冲，财务波动或被迫重分配",
                    })
    return effects


def _cycle_food_events(cycle: dict, dm_elem: str) -> list[dict]:
    """
    Detects 食伤生财: cycle 运柱 carries 食伤 star in stem or any branch hidden tier,
    AND the combined natal+cycle food element meets the FOOD_GOD_HURT_OFFICER_STRONG_ENOUGH threshold.
    Fires regardless of whether natal wealth stars exist.
    """
    run_zhu_shi_shen = cycle.get("运柱", {}).get("十神", {})

    stem_food = run_zhu_shi_shen.get("天干", {}).get("十神")
    stem_food = stem_food if stem_food in FOOD_GOD_HURT_OFFICER else None

    branch_food = [
        (tier, run_zhu_shi_shen[tier]["十神"])
        for tier in BRANCH_TIERS
        if isinstance(run_zhu_shi_shen.get(tier), dict)
        and run_zhu_shi_shen[tier].get("十神") in FOOD_GOD_HURT_OFFICER
    ]

    if not stem_food and not branch_food:
        return []

    # Gate: check combined natal+cycle food element strength
    food_elem = FOOD_GOD_HURT_OFFICER_ELEMENT_MAP[dm_elem]
    wu_xing = cycle.get("五行力量")
    if not isinstance(wu_xing, dict):
        return []
    food_tier = wu_xing.get(food_elem, {}).get("能级", {}).get("名称", "")
    if food_tier not in FOOD_GOD_HURT_OFFICER_STRONG_ENOUGH:
        return []

    # Build location-aware 解读
    parts = []
    if stem_food:
        if stem_food == "食神":
            parts.append("运柱天干食神透出，才华外显，生财渠道清晰有力")
        else:
            parts.append("运柱天干伤官透出，突破性输出旺盛，生财积极但需留意官运影响")
    for tier, star in branch_food:
        tier_desc = {"本气": "本气（力场最强）", "中气": "中气（力场中等）", "余气": "余气（力场较薄）"}.get(tier, tier)
        if star == "食神":
            parts.append(f"运柱地支藏食神（{tier_desc}），生财渠道隐而有厚度")
        else:
            parts.append(f"运柱地支藏伤官（{tier_desc}），创意输出潜藏，生财动能内敛")

    parts.append(f"食伤元素（{food_elem}）整体旺度{food_tier}，间接生财能力显著")
    jiedu = "；".join(parts)

    return [{
        "作用类型": "食伤生财",
        "互动类型": "食伤",
        "涉及柱": None,
        "强度": "显著影响",
        "解读": jiedu,
    }]


def _cycle_void_events(cycle: dict) -> list[dict]:
    """
    Detects 运星落空: the cycle's 运柱 branch falls in its own 旬空.
    Only branch-resident wealth or 食伤 is affected — stem stars are not subject to 旬空.
    """
    run_zhu = cycle.get("运柱", {})
    branch_char = run_zhu.get("地支", "")
    xun_kong_str = run_zhu.get("旬空", "")
    if not branch_char or branch_char not in xun_kong_str:
        return []

    shi_shen = run_zhu.get("十神", {})
    affected = [
        tier_data["十神"]
        for tier in BRANCH_TIERS
        if isinstance((tier_data := shi_shen.get(tier)), dict)
        and tier_data.get("十神") in WEALTH_STARS | FOOD_GOD_HURT_OFFICER
    ]
    if not affected:
        return []

    star_str = "、".join(affected)
    return [{
        "作用类型": "运星落空",
        "互动类型": "旬空",
        "涉及柱": None,
        "强度": "中等衰减",
        "解读": f"运柱地支{branch_char}落旬空，支中{star_str}力场虚浮 — 此运财运看似存在，实则底气不足，财来易散。",
    }]


def _get_cycle_wealth_events(
    shi_shen: dict,
    wp: dict,
    bazi: dict,
    da_yun: dict,
    natal_interactions: dict,
    dm_elem: str,
) -> list[dict]:
    """
    Orchestrator: scans all 大运 cycles and collects wealth-relevant events.

    Delegates to five focused helpers:
      _cycle_tomb_events       — 开库 (sealed tomb triggered by cycle)
      _cycle_activating_events — 激活 (cycle 合 on wealth pillar)
      _cycle_disrupting_events — 冲破 (cycle 冲/刑 on non-tomb wealth pillar)
      _cycle_food_events       — 食伤生财 (cycle carries 食伤)
      _cycle_void_events       — 运星落空 (cycle branch falls in 旬空)

    Returns only cycles with ≥1 effect, ordered past → current → future.
    """
    today_year = date.today().year

    # Precompute wealth-bearing pillar sets
    stem_wealth_pillars = {pos[0] + "柱" for pos in wp["in_stems"]}
    branch_wealth_pillars = {BRANCH_LABEL_TO_PILLAR[pos[:2]] for pos in wp["in_branches"]}
    all_wealth_pillars = stem_wealth_pillars | branch_wealth_pillars

    # Sealed tomb pillars: wealth in tomb with no natal trigger
    branch_chars = _get_branch_chars(bazi)
    tomb_list = _wealth_in_tomb_list(shi_shen, branch_chars)
    sealed_tomb_pillars = {
        BRANCH_LABEL_TO_PILLAR[entry[:2]] for entry in tomb_list
        if not _has_chong_xing_on_pillar(BRANCH_LABEL_TO_PILLAR[entry[:2]], natal_interactions)
    }

    cycles = da_yun.get("大运", {}).get("大运周期", [])[1:]  # skip index 0 placeholder
    events = []

    for cycle in cycles:
        zuo_yong = cycle.get("作用", {})
        if not isinstance(zuo_yong, dict):
            continue  # "未行大运" string placeholder

        if cycle.get("当运"):
            zhuangtai = "当运"
        elif cycle.get("结束年份", 9999) < today_year:
            zhuangtai = "已过"
        else:
            zhuangtai = "未来"

        zhu_wei = zuo_yong.get("柱位动态", {})

        effects = (
            _cycle_tomb_events(sealed_tomb_pillars, zhu_wei)
            + _cycle_activating_events(stem_wealth_pillars, branch_wealth_pillars, zhu_wei)
            + _cycle_disrupting_events(all_wealth_pillars, sealed_tomb_pillars, zhu_wei)
            + _cycle_food_events(cycle, dm_elem)
            + _cycle_void_events(cycle)
        )

        if effects:
            events.append({
                "大运": cycle.get("周期", ""),
                "状态": zhuangtai,
                "财运作用": effects,
            })

    return events


# ── Synthesis header ──────────────────────────────────────────────────────────


def _synthesize_wealth_patterns(patterns: list[dict]) -> dict:
    """
    Produces a net assessment header from the fired pattern list.

    Scans patterns by 格局编号 role:
      PRIMARY_PATTERNS    → anchor (first hit sets the narrative frame)
      SUPPLEMENTARY_IDS   → buffers / additional sources
      RISK_IDS            → active drags / disruptions

    Returns:
        {
            "主格局":   str | None,   # anchor 格局名称 (tier label for abundant_wealth)
            "辅助来源": list[str],    # 格局名称 of supplementary patterns that fired
            "风险因素": list[str],    # 格局名称 of risk patterns that fired
            "综合解读": str,          # 1–2 sentence net assessment
        }
    """
    # Step 1 — find anchor (first primary pattern sets the narrative frame)
    anchor_name = None
    anchor_pid  = None
    for p in patterns:
        if p["格局编号"] in PRIMARY_PATTERNS:
            anchor_name = p["格局名称"]
            anchor_pid  = p["格局编号"]
            break

    # Step 2 — classify supplementary and risk
    # Non-anchor primary patterns go into 辅助来源 — structurally significant even without anchor slot.
    supplementary_names = [
        p["格局名称"] for p in patterns
        if p["格局编号"] in SUPPLEMENTARY_IDS
        or (p["格局编号"] in PRIMARY_PATTERNS and p["格局编号"] != anchor_pid)
    ]
    risk_names   = [p["格局名称"] for p in patterns if p["格局编号"] in RISK_IDS]
    has_supp     = bool(supplementary_names)
    has_risk     = bool(risk_names)
    has_external = bool(set(supplementary_names) & _EXTERNAL_SUPP_NAMES)

    # Step 3 — build interpolation context
    ctx: dict[str, str] = {
        "supp_str":         "、".join(supplementary_names),
        "risk_str":         "、".join(risk_names),
        "anchor_name":      anchor_name or "",
        "wealth_type_name": "",
        "wealth_nature":    "",
    }
    if anchor_pid == "month_pillar_wealth":
        mpw = next(p for p in patterns if p["格局编号"] == "month_pillar_wealth")
        is_zhengcai              = "正财" in mpw.get("依据", "")
        ctx["wealth_type_name"]  = "正财格" if is_zhengcai else "偏财格"
        ctx["wealth_nature"]     = "正财"   if is_zhengcai else "偏财"

    # Step 4 — look up template (3-tuple → 2-tuple fallback) and interpolate
    templates = _SYNTH.get(anchor_name, _SYNTH_DEFAULT)
    template  = (
        templates.get((has_supp, has_risk, has_external))
        or templates.get((has_supp, has_risk), "")
    )
    return {
        "主格局":   anchor_name,
        "辅助来源": supplementary_names,
        "风险因素": risk_names,
        "综合解读": template.format(**ctx),
    }


# ── Public API ────────────────────────────────────────────────────────────────


def extract_wealth_insights(raw_data: dict) -> dict:
    """
    Pre-compute structural wealth patterns from raw aggregator output.

    Args:
        raw_data: Output of AstroDataAggregator.collect_data()

    Returns:
        {
            "命盘财运格局": list of matched pattern dicts (格局编号, 格局名称, 解读, 依据),
            "大运财运动态": list of cycle event dicts (大运, 状态, 财运作用),
            "无格局提示":   str | None — fallback text when no natal pattern matched
        }
    """
    shi_shen = raw_data["shi_shen"]["十神"]
    ri_zhu = raw_data["day_master"]["日主"]
    bazi = raw_data["bazi"]
    wu_xing = raw_data["wu_xing"]["五行力量"]
    da_yun = raw_data["da_yun"]
    interactions = raw_data["interactions"]
    xun_kong = raw_data["xun_kong"]
    dm_elem = ri_zhu["五行"]

    wp = _get_wealth_positions(shi_shen)
    branch_chars = _get_branch_chars(bazi)
    tomb_list = _wealth_in_tomb_list(shi_shen, branch_chars)

    candidates = [
        # Tier 1a — Visibility
        ("hidden_wealth",           "财星藏支",      _pattern_hidden_wealth(wp)),
        ("visible_wealth",          "财星透干",      _pattern_visible_wealth(wp)),
        ("mixed_visibility",        "财星半显半隐",   _pattern_mixed_visibility(wp)),
        # Tier 1b — Quantity
        ("single_wealth",           "财星独现",      _pattern_single_wealth(wp)),
        ("dual_wealth",             "财星适中",      _pattern_dual_wealth(wp)),
        ("abundant_wealth",         "财星多见",      _pattern_abundant_wealth(wp, ri_zhu, wu_xing, dm_elem)),
        # Tier 1c — Source / Origin
        ("inherited_wealth",        "祖业财星",      _pattern_inherited_wealth(wp)),
        ("spousal_wealth",          "配偶财星",      _pattern_spousal_wealth(wp)),
        ("month_pillar_wealth",     "月令财格",      _pattern_month_pillar_wealth(shi_shen)),
        ("wealth_arrives_late",     "时上财星",      _pattern_wealth_arrives_late(wp)),
        ("self_generated_wealth",   "食伤生财",      _pattern_self_generated_wealth(shi_shen, wp, ri_zhu, wu_xing, dm_elem)),
        # Tier 2 — Structural Formations
        ("virtual_bureau",          "暗财局",        _pattern_virtual_bureau(wu_xing, dm_elem)),
        ("wealth_supported_by_yin", "印财并存",      _pattern_wealth_supported_by_yin(shi_shen, wp, ri_zhu, wu_xing, dm_elem)),
        ("wealth_leaked",           "食伤泄财",      _pattern_wealth_leaked(wp, wu_xing, ri_zhu, dm_elem)),
        ("rivals_take_wealth",      "比劫夺财",      _pattern_rivals_take_wealth(wp, wu_xing, ri_zhu, dm_elem)),
        ("wealth_void",             "财星落空",      _pattern_wealth_void(wp, xun_kong, branch_chars)),
        # Tier 3 — Natal Interaction Patterns
        ("tomb_opened",             "开库",          _pattern_tomb_opened(tomb_list, interactions)),
        ("tomb_closed",             "财库未冲",      _pattern_tomb_closed(tomb_list, interactions)),
        ("tomb_void",               "财库落空",      _pattern_tomb_void(tomb_list, xun_kong, branch_chars)),
        ("wealth_combined_with_dm", "日主合财",      _pattern_wealth_combined_with_dm(shi_shen, interactions)),
        ("wealth_combined_away",    "财星被合",      _pattern_wealth_combined_away(shi_shen, interactions)),
        ("wealth_clashed",          "财星受冲",      _pattern_wealth_clashed(shi_shen, interactions, wp, ri_zhu)),
        # Tier 4 — Cycle-Relative Timing
        ("wealth_activated_now",    "当运财星",      _pattern_wealth_activated_now(da_yun, wp)),
        ("wealth_dormant_now",      "财星休眠",      _pattern_wealth_dormant_now(da_yun, wp)),
    ]

    patterns = [
        {"格局编号": pid, "格局名称": name, **result}
        for pid, name, result in candidates
        if result is not None
    ]

    cycle_wealth_events = _get_cycle_wealth_events(
        shi_shen, wp, bazi, da_yun, interactions, dm_elem
    )

    return {
        "财运综合评估": _synthesize_wealth_patterns(patterns),
        "命盘财运格局": patterns,
        "大运财运动态": cycle_wealth_events,
        "无格局提示": (
            "财运结构特征不显著，财运走向主要依赖大运与自身努力。"
            if not patterns
            else None
        ),
    }



# ============================================================================
# EXECUTION
# python -m src.astronomer_calculations.interpretive_insights_wealth
# ============================================================================

if __name__ == "__main__":
    import json
    from datetime import datetime as dt
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
    from src.services.astronomer_data_aggregator import AstroDataAggregator
    from src.utils.logging import configure_logging, get_logger

    # python -m src.astronomer_calculations.interpretive_insights_wealth

    configure_logging()
    logger = get_logger(__name__)

    # ── Subjects ──────────────────────────────────────────────────────────────
    subjects = {
        "Desmond": (dt(1985, 11, 25, 17, 7, 0),  1.3253,  103.808053, 1),
        # "Corinne": (dt(1987,  6,  3, 12, 6, 0),  1.4759,  103.808053, 0),
        # "Lara":    (dt(2025,  7, 31,  9, 10, 0), 1.3253,  103.808053, 0),
    }

    for name, (birthday, lat, lon, gender) in subjects.items():
        logger.info("=" * 60)
        logger.info("Subject: %s  (%s)", name, birthday.strftime("%Y-%m-%d %H:%M"))

        tst_birthday, _ = get_true_solar_time(birthday, lat, lon)
        lunar_birthday  = tst_birthday.getLunar()

        raw_data = AstroDataAggregator().collect_data(
            lunar_birthday,
            birth_datetime=birthday,
            latitude=lat,
            longitude=lon,
            gender=gender,
        )

        insights = extract_wealth_insights(raw_data)
        logger.info(json.dumps(insights, ensure_ascii=False, indent=2))