"""
This module calculates and analyzes interactions between Heavenly Stems (天干) and
Earthly Branches (地支) in a BaZi (八字) chart using a state-machine registry with
five-pass intelligent priority filtering. It detects 16 interaction types using
physics-based energy/resonance semantics for LLM clarity.

ARCHITECTURE OVERVIEW:

    The module uses a central InteractionRegistry system with BranchActor and StemActor
    entities that maintain state machines (ACTIVE → LOCKED → ABSORBED) and track which
    interactions touch each pillar. The five-pass priority filter systematically resolves
    competing interactions with declarative rules and tie-breaker logic.

CORE INNOVATION — Five-Pass Priority Filter + Stem Rooting Pass:

    Pass 1 (Structural Lock):
        For each branch with multiple triple-structure candidates (三会/三合):
        - Applies deterministic tie-breakers: 三会 > 三合, position (月支 preferred), proximity
        - Winning structure locks all participant branches (hard-locked)
        - Losers inject synthetic half-structures (半合/残会) for orphaned branch pairs
        - Remaining branches marked 中等衰减

    Pass 2 (Dual Lock — Two Rounds + Sub-round):
        - Round 1: All 六合 locked greedily (贪合忘冲)
          → Emits Broken Link signal: absorbs all 六冲 on that branch, marks partners VACANT
        - Round 1b: Unlocked branches claim their 六冲 as PRIMARY_六冲
        - Round 2: VACANT branches (freed by Broken Links) resolve to next-best secondary
          (forbids new 六合 to prevent circular standoffs)

    Passes 3–5 (Modulation):
        Read only — apply PRIORITY_RULE_TABLE to downgrade 强度 (never upgrade).
        - Pass 3: Apply branch-pair suppression rules
        - Pass 4: 拱局 (拱合/拱会) echo check and conflict marking
        - Pass 5: Final strength consolidation

    Pass S (Stem Rooting Modulation — orthogonal post-pass):
        Operates on the sorted result list after Pass 5 (bypasses registry/lock logic).
        Downgrades 天干合/克/冲 strength when participating stems are 无根 (floating).
        Classical principle: a floating stem cannot execute a 合/克/冲 at full force.
        - 天干合: one stem 无根 → cap "显著影响" (合而不化); both 无根 → cap "中等衰减"
        - 天干克: controller 无根 + target rooted → cap "大幅衰减" (克力瓦解);
                  controller 无根 + target 无根 → cap "中等衰减"
        - 天干冲: one stem 无根 → cap "显著影响"; both 无根 → cap "中等衰减"
        Uses _downgrade_if_stronger() — caps only; never upgrades.

KEY FEATURES:

    1. InteractionRegistry System:
       - Each interest gets a unique _iid (stable ID) and state tracking
       - BranchActor/StemActor agents track which interactions affect each pillar
       - O(1) lookups for state queries and type-based filtering
       - Deduplication via (pillar_idx, tier, item_id) key during output assembly

    2. Synthetic Injection:
       When a triple-structure loses Pass 1 competition, orphaned branch pairs
       are injected as synthetic 半合 (if from 三合) or 残会 (if from 三会).
    3. Broken Link Signaling:
       六合 lock immediately absorbs competing 六冲 and frees partner branches
       for secondary resolution — enables clean 贪合忘冲 mechanics.

    4. Declarative Priority Rules:
       PRIORITY_RULE_TABLE maps (lock_type, interaction_type) → 强度 downgrade.
       STRENGTH_REMARKS provides causal explanations (no generic noise).

    5. 拱局 Detection (拱合 + 拱会) — Virtual Arch System:
       Two classical arch subtypes, both requiring adjacent pillars and an unfilled
       missing cardinal (填实 check: missing branch absent from all 4 pillars).

       拱合 (Gong He — Sanhe arch):
         The two non-cardinal branches of a Sanhe triad are present on adjacent
         pillars; the cardinal is the missing virtual target. Cyclic distance = 4.
         Example: 申+辰 (Year-Month) → virtual 子 (Water cardinal).

       拱会 (Gong Hui — Sanhui arch):
         The two flanking branches of a Sanhui trio are present on adjacent pillars;
         the cardinal is the missing virtual target. Cyclic distance = 2.
         Example: 寅+辰 (Day-Hour) → virtual 卯 (Wood cardinal).

       Clash turbidity (混杂): if either participating branch is clashed, strength
       degrades from 强势主流 to 显著影响. 缺失支 carries the missing cardinal branch.

    6. Distance Semantics (距离 Field):
       All interactions include a numeric 距离 (converted to label in output):
       - 1 = 相邻 (adjacent pillars) → DIRECT/IMMEDIATE
       - 2 = 隔柱 (one gap) → MEDIATED/DELAYED
       - 3 = 远隔 (year-hour) → DISTANT
       Applies to all interaction types; 三合/三会 use minimum pairwise distance.

    7. Interaction Types (22 total):
       Tier 1 (Structural): 三会, 三合, 六冲, 六合, 天克地冲
       Tier 2 (Operational): 比和, 残会, 半合, 天干合, 干支透合, 天干克, 天干冲, 伏吟
       Tier 3 (Virtual):    拱合, 拱会 (non-occupying; echo-only strength)
       Tier 4 (Frictional): 三刑 (四种: 无恩之刑/恃势之刑/无礼之刑/自刑), 六害, 六破, 暗合

    8. Heavenly Stem Interactions:
       天干合 (Harmony) locks stems only when adjacent (distance == 1, 合绊 or 合化),
       absorbing 克/冲 on those two stems. Non-adjacent 天干合 is 遥合 — attractive
       but not binding, no lock issued.
       天干克 (Control) and 天干冲 (Clash) are directional forces only — they do not
       lock or prevent other stem interactions.

       All three types share a consistent field schema:
         类型, 组合, 组合明细, 距离, 主动方, 根基
       天干合 additionally carries:
         元素 (合化五行)
       主动方: "相互" for 天干合/冲; controller pillar label for 天干克.
       根基: {pillar_label: tier} for each participating stem — 4-tier system
             (深根/中根/浅根/无根) from bazi_pillars compute_pillar_rooting().
       Strength is further modulated by Pass S (see CORE INNOVATION above).

    9. Punishment Detection (三刑):
       - Ungrateful (无恩之刑): 寅-巳-申 set
       - Bullying (恃势之刑): 丑-未-戌 set
       - Uncivilized (无礼之刑): 子-卯 pair (正刑/遥刑)
       - Self-Punishment (自刑): Repeat branches (距离=1 adjacent/direct vs distant/harmonic)

   10. Peer Combinations (比和):
       Adjacent same-element branches (e.g., 寅卯, 巳午, 申酉, 亥子, and all earth pairs).
       Harmonious but non-binding; weaker than 六合/三合.
       Uses set-based element matching for precise validation.

   11. Multi-Pillar Distribution:
       Three-way interactions (三会, 三合) appear in all affected pillars
       (same object reference for context preservation).
       Deduplication via (idx, tier, _iid) prevents duplicate entries per pillar+tier.

INTERNAL KEYS (STRIPPED BEFORE OUTPUT):

    _iid:        Unique interaction identifier (for state tracking and dedup)
    _synthetic:  Flag indicating synthetic half-structure (from Pass 1 loser injection)
    _layer:      Reserved layer discriminator (unused in natal; available for cycle extensions)
    干柱索引:    Source stem pillar index for 干支透合 suppression logic
    支柱索引:    Target branch pillar index for 干支透合 suppression logic

These keys are stripped in-place during _build_pillar_dynamics (first encounter per item).

STRENGTH LEVELS (Hierarchical Degradation):

    强势主流        Active, full-force dominance
    显著影响        Weakened but still influential
    中等衰减        Moderately suppressed
    大幅衰减        Heavily suppressed
    消融吸收        Fully absorbed or neutralised

DECLARATIVE RULES & REMARKS:

    PRIORITY_RULE_TABLE: (lock_key, interaction_type) → 强度 downgrade
        lock_key examples: "STRUCTURAL_三会", "STRUCTURAL_三合",
                          "PRIMARY_六合", "PRIMARY_六冲", "STEM_天干合"

    STRENGTH_REMARKS: Causal explanations (e.g., "三会已完整成局，拱合虚局被吸收")

Main Functions:

    get_natal_interactions(pillars, void) → dict:
        Extract and analyze all pillar interactions from a BaZi chart.
        Returns LLM-optimized JSON with:
        - 关系总览: Summary of strong/significant interactions
        - 柱位动态: Per-pillar interactions distributed into four tiers

    apply_bazi_master_priority(registry) → list:
        Five-pass filter orchestrator. Returns filtered interactions with
        modulated 强度 and causal 备注 fields.

    extract_pillar_indices(pillar_indices_str) → tuple:
        Parse pillar combination strings ("年柱-月柱-日柱") into sorted indices.
        Uses priority-based mapping (full names before abbreviations).

    _build_pillar_dynamics(filtered) → list:
        Strip internal keys (_iid, _synthetic, etc.) and convert 距离 int → label.
        Returns the flat filtered list directly (no per-pillar distribution).

Validators:

    is_valid_punishment(branch1, branch2, natal_branches=None) → bool:
        Unified validator for all four punishment types (full/partial distinction).

    is_valid_peer_combination(branch1, branch2) → bool:
        Validates adjacent same-element branches for 比和.

Interaction Maps (Declarative Configuration):

    clash_map, harm_map, six_he_map, triple_he, cardinal_branches, directional_he,
    break_map, hidden_stem_he, stem_combines, stem_clashes, stem_controls,
    six_he_element_map: All branch/stem relationships and element mappings.

    INTERACTION_TIER_ORDER: 22 types mapped to tiers (0–17)
    STRENGTH_LEVELS, STRENGTH_ORDER: Hierarchical strength definitions

Dependencies:

    - lunar_python: BaZi chart extraction
    - datetime: Date/time handling
    - src.astronomer_calculations.solar_lunar_time: True solar time

Output Format:

    {
        "作用": {
            "关系总览": [status strings for strong/significant interactions],
            "柱位动态": [...],   # Flat list of interaction dicts, sorted by INTERACTION_TIER_ORDER
        }
    }

    Each interaction dict contains:
    - 类型: Interaction type
    - 组合: Pillar composition (e.g., "年柱-月柱")
    - 组合明细: Branch/stem mapping per pillar
    - 距离: Pillar distance — 1=相邻, 2=隔柱, 3=远隔 (all interaction types)
    - 元素: Produced/transformed element (applicable to: 三会, 三合, 半合 — triple element;
      六合 — transformation element; 比和 — shared peer element; 拱合/拱会 — arched-toward
      cardinal element; 残会 — directional element; 天干合 — 合化五行)
    - 缺失支: Missing branch in combinations — missing non-cardinal for 半合/残会,
      missing cardinal for 拱合/拱会 (the virtual target of the arch)
    - 主动方: Controller pillar label for 天干克; "相互" for 天干合/冲
    - 根基: {pillar_label: tier} 4-tier rooting per participating stem (天干合/克/冲 only)
    - 强度: Modulated strength (强势主流/显著影响/中等衰减/大幅衰减/消融吸收)
    - 备注: Causal note (if suppressed/absorbed)

    Output Field Order (registration-time fields; pass-added fields append afterward):
        "类型"           — all types
        "形态"           — if present (六冲, 六合, 伏吟, 刑×4, 六害, 六破, 天干合/克/冲)
        "组合明细"       — all types
        "根基"           — if present (天干合, 天干克, 天干冲 only)
        "距离"           — all types
        "元素"           — if present (三会, 三合, 六合, 比和, 半合, 残会, 拱合, 拱会, 天干合)
        "藏干详情"       — if present (干支透合 only)
        "缺失支"         — if present (半合, 拱合, 残会, 拱会)
        "主动方"         — if present (天干合, 天干克, 天干冲)
    Pass-added (always at end):
        "强度", "备注", "旬空涉及", "互换空亡涉及"

Implemented:
    - compute_pillar_rooting() — per-pillar 4-tier rooting summary (importable by cycle modules)
    - _pass_stem_rooting()     — Pass S stem rooting modulation (importable by cycle modules)
    - BRANCH_HIDDEN_ROOTING    — hidden-stem rooting weight table
"""

import dataclasses

from lunar_python.util import LunarUtil
from src.utils.logging import get_logger

logger = get_logger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# NATAL CHART INTERACTIONS
# Five-Pass Resource Consumption Filter with InteractionRegistry
#
# SECTION 1 — Constants & Maps
# SECTION 2 — Validators & Utilities
# SECTION 3 — InteractionRegistry & Actors
# SECTION 4 — Priority Filter  (apply_bazi_master_priority)
# SECTION 5 — Detection Helpers
# SECTION 6 — Output Assembly
# SECTION 7 — Orchestrator     (get_natal_interactions)
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Constants & Maps
# ══════════════════════════════════════════════════════════════════════════════

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
# Uses canonical pair ordering: tuple(sorted([branch1, branch2])) to ensure single map entry
six_he_element_map = {
    ("丑", "子"): {"primary": "土"},
    ("亥", "寅"): {"primary": "木"},
    ("卯", "戌"): {"primary": "火"},
    ("辰", "酉"): {"primary": "金"},
    ("巳", "申"): {"primary": "水"},
    ("午", "未"): {"primary": "土"},
}

# Triple Combination Map (Needs 2 out of 3 for a "Partial" or 3 for "Full")
# Structure: Element -> [Growing, Peak/Cardinal, Storage/Graveyard]
triple_he = {
    "水": {"申", "子", "辰"},  # Cardinal: 子 | Growing: 申 | Graveyard: 辰
    "木": {"亥", "卯", "未"},  # Cardinal: 卯 | Growing: 亥 | Graveyard: 未
    "火": {"寅", "午", "戌"},  # Cardinal: 午 | Growing: 寅 | Graveyard: 戌
    "金": {"巳", "酉", "丑"},  # Cardinal: 酉 | Growing: 巳 | Graveyard: 丑
}

# Canonical cardinal (帝旺) branch for each element — used by 三合 peak detection,
# 三会 rooting check, and 半合 arching state. Single source of truth.
cardinal_branches = {"水": "子", "木": "卯", "火": "午", "金": "酉"}

# Directional Combinations (San Hui) - Three Meetings of entire season
directional_he = {
    "木": {"寅", "卯", "辰"},
    "火": {"巳", "午", "未"},
    "金": {"申", "酉", "戌"},
    "水": {"亥", "子", "丑"},
}

# San Hui direction mapping — used to identify which directional quadrant
SAN_HUI_DIRECTION = {
    frozenset(["寅", "卯", "辰"]): "东",
    frozenset(["巳", "午", "未"]): "南",
    frozenset(["申", "酉", "戌"]): "西",
    frozenset(["亥", "子", "丑"]): "北",
}

