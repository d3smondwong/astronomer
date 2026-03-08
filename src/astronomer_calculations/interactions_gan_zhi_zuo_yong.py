"""
This module calculates and analyzes the interactions between Heavenly Stems (天干) and
Earthly Branches (地支) in a BaZi (八字) chart based on the lunar birthday. It detects
comprehensive relationship patterns and uses physics-based energy/resonance semantics
for LLM clarity (replacing moral language with systematic terminology).

PHYSICS-BASED SEMANTIC FRAMEWORK:
    Core Philosophy: Interactions modeled as electromagnetic/resonance phenomena rather than
    ethical judgments. Energy entities create interference patterns at different frequencies.

Key Features:
    - Earthly Branch Interactions: Detects clashes (冲), harms (害), six-harmonies (六合),
      full triple combinations (三合), directional combinations (三会), and partial combinations (半合/半会)
      with universal distance semantics (正/遥 = Adjacent/Distant signal decay)

    - Half-Harmony Arching State & Co-Arching Detection: Distinguishes Strong (强=cardinal present),
      Arching (拱=virtual potential when cardinal missing but connection exists), and Weak (弱=no support).
      When a 半会(directional partial) and a 半合拱(elemental partial) both converge on the same missing
      cardinal branch, they form a Co-Arching (共拱) Virtual Element Frame—a structurally superior
      unified virtual-element field. Clash events involving co-arching pillars mark the frame as
      turbid (混杂), downgrading it from 强势主流 to 显著影响.

    - Heavenly Stem Distance Handling: Stem clashes (天干克) and combinations (天干合) now properly
      calculate pillar distance using Signal Decay model: 正克/正冲 (Short Circuit = adjacent) vs
      遥克/遥冲 (Atmospheric Interference = distant). Stem combinations (天干合) lock their participant
      stems, preventing lower-tier 克 interactions from activating (合 > 克 principle).

    - Punishment Detection with Energy Semantics: Recognizes full/partial three-punishment
      patterns (三刑) with distinct physics models:
      * Ungrateful (恩将仇报): 寅-巳-申 triple-set → Systemic Resonance Chaos (三刑全/半刑)
      * Bullying (欺负): 丑-未-戌 triple-set → Systemic Resonance Chaos (三刑全/半刑)
      * Uncivilized (无礼): 子-卯 pair → Direct/Remote Structural Stress (正刑/遥刑)
      * Self-Punishment (自刑): Repeat branches → Feedback Loop Energy Interference
        - Adjacent (紧贴): "自刑 (直接反馈过载)" = High-freq internal collision, immediate stress
        - Distant (遥隔): "遥自刑 (谐波自我纠缠)" = Low-freq resonance, delayed/cyclic response

    - Integrated Branch Energy: Consolidates elemental mapping from six-harmonies (六合 resultant
      elements), triple-element combinations (三合/三会 cardinal branches), and stem-rooted qi
      to provide unified energy signatures across the chart without dependencies on separate modules.

    - Pillar-based Tiered Analysis: Returns interaction details organized by priority tier:
      Tier 1 (纲领层=Framework): Structural harmonies (三会, 三合, 六冲, 六合)
      Tier 2 (气势层=Dynamics): Partial/co-arching dynamics (半会, 共拱, 半合, 天干克, 天干冲, 天干合)
      Tier 3 (琐碎层=Details): Minute punishments (三刑, 六害, 六破, 暗合)

    - Multi-Pillar Interaction Distribution: Three-way combinations (三会, 三合) are robustly
      distributed across all affected pillars using extract_pillar_indices() function with
      priority-based pillar name mapping. Same interaction object is shared across pillars for
      context preservation. Deduplication key (pillar_idx, tier_key, item_id) prevents duplicate
      entries within the same pillar+tier combination while preserving multi-pillar visibility.

DISTANCE SEMANTICS (Signal Decay Model):
    All friction interactions use unified Adjacent/Distant distinction:
    - 正X (正冲/正害/正破/正克/正刑) = Adjacent pillars → DIRECT/IMMEDIATE impact
    - 遥X (遥冲/遥害/遥破/遥克/遥刑) = Distant pillars → MEDIATED/DELAYED impact
    Distance calculated as: is_adjacent = (pillar_j - pillar_i == 1)

INTERACTION PRIORITY (in order of checking):
    TIER 1 - Structural Integrity (Hard Locks - consume branches entirely):
        1. San Hui (三会) - Directional seasonal combinations → Total field dominance
        2. San He (三合) - Full triple element combinations → Massive systemic shift
        3. Clash (六冲) - Direct opposition/friction → Structural failure/Explosion
        4. Liu He (六合) - Six harmonies/pairwise combinations → Locked molecular bond

    TIER 2 - Operational Momentum (Fluid Flow with locking power):
        5. Half San He (半合) - Partial harmonies with potential → Significant energy current (overrides Tier 3)
        6. Stem Clashes (天干克) - Heavenly stem frictions → High-voltage electrical tension

    TIER 3 - Parasitic Losses (Frictional Layer - subject to Tier 2 locks):
        7. San Xing (三刑) - Punishments with full/partial distinction → Internal feedback loops
        8. Harm (害) - Damage relationships → Mutual interference/Signal distortion
        9. Liu Po (六破) - Six destructions → Surface-level structural wear
        10. An He (暗合) - Hidden stem combinations (independent, secret interactions)

Note: All applicable interactions are evaluated and accumulated in priority order. This allows
"double-whammy" relationships to display all relevant interactions (e.g., a Clash that also
has a Punishment will show both). The order reflects which interaction is checked first.

Interaction Maps:
    - clash_map: Maps branches to their clash (opposing) partners
    - harm_map: Maps branches to their harm (harmful) partners
    - six_he_map: Maps branches to their harmonious partners
    - triple_he: Groups branches by element with positions (Cardinal/成, Growing/旺, Graveyard/墓)
    - cardinal_branches: Maps elements to their stability/cardinal branches (for arching detection)
    - directional_he: Groups branches by season/direction (directional combinations)
    - break_map: Maps branches to their destruction partners (六破)
    - hidden_stem_he: Maps branches to hidden stem combination partners
    - punishments: Maps branch pairs to punishment types (三刑) with adjacent/distant distinction
    - stem_combines: Maps stems to their harmonious partners (天干合)
    - stem_clashes: Maps stems to their polar-opposite partners (天干克) with distance routing
    - INTERACTION_STATUSES: Centralized configuration library for all status strings (305+ lines)

Main Functions:
    get_interactions(lunar_birthday): Extracts and analyzes all pillar interactions from a
        BaZi chart, returning LLM-optimized JSON with structured interaction data organized
        by priority tier.

    get_status(interaction_type, context): Retrieves and composes status values from centralized
        library, handling 4 pattern types: strings, templates, multi-type, and lookups.

    extract_pillar_indices(pillar_indices_str): Robustly extracts pillar indices from combination
        strings like "年柱-月柱" or "年柱-月柱-日柱". Uses priority-based mapping: full names
        (年柱) before abbreviated (年). Handles mixed formats, whitespace, and malformed input.
        Returns tuple of sorted unique indices (e.g., (0, 1, 2)) for multi-pillar routing.

    apply_bazi_master_priority(all_interactions, zhis): Post-calculation filtering applying
        hierarchical 6-tier priority system. Modulates interaction strength based on structural
        dominance rules. Interactions don't disappear but their effects are context-dependent.

Dependencies:
    - lunar_python: For lunar calendar conversion and BaZi chart extraction
    - datetime: For date/time handling
    - src.astronomer_calculations.solar_lunar_time: For true solar time calculations

Output Format:
    Returns nested dict with structure:
    {
        "作用": {
            "关系总览": [list of all interactions],
            "柱位动态": {
                "年柱": {"第一梯队_纲领层": [...], "第二梯队_气势层": [...], "第三梯队_琐碎层": [...]},
                "月柱": {"第一梯队_纲领层": [...], "第二梯队_气势层": [...], "第三梯队_琐碎层": [...]},
                "日柱": {"第一梯队_纲领层": [...], "第二梯队_气势层": [...], "第三梯队_琐碎层": [...]},
                "时柱": {"第一梯队_纲领层": [...], "第二梯队_气势层": [...], "第三梯队_琐碎层": [...]}
            },
            "判定优先级": {hierarchy categories}
        }
    }

    Multi-Pillar Interaction Strategy:
    - Three-way combinations (三会, 三合) appear in all affected pillars (same object reference)
    - Deduplication ensures no duplicate entries per pillar+tier
    - Pillar mapping via extract_pillar_indices(): {年柱→0, 月柱→1, 日柱→2, 时柱→3}
    - Example: 三会木局 matching Year/Month/Day appears in 年柱, 月柱, and 日柱

    Each interaction dict contains:
    - 类型: Type of interaction (六合, 六冲, 三刑, etc.)
    - 组合: Pillar composition (e.g., "年柱-月柱" or "年柱-月柱-日柱" for multi-pillar)
    - 组合明细: Detailed branch/stem mapping for each pillar
    - 状态: Status from centralized library with physics semantics
    - 紧贴: Boolean for adjacency detection (distance semantics)
    - 邀出: Invited branch for partial combinations
    - 元素: Element for harmony-based interactions
    - 强度: Modulated strength based on hierarchical priority system
    - 备注: Context notes (e.g., absorption, suppression by higher-tier interactions)
"""

