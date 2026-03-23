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
        - Pass 4: Co-arching (共拱) detection and conflict marking
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
       These synthetics may later match on 共拱 in Pass 4.

    3. Broken Link Signaling:
       六合 lock immediately absorbs competing 六冲 and frees partner branches
       for secondary resolution — enables clean 贪合忘冲 mechanics.

    4. Declarative Priority Rules:
       PRIORITY_RULE_TABLE maps (lock_type, interaction_type) → 强度 downgrade.
       STRENGTH_REMARKS provides causal explanations (no generic noise).

    5. Co-Arching Detection (共拱) — Two-Layer System:
       Detects virtual frames formed by partial interactions all targeting the same
       missing cardinal branch (拱向).

       Layer 1 (L1 — Positional):
         Two adjacent/nearby branches whose partial structures aim at the same
         missing branch form a positional co-arch.

       Layer 2 (L2 — Structural Composite):
         When multiple partial interactions (拱会, 半合, 残会) across the chart
         collectively target the same missing branch, they form a composite 共拱.
         Unified Subsumption Rule: once an L2 composite exists, every other active
         item stamped with the same 拱向 target (including L1 positional 共拱 and
         contributing partials) is absorbed → 消融吸收. The L2 composite is the
         authoritative structure (以大局为主).

       Clash events mark the frame as turbid (混杂), downgrading from 强势主流
       to 显著影响. Each 共拱 item carries a 拱向 field (the missing target branch)
       and 元素 (the element of that branch).

    6. Distance Semantics (紧贴 Field):
       All branch-pair interactions include adjacency tracking:
       - 正X (adjacent/adjacent pillars) → DIRECT/IMMEDIATE
       - 遥X (distant/non-adjacent pillars) → MEDIATED/DELAYED
       Applies to: 六冲, 六合, 六害, 六破, 天干合, 天干克, 天干冲, 比和, 三刑

    7. Interaction Types (16 total):
       Tier 1 (Structural): 三会, 三合, 六冲, 六合
       Tier 2 (Operational): 共拱, 比和, 拱会, 残会, 半合, 天干合, 干支透合, 天干克, 天干冲
       Tier 3 (Frictional): 三刑 (四种/full/partial), 六害, 六破, 暗合

    8. Heavenly Stem Interactions:
       天干合 (Harmony) locks stems, blocking lower-tier 克/冲.
       天干克 (Control) suppresses 天干冲.
       天干冲 (Clash) is weakest stem interaction.

       All three types share a consistent field schema:
         类型, 组合, 组合明细, 状态, 紧贴, 主动方, 根基
       天干合 additionally carries:
         元素 (合化五行)
       主动方: "相互" for 天干合/冲; controller pillar label for 天干克.
       根基: {pillar_label: tier} for each participating stem — 4-tier system
             (深根/中根/浅根/无根) computed via get_stem_root_tier().
       Strength is further modulated by Pass S (see CORE INNOVATION above).

    9. Punishment Detection (三刑):
       - Ungrateful (无恩之刑): 寅-巳-申 set
       - Bullying (恃势之刑): 丑-未-戌 set
       - Uncivilized (无礼之刑): 子-卯 pair (正刑/遥刑)
       - Self-Punishment (自刑): Repeat branches (紧贴 = adjacent/direct vs distant/harmonic)

   10. Peer Combinations (比和):
       Adjacent same-element branches (e.g., 寅卯, 巳午, 申酉, 亥子, and all earth pairs).
       Harmonious but non-binding; weaker than 六合/三合.
       Uses set-based element matching for precise validation.

   11. Multi-Pillar Distribution:
       Three-way interactions (三会, 三合) appear in all affected pillars
       (same object reference for context preservation).
       Deduplication via (idx, tier, _iid) prevents duplicate entries per pillar+tier.

   12. Vacant Pillar Signals (柱位开放):
       Any branch with lock_type == "VACANT" indicates structural openness
       for LLM interpretation of reactive potential.

INTERNAL KEYS (STRIPPED BEFORE OUTPUT):

    _iid:        Unique interaction identifier (for state tracking and dedup)
    _synthetic:  Flag indicating synthetic half-structure (from Pass 1 loser injection)
    _layer:      Layer discriminator for 共拱 (1 = positional, 2 = structural composite)
    干方索引:    Source stem pillar index for 干支透合 suppression logic
    支方索引:    Target branch pillar index for 干支透合 suppression logic

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

    STRENGTH_REMARKS: Causal explanations (e.g., "三会方位场已成，共拱虚局被吸收")

Main Functions:

    get_interactions(lunar_birthday) → dict:
        Extract and analyze all pillar interactions from a BaZi chart.
        Returns LLM-optimized JSON with:
        - 关系总览: Summary of strong/significant interactions
        - 柱位动态: Per-pillar interactions distributed into three tiers
        - 柱位开放: Vacant pillar flags indicating structural openness
        - 判定优先级: Tier groupings (纲领层/气势层/琐碎层)

    apply_bazi_master_priority(all_interactions, zhis, registry) → list:
        Five-pass filter orchestrator. Returns filtered interactions with
        modulated 强度 and causal 备注 fields.

    extract_pillar_indices(pillar_indices_str) → tuple:
        Parse pillar combination strings ("年柱-月柱-日柱") into sorted indices.
        Uses priority-based mapping (full names before abbreviations).

    _build_pillar_dynamics(filtered) → dict:
        Distribute interactions into per-pillar tier buckets (第一梯队/第二梯队/第三梯队).
        Strips internal keys (_iid, _synthetic) on first encounter.

Validators:

    is_valid_punishment(branch1, branch2, natal_branches=None) → bool:
        Unified validator for all four punishment types (full/partial distinction).

    is_valid_peer_combination(branch1, branch2) → bool:
        Validates adjacent same-element branches for 比和.

Interaction Maps (Declarative Configuration):

    clash_map, harm_map, six_he_map, triple_he, cardinal_branches, directional_he,
    break_map, hidden_stem_he, stem_combines, stem_clashes, stem_controls,
    six_he_element_map: All branch/stem relationships and element mappings.

    INTERACTION_TIER_ORDER: 16 types mapped to tiers (0–14)
    INTERACTION_STATUSES: Centralized status library with distance modulation
    STRENGTH_LEVELS, STRENGTH_ORDER: Hierarchical strength definitions

Dependencies:

    - lunar_python: BaZi chart extraction
    - datetime: Date/time handling
    - src.astronomer_calculations.solar_lunar_time: True solar time

Output Format:

    {
        "作用": {
            "关系总览": [status strings for strong/significant interactions],
            "柱位动态": {
                "年柱": {"第一梯队_纲领层": [...], "第二梯队_气势层": [...], "第三梯队_琐碎层": [...]},
                "月柱": {...}, "日柱": {...}, "时柱": {...}
            },
            "柱位开放": {"年柱": True, ...}  # for VACANT branches,
            "判定优先级": {
                "第一梯队_纲领层": ["三会", "三合", "六冲", "六合"],
                "第二梯队_气势层": [list of tier 2 types],
                "第三梯队_琐碎层": [list of tier 3 types]
            }
        }
    }

    Each interaction dict contains:
    - 类型: Interaction type
    - 组合: Pillar composition (e.g., "年柱-月柱")
    - 组合明细: Branch/stem mapping per pillar
    - 状态: Status (from INTERACTION_STATUSES)
    - 紧贴: Boolean adjacency flag (applicable to: 六冲, 六合, 六害, 六破, 三刑,
      天干冲, 天干克, 比和, 半合, 三合, 拱会/残会, 共拱)
    - 元素: Produced/transformed element (applicable to: 三会, 三合, 半合 — triple element;
      六合 — transformation element; 比和 — shared peer element; 共拱 — arched-toward
      branch element; 拱会/残会 — directional element; 天干合 — 合化五行)
    - 方位: Directional info (三会, 拱会, 残会 only)
    - 邀出: Missing third branch for 半合; "已全" for complete 三合
    - 犹出: Missing cardinal branch (拱会 only — the branch the 拱会 is still waiting to form)
    - 待会: Missing non-cardinal branch (残会 only — the incomplete satellite branch)
    - 拱向: The missing target branch a 共拱/拱会/残会/半合 is arching toward
    - 混杂: Clash turbidity flag (共拱 only)
    - 主动方: Controller pillar label for 天干克; "相互" for 天干合/冲
    - 根基: {pillar_label: tier} 4-tier rooting per participating stem (天干合/克/冲 only)
    - 强度: Modulated strength (强势主流/显著影响/中等衰减/大幅衰减/消融吸收)
    - 备注: Causal note (if suppressed/absorbed)

Implemented:
    - compute_pillar_rooting() — per-pillar 4-tier rooting summary (importable by cycle modules)
    - get_stem_root_tier()     — single-stem rooting tier against a list of branches
    - _pass_stem_rooting()     — Pass S stem rooting modulation (importable by cycle modules)
    - BRANCH_HIDDEN_ROOTING    — hidden-stem rooting weight table