# Direction to element mapping — converts direction to five-element
DIRECTION_TO_ELEMENT = {
    "东": "木",  # East → Wood
    "南": "火",  # South → Fire
    "西": "金",  # West → Metal
    "北": "水",  # North → Water
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
# Zi Ping (子平) methods
hidden_stem_he: dict[str, set[str]] = {
    "寅": {"丑"},  # 甲己合
    "丑": {"寅"},
    "午": {"亥"},  # 丁壬合
    "亥": {"午"},
}

# 通禄合 (Tōng Lù Hé) — Palace/Lu Combination method for an he. not in used.
# hidden_stem_he: {
#         "卯": {"申"},
#         "申": {"卯"},
#         "寅": {"午"},
#         "午": {"寅"},
#         "巳": {"酉", "子"},
#         "酉": {"巳"},
#         "子": {"巳"},
#     }

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

stem_controls = frozenset(
    {
        ("庚", "甲"),
        ("庚", "乙"),
        ("辛", "甲"),
        ("辛", "乙"),
        ("甲", "戊"),
        ("甲", "己"),
        ("乙", "戊"),
        ("乙", "己"),
        ("戊", "壬"),
        ("戊", "癸"),
        ("己", "壬"),
        ("己", "癸"),
        ("壬", "丙"),
        ("壬", "丁"),
        ("癸", "丙"),
        ("癸", "丁"),
        ("丙", "庚"),
        ("丙", "辛"),
        ("丁", "庚"),
        ("丁", "辛"),
    }
)

# ── 合化五行 lookup — element produced by each 天干合 pair ───────────────────
# 甲己→土, 乙庚→金, 丙辛→水, 丁壬→木, 戊癸→火
_STEM_COMBINE_ELEMENT: dict[str, str] = {
    "甲": "土",
    "己": "土",
    "乙": "金",
    "庚": "金",
    "丙": "水",
    "辛": "水",
    "丁": "木",
    "壬": "木",
    "戊": "火",
    "癸": "火",
}

# Elemental control cycle (五行相克): used by _check_he_hua_conditions (假化 breaker check).
_ELEMENT_CONTROLS: dict[str, str] = {
    "木": "金",
    "火": "水",
    "土": "木",
    "金": "火",
    "水": "土",
}

# Month branch → elements that are 旺 or 相 in that branch's season.
# Used by _check_he_hua_conditions (Condition 2: 得令).
_ZHI_WANG_XIANG_ELEMENTS = {
    "寅": frozenset({"木", "火"}),
    "卯": frozenset({"木", "火"}),
    "辰": frozenset({"木", "火"}),  # fix: spring, no earth
    "巳": frozenset({"火", "土"}),
    "午": frozenset({"火", "土"}),
    "未": frozenset({"火", "土"}),  # summer, 火旺土相 (same as 巳午)
    "申": frozenset({"金", "水"}),
    "酉": frozenset({"金", "水"}),
    "戌": frozenset({"金", "水"}),  # fix: autumn, no earth
    "亥": frozenset({"水", "木"}),
    "子": frozenset({"水", "木"}),
    "丑": frozenset({"水", "木"}),  # fix: winter, no earth
}

# Element → branches where it is 本气 (primary hidden stem).
# Used by _check_he_hua_conditions (Condition 5: 化神有根).
_ELEMENT_BEN_QI_ZHI: dict[str, frozenset] = {
    "木": frozenset({"寅", "卯"}),
    "火": frozenset({"巳", "午"}),
    "土": frozenset({"辰", "未", "戌", "丑"}),
    "金": frozenset({"申", "酉"}),
    "水": frozenset({"亥", "子"}),
}

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

# STRUCTURED PUNISHMENT DEFINITIONS
UNGRATEFUL_PUNISHMENT = {"name": "无恩之刑", "universe": {"寅", "巳", "申"}}
BULLYING_PUNISHMENT = {"name": "恃势之刑", "universe": {"丑", "戌", "未"}}
RUDE_PUNISHMENT = {"name": "无礼之刑", "universe": {"子", "卯"}}
SELF_PUNISHMENT = {"name": "自刑", "universe": {"辰", "午", "酉", "亥"}}


# 比和 — classical same-element peer harmony.
# Covers all same-element branch pairings:
#   Adjacent phase pairs: 寅卯(木), 巳午(火), 申酉(金), 亥子(水)
#   Earth pairs: all 6 distinct pairs among 辰丑未戌 (all are 土)
#     辰戌 and 丑未 are also 六冲; 辰丑/辰未/丑戌/未戌 are not.
#     All registered independently; priority filter handles suppression.
#   Same-branch pairs: handled dynamically in is_valid_peer_combination.
_PEER_ELEMENT_MAP: dict[tuple, str] = {
    ("寅", "卯"): "木",
    ("卯", "寅"): "木",
    ("巳", "午"): "火",
    ("午", "巳"): "火",
    ("申", "酉"): "金",
    ("酉", "申"): "金",
    ("亥", "子"): "水",
    ("子", "亥"): "水",
    # Earth — all 6 distinct pairs among the four 土 branches
    ("辰", "丑"): "土",
    ("丑", "辰"): "土",
    ("辰", "未"): "土",
    ("未", "辰"): "土",
    ("辰", "戌"): "土",
    ("戌", "辰"): "土",
    ("丑", "未"): "土",
    ("未", "丑"): "土",
    ("丑", "戌"): "土",
    ("戌", "丑"): "土",
    ("未", "戌"): "土",
    ("戌", "未"): "土",
}


STRENGTH_LEVELS = {
    "强势主流": "主要作用力，完全激活",
    "显著影响": "受压但仍有影响力",
    "中等衰减": "能量衰减至中等水平",
    "大幅衰减": "被压制，作用力微弱",
    "消融吸收": "被完全吸收或消融",
}

STRENGTH_ORDER = {
    "强势主流": 0,
    "显著影响": 1,
    "中等衰减": 2,
    "大幅衰减": 3,
    "消融吸收": 4,
}


INTERACTION_TIER_ORDER = {
    "三会": 0,
    "三合": 1,
    "六冲": 2,
    "天克地冲": 2,  # treated as same tier as 六冲 for priority purposes. Combi of 六冲 and 天干冲
    "六合": 3,
    "半合": 4,
    "残会": 5,
    "天干合": 6,
    "拱合": 7,
    "拱会": 8,
    "比和": 9,
    "伏吟": 10,
    "无恩之刑": 11,
    "恃势之刑": 11,
    "无礼之刑": 11,
    "自刑": 11,
    "六害": 12,
    "六破": 13,
    "天干克": 14,
    "天干冲": 15,
    "暗合": 16,
    "干支透合": 17,
}

# ── Declarative Priority Rule Table ──────────────────────────────────────────
# Key: (lock_type, interaction_type) → 强度
# Only downgrades — the pass logic never upgrades via this table.
# lock_type: "STRUCTURAL_三会" | "STRUCTURAL_三合"
#            "PRIMARY_六合"    | "PRIMARY_六冲"    | "PRIMARY_天克地冲"
#            "STEM_天干合"     | "STEM_天干克"     | "STEM_天克地冲"
PRIORITY_RULE_TABLE = {
    # STRUCTURAL_三会
    ("STRUCTURAL_三会", "三合"): "消融吸收",
    ("STRUCTURAL_三会", "六合"): "大幅衰减",
    ("STRUCTURAL_三会", "六冲"): "大幅衰减",
    ("STRUCTURAL_三会", "半合"): "大幅衰减",
    ("STRUCTURAL_三会", "残会"): "大幅衰减",
    ("STRUCTURAL_三会", "六害"): "大幅衰减",
    ("STRUCTURAL_三会", "六破"): "大幅衰减",
    ("STRUCTURAL_三会", "无恩之刑"): "大幅衰减",
    ("STRUCTURAL_三会", "恃势之刑"): "大幅衰减",
    ("STRUCTURAL_三会", "无礼之刑"): "大幅衰减",
    ("STRUCTURAL_三会", "自刑"): "大幅衰减",
    ("STRUCTURAL_三会", "比和"): "显著影响",
    ("STRUCTURAL_三会", "暗合"): "显著影响",
    # STRUCTURAL_三合
    ("STRUCTURAL_三合", "六合"): "大幅衰减",
    ("STRUCTURAL_三合", "六冲"): "中等衰减",
    ("STRUCTURAL_三合", "半合"): "大幅衰减",
    ("STRUCTURAL_三合", "残会"): "大幅衰减",
    ("STRUCTURAL_三合", "六害"): "大幅衰减",
    ("STRUCTURAL_三合", "六破"): "大幅衰减",
    ("STRUCTURAL_三合", "无恩之刑"): "大幅衰减",
    ("STRUCTURAL_三合", "恃势之刑"): "大幅衰减",
    ("STRUCTURAL_三合", "无礼之刑"): "大幅衰减",
    ("STRUCTURAL_三合", "自刑"): "大幅衰减",
    ("STRUCTURAL_三合", "比和"): "显著影响",
    ("STRUCTURAL_三合", "暗合"): "显著影响",
    # PRIMARY_六合 (贪合忘冲)
    ("PRIMARY_六合", "六冲"): "消融吸收",
    ("PRIMARY_六合", "六害"): "大幅衰减",
    ("PRIMARY_六合", "六破"): "大幅衰减",
    ("PRIMARY_六合", "无恩之刑"): "大幅衰减",
    ("PRIMARY_六合", "恃势之刑"): "大幅衰减",
    ("PRIMARY_六合", "无礼之刑"): "大幅衰减",
    ("PRIMARY_六合", "自刑"): "大幅衰减",
    ("PRIMARY_六合", "半合"): "中等衰减",
    ("PRIMARY_六合", "残会"): "中等衰减",
    ("PRIMARY_六合", "比和"): "显著影响",
    ("PRIMARY_六合", "暗合"): "显著影响",
    # PRIMARY_六冲 (刑冲并见 amplification)
    ("PRIMARY_六冲", "六合"): "消融吸收",
    ("PRIMARY_六冲", "六害"): "显著影响",
    ("PRIMARY_六冲", "六破"): "显著影响",
    ("PRIMARY_六冲", "无恩之刑"): "显著影响",
    ("PRIMARY_六冲", "恃势之刑"): "显著影响",
    ("PRIMARY_六冲", "无礼之刑"): "显著影响",
    ("PRIMARY_六冲", "自刑"): "显著影响",
    ("PRIMARY_六冲", "半合"): "大幅衰减",
    ("PRIMARY_六冲", "残会"): "大幅衰减",
    ("PRIMARY_六冲", "比和"): "显著影响",
    ("PRIMARY_六冲", "暗合"): "显著影响",
    # STEM locks
    # 天干合 in place: harmonisation absorbs both clash and control
    ("STEM_天干合", "天干克"): "消融吸收",
    ("STEM_天干合", "天干冲"): "消融吸收",
    # PRIMARY_天克地冲 — pillar-level composite (stem clash + branch clash)
    ("PRIMARY_天克地冲", "六合"): "消融吸收",  # 贪合忘冲 absorbs branch clash component
    ("PRIMARY_天克地冲", "六害"): "显著影响",
    ("PRIMARY_天克地冲", "六破"): "显著影响",
    ("PRIMARY_天克地冲", "半合"): "大幅衰减",
    ("PRIMARY_天克地冲", "残会"): "大幅衰减",
    ("PRIMARY_天克地冲", "比和"): "显著影响",
    ("PRIMARY_天克地冲", "暗合"): "显著影响",
    ("PRIMARY_天克地冲", "干支透合"): "大幅衰减",
    ("PRIMARY_天克地冲", "无恩之刑"): "显著影响",
    ("PRIMARY_天克地冲", "恃势之刑"): "显著影响",
    ("PRIMARY_天克地冲", "无礼之刑"): "显著影响",
    ("PRIMARY_天克地冲", "自刑"): "显著影响",
    ("PRIMARY_天克地冲", "伏吟"): "大幅衰减",
    # PRIMARY_六冲 cross-lock: branch already consumed; 天克地冲 on same branch weakened
    ("PRIMARY_六冲", "天克地冲"): "大幅衰减",
    # STRUCTURAL fields suppress pillar-level composites
    ("STRUCTURAL_三会", "天克地冲"): "大幅衰减",
    ("STRUCTURAL_三会", "伏吟"): "大幅衰减",
    ("STRUCTURAL_三合", "天克地冲"): "中等衰减",
    ("STRUCTURAL_三合", "伏吟"): "大幅衰减",
    # PRIMARY_六合 (贪合忘冲) — absorbs branch clash; stem clash persists weakened
    ("PRIMARY_六合", "天克地冲"): "大幅衰减",
    ("PRIMARY_六合", "伏吟"): "中等衰减",
    # PRIMARY_六冲 disrupts stagnation
    ("PRIMARY_六冲", "伏吟"): "显著影响",
    # Branch/Stem locks → 干支透合
    # 干支透合 is a covert stem-to-hidden-stem bond; always secondary to direct interactions.
    # STRUCTURAL: target branch in a 三会/三合 field — hidden stems consumed by transformation.
    # PRIMARY_六合: target branch occupied by 六合 (贪合) — hidden stems tied up, unavailable.
    # PRIMARY_六冲: target branch clashed — hidden stems scattered (冲则气散).
    # STEM_天干合: source stem already directly combining — covert bond absorbed (贪合忘合).
    # STEM_天干克 omitted: 克 operates stem-to-stem; branch hidden stem is a different layer.
    ("STRUCTURAL_三会", "干支透合"): "大幅衰减",
    ("STRUCTURAL_三合", "干支透合"): "大幅衰减",
    ("PRIMARY_六合", "干支透合"): "大幅衰减",
    ("PRIMARY_六冲", "干支透合"): "大幅衰减",
    ("STEM_天干合", "干支透合"): "消融吸收",
}

# ── Declarative Remarks Table ─────────────────────────────────────────────────
# Causal explanations only — no generic noise.
# LLM derives interpretation; Python provides mechanism context.

STRENGTH_REMARKS = {
    ("STRUCTURAL_三会", "三合"): "三会方位场已成，三合独立性被吸收",
    ("STRUCTURAL_三会", "拱合"): "三会已完整成局，拱合虚局被吸收",
    ("STRUCTURAL_三会", "六冲"): "冲力被三会方位场吸收",
    ("STRUCTURAL_三合", "六冲"): "与三合结构形成内部张力，冲力被部分吸收",
    ("STRUCTURAL_三合", "六合"): "被三合压制，合力弱化",
    ("PRIMARY_六合", "六冲"): "贪合忘冲：六合在位，冲力被合化消融",
    ("PRIMARY_六合", "六害"): "六合主导，害力被合力压制",
    ("PRIMARY_六合", "六破"): "六合主导，破力被合力压制",
    ("PRIMARY_六冲", "六害"): "刑冲并见：冲位不稳，害力乘虚协同增强",
    ("PRIMARY_六冲", "六破"): "刑冲并见：冲位不稳，破力乘虚协同增强",
    ("PRIMARY_六冲", "无恩之刑"): "刑冲并见：冲位已破，无恩之刑乘虚而入",
    ("PRIMARY_六冲", "恃势之刑"): "刑冲并见：冲位已破，恃势之刑乘虚而入",
    ("PRIMARY_六冲", "无礼之刑"): "刑冲并见：冲位已破，无礼之刑乘虚而入",
    ("PRIMARY_六冲", "自刑"): "刑冲并见：冲位已破，自刑内耗加剧",
    ("STEM_天干合", "天干克"): "天干合化锁定，克力被合化消融",
    ("STEM_天干合", "天干冲"): "天干合化锁定，冲力被合化消融",
    (
        "INTERACTION_STATE_天干合",
        "binding",
    ): "遥合绊定：虽有引力但距离阻隔，缺乏化神助力，合力虚浮流于表面",
    ("STRUCTURAL_三会", "干支透合"): "三会方位场锁定地支，藏干不得透出，干支透合受压",
    ("STRUCTURAL_三合", "干支透合"): "三合局锁定地支，藏干不得透出，干支透合受压",
    ("PRIMARY_六合", "干支透合"): "目标地支已被六合占位，藏干潜合力被合力压制",
    ("PRIMARY_六冲", "干支透合"): "目标地支被六冲气散，藏干无力应合",
    ("STEM_天干合", "干支透合"): "源天干已与他干直合，贪合之下，藏干透合消融",
("INTERACTION_STATE_拱合", "echo"): "虚局与实局同元素共鸣，气场压倒性主导",
    ("INTERACTION_STATE_拱合", "suppressed"): "虚局被异元素结构压制，共鸣瓦解",
    ("INTERACTION_STATE_拱合", "turbid"): "虚局参与支遭冲，框架混杂衰减",
    ("INTERACTION_STATE_拱会", "echo"): "虚局与实局同元素共鸣，气场压倒性主导",
    ("INTERACTION_STATE_拱会", "suppressed"): "虚局被异元素结构压制，共鸣瓦解",
    ("INTERACTION_STATE_拱会", "turbid"): "虚局参与支遭冲，框架混杂衰减",
    ("STRUCTURAL_VACANT", "branch"): "贪合忘冲释放，该柱位主动开放，易受外部影响",
    ("STRUCTURAL_三会", "天克地冲"): "三会方位场主导，天克地冲烈度受压",
    ("STRUCTURAL_三合", "天克地冲"): "三合格局稳固，天克地冲烈度受压",
    ("PRIMARY_六合", "天克地冲"): "贪合忘冲：六合在位，地冲被合化，天克独留",
    ("INTERACTION_CONTEXT_天克地冲", "day_master"): "日柱天克地冲，命主根基受双重冲击",
    ("INTERACTION_CONTEXT_伏吟", "day_master"): "日柱伏吟，命主气场自我凝滞",
    ("DISTANCE_3", "六冲"): "年时相距三柱，冲势内收，作用由外部事件转为内在张力",
    ("DISTANCE_3", "天干克"): "年时相距三柱，远距衰减加深",
    ("DISTANCE_3", "天干冲"): "年时相距三柱，远距衰减加深",
    ("DISTANCE_3", "天干合"): "年时相距三柱，远距衰减加深",
}

# ── Default Strength Table ────────────────────────────────────────────────────
# (interaction_type, distance) → 强度
# distance: 1 = adjacent (紧贴), 2 = moderate-distant, 3 = year-hour (年柱-时柱)
# Pass 5: any item without 强度 looks up (type, distance); falls back to (type, 2).
# Only types whose year-hour strength differs from distance-2 need a (type, 3) entry.

DEFAULT_STRENGTH = {
    ("三会", 1): "强势主流",
    ("三会", 2): "强势主流",
    ("三合", 1): "强势主流",
    ("三合", 2): "强势主流",
    ("六冲", 1): "强势主流",
    ("六冲", 2): "显著影响",
    (
        "六冲",
        3,
    ): "中等衰减",  # year-hour: further decay; remark applied via STRENGTH_REMARKS
    ("六合", 1): "强势主流",
    ("六合", 2): "大幅衰减",
    ("六合", 3): "大幅衰减",
    ("半合", 1): "强势主流",
    ("拱合", 1): "强势主流",
    ("残会", 1): "强势主流",
    ("残会", 2): "显著影响",
    ("拱会", 1): "强势主流",
    ("天干合", "合化"):  "强势主流",   # full transformation (day master not involved)
    ("天干合", "化气格"): "强势主流",  # true transformation (day master is one of the pair)
    ("天干合", "假化"):  "显著影响",   # unstable — breaker element present
    ("天干合", "合绊"):  "中等衰减",   # binding without transformation
    ("天干合", "遥合"):  "大幅衰减",   # non-adjacent attraction
    ("天干克", 1): "强势主流",
    ("天干克", 2): "中等衰减",
    ("天干克", 3): "大幅衰减",
    ("天干冲", 1): "强势主流",
    ("天干冲", 2): "中等衰减",
    ("天干冲", 3): "大幅衰减",
    ("六害", 1): "显著影响",
    ("六害", 2): "中等衰减",
    ("六害", 3): "大幅衰减",
    ("六破", 1): "显著影响",
    ("六破", 2): "中等衰减",
    ("六破", 3): "大幅衰减",
    ("比和", 1): "显著影响",
    ("比和", 2): "中等衰减",
    ("暗合", 1): "显著影响",
    ("干支透合", 1): "显著影响",
    ("干支透合", 2): "中等衰减",
    ("天克地冲", 1): "强势主流",
    ("天克地冲", 2): "强势主流",
    ("天克地冲", 3): "中等衰减",
    ("伏吟", 1): "显著影响",
    ("伏吟", 2): "中等衰减",
    ("伏吟", 3): "中等衰减",
}

# ── Punishment Strength Table ─────────────────────────────────────────────────
# (type, 形态, distance) → 强度
# Consulted by _pass5_defaults for _XK_XING_TYPES; supersedes DEFAULT_STRENGTH for these types.
_PUNISHMENT_STRENGTH: dict[tuple, str] = {
    # 无恩之刑 — full triad always dominant regardless of distance
    ("无恩之刑", "三刑全", 1): "强势主流",
    ("无恩之刑", "三刑全", 2): "强势主流",
    ("无恩之刑", "三刑全", 3): "强势主流",
    ("无恩之刑", "半刑 - 紧邻之刑", 1): "显著影响",
    ("无恩之刑", "半刑 - 隔柱之刑", 2): "中等衰减",
    ("无恩之刑", "刑 - 遥隔之刑", 3): "大幅衰减",
    # 恃势之刑 — same pattern as 无恩之刑
    ("恃势之刑", "三刑全", 1): "强势主流",
    ("恃势之刑", "三刑全", 2): "强势主流",
    ("恃势之刑", "三刑全", 3): "强势主流",
    ("恃势之刑", "半刑 - 紧邻之刑", 1): "显著影响",
    ("恃势之刑", "半刑 - 隔柱之刑", 2): "中等衰减",
    ("恃势之刑", "刑 - 遥隔之刑", 3): "大幅衰减",
    # 无礼之刑 — distance-only graduation (always two branches)
    ("无礼之刑", "正刑", 1): "显著影响",
    ("无礼之刑", "遥刑", 2): "中等衰减",
    ("无礼之刑", "遥刑", 3): "大幅衰减",
    # 自刑 — inherently weaker; steeper distance decay
    ("自刑", "正刑", 1): "显著影响",
    ("自刑", "遥刑", 2): "中等衰减",
    ("自刑", "遥刑", 3): "大幅衰减",
}

# ── Xun Kong (旬空) Constants ────────────────────────────────────────────────
_STRENGTH_BY_RANK = {v: k for k, v in STRENGTH_ORDER.items()}

_XK_HE_TYPES = frozenset({"六合", "三合", "三会", "半合", "拱会", "残会"})
_XK_CHONG_TYPES = frozenset({"六冲", "天克地冲"})
_XK_XING_TYPES = frozenset({"无恩之刑", "恃势之刑", "无礼之刑", "自刑"})
_XK_HAI_PO_TYPES = frozenset({"六害", "六破"})
_XK_MISC_TYPES = frozenset({"暗合", "干支透合", "比和", "拱合", "伏吟"})
_XK_STEM_ONLY = frozenset({"天干合", "天干克", "天干冲"})

_XK_REMARKS = {
    "合_single": "{pillars}支落旬空，合力虚浮，力场不实",
    "冲开旬空": "冲开旬空，虚局受激",
    "双空相冲": "{pillars}支双空相冲，冲力涣散",
    "刑_single": "{pillars}支落旬空，刑力减弱",
    "害破_single": "{pillars}支落旬空，害破力场减弱",
    "misc_single": "{pillars}支落旬空，合力虚浮",
}

_XK_MUTUAL_REMARKS: dict[frozenset, str] = {
    frozenset({"年柱", "日柱"}): "根不养花，年日互换落空，双空无救",
    frozenset({"月柱", "日柱"}): "路不载人，月日互换落空，双空无救",
    frozenset({"日柱", "时柱"}): "花不结果，日时互换落空，双空无救",
}

# Pillar name constants
_PILLAR_NAMES_CN = ["年柱", "月柱", "日柱", "时柱"]
_PILLAR_IDX_MAP = {"年柱": 0, "月柱": 1, "日柱": 2, "时柱": 3}
_PILLAR_ABBR_MAP = {"年": 0, "月": 1, "日": 2, "时": 3}
_PILLAR_NAME_SET = frozenset(
    _PILLAR_NAMES_CN
)  # fast membership test; avoids rebuilding per call
_STEM_LOCK_PRIORITY = [2, 1, 3, 0]  # 日柱=2 absolute anchor

# ── Xun Kong (旬空) Helpers ───────────────────────────────────────────────────


def _is_branch_in_xun_kong(branch: str, pillar_name: str, xun_kong_data: dict) -> bool:
    pd = xun_kong_data.get(pillar_name)
    return bool(pd and branch in pd.get("旬空", ""))


def _extract_branch_pairs(combo_detail: dict) -> list:
    pairs = []
    for pn, val in combo_detail.items():
        if pn not in _PILLAR_NAME_SET:
            continue
        if isinstance(val, str) and len(val) == 1 and val in branch_elements:
            pairs.append((pn, val))
    return pairs


def _build_xk_remark(void_pillars: list, rule: str) -> str:
    template = _XK_REMARKS.get(rule, "{pillars}旬空")
    return template.format(pillars="、".join(void_pillars))


def _downgrade_by_one_tier_xk(item: dict, remark: str) -> None:
    current_rank = STRENGTH_ORDER.get(item.get("强度", "强势主流"), 0)
    new_rank = min(current_rank + 1, 4)
    if new_rank > current_rank:
        item["强度"] = _STRENGTH_BY_RANK[new_rank]
    existing = item.get("备注", "")
    item["备注"] = (existing + "；" + remark) if existing else remark


def _append_remark_xk(item: dict, remark: str) -> None:
    existing = item.get("备注", "")
    item["备注"] = (existing + "；" + remark) if existing else remark


def _downgrade_mutual_void(item: dict, remark: str) -> None:
    """Downgrade one tier, capped at 大幅衰减 (rank 3). Void alone never fully nullifies."""
    current_rank = STRENGTH_ORDER.get(item.get("强度", "强势主流"), 0)
    new_rank = min(current_rank + 1, 3)
    if new_rank > current_rank:
        item["强度"] = _STRENGTH_BY_RANK[new_rank]
    existing = item.get("备注", "")
    item["备注"] = (existing + "；" + remark) if existing else remark


def _pass6b_mutual_void(filtered: list, active_mutual: set) -> None:
    """
    Pass 6b — Mutual Void (互换空亡) modulation.

    Runs after the primary void loop. For each active mutual void pair
    (年日 / 月日 / 日时), any direct interaction between those two pillars
    receives one additional tier downgrade (capped at 大幅衰减) with the
    appropriate classical remark.

    For 3-pillar interactions (三合/三会) where a 2-pillar mutual void subset
    is involved: remark only, no extra downgrade (primary void already handled it).
    """
    for item in filtered:
        if item.get("类型") in _XK_STEM_ONLY:
            continue
        if item.get("强度") == "消融吸收":
            continue

        pairs = _extract_branch_pairs(item.get("组合明细", {}))
        if not pairs:
            continue
        pillar_set = {pn for pn, _ in pairs}

        matched_pair = next((mp for mp in active_mutual if mp <= pillar_set), None)
        if matched_pair is None:
            continue

        remark = _XK_MUTUAL_REMARKS[matched_pair]
        if pillar_set == matched_pair:
            # Direct 2-pillar interaction between the mutually voided pair
            _downgrade_mutual_void(item, remark)
        else:
            # Multi-pillar interaction (三合/三会) — remark only
            _append_remark_xk(item, remark)
        item["互换空亡涉及"] = sorted(matched_pair)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Validators & Utilities
# ══════════════════════════════════════════════════════════════════════════════


def extract_pillar_indices(pillar_indices_str: str) -> tuple:
    """
    Extract sorted unique pillar indices from a combination string like "年柱-月柱".
    Priority 1: full names.  Priority 2: abbreviated names.
    Always returns a tuple — empty () if no valid indices found.
    Callers can safely do `for idx in extract_pillar_indices(...)` with no None guard.
    """
    if not pillar_indices_str:
        return ()
    indices = []
    for part in pillar_indices_str.split("-"):
        part = part.strip()
        if not part:
            continue
        if part in _PILLAR_IDX_MAP:
            indices.append(_PILLAR_IDX_MAP[part])
        elif part in _PILLAR_ABBR_MAP:
            indices.append(_PILLAR_ABBR_MAP[part])
    return tuple(sorted(set(indices)))




def is_valid_punishment(
    branch1: str, branch2: str, natal_branches: list = None
) -> dict | None:
    """Set-based punishment validator. Returns result dict or None."""
    if branch1 == branch2:
        if branch1 in SELF_PUNISHMENT["universe"]:
            return {"type": "自刑", "branch_count": 1}
        return None
    bs = {branch1, branch2}
    if bs == RUDE_PUNISHMENT["universe"]:
        return {"type": "无礼之刑", "branch_count": 2}
    for punishment in (UNGRATEFUL_PUNISHMENT, BULLYING_PUNISHMENT):
        if bs.issubset(punishment["universe"]):
            if natal_branches:
                branch_count = len((set(natal_branches) | bs) & punishment["universe"])
            else:
                branch_count = len(bs)
            return {"type": punishment["name"], "branch_count": branch_count}
    return None


def is_valid_peer_combination(branch1: str, branch2: str) -> dict | None:
    """
    Returns 比和 dict or None.
    Covers: adjacent phase pairs, earth clash pairs (辰戌/丑未), and
    same-branch repetition across pillars (e.g. 午午).
    """
    # Same branch in two different pillars — element from branch_elements
    if branch1 == branch2:
        return {"type": "比和", "element": branch_elements[branch1]}
    pair = (branch1, branch2)
    if pair in _PEER_ELEMENT_MAP:
        return {"type": "比和", "element": _PEER_ELEMENT_MAP[pair]}
    return None


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — InteractionRegistry & Actors
# ══════════════════════════════════════════════════════════════════════════════


class BranchActor:
    """
    One of the four natal branches as a competitive actor.

    lock_type values:
        None              — unclaimed
        "STRUCTURAL_三会" — locked by full 三会
        "STRUCTURAL_三合" — locked by full 三合
        "PRIMARY_六合"    — locked by 六合 (贪合忘冲)
        "PRIMARY_六冲"    — locked by 六冲
        "SECONDARY"       — next-best after VACANT resolution
        "VACANT"          — freed by 贪合忘冲 broken link; pillar is open/susceptible
    """

    __slots__ = (
        "idx",
        "branch",
        "lock_type",
        "lock_element",
        "lock_item_id",
        "item_ids",
    )

    def __init__(self, idx: int, branch: str):
        self.idx = idx
        self.branch = branch
        self.lock_type: str | None = None
        self.lock_element: str | None = (
            None  # element of structural lock (for 拱局 echo check)
        )
        self.lock_item_id: int | None = None
        self.item_ids: list[int] = []


class StemActor:
    """One of the four natal stems as a competitive actor."""

    __slots__ = ("idx", "stem", "lock_type", "lock_item_id", "item_ids")

    def __init__(self, idx: int, stem: str):
        self.idx = idx
        self.stem = stem
        self.lock_type: str | None = (
            None  # "STEM_天干合" (adjacent 合绊/合化 only) | None
        )
        self.lock_item_id: int | None = None
        self.item_ids: list[int] = []


class InteractionRegistry:
    """
    Central nervous system: single source of truth for all interaction objects.

    State machine:
        ACTIVE   → default
        LOCKED   → claimed as primary lock
        ABSORBED → neutralised (消融吸收)

    State transitions only in Passes 1 & 2.
    Passes 3–5 only write 强度 — never change state.
    """

    def __init__(self):
        self._items: list[dict] = []
        self._state: dict[int, str] = {}  # _iid → "ACTIVE"|"LOCKED"|"ABSORBED"
        self._index: dict[int, dict] = {}  # _iid → item  (O(1) lookup)
        self._counter: int = 0  # monotonic counter — never reuses a value
        self.branch_actors: dict[int, BranchActor] = {}
        self.stem_actors: dict[int, StemActor] = {}

    def _next_iid(self) -> int:
        self._counter += 1
        return self._counter

    # ── Registration ──────────────────────────────────────────────────────────

    def register(self, item: dict) -> None:
        """Stamp item with stable _iid, state → ACTIVE, wire to actors."""
        item["_iid"] = self._next_iid()
        self._items.append(item)
        self._state[item["_iid"]] = "ACTIVE"
        self._index[item["_iid"]] = item
        self._wire(item)

    def inject(self, item: dict) -> None:
        """Add synthetic entry (Pass 1 loser half-structure). Wired identically."""
        item["_synthetic"] = True
        item["_iid"] = self._next_iid()
        self._items.append(item)
        self._state[item["_iid"]] = "ACTIVE"
        self._index[item["_iid"]] = item
        self._wire(item)

    def _wire(self, item: dict) -> None:
        indices = extract_pillar_indices(item.get("组合", ""))
        if not indices:
            return
        iid = item["_iid"]
        itype = item.get("类型", "")
        is_stem = itype in {"天干合", "天干克", "天干冲"}
        for idx in indices:
            if is_stem:
                if idx in self.stem_actors:
                    self.stem_actors[idx].item_ids.append(iid)
            else:
                if idx in self.branch_actors:
                    self.branch_actors[idx].item_ids.append(iid)

    # ── State transitions ─────────────────────────────────────────────────────

    def lock(self, iid: int) -> None:
        self._state[iid] = "LOCKED"

    def absorb(self, iid: int) -> None:
        self._state[iid] = "ABSORBED"

    # ── State queries ─────────────────────────────────────────────────────────

    def is_active(self, iid: int) -> bool:
        return self._state.get(iid) == "ACTIVE"

    def is_locked(self, iid: int) -> bool:
        return self._state.get(iid) == "LOCKED"

    def is_absorbed(self, iid: int) -> bool:
        return self._state.get(iid) == "ABSORBED"

    # ── Lookup helpers ────────────────────────────────────────────────────────

    def get_by_type(
        self, types: list[str], branch_idx: int, active_only: bool = True
    ) -> list[dict]:
        """ACTIVE interactions of given type(s) touching branch_idx."""
        actor = self.branch_actors.get(branch_idx)
        if not actor:
            return []
        result = []
        for iid in actor.item_ids:
            item = self._item_by_id(iid)
            if item is None:
                continue
            if active_only and not self.is_active(iid):
                continue
            if item.get("类型") in types:
                result.append(item)
        return result

    def get_stem_by_type(
        self, types: list[str], stem_idx: int, active_only: bool = True
    ) -> list[dict]:
        actor = self.stem_actors.get(stem_idx)
        if not actor:
            return []
        result = []
        for iid in actor.item_ids:
            item = self._item_by_id(iid)
            if item is None:
                continue
            if active_only and not self.is_active(iid):
                continue
            if item.get("类型") in types:
                result.append(item)
        return result

    def all_items(self) -> list[dict]:
        return list(self._items)

    def active_items(self) -> list[dict]:
        return [it for it in self._items if self.is_active(it["_iid"])]

    def _item_by_id(self, iid: int) -> dict | None:
        return self._index.get(iid)

    def partner_branch_idx(self, item: dict, known_idx: int) -> int | None:
        """For a pairwise interaction, return the branch index that is NOT known_idx."""
        indices = extract_pillar_indices(item.get("组合", ""))
        if not indices:
            return None
        others = [i for i in indices if i != known_idx]
        return others[0] if others else None


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Priority Filter
# ══════════════════════════════════════════════════════════════════════════════


def _apply_rule(item: dict, lock_key: str) -> bool:
    """
    Look up (lock_key, itype) in PRIORITY_RULE_TABLE.
    Write 强度 (only downgrade) and optional 备注. Return True if matched.
    """
    itype = item.get("类型", "")
    rule_key = (lock_key, itype)
    strength = PRIORITY_RULE_TABLE.get(rule_key)
    if strength is None:
        return False
    current_rank = STRENGTH_ORDER.get(item.get("强度", "强势主流"), 0)
    new_rank = STRENGTH_ORDER.get(strength, 0)
    if new_rank > current_rank:
        item["强度"] = strength
    remark = STRENGTH_REMARKS.get(rule_key, "")
    if remark and not item.get("备注"):  # first causal remark wins; never overwrite
        item["备注"] = remark
    return True


def _pass1_structural(registry: InteractionRegistry) -> None:
    """
    Pass 1 — Structural Lock (per-branch).

    A 4-pillar natal chart can never produce two competing triple-structures
    for the same branch (would require 5+ distinct branch positions), so each
    branch has at most one 三会/三合 candidate.
    """
    for idx, actor in registry.branch_actors.items():
        candidates = registry.get_by_type(["三会", "三合"], idx)
        if not candidates:
            continue

        winner = candidates[0]

        winner_itype = winner.get("类型")
        winner_lock = f"STRUCTURAL_{winner_itype}"
        winner_element = winner.get("元素") or winner.get("方位")
        winner_iid = winner["_iid"]
        registry.lock(winner_iid)
        # Lock ALL branches that participate in the winning structure, not just
        # the current contest branch. Without this, Pass 3 misses suppression
        # for interactions that touch only the un-locked co-participants.
        for winning_idx in extract_pillar_indices(winner.get("组合", "无")):
            winning_actor = registry.branch_actors.get(winning_idx)
            if winning_actor and winning_actor.lock_type is None:
                winning_actor.lock_type = winner_lock
                winning_actor.lock_element = winner_element
                winning_actor.lock_item_id = winner_iid


# Lock types that block a VACANT branch from claiming a 六冲 in Round 2.
# A branch already committed to a structural field or primary dual bond
# cannot be "struck" by a freed branch.
_HARD_LOCKED = frozenset(
    {
        "STRUCTURAL_三会",
        "STRUCTURAL_三合",
        "PRIMARY_六合",
        "PRIMARY_六冲",
        "PRIMARY_天克地冲",
    }
)

# Priority order for VACANT branch secondary lock resolution (Round 2).
# 六合 is intentionally absent — Round 2 cannot trigger new 六合 (prevents
# circular standoffs where two freed branches keep greedily re-locking each other).
_SECONDARY_ORDER = (
    "六冲",
    "六害",
    "无恩之刑",
    "恃势之刑",
    "无礼之刑",
    "自刑",
    "六破",
    "暗合",
    "半合",
    "残会",
    # 拱会/拱合 excluded: virtual arches do not occupy branch positions
)


def _partner_is_available(registry: InteractionRegistry, chong: dict, idx: int) -> bool:
    """
    Return True if the 六冲 partner of `chong` (relative to `idx`) is not
    already claimed by a hard-locked state, making it available for a
    VACANT branch to claim the clash in Round 2.
    """
    partner_idx = registry.partner_branch_idx(chong, idx)
    if partner_idx is None:
        return True  # no partner found — treat as available (safe default)
    partner = registry.branch_actors.get(partner_idx)
    return partner is None or partner.lock_type not in _HARD_LOCKED


def _pass2_dual(registry: InteractionRegistry) -> None:
    """
    Pass 2 — Dual Lock (two strict rounds + one sub-round).

    Round 1:  All 六合 locked greedily (贪合忘冲).
              Each 六合 lock immediately emits a Broken Link signal:
                → every 六冲 on that branch is absorbed
                → the 六冲 partner is marked VACANT
              Note: each branch has at most one 六合 partner (six-harmony is
              a bijection on the 12 branches), so he_candidates always has
              0 or 1 entries. The `[0]` selection is always unambiguous.

    Round 1b: Branches still unlocked after Round 1 (had no 六合) claim
              their 六冲 as PRIMARY_六冲. Processed only after all 六合 locks
              are finalised so Broken Link signals have fully propagated.

    Round 2:  VACANT branches (freed by Broken Link) resolve to a next-best
              secondary lock from _SECONDARY_ORDER. New 六合 is forbidden here
              to prevent circular standoffs between two freed branches.
    """
    # Round 1 — Greedy 六合
    for idx, actor in registry.branch_actors.items():
        if actor.lock_type is not None:
            continue
        he_candidates = registry.get_by_type(["六合"], idx)
        if not he_candidates:
            continue
        winner = he_candidates[0]  # always exactly one; see docstring
        actor.lock_type = "PRIMARY_六合"
        actor.lock_item_id = winner["_iid"]
        registry.lock(winner["_iid"])
        # Broken Link: absorb all 六冲 on this branch, free partners
        for chong in registry.get_by_type(["六冲"], idx):
            registry.absorb(chong["_iid"])
            chong_partner_idx = registry.partner_branch_idx(chong, idx)
            if chong_partner_idx is not None:
                chong_partner = registry.branch_actors.get(chong_partner_idx)
                if chong_partner and chong_partner.lock_type is None:
                    chong_partner.lock_type = "VACANT"
                    chong_partner.lock_item_id = None
        # 贪合忘冲 is bidirectional: the 六合 partner is equally "in the bond"
        # and must also forget its own 六冲.
        he_partner_idx = registry.partner_branch_idx(winner, idx)
        if he_partner_idx is not None:
            he_partner = registry.branch_actors.get(he_partner_idx)
            if he_partner and he_partner.lock_type is None:
                he_partner.lock_type = "PRIMARY_六合"
                he_partner.lock_item_id = winner["_iid"]
                for chong in registry.get_by_type(["六冲"], he_partner_idx):
                    registry.absorb(chong["_iid"])
                    chong_partner_idx = registry.partner_branch_idx(
                        chong, he_partner_idx
                    )
                    if chong_partner_idx is not None:
                        chong_partner = registry.branch_actors.get(chong_partner_idx)
                        if chong_partner and chong_partner.lock_type is None:
                            chong_partner.lock_type = "VACANT"
                            chong_partner.lock_item_id = None

    # Round 1b — Assign PRIMARY_六冲 to unlocked branches with 六冲 (no 六合 available)
    # Mirror 六合 Round 1: propagate lock to the clash partner so both sides
    # are recognised as engaged in the clash (enables correct suppression of
    # interactions targeting the partner branch, e.g. 干支透合).
    for idx, actor in registry.branch_actors.items():
        if actor.lock_type is not None:
            continue
        chong_candidates = registry.get_by_type(["六冲"], idx)
        if not chong_candidates:
            continue
        winner = chong_candidates[0]
        actor.lock_type = "PRIMARY_六冲"
        actor.lock_item_id = winner["_iid"]
        registry.lock(winner["_iid"])
        # Propagate to clash partner (if still unlocked)
        chong_partner_idx = registry.partner_branch_idx(winner, idx)
        if chong_partner_idx is not None:
            chong_partner = registry.branch_actors.get(chong_partner_idx)
            if chong_partner and chong_partner.lock_type is None:
                chong_partner.lock_type = "PRIMARY_六冲"
                chong_partner.lock_item_id = winner["_iid"]

    # Round 1b-ext — Assign PRIMARY_天克地冲 to branches still unlocked after 六合/六冲.
    # 六冲 is not registered for these pairs (guard in detection skips it),
    # so Round 1b above never fires for them — this step fills the gap.
    for idx, actor in registry.branch_actors.items():
        if actor.lock_type is not None:
            continue
        tkdc_candidates = registry.get_by_type(["天克地冲"], idx)
        if not tkdc_candidates:
            continue
        winner = tkdc_candidates[0]
        actor.lock_type = "PRIMARY_天克地冲"
        actor.lock_item_id = winner["_iid"]
        registry.lock(winner["_iid"])
        partner_idx = registry.partner_branch_idx(winner, idx)
        if partner_idx is not None:
            partner = registry.branch_actors.get(partner_idx)
            if partner and partner.lock_type is None:
                partner.lock_type = "PRIMARY_天克地冲"
                partner.lock_item_id = winner["_iid"]

    # Round 2 — VACANT resolution (no new 六合)
    for idx, actor in registry.branch_actors.items():
        if actor.lock_type != "VACANT":
            continue
        for candidate_type in _SECONDARY_ORDER:
            candidates = registry.get_by_type([candidate_type], idx)
            if not candidates:
                continue
            if candidate_type == "六冲":
                candidates = [
                    c for c in candidates if _partner_is_available(registry, c, idx)
                ]
            if not candidates:
                continue
            winner = candidates[0]
            actor.lock_type = "SECONDARY"
            actor.lock_item_id = winner["_iid"]
            registry.lock(winner["_iid"])
            break
        # Branch remains VACANT if nothing found — open/susceptible pillar


def _pass3_conflict(registry: InteractionRegistry) -> None:
    """
    Pass 3 — Conflict Pass.
    For each ACTIVE item, for each branch it touches, look up (lock_type, itype)
    in PRIORITY_RULE_TABLE. Only downgrades. Stems handled separately.

    Multi-branch note: a pairwise item (e.g. 六害 on 年柱-月柱) is visited once
    per branch it touches, so _apply_rule may be called twice on the same item.
    This is intentional and safe: _apply_rule only downgrades (never upgrades),
    and the remark is written only if none exists yet. The strongest applicable
    lock across all participating branches naturally wins.
    """
    for item in registry.active_items():
        indices = extract_pillar_indices(item.get("组合", "无"))
        for idx in indices:
            actor = registry.branch_actors.get(idx)
            if not actor or not actor.lock_type:
                continue
            if actor.lock_item_id == item.get("_iid"):
                continue  # never downgrade the winner itself
            # 干支透合: the source-stem pillar's branch lock is irrelevant.
            # Only the TARGET branch (支柱索引) can suppress its own hidden-stem availability.
            if item.get("类型") == "干支透合" and item.get("支柱索引") != idx:
                continue
            _apply_rule(item, actor.lock_type)

    _pass3_stems(registry)


# Lock-type priority for remark ordering in _pass3_stems.
# Actors with stronger locks write their causal remark first.
_STEM_LOCK_REMARK_ORDER = {"STEM_天干合": 0}


def _pass3_stems(registry: InteractionRegistry) -> None:
    """
    Stem lock: only adjacent 天干合 (distance == 1, 合绊 or 合化) binds.
    Classical principle: 天干克 and 天干冲 are directional forces — they do not
    lock other stem interactions. Only 天干合 between adjacent pillars creates
    a true binding that absorbs 克/冲 on those two stems.

    Two-phase design:
      Phase 1 — assign STEM_天干合 lock to actors with an adjacent 天干合.
      Phase 2 — apply suppression rules so the authoritative remark lands first.
    """
    # ── Phase 1: assign locks and register winners ───────────────────────────
    actor_state: dict[int, tuple[str, list]] = {}
    for idx, actor in registry.stem_actors.items():
        he_items = registry.get_stem_by_type(["天干合"], idx, active_only=False)
        adjacent_he = [h for h in he_items if h.get("距离") == 1]

        if not adjacent_he:
            continue

        winner: dict | None = _pick_stem_winner(adjacent_he)
        if winner is None:
            continue

        actor.lock_type = "STEM_天干合"
        actor.lock_item_id = winner["_iid"]
        registry.lock(winner["_iid"])
        actor_state[idx] = ("STEM_天干合", he_items)

    # ── Phase 2: apply rules in lock-priority order ───────────────────────────
    for idx in sorted(
        actor_state, key=lambda i: _STEM_LOCK_REMARK_ORDER.get(actor_state[i][0], 99)
    ):
        lock_key, he_items = actor_state[idx]
        winner_iid = registry.stem_actors[idx].lock_item_id
        for item in he_items:
            if item.get("_iid") != winner_iid:
                _apply_rule(item, lock_key)

        # ── STEM_天干合 → 天干克/天干冲 (合化锁定，克冲消融) ─────────────────
        for item in registry.get_stem_by_type(["天干克", "天干冲"], idx):
            _apply_rule(item, lock_key)

        # ── Cross-actor: STEM_天干合 → 干支透合 (贪合忘合) ────────────────────
        # 干支透合 is wired to branch_actor (target branch), so its suppression
        # by the SOURCE STEM's 天干合 lock must be applied explicitly here.
        # 贪合忘合: once the stem is engaged in a direct 天干合, it cannot also
        # form a covert bond with a hidden stem in another branch.
        for item in registry.active_items():
            if item.get("类型") == "干支透合" and item.get("干柱索引") == idx:
                _apply_rule(item, lock_key)


def _pick_stem_winner(candidates: list[dict]) -> dict | None:
    """日柱 absolute anchor, then _STEM_LOCK_PRIORITY order."""
    if not candidates:
        return None
    ri_zhu = [c for c in candidates if 2 in extract_pillar_indices(c.get("组合", "无"))]
    pool = ri_zhu if ri_zhu else candidates

    def _rank(item):
        indices = extract_pillar_indices(item.get("组合", "无"))
        ranks = [
            _STEM_LOCK_PRIORITY.index(i) for i in indices if i in _STEM_LOCK_PRIORITY
        ]
        return min(ranks) if ranks else 99

    return min(pool, key=_rank)


def _pass4_group(registry: InteractionRegistry) -> None:
    """
    Pass 4 — Group / Environment Pass.

    比和 / 暗合 / 干支透合 : default 显著影响 if not already downgraded by Pass 3.
    半合/残会 : capped by participating branch lock types.
               VACANT branch → treated as open/susceptible → 强势主流.
    拱合/拱会 : echo check — same element as structural lock → 强势主流.
               Mismatched structural element → 大幅衰减. No structural lock → 显著影响.
               Virtual arches; never occupy branches.
    """
    for item in registry.active_items():
        itype = item.get("类型", "")
        indices = extract_pillar_indices(item.get("组合", "无"))

        if itype in {"比和", "暗合", "干支透合"}:
            if not item.get("强度"):
                item["强度"] = "显著影响"
            continue

        if itype in {"半合", "残会"}:
            if item.get("强度"):
                continue  # already assigned in Pass 3
            lock_types = [
                registry.branch_actors[i].lock_type
                for i in indices
                if i in registry.branch_actors
            ]
            if any(lt and lt.startswith("STRUCTURAL") for lt in lock_types):
                item["强度"] = "大幅衰减"
            elif any(lt == "PRIMARY_六冲" for lt in lock_types):
                item["强度"] = "大幅衰减"
            elif any(lt == "PRIMARY_六合" for lt in lock_types):
                item["强度"] = "中等衰减"
            elif any(lt == "VACANT" for lt in lock_types):
                # VACANT = freed by 贪合忘冲; the pillar is open and undefended.
                # A partial structure pulling on an open pillar activates fully.
                item["强度"] = "强势主流"
                item["备注"] = STRENGTH_REMARKS.get(
                    ("STRUCTURAL_VACANT", "branch"), "无"
                )
            else:
                # Covers None (no lock) and SECONDARY (next-best minor lock).
                # SECONDARY is a weak residual bond — not strong enough to suppress
                # a partial structure, so it also resolves to 强势主流 here.
                # Pass 3 will have already downgraded the item if the SECONDARY
                # lock type generated a rule against it.
                item["强度"] = "强势主流"
            continue

        if itype in {"伏吟", "天克地冲"}:
            if not item.get("强度"):
                if 2 in indices:  # 日柱 involved
                    item["强度"] = "强势主流"
                    item["备注"] = STRENGTH_REMARKS.get(
                        (f"INTERACTION_CONTEXT_{itype}", "day_master"), ""
                    )
                else:
                    _dist = item.get("距离", 2)
                    item["强度"] = DEFAULT_STRENGTH.get(
                        (itype, _dist)
                    ) or DEFAULT_STRENGTH.get((itype, 2), "显著影响")
            continue

        if itype in {"拱合", "拱会"}:
            gong_element = item.get("元素", "无")
            structural_elements = [
                registry.branch_actors[i].lock_element
                for i in indices
                if i in registry.branch_actors
                and (registry.branch_actors[i].lock_type or "无").startswith(
                    "STRUCTURAL"
                )
                and registry.branch_actors[i].lock_element
            ]
            existing = item.get("强度")
            if item.get("混杂"):
                # 混杂 is a downgrade — only apply if Pass 3 has not already set
                # a stronger downgrade (i.e. don't worsen what is already worse).
                if not existing or STRENGTH_ORDER.get(
                    "显著影响", 0
                ) > STRENGTH_ORDER.get(existing, 0):
                    item["强度"] = "显著影响"
                    item["备注"] = STRENGTH_REMARKS.get(
                        (f"INTERACTION_STATE_{itype}", "turbid"), "无"
                    )
            elif gong_element in structural_elements:
                # Echo upgrade: same element resonance — legitimate Pass 4 upgrade,
                # BUT respect Pass 3 suppressions: if already 消融吸收 or 大幅衰减,
                # the branch is too disrupted for echo to resurrect.
                if existing and STRENGTH_ORDER.get(existing, 0) >= STRENGTH_ORDER.get(
                    "大幅衰减", 0
                ):
                    pass  # Pass 3 suppression stands — echo cannot resurrect
                else:
                    item["强度"] = "强势主流"
                    item["备注"] = STRENGTH_REMARKS.get(
                        (f"INTERACTION_STATE_{itype}", "echo"), "无"
                    )
            elif structural_elements:
                # Structural suppression — only apply if not already weaker.
                if not existing or STRENGTH_ORDER.get(
                    "大幅衰减", 0
                ) > STRENGTH_ORDER.get(existing, 0):
                    item["强度"] = "大幅衰减"
                    item["备注"] = STRENGTH_REMARKS.get(
                        (f"INTERACTION_STATE_{itype}", "suppressed"), "无"
                    )
            elif not existing:
                item["强度"] = "显著影响"
            continue


def _pass5_defaults(registry: InteractionRegistry) -> None:
    """
    Pass 5 — Default Strength Assignment.
    Any item still without 强度 gets its default from DEFAULT_STRENGTH.
    ABSORBED items get 消融吸收.
    """
    for item in registry.all_items():
        if item.get("强度"):
            continue
        if registry.is_absorbed(item.get("_iid", -1)):
            item["强度"] = "消融吸收"
            continue
        itype = item.get("类型", "无")
        distance = item.get("距离", 2)
        if itype in _XK_XING_TYPES:
            xing_form = item.get("形态", "")
            item["强度"] = _PUNISHMENT_STRENGTH.get(
                (itype, xing_form, distance)
            ) or _PUNISHMENT_STRENGTH.get((itype, xing_form, 2), "显著影响")
        elif itype == "天干合":
            he_form = item.get("形态", "")
            item["强度"] = DEFAULT_STRENGTH.get(
                ("天干合", he_form)
            ) or DEFAULT_STRENGTH.get(("天干合", distance), "显著影响")
        else:
            item["强度"] = DEFAULT_STRENGTH.get(
                (itype, distance)
            ) or DEFAULT_STRENGTH.get((itype, 2), "强势主流")
        if distance == 3:
            d3_note = STRENGTH_REMARKS.get(("DISTANCE_3", itype))
            if d3_note:
                existing = item.get("备注", "")
                item["备注"] = (existing + "；" + d3_note) if existing else d3_note
        if itype == "天干合" and item.get("形态") == "遥合" and not item.get("备注"):
            item["备注"] = STRENGTH_REMARKS.get(
                ("INTERACTION_STATE_天干合", "binding"), ""
            )


def _downgrade_if_stronger(current: str, cap: str) -> str:
    """Return cap only if current strength is stronger than cap; otherwise return current unchanged."""
    return (
        cap
        if STRENGTH_ORDER.get(current, 99) < STRENGTH_ORDER.get(cap, 99)
        else current
    )


def _pass_stem_rooting(items: list, tong_gen: str = "中根") -> None:
    """
    Stem Rooting Modulation Pass.
    Downgrades 天干合/克/冲 strength based on participating stems' 无根 status (multi-tier).
    Operates on a flat list (post-priority); does NOT use registry.

    When 日柱特殊=True on an item, the day master's branch-rooting tier is substituted
    with the 通根 tier from 得地 (深根/中根/浅根/无根). This prevents false downgrades for
    a deeply-rooted day master whose root falls outside the local branch subset, and ensures
    a rootless day master is correctly treated as 无根.
    All other stem pairs use actual branch-rooting tiers unchanged.

    Scenario table:
        天干合: one stem 无根 → "显著影响"; both 无根 → "中等衰减"
        天干克: controller 无根 + target rooted → "大幅衰减";
                controller 无根 + target 无根   → "中等衰减"
        天干冲: one stem 无根 → "显著影响"; both 无根 → "中等衰减"

    Scope note: the substitution operates on a local effective_rooting copy and does
    NOT write back to item["根基"]. Wu_xing's combo_factor and per_stem_retain (both read
    根基 directly) therefore still use the raw branch-rooting tier for the day master.
    """
    for item in items:
        itype = item.get("类型")
        if itype not in ("天干合", "天干克", "天干冲"):
            continue
        if item.get("强度") == "消融吸收":
            continue
        rooting = item.get("根基", {})
        if not rooting:
            continue
        strength = item.get("强度", "")

        # When the day master participates, substitute its tier with 通根 directly
        effective_rooting = dict(rooting)
        if item.get("日柱特殊") and "日柱" in effective_rooting:
            effective_rooting["日柱"] = tong_gen

        tiers = list(effective_rooting.values())
        wugen_count = tiers.count("无根")

        if itype == "天干合":
            he_form = item.get("形态", "合绊")
            if wugen_count == len(tiers):
                cap, note = "中等衰减", f"{he_form}·双干无根，合力近无"
            elif wugen_count > 0:
                cap, note = "显著影响", f"{he_form}·浮干无力"
            else:
                continue
            new_strength = _downgrade_if_stronger(strength, cap)
            if new_strength != strength:
                item["强度"] = new_strength
                item.setdefault("备注", "")
                item["备注"] += ("、" if item["备注"] else "") + note

        elif itype == "天干克":
            controller = item.get("主动方")
            if not controller or effective_rooting.get(controller) != "无根":
                continue
            target_tier = next(
                (v for k, v in effective_rooting.items() if k != controller), "无根"
            )
            if target_tier != "无根":
                cap, note = "大幅衰减", "反克. 克者无根，被克者有根，克力瓦解"
            else:
                cap, note = "中等衰减", "克者无根，克力虚浮"
            item["强度"] = _downgrade_if_stronger(strength, cap)
            item.setdefault("备注", "")
            item["备注"] += ("、" if item["备注"] else "") + note

        elif itype == "天干冲":
            if wugen_count == len(tiers):
                cap, note = "中等衰减", "双干无根，冲势空洞"
            elif wugen_count > 0:
                cap, note = "显著影响", "一方无根，冲势偏斜"
            else:
                continue
            item["强度"] = _downgrade_if_stronger(strength, cap)
            item.setdefault("备注", "")
            item["备注"] += ("、" if item["备注"] else "") + note


def apply_bazi_master_priority(registry: InteractionRegistry) -> list:
    """
    Five-Pass Resource Consumption Filter orchestrator.

    Pass 1 — Structural Lock    (三会/三合 per-branch, tie-breaker, synthetic inject)
    Pass 2 — Dual Lock          (贪合忘冲, VACANT, two strict rounds)
    Pass 3 — Conflict Pass      (PRIORITY_RULE_TABLE lookup per actor lock)
    Pass 4 — Group/Environment  (拱合/拱会/半合/比和/暗合 with echo & VACANT susceptibility)
    Pass 5 — Default Assignment (DEFAULT_STRENGTH table)

    Note: Pass S (Stem Rooting Modulation) is applied by the caller after this
    function returns, so the caller can supply the correct 通根 tier.
    """
    _pass1_structural(registry)
    _pass2_dual(registry)
    _pass3_conflict(registry)
    _pass4_group(registry)
    _pass5_defaults(registry)

    result = registry.all_items()
    result.sort(key=lambda x: INTERACTION_TIER_ORDER.get(x.get("类型", "无"), 999))
    return result


# ── Pass 7 — Reconcile 天干克 After Stem Transformation ──────────────────────


def __reconcile_stemcontrol_after_stem_transformation(filtered: list) -> None:
    """Neutralise 天干克 whose control no longer holds after 合化/化气格 transformation.

    Dead Code. Kept here for reference in case future stem transformation rules changes.

    Why Pass 2 already covers it completely:

    1. 合化/化气格 always requires distance == 1 — non-adjacent pairs become 遥合 (line 772). So both forms are inherently adjacent.

    2. Adjacent 天干合 always triggers STEM_天干合 lock — Pass 2 Phase 1 (line 1467) filters [h for h in he_items if h.get("距离") == 1], so every 合化/化气格 pair gets a lock on both of their stem actors.

    3. Pass 2 Phase 2 (line 1492) neutralises ALL 天干克 on the locked actor:

        for item in registry.get_stem_by_type(["天干克", "天干冲"], idx):
            _apply_rule(item, lock_key)  # → 消融吸收
            
        This scopes to the actor (idx), which means every 天干克 where that stem is either controller OR target — not just the克 between the two 合 partners. So a third-party stem controlling the transformed stem is also neutralised here.

    4. Pass 7 explicitly skips already-neutralised items — line 1817:

        if item.get("强度") == "消融吸收":
            continue

        By the time Pass 7 runs, any 天干克 involving a 合化/化气格 stem is already at 消融吸收 from Pass 2. Pass 7 never finds anything to act on.
        """

    # Step 1 — build stem_combined: pillar → {element, 形态}
    stem_combined: dict[str, dict] = {}
    for item in filtered:
        if item.get("类型") != "天干合":
            continue
        he_form = item.get("形态")
        if he_form not in ("合化", "化气格"):
            continue
        transformed_element = item.get("元素")
        if not transformed_element:
            continue
        for pillar in item.get("组合明细", {}):
            if pillar not in stem_combined:  # first transformation wins
                stem_combined[pillar] = {"element": transformed_element, "形态": he_form}

    if not stem_combined:
        return

    # Step 2 — re-evaluate each 天干克
    for item in filtered:
        if item.get("类型") != "天干克":
            continue
        if item.get("强度") == "消融吸收":
            continue

        combo = item.get("组合明细", {})
        pillars_in_ke = list(combo.keys())
        if len(pillars_in_ke) != 2:
            continue
        p1, p2 = pillars_in_ke

        if p1 not in stem_combined and p2 not in stem_combined:
            continue  # neither stem transformed

        eff1 = stem_combined[p1]["element"] if p1 in stem_combined else LunarUtil.WU_XING_GAN.get(combo[p1], "无")
        eff2 = stem_combined[p2]["element"] if p2 in stem_combined else LunarUtil.WU_XING_GAN.get(combo[p2], "无")

        controller_pillar = item.get("主动方")
        ctrl_eff, tgt_eff = (eff1, eff2) if controller_pillar == p1 else (eff2, eff1)

        # _ELEMENT_CONTROLS maps element → what controls that element (reverse direction)
        # correct check: does ctrl_eff control tgt_eff? → _ELEMENT_CONTROLS[tgt_eff] == ctrl_eff
        still_controls = _ELEMENT_CONTROLS.get(tgt_eff) == ctrl_eff

        if not still_controls:
            transformed_pillar = p1 if p1 in stem_combined else p2
            he_form_label = stem_combined[transformed_pillar]["形态"]
            item["强度"] = "消融吸收"
            existing = item.get("备注", "")
            remark = f"{he_form_label}后控制关系消失"
            item["备注"] = f"{existing}；{remark}" if existing else remark


# ── Pass 6 — Xun Kong (旬空) Post-Filter ─────────────────────────────────────


def _pass6_xun_kong(filtered: list, xun_kong_data: dict, zhis: list) -> None:
    """
    Post-filter: downgrade interactions involving void (旬空) branches.

    Pass 6a — Primary void (日柱旬空):
    The day pillar's xun kong pair applies to the entire natal chart.
    Any branch matching that pair is void.
    - 合类: 1+ void → downgrade 1 tier
    - 六冲: 1 void → 冲开旬空 remark only; both void → downgrade 1 tier
    - 刑/害/破/暗合/比和: 1+ void → downgrade 1 tier
    - 拱合/拱会: 1+ void participant branches → downgrade 1 tier
    - 天干: skip

    Pass 6b — Mutual void (互换空亡):
    Runs after primary void. For each active mutual void pair, direct 2-pillar
    interactions between those pillars receive 1 additional tier downgrade
    (capped at 大幅衰减). 3-pillar interactions get a remark only.
    - 年日互换空亡 (根不养花): year ↔ day both void each other
    - 月日互换空亡 (路不载人): month ↔ day both void each other
    - 日时互换空亡 (花不结果): day ↔ hour both void each other
    """
    # Day pillar void pair applies to the entire chart
    day_xk_str = xun_kong_data.get("日柱", {}).get("旬空", "")

    for item in filtered:
        itype = item.get("类型", "")
        if itype in _XK_STEM_ONLY:
            continue

        # 干支透合: use 支柱索引 to find the branch side
        if itype == "干支透合":
            zhi_idx = item.get("支柱索引")
            if zhi_idx is not None:
                pn = _PILLAR_NAMES_CN[zhi_idx]
                if zhis[zhi_idx] in day_xk_str:
                    _downgrade_by_one_tier_xk(
                        item, _build_xk_remark([pn], "misc_single")
                    )
                    item["旬空涉及"] = [pn]
            continue

        pairs = _extract_branch_pairs(item.get("组合明细", {}))
        if not pairs:
            continue

        void_pillars = [pn for pn, br in pairs if br in day_xk_str]

        if not void_pillars:
            continue

        if itype in _XK_HE_TYPES:
            _downgrade_by_one_tier_xk(item, _build_xk_remark(void_pillars, "合_single"))
            item["旬空涉及"] = void_pillars
        elif itype in _XK_CHONG_TYPES:
            if len(void_pillars) == len(pairs):
                _downgrade_by_one_tier_xk(
                    item, _build_xk_remark(void_pillars, "双空相冲")
                )
                item["旬空涉及"] = void_pillars
            else:
                _append_remark_xk(item, _build_xk_remark(void_pillars, "冲开旬空"))
                item["旬空涉及"] = void_pillars
        elif itype in _XK_XING_TYPES:
            _downgrade_by_one_tier_xk(item, _build_xk_remark(void_pillars, "刑_single"))
            item["旬空涉及"] = void_pillars
        elif itype in _XK_HAI_PO_TYPES:
            _downgrade_by_one_tier_xk(
                item, _build_xk_remark(void_pillars, "害破_single")
            )
            item["旬空涉及"] = void_pillars
        elif itype in _XK_MISC_TYPES:
            _downgrade_by_one_tier_xk(
                item, _build_xk_remark(void_pillars, "misc_single")
            )
            item["旬空涉及"] = void_pillars

    # ── Pass 6b: Mutual Void (互换空亡) ──────────────────────────────────────
    year_void = xun_kong_data.get("年柱", {}).get("旬空", "")
    month_void = xun_kong_data.get("月柱", {}).get("旬空", "")
    time_void = xun_kong_data.get("时柱", {}).get("旬空", "")

    active_mutual: set = set()
    if zhis[0] in day_xk_str and zhis[2] in year_void:
        active_mutual.add(frozenset({"年柱", "日柱"}))
    if zhis[1] in day_xk_str and zhis[2] in month_void:
        active_mutual.add(frozenset({"月柱", "日柱"}))
    if zhis[3] in day_xk_str and zhis[2] in time_void:
        active_mutual.add(frozenset({"日柱", "时柱"}))

    if active_mutual:
        _pass6b_mutual_void(filtered, active_mutual)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Detection Helpers
# ══════════════════════════════════════════════════════════════════════════════


def _detect_san_hui(zhis: list, registry: InteractionRegistry) -> None:
    """
    Detect full 三会 and partial 拱会/残会.

    Field assignment for partials:
      - 拱会 (cardinal branch absent): carries `缺失支` = the missing cardinal branch.
        The cardinal is the most powerful member; its absence means the structure
        is still arching toward it — hence 缺失支 ("still to emerge").
      - 残会 (cardinal branch present, one satellite missing): carries `缺失支` = the
        missing non-cardinal branch. The structure is partially formed; it waits
        for the last satellite — hence 缺失支 ("waiting to convene").
    Both partials carry `元素` derived from the directional group.
    """
    for element, group in directional_he.items():
        matched: dict[str, int] = {}
        for branch in group:
            for k, zhi in enumerate(zhis):
                if zhi == branch and k not in matched.values():
                    matched[branch] = k
                    break

        if not matched:
            continue

        match_names = sorted(
            [_PILLAR_NAMES_CN[k] for k in matched.values()],
            key=lambda p: _PILLAR_IDX_MAP[p],
        )
        combo_detail = {_PILLAR_NAMES_CN[k]: zhis[k] for k in matched.values()}

        # Determine direction from branch set
        branch_set = frozenset(matched.keys())
        # For partials (2 branches), find direction if both are in same directional group
        direction = None
        if len(branch_set) == 2:
            for dir_branches, dir_name in SAN_HUI_DIRECTION.items():
                if branch_set.issubset(dir_branches):
                    direction = dir_name
                    break
        else:
            # For full 三会 (3 branches), direct lookup
            direction = SAN_HUI_DIRECTION.get(branch_set)

        element_from_direction = (
            DIRECTION_TO_ELEMENT.get(direction) if direction else element
        )

        if len(matched) == 3:
            indices_3h = tuple(sorted(matched.values()))
            min_dist_3h = min(
                indices_3h[i + 1] - indices_3h[i] for i in range(len(indices_3h) - 1)
            )
            registry.register(
                {
                    "类型": "三会",
                    "组合明细": combo_detail,
                    "距离": min_dist_3h,
                    "元素": element_from_direction,
                    "组合": "-".join(match_names),
                }
            )

        elif len(matched) == 2:
            cardinal = cardinal_branches.get(element)
            cardinal_present = cardinal in matched
            idxs = list(matched.values())

            if not cardinal_present:
                # 拱会: enforce adjacency — classical arching requires adjacent pillars
                if abs(idxs[0] - idxs[1]) != 1:
                    continue
                itype_partial = "拱会"
                branch_list = list(matched.keys())
                clashed = bool(
                    clash_map.get(branch_list[0]) in set(zhis)
                    or clash_map.get(branch_list[1]) in set(zhis)
                )
            else:
                itype_partial = "残会"
                clashed = False
                if abs(idxs[0] - idxs[1]) == 3:
                    continue

            missing = next((b for b in group if b not in matched), None)
            dist_partial = abs(idxs[0] - idxs[1])
            item = {
                "类型": itype_partial,
                "组合明细": combo_detail,
                "距离": dist_partial,
                "元素": element_from_direction,
                "缺失支": missing or "无",
                "组合": "-".join(match_names),
            }
            if itype_partial == "拱会":
                item["混杂"] = clashed
            registry.register(item)


def _detect_san_he(zhis: list, registry: InteractionRegistry) -> None:
    """Detect full 三合, partial 半合 (cardinal present, adjacency required), and 拱合 (both non-cardinals, cardinal absent, adjacency required)."""
    for element, group in triple_he.items():
        matched: dict[str, int] = {}
        for branch in group:
            for k, zhi in enumerate(zhis):
                if zhi == branch and k not in matched.values():
                    matched[branch] = k
                    break

        if not matched:
            continue

        match_names = sorted(
            [_PILLAR_NAMES_CN[k] for k in matched.values()],
            key=lambda p: _PILLAR_IDX_MAP[p],
        )
        combo_detail = {_PILLAR_NAMES_CN[k]: zhis[k] for k in matched.values()}
        combo = "-".join(match_names)

        if len(matched) == 3:
            indices = tuple(sorted(matched.values()))
            min_dist = min(indices[i + 1] - indices[i] for i in range(len(indices) - 1))
            registry.register(
                {
                    "类型": "三合",
                    "组合明细": combo_detail,
                    "距离": min_dist,
                    "元素": element,
                    "组合": combo,
                }
            )

        elif len(matched) == 2:
            cardinal = cardinal_branches.get(element)
            cardinal_present = cardinal in matched
            idxs = sorted(matched.values())
            distance = idxs[1] - idxs[0]

            if cardinal_present:
                # 半合: cardinal present, one satellite missing — adjacency required
                if distance != 1:
                    continue
                missing = next((b for b in group if b not in matched), None)
                registry.register(
                    {
                        "类型": "半合",
                        "组合明细": combo_detail,
                        "距离": distance,
                        "元素": element,
                        "缺失支": missing or "无",
                        "组合": combo,
                    }
                )
            else:
                # 拱合: both non-cardinals, cardinal absent from chart — adjacency required
                if distance != 1:
                    continue
                if cardinal not in zhis:
                    branch_list = list(matched.keys())
                    present_set = set(zhis)
                    clashed = bool(
                        clash_map.get(branch_list[0]) in present_set
                        or clash_map.get(branch_list[1]) in present_set
                    )
                    registry.register(
                        {
                            "类型": "拱合",
                            "组合明细": combo_detail,
                            "距离": distance,
                            "元素": element,
                            "缺失支": cardinal,
                            "混杂": clashed,
                            "组合": combo,
                        }
                    )


@dataclasses.dataclass(frozen=True)
class _PairCtx:
    """Immutable context for one pillar pair (i, j) inside _detect_pairwise."""

    i: int
    j: int
    b_i: str
    b_j: str
    g_i: str
    g_j: str
    distance: int
    pn_i: str
    pn_j: str
    combo: str
    detail: dict


def _detect_earthly_branch_relations(
    ctx: _PairCtx, registry: InteractionRegistry
) -> None:
    """
    Register pure branch-to-branch interactions: 六冲, 六合, 比和, 六害, 六破, 暗合.

    六冲, 六合, and 比和 are all registered independently even when the same pair
    qualifies for multiple — suppression is a priority-filter question, not a
    detection question.
    六冲 guard excludes 天克地冲 pairs (stem_clashes.get(g_i) != g_j).
    六合, 六害, 六破, 暗合 register at any distance; 形态 reflects distance == 1 (正) vs farther (遥).
    """
    b_i, b_j = ctx.b_i, ctx.b_j
    g_i, g_j = ctx.g_i, ctx.g_j
    distance = ctx.distance
    detail, combo = ctx.detail, ctx.combo

    if clash_map.get(b_i) == b_j and stem_clashes.get(g_i) != g_j:
        registry.register(
            {
                "类型": "六冲",
                "形态": "正冲" if distance == 1 else "遥冲",
                "组合明细": detail,
                "距离": distance,
                "组合": combo,
            }
        )
    if six_he_map.get(b_i) == b_j:
        pk: tuple[str, str] = (b_i, b_j) if b_i <= b_j else (b_j, b_i)
        elem = six_he_element_map.get(pk, {}).get("primary", "无")
        registry.register(
            {
                "类型": "六合",
                "形态": "正合" if distance == 1 else "遥合",
                "组合明细": detail,
                "距离": distance,
                "元素": elem,
                "组合": combo,
            }
        )
    peer = is_valid_peer_combination(b_i, b_j)
    if peer:
        registry.register(
            {
                "类型": "比和",
                "组合明细": detail,
                "距离": distance,
                "元素": peer["element"],
                "组合": combo,
            }
        )
    if harm_map.get(b_i) == b_j:
        registry.register(
            {
                "类型": "六害",
                "形态": "正害" if distance == 1 else "遥害",
                "组合明细": detail,
                "距离": distance,
                "组合": combo,
            }
        )
    if break_map.get(b_i) == b_j:
        registry.register(
            {
                "类型": "六破",
                "形态": "正破" if distance == 1 else "遥破",
                "组合明细": detail,
                "距离": distance,
                "组合": combo,
            }
        )
    # hidden_stem_he pairs (寅丑, 卯申, 午亥) have no overlap with clash_map;
    # 六冲 suppression is handled by the priority filter, not at detection.
    if b_j in hidden_stem_he.get(b_i, set()):
        registry.register(
            {
                "类型": "暗合",
                "组合明细": detail,
                "距离": distance,
                "组合": combo,
            }
        )


def _detect_earthly_branch_punishments(
    ctx: _PairCtx, registry: InteractionRegistry, zhis: list
) -> None:
    """
    Register 刑 interactions: 无恩之刑, 恃势之刑, 无礼之刑, 自刑.

    is_valid_punishment handles all four types:
      b_i == b_j → 自刑 (same branch repeated across two pillars)
      b_i != b_j → 无恩/恃势/无礼 where applicable
    zhis (full 4-branch list) is required for the set-based 三刑全/半刑 check.
    半刑 形态 is distance-graded: 紧邻之刑 (d=1), 隔柱之刑 (d=2), 遥隔之刑 (d=3).
    无礼之刑/自刑 use 正刑 (d=1) or 遥刑 (d>1).
    """
    result = is_valid_punishment(ctx.b_i, ctx.b_j, natal_branches=zhis)
    if not result:
        return
    xing_type = result["type"]
    if xing_type in ("无恩之刑", "恃势之刑"):
        if result["branch_count"] == 3:
            xing_form = "三刑全"
        elif ctx.distance == 1:
            xing_form = "半刑 - 紧邻之刑"
        elif ctx.distance == 2:
            xing_form = "半刑 - 隔柱之刑"
        else:
            xing_form = "刑 - 遥隔之刑"
    else:
        xing_form = "正刑" if ctx.distance == 1 else "遥刑"
    registry.register(
        {
            "类型": xing_type,
            "形态": xing_form,
            "组合明细": ctx.detail,
            "距离": ctx.distance,
            "组合": ctx.combo,
        }
    )


def _detect_pillar_interactions(ctx: _PairCtx, registry: InteractionRegistry) -> None:
    """
    Register pillar-level interactions that require stem AND branch simultaneously:
    伏吟 (identical gan+zhi) and 天克地冲 (stem clash + branch clash).

    伏吟 is mutually exclusive with 天克地冲 — identical branches cannot also clash.
    组合明细 uses the combined "干支" label (e.g. "甲子") rather than branch alone.
    """
    pn_i, pn_j = ctx.pn_i, ctx.pn_j
    g_i, g_j = ctx.g_i, ctx.g_j
    b_i, b_j = ctx.b_i, ctx.b_j
    distance, combo = ctx.distance, ctx.combo
    pillar_detail = {pn_i: f"{g_i}{b_i}", pn_j: f"{g_j}{b_j}"}

    if g_i == g_j and b_i == b_j:
        registry.register(
            {
                "类型": "伏吟",
                "形态": "正伏吟" if distance == 1 else "遥伏吟",
                "组合明细": pillar_detail,
                "距离": distance,
                "组合": combo,
            }
        )
    # Guards on 六冲/天干冲 detection ensure no redundant output for this pair.
    if stem_clashes.get(g_i) == g_j and clash_map.get(b_i) == b_j:
        registry.register(
            {
                "类型": "天克地冲",
                "组合明细": pillar_detail,
                "距离": distance,
                "组合": combo,
            }
        )


def _detect_stem_hidden_stem_bonds(
    ctx: _PairCtx,
    registry: InteractionRegistry,
    ten_gods_hidden: dict,
) -> None:
    """
    Register 干支透合: a heavenly stem from one pillar covertly combines with a
    hidden stem (藏干) inside another pillar's branch. Bidirectional per pair.

    Distinct from 暗合 (branch↔branch): here the source is a transparent stem.
    Year-Hour pairs (distance == 3) are excluded — too distant for covert bonding.
    冲则气散 and 贪合忘合 are handled by the priority filter post-detection.
    藏干十神 is always relative to the day master (gans[2]).
    天干合 is 1-to-1, so only the first hidden-stem match per branch is registered.
    """
    if ctx.distance >= 3:
        return

    _hidden_labels = ("本气", "中气", "余气")
    directions = [
        (ctx.i, ctx.j, ctx.pn_i, ctx.pn_j, ctx.g_i, ctx.b_j),
        (ctx.j, ctx.i, ctx.pn_j, ctx.pn_i, ctx.g_j, ctx.b_i),
    ]

    for s_idx, b_idx, s_pn, b_pn, s_val, b_val in directions:
        target_stem = stem_combines.get(s_val)
        for h_idx, h_stem in enumerate(LunarUtil.ZHI_HIDE_GAN.get(b_val, [])):
            if target_stem == h_stem:
                label = _hidden_labels[h_idx]
                registry.register(
                    {
                        "类型": "干支透合",
                        "形态": "正透合" if ctx.distance == 1 else "遥透合",
                        "组合明细": {s_pn: s_val, b_pn: b_val},
                        "藏干详情": {
                            "藏干": h_stem,
                            "藏干层": label,
                            "藏干十神": ten_gods_hidden[b_pn].get(f"{label}十神", "无"),
                            "合化五行": _STEM_COMBINE_ELEMENT.get(s_val, "无"),
                        },
                        "距离": ctx.distance,
                        "干柱索引": s_idx,
                        "支柱索引": b_idx,
                        "组合": ctx.combo,
                    }
                )
                break


def _detect_stem_interference(gans: list, i: int, j: int) -> tuple[bool, str | None]:
    """
    Detect 争合 (competing) or 妒合 (jealous) interference for an adjacent pair (i,j).
    Returns (has_interference, interference_type).

    Two Blocking Patterns:
    ═══════════════════════════════════════════════════════════════════════════

    Pattern 1: 争合 (Competing Combination)
    ───────────────────────────────────────
    One stem appears TWICE in the chart, on both sides of its partner.
    Structure: X - Y - X (the X on both ends "compete" for Y in the middle)

    Example 1: [甲, 己, 甲, 丙]
              Year Month Day Hour
              0    1     2   3

        For pair (0,1): 甲-己
        Check: Is there another 甲 at position 2?
        Yes → 争合 detected (两个甲争夺己)

    Example 2: [己, 甲, 甲, 己]
              0    1    2   3
        For pair (1,2): 甲-甲 (invalid, same stem, skip)
        NOT 争合

    Pattern 2: 妒合 (Jealous/Blocking Combination)
    ──────────────────────────────────────────────
    A duplicate stem sits IMMEDIATELY OUTSIDE the combining pair, blocking it.
    Structure: A - A - B (left duplicate) or A - B - B (right duplicate)

    Example 1: [甲, 甲, 己, 丙]
              0    1    2   3
        For pair (1,2): 甲-己
        Check: gans[0] == gans[1]? 甲 == 甲 ✓
        → 妒合 detected (左侧甲妒忌，阻挠甲-己组合)

    Example 2: [己, 甲, 甲, 丙]
              0    1    2   3
        For pair (0,1): 己-甲
        Check: gans[2] == gans[1]? 甲 == 甲 ✓
        → 妒合 detected (右侧甲妒忌，阻挠己-甲组合)

    Example 3: [己, 甲, 丙, 丙]
              0    1    2   3
        For pair (0,1): 己-甲
        Check right: gans[2] == gans[1]? 丙 == 甲 ✗
        Check left: gans[-1] invalid
        → NO interference
    ═══════════════════════════════════════════════════════════════════════════
    """
    if i >= j or not (j == i + 1):  # Assume caller provides adjacent pair
        return False, None

    stem_a = gans[i]
    stem_b = gans[j]

    # Check Pattern 1: 争合 (both sides competition)
    # One stem appears exactly 2 times; the other appears exactly 1 time.
    # The 2-time stem must be on both sides of the 1-time stem (middle).
    count_a = gans.count(stem_a)
    count_b = gans.count(stem_b)

    if count_a == 2 and count_b == 1:
        competitor = stem_a
        partner_stem = stem_b
        positions = [k for k, val in enumerate(gans) if val == competitor]
        if len(positions) == 2:
            pos1, pos2 = sorted(positions)
            # Check: exactly one position gap, and partner is in the middle
            if pos2 - pos1 == 2 and gans[pos1 + 1] == partner_stem:
                return True, "争合"
    elif count_b == 2 and count_a == 1:
        competitor = stem_b
        partner_stem = stem_a
        positions = [k for k, val in enumerate(gans) if val == competitor]
        if len(positions) == 2:
            pos1, pos2 = sorted(positions)
            if pos2 - pos1 == 2 and gans[pos1 + 1] == partner_stem:
                return True, "争合"

    # Check Pattern 2: 妒合 (immediate outside duplicate)
    # A duplicate of one combining stem sits immediately adjacent on the outside.

    # Left side: check if gans[i-1] == gans[i]
    if i > 0 and gans[i - 1] == gans[i] and (i - 1) != j:
        return True, "妒合"

    # Right side: check if gans[j+1] == gans[j]
    if j + 1 < 4 and gans[j + 1] == gans[j] and (j + 1) != i:
        return True, "妒合"

    return False, None


def _check_he_hua_conditions(
    g_i: str,
    g_j: str,
    i: int,
    j: int,
    gans: list,
    zhis: list,
    rooting: dict,
) -> tuple[str, dict]:
    """
    Classify an adjacent 天干合 pair by evaluating Five Conditions.
    Caller pre-confirms adjacency (distance == 1).

    Returns:
        (he_form, detail) where he_form is one of:
            "合化"   — All conditions pass; day master not involved → simple transformation
            "化气格" — All conditions pass; day master is one of the pair → true transformation
            "假化"   — Transformation passes but breaker element present → unstable
            "合绊"   — One or more conditions fail → combination without transformation

        Interference (争合/妒合) is NOT returned as he_form; it appears only in
        detail["干扰"] field when detected.

    Five Conditions:
    ═══════════════════════════════════════════════════════════════════════════

    1. Adjacency (distance == 1)
       Pre-confirmed by caller.

    2. 得令 (Seasonal Support)
       Transformed element must be 旺 or 相 in the month branch.
       Classical rule: month dominance is required (no fallback conditions).

    3. 无根/极弱 (Root Weakness)
       Two paths depending on day master involvement:

       Path A (day master involved):
           - Day master must be 浅根 or 无根
           - Partner stem's root tier is ignored
           - Mode: "日主极弱"

       Path B (general transformation):
           - Both stems must avoid 深根, OR
           - Month branch contains 本气 of transformed element (classical concession)
           - Mode: "通用合化"

    4. 无妒合/争合 (No Interference)
       No duplicate stem of either combining stem elsewhere in the 4 pillars.
       Evaluated via _detect_stem_interference():
           - 争合: One stem appears on both sides of partner (X-Y-X pattern)
           - 妒合: Duplicate sits immediately outside the pair (A-A-B pattern)
       When interference detected, transformation FAILS → 合绊, with
       interference_type stored in detail["干扰"].

    5. 化神有根 (Transformed Element Rooting)
       At least one 本气 branch of the transformed element exists in the 4 pillars.

    假化 Check (化气格 only):
       If day master path succeeds, check for breaker element (the element that
       controls the transformed element via 五行相克). If breaker's 本气 exists
       in the branches, transformation is unstable → 假化. Otherwise → 化气格.

    Detail Dict Structure:
    ═══════════════════════════════════════════════════════════════════════════
    Always includes:
        "合化元素": transformed element (e.g. "土")
        "得令": {"通过": bool, "月支": branch}
        "两干极弱": {"通过": bool, "模式": str, pillar1+"根基": tier, pillar2+"根基": tier}
        "化神有根": {"通过": bool, "锚支": {"月柱": "巳", "时柱": "午"}}
        "干扰": interference_type ("争合" | "妒合" | "无争合妒合")

    For 化气格/假化 only:
        "转化品质": {"品质": "假化", "破坏元素": breaker, "破坏支": {"年柱": "申"}}
                   OR "无破坏元素" (if not 假化)
    """
    hua_element = _STEM_COMBINE_ELEMENT.get(g_i, "")
    if not hua_element:
        return "合绊", {"原因": "不构成天干合"}

    is_day_master_involved = i == 2 or j == 2  # Day master involved
    ben_qi_zhi = _ELEMENT_BEN_QI_ZHI.get(hua_element, frozenset())
    ben_qi_branches = {_PILLAR_NAMES_CN[k]: z for k, z in enumerate(zhis) if z in ben_qi_zhi}

    # Condition 2: classical – only month branch matters
    in_season = hua_element in _ZHI_WANG_XIANG_ELEMENTS.get(zhis[1], frozenset())
    c2 = in_season  # no fallback to branch count

    # Condition 3: 极弱 (root weakness)
    root_i = rooting.get(_PILLAR_NAMES_CN[i], {}).get("根基强度", "无根")
    root_j = rooting.get(_PILLAR_NAMES_CN[j], {}).get("根基强度", "无根")

    if is_day_master_involved:
        # Day master must be 浅根 or 无根
        dm_root = root_i if i == 2 else root_j
        c3 = dm_root in {"浅根", "无根"}
        c3_mode = "日主极弱"
    else:
        # General transformation: both stems must be 浅根 or 无根 (极弱) to surrender
        # their original element. 中根 retains enough grounding to resist transformation.
        # Exception: if the month branch is a 本气 of the transformed element, seasonal
        # compulsion overrides root strength — even 中根/深根 stems must transform.
        both_weak = root_i in {"浅根", "无根"} and root_j in {"浅根", "无根"}
        month_ben_qi = zhis[1] in ben_qi_zhi
        c3 = both_weak or month_ben_qi
        c3_mode = "通用合化"

    # Condition 5: 化神有根
    c5 = bool(ben_qi_branches)

    # Condition 4: 无妒合/争合 (interference detection)
    interference, interference_type = _detect_stem_interference(gans, i, j)

    # Transformation possible only if all conditions (2,3,5) pass and no interference (4)
    can_transform = c2 and c3 and c5 and not interference

    if not can_transform:
        detail = {
            "合化元素": hua_element,
            "得令": {"通过": c2, "月支": zhis[1]},
            "两干极弱": {
                "通过": c3,
                "模式": c3_mode,
                _PILLAR_NAMES_CN[i] + "根基": root_i,
                _PILLAR_NAMES_CN[j] + "根基": root_j,
            },
            "化神有根": {"通过": c5, "锚支": ben_qi_branches},
            "干扰": interference_type if interference else "无争合妒合",
        }
        return "合绊", detail

    # Transformation possible
    if is_day_master_involved:
        breaker = _ELEMENT_CONTROLS.get(hua_element, "")
        breaker_ben_qi = _ELEMENT_BEN_QI_ZHI.get(breaker, frozenset())
        has_breaker = any(z in breaker_ben_qi for z in zhis)
        he_form = "假化" if has_breaker else "化气格"
        detail = {
            "合化元素": hua_element,
            "得令": {"通过": c2, "月支": zhis[1]},
            "两干极弱": {
                "通过": c3,
                "模式": c3_mode,
                _PILLAR_NAMES_CN[i] + "根基": root_i,
                _PILLAR_NAMES_CN[j] + "根基": root_j,
            },
            "化神有根": {"通过": c5, "锚支": ben_qi_branches},
            "干扰": interference_type if interference else "无争合妒合",
            "转化品质": (
                {
                    "品质": he_form,
                    "破坏元素": breaker,
                    "破坏支": {_PILLAR_NAMES_CN[k]: zhis[k] for k in range(4) if zhis[k] in breaker_ben_qi},
                }
                if he_form == "假化"
                else "无破坏元素"
            ),
        }
        return he_form, detail
    else:
        return "合化", {
            "合化元素": hua_element,
            "得令": {"通过": c2, "月支": zhis[1]},
            "两干极弱": {
                "通过": c3,
                "模式": c3_mode,
                _PILLAR_NAMES_CN[i] + "根基": root_i,
                _PILLAR_NAMES_CN[j] + "根基": root_j,
            },
            "化神有根": {"通过": c5, "锚支": ben_qi_branches},
            "干扰": interference_type if interference else "无争合妒合",
        }


def _detect_heavenly_stem_interactions(
    ctx: _PairCtx,
    registry: InteractionRegistry,
    rooting: dict,
    gans: list,
    zhis: list,
) -> None:
    """
    Register pure stem interactions: 天干合, 天干冲, 天干克.

    A stem pair may simultaneously combine AND clash/control (e.g. 甲-庚: both
    天干冲 and 天干克). All are registered independently; PRIORITY_RULE_TABLE
    suppresses the weaker via 消融吸收.
    天干冲 guard excludes 天克地冲 pairs (clash_map.get(b_i) == b_j).
    根基 carries the 4-tier rooting depth from bazi_pillars compute_pillar_rooting().
    """
    g_i, g_j = ctx.g_i, ctx.g_j
    b_i, b_j = ctx.b_i, ctx.b_j
    pn_i, pn_j = ctx.pn_i, ctx.pn_j
    distance, combo = ctx.distance, ctx.combo
    stem_detail = {pn_i: g_i, pn_j: g_j}
    root_detail = {
        pn_i: rooting[pn_i]["根基强度"],
        pn_j: rooting[pn_j]["根基强度"],
    }

    day_master_involved = ctx.i == 2 or ctx.j == 2

    if stem_combines.get(g_i) == g_j:
        if distance == 1:
            he_form, he_hua_detail = _check_he_hua_conditions(
                g_i, g_j, ctx.i, ctx.j, gans, zhis, rooting
            )
        else:
            he_form, he_hua_detail = "遥合", None
        item: dict = {
            "类型": "天干合",
            "形态": he_form,
            "组合明细": stem_detail,
            "根基": root_detail,
            "距离": distance,
            "元素": _STEM_COMBINE_ELEMENT.get(g_i, ""),
            "主动方": "相互",
            "组合": combo,
        }
        if he_hua_detail is not None:
            item["合化条件"] = he_hua_detail
        if day_master_involved:
            item["日柱特殊"] = True
        registry.register(item)
    if stem_clashes.get(g_i) == g_j and not (clash_map.get(b_i) == b_j):
        item = {
            "类型": "天干冲",
            "形态": "正冲" if distance == 1 else "遥冲",
            "组合明细": stem_detail,
            "根基": root_detail,
            "距离": distance,
            "主动方": "相互",
            "组合": combo,
        }
        if day_master_involved:
            item["日柱特殊"] = True
        registry.register(item)
    if (g_i, g_j) in stem_controls or (g_j, g_i) in stem_controls:
        controller_label = pn_i if (g_i, g_j) in stem_controls else pn_j
        item = {
            "类型": "天干克",
            "形态": "正克" if distance == 1 else "遥克",
            "组合明细": stem_detail,
            "根基": root_detail,
            "距离": distance,
            "主动方": controller_label,
            "组合": combo,
        }
        if day_master_involved:
            item["日柱特殊"] = True
        registry.register(item)


def _detect_pairwise(
    zhis: list,
    gans: list,
    registry: InteractionRegistry,
    rooting: dict,
    ten_gods_hidden: dict,
) -> None:
    """
    Detect all pairwise branch and stem interactions.

    Branch (all registered independently):  六冲, 六合, 比和, 六害, 六破, 刑, 暗合, 干支透合
    Stem (all registered independently):    天干合, 天干冲, 天干克
    Suppression is handled by the priority filter, not at detection time.

    Stem interaction field schema (consistent across all three types):
        类型, 组合, 组合明细, 距离, 主动方, 根基
      天干合 additionally:
        元素 (合化五行)

      主动方: controller pillar label for 天干克; "相互" for 天干合/冲.
      根基: {pillar_label: tier} — 4-tier (深根/中根/浅根/无根) from bazi_pillars rooting.

    Args:
        rooting:         {pillar_name: {"根基强度": tier}} from compute_pillar_rooting.
        ten_gods_hidden: {pillar_name: {"本气十神": ..., "中气十神": ..., "余气十神": ...}}.

    干支透合 is bidirectional per pair: checks both g_i→zhis[j] and g_j→zhis[i].
    Each item stores 干柱索引 (source stem pillar) and 支柱索引 (target branch pillar)
    so the priority filter can apply branch locks only from the target branch.
    """
    for i in range(4):
        for j in range(i + 1, 4):
            ctx = _PairCtx(
                i=i,
                j=j,
                b_i=zhis[i],
                b_j=zhis[j],
                g_i=gans[i],
                g_j=gans[j],
                distance=j - i,
                pn_i=_PILLAR_NAMES_CN[i],
                pn_j=_PILLAR_NAMES_CN[j],
                combo=f"{_PILLAR_NAMES_CN[i]}-{_PILLAR_NAMES_CN[j]}",
                detail={_PILLAR_NAMES_CN[i]: zhis[i], _PILLAR_NAMES_CN[j]: zhis[j]},
            )
            _detect_earthly_branch_relations(ctx, registry)
            _detect_earthly_branch_punishments(ctx, registry, zhis)
            _detect_pillar_interactions(ctx, registry)
            _detect_stem_hidden_stem_bonds(ctx, registry, ten_gods_hidden)
            _detect_heavenly_stem_interactions(ctx, registry, rooting, gans, zhis)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Output Assembly
# ══════════════════════════════════════════════════════════════════════════════

# ── Distance Descriptors ──────────────────────────────────────────────────────
_DISTANCE_LABELS = {
    1: "相邻",
    2: "隔柱",
    3: "远隔",
}

_OUTPUT_STRIP_KEYS = {
    "_iid",
    "_synthetic",
    "_layer",
    "干柱索引",
    "支柱索引",
    "组合",
    "混杂",
    "日柱特殊",
}


def _build_pillar_dynamics(filtered: list) -> list:
    """
    Strip internal keys from each interaction and return the list directly.
    Each item in filtered is already unique — no per-pillar distribution needed.
    """
    for item in filtered:
        for k in _OUTPUT_STRIP_KEYS:
            item.pop(k, None)
        if "距离" in item and isinstance(item["距离"], int):
            item["距离"] = _DISTANCE_LABELS.get(
                item["距离"], f"未知距离 ({item['距离']})"
            )
    return filtered


def get_natal_interactions(pillars: dict, void: dict) -> dict:
    """
    Extract and analyze all pillar interactions from a BaZi chart.

    Args:
        pillars: Result of get_bazi_pillars() — {"年柱": {"天干": ..., "地支": ...}, ...}
        void:    Result of get_void_xun_kong() — {"年柱": "戌亥", ..., "日柱": "...", ...}
                 Primary Void (空亡) is derived from the day pillar's void pair.
                 Reverse Void is not evaluated.

    Returns:
        {"作用": {
            "关系总览": [...],   # High-strength interactions (强势主流/显著影响 only)
            "柱位动态": [...],   # Flat list of all interactions sorted by INTERACTION_TIER_ORDER
        }}
    """
    gans = [pillars[k]["天干"] for k in _PILLAR_NAMES_CN]
    zhis = [pillars[k]["地支"] for k in _PILLAR_NAMES_CN]

    # ── Rooting & ten gods — already in pillars (merged by orchestrator) ──
    rooting = {k: {"根基强度": pillars[k]["根基强度"]} for k in _PILLAR_NAMES_CN}
    ten_gods_hidden = {k: pillars[k]["藏干十神"] for k in _PILLAR_NAMES_CN}

    # ── Initialise registry ────────────────────────────────────────────────
    registry = InteractionRegistry()
    for idx in range(4):
        registry.branch_actors[idx] = BranchActor(idx, zhis[idx])
        registry.stem_actors[idx] = StemActor(idx, gans[idx])

    # ── Detection ─────────────────────────────────────────────────────────
    _detect_san_hui(zhis, registry)
    _detect_san_he(zhis, registry)
    _detect_pairwise(zhis, gans, registry, rooting, ten_gods_hidden)

    # ── Five-pass priority filter ──
    filtered = apply_bazi_master_priority(registry)

    # ── Pass S: Stem Rooting Modulation ──────────────────────────────────
    _pass_stem_rooting(filtered, tong_gen=pillars["日柱"]["根基强度"])

    # ── Pass 7: Reconcile 天干克 after stem transformation ────────────────
    __reconcile_stemcontrol_after_stem_transformation(filtered)

    # ── Pass 6: Xun Kong (旬空) post-filter ──────────────────────────────
    # Convert flat void format {"日柱": "戌亥"} to the nested format _pass6_xun_kong expects
    xk_inner = {k: {"旬空": v} for k, v in void.items()}
    _pass6_xun_kong(filtered, xk_inner, zhis)

    # ── Output assembly ───────────────────────────────────────────────────
    pillar_dynamics = _build_pillar_dynamics(filtered)

    summary: list[str] = []
    for item in filtered:
        if item.get("强度") not in ("强势主流", "显著影响"):
            continue
        combo = item.get("组合明细", {})
        detail = "".join(f"{k}{v}" for k, v in combo.items())
        summary.append(f"{item.get('类型', '')}({detail})")

    return {
        "作用": {
            "关系总览": summary,
            "柱位动态": pillar_dynamics,
        },
    }


# ============================================================================
# EXECUTION
# python -m apps.backend.astronomer_logic.natal_interactions
# ============================================================================

if __name__ == "__main__":
    import json
    from datetime import datetime as dt
    from apps.backend.astronomer_logic.true_solar_time import get_true_solar_time
    from apps.backend.astronomer_logic.bazi_pillars import get_bazi_pillars
    from apps.backend.astronomer_logic.void_xun_kong import get_void_xun_kong
    from apps.backend.astronomer_logic.ten_gods import get_ten_gods
    from src.utils.logging import configure_logging, get_logger

    configure_logging()
    logger = get_logger(__name__)

    # ── Subjects ──────────────────────────────────────────────────────────────
    subjects = {
        # "Desmond": (dt(1985, 11, 25, 17, 7, 0), 1.3253, 103.808053, 1),
        "Corinne": (dt(1987, 6, 3, 12, 6, 0), 1.4759, 103.808053, 0),
        # "Lara":    (dt(2025,  7, 31,  9, 10, 0), 1.3253,  103.808053, 0),
    }

    for name, (birthday, lat, lon, gender) in subjects.items():
        logger.info("=" * 60)
        logger.info("Subject: %s  (%s)", name, birthday.strftime("%Y-%m-%d %H:%M"))

        tst_birthday = get_true_solar_time(birthday, lat, lon)
        lunar_birthday = tst_birthday.getLunar()

        bazi = lunar_birthday.getEightChar()
        pillars = get_bazi_pillars(bazi)
        void = get_void_xun_kong(bazi)
        ten_gods = get_ten_gods(bazi)

        # Merge 藏干十神 into pillars so natal_interactions can read ten gods
        for k in ["年柱", "月柱", "日柱", "时柱"]:
            pillars[k]["藏干十神"] = ten_gods[k]["藏干十神"]

        interactions = get_natal_interactions(pillars, void)
        logger.info(json.dumps(interactions, ensure_ascii=False, indent=2))