from lunar_python import Solar, Lunar
from datetime import datetime
from src.astronomer_calculations.solar_lunar_time import get_true_solar_time

# Interactions: Key is one branch, value is its partner
clash_map = {
    "子": "午",
    "午": "子",
    "丑": "未",
    "未": "丑",
    "寅": "申",
    "申": "寅",
    "卯": "酉",
    "酉": "卯",
    "辰": "戌",
    "戌": "辰",
    "巳": "亥",
    "亥": "巳",
}

harm_map = {
    "子": "未",
    "未": "子",
    "丑": "午",
    "午": "丑",
    "寅": "巳",
    "巳": "寅",
    "卯": "辰",
    "辰": "卯",
    "申": "亥",
    "亥": "申",
    "酉": "戌",
    "戌": "酉",
}

# Six Combinations (Harmony)
six_he_map = {
    "子": "丑",
    "丑": "子",
    "寅": "亥",
    "亥": "寅",
    "卯": "戌",
    "戌": "卯",
    "辰": "酉",
    "酉": "辰",
    "巳": "申",
    "申": "巳",
    "午": "未",
    "未": "午",
}

# 六合 Six Harmonies Resultant Element Mapping (from branch_energy.py)
# Double-mapping: Both directions explicitly defined for safety
# Six Harmony Element Map (Element resulted from 六合 harmony)
# Uses canonical pair ordering: tuple(sorted([branch1, branch2])) to ensure single map entry
# This makes lookups safe regardless of branch order, avoiding duplication and fragility
six_he_element_map = {
    ("丑", "子"): {"primary": "土"},
    ("亥", "寅"): {"primary": "木"},
    ("卯", "戌"): {"primary": "火"},
    ("辰", "酉"): {"primary": "金"},
    ("巳", "申"): {"primary": "水"},
    ("午", "未"): {"primary": "土", "secondary": "火"},
}

# Triple Combination Map (Needs 2 out of 3 for a "Partial" or 3 for "Full")
# Structure: Element -> [Growing, Peak/Cardinal, Storage/Graveyard]
triple_he = {
    "水": {"申", "子", "辰"},  # Cardinal: 子 | Growing: 申 | Graveyard: 辰
    "木": {"亥", "卯", "未"},  # Cardinal: 卯 | Growing: 亥 | Graveyard: 未
    "火": {"寅", "午", "戌"},  # Cardinal: 午 | Growing: 寅 | Graveyard: 戌
    "金": {"巳", "酉", "丑"},  # Cardinal: 酉 | Growing: 巳 | Graveyard: 丑
}

# Cardinal/Peak Branches for each element (for 邀出 tracking and half-harmony strength)
peak_branches = {
    "水": "子",
    "木": "卯",
    "火": "午",
    "金": "酉",
}

# Cardinal Branches (Stability Points) - Used to assess half-harmony strength
cardinal_branches = {
    "水": "子",
    "木": "卯",
    "火": "午",
    "金": "酉",
}

# Directional Combinations (San Hui) - Three Meetings of entire season
directional_he = {
    "Wood": {"寅", "卯", "辰"},
    "Fire": {"巳", "午", "未"},
    "Metal": {"申", "酉", "戌"},
    "Water": {"亥", "子", "丑"},
}

# Six Destructions (Liu Po) - Shattering or hidden cracks
break_map = {
    "子": "酉",
    "酉": "子",
    "卯": "午",
    "午": "卯",
    "辰": "丑",
    "丑": "辰",
    "未": "戌",
    "戌": "未",
    "寅": "亥",
    "亥": "寅",
    "巳": "申",
    "申": "巳",
}

# Hidden Stem Combinations (An He) - Secret affairs or hidden wealth
hidden_stem_he = {
    "寅": "丑",
    "丑": "寅",
    "午": "亥",
    "亥": "午",
    "卯": "申",
    "申": "卯",
}

# "Three Punishments" (三刑 - San Xing) with full/partial detection
# Ungrateful (恩将仇报): 寅-巳-申 (needs all 3 for FULL, just 2 is PARTIAL)
# Bullying (欺负): 丑-未-戌 (needs all 3 for FULL, just 2 is PARTIAL)
# Uncivilized (无礼): 子-卯 (simple pair)
# Self-Punishment: 辰-辰, 午-午, 酉-酉, 亥-亥

ungrateful_punishment_branches = {"寅", "巳", "申"}
bullying_punishment_branches = {"丑", "未", "戌"}
uncivilized_punishment_pairs = {
    "子卯": "刑",
    "卯子": "刑",
}
self_punishment_branches = {"辰", "午", "酉", "亥"}

punishments = {
    "辰辰": "自刑",
    "午午": "自刑",
    "酉酉": "自刑",
    "亥亥": "自刑",
}

# Stem Interactions
stem_combines = {
    "甲": "己",
    "己": "甲",
    "乙": "庚",
    "庚": "乙",
    "丙": "辛",
    "辛": "丙",
    "丁": "壬",
    "壬": "丁",
    "戊": "癸",
    "癸": "戊",
}
stem_clashes = {
    "甲": "庚",
    "庚": "甲",
    "乙": "辛",
    "辛": "乙",
    "丙": "壬",
    "壬": "丙",
    "丁": "癸",
    "癸": "丁",
}

# Stem Controls (Different-polarity smooth/gentle control - 有情之克)
# Uses tuple list instead of dict to handle stems with multiple control targets
# Example: 乙 controls both 庚 (metal-wood cycle) AND 戊 (wood-earth cycle)
# Each pair included bidirectionally: (A, B) means A controls B, (B, A) means B controls A
stem_controls = [
    ("庚", "乙"),
    ("乙", "庚"),  # Yang Metal controls Yin Wood (bidirectional)
    ("辛", "甲"),
    ("甲", "辛"),  # Yin Metal controls Yang Wood (bidirectional)
    ("壬", "丁"),
    ("丁", "壬"),  # Yang Water controls Yin Fire (bidirectional)
    ("癸", "丙"),
    ("丙", "癸"),  # Yin Water controls Yang Fire (bidirectional)
    ("乙", "戊"),
    ("戊", "乙"),  # Yin Wood controls Yang Earth (bidirectional)
    ("丁", "庚"),
    ("庚", "丁"),  # Yin Fire controls Yang Metal (bidirectional)
    ("己", "壬"),
    ("壬", "己"),  # Yin Earth controls Yang Water (bidirectional)
]

# Stem to Five-Element mapping
stem_elements = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}

# Branch to Five-Element mapping
branch_elements = {
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}

# ===== INTERACTION STATUS LIBRARY (Centralized Configuration) =====
# All status values used across interactions. Modify here for global consistency.
INTERACTION_STATUSES = {
    # Basic adjacent/distant pattern
    "六合": {
        "adjacent": "正合",
        "distant": "遥合",
    },
    "六冲": {
        "adjacent": "正冲",
        "distant": "遥冲",
    },
    "六害": {
        "adjacent": "正害",
        "distant": "遥害",
    },
    "六破": {
        "adjacent": "正破",
        "distant": "遥破",
    },
    # Half-Harmonies - Element + State composition
    "半合": {
        "prefix": "半合{element}局",  # Template
        "strong": "强",  # Cardinal present: Full structural support
        "weak": "弱",  # Growing+Graveyard, no cardinal: Weak connection
        "arching": "拱",  # Cardinal missing, but connection exists: Virtual potential
    },
    # Punishments - Multiple types with distinct patterns
    "三刑": {
        # Triple-Set Patterns: Resonance Chaos (三-branch combinations)
        # Ungrateful (恩将仇报) - Systemic Resonance Chaos
        "ungrateful_full": "三刑全",
        "ungrateful_partial": "半刑",
        # Bullying (欺负) - Systemic Resonance Chaos
        "bullying_full": "三刑全",
        "bullying_partial": "半刑",
        # Self-Punishment (自刑) - Feedback Loop Energy Interference
        # Distinct from uncivilized - self-interaction creates resonant frequency collision
        "self_adjacent": "自刑 (直接反馈过载)",  # High-freq internal loop, immediate structural stress
        "self_distant": "遥自刑 (谐波自我纠缠)",  # Low-freq resonance, delayed/cyclic feedback
        # Uncivilized (无礼) - Simple Pair Structural Stress
        # Only Zi-Mao pair gets this
        "adjacent": "正刑",  # Direct Structural Stress (Zi-Mao)
        "distant": "遥刑",  # Remote Signal Distortion (Zi-Mao)
    },
    # Directional - Full/partial only
    "三会": {
        "full": "三会成局",
        "partial": "半会局",
    },
    # Triple - Full only
    "三合": {
        "full": "三合全局",
    },
    # Single status types
    "暗合": "暗(隐秘)",
    "天干合": "合化",
    # Stem Clash (Same-polarity, Violent) - with distance semantics
    "天干冲": {
        "adjacent": "正冲",  # Direct clash (violent collision)
        "distant": "遥冲",  # Distant clash (atmospheric interference)
    },
    # Stem Control (Different-polarity, Smooth) - with distance semantics
    "天干克": {
        "adjacent": "正克",  # Direct control (smooth management)
        "distant": "遥克",  # Distant control (mediated influence)
    },
}