"""

from lunar_python import Solar, Lunar
from lunar_python.util import LunarUtil
from datetime import datetime
from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
from src.astronomer_calculations import void_xun_kong
from src.utils.logging import get_logger
from src.astronomer_calculations.day_master import (
    BRANCH_HIDDEN_ROOTING,
    compute_de_di,
    get_stem_root_tier,
    get_shi_shen_for_stem_pair,
    stem_elements,
)

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
# SECTION 7 — Orchestrator     (get_interactions)
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
    "寅": {"丑"},      # Jia-Ji
    "丑": {"寅"},
    "卯": {"申"},      # Yi-Geng
    "申": {"卯"},
    "午": {"亥"},      # Ding-Ren
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

stem_controls = frozenset({
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
})

# stem_elements, BRANCH_HIDDEN_ROOTING, _ROOT_DEPTH_LABELS imported from day_master
_ROOT_DEPTH_LABELS: list[str] = ["本气根", "中气根", "余气根"]

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

INTERACTION_STATUSES = {
    "六合": {"adjacent": "正合", "distant": "遥合"},
    "六冲": {"adjacent": "正冲", "distant": "遥冲"},
    "六害": {"adjacent": "正害", "distant": "遥害"},
    "六破": {"adjacent": "正破", "distant": "遥破"},
    "半合": {
        "prefix": "半合{element}局",
        "strong": "强",
        "weak": "弱",
        "arching": "拱",
    },
    "三刑": {
        "ungrateful_full": "三刑全",
        "ungrateful_partial": "半刑",
        "bullying_full": "三刑全",
        "bullying_partial": "半刑",
        "uncivilized_adjacent": "正刑",
        "uncivilized_distant": "遥刑",
        "self_adjacent": "自刑 (直接反馈过载)",
        "self_distant": "遥自刑 (谐波自我纠缠)",
        "adjacent": "正刑",
        "distant": "遥刑",
    },
    "三会": {"full": "三会成局", "arch": "拱会局", "residual": "残会局"},
    "三合": {"full": "三合全局"},
    "比和": "同气共鸣",
    "暗合": "暗(隐秘)",
    "干支透合": "透合(藏干隐合)",
    "天干合": "合化",
    "天干冲": {"adjacent": "正冲", "distant": "遥冲"},
    "天干克": {"adjacent": "正克", "distant": "遥克"},
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
    "六合": 3,
    "共拱": 4,
    "比和": 5,
    "拱会": 6,
    "残会": 7,
    "半合": 7,
    "天干合": 8,
    "天干克": 9,
    "天干冲": 10,
    "三刑": 11,
    "无恩之刑": 11,
    "恃势之刑": 11,
    "无礼之刑": 11,
    "自刑": 11,
    "六害": 12,
    "六破": 13,
    "暗合": 14,
    "干支透合": 15,
}

# ── Declarative Priority Rule Table ──────────────────────────────────────────
# Key: (lock_type, interaction_type) → 强度
# Only downgrades — the pass logic never upgrades via this table.
# lock_type: "STRUCTURAL_三会" | "STRUCTURAL_三合"
#            "PRIMARY_六合"    | "PRIMARY_六冲"
#            "STEM_天干合"     | "STEM_天干克"
PRIORITY_RULE_TABLE = {
    # STRUCTURAL_三会
    ("STRUCTURAL_三会", "三合"): "消融吸收",
    ("STRUCTURAL_三会", "六合"): "大幅衰减",
    ("STRUCTURAL_三会", "六冲"): "大幅衰减",
    ("STRUCTURAL_三会", "半合"): "大幅衰减",
    ("STRUCTURAL_三会", "拱会"): "大幅衰减",
    ("STRUCTURAL_三会", "残会"): "大幅衰减",
    ("STRUCTURAL_三会", "共拱"): "消融吸收",  # overridden by echo check in Pass 4
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
    ("STRUCTURAL_三合", "拱会"): "大幅衰减",
    ("STRUCTURAL_三合", "残会"): "大幅衰减",
    ("STRUCTURAL_三合", "共拱"): "大幅衰减",
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
    ("PRIMARY_六合", "拱会"): "中等衰减",
    ("PRIMARY_六合", "残会"): "中等衰减",
    ("PRIMARY_六合", "比和"): "显著影响",
    ("PRIMARY_六合", "暗合"): "显著影响",
    # 共拱 is a virtual overlay — loses a supporting pillar to 六合 bond.
    # Weaker than 半合 under same lock, so same suppression level.
    ("PRIMARY_六合", "共拱"): "中等衰减",
    # PRIMARY_六冲 (刑冲并见 amplification)
    ("PRIMARY_六冲", "六合"): "消融吸收",
    ("PRIMARY_六冲", "六害"): "显著影响",
    ("PRIMARY_六冲", "六破"): "显著影响",
    ("PRIMARY_六冲", "无恩之刑"): "显著影响",
    ("PRIMARY_六冲", "恃势之刑"): "显著影响",
    ("PRIMARY_六冲", "无礼之刑"): "显著影响",
    ("PRIMARY_六冲", "自刑"): "显著影响",
    ("PRIMARY_六冲", "半合"): "大幅衰减",
    ("PRIMARY_六冲", "拱会"): "大幅衰减",
    ("PRIMARY_六冲", "残会"): "大幅衰减",
    ("PRIMARY_六冲", "比和"): "显著影响",
    ("PRIMARY_六冲", "暗合"): "显著影响",
    # 共拱 with a clashed participant is structurally undermined.
    # Matches suppression level of 半合/拱会 under 六冲.
    ("PRIMARY_六冲", "共拱"): "大幅衰减",
    # STEM locks
    # 天干合 in place: harmonisation absorbs both clash and control
    ("STEM_天干合", "天干克"): "消融吸收",
    ("STEM_天干合", "天干冲"): "消融吸收",
    # 天干克 in place: control suppresses clash (controller channels destructive force)
    ("STEM_天干克", "天干冲"): "消融吸收",
    # 天干冲 in place: clash weakens control but does not nullify it
    ("STEM_天干冲", "天干克"): "大幅衰减",
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
    ("STRUCTURAL_三会", "共拱"): "三会已完整成局，共拱虚局被吸收",
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
    ("STEM_天干克", "天干冲"): "天干克在位，冲势被制化消融",
    ("STEM_天干冲", "天干克"): "天干冲动场域，克力受震荡大幅衰减",
    ("STRUCTURAL_三会", "干支透合"): "三会方位场锁定地支，藏干不得透出，干支透合受压",
    ("STRUCTURAL_三合", "干支透合"): "三合局锁定地支，藏干不得透出，干支透合受压",
    ("PRIMARY_六合", "干支透合"): "目标地支已被六合占位，藏干潜合力被合力压制",
    ("PRIMARY_六冲", "干支透合"): "目标地支被六冲气散，藏干无力应合",
    ("STEM_天干合", "干支透合"): "源天干已与他干直合，贪合之下，藏干透合消融",
    ("SYNTHETIC_半合", "origin"): "原三合因争位失败，剩余两支保留半合牵引",
    ("SYNTHETIC_残会", "origin"): "原三会因争位失败，剩余两支保留残会框架",
    ("GONG_GONG", "echo"): "虚局与实局同元素共鸣，气场压倒性主导",
    ("GONG_GONG", "suppressed"): "虚局被异元素结构压制，共鸣瓦解",
    ("GONG_GONG", "turbid"): "虚局参与支遭冲，框架混杂衰减",
    ("VACANT", "branch"): "贪合忘冲释放，该柱位主动开放，易受外部影响",
}

# ── Default Strength Table ────────────────────────────────────────────────────
# (interaction_type, is_adjacent) → 强度
# Pass 5: any interaction without 强度 gets this default.

DEFAULT_STRENGTH = {
    ("三会", True): "强势主流",
    ("三会", False): "强势主流",
    ("三合", True): "强势主流",
    ("三合", False): "强势主流",
    ("六冲", True): "强势主流",
    ("六冲", False): "强势主流",
    ("六合", True): "强势主流",
    ("六合", False): "强势主流",
    ("半合", True): "强势主流",
    ("半合", False): "中等衰减",
    ("拱会", True): "强势主流",
    ("拱会", False): "中等衰减",
    ("残会", True): "强势主流",
    ("残会", False): "中等衰减",
    ("天干合", True): "强势主流",
    ("天干合", False): "强势主流",
    ("天干克", True): "强势主流",
    ("天干克", False): "中等衰减",
    ("天干冲", True): "强势主流",
    ("天干冲", False): "中等衰减",
    ("无恩之刑", True): "强势主流",
    ("无恩之刑", False): "大幅衰减",
    ("恃势之刑", True): "强势主流",
    ("恃势之刑", False): "大幅衰减",
    ("无礼之刑", True): "强势主流",
    ("无礼之刑", False): "大幅衰减",
    ("自刑", True): "强势主流",
    ("自刑", False): "大幅衰减",
    ("六害", True): "显著影响",
    ("六害", False): "显著影响",
    ("六破", True): "显著影响",
    ("六破", False): "显著影响",
    ("比和", True): "显著影响",
    ("比和", False): "显著影响",
    ("暗合", True): "显著影响",
    ("暗合", False): "显著影响",
    ("干支透合", True): "显著影响",
    ("干支透合", False): "显著影响",
    ("共拱", True): "强势主流",
    ("共拱", False): "强势主流",
}

# ── Xun Kong (旬空) Constants ────────────────────────────────────────────────
_STRENGTH_BY_RANK = {v: k for k, v in STRENGTH_ORDER.items()}

_XK_HE_TYPES = frozenset({"六合", "三合", "三会", "半合", "拱会", "残会"})
_XK_CHONG_TYPES = frozenset({"六冲"})
_XK_XING_TYPES = frozenset({"无恩之刑", "恃势之刑", "无礼之刑", "自刑"})
_XK_HAI_PO_TYPES = frozenset({"六害", "六破"})
_XK_MISC_TYPES = frozenset({"暗合", "干支透合", "比和", "共拱"})
_XK_STEM_ONLY = frozenset({"天干合", "天干克", "天干冲"})

_XK_REMARKS = {
    "合_single": "{pillars}支落旬空，合力虚浮，力场不实",
    "冲开旬空": "冲开旬空，虚局受激",
    "双空相冲": "{pillars}支双空相冲，冲力涣散",
    "刑_single": "{pillars}支落旬空，刑力减弱",
    "害破_single": "{pillars}支落旬空，害破力场减弱",
    "misc_single": "{pillars}支落旬空，合力虚浮",
}

# Pillar name constants
_PILLAR_NAMES_CN = ["年柱", "月柱", "日柱", "时柱"]
_PILLAR_IDX_MAP = {"年柱": 0, "月柱": 1, "日柱": 2, "时柱": 3}
_PILLAR_ABBR_MAP = {"年": 0, "月": 1, "日": 2, "时": 3}
_PILLAR_NAME_SET = frozenset(_PILLAR_NAMES_CN)  # fast membership test; avoids rebuilding per call
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


def _proximity_score(indices: tuple) -> int:
    """
    Sum of |idx_i - idx_j| for all pairs.
    Lower = tighter = wins Pass 1 tie-breaker C.
    """
    idxs = list(indices)
    return sum(
        abs(idxs[a] - idxs[b])
        for a in range(len(idxs))
        for b in range(a + 1, len(idxs))
    )


def get_status(interaction_type: str, context: dict = None) -> str:
    """Retrieve status string from INTERACTION_STATUSES."""
    if interaction_type not in INTERACTION_STATUSES:
        return "未知"
    cfg = INTERACTION_STATUSES[interaction_type]
    if isinstance(cfg, str):
        return cfg
    context = context or {}
    if interaction_type == "半合":
        element = context.get("element", "")
        state = context.get("state", "weak")
        char = cfg.get(state, "弱")
        return cfg["prefix"].format(element=element) + f"({char})"
    if interaction_type == "三刑":
        pt = context.get("punishment_type")
        if pt in ("ungrateful", "bullying"):
            key = f"{pt}_full" if context.get("is_full") else f"{pt}_partial"
        elif pt == "uncivilized":
            # 无礼之刑 is always a 2-branch interaction (子卯); no partial form.
            key = (
                "uncivilized_adjacent"
                if context.get("is_adjacent")
                else "uncivilized_distant"
            )
        elif pt == "self":
            key = "self_adjacent" if context.get("is_adjacent") else "self_distant"
        else:
            key = "adjacent" if context.get("is_adjacent") else "distant"
        return cfg.get(key, "未知")
    return cfg.get(context.get("key", ""), "未知")


def is_valid_punishment(
    branch1: str, branch2: str, natal_branches: list = None
) -> dict | None:
    """Set-based punishment validator. Returns result dict or None."""
    if branch1 == branch2:
        if branch1 in SELF_PUNISHMENT["universe"]:
            return {"type": "自刑", "is_full": True, "triple_count": 1}
        return None
    bs = {branch1, branch2}
    if bs == RUDE_PUNISHMENT["universe"]:
        return {"type": "无礼之刑", "is_full": True, "triple_count": 2}
    for punishment in (UNGRATEFUL_PUNISHMENT, BULLYING_PUNISHMENT):
        if bs.issubset(punishment["universe"]):
            if natal_branches:
                triple_count = len((set(natal_branches) | bs) & punishment["universe"])
            else:
                triple_count = len(bs)
            return {
                "type": punishment["name"],
                "is_full": triple_count == 3,
                "triple_count": triple_count,
            }
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
            None  # element of structural lock (for 共拱 echo)
        )
        self.lock_item_id: int | None = None
        self.item_ids: list[int] = []


class StemActor:
    """One of the four natal stems as a competitive actor."""

    __slots__ = ("idx", "stem", "lock_type", "lock_item_id", "item_ids")

    def __init__(self, idx: int, stem: str):
        self.idx = idx
        self.stem = stem
        self.lock_type = None  # "STEM_天干合" | "STEM_天干克" | "STEM_天干冲" | None
        self.lock_item_id = None
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


def _pass1_structural(registry: InteractionRegistry, zhis: list) -> None:
    """
    Pass 1 — Structural Lock (per-branch).

    For each branch with multiple triple-structure candidates:
      Tie-breaker A: 三会 > 三合
      Tie-breaker B: structure containing 月支 (idx 1) wins
      Tie-breaker C: lower proximity score wins

    Loser → 中等衰减 + synthetic half-structure injected for surviving pair.

    NOTE — Synthetic injection is NEVER triggered for the natal 4-pillar chart.
    A contest (len(candidates) > 1) requires the same branch to appear in two
    competing triple-structures simultaneously, which needs 5+ distinct branch
    positions. This function is only ever called from apply_bazi_master_priority,
    which is only ever called from get_interactions (natal 4-pillar). Da Yun and
    all cycle interactions use cycle_interactions.py, which has its own structural
    detection and correctly dispatches 拱会 vs 残会 independently of this path.
    The synthetic injection block below is therefore dead code for all current
    call sites; it is retained for completeness but must not be extended to
    cycle use cases without a full audit of 拱会/残会 type logic.
    """
    for idx, actor in registry.branch_actors.items():
        candidates = registry.get_by_type(["三会", "三合"], idx)
        if not candidates:
            continue

        if len(candidates) == 1:
            winner = candidates[0]
        else:

            def _sort_key(item):
                itype = item.get("类型")
                indices = extract_pillar_indices(item.get("组合", ""))
                return (
                    0 if itype == "三会" else 1,  # A
                    0 if 1 in indices else 1,  # B
                    _proximity_score(indices),  # C
                )

            ranked = sorted(candidates, key=_sort_key)
            winner = ranked[0]

            for loser in ranked[1:]:
                loser["强度"] = "中等衰减"
                loser_indices = extract_pillar_indices(loser.get("组合", "无"))
                surviving = [i for i in loser_indices if i != idx]
                if len(surviving) == 2:
                    s_a, s_b = surviving[0], surviving[1]
                    loser_itype = loser.get("类型")
                    synthetic_itype = "半合" if loser_itype == "三合" else "残会"
                    pn_a, pn_b = _PILLAR_NAMES_CN[s_a], _PILLAR_NAMES_CN[s_b]
                    synthetic = {
                        "类型": synthetic_itype,
                        "组合": f"{pn_a}-{pn_b}",
                        "组合明细": {pn_a: zhis[s_a], pn_b: zhis[s_b]},
                        "紧贴": abs(s_a - s_b) == 1,
                        "邀出": loser.get("组合明细", {}).get(
                            _PILLAR_NAMES_CN[idx], "无"
                        ),
                        "备注": STRENGTH_REMARKS.get(
                            (f"SYNTHETIC_{synthetic_itype}", "origin"), "无"
                        ),
                    }
                    if loser_itype == "三合":
                        # Compute element from the two surviving branches via triple_he lookup.
                        branches_pair = {zhis[s_a], zhis[s_b]}
                        synthetic["元素"] = next(
                            (
                                elem
                                for elem, group in triple_he.items()
                                if branches_pair.issubset(group)
                            ),
                            "无",
                        )
                    else:
                        # 残会: compute direction/element from the two surviving branches directly.
                        branches_present = {zhis[s_a], zhis[s_b]}
                        direction = None
                        missing_branch = "无"
                        for dir_branches, dir_name in SAN_HUI_DIRECTION.items():
                            if branches_present.issubset(dir_branches):
                                direction = dir_name
                                missing_branch = next(
                                    (
                                        b
                                        for b in dir_branches
                                        if b not in branches_present
                                    ),
                                    "无",
                                )
                                break
                        synthetic["方位"] = direction or "无"
                        synthetic["元素"] = (
                            DIRECTION_TO_ELEMENT[direction] if direction else "无"
                        )
                        synthetic["待会"] = missing_branch
                    registry.inject(synthetic)

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
    "拱会",
    "残会",
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
            # Only the TARGET branch (支方索引) can suppress its own hidden-stem availability.
            if item.get("类型") == "干支透合" and item.get("支方索引") != idx:
                continue
            _apply_rule(item, actor.lock_type)

    _pass3_stems(registry)


# Lock-type priority for remark ordering in _pass3_stems.
# Actors with stronger locks write their causal remark first.
_STEM_LOCK_REMARK_ORDER = {"STEM_天干合": 0, "STEM_天干克": 1, "STEM_天干冲": 2}


def _pass3_stems(registry: InteractionRegistry) -> None:
    """
    Stem lock: 天干合 > 天干克 > 天干冲.
    日柱 (idx 2) is the absolute anchor; tiebreaker = _STEM_LOCK_PRIORITY.

    Two-phase design:
      Phase 1 — assign every actor its lock_type and lock the winner item.
      Phase 2 — apply suppression rules in lock-priority order (天干合 first)
                so the most authoritative causal remark lands on each item
                before weaker locks can claim it.
    Without phase separation, a 天干克-locked actor processed before a
    天干合-locked actor would write a misleading remark that the "first
    causal remark wins" guard would then protect from correction.
    """
    # ── Phase 1: assign locks and register winners ───────────────────────────
    actor_state: dict[int, tuple[str, list, list, list]] = {}
    for idx, actor in registry.stem_actors.items():
        he_items = registry.get_stem_by_type(["天干合"], idx, active_only=False)
        ke_items = registry.get_stem_by_type(["天干克"], idx, active_only=False)
        chong_items = registry.get_stem_by_type(["天干冲"], idx, active_only=False)

        winner, lock_key = None, None
        if he_items:
            winner, lock_key = _pick_stem_winner(he_items), "STEM_天干合"
        elif ke_items:
            winner, lock_key = _pick_stem_winner(ke_items), "STEM_天干克"
        elif chong_items:
            winner, lock_key = _pick_stem_winner(chong_items), "STEM_天干冲"
        if winner is None:
            continue

        actor.lock_type = lock_key
        actor.lock_item_id = winner["_iid"]
        registry.lock(winner["_iid"])
        actor_state[idx] = (lock_key, he_items, ke_items, chong_items)

    # ── Phase 2: apply rules in lock-priority order ───────────────────────────
    for idx in sorted(
        actor_state, key=lambda i: _STEM_LOCK_REMARK_ORDER.get(actor_state[i][0], 99)
    ):
        lock_key, he_items, ke_items, chong_items = actor_state[idx]
        winner_iid = registry.stem_actors[idx].lock_item_id
        for item in he_items + ke_items + chong_items:
            if item.get("_iid") != winner_iid:
                _apply_rule(item, lock_key)

        # ── Cross-actor: STEM_天干合 → 干支透合 (贪合忘合) ────────────────────
        # 干支透合 is wired to branch_actor (target branch), so its suppression
        # by the SOURCE STEM's 天干合 lock must be applied explicitly here.
        # 贪合忘合: once the stem is engaged in a direct 天干合, it cannot also
        # form a covert bond with a hidden stem in another branch.
        if lock_key == "STEM_天干合":
            for item in registry.active_items():
                if item.get("类型") == "干支透合" and item.get("干方索引") == idx:
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
    半合/拱会/残会 : capped by participating branch lock types.
                    VACANT branch → treated as open/susceptible → 强势主流.
    共拱          : echo check — same element as structural lock → amplified.
    """
    for item in registry.active_items():
        itype = item.get("类型", "")
        indices = extract_pillar_indices(item.get("组合", "无"))

        if itype in {"比和", "暗合", "干支透合"}:
            if not item.get("强度"):
                item["强度"] = "显著影响"
            continue

        if itype in {"半合", "拱会", "残会"}:
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
                item["备注"] = STRENGTH_REMARKS.get(("VACANT", "branch"), "无")
            else:
                # Covers None (no lock) and SECONDARY (next-best minor lock).
                # SECONDARY is a weak residual bond — not strong enough to suppress
                # a partial structure, so it also resolves to 强势主流 here.
                # Pass 3 will have already downgraded the item if the SECONDARY
                # lock type generated a rule against it.
                item["强度"] = "强势主流"
            continue

        if itype == "共拱":
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
                    item["备注"] = STRENGTH_REMARKS.get(("GONG_GONG", "turbid"), "无")
            elif gong_element in structural_elements:
                # Echo upgrade: same element resonance — legitimate Pass 4 upgrade,
                # BUT respect Pass 3 suppressions: if already 消融吸收 or 大幅衰减,
                # the branch is too disrupted for echo to resurrect.
                if existing and STRENGTH_ORDER.get(existing, 0) >= STRENGTH_ORDER.get("大幅衰减", 0):
                    pass  # Pass 3 suppression stands — echo cannot resurrect
                else:
                    item["强度"] = "强势主流"
                    item["备注"] = STRENGTH_REMARKS.get(("GONG_GONG", "echo"), "无")
                    # Elevate constituent partials (same guard: respect Pass 3 suppressions)
                    target = item.get("拱向")
                    for sub in registry.active_items():
                        if sub.get("拱向") == target and sub.get("类型") in {
                            "半合",
                            "拱会",
                            "残会",
                        }:
                            sub_str = sub.get("强度")
                            if sub_str and STRENGTH_ORDER.get(sub_str, 0) >= STRENGTH_ORDER.get("大幅衰减", 0):
                                continue  # Pass 3 suppression stands
                            sub["强度"] = "强势主流"
            elif structural_elements:
                # Structural suppression — only apply if not already weaker.
                if not existing or STRENGTH_ORDER.get(
                    "大幅衰减", 0
                ) > STRENGTH_ORDER.get(existing, 0):
                    item["强度"] = "大幅衰减"
                    item["备注"] = STRENGTH_REMARKS.get(
                        ("GONG_GONG", "suppressed"), "无"
                    )
            elif not existing:
                item["强度"] = "强势主流"
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
        is_adj = item.get("紧贴", False)
        item["强度"] = DEFAULT_STRENGTH.get((itype, is_adj), "强势主流")


def _downgrade_if_stronger(current: str, cap: str) -> str:
    """Return cap only if current strength is stronger than cap; otherwise return current unchanged."""
    return cap if STRENGTH_ORDER.get(current, 99) < STRENGTH_ORDER.get(cap, 99) else current


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
            if wugen_count == len(tiers):
                cap, note = "中等衰减", "合而不化，双干无根，合力近无"
            elif wugen_count > 0:
                cap, note = "显著影响", "合而不化，浮干无力成合"
            else:
                continue
            item["强度"] = _downgrade_if_stronger(strength, cap)
            item.setdefault("备注", "")
            item["备注"] += ("、" if item["备注"] else "") + note

        elif itype == "天干克":
            controller = item.get("主动方")
            if not controller or effective_rooting.get(controller) != "无根":
                continue
            target_tier = next((v for k, v in effective_rooting.items() if k != controller), "无根")
            if target_tier != "无根":
                cap, note = "大幅衰减", "克者无根，被克者有根，克力瓦解"
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


def apply_bazi_master_priority(
    all_interactions: list, zhis: list, registry: InteractionRegistry
) -> list:
    """
    Five-Pass Resource Consumption Filter orchestrator.

    Pass 1 — Structural Lock    (三会/三合 per-branch, tie-breaker, synthetic inject)
    Pass 2 — Dual Lock          (贪合忘冲, VACANT, two strict rounds)
    Pass 3 — Conflict Pass      (PRIORITY_RULE_TABLE lookup per actor lock)
    Pass 4 — Group/Environment  (半合/共拱/比和/暗合 with echo & VACANT susceptibility)
    Pass 5 — Default Assignment (DEFAULT_STRENGTH table)

    Note: Pass S (Stem Rooting Modulation) is applied by the caller after this
    function returns, so the caller can supply the correct 通根 tier.
    """
    _pass1_structural(registry, zhis)
    # 共拱 detection runs here so any synthetic 半合/残会 from Pass 1 tie-breaking
    # are visible. In 4-pillar natal charts Pass 1 never injects synthetics
    # (requires 5+ branches — see _pass1_structural docstring). Da Yun and other
    # cycle contexts use cycle_interactions.py, not this function.
    _detect_gong_gong(registry, zhis)
    _pass2_dual(registry)
    _pass3_conflict(registry)
    _pass4_group(registry)
    _pass5_defaults(registry)

    result = registry.all_items()
    result.sort(key=lambda x: INTERACTION_TIER_ORDER.get(x.get("类型", "无"), 999))
    return result