# ===== QUALITATIVE STRENGTH LEVELS =====
# Post-calculation modulation system: Interactions don't disappear but weaken based on context
STRENGTH_LEVELS = {
    "强势主流": "主要作用力，完全激活",  # Tier 1: Full activation, primary force
    "显著影响": "受压但仍有影响力",  # Tier 2: Suppressed but still influential
    "中等衰减": "能量衰减至中等水平",  # Tier 3: Moderate energy reduction
    "大幅衰减": "被压制，作用力微弱",  # Tier 4: Heavily suppressed, weak force
    "消融吸收": "被完全吸收或消融",  # Tier 5: Completely absorbed/dissolved
}

# Tier priority ordering for sorting (lower index = higher priority)
STRENGTH_ORDER = {
    "强势主流": 0,
    "显著影响": 1,
    "中等衰减": 2,
    "大幅衰减": 3,
    "消融吸收": 4,
}

# Interaction type tier ordering (lower index = higher tier)
INTERACTION_TIER_ORDER = {
    # 第一梯队_纲领层 (Framework tier - structural relationships)
    "三会": 0,
    "三合": 1,
    "六冲": 2,
    "六合": 3,
    # 第二梯队_气势层 (Momentum tier - dynamic relationships)
    "半会": 4,
    "共拱": 4,  # Co-arching spans both 半会 and 半合; same tier but consolidates them
    "半合": 5,
    "天干克": 6,
    "天干冲": 7,
    "天干合": 8,
    # 第三梯队_琐碎层 (Friction tier - parasitic relationships)
    "三刑": 9,
    "六害": 10,
    "六破": 11,
    "暗合": 12,
}


def extract_pillar_indices(pillar_indices_str):
    """
    Extract all pillar indices from combination string like "年柱-月柱" or "年柱-月柱-日柱".

    Robustness:
    - Handles both full names (年柱, 月柱, 日柱, 时柱) and abbreviated names (年, 月, 日, 时)
    - Prioritizes full pillar names before attempting abbreviated matching
    - Strips whitespace and handles malformed input gracefully
    - Returns tuple of sorted unique indices for multi-pillar interactions
    - Returns None if fewer than 2 valid indices found

    Args:
        pillar_indices_str (str): Pillar combination like "年柱-月柱" or "年柱-月柱-日柱"

    Returns:
        tuple: Sorted indices (e.g., (0, 1, 2)) or None if invalid
    """
    # Full pillar name mapping (priority 1)
    pillar_full_map = {"年柱": 0, "月柱": 1, "日柱": 2, "时柱": 3}
    # Abbreviated pillar name mapping (priority 2, fallback only)
    pillar_abbr_map = {"年": 0, "月": 1, "日": 2, "时": 3}

    if not pillar_indices_str:
        return None

    parts = pillar_indices_str.split("-")
    indices = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Priority 1: Try exact full pillar name match first
        if part in pillar_full_map:
            indices.append(pillar_full_map[part])
        # Priority 2: Try exact abbreviated name match (single character)
        elif part in pillar_abbr_map:
            indices.append(pillar_abbr_map[part])
        else:
            # Log or handle unrecognized pillar name gracefully
            # Could raise error here for strict validation, but continue for robustness
            pass

    # Return sorted unique indices if we found at least 2 valid pillar references
    if len(indices) >= 2:
        return tuple(sorted(set(indices)))

    # Not enough valid pillar indices found
    return None


def apply_bazi_master_priority(all_interactions, zhis):
    """
    Post-calculation filtering: Apply hierarchical 6-tier priority system.
    Interactions don't disappear but modulate their strength based on context.

    Rules:
    1. 三会 (Directional Field) → Absorbs all others in same pillars
    2. 三合 → Dominates local structure, absorbs 六合/半合, suppresses tensions
    3. 六冲 → Shatters paired harmonies, creates tension in structure
    4. 六合 → Suppresses lower frictions (害/破)
    5. 半合/天干克 → Active but can be suppressed by above
    6. 三刑/六害/六破 → Parasitic layer, heavily suppressed by Tier 1-2

    Args:
        all_interactions: List of detected interactions (each is a dict)
        zhis: List of branch characters for each pillar [year, month, day, hour]

    Returns:
        Filtered and modulated interactions with 强度 and 备注 fields
    """
    # Scan Phase: Identify what structures exist
    interaction_types = [item.get("类型") for item in all_interactions]

    # Check for FULL 三会成局 only (partial 半会 should not suppress Tier 1 interactions)
    has_san_hui_full = any(
        item.get("类型") == "三会" and "成局" in item.get("状态", "")
        for item in all_interactions
    )
    has_san_he = "三合" in interaction_types
    has_liu_chong = "六冲" in interaction_types
    has_liu_he = "六合" in interaction_types
    has_gong_gong = "共拱" in interaction_types

    # Flat sets: individual pillar indices per structure (enables pillar-overlap checking).
    # Correct approach — pairwise interactions affect interactions that SHARE a pillar,
    # not just those on the exact same pair (which is impossible for clash+harmony).
    flat_liu_chong_pillars = set()  # pillars involved in any 六冲
    flat_liu_he_pillars = set()  # pillars involved in any 六合
    # Individual pillar indices whose stems are locked in 天干合化 (合 > 克 principle)
    tian_gan_he_locked_pillars = set()

    for item in all_interactions:
        itype = item.get("类型")
        combo = item.get("组合", "")
        indices = extract_pillar_indices(combo)

        if itype == "六冲" and indices:
            flat_liu_chong_pillars.update(indices)
        elif itype == "六合" and indices:
            flat_liu_he_pillars.update(indices)
        elif itype == "天干合" and indices:
            tian_gan_he_locked_pillars.update(indices)

    # Apply 6-tier hierarchical filtering
    modulated_interactions = []

    for item in all_interactions:
        itype = item.get("类型")
        combo = item.get("组合", "")
        indices = extract_pillar_indices(combo)

        # TIER 1: 三会成局 - Directional Field (Highest Priority - full only)
        if has_san_hui_full:
            if itype == "三合":
                # 三合 absorbed into directional field
                item["状态"] = "absorbed_into_directional_field"
                item["强度"] = "消融吸收"
                item["备注"] = "被三会完全吸收，独立性消失"
            elif itype in ["六合", "半合"]:
                # Harmonies suppressed
                item["强度"] = "大幅衰减"
                item["备注"] = "被三会压制，作用力大幅减弱"
            elif itype in ["六冲", "六害", "六破"]:
                # Frictions suppressed
                item["强度"] = "大幅衰减"
                item["备注"] = "被三会压制，冲力被方位场吸收"
            elif itype == "三刑":
                # Punishments suppressed
                item["强度"] = "大幅衰减"
                item["备注"] = "被三会压制，刑力衰减"
            elif itype == "三会":
                # 三会 itself asserts full directional field strength
                item["强度"] = "强势主流"
                if not item.get("备注"):
                    item["备注"] = "方位场完整成局，主导全局"
            elif itype == "半会":
                # Partial directional suppressed by the full directional field
                item["强度"] = "大幅衰减"
                item["备注"] = "被三会压制，半会方位力大幅弱化"
            elif itype == "共拱":
                # Co-arching dissolved — the full 三会 already claims the directional field
                item["强度"] = "消融吸收"
                item["备注"] = "三会已完整成局，共拱虚局被吸收"
            elif itype not in ["天干合", "天干克"]:
                if not item.get("强度"):
                    item["强度"] = "显著影响"

        # TIER 2: 三合 - Triple Combination (if no 三会)
        elif has_san_he and itype != "三会":
            if itype == "六合":
                # 六合 absorbed/suppressed by 三合
                item["强度"] = "消融吸收"
                item["备注"] = "被三合吸收，独立作用消失"
            elif itype == "半合":
                # Half-harmonies weakened
                item["强度"] = "大幅衰减"
                item["备注"] = "被三合压制，半合势力弱化"
            elif itype == "半会":
                # Partial directional field suppressed by triple combination
                item["强度"] = "大幅衰减"
                item["备注"] = "被三合压制，半会方位力弱化"
            elif itype == "六冲":
                # Clash creates tension within the 三合 structure
                item["强度"] = "中等衰减"
                item["备注"] = "与三合结构形成内部张力，冲力被部分吸收"
            elif itype in ["六害", "六破"]:
                # Lower frictions heavily suppressed
                item["强度"] = "大幅衰减"
                item["备注"] = "被三合压制，摩擦作用衰减"
            elif itype == "三刑":
                item["强度"] = "大幅衰减"
                item["备注"] = "被三合压制，刑力衰减"

        # TIER 3: 六冲 - Clash (if no 三会/三合)
        # Pillar-aware: a clash only affects interactions that SHARE a pillar with it.
        elif has_liu_chong and itype not in ["三会", "三合", "六冲"]:
            shares_clash_pillar = bool(set(indices or ()) & flat_liu_chong_pillars)
            if itype == "六合":
                if shares_clash_pillar:
                    # Clash shatters harmony sharing a pillar — the clashing branch
                    # cannot simultaneously harmonize; its energy is consumed by conflict
                    item["强度"] = "消融吸收"
                    item["备注"] = "被六冲摧毁，合力瓦解"
                # else: 六合 on completely unrelated pillars — unaffected (falls to Tier 6)
            elif itype in ["半合", "半会"]:
                if shares_clash_pillar:
                    item["强度"] = "大幅衰减"
                    item["备注"] = "六冲冲散半合/半会，势力大幅衰减"
                else:
                    item["强度"] = "中等衰减"
                    item["备注"] = "六冲影响扩散，半合/半会衰减"
            elif itype in ["六害", "六破"]:
                if shares_clash_pillar:
                    # Clash amplifies frictions sharing a pillar (tension compounds)
                    item["强度"] = "显著影响"
                    item["备注"] = "六冲加剧摩擦效应，冲害/冲破协同增强"
                # else: unrelated pillars — unaffected (falls to Tier 6)
            elif itype == "三刑":
                item["强度"] = "显著影响"
                item["备注"] = "六冲与刑力协同作用，压力增强"

        # TIER 4: 六合 - Six Harmony (if no 三会/三合/六冲)
        # Pillar-aware: harmony only suppresses frictions that SHARE a pillar with it.
        elif has_liu_he and itype not in ["三会", "三合", "六冲", "六合"]:
            shares_he_pillar = bool(set(indices or ()) & flat_liu_he_pillars)
            if itype in ["六害", "六破"]:
                if shares_he_pillar:
                    # Harmony smooths over frictions sharing a pillar
                    item["强度"] = "消融吸收"
                    item["备注"] = "被六合吸收，摩擦力消融"
                # else: unrelated pillars — unaffected (falls to Tier 6)
            elif itype in ["半合", "半会"] and shares_he_pillar:
                item["强度"] = "中等衰减"
                item["备注"] = "被六合压制，半合/半会势力衰减"
            elif itype == "三刑":
                item["强度"] = "大幅衰减"
                item["备注"] = "被六合压制，刑力衰减"

        # BaZi Principle: 合 > 克 — A stem bound in 天干合化 loses its independent 克 capacity.
        # When 乙庚合化金, 乙 is no longer wood and cannot control earth (克戊);
        # 庚 is merged and cannot be controlled by fire (丁克庚 dissolves).
        if itype == "天干克" and tian_gan_he_locked_pillars:
            combo_indices_set = set(indices) if indices else set()
            if combo_indices_set & tian_gan_he_locked_pillars:
                item["强度"] = "消融吸收"
                item["备注"] = "天干合化锁定本干，克力被合化消融"

        # TIER 5 (Co-Arching): 共拱 self-asserts its strength; its constituent 半会/半合
        # are elevated because they are not isolated partials — they reinforce each other.
        # Exception: if any participating branch is clashed (混杂), the frame is weakened
        # to 显著影响 — present but conflicted, not dominant.
        if has_gong_gong and not has_san_hui_full and not has_san_he:
            if itype == "共拱" and not item.get("强度"):
                if item.get("混杂"):
                    # Clash override: co-arching frame is turbid — demoted from dominant
                    item["强度"] = "显著影响"
                    # 备注 already set during construction (names the clashing branch)
                else:
                    item["强度"] = "强势主流"
                    # 备注 already set during construction
            elif (
                itype in ("半合", "半会") and item.get("共拱") and not item.get("强度")
            ):
                # Constituent of a co-arching group. Inherit turbidity from parent frame.
                target = item.get("共拱目标", "")
                parent_is_turbid = any(
                    x.get("混杂")
                    for x in all_interactions
                    if x.get("类型") == "共拱" and x.get("共拱目标") == target
                )
                if parent_is_turbid:
                    item["强度"] = "显著影响"
                    item["备注"] = f"共拱{target}，但虚局被冲混杂，势力衰减"
                else:
                    item["强度"] = "强势主流"
                    item["备注"] = f"共拱{target}，虚元局协同共振，势力强化"
        # OPTION A: Distance modulates strength across all tiers
        if not has_san_hui_full and not has_san_he and not has_liu_chong:
            if itype == "半合" and not item.get("强度"):
                is_adjacent = item.get("紧贴", False)
                if is_adjacent:
                    item["强度"] = "强势主流"
                    if not item.get("备注"):
                        item["备注"] = "独立作用层，半合势力完整激活"
                else:
                    item["强度"] = "中等衰减"
                    if not item.get("备注"):
                        item["备注"] = "独立作用层，距离衰减"
            elif itype == "天干克" and not item.get("强度"):
                # 天干克 items have no "紧贴" field — infer adjacency from pillar indices
                is_adjacent = (max(indices) - min(indices) == 1) if indices else False
                if is_adjacent:
                    item["强度"] = "强势主流"
                    if not item.get("备注"):
                        item["备注"] = "天干克独立作用，天平失衡"
                else:
                    item["强度"] = "中等衰减"
                    if not item.get("备注"):
                        item["备注"] = "天干克独立作用，距离衰减"
            elif itype == "天干合" and not item.get("强度"):
                item["强度"] = "强势主流"
                if not item.get("备注"):
                    item["备注"] = "天干合独立作用，天干合化"

        # TIER 6: All remaining interactions (Tier 1/2/3) - Default strength assignment
        # Default strength assignment if not yet assigned
        # OPTION A: Distance modulates strength consistently across all tiers
        if not item.get("强度"):
            # Tier 1: 六冲, 六合, 三会（已处理）, 三合（已处理）
            if itype in ["六冲", "六合", "三会", "三合"]:
                is_adjacent = item.get("紧贴", False)
                if is_adjacent:
                    item["强度"] = "强势主流"
                    if not item.get("备注"):
                        item["备注"] = "独立激活，完全激活"
                else:
                    item["强度"] = "显著影响"
                    if not item.get("备注"):
                        item["备注"] = "独立激活，距离衰减"
            # Tier 3: 三刑, 六害, 六破 and all punishment subtypes
            elif itype in [
                "三刑",
                "六害",
                "六破",
                "无恩之刑",
                "恃势之刑",
                "无礼之刑",
                "自刑",
            ]:
                is_adjacent = item.get("紧贴", False)
                if is_adjacent:
                    item["强度"] = "强势主流"
                    if not item.get("备注"):
                        item["备注"] = "独立作用，完全激活"
                else:
                    item["强度"] = "大幅衰减"
                    if not item.get("备注"):
                        item["备注"] = "独立作用，距离衰减"
            # Special case: 暗合 (Hidden harmonies - no distance semantics)
            elif itype in ["暗合"]:
                item["强度"] = "强势主流"
                if not item.get("备注"):
                    item["备注"] = "隐秘作用，秘密互动"
            else:
                item["强度"] = "强势主流"
                if not item.get("备注"):
                    item["备注"] = "独立激活"

        modulated_interactions.append(item)

    # Sort by tier (interaction type priority) then by strength
    modulated_interactions.sort(
        key=lambda x: (INTERACTION_TIER_ORDER.get(x.get("类型"), 999),)
    )

    return modulated_interactions