# ── Pass 6 — Xun Kong (旬空) Post-Filter ─────────────────────────────────────

def _pass6_xun_kong(filtered: list, xun_kong_data: dict, zhis: list) -> None:
    """
    Post-filter: downgrade interactions involving void (旬空) branches.

    The 日柱 (day pillar) is the primary anchor: its xun kong pair applies to the
    entire natal chart. Any natal branch matching the day pillar's void pair is void.
    Rules:
    - 合类: 1+ void → downgrade 1 tier
    - 六冲: 1 void → 冲开旬空 remark only; both void → downgrade 1 tier
    - 刑/害/破/暗合/比和: 1+ void → downgrade 1 tier
    - 共拱: 1+ void participant branches → downgrade 1 tier
    - 天干: skip
    """
    # Day pillar void pair applies to the entire chart
    day_xk_str = xun_kong_data.get("日柱", {}).get("旬空", "")

    for item in filtered:
        itype = item.get("类型", "")
        if itype in _XK_STEM_ONLY:
            continue

        # 干支透合: use 支方索引 to find the branch side
        if itype == "干支透合":
            zhi_idx = item.get("支方索引")
            if zhi_idx is not None:
                pn = _PILLAR_NAMES_CN[zhi_idx]
                if zhis[zhi_idx] in day_xk_str:
                    _downgrade_by_one_tier_xk(item, _build_xk_remark([pn], "misc_single"))
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


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Detection Helpers
# ══════════════════════════════════════════════════════════════════════════════