def get_status(interaction_type, context=None):
    """
    Retrieve and compose status value from centralized library.

    Args:
        interaction_type: Type of interaction (e.g., "六合", "半合")
        context: dict with contextual information for composition
                 - key: lookup key (e.g., "adjacent", "distant", "strong")
                 - element: element name (for half-harmony)
                 - state: "strong", "weak", or "arching" (for half-harmony)
                 - punishment_type: "ungrateful", "bullying", "uncivilized", "self" (for 三刑)
                 - is_full: boolean for full/partial (for ungrateful/bullying 三刑)
                 - is_adjacent: boolean for adjacency (for uncivilized Zi-Mao / self 自刑)

    Returns:
        Status string
    """
    if interaction_type not in INTERACTION_STATUSES:
        return "未知"

    status_config = INTERACTION_STATUSES[interaction_type]

    # Handle single string statuses (暗合, 天干合, 天干克)
    if isinstance(status_config, str):
        return status_config

    context = context or {}

    # Template-based (半合) - compose element + state
    if interaction_type == "半合":
        element = context.get("element", "")
        state = context.get("state", "weak")  # default to weak
        state_char = status_config.get(state, "弱")  # Lookup state: 强/弱/拱
        prefix = status_config["prefix"].format(element=element)
        return f"{prefix}({state_char})"

    # Multi-type (三刑) - needs punishment type + full/partial or adjacent/distant
    if interaction_type == "三刑":
        punishment_type = context.get("punishment_type")
        is_full = context.get("is_full")
        is_adjacent = context.get("is_adjacent")

        # Route based on punishment_type
        if punishment_type in ("ungrateful", "bullying"):
            # Triple-set: Full/partial Resonance Chaos
            key = f"{punishment_type}_full" if is_full else f"{punishment_type}_partial"
        elif punishment_type == "self":
            # Self-Punishment: Feedback Loop (distinct routing)
            key = f"self_adjacent" if is_adjacent else "self_distant"
        else:  # uncivilized (Zi-Mao only)
            # Simple pair: Direct/Remote Structural Stress
            key = "adjacent" if is_adjacent else "distant"

        return status_config.get(key, "未知")

    # Simple lookup (adjacent/distant, full/partial)
    key = context.get("key", "default")
    return status_config.get(key, "未知")


def get_interactions(lunar_birthday):
    """
    Extract pillar interactions from the BaZi chart and return structured LLM-ready JSON.
    Detects clashes, harms, harmonies, punishments, and stem combinations.
    Uses detailed output format from branch_energy.py with priority tier system from interactions_gan_zhi_zuo_yong.py.

    Args:
        lunar_birthday: Lunar object from BaZi chart

    Returns:
        dict: Structured interaction data organized by pillar dynamics and priority tiers
    """
    baZi = lunar_birthday.getEightChar()
    gans = [baZi.getYearGan(), baZi.getMonthGan(), baZi.getDayGan(), baZi.getTimeGan()]
    zhis = [baZi.getYearZhi(), baZi.getMonthZhi(), baZi.getDayZhi(), baZi.getTimeZhi()]

    pillar_names_cn = ["年柱", "月柱", "日柱", "时柱"]
    pillar_names_abr = ["年", "月", "日", "时"]

    # Track interactions by type for priority categorization
    interactions_by_type = {
        "三会": [],
        "半会": [],
        "三合": [],
        "共拱": [],
        "天干合": [],
        "天干冲": [],
        "天干克": [],
        "六冲": [],
        "六合": [],
        "三刑": [],
        "六害": [],
        "六破": [],
        "暗合": [],
    }

    # Track interactions by pillar for dynamics
    pillar_dynamics = {
        0: {"structural": [], "frictional": []},
        1: {"structural": [], "frictional": []},
        2: {"structural": [], "frictional": []},
        3: {"structural": [], "frictional": []},
    }

    interaction_summary = []
    interaction_shens = []
    all_interactions = []  # Collect all interactions for post-calculation filtering

    # --- Earthly Branch Interactions ---
    # PRIORITY 1: Directional Combinations (San Hui) - Highest Priority
    for direction, group in directional_he.items():
        # Check that all 3 branches exist and each appears in a DIFFERENT pillar
        # This prevents false positives like zhis=["申", "申", "子", "辰"] being detected as 三会
        matched_branches = {}
        for branch in group:
            for k, zhi in enumerate(zhis):
                if zhi == branch and k not in matched_branches.values():
                    matched_branches[branch] = k
                    break

        # FULL 三会 DETECTION: All 3 branches found in distinct pillars (TIER 1)
        if len(matched_branches) == 3:
            direction_cn = {
                "Wood": "木",
                "Fire": "火",
                "Metal": "金",
                "Water": "水",
            }.get(direction, direction)
            display_text = f"三会{direction_cn}局"
            interaction_summary.append(display_text)
            interaction_shens.append(f"三会{direction}局")
            interactions_by_type["三会"].append(display_text)

            # Build detailed 三会 entry
            matches = [
                {"name": pillar_names_cn[k], "zhi": zhis[k]}
                for k, zhi in enumerate(zhis)
                if zhi in group
            ]
            san_hui_detail = {
                "类型": "三会",
                "方位": direction,
                "组合": "-".join([m["name"] for m in matches]),
                "组合明细": {m["name"]: m["zhi"] for m in matches},
                "状态": get_status("三会", {"key": "full"}),
            }

            # Add to all_interactions once (outside loop to avoid triplicates)
            all_interactions.append(san_hui_detail)

            # Distribute to all matching pillars
            for idx, branch in enumerate(zhis):
                if branch in group:
                    pillar_dynamics[idx]["structural"].append(san_hui_detail)

    # PRIORITY 2: Full Triple Combinations (San He)
    for element, group in triple_he.items():
        # Check that all 3 branches exist and each appears in a DIFFERENT pillar
        # This prevents false positives like zhis=["申", "申", "子", "辰"] being detected as 三合
        matched_branches = {}
        for branch in group:
            for k, zhi in enumerate(zhis):
                if zhi == branch and k not in matched_branches.values():
                    matched_branches[branch] = k
                    break

        # FULL 三合 DETECTION: All 3 branches found in distinct pillars
        if len(matched_branches) == 3:
            display_text = f"三合{element}局"
            interaction_summary.append(display_text)
            interaction_shens.append(f"全三合{element}局")
            interactions_by_type["三合"].append(display_text)

            # Build detailed 三合 entry
            matches = [
                {"name": pillar_names_cn[k], "zhi": zhis[k], "index": k}
                for k, zhi in enumerate(zhis)
                if zhi in group
            ]
            san_he_detail = {
                "类型": "三合",
                "元素": element,
                "组合": "-".join([m["name"] for m in matches]),
                "组合明细": {m["name"]: m["zhi"] for m in matches},
                "状态": get_status("三合", {"key": "full"}),
                "邀出": "已全",
                "紧贴": (
                    any(
                        matches[i + 1]["index"] - matches[i]["index"] == 1
                        for i in range(len(matches) - 1)
                    )
                    if len(matches) > 1
                    else False
                ),
            }

            # Add to all_interactions once (outside loop to avoid triplicates)
            all_interactions.append(san_he_detail)

            # Distribute to all matching pillars
            for idx, branch in enumerate(zhis):
                if branch in group:
                    pillar_dynamics[idx]["structural"].append(san_he_detail)

    # PRIORITY 2 (TIER 2): Partial Directional (半会) - Weaker alignment, partial field
    for direction, group in directional_he.items():
        matched_branches = {}
        for branch in group:
            for k, zhi in enumerate(zhis):
                if zhi == branch and k not in matched_branches.values():
                    matched_branches[branch] = k
                    break

        # PARTIAL 三会 DETECTION: Exactly 2 of 3 branches found in distinct pillars (半会局) - TIER 2
        if len(matched_branches) == 2:
            direction_cn = {
                "Wood": "木",
                "Fire": "火",
                "Metal": "金",
                "Water": "水",
            }.get(direction, direction)
            display_text = f"半会{direction_cn}局"
            interaction_summary.append(display_text)
            interaction_shens.append(f"半会{direction}局")
            interactions_by_type["半会"].append(display_text)

            # Build detailed 半会 entry
            matches = [
                {"name": pillar_names_cn[k], "zhi": zhis[k]}
                for k, zhi in enumerate(zhis)
                if zhi in group
            ]
            # Compute the missing (arching) branch: the cardinal of this directional group
            missing_branch = next((b for b in group if b not in matched_branches), None)
            san_hui_partial_detail = {
                "类型": "半会",
                "方位": direction,
                "组合": "-".join([m["name"] for m in matches]),
                "组合明细": {m["name"]: m["zhi"] for m in matches},
                "犹出": missing_branch or "无",
                "状态": get_status("三会", {"key": "partial"}),
            }

            # Add to all_interactions
            all_interactions.append(san_hui_partial_detail)

            # Distribute to all matching pillars (TIER 2, not locked)
            for idx, branch in enumerate(zhis):
                if branch in group:
                    pillar_dynamics[idx]["frictional"].append(san_hui_partial_detail)

    # Check pairwise interactions - Evaluate all conditions in priority order
    # LOCKING SYSTEM: Tier 1 structural relationships lock branches, preventing lower-tier interactions
    # SHORT-CIRCUIT LOGIC: Use if/elif for mutually exclusive Tier 1 relationships
    # INDEPENDENT CHECKS: Use if (not elif) for Tier 3 (Punishments) - they layer on top of primary relationships
    for i in range(4):
        for j in range(i + 1, 4):
            b_i, b_j = zhis[i], zhis[j]
            pair_key = "".join(sorted([b_i, b_j]))
            is_adjacent = j - i == 1

            # === TIER 1 STRUCTURAL BONDS (SHORT-CIRCUIT CHAIN) ===
            # Only ONE Tier 1 relationship per pillar pair. Each locks branches from lower-tier interactions.

            # Priority 1: Clashes (冲) - Direct opposition friction (checked BEFORE harmony for separation)
            if clash_map.get(b_i) == b_j:
                clash_detail = {
                    "类型": "六冲",
                    "组合": f"{pillar_names_cn[i]}-{pillar_names_cn[j]}",
                    "组合明细": {pillar_names_cn[i]: b_i, pillar_names_cn[j]: b_j},
                    "紧贴": is_adjacent,
                    "状态": get_status(
                        "六冲", {"key": "adjacent" if is_adjacent else "distant"}
                    ),
                }

                interaction_shens.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}冲"
                )
                pillar_dynamics[i]["structural"].append(clash_detail)
                pillar_dynamics[j]["structural"].append(clash_detail)
                all_interactions.append(clash_detail)
                interactions_by_type["六冲"].append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j})地支相冲"
                )
                interaction_summary.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j})地支相冲"
                )

            # Priority 2: Six Harmonies (Liu He) - Structural bond (checked AFTER clash for priority)
            elif six_he_map.get(b_i) == b_j:
                # Use canonical pair ordering for robust element lookup
                pair_key = tuple(sorted([b_i, b_j]))
                elem = six_he_element_map.get(pair_key, {}).get("primary", "")

                six_he_detail = {
                    "类型": "六合",
                    "组合": f"{pillar_names_cn[i]}-{pillar_names_cn[j]}",
                    "组合明细": {
                        pillar_names_cn[i]: b_i,
                        pillar_names_cn[j]: b_j,
                    },
                    "结果": f"化{elem}",
                    "紧贴": is_adjacent,
                    "状态": get_status(
                        "六合", {"key": "adjacent" if is_adjacent else "distant"}
                    ),
                }

                interaction_shens.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}合"
                )
                pillar_dynamics[i]["structural"].append(six_he_detail)
                pillar_dynamics[j]["structural"].append(six_he_detail)
                all_interactions.append(six_he_detail)
                interactions_by_type["六合"].append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j})地支相合"
                )
                interaction_summary.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j})地支相合"
                )

            # Priority 3: Partial Triple Combinations (Half San He) - TIER 2 momentum
            # Checked independent of Tier 1 - will be modulated by post-calculation filtering
            else:
                # Try to find a half-harmony for this pair
                for element, group in triple_he.items():
                    if b_i in group and b_j in group:
                        # Determine 邀出 (invited branch) and State (强/弱/拱)
                        unique_zhis_in_group = set(z for z in zhis if z in group)
                        cardinal = cardinal_branches.get(element)
                        peak = peak_branches[element]

                        # Calculate state based on cardinal presence
                        # 强 (Strong): Cardinal present = full structural support
                        # 拱 (Arching): Cardinal absent BUT both non-cardinal members present = virtual potential
                        # 弱 (Weak): Only ONE non-cardinal member present = weak connection
                        if cardinal in zhis:
                            state = "strong"
                            yao_chu = "无"
                        elif len(unique_zhis_in_group) == 2:
                            # Both non-cardinal members present (growing + graveyard), cardinal absent
                            state = "arching"
                            yao_chu = peak
                        else:
                            # Only one of {growing, graveyard} present, cardinal absent
                            state = "weak"
                            yao_chu = "无"

                        half_he_detail = {
                            "类型": "半合",
                            "元素": element,
                            "组合": f"{pillar_names_cn[i]}-{pillar_names_cn[j]}",
                            "组合明细": {
                                pillar_names_cn[i]: b_i,
                                pillar_names_cn[j]: b_j,
                            },
                            "状态": get_status(
                                "半合",
                                {
                                    "element": element,
                                    "state": state,
                                },
                            ),
                            "邀出": yao_chu,
                            "紧贴": is_adjacent,
                        }

                        interaction_shens.append(
                            f"{pillar_names_abr[i]}{pillar_names_abr[j]}半合{element}局"
                        )
                        pillar_dynamics[i]["frictional"].append(half_he_detail)
                        pillar_dynamics[j]["frictional"].append(half_he_detail)
                        all_interactions.append(half_he_detail)
                        interactions_by_type["六合"].append(
                            f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j})半合{element}局"
                        )
                        interaction_summary.append(
                            f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j})半合{element}局"
                        )

                        break

            # Priority 4: Harms (害) - TIER 3 parasitic loss
            if harm_map.get(b_i) == b_j:
                harm_detail = {
                    "类型": "六害",
                    "组合": f"{pillar_names_cn[i]}-{pillar_names_cn[j]}",
                    "组合明细": {pillar_names_cn[i]: b_i, pillar_names_cn[j]: b_j},
                    "紧贴": is_adjacent,
                    "状态": get_status(
                        "六害", {"key": "adjacent" if is_adjacent else "distant"}
                    ),
                }

                interaction_shens.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}害"
                )
                pillar_dynamics[i]["frictional"].append(harm_detail)
                pillar_dynamics[j]["frictional"].append(harm_detail)
                all_interactions.append(harm_detail)
                interactions_by_type["六害"].append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j})地支相害"
                )
                interaction_summary.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j})地支相害"
                )

            # Priority 5: Liu Po (Six Destructions) - TIER 3 parasitic loss, lowest friction tier
            if break_map.get(b_i) == b_j:
                po_detail = {
                    "类型": "六破",
                    "组合": f"{pillar_names_cn[i]}-{pillar_names_cn[j]}",
                    "组合明细": {pillar_names_cn[i]: b_i, pillar_names_cn[j]: b_j},
                    "紧贴": is_adjacent,
                    "状态": get_status(
                        "六破", {"key": "adjacent" if is_adjacent else "distant"}
                    ),
                }

                interaction_shens.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}破"
                )
                pillar_dynamics[i]["frictional"].append(po_detail)
                pillar_dynamics[j]["frictional"].append(po_detail)
                all_interactions.append(po_detail)
                interactions_by_type["六破"].append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j})地支相破"
                )
                interaction_summary.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j})地支相破"
                )

            # === INDEPENDENT CHECKS: These can coexist with the short-circuit relationships ===
            # Punishments add "flavor" to primary relationships (e.g., "Clash" + "Ungrateful Punishment")

            # Check for Full/Partial Ungrateful Punishment (寅-巳-申)
            if (
                b_i in ungrateful_punishment_branches
                and b_j in ungrateful_punishment_branches
            ):
                ungrateful_count = sum(
                    1 for branch in zhis if branch in ungrateful_punishment_branches
                )
                label_cn = "刑(恩将仇报)" if ungrateful_count == 3 else "刑(半恩将仇报)"

                xing_detail = {
                    "类型": "无恩之刑",
                    "组合": f"{pillar_names_cn[i]}-{pillar_names_cn[j]}",
                    "组合明细": {pillar_names_cn[i]: b_i, pillar_names_cn[j]: b_j},
                    "紧贴": is_adjacent,
                    "状态": get_status(
                        "三刑",
                        {
                            "punishment_type": "ungrateful",
                            "is_full": ungrateful_count == 3,
                        },
                    ),
                }

                interaction_shens.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}{label_cn}"
                )
                pillar_dynamics[i]["frictional"].append(xing_detail)
                pillar_dynamics[j]["frictional"].append(xing_detail)
                all_interactions.append(xing_detail)
                interactions_by_type["三刑"].append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j}){label_cn}"
                )
                interaction_summary.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j}){label_cn}"
                )

            # Check for Full/Partial Bullying Punishment (丑-未-戌)
            if (
                b_i in bullying_punishment_branches
                and b_j in bullying_punishment_branches
            ):
                bullying_count = sum(
                    1 for branch in zhis if branch in bullying_punishment_branches
                )
                label_cn = "刑(欺负)" if bullying_count == 3 else "刑(半欺负)"

                xing_detail = {
                    "类型": "恃势之刑",
                    "组合": f"{pillar_names_cn[i]}-{pillar_names_cn[j]}",
                    "组合明细": {pillar_names_cn[i]: b_i, pillar_names_cn[j]: b_j},
                    "紧贴": is_adjacent,
                    "状态": get_status(
                        "三刑",
                        {"punishment_type": "bullying", "is_full": bullying_count == 3},
                    ),
                }

                interaction_shens.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}{label_cn}"
                )
                pillar_dynamics[i]["frictional"].append(xing_detail)
                pillar_dynamics[j]["frictional"].append(xing_detail)
                all_interactions.append(xing_detail)
                interactions_by_type["三刑"].append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j}){label_cn}"
                )
                interaction_summary.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j}){label_cn}"
                )

            # Check for Uncivilized Punishment (子-卯)
            if pair_key in uncivilized_punishment_pairs:
                label_cn = "刑(无礼)"
                xing_detail = {
                    "类型": "无礼之刑",
                    "组合": f"{pillar_names_cn[i]}-{pillar_names_cn[j]}",
                    "组合明细": {pillar_names_cn[i]: b_i, pillar_names_cn[j]: b_j},
                    "紧贴": is_adjacent,
                    "状态": get_status(
                        "三刑",
                        {"punishment_type": "uncivilized", "is_adjacent": is_adjacent},
                    ),
                }

                interaction_shens.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}{label_cn}"
                )
                pillar_dynamics[i]["frictional"].append(xing_detail)
                pillar_dynamics[j]["frictional"].append(xing_detail)
                all_interactions.append(xing_detail)
                interactions_by_type["三刑"].append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j}){label_cn}"
                )
                interaction_summary.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j}){label_cn}"
                )

            # Check for Self-Punishment (辰-辰, 午-午, 酉-酉, 亥-亥)
            if pair_key in punishments and "自刑" in punishments.get(pair_key, ""):
                label_cn = punishments[pair_key]
                xing_detail = {
                    "类型": "自刑",
                    "组合": f"{pillar_names_cn[i]}-{pillar_names_cn[j]}",
                    "组合明细": {pillar_names_cn[i]: b_i, pillar_names_cn[j]: b_j},
                    "紧贴": is_adjacent,
                    "状态": get_status(
                        "三刑", {"punishment_type": "self", "is_adjacent": is_adjacent}
                    ),
                }

                interaction_shens.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}{label_cn}"
                )
                pillar_dynamics[i]["frictional"].append(xing_detail)
                pillar_dynamics[j]["frictional"].append(xing_detail)
                all_interactions.append(xing_detail)
                interactions_by_type["三刑"].append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j}){label_cn}"
                )
                interaction_summary.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j}){label_cn}"
                )

            # Priority 9: Hidden Stem Combinations (An He) - Secret interactions
            if hidden_stem_he.get(b_i) == b_j and clash_map.get(b_i) != b_j:
                an_he_detail = {
                    "类型": "暗合",
                    "组合": f"{pillar_names_cn[i]}-{pillar_names_cn[j]}",
                    "组合明细": {pillar_names_cn[i]: b_i, pillar_names_cn[j]: b_j},
                    "状态": get_status("暗合"),
                }

                interaction_shens.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}暗合"
                )
                pillar_dynamics[i]["structural"].append(an_he_detail)
                pillar_dynamics[j]["structural"].append(an_he_detail)
                all_interactions.append(an_he_detail)
                interactions_by_type["暗合"].append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j})地支暗合"
                )
                interaction_summary.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({b_i}{b_j})地支暗合"
                )

    # --- Heavenly Stem Interactions ---
    for i in range(4):
        for j in range(i + 1, 4):
            g_i, g_j = gans[i], gans[j]
            is_adjacent = j - i == 1  # Distance calculation for stem interactions

            # Heavenly Stem Interactions - Priority Lock: Combine > Clash > Control
            # Only ONE interaction per pair, applied in hierarchical order

            # 1. Combine (Harmony) - Highest Priority: Transforms stems fundamentally
            if stem_combines.get(g_i) == g_j:
                stem_he_detail = {
                    "类型": "天干合",
                    "组合": f"{pillar_names_cn[i]}-{pillar_names_cn[j]}",
                    "组合明细": {pillar_names_cn[i]: g_i, pillar_names_cn[j]: g_j},
                    "状态": get_status("天干合"),
                }

                interaction_shens.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}天干合"
                )
                pillar_dynamics[i]["structural"].append(stem_he_detail)
                pillar_dynamics[j]["structural"].append(stem_he_detail)
                all_interactions.append(stem_he_detail)
                interactions_by_type["天干合"].append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({g_i}{g_j})天干合化"
                )
                interaction_summary.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({g_i}{g_j})天干合化"
                )

            # 2. Clash (Same-polarity, Violent) - Medium Priority: Direct collision
            elif stem_clashes.get(g_i) == g_j:
                stem_clash_detail = {
                    "类型": "天干冲",
                    "组合": f"{pillar_names_cn[i]}-{pillar_names_cn[j]}",
                    "组合明细": {pillar_names_cn[i]: g_i, pillar_names_cn[j]: g_j},
                    "状态": get_status(
                        "天干冲", {"key": "adjacent" if is_adjacent else "distant"}
                    ),
                }

                interaction_shens.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}天干冲"
                )
                pillar_dynamics[i]["frictional"].append(stem_clash_detail)
                pillar_dynamics[j]["frictional"].append(stem_clash_detail)
                all_interactions.append(stem_clash_detail)
                interactions_by_type["天干冲"].append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({g_i}{g_j})天干相冲"
                )
                interaction_summary.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({g_i}{g_j})天干相冲"
                )

            # 3. Control (Different-polarity, Smooth) - Lower Priority: Disciplined management
            elif (g_i, g_j) in stem_controls or (g_j, g_i) in stem_controls:
                stem_control_detail = {
                    "类型": "天干克",
                    "组合": f"{pillar_names_cn[i]}-{pillar_names_cn[j]}",
                    "组合明细": {pillar_names_cn[i]: g_i, pillar_names_cn[j]: g_j},
                    "状态": get_status(
                        "天干克", {"key": "adjacent" if is_adjacent else "distant"}
                    ),
                }

                interaction_shens.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}天干克"
                )
                pillar_dynamics[i]["frictional"].append(stem_control_detail)
                pillar_dynamics[j]["frictional"].append(stem_control_detail)
                all_interactions.append(stem_control_detail)
                interactions_by_type["天干克"].append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({g_i}{g_j})天干相克"
                )
                interaction_summary.append(
                    f"{pillar_names_abr[i]}{pillar_names_abr[j]}({g_i}{g_j})天干相克"
                )

    # === POST-CALCULATION FILTERING ===
    # --- Co-Arching (共拱) Detection ---
    # When a 半会 and a 半合(拱) both have the same missing (犹出) cardinal branch,
    # their combined aspiration toward that branch forms a Virtual Element Frame (虚拱局).
    # This is structurally more significant than two independent partial structures.
    #
    # BaZi principle: 共拱 (co-arching) amplifies the virtual element energy far beyond
    # what either partial structure achieves alone. When 一宥两伴 (one half-assembly +
    # one half-combination) point to the same cardinal, the chart’s qi field is
    # dominated by that element’s virtual presence.
    # 半合 uses the "邀出" field; 半会 uses the "犹出" field — both name the same concept
    # (the missing cardinal the partial structure is stretching toward), but were labelled
    # differently during detection.  The co-arching grouping must use the correct key for
    # each type so the shared-target lookup actually matches.
    arching_half_he = [
        item
        for item in all_interactions
        if item.get("类型") == "半合" and item.get("邀出") not in (None, "无")
    ]
    arching_half_hui = [
        item
        for item in all_interactions
        if item.get("类型") == "半会" and item.get("犹出") not in (None, "无")
    ]

    # Group by shared missing-cardinal target
    yao_chu_map = {}  # missing_branch -> {"ban_he": [...], "ban_hui": [...]}
    for item in arching_half_he:
        yc = item.get("邀出")  # 半合 key
        yao_chu_map.setdefault(yc, {"ban_he": [], "ban_hui": []})["ban_he"].append(item)
    for item in arching_half_hui:
        yc = item.get("犹出")  # 半会 key
        yao_chu_map.setdefault(yc, {"ban_he": [], "ban_hui": []})["ban_hui"].append(
            item
        )

    for missing_branch, groups in yao_chu_map.items():
        if not groups["ban_he"] or not groups["ban_hui"]:
            continue  # Need at least one of each for co-arching

        # Collect all pillars from both partial structures
        all_pillar_indices = set()
        all_pillar_names = []
        seen_pillar_indices = set()
        combined_detail = {}

        for item in groups["ban_he"] + groups["ban_hui"]:
            for pillar_name, branch in item.get("组合明细", {}).items():
                pidx = {
                    "\u5e74\u67f1": 0,
                    "\u6708\u67f1": 1,
                    "\u65e5\u67f1": 2,
                    "\u65f6\u67f1": 3,
                }.get(pillar_name)
                if pidx is not None and pidx not in seen_pillar_indices:
                    all_pillar_indices.add(pidx)
                    all_pillar_names.append(pillar_names_cn[pidx])
                    seen_pillar_indices.add(pidx)
                    combined_detail[pillar_name] = branch

        # Sort pillar names by index order
        all_pillar_names_sorted = sorted(
            all_pillar_names,
            key=lambda p: {
                "\u5e74\u67f1": 0,
                "\u6708\u67f1": 1,
                "\u65e5\u67f1": 2,
                "\u65f6\u67f1": 3,
            }[p],
        )

        # Determine element from the half-he (triple combination element)
        element = groups["ban_he"][0].get("元素", "")
        direction = groups["ban_hui"][0].get("方位", "")
        element_cn = {"水": "水", "木": "木", "火": "火", "金": "金"}.get(
            element, element
        )

        # Clash Override: if any branch inside the virtual frame is being clashed by
        # another branch elsewhere in the chart, the co-arching structure becomes
        # "turbid" (混杂).  The virtual element field is internally conflicted and cannot
        # assert full dominance — it manifests as 显著影响 rather than 强势主流.
        participating_branches = set(combined_detail.values())
        clashed_branches = {
            b for b in participating_branches if clash_map.get(b) in zhis
        }
        is_clashed = bool(clashed_branches)

        # Generalized virtual frame label — covers all four elements
        virtual_label_map = {
            "水": "虚水局",
            "火": "虚火局",
            "木": "虚木局",
            "金": "虚金局",
        }
        virtual_label = virtual_label_map.get(element_cn, "虚局")
        status_label = (
            f"共拱{element_cn}局({virtual_label}，混杂)"
            if is_clashed
            else f"共拱{element_cn}局({virtual_label})"
        )

        gong_gong_detail = {
            "类型": "共拱",
            "元素": element,
            "方位": direction,
            "组合": "-".join(all_pillar_names_sorted),
            "组合明细": combined_detail,
            "共拱目标": missing_branch,
            "状态": status_label,
            "混杂": is_clashed,
            "备注": (
                (
                    f"半会({groups['ban_hui'][0].get('组合', '')})与半合(拱)"
                    f"({groups['ban_he'][0].get('组合', '')})同拱{missing_branch}，"
                    f"虚{element_cn}局主导全局"
                )
                if not is_clashed
                else (
                    f"半会({groups['ban_hui'][0].get('组合', '')})与半合(拱)"
                    f"({groups['ban_he'][0].get('组合', '')})同拱{missing_branch}，"
                    f"但{'、'.join(sorted(clashed_branches))}遭冲，虚{element_cn}局混杂衰减"
                )
            ),
        }

        display_text = (
            f"共拱{element_cn}局(混杂虚局)"
            if is_clashed
            else f"共拱{element_cn}局(虚局)"
        )
        interactions_by_type["共拱"].append(display_text)
        interaction_summary.append(display_text)
        interaction_shens.append(f"共拱{element_cn}局")
        all_interactions.append(gong_gong_detail)

        # Mark both constituent interactions as part of a co-arching group
        for item in groups["ban_he"] + groups["ban_hui"]:
            item["共拱"] = True
            item["共拱目标"] = missing_branch

    # Apply hierarchical priority filtering to modulate interaction strength
    filtered_interactions = apply_bazi_master_priority(all_interactions, zhis)

    # Rebuild pillar_dynamics from filtered (modulated) interactions
    # Multi-Pillar Interaction Distribution Strategy:
    # ================================================
    # For multi-pillar interactions (三会, 三合), the SAME interaction object is distributed
    # to ALL affected pillars so each pillar shows complete context about multi-pillar dynamics.
    #
    # Deduplication Key: (pillar_idx, tier_key, item_id)
    #   - pillar_idx: Which pillar (0=Year, 1=Month, 2=Day, 3=Hour)
    #   - tier_key: Which tier (纲领层/气势层/琐碎层)
    #   - item_id: Object identity (prevents same object added to same pillar+tier twice)
    #
    # Three-Way Combination Examples:
    #   - 三会木局 (Year-Month-Day): Added to pillars 0, 1, 2 (same object, 3 times)
    #   - 三合火局 (Year-Month-Day): Added to pillars 0, 1, 2 (same object, 3 times)
    #
    # Key Point: extract_pillar_indices() maps "年柱-月柱-日柱" → (0, 1, 2)
    #            This ensures consistent multi-pillar routing across all interactions.

    # Initialize empty structure with modulated interactions
    pillar_dynamics_modulated = {
        0: {"第一梯队_纲领层": [], "第二梯队_气势层": [], "第三梯队_琐碎层": []},
        1: {"第一梯队_纲领层": [], "第二梯队_气势层": [], "第三梯队_琐碎层": []},
        2: {"第一梯队_纲领层": [], "第二梯队_气势层": [], "第三梯队_琐碎层": []},
        3: {"第一梯队_纲领层": [], "第二梯队_气势层": [], "第三梯队_琐碎层": []},
    }

    # Define tier assignment by interaction type (strength-modulated)
    tier1_types = ["三会", "三合", "六冲", "六合"]
    tier2_types = ["半会", "共拱", "半合", "天干冲", "天干克", "天干合"]
    tier3_types = [
        "三刑",
        "六害",
        "六破",
        "暗合",
        "无恩之刑",
        "恃势之刑",
        "无礼之刑",
        "自刑",
    ]

    # Populate pillar_dynamics_modulated with filtered interactions
    # Track added interactions by (pillar_idx, tier_key, item_id) to prevent duplicates
    # within the same pillar+tier combination
    added_interactions = set()

    for item in filtered_interactions:
        itype = item.get("类型")
        combo = item.get("组合", "")
        indices = extract_pillar_indices(combo)

        if not indices:
            # Robustness: Skip if pillar mapping failed
            continue

        # Determine tier based on interaction type
        if itype in tier1_types:
            tier_key = "第一梯队_纲领层"
        elif itype in tier2_types:
            tier_key = "第二梯队_气势层"
        elif itype in tier3_types:
            tier_key = "第三梯队_琐碎层"
        else:
            tier_key = "第三梯队_琐碎层"  # Default to tier 3

        # Distribute interaction to all affected pillars
        # For multi-pillar interactions (三会, 三合), indices will have 2-3 elements
        # Each pillar receiving the interaction gets the SAME object reference
        item_id = id(item)  # Use object identity for per-pillar deduplication

        for pillar_idx in indices:
            # Dedup key ensures same interaction not added twice to same pillar+tier
            dedup_key = (pillar_idx, tier_key, item_id)
            if dedup_key not in added_interactions:
                pillar_dynamics_modulated[pillar_idx][tier_key].append(item)
                added_interactions.add(dedup_key)

    # Build 柱位动态 with modulated interactions organized by pillar and tier
    pillar_dynamics_dict = {}
    for k in range(4):
        pillar_dynamics_dict[pillar_names_cn[k]] = {
            "第一梯队_纲领层": pillar_dynamics_modulated[k]["第一梯队_纲领层"],
            "第二梯队_气势层": pillar_dynamics_modulated[k]["第二梯队_气势层"],
            "第三梯队_琐碎层": pillar_dynamics_modulated[k]["第三梯队_琐碎层"],
        }

    # Build 关系总览 from filtered_interactions (ensures tier ordering and deduplication)
    # Only include interactions that have meaningful presence (强势主流 or 显著影响)
    # Exclude heavily suppressed interactions (大幅衰减, 消融吸收, 中等衰减) from overview
    summary_dict = {}  # Use dict to deduplicate while preserving tier order
    for item in filtered_interactions:
        strength = item.get("强度")
        # Only include interactions with active presence (前两档)
        if strength not in ("强势主流", "显著影响"):
            continue

        itype = item.get("类型")
        # For each interaction type, find its display text from interactions_by_type
        if itype in interactions_by_type:
            for text in interactions_by_type[itype]:
                if text not in summary_dict:
                    summary_dict[text] = None

    result = {
        "关系总览": list(summary_dict.keys()),
        "柱位动态": pillar_dynamics_dict,
        "判定优先级": {
            "第一梯队_纲领层": [
                "三会",
                "三合",
                "六冲",
                "六合",
            ],
            "第二梯队_气势层": [
                "半会",
                "共拱",
                "半合",
                "天干克",
                "天干合",
            ],
            "第三梯队_琐碎层": [
                "三刑",
                "六害",
                "六破",
                "暗合",
            ],
        },
    }

    return {"作用": result}


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from src.astronomer_calculations.bazi_pillars import get_bazi_pillars

    # python -m src.astronomer_calculations.interactions_gan_zhi_zuo_yong

    # Desmond's birthday example
    # solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    # datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    # tst_birthday, _ = get_true_solar_time(
    #     datetime_birthday, 1.3253, 103.808053
    # )  # Get true solar time

    # Corinne's birthday example
    solar_birthday = Solar.fromYmdHms(
        1987, 6, 3, 12, 6, 0
    )  # Create solar date June 3, 1987 at 12:06 PM
    tst_birthday, inputs_report = get_true_solar_time(
        datetime(1987, 6, 3, 12, 6, 0), 1.4759, 103.808053
    )
    lunar_birthday = tst_birthday.getLunar()

    print("阳历生日: " + solar_birthday.toYmdHms())
    print("真太阳时生日: " + tst_birthday.toYmdHms())

    lunar_birthday = tst_birthday.getLunar()  # Convert to lunar calendar

    bazi_json = get_bazi_pillars(tst_birthday.getLunar())
    print(f"{bazi_json}")

    # Get interactions in LLM-ready JSON format
    result = get_interactions(lunar_birthday)

    print(f"\n--- JSON Output for LLM ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))