# _get_shi_shen_for_stem_pair → now get_shi_shen_for_stem_pair (public) imported from day_master
_get_shi_shen_for_stem_pair = get_shi_shen_for_stem_pair


def _detect_san_hui(zhis: list, registry: InteractionRegistry) -> None:
    """
    Detect full 三会 and partial 拱会/残会.

    Field assignment for partials:
      - 拱会 (cardinal branch absent): carries `犹出` = the missing cardinal branch.
        The cardinal is the most powerful member; its absence means the structure
        is still arching toward it — hence 犹出 ("still to emerge").
      - 残会 (cardinal branch present, one satellite missing): carries `待会` = the
        missing non-cardinal branch. The structure is partially formed; it waits
        for the last satellite — hence 待会 ("waiting to convene").
    Both partials carry `方位` and `元素` derived from the directional group.
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
            registry.register(
                {
                    "类型": "三会",
                    "元素": element_from_direction,
                    "方位": direction,
                    "组合": "-".join(match_names),
                    "组合明细": combo_detail,
                    "状态": get_status("三会", {"key": "full"}),
                }
            )

        elif len(matched) == 2:
            cardinal = cardinal_branches.get(element)
            cardinal_present = cardinal in matched
            itype_partial = "残会" if cardinal_present else "拱会"
            missing = next((b for b in group if b not in matched), None)
            idxs = list(matched.values())
            item = {
                "类型": itype_partial,
                "元素": element_from_direction,
                "方位": direction,
                "组合": "-".join(match_names),
                "组合明细": combo_detail,
                "状态": get_status(
                    "三会", {"key": "residual" if cardinal_present else "arch"}
                ),
                "紧贴": abs(idxs[0] - idxs[1]) == 1,
            }
            if cardinal_present:
                item["待会"] = missing or "无"   # 残会: missing non-cardinal branch
            else:
                item["犹出"] = missing or "无"   # 拱会: missing cardinal branch
            registry.register(item)


def _detect_san_he(zhis: list, registry: InteractionRegistry) -> None:
    """Detect full 三合."""
    for element, group in triple_he.items():
        matched: dict[str, int] = {}
        for branch in group:
            for k, zhi in enumerate(zhis):
                if zhi == branch and k not in matched.values():
                    matched[branch] = k
                    break
        if len(matched) != 3:
            continue
        indices = tuple(sorted(matched.values()))
        match_names = sorted(
            [_PILLAR_NAMES_CN[k] for k in matched.values()],
            key=lambda p: _PILLAR_IDX_MAP[p],
        )
        registry.register(
            {
                "类型": "三合",
                "元素": element,
                "组合": "-".join(match_names),
                "组合明细": {_PILLAR_NAMES_CN[k]: zhis[k] for k in matched.values()},
                "状态": get_status("三合", {"key": "full"}),
                "邀出": "已全",
                "紧贴": any(
                    indices[i + 1] - indices[i] == 1 for i in range(len(indices) - 1)
                ),
            }
        )


_PT_KEY_MAP: dict[str, str] = {
    "无恩之刑": "ungrateful",
    "恃势之刑": "bullying",
    "无礼之刑": "uncivilized",
    "自刑": "self",
}


def _detect_pairwise(zhis: list, gans: list, registry: InteractionRegistry) -> None:
    """
    Detect all pairwise branch and stem interactions.

    Branch (all registered independently):  六冲, 六合, 半合, 比和, 六害, 六破, 刑, 暗合, 干支透合
    Stem (all registered independently):    天干合, 天干冲, 天干克
    Suppression is handled by the priority filter, not at detection time.

    Stem interaction field schema (consistent across all three types):
        类型, 组合, 组合明细, 状态, 紧贴, 主动方, 根基
      天干合 additionally:
        元素 (合化五行)

      主动方: controller pillar label for 天干克; "相互" for 天干合/冲.
      根基: {pillar_label: tier} — 4-tier (深根/中根/浅根/无根) via get_stem_root_tier().

    干支透合 is bidirectional per pair: checks both g_i→zhis[j] and g_j→zhis[i].
    Each item stores 干方索引 (source stem pillar) and 支方索引 (target branch pillar)
    so the priority filter can apply branch locks only from the target branch.
    """
    _day_stem = gans[2]
    _hidden_labels = ("本气", "中气", "余气")
    for i in range(4):
        for j in range(i + 1, 4):
            b_i, b_j = zhis[i], zhis[j]
            is_adjacent = j - i == 1
            pn_i, pn_j = _PILLAR_NAMES_CN[i], _PILLAR_NAMES_CN[j]
            combo = f"{pn_i}-{pn_j}"
            detail = {pn_i: b_i, pn_j: b_j}

            # ── Branch Tier 1 — register all; priority filter suppresses later ──
            # 六冲, 六合, and 半合 are all registered independently even when
            # the same pair qualifies for multiple. A practitioner notes all
            # relationships present; suppression is a priority question, not
            # a detection question.
            if clash_map.get(b_i) == b_j:
                registry.register(
                    {
                        "类型": "六冲",
                        "组合": combo,
                        "组合明细": detail,
                        "紧贴": is_adjacent,
                        "状态": get_status(
                            "六冲", {"key": "adjacent" if is_adjacent else "distant"}
                        ),
                    }
                )
            if six_he_map.get(b_i) == b_j:
                pk = tuple(sorted([b_i, b_j]))
                elem = six_he_element_map.get(pk, {}).get("primary", "无")
                registry.register(
                    {
                        "类型": "六合",
                        "组合": combo,
                        "组合明细": detail,
                        "元素": elem,
                        "紧贴": is_adjacent,
                        "状态": get_status(
                            "六合", {"key": "adjacent" if is_adjacent else "distant"}
                        ),
                    }
                )
            # 半合 — always checked regardless of 六冲/六合 on same pair.
            # Guard: b_i == b_j means two pillars share the same branch — not
            # a valid 半合 (a branch cannot combine with itself).
            for element, group in triple_he.items():
                if b_i != b_j and b_i in group and b_j in group:
                    unique_in = set(z for z in zhis if z in group)
                    cardinal = cardinal_branches.get(element)
                    if cardinal in zhis:
                        state, yao = "strong", "无"
                    elif len(unique_in) == 2:
                        state, yao = "arching", cardinal_branches[element]
                    else:
                        state, yao = "weak", "无"
                    registry.register(
                        {
                            "类型": "半合",
                            "元素": element,
                            "组合": combo,
                            "组合明细": detail,
                            "状态": get_status(
                                "半合", {"element": element, "state": state}
                            ),
                            "邀出": yao,
                            "紧贴": is_adjacent,
                        }
                    )
                    break

            # ── Independent branch checks ──────────────────────────────────
            peer = is_valid_peer_combination(b_i, b_j)
            if peer:
                registry.register(
                    {
                        "类型": "比和",
                        "组合": combo,
                        "组合明细": detail,
                        "元素": peer["element"],
                        "紧贴": is_adjacent,
                        "状态": get_status("比和"),
                    }
                )

            if harm_map.get(b_i) == b_j:
                registry.register(
                    {
                        "类型": "六害",
                        "组合": combo,
                        "组合明细": detail,
                        "紧贴": is_adjacent,
                        "状态": get_status(
                            "六害", {"key": "adjacent" if is_adjacent else "distant"}
                        ),
                    }
                )

            if break_map.get(b_i) == b_j:
                registry.register(
                    {
                        "类型": "六破",
                        "组合": combo,
                        "组合明细": detail,
                        "紧贴": is_adjacent,
                        "状态": get_status(
                            "六破", {"key": "adjacent" if is_adjacent else "distant"}
                        ),
                    }
                )

            # 刑 — all applicable types, independent of Tier 1.
            # is_valid_punishment handles all cases:
            #   b_i == b_j → 自刑 (same branch in two pillars, e.g. 午年-午日)
            #   b_i != b_j → 无恩/恃势/无礼 where applicable
            result = is_valid_punishment(b_i, b_j, natal_branches=zhis)
            if result:
                pt_key = _PT_KEY_MAP.get(result["type"], "ungrateful")
                registry.register(
                    {
                        "类型": result["type"],
                        "组合": combo,
                        "组合明细": detail,
                        "紧贴": is_adjacent,
                        "状态": get_status(
                            "三刑",
                            {
                                "punishment_type": pt_key,
                                "is_full": result.get("is_full", False),
                                "is_adjacent": is_adjacent,
                            },
                        ),
                    }
                )

            # hidden_stem_he pairs (寅丑, 卯申, 午亥) have no overlap with clash_map;
            # 六冲 suppression is handled by the priority filter, not at detection.
            if b_j in hidden_stem_he.get(b_i, set()):
                registry.register(
                    {
                        "类型": "暗合",
                        "组合": combo,
                        "组合明细": detail,
                        "状态": get_status("暗合"),
                    }
                )

            # ── 干支透合 — natal stem combines covertly with hidden stem in a different pillar's branch ──
            # Distinct from 暗合 (branch↔branch): here a heavenly stem from one pillar
            # covertly combines with a hidden stem (藏干) inside another pillar's branch.
            # Bidirectional per pair: g_i → zhis[j] AND g_j → zhis[i].
            # 冲则气散 and 贪合忘合 are handled by the priority filter (PRIMARY_六冲 and STEM_天干合
            # rules); detection registers all candidates and suppression is applied post-detection.
            # 藏干十神 is always relative to the day master (gans[2]).
            _stem_i, _stem_j = gans[i], gans[j]
            # Direction 1: stem of pillar i covertly bonds with hidden stem in branch of pillar j
            for _hi, _hs in enumerate(LunarUtil.ZHI_HIDE_GAN.get(b_j, [])):
                if stem_combines.get(_stem_i) == _hs:
                    registry.register(
                        {
                            "类型": "干支透合",
                            "组合": combo,
                            "组合明细": {
                                f"{pn_i}干": _stem_i,
                                f"{pn_j}支": b_j,
                                "藏干": _hs,
                                "藏干层": _hidden_labels[_hi] if _hi < 3 else "余气",
                                "藏干十神": _get_shi_shen_for_stem_pair(_day_stem, _hs),
                                "合化五行": _STEM_COMBINE_ELEMENT.get(_stem_i, "无"),
                            },
                            "干方索引": i,
                            "支方索引": j,
                            "状态": get_status("干支透合"),
                        }
                    )
                    break  # 天干合 is 1-to-1; one hidden stem match per branch
            # Direction 2: stem of pillar j covertly bonds with hidden stem in branch of pillar i
            for _hi, _hs in enumerate(LunarUtil.ZHI_HIDE_GAN.get(b_i, [])):
                if stem_combines.get(_stem_j) == _hs:
                    registry.register(
                        {
                            "类型": "干支透合",
                            "组合": combo,
                            "组合明细": {
                                f"{pn_j}干": _stem_j,
                                f"{pn_i}支": b_i,
                                "藏干": _hs,
                                "藏干层": _hidden_labels[_hi] if _hi < 3 else "余气",
                                "藏干十神": _get_shi_shen_for_stem_pair(_day_stem, _hs),
                                "合化五行": _STEM_COMBINE_ELEMENT.get(_stem_j, "无"),
                            },
                            "干方索引": j,
                            "支方索引": i,
                            "状态": get_status("干支透合"),
                        }
                    )
                    break  # 天干合 is 1-to-1; one hidden stem match per branch

            # ── Stem interactions — all registered independently ──────────
            # A stem pair may simultaneously combine AND clash/control
            # (e.g. 甲-庚: 甲庚天干冲 + 庚克甲天干克). All are registered;
            # PRIORITY_RULE_TABLE suppresses the weaker via 消融吸收.
            g_i, g_j = gans[i], gans[j]
            stem_detail = {pn_i: g_i, pn_j: g_j}
            # Pre-compute rooting tiers for both stems across ALL natal branches
            tier_i = get_stem_root_tier(stem_elements.get(g_i, ""), zhis)
            tier_j = get_stem_root_tier(stem_elements.get(g_j, ""), zhis)
            root_detail = {pn_i: tier_i, pn_j: tier_j}
            if stem_combines.get(g_i) == g_j:
                registry.register(
                    {
                        "类型": "天干合",
                        "元素": _STEM_COMBINE_ELEMENT.get(g_i, ""),
                        "组合": combo,
                        "组合明细": stem_detail,
                        "状态": get_status("天干合"),
                        "紧贴": is_adjacent,
                        "主动方": "相互",
                        "根基": root_detail,
                    }
                )
            if stem_clashes.get(g_i) == g_j:
                registry.register(
                    {
                        "类型": "天干冲",
                        "组合": combo,
                        "组合明细": stem_detail,
                        "状态": get_status(
                            "天干冲", {"key": "adjacent" if is_adjacent else "distant"}
                        ),
                        "紧贴": is_adjacent,
                        "主动方": "相互",
                        "根基": root_detail,
                    }
                )
            if (g_i, g_j) in stem_controls or (g_j, g_i) in stem_controls:
                controller_label = pn_i if (g_i, g_j) in stem_controls else pn_j
                registry.register(
                    {
                        "类型": "天干克",
                        "组合": combo,
                        "组合明细": stem_detail,
                        "状态": get_status(
                            "天干克", {"key": "adjacent" if is_adjacent else "distant"}
                        ),
                        "紧贴": is_adjacent,
                        "主动方": controller_label,
                        "根基": root_detail,
                    }
                )


# ── 共拱 positional lookup ───────────────────────────────────────────────────
# All 12 gap-1 cyclic pairs: for each missing branch C, the one pair (A, B)
# that sandwiches it on the 12-branch cycle (A–C–B consecutive).
# Source: 子丑寅卯辰巳午未申酉戌亥 (circular).
POSITIONAL_ARCH_MAP: dict[str, tuple[str, str]] = {
    "丑": ("子", "寅"),
    "寅": ("丑", "卯"),
    "卯": ("寅", "辰"),
    "辰": ("卯", "巳"),
    "巳": ("辰", "午"),
    "午": ("巳", "未"),
    "未": ("午", "申"),
    "申": ("未", "酉"),
    "酉": ("申", "戌"),
    "戌": ("酉", "亥"),
    "亥": ("戌", "子"),
    "子": ("亥", "丑"),
}

# Classification of each positional arch by structural context.
# 三会共拱: both flanking branches share a directional group with the missing cardinal.
# 跨局共拱: flanking branches come from different groups — purely positional.
_ARCH_CLASSIFICATION: dict[str, str] = {
    "丑": "跨局共拱",
    "寅": "跨局共拱",
    "卯": "三会共拱木方",
    "辰": "跨局共拱",
    "巳": "跨局共拱",
    "午": "三会共拱火方",
    "未": "跨局共拱",
    "申": "跨局共拱",
    "酉": "三会共拱金方",
    "戌": "跨局共拱",
    "亥": "跨局共拱",
    "子": "三会共拱水方",
}


def _gong_gong_target(item: dict) -> str | None:
    """
    Return the missing branch that a partial structure is arching toward, or None.

    Partial type → key that holds the missing branch:
        半合  → 邀出  (missing cardinal of the triple-combination)
        拱会  → 犹出  (missing branch of the directional group, cardinal absent)
        残会  → 待会  (missing non-cardinal branch; cardinal is present)
    """
    itype = item.get("类型")
    if itype == "半合":
        v = item.get("邀出")
        return v if v and v != "无" else None
    if itype == "拱会":
        v = item.get("犹出")
        return v if v and v != "无" else None
    if itype == "残会":
        v = item.get("待会")
        return v if v and v != "无" else None
    return None


def _detect_gong_gong(registry: InteractionRegistry, zhis: list) -> None:
    """
    Detect 共拱 in two layers, both registered independently:

    Layer 1 — Positional 共拱 (primary classical form):
        Any two branches present in the chart that sandwich a missing branch
        between them on the 12-branch cycle (A–C–B consecutive, C absent).
        All 12 possible missing-branch targets are checked.
        Subtypes:
            三会共拱  — A and B are in the same directional group; C is cardinal
            跨局共拱  — A and B span different groups (purely positional)

    Layer 2 — Structural 共拱 (named subtype, multi-partial convergence):
        Two or more partial structures (半合/拱会/残会) from different structural
        groups both arching toward the same missing branch.
        Only fires when at least two partials converge — a single 拱会 or
        arching 半合 is already labelled as such and does not qualify.

    Both layers independently stamp "共拱" on their constituent items.
    Priority filter handles suppression relative to other locks.
    """
    # ── Layer 1: Positional 共拱 ──────────────────────────────────────────────
    present = set(zhis)
    for missing_branch, (a, b) in POSITIONAL_ARCH_MAP.items():
        if missing_branch in present:
            continue  # branch is not actually missing
        if a not in present or b not in present:
            continue  # both flanking branches must be in chart

        # Find which pillars hold A and B (there may be duplicates)
        a_indices = [i for i, z in enumerate(zhis) if z == a]
        b_indices = [i for i, z in enumerate(zhis) if z == b]

        for a_idx in a_indices:
            for b_idx in b_indices:
                if a_idx == b_idx:
                    continue  # same pillar cannot count as both
                lo, hi = min(a_idx, b_idx), max(a_idx, b_idx)
                pn_lo = _PILLAR_NAMES_CN[lo]
                pn_hi = _PILLAR_NAMES_CN[hi]
                combo = f"{pn_lo}-{pn_hi}"
                detail = {pn_lo: zhis[lo], pn_hi: zhis[hi]}
                frame = _ARCH_CLASSIFICATION[missing_branch]

                # Element from the directional group if 三会共拱,
                # else from branch_elements of the missing branch
                if frame.startswith("三会共拱"):
                    element = next(
                        (
                            el
                            for el, cb in cardinal_branches.items()
                            if cb == missing_branch
                        ),
                        "无",
                    )
                else:
                    element = branch_elements.get(missing_branch, "无")

                clashed = bool(
                    clash_map.get(zhis[lo]) in present
                    or clash_map.get(zhis[hi]) in present
                )
                virtual_label = f"虚{element}局" if element else "虚局"
                status = (
                    f"共拱{missing_branch}({frame}，{virtual_label}，混杂)"
                    if clashed
                    else f"共拱{missing_branch}({frame}，{virtual_label})"
                )

                item = {
                    "类型": "共拱",
                    "元素": element,
                    "框架": frame,
                    "组合": combo,
                    "组合明细": detail,
                    "拱向": missing_branch,
                    "紧贴": hi - lo == 1,
                    "状态": status,
                    "混杂": clashed,
                }
                registry.register(item)
                # Stamp constituent pillars
                for idx in (lo, hi):
                    for it in registry.active_items():
                        if (
                            it.get("类型") in {"半合", "拱会", "残会"}
                            and idx in extract_pillar_indices(it.get("组合", "无"))
                            and _gong_gong_target(it) == missing_branch
                        ):
                            it["拱向"] = missing_branch

    # ── Layer 2: Structural 共拱 (multi-partial convergence) ──────────────────
    partials: list[dict] = [
        it for it in registry.active_items() if _gong_gong_target(it) is not None
    ]
    target_map: dict[str, list[dict]] = {}
    for it in partials:
        target_map.setdefault(_gong_gong_target(it), []).append(it)

    for missing_branch, contributors in target_map.items():
        if len(contributors) < 2:
            continue

        # Deduplicate pillar indices across contributors
        seen: set[int] = set()
        combined_detail: dict = {}
        all_names: list[str] = []
        for sub in contributors:
            for pname, branch in sub.get("组合明细", {}).items():
                pidx = _PILLAR_IDX_MAP.get(pname)
                if pidx is not None and pidx not in seen:
                    seen.add(pidx)
                    all_names.append(pname)
                    combined_detail[pname] = branch

        all_names_sorted = sorted(all_names, key=lambda p: _PILLAR_IDX_MAP[p])
        # Derive element from the missing branch directly — not inherited from contributors.
        element = branch_elements.get(missing_branch, "无")

        itypes = {c.get("类型") for c in contributors}
        if "拱会" in itypes and "半合" in itypes:
            frame_label = "会合共拱"
        elif "半合" in itypes:
            frame_label = "双半合共拱"
        elif "拱会" in itypes:
            frame_label = "双拱会共拱"
        else:
            frame_label = "复合共拱"

        participating = set(combined_detail.values())
        clashed = bool({b for b in participating if clash_map.get(b) in zhis})
        virtual_label = f"虚{element}局" if element else "虚局"
        status = (
            f"共拱{missing_branch}({frame_label}，{virtual_label}，混杂)"
            if clashed
            else f"共拱{missing_branch}({frame_label}，{virtual_label})"
        )

        # 紧贴: True if all participant pillars are consecutive (no gaps in index span)
        sorted_indices = [_PILLAR_IDX_MAP[p] for p in all_names_sorted]
        is_tight = (sorted_indices[-1] - sorted_indices[0]) == (len(sorted_indices) - 1)

        item = {
            "类型": "共拱",
            "元素": element,
            "框架": frame_label,
            "组合": "-".join(all_names_sorted),
            "组合明细": combined_detail,
            "拱向": missing_branch,
            "紧贴": is_tight,
            "状态": status,
            "混杂": clashed,
            "_layer": 2,
        }
        registry.register(item)
        for sub in contributors:
            sub["拱向"] = missing_branch

    # ── Unified subsumption: L2 composite weakens its contributors ───
    # One rule (以大局为主): if a composite 共拱 (L2) exists for a given
    # missing branch, every other active item stamped with the same 拱向 target
    # — contributors (拱会/半合/残会) AND any smaller L1 positional 共拱 —
    # is weakened to 中等衰减 (moderately suppressed, not fully absorbed).
    # If a contributor has void branches, Pass 6 will further downgrade it to 大幅衰减.
    for item in list(registry.active_items()):
        if item.get("类型") != "共拱" or item.get("_layer") != 2:
            continue
        target = item["拱向"]
        frame = item["框架"]
        for sub in list(registry.active_items()):
            if sub["_iid"] == item["_iid"]:
                continue
            if sub.get("拱向") == target:
                # Defensive guard: only downgrade — don't upgrade items already
                # at a stronger suppression (future-proofing against pass reordering).
                sub_str = sub.get("强度")
                if sub_str and STRENGTH_ORDER.get(sub_str, 0) > STRENGTH_ORDER.get("中等衰减", 0):
                    continue  # already more suppressed than 中等衰减
                sub["强度"] = "中等衰减"
                sub["备注"] = f"已被复合共拱（{frame}，拱{target}）涵盖，力场衰减"


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Output Assembly
# ══════════════════════════════════════════════════════════════════════════════

_TIER1_TYPES = {"三会", "三合", "六冲", "六合"}
_TIER2_TYPES = {"共拱", "拱会", "残会", "半合", "天干合", "天干克", "天干冲", "比和"}
_TIER3_TYPES = {
    "无恩之刑",
    "恃势之刑",
    "无礼之刑",
    "自刑",
    "六害",
    "六破",
    "暗合",
    "干支透合",
}


_OUTPUT_STRIP_KEYS = {"_iid", "_synthetic", "_layer", "干方索引", "支方索引"}


def _build_pillar_dynamics(filtered: list) -> dict:
    """
    Distribute interactions into per-pillar tier buckets.
    Multi-pillar interactions appear in all affected pillars (same object reference).
    Internal keys (_iid, _synthetic) are stripped from each item in-place on
    first encounter — single pass, no extra iteration.
    """
    dynamics = {
        i: {"第一梯队_纲领层": [], "第二梯队_气势层": [], "第三梯队_琐碎层": []}
        for i in range(4)
    }
    stripped: set[int] = set()  # id(item) — track which items are already clean
    added: set[tuple] = set()
    for item in filtered:
        itype = item.get("类型", "无")
        indices = extract_pillar_indices(item.get("组合", "无"))
        if not indices:
            continue
        if itype in _TIER1_TYPES:
            tier = "第一梯队_纲领层"
        elif itype in _TIER2_TYPES:
            tier = "第二梯队_气势层"
        elif itype in _TIER3_TYPES:
            tier = "第三梯队_琐碎层"
        else:
            logger.warning("未知交互类型 %s 未分配梯队，默认归入第三梯队", itype)
            tier = "第三梯队_琐碎层"
        item_id = item["_iid"]
        # Strip internal keys once per item, reusing item_id before it's gone
        if item_id not in stripped:
            for k in _OUTPUT_STRIP_KEYS:
                item.pop(k, None)
            stripped.add(item_id)
        for idx in indices:
            key = (idx, tier, item_id)
            if key not in added:
                dynamics[idx][tier].append(item)
                added.add(key)

    return {_PILLAR_NAMES_CN[k]: dynamics[k] for k in range(4)}


def _build_vacant_flags(registry: InteractionRegistry) -> dict:
    """
    Return pillar_name → True for any VACANT branch actor.
    Signals the LLM that a pillar is structurally open and reactive.
    """
    return {
        _PILLAR_NAMES_CN[idx]: True
        for idx, actor in registry.branch_actors.items()
        if actor.lock_type == "VACANT"
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Branch Rooting Helpers
# ══════════════════════════════════════════════════════════════════════════════


# get_stem_root_tier imported from day_master


def compute_pillar_rooting(
    gans: list[str],
    zhis: list[str],
    pillar_cn: list[str] | None = None,
) -> dict:
    """
    Qualitative 根基 computation for any set of pillars.

    Tier determined by deepest root type found across all branches:
    本气根 → 深根 | 中气根 → 中根 | 余气根 → 浅根 | none → 无根

    Args:
        gans: stems in order (any length)
        zhis: branches in order, parallel to gans
        pillar_cn: pillar display names used as result keys
                   (default: ["年柱","月柱","日柱","时柱"]).
                   "柱" is stripped when building branch descriptions.

    Returns:
        {"年柱": {"天干": "甲", "根基强度": "中根", "根基说明": "通根于月支寅(本气根)"}, ...}
    """
    if pillar_cn is None:
        pillar_cn = ["年柱", "月柱", "日柱", "时柱"]

    def _short(label: str) -> str:
        return label[:-1] if label.endswith("柱") else label

    result = {}
    for gan, col in zip(gans, pillar_cn):
        elem = stem_elements.get(gan)
        best_idx = len(_ROOT_DEPTH_LABELS)  # sentinel: no match
        matches: list[str] = []

        for j, zhi in enumerate(zhis):
            for idx, (hidden_stem, _) in enumerate(BRANCH_HIDDEN_ROOTING.get(zhi, [])):
                if stem_elements.get(hidden_stem) == elem:
                    if idx < best_idx:
                        best_idx = idx
                    tier_label = _ROOT_DEPTH_LABELS[idx] if idx < len(_ROOT_DEPTH_LABELS) else "余气根"
                    matches.append(f"{_short(pillar_cn[j])}支{zhi}({tier_label})")
                    break

        if best_idx == 0:
            strength = "深根"
        elif best_idx == 1:
            strength = "中根"
        elif best_idx == 2:
            strength = "浅根"
        else:
            strength = "无根"

        result[col] = {
            "天干": gan,
            "根基强度": strength,
            "根基说明": "通根于" + "、".join(matches) if matches else "无根浮干",
        }
    return result


# SECTION 8 — Orchestrator
# ══════════════════════════════════════════════════════════════════════════════


def get_interactions(lunar_birthday) -> dict:
    """
    Extract and analyze all pillar interactions from a BaZi chart.

    Args:
        lunar_birthday (Lunar): Lunar calendar object from lunar_python.

    Returns:
        dict: LLM-ready JSON under the "作用" key containing:
            - 关系总览: Status strings for all 强势主流/显著影响 interactions
            - 柱位动态: Per-pillar interactions split into three tiers
                (第一梯队_纲领层 / 第二梯队_气势层 / 第三梯队_琐碎层)
            - 柱位开放: Pillars freed by 贪合忘冲 (VACANT); only True entries shown
            - 判定优先级: Reference tier groupings for all 16 interaction types
            - _raw_priority_list: Internal list passed to wu_xing for scoring
              (stripped from final output by the aggregator)

    Flow:
      1. Build InteractionRegistry with BranchActor/StemActor per pillar
      2. Detect 三会/三合 (structural), then all pairwise interactions
      3. Five-pass priority filter (共拱 detection runs inside, after Pass 1
         so synthetic half-structures from losers are visible)
      4. Apply Pass 6 xun kong post-filter (self-computed from lunar_birthday)
      5. Assemble per-pillar dynamics, vacant flags, and 关系总览 summary
    """
    baZi = lunar_birthday.getEightChar()
    gans = [baZi.getYearGan(), baZi.getMonthGan(), baZi.getDayGan(), baZi.getTimeGan()]
    zhis = [baZi.getYearZhi(), baZi.getMonthZhi(), baZi.getDayZhi(), baZi.getTimeZhi()]

    # ── Initialise registry ────────────────────────────────────────────────
    registry = InteractionRegistry()
    for idx in range(4):
        registry.branch_actors[idx] = BranchActor(idx, zhis[idx])
        registry.stem_actors[idx] = StemActor(idx, gans[idx])

    # ── Detection ─────────────────────────────────────────────────────────
    _detect_san_hui(zhis, registry)
    _detect_san_he(zhis, registry)
    _detect_pairwise(zhis, gans, registry)
    # Note: _detect_gong_gong is called inside apply_bazi_master_priority,
    # after Pass 1, so synthetic 半合/残会 injected during structural
    # tie-breaking are visible to 共拱 detection.

    # ── Five-pass priority filter (includes 共拱 detection after Pass 1) ──
    filtered = apply_bazi_master_priority(registry.all_items(), zhis, registry)

    # ── Pass S: Stem Rooting Modulation ──────────────────────────────────
    day_elem = stem_elements.get(gans[2], "")
    tong_gen = compute_de_di(day_elem, zhis)["通根"] if day_elem else "中根"
    _pass_stem_rooting(filtered, tong_gen=tong_gen)

    # ── Pass 6: Xun Kong (旬空) post-filter ──────────────────────────────
    xun_kong_result = void_xun_kong.get_xun_kong(lunar_birthday)
    xk_inner = xun_kong_result.get("旬空", {})
    _pass6_xun_kong(filtered, xk_inner, zhis)

    # ── Branch rooting (根基) ─────────────────────────────────────────────
    rooting = compute_pillar_rooting(gans, zhis)

    # ── Output assembly ───────────────────────────────────────────────────
    # Internal keys (_iid, _synthetic) are stripped inside _build_pillar_dynamics.
    pillar_dynamics = _build_pillar_dynamics(filtered)
    vacant_flags = _build_vacant_flags(registry)

    # 关系总览: active (强势主流 / 显著影响) interactions only
    summary: list[str] = []
    seen_summary: set[str] = set()
    for item in filtered:
        if item.get("强度") not in ("强势主流", "显著影响"):
            continue
        detail_vals = "".join(item.get("组合明细", {}).values())
        label = item.get("状态") or f"{item.get('类型', '')}({detail_vals})"
        if label not in seen_summary:
            summary.append(label)
            seen_summary.add(label)

    return {
        "作用": {
            "关系总览": summary,
            "根基": rooting,
            "柱位动态": pillar_dynamics,
            "柱位开放": vacant_flags,
            "判定优先级": {
                "第一梯队_纲领层": ["三会", "三合", "六冲", "六合"],
                "第二梯队_气势层": [
                    "共拱",
                    "比和",
                    "拱会",
                    "残会",
                    "半合",
                    "天干合",
                    "天干克",
                    "天干冲",
                ],
                "第三梯队_琐碎层": [
                    "无恩之刑",
                    "恃势之刑",
                    "无礼之刑",
                    "自刑",
                    "六害",
                    "六破",
                    "暗合",
                    "干支透合",
                ],
            },
        },
        "_raw_priority_list": filtered,
    }


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from src.astronomer_calculations.bazi_pillars import get_bazi_pillars
    from src.utils.logging import configure_logging, get_logger

    # Initialize logging system
    configure_logging()
    logger = get_logger(__name__)

    # python -m src.astronomer_calculations.natal_interactions

    # Desmond's birthday example
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    tst_birthday, _ = get_true_solar_time(
        datetime_birthday, 1.3253, 103.808053
    )  # Get true solar time

    # # Corinne's birthday example
    # solar_birthday = Solar.fromYmdHms(
    #     1987, 6, 3, 12, 6, 0
    # )  # Create solar date June 3, 1987 at 12:06 PM
    # tst_birthday, inputs_report = get_true_solar_time(
    #     datetime(1987, 6, 3, 12, 6, 0), 1.4759, 103.808053
    # )

    # Random's birthday example
    # solar_birthday = Solar.fromYmdHms(1999, 2, 11, 9, 7, 0)  # Create solar date
    # datetime_birthday = datetime(1999, 2, 11, 9, 7, 0)  # Create datetime object
    # tst_birthday, _ = get_true_solar_time(
    #     datetime_birthday, 1.3253, 103.808053
    # )  # Get true solar time

    lunar_birthday = tst_birthday.getLunar()

    logger.info("阳历生日: " + solar_birthday.toYmdHms())
    logger.info("真太阳时生日: " + tst_birthday.toYmdHms())

    lunar_birthday = tst_birthday.getLunar()  # Convert to lunar calendar

    bazi_json = get_bazi_pillars(tst_birthday.getLunar())
    logger.info(f"{bazi_json}")

    # Get interactions in LLM-ready JSON format
    result = get_interactions(lunar_birthday)

    logger.info("--- JSON Output for LLM ---")
    logger.info(json.dumps(result, ensure_ascii=False, indent=2))
