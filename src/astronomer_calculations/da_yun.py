"""
Da Yun (大运 - Big Luck Cycles) Calculation Module

This module calculates the Big Luck Cycles (Da Yun) for a given lunar birthday and gender.
Each Da Yun cycle lasts 10 years and represents a major phase of life's fortune.

Comprehensive BaZi Destiny Analysis Components:

1. 起运 (Luck Cycle Start):
   - Gender-dependent timing based on birth solar term position
   - 顺推 (forward progression) or 逆推 (backward progression) logic

2. 大运周期 (10-Year Big Luck Cycles):
   - 10 consecutive cycles covering major life phases
   - Year ranges and age calculations included for each cycle

3. 干支 (Heavenly Stem & Earthly Branch):
   - Complete Gan-Zhi representation for each cycle
   - 旬 (Sexagenary Cycle) and 旬空 (Void Day) information

4. 五行 (Five Elements with Polarity):
   - Stem Five Element (干:木/火/土/金/水) and polarity (阳/阴)
   - Branch Five Element (支:木/火/土/金/水) and polarity (阳/阴)
   - Derived from lunar-python library data

5. 纳音 (Nayin - Harmonic Resonance Element):
   - Descriptive nayin names for each stem-branch combination
   - Examples: "海中金" (Gold in the Sea), "炉中火" (Fire in the Furnace)
   - Classical BaZi concept from lunar-python library's LunarUtil.NAYIN mapping

6. 十神 (Ten Gods - Relational Categories):
   - Primary theme: Based on Day Stem vs. Cycle Stem relationship
   - Hidden themes: Ten Gods for all three hidden stems in branch (本气/中气/余气)
   - 10 relationship categories mapping: 正财/偏财/正官/七杀/正印/偏印/食神/伤官/比肩/劫财

7. 地势 (Life Stage - Long Life Palace):
   - 12-stage positional strength from 长生十二宫 system
   - Maps each stem-branch pair to its corresponding life stage
   - Values: 长生→沐浴→冠带→临官→帝旺→衰→病→死→墓→绝→胎→养

8. 作用 (Interactions - Comprehensive 1×4 Scan):
   Da Yun pillar scanned against all 4 natal pillars with Tier-Based Priority (16 types):

   TIER 0-1 (Framework - Extreme):
   - 反吟: Stem clash + Branch clash (same natal pillar) → complete instability
   - 伏吟: Stem match + Branch match (same natal pillar) → stagnation

   TIER 2-3 (Framework - Structural):
   - 三会: Directional combination (3 branches, one per pillar)
   - 三合: Triple harmony (3 branches, specific elements)
   - 六冲: Clash (6 combinations) + 开库 sub-type (Earth tomb release)
   - 六合: Six Harmony (6 combinations with transformation)

   TIER 4-7 (Dynamics - Partial Combinations):
   - 共拱: Co-arching (two partial combos converging on missing branch)
   - 比和: Peer combinations (adjacent same-element branches)
   - 拱会: Two non-cardinal branches virtually pulling toward missing cardinal
   - 残会/半合: Cardinal + one flank, or partial element triple

   TIER 8-14 (Details - Stem & Parasitic):
   - 天干合(日主): Day Master stem harmony (highest stem priority)
   - 天干克(日主): Day Master stem clash (Day Master threat)
   - 天干合: Heavenly stem harmony
   - 天干克: Heavenly stem control
   - 天干冲: Heavenly stem opposition (same polarity, mutual clash)
   - 三刑 (Triple Punishments): [寅巳申], [丑戌未], Zi-Mao uncivilized, self-punishment
   - 六害: Six Harms (parasitic draining)
   - 六破: Six Destructions (undermining)

   TIER 15-19 (Covert):
   - 暗合: Hidden stem harmony (隐秘, constructive but weakest)

   Distance Semantics (紧贴 field):
   - Adjacent (月柱/日柱): Full-force interactions (正冲/正合/etc.)
   - Distant (年柱/时柱): Attenuated interactions (遥冲/遥合/etc.)
   - Applies to: 六冲, 六合, 六害, 六破, 天干克, 天干冲, 比和, all punishments

   Post-Calculation Modulation (apply_da_yun_master_priority):
   - Hierarchical strength scoring: 强势主流 → 显著影响 → 中等衰减 → 大幅衰减 → 消融吸收
   - Tier 0 (反吟/伏吟) absorbs or reduces lower-tier interactions
   - Tier 1 (三会/三合) suppresses interactions on same pillars
   - Tier 2 (六冲) shatters harmonies and amplifies conflicts
   - Tier 3 (六合) stabilizes and suppresses negative interactions
   - Stem interaction priority: 天干合 > 天干克

Key Functions:

    get_da_yun(lunar_birthday, gender):
        Calculates complete Big Luck Cycles analysis.
        Args:
            lunar_birthday (Lunar): Lunar calendar object
            gender (int): 0 for Female, 1 for Male
        Returns:
            dict: 10 × Big Luck Cycles with interactions, strengths, and interpretations

    _detect_da_yun_interactions(da_yun_stem, da_yun_branch, birth_chart):
        1×4 scan detecting all interaction types between Da Yun pillar and 4 natal pillars.
        Uses set-based validators for accuracy.
        Returns raw interactions (pre-modulation).

    apply_da_yun_master_priority(all_interactions, zhis):
        Post-calculation filtering and strength modulation.
        Applies hierarchical priority rules to assign 强度 scores.
        Sorts by DA_YUN_TIER_ORDER for consistent output.

Output Format:
    All dictionary keys and values use Chinese characters for consistency.
    Integrates lunar-python library data for accuracy and reliability.
    Each Da Yun cycle includes complete interaction details with:
    - 组合: interaction partners
    - 組合明細: detailed mapping
    - 状态: normalized status (正/遥)
    - 强度: strength level post-modulation
    - 备注: contextual interpretation
    - 紧贴: adjacency flag for distance semantics
"""

from lunar_python import Lunar
from lunar_python.util import LunarUtil
from lunar_python.EightChar import EightChar
from src.astronomer_calculations.wu_xing import (
    MingQiDynamicsCalculator,
    Pillar,
    Stem,
    Branch,
)
from src.astronomer_calculations.interactions_gan_zhi_zuo_yong import (
    clash_map,
    harm_map,
    six_he_map,
    triple_he,
    cardinal_branches,
    directional_he,
    directional_cardinal,
    break_map,
    hidden_stem_he,
    stem_combines,
    stem_clashes,
    stem_controls,
    get_status,
    is_valid_punishment,
    is_valid_peer_combination,
)

# Pillar names for reference
pillar_names = ["年柱", "月柱", "日柱", "时柱"]


# ============================================================================
# TEN GOD CATEGORIZATION & COMBINATION ANALYSIS
# ============================================================================


# Have removed the original _categorize_ten_god and _check_branch_rooting functions as they are no longer used in the current implementation for interactions. They can be reintroduced if we decide to add more detailed Ten God interpretations or rooting analysis in the future.
def _categorize_ten_god(ten_god: str) -> dict:
    """
    Categorize a Ten God (十神) into its type and provide templates for interpretation.

    Args:
        ten_god (str): The Ten God name (e.g., "正财", "七杀", "食神")

    Returns:
        dict: Category type and description templates for favorable/unfavorable scenarios
    """
    # Wealth Gods
    if ten_god in ["正财", "偏财"]:
        return {
            "category": "Wealth (财)",
            "type": "Wealth",
            "favorable": "财运亨通，婚姻美满（男性），物质丰沛，但需防贪心与执着",
            "unfavorable": "财运缠身如枷锁，婚姻困顿（男性），身体缺乏自由，易因钱财或感情身不由己",
        }
    # Officer/Authority Gods
    elif ten_god in ["正官", "七杀"]:
        return {
            "category": "Officer/Power (官)",
            "type": "Officer",
            "favorable": "官运亨通，名声卓著（女性婚运佳），受他人重视，事业突破，但需防权力带来的束缚",
            "unfavorable": "被权力困扰，被上司或伴侣压制（女性），身不由己，易因权力冲突或感情失控",
        }
    # Output Gods (Creativity)
    elif ten_god in ["食神", "伤官"]:
        return {
            "category": "Output/Creativity (食伤)",
            "type": "Output",
            "favorable": "才华绽放，名气提升，创意爆发，社交活跃，但需防过度消耗与心力疲惫",
            "unfavorable": "思维混乱，创意成灾，多说话惹祸，易因言语或创意陷入纠纷，精力过度消耗",
        }
    # Printing Gods (Knowledge/Foundation)
    elif ten_god in ["正印", "偏印"]:
        return {
            "category": "Printing/Knowledge (印)",
            "type": "Printing",
            "favorable": "智慧增长，学业进步，贵人庇护，心神安定，获得精神寄托",
            "unfavorable": "被印象困扰，思想固化，依赖他人，易陷沉思冥想，缺乏实际行动",
        }
    # Sister/Competitor Gods
    elif ten_god in ["比肩", "劫财"]:
        return {
            "category": "Peer/Competitor (比劫)",
            "type": "Peer",
            "favorable": "同伴聚合，朋友相助，团队合作，力量倍增，但需防权力争夺与利益冲突",
            "unfavorable": "竞争激烈，小人环绕，合伙生变，兄弟反目，易因权力或金钱失和",
        }
    else:
        return {
            "category": "Unknown",
            "type": "Unknown",
            "favorable": "该大运与日主产生关键作用，需深入分析八字喜忌",
            "unfavorable": "该大运与日主产生关键作用，需深入分析八字喜忌",
        }


def _check_branch_rooting(stem: str, branch: str) -> dict:
    """
    Check if an Earthly Branch properly supports (or opposes) a Heavenly Stem.
    "Rooting" means the branch contains compatible Five Element support.

    Args:
        stem (str): Heavenly Stem
        branch (str): Earthly Branch

    Returns:
        dict: Rooting strength ("tight"/"loose"/"neutral") and explanation
    """
    from lunar_python.util import LunarUtil

    stem_element = LunarUtil.WU_XING_GAN.get(stem, "Unknown")
    branch_element = LunarUtil.WU_XING_ZHI.get(branch, "Unknown")

    # Same element = tight rooting
    if stem_element == branch_element:
        return {
            "strength": "紧密",
            "rooting": f"{stem}(阳干){branch}(地支)同属{stem_element}，根基稳固",
            "interpretation": "绑定紧密，约束力强，影响深远",
        }

    # Generating relationship (stem feeds into branch's growth)
    generating_map = {
        "木": ["火", "水"],  # Wood feeds Fire, Water nourishes Wood
        "火": ["土", "木"],  # Fire feeds Earth, Wood feeds Fire
        "土": ["金", "火"],  # Earth feeds Metal, Fire feeds Earth
        "金": ["水", "土"],  # Metal feeds Water, Earth feeds Metal
        "水": ["木", "金"],  # Water feeds Wood, Metal feeds Water
    }

    if branch_element in generating_map.get(stem_element, []):
        return {
            "strength": "平衡",
            "rooting": f"{stem}({stem_element}阳干) creates cycle toward 地支{branch}({branch_element})，生克有情",
            "interpretation": "绑定平衡，既有约束也有助力",
        }

    # Opposing/clashing elements
    clashing_map = {
        "木": ["金"],  # Wood vs Metal
        "火": ["水"],  # Fire vs Water
        "土": ["木", "水"],  # Earth vs Wood/Water
        "金": ["木"],  # Metal vs Wood
        "水": ["火"],  # Water vs Fire
    }

    if branch_element in clashing_map.get(stem_element, []):
        return {
            "strength": "松散",
            "rooting": f"{stem}({stem_element}) ⚔ {branch}({branch_element})，元素冲突，根基松动",
            "interpretation": "绑定松散，约束力弱，易突破桎梏",
        }

    return {
        "strength": "中立",
        "rooting": "五行关系中立",
        "interpretation": "需结合完整八字判断",
    }


# ============================================================================
# DA YUN INTERACTIONS - 1x4 Scan with Tier-Based Priority
# ============================================================================

# Da Yun-specific tier ordering (extends shared INTERACTION_TIER_ORDER)
# 反吟/伏吟 are Tier 0-1 (pre-empt everything); 开库 is a specialized 六冲 variant.
DA_YUN_TIER_ORDER = {
    "反吟": 0,
    "伏吟": 1,
    "三会": 2,
    "三合": 3,
    "共拱": 4,  # Co-arching: strongest partial combination
    "比和": 5,  # Peer combination: adjacent same-element branches
    "拱会": 6,  # Two non-cardinal flanks arching
    "残会": 7,  # Cardinal + one flank, lopsided
    "半合": 7,  # Half harmony
    "六冲": 8,
    "开库": 8,  # Shares the clash tier — specialized clash
    "六合": 9,
    "天干合(日主)": 10,  # Day Master special case
    "天干克(日主)": 11,  # Day Master direct threat
    "天干合": 12,
    "天干克": 13,
    "天干冲": 14,  # Stem opposition
    "无恩之刑": 15,
    "恃势之刑": 15,
    "无礼之刑": 15,
    "自刑": 16,
    "六害": 17,
    "六破": 18,
    "暗合": 19,
}


def apply_da_yun_master_priority(
    all_interactions: list, zhis: list, cycle_name: str = "大运"
) -> list:
    """
    Post-calculation priority modulation for Da Yun interactions.

    Mirrors apply_bazi_master_priority() from interactions_gan_zhi_zuo_yong.py but
    adapted for 1×4 semantics: the Da Yun pillar is always the external side, so
    pillar-overlap logic operates only on natal pillar indices (0–3).

    The natal pillar index is parsed from the 组合 string (e.g. "大运-年柱" → index 0).

    Rules:
    1. 反吟 / 伏吟 — Tier 0: override everything on that natal pillar; lower-tier
       interactions on the same pillar are absorbed.  Exception: 三会/三合 are
       multi-pillar structural bonds — when one of their nodes is owned by 反吟/伏吟
       only that node is disrupted, so the combination is reduced to 中等衰减 rather
       than fully dissolved.
    2. 三会 / 三合 — Tier 1: structural field; suppresses all lower-tier interactions
       on the same natal pillars.  When the Da Yun branch is ITSELF part of a 三合
       with natal branches, a 六冲 on those same pillars gets 中等衰减 (tension
       between combining and clashing).
    3. 六冲 / 开库 — Tier 2: shatters 六合/半合 sharing a pillar; amplifies 六害/六破.
       EXCEPTION — natal three-way protection: if the targeted natal branch is part of
       a full natal 三合 or 三会 (all 3 members purely within the natal chart, Da Yun
       branch not involved), the triple structure resists the external clash and the
       六冲 is marked 大幅衰减 instead.  Example: 子 clashed by Da Yun 午, but natal
       chart has 申‑子‑辰 full triple → 申子辰 护体, 冲力大幅减弱.
       开库 with 钥匙受困=True is weakened by the pre-scan.
    4. 六合 — Tier 3: smooths over 六害/六破 on the same pillar.
    5. 天干合(日主) — absorbs 天干克(日主) on the Day Pillar (合 > 克 principle).
    6. All remaining interactions receive default 强度 based on tier.

    Args:
        all_interactions: Raw list of interaction dicts from the 1×4 scan
        zhis: Natal branch list [year, month, day, hour] (for context lookups)

    Returns:
        Modulated list with 强度 and 备注 fields added, sorted by tier.
    """
    # Pillar name → natal index mapping
    pillar_idx_map = {"年柱": 0, "月柱": 1, "日柱": 2, "时柱": 3}

    def _natal_pillar_index(item: dict):
        """Extract the natal pillar index from a 组合 string like '大运-年柱'."""
        combo = item.get("组合", "")
        for part in combo.split("-"):
            part = part.strip()
            if part in pillar_idx_map:
                return pillar_idx_map[part]
        return None

    # ── Scan phase: identify what structural types exist and which natal pillars they cover ──
    interaction_types = {item.get("类型") for item in all_interactions}

    has_tian_gan_he_ri_zhu = "天干合(日主)" in interaction_types

    # Natal pillar indices consumed by each structural tier
    fan_fu_pillars: set = set()
    fu_yin_pillars: set = set()
    san_hui_pillars: set = set()
    san_he_pillars: set = set()
    liu_chong_pillars: set = set()
    liu_he_pillars: set = set()
    partial_hui_pillars: set = set()  # 拱会/残会 natal pillar indices

    for item in all_interactions:
        itype = item.get("类型")
        idx = _natal_pillar_index(item)
        if idx is None:
            continue
        if itype == "反吟":
            fan_fu_pillars.add(idx)
        elif itype == "伏吟":
            fu_yin_pillars.add(idx)
        elif itype == "三会":
            # Multi-pillar: parse all natal indices from 组合明细 keys
            for k in item.get("组合明细", {}):
                if k in pillar_idx_map:
                    san_hui_pillars.add(pillar_idx_map[k])
        elif itype == "三合":
            for k in item.get("组合明细", {}):
                if k in pillar_idx_map:
                    san_he_pillars.add(pillar_idx_map[k])
        elif itype in ("六冲", "开库"):
            liu_chong_pillars.add(idx)
        elif itype == "六合":
            liu_he_pillars.add(idx)
        elif itype in ("拱会", "残会"):
            for k in item.get("组合明细", {}):
                if k in pillar_idx_map:
                    partial_hui_pillars.add(pillar_idx_map[k])

    # ── Purely natal three-way protection ──
    # Detect natal branches shielded by a full 三合 or 三会 formed entirely within
    # the natal chart (Da Yun branch not involved).  A branch inside such a complete
    # triple structure is harder to dislodge by an external 六冲.
    # pillar_idx → element/direction name, so the protection note is specific
    natal_san_he_pillars: dict[int, str] = {}
    natal_san_hui_pillars: dict[int, str] = {}

    for element, group in triple_he.items():
        involved = [(i, z) for i, z in enumerate(zhis) if z in group]
        if len(involved) == 3:  # Full natal 三合: all 3 members present in natal chart
            for idx_n, _ in involved:
                natal_san_he_pillars[idx_n] = element

    for direction, group in directional_he.items():
        involved = [(i, z) for i, z in enumerate(zhis) if z in group]
        if len(involved) == 3:  # Full natal 三会: all 3 members present in natal chart
            for idx_n, _ in involved:
                natal_san_hui_pillars[idx_n] = direction

    modulated = []
    for item in all_interactions:
        itype = item.get("类型")
        idx = _natal_pillar_index(item)

        # ── TIER 0: 反吟 / 伏吟 — consume the entire natal pillar ──
        if itype in ("反吟", "伏吟"):
            item["强度"] = "强势主流"
            if itype == "反吟":
                item.setdefault("备注", f"反吟：干支皆反，该柱位被{cycle_name}完全支配")
            else:  # 伏吟
                item.setdefault("备注", f"伏吟：干支皆同，该柱位被{cycle_name}完全占据")
            modulated.append(item)
            continue

        # Interactions on a pillar owned by 反吟 or 伏吟 — absorbed or reduced
        if idx is not None and idx in (fan_fu_pillars | fu_yin_pillars):
            if itype in ("三会", "三合"):
                # Multi-pillar bond: 反吟/伏吟 disrupts one node but cannot dissolve
                # the whole structural combination — suppress, not eliminate
                item["强度"] = "中等衰减"
                item["备注"] = "部分柱位被反吟/伏吟支配，三会/三合合力受阻但不消失"
            else:
                item["强度"] = "消融吸收"
                item["备注"] = "被反吟/伏吟完全吸收，独立作用消失"
            modulated.append(item)
            continue

        # ── TIER 1: 三会 / 三合 ──
        if itype == "三会":
            item["强度"] = "强势主流"
            item.setdefault("备注", "三会方位成局，主导全局")
            modulated.append(item)
            continue
        if itype == "三合":
            item["强度"] = "强势主流"
            item.setdefault("备注", "三合全局成形，合力主导运势")
            modulated.append(item)
            continue

        # ── TIER 1.5: 拱会 / 残会 — partial directional structures ──
        if itype == "拱会":
            item["强度"] = "显著影响"
            item.setdefault(
                "备注", f"拱会：命盘与{cycle_name}虚拟拱会，引力指向缺失方位"
            )
            modulated.append(item)
            continue
        if itype == "残会":
            item["强度"] = "显著影响"
            item.setdefault("备注", f"残会：命盘与{cycle_name}残会，方位带头但缺乏支撑")
            modulated.append(item)
            continue

        # Interactions on pillars dominated by 三会 or 三合
        if idx is not None and idx in (san_hui_pillars | san_he_pillars):
            if itype in ("六合", "半合"):
                item["强度"] = "大幅衰减"
                item["备注"] = "被三会/三合压制，合力弱化"
            elif itype in ("拱会", "残会"):
                item["强度"] = "大幅衰减"
                item["备注"] = "被三会/三合压制，拱/残会势力被吸收"
            elif itype in ("六冲", "开库"):
                item["强度"] = "中等衰减"
                item["备注"] = "与三会/三合结构形成张力，冲力被部分吸收"
            elif itype in ("六害", "六破", "无恩之刑", "恃势之刑", "无礼之刑", "自刑"):
                item["强度"] = "大幅衰减"
                item["备注"] = "被三会/三合压制，摩擦衰减"
            else:
                item.setdefault("强度", "显著影响")
            modulated.append(item)
            continue

        # ── TIER 2: 六冲 ──
        _direction_cn = {"Wood": "木", "Fire": "火", "Metal": "金", "Water": "水"}
        if itype == "六冲":
            if idx is not None and idx in natal_san_hui_pillars:
                direction = _direction_cn.get(
                    natal_san_hui_pillars[idx], natal_san_hui_pillars[idx]
                )
                item["强度"] = "大幅衰减"
                item["备注"] = f"命盘{direction}三会护体，大运冲力大幅衰减"
            elif idx is not None and idx in natal_san_he_pillars:
                element = natal_san_he_pillars[idx]
                item["强度"] = "大幅衰减"
                item["备注"] = f"命盘{element}三合护体，大运冲力大幅衰减"
            else:
                item["强度"] = "强势主流"
                item.setdefault("备注", f"六冲：{cycle_name}冲力完整激活，结构破位")
            modulated.append(item)
            continue

        # ── TIER 2 special: 开库 ──
        if itype == "开库":
            if item.get("钥匙受困"):
                item["强度"] = "大幅衰减"
                item["备注"] = (
                    f"开库受阻：{cycle_name}支被高优先级组合占用，库力释放大幅减弱"
                )
            else:
                item["强度"] = "强势主流"
                item.setdefault(
                    "备注", f"开库激活：{cycle_name}钥匙自由，库力释放完整激活"
                )
            modulated.append(item)
            continue

        # Interactions on pillars clashed by 六冲/开库
        if idx is not None and idx in liu_chong_pillars:
            if itype == "六合":
                item["强度"] = "消融吸收"
                item["备注"] = "被六冲摧毁，合力瓦解"
            elif itype in ("半合", "拱会", "残会"):
                item["强度"] = "大幅衰减"
                item["备注"] = "六冲冲散半合/拱会/残会势力"
            elif itype in ("六害", "六破"):
                item["强度"] = "显著影响"
                item["备注"] = "六冲加剧摩擦，冲害/冲破协同增强"
            elif itype in ("无恩之刑", "恃势之刑", "无礼之刑"):
                item["强度"] = "显著影响"
                item["备注"] = "六冲与刑力协同，压力增强"
            elif itype == "自刑":
                item["强度"] = "显著影响"
                item["备注"] = "冲力转化为外部冲突带来的内在自我怀疑"
            else:
                item.setdefault("强度", "显著影响")
            modulated.append(item)
            continue

        # ── TIER 3: 六合 ──
        if itype == "六合":
            item["强度"] = "强势主流"
            item.setdefault("备注", f"六合：{cycle_name}与命盘和谐共济，柱位稳定")
            modulated.append(item)
            continue

        # Interactions on pillars harmonised by 六合
        if idx is not None and idx in liu_he_pillars:
            if itype in ("六害", "六破"):
                item["强度"] = "消融吸收"
                item["备注"] = "被六合吸收，摩擦消融"
            elif itype in ("半合", "拱会", "残会"):
                item["强度"] = "中等衰减"
                item["备注"] = "被六合压制，半合/拱会/残会势力衰减"
            elif itype in ("无恩之刑", "恃势之刑", "无礼之刑", "自刑"):
                item["强度"] = "大幅衰减"
                item["备注"] = "被六合压制，刑力衰减"
            else:
                item.setdefault("强度", "显著影响")
            modulated.append(item)
            continue

        # ── BaZi principle: 天干合 > 天干克 on the Day Pillar ──
        if itype == "天干克(日主)" and has_tian_gan_he_ri_zhu:
            item["强度"] = "消融吸收"
            item["备注"] = "日主天干已被合化，克力被合化消融"
            modulated.append(item)
            continue

        # ── Default strength assignment for remaining interactions ──
        if itype in ("天干合(日主)", "天干合"):
            item["强度"] = "强势主流"
            item.setdefault("备注", "天干合化，绑定激活")
        elif itype == "天干克(日主)":
            item["强度"] = "强势主流"
            item.setdefault("备注", f"天干克(日主)：{cycle_name}直克日主，压力极大")
        elif itype == "天干克":
            item["强度"] = "显著影响"
            item.setdefault("备注", "天干克，柱位有冲突")
        elif itype == "半合":
            item["强度"] = "强势主流"
            item.setdefault("备注", "半合独立激活，部分合力")
        elif itype in ("拱会", "残会"):
            item["强度"] = "显著影响"
            item.setdefault("备注", "拱会/残会独立激活，虚拟方位出现")
        elif itype in ("无恩之刑", "恃势之刑", "无礼之刑", "自刑"):
            item["强度"] = "强势主流"
            item.setdefault("备注", "刑力独立激活")
        elif itype in ("六害", "六破"):
            item["强度"] = "显著影响"
            item.setdefault("备注", "摩擦独立作用")
        elif itype == "暗合":
            item["强度"] = "强势主流"
            item.setdefault("备注", "暗合隐秘作用")
        else:
            item.setdefault("强度", "强势主流")
            item.setdefault("备注", "独立激活")

        modulated.append(item)

    # Sort by interaction tier
    modulated.sort(key=lambda x: DA_YUN_TIER_ORDER.get(x.get("类型", ""), 99))
    return modulated


def _detect_global_triple_combinations(
    da_yun_branch: str, natal_branches: list
) -> dict:
    """
    PRE-SCAN: Detect if Da Yun branch forms San Hui or San He with natal branches.

    This must be called BEFORE the main 1x4 loop to determine if the Da Yun branch
    itself is globally bound by a beneficial combination. If bound, it lacks energy
    to open tombs (开库) or fully manifest other interactions.

    Args:
        da_yun_branch (str): Da Yun earthly branch
        natal_branches (list): List of 4 natal earth branches [year, month, day, hour]

    Returns:
        dict: {
            "is_bound": bool - whether Da Yun branch is part of a triple combination,
            "affected_indices": set - which natal pillars participate in the triple,
            "combination_type": str - "三会" or "三合" or None,
            "element": str - element of the combination (for 三合)
        }
    """
    # Check for San Hui (三会) - Directional combinations
    for direction, group in directional_he.items():
        if da_yun_branch in group:
            remaining_needed = [b for b in group if b != da_yun_branch]
            # Find which natal branches complete the triple
            participating_pillars = []
            for i, natal_branch in enumerate(natal_branches):
                if natal_branch in remaining_needed:
                    participating_pillars.append(i)

            # If we found all remaining branches needed, this is a valid San Hui
            if len(participating_pillars) == len(remaining_needed):
                return {
                    "is_bound": True,
                    "affected_indices": set(participating_pillars),
                    "combination_type": "三会",
                    "element": direction,
                }

    # Check for San He (三合) - Triple element combinations
    for element, group in triple_he.items():
        if da_yun_branch in group:
            remaining_needed = [b for b in group if b != da_yun_branch]
            # Find which natal branches complete the triple
            participating_pillars = []
            for i, natal_branch in enumerate(natal_branches):
                if natal_branch in remaining_needed:
                    participating_pillars.append(i)

            # If we found all remaining branches needed, this is a valid San He
            if len(participating_pillars) == len(remaining_needed):
                return {
                    "is_bound": True,
                    "affected_indices": set(participating_pillars),
                    "combination_type": "三合",
                    "element": element,
                }

    # No global triple combination found
    return {
        "is_bound": False,
        "affected_indices": set(),
        "combination_type": None,
        "element": None,
    }


def _detect_da_yun_interactions(
    da_yun_stem: str, da_yun_branch: str, birth_chart: dict, pillar_prefix: str = "大运"
) -> dict:
    """
    Detect Da Yun interactions with the birth chart using a 1x4 scan.

    The Da Yun pillar acts as an External Trigger entering the birth chart.
    All interactions are accumulated without manual locking, then passed through
    apply_da_yun_master_priority() for hierarchical strength modulation.

    Output schema mirrors interactions_gan_zhi_zuo_yong.py:
        {类型, 组合, 组合明细, 状态, 强度, 备注, ...}
    where 组合 uses pillar_prefix-combined with pillar names (e.g., "大运-年柱", "小运-月柱").

    Da Yun-unique interaction types (handled before shared logic):
    - 反吟: Da Yun stem AND branch both clash the same natal pillar → extreme instability
    - 伏吟: Da Yun pillar exactly matches a natal pillar → stagnation / groaning decade
    - 开库: Earth branch clash (辰↔戌 or 丑↔未) releasing hidden stems (Key vs Lock)
    - 天干合(日主) / 天干克(日主): stem hit on the Day Master pillar → elevated severity

    Args:
        da_yun_stem (str): Da Yun heavenly stem
        da_yun_branch (str): Da Yun earthly branch
        birth_chart (dict): Birth chart with keys "year", "month", "day", "hour"
                            each containing "stem" and "branch" strings
        pillar_prefix (str): Prefix for pillar combination strings (default "大运", can be "小运")

    Returns:
        dict: {"作用": [list of modulated interaction dicts]}
    """
    if not da_yun_stem or not da_yun_branch:
        return {"作用": []}

    # Create cycle_name variable for context messages (used in 备注 fields)
    cycle_name = pillar_prefix

    # Extract birth chart data
    day_stem = birth_chart["day"]["stem"]  # Day Master (日主) - reference for Ten Gods
    gans = [
        birth_chart["year"]["stem"],
        birth_chart["month"]["stem"],
        birth_chart["day"]["stem"],
        birth_chart["hour"]["stem"],
    ]
    zhis = [
        birth_chart["year"]["branch"],
        birth_chart["month"]["branch"],
        birth_chart["day"]["branch"],
        birth_chart["hour"]["branch"],
    ]

    all_interactions = []  # Accumulate raw; priority modulation applied afterwards

    # === PRE-SCAN: Is Da Yun branch globally bound by 三会 or 三合? ===
    # This feeds into 开库 Key vs Lock logic.
    global_binding_info = _detect_global_triple_combinations(da_yun_branch, zhis)
    da_yun_branch_bound = global_binding_info["is_bound"]

    # Report the global triple combination itself (once, tagged as global)
    if da_yun_branch_bound:
        combination_type = global_binding_info.get("combination_type")
        element = global_binding_info.get("element", "")
        direction_cn_map = {"Wood": "木", "Fire": "火", "Metal": "金", "Water": "水"}

        if combination_type == "三会":
            direction_cn = direction_cn_map.get(element, element)
            participating = sorted(global_binding_info["affected_indices"])
            combo_pillars = "-".join(
                [pillar_prefix] + [pillar_names[k] for k in participating]
            )
            combo_detail = {pillar_names[k]: zhis[k] for k in participating}
            combo_detail[pillar_prefix] = da_yun_branch
            all_interactions.append(
                {
                    "类型": "三会",
                    "组合": combo_pillars,
                    "组合明细": combo_detail,
                    "状态": get_status("三会", {"key": "full"}),
                    "元素": direction_cn,
                }
            )
        elif combination_type == "三合":
            participating = sorted(global_binding_info["affected_indices"])
            combo_pillars = "-".join(
                [pillar_prefix] + [pillar_names[k] for k in participating]
            )
            combo_detail = {pillar_names[k]: zhis[k] for k in participating}
            combo_detail[pillar_prefix] = da_yun_branch
            all_interactions.append(
                {
                    "类型": "三合",
                    "组合": combo_pillars,
                    "组合明细": combo_detail,
                    "状态": get_status("三合", {"key": "full"}),
                    "元素": element,
                }
            )

    # === PRE-SCAN: Partial 三会 — 拱会 / 残会 ===
    # When the Da Yun branch contributes to a PARTIAL directional frame (exactly one natal
    # branch from the same 三会 group), we detect the subtype:
    #   拱会 — Da Yun + one natal flank, BOTH non-cardinal → virtual pull toward missing cardinal
    #   残会 — Da Yun is/pairs with the cardinal → king-present but one support missing
    # These are NOT marked as bound (da_yun_branch_bound stays False here), so 开库 logic
    # is unaffected.  They are Tier 1.5 structural signals below full 三会/三合.
    if not da_yun_branch_bound:
        direction_cn_map = {"Wood": "木", "Fire": "火", "Metal": "金", "Water": "水"}
        for direction, group in directional_he.items():
            if da_yun_branch in group:
                # Collect natal branches that belong to this directional group
                natal_matches = [(i, zhis[i]) for i in range(4) if zhis[i] in group]
                if len(natal_matches) == 1:
                    natal_idx, natal_branch = natal_matches[0]
                    cardinal = directional_cardinal.get(direction)
                    cardinal_present = (da_yun_branch == cardinal) or (
                        natal_branch == cardinal
                    )
                    itype_partial = "残会" if cardinal_present else "拱会"
                    missing_branch = next(
                        (b for b in group if b != da_yun_branch and b != natal_branch),
                        None,
                    )
                    direction_cn = direction_cn_map.get(direction, direction)
                    combo_pillars = f"{pillar_prefix}-{pillar_names[natal_idx]}"
                    combo_detail_partial = {
                        pillar_names[natal_idx]: natal_branch,
                        pillar_prefix: da_yun_branch,
                    }
                    entry = {
                        "类型": itype_partial,
                        "方位": direction,
                        "元素": direction_cn,
                        "组合": combo_pillars,
                        "组合明细": combo_detail_partial,
                        "待会": missing_branch or "无",
                        "状态": get_status(
                            "三会",
                            {"key": "residual" if cardinal_present else "arch"},
                        ),
                    }
                    if not cardinal_present:
                        entry["犹出"] = missing_branch or "无"
                    all_interactions.append(entry)

    # === 1x4 SCAN: Da Yun pillar vs each natal pillar ===
    for i in range(4):
        target_gan = gans[i]
        target_zhi = zhis[i]
        pillar = pillar_names[i]
        combo = f"{pillar_prefix}-{pillar}"
        combo_detail = {f"{pillar_prefix}支": da_yun_branch, pillar: target_zhi}
        combo_detail_stem = {f"{pillar_prefix}干": da_yun_stem, pillar: target_gan}

        # Distance semantics: Da Yun energy flows directly through 月柱 (i=1) and 日柱 (i=2)
        # (its structural origin and the Day Master).  年柱 and 时柱 receive attenuated signal.
        # is_adjacent=True  → 正X (immediate, full-force)
        # is_adjacent=False → 遥X (mediated, reduced intensity)
        is_adjacent = i in (1, 2)

        # ── TIER 0A: 反吟 (Fan Fu) - Branch clash + Stem clash on same natal pillar ──
        if (
            clash_map.get(da_yun_branch) == target_zhi
            and stem_clashes.get(da_yun_stem) == target_gan
        ):
            all_interactions.append(
                {
                    "类型": "反吟",
                    "组合": combo,
                    "组合明细": {
                        f"{pillar_prefix}干": da_yun_stem,
                        f"{pillar_prefix}支": da_yun_branch,
                        pillar: f"{target_gan}{target_zhi}",
                    },
                    "状态": "干支皆反",
                    "日柱特殊": i == 2,
                }
            )
            # No continue — lower-tier branch/stem interactions are recorded below
            # and absorbed by apply_da_yun_master_priority (六冲, 天干克 become 消融吸收).

        # ── TIER 0B: 伏吟 (Fu Yin) - Da Yun pillar exactly matches natal pillar ──
        if da_yun_stem == target_gan and da_yun_branch == target_zhi:
            all_interactions.append(
                {
                    "类型": "伏吟",
                    "组合": combo,
                    "组合明细": {
                        f"{pillar_prefix}干": da_yun_stem,
                        f"{pillar_prefix}支": da_yun_branch,
                        pillar: f"{target_gan}{target_zhi}",
                    },
                    "状态": "干支皆同",
                    "日柱特殊": i == 2,
                }
            )
            # No continue — lower-tier interactions are recorded below and absorbed by
            # apply_da_yun_master_priority.  When da_yun_branch == target_zhi (伏吟),
            # guards below prevent spurious self-matches (半合, triple-刑); 自刑 is
            # intentionally kept (e.g. 辰+辰 on 伏吟 is a valid feedback-loop signal).

        # ── Branch Interactions ──

        # 六合
        if six_he_map.get(da_yun_branch) == target_zhi:
            all_interactions.append(
                {
                    "类型": "六合",
                    "组合": combo,
                    "组合明细": combo_detail,
                    "紧贴": is_adjacent,
                    "状态": get_status(
                        "六合", {"key": "adjacent" if is_adjacent else "distant"}
                    ),
                }
            )

        # 六冲 — with 开库 special case for Earth-branch pairs
        if clash_map.get(da_yun_branch) == target_zhi:
            earth_tomb_pairs = {"辰": "戌", "戌": "辰", "丑": "未", "未": "丑"}
            if target_zhi in earth_tomb_pairs:
                # 开库: Key (Da Yun branch) vs Lock (natal tomb branch)
                hidden_stems = LunarUtil.ZHI_HIDE_GAN.get(target_zhi, [])
                hidden_ten_gods = [
                    _get_shi_shen_for_stem_pair(day_stem, s) for s in hidden_stems
                ]
                all_interactions.append(
                    {
                        "类型": "开库",
                        "组合": combo,
                        "组合明细": combo_detail,
                        "紧贴": is_adjacent,
                        "状态": (
                            f"钥匙受困：{cycle_name}库力受阻"
                            if da_yun_branch_bound
                            else "开库冲出，库藏释放"
                        ),
                        "钥匙受困": da_yun_branch_bound,
                        "释放天干": (
                            "、".join(hidden_stems)
                            if not da_yun_branch_bound
                            else "(被组合所占用，释放力减弱)"
                        ),
                        "释放十神": (
                            "、".join(hidden_ten_gods)
                            if not da_yun_branch_bound
                            else "(被组合所占用，释放力减弱)"
                        ),
                    }
                )
            else:
                all_interactions.append(
                    {
                        "类型": "六冲",
                        "组合": combo,
                        "组合明细": combo_detail,
                        "紧贴": is_adjacent,
                        "状态": get_status(
                            "六冲", {"key": "adjacent" if is_adjacent else "distant"}
                        ),
                    }
                )

        # 半合 — guard: skip when da_yun_branch == target_zhi (spurious self-match on 伏吟)
        for element, group in triple_he.items():
            if (
                da_yun_branch != target_zhi
                and da_yun_branch in group
                and target_zhi in group
            ):
                cardinal = cardinal_branches.get(element)
                branches_with_da_yun = zhis + [da_yun_branch]
                if cardinal in branches_with_da_yun:
                    state = "strong"
                elif da_yun_branch != cardinal and target_zhi != cardinal:
                    state = "arching"
                else:
                    state = "weak"
                all_interactions.append(
                    {
                        "类型": "半合",
                        "元素": element,
                        "组合": combo,
                        "组合明细": combo_detail,
                        "状态": get_status(
                            "半合", {"element": element, "state": state}
                        ),
                        "邀出": cardinal if state == "arching" else "无",
                        "紧贴": is_adjacent,
                    }
                )
                break

        # 六害
        if harm_map.get(da_yun_branch) == target_zhi:
            all_interactions.append(
                {
                    "类型": "六害",
                    "组合": combo,
                    "组合明细": combo_detail,
                    "紧贴": is_adjacent,
                    "状态": get_status(
                        "六害", {"key": "adjacent" if is_adjacent else "distant"}
                    ),
                }
            )

        # 六破
        if break_map.get(da_yun_branch) == target_zhi:
            all_interactions.append(
                {
                    "类型": "六破",
                    "组合": combo,
                    "组合明细": combo_detail,
                    "紧贴": is_adjacent,
                    "状态": get_status(
                        "六破", {"key": "adjacent" if is_adjacent else "distant"}
                    ),
                }
            )

        # ── PUNISHMENTS (三刑) ──
        # Use set-based validator to detect all punishment types
        # (ungrateful, bullying, rude, self). Skips self-matches on 伏吟 pillars.
        if da_yun_branch != target_zhi:
            punishment_result = is_valid_punishment(
                da_yun_branch, target_zhi, natal_branches=zhis
            )

            if punishment_result:
                punishment_type = punishment_result["type"]
                is_full = punishment_result["is_full"]

                # Map punishment type to internal codes for get_status()
                if punishment_type == "无恩之刑":
                    punishment_code = "ungrateful"
                elif punishment_type == "恃势之刑":
                    punishment_code = "bullying"
                elif punishment_type == "无礼之刑":
                    punishment_code = "uncivilized"
                elif punishment_type == "自刑":
                    punishment_code = "self"
                else:
                    punishment_code = "unknown"

                all_interactions.append(
                    {
                        "类型": punishment_type,
                        "组合": combo,
                        "组合明细": combo_detail,
                        "紧贴": is_adjacent,
                        "状态": get_status(
                            "三刑",
                            {
                                "punishment_type": punishment_code,
                                "is_full": is_full,
                                "is_adjacent": is_adjacent,
                            },
                        ),
                    }
                )

        # 暗合
        if hidden_stem_he.get(da_yun_branch) == target_zhi:
            all_interactions.append(
                {
                    "类型": "暗合",
                    "组合": combo,
                    "组合明细": combo_detail,
                    "状态": get_status("暗合"),
                }
            )

        # ── TIER 2: 比和 (Peer Combinations) ──
        # Adjacent branches of the same element: supportive but not binding
        peer_result = is_valid_peer_combination(da_yun_branch, target_zhi)
        if peer_result:
            all_interactions.append(
                {
                    "类型": "比和",
                    "组合": combo,
                    "组合明细": combo_detail,
                    "元素": peer_result["element"],
                    "紧贴": is_adjacent,
                    "状态": get_status(
                        "比和",
                        {"key": "adjacent" if is_adjacent else "distant"},
                    ),
                }
            )

        # ── Stem Interactions ──

        # 天干合 — special case when combining with Day Master
        if stem_combines.get(da_yun_stem) == target_gan:
            rooting_info = _check_branch_rooting(da_yun_stem, da_yun_branch)
            all_interactions.append(
                {
                    "类型": "天干合(日主)" if i == 2 else "天干合",
                    "组合": f"{pillar_prefix}-{pillar}",
                    "组合明细": combo_detail_stem,
                    "状态": get_status("天干合"),
                    "日柱特殊": i == 2,
                    "根基强度": rooting_info["strength"],
                    "根基说明": rooting_info["interpretation"],
                }
            )

        # 天干克 — special case when clashing Day Master
        if stem_clashes.get(da_yun_stem) == target_gan:
            rooting_info = _check_branch_rooting(da_yun_stem, da_yun_branch)
            all_interactions.append(
                {
                    "类型": "天干克(日主)" if i == 2 else "天干克",
                    "组合": f"{pillar_prefix}-{pillar}",
                    "组合明细": combo_detail_stem,
                    "状态": get_status(
                        "天干克", {"key": "adjacent" if is_adjacent else "distant"}
                    ),
                    "日柱特殊": i == 2,
                    "根基强度": rooting_info["strength"],
                    "根基说明": rooting_info["interpretation"],
                }
            )

        # 天干冲 — Heavenly Stem Opposition
        if (da_yun_stem, target_gan) in stem_controls or (
            target_gan,
            da_yun_stem,
        ) in stem_controls:
            rooting_info = _check_branch_rooting(da_yun_stem, da_yun_branch)
            all_interactions.append(
                {
                    "类型": "天干冲",
                    "组合": f"{pillar_prefix}-{pillar}",
                    "组合明细": combo_detail_stem,
                    "状态": get_status(
                        "天干冲", {"key": "adjacent" if is_adjacent else "distant"}
                    ),
                    "根基强度": rooting_info["strength"],
                    "根基说明": rooting_info["interpretation"],
                }
            )

    # Apply Da Yun-specific priority modulation (replaces manual lock system)
    modulated = apply_da_yun_master_priority(all_interactions, zhis, cycle_name)
    return {"作用": modulated}


# ============================================================================
# FIVE ELEMENTS (五行) - Stem and Branch Element Analysis
# ============================================================================


def _get_stem_wu_xing(stem: str) -> dict:
    """
    Get Five Element (五行) info for a Heavenly Stem (天干).

    Uses lunar_python library data which maps stems to elements.
    Polarity (阳/阴) is derived from the stem's index position:
    - Odd indices (甲丙戊庚壬) = 阳 (Yang)
    - Even indices (乙丁己辛癸) = 阴 (Yin)

    Args:
        stem (str): Heavenly Stem (e.g., "甲", "乙", etc.)

    Returns:
        dict: {"五行": "木/火/土/金/水", "阴阳": "阳/阴"}
    """
    element = LunarUtil.WU_XING_GAN.get(stem, "Unknown")

    if element == "Unknown":
        return {"五行": "Unknown", "阴阳": "Unknown"}

    # Find index to determine polarity (odd=Yang, even=Yin)
    try:
        index = LunarUtil.GAN.index(stem)
        polarity = "阳" if index % 2 == 1 else "阴"
    except ValueError:
        polarity = "Unknown"

    return {"五行": element, "阴阳": polarity}


def _get_branch_wu_xing(branch: str) -> dict:
    """
    Get Five Element (五行) info for an Earthly Branch (地支).

    Uses lunar_python library data which maps branches to elements.
    Polarity (阳/阴) is derived from the branch's index position:
    - Odd indices (子寅辰午申戌) = 阳 (Yang)
    - Even indices (丑卯巳未酉亥) = 阴 (Yin)

    Args:
        branch (str): Earthly Branch (e.g., "子", "丑", etc.)

    Returns:
        dict: {"五行": "木/火/土/金/水", "阴阳": "阳/阴"}
    """
    element = LunarUtil.WU_XING_ZHI.get(branch, "Unknown")

    if element == "Unknown":
        return {"五行": "Unknown", "阴阳": "Unknown"}

    # Find index to determine polarity (odd=Yang, even=Yin)
    try:
        index = LunarUtil.ZHI.index(branch)
        polarity = "阳" if index % 2 == 1 else "阴"
    except ValueError:
        polarity = "Unknown"

    return {"五行": element, "阴阳": polarity}


# ============================================================================
# NAYIN SYSTEM (纳音) - 60 Stem-Branch Nayin Element Mapping
# ============================================================================

# Uses LunarUtil.NAYIN from lunar-python for complete nayin descriptive names
# (纳音) represents the harmonic resonance element associated with each sexagenary pair
# Examples: "海中金" (Gold in the Sea), "炉中火" (Fire in the Furnace), etc.


def _get_nayin(stem: str, branch: str) -> str:
    """
    Get Nayin Element (纳音) for a Stem-Branch pair.

    Nayin (纳音) represents the harmonic resonance element associated with each
    of the 60 sexagenary stem-branch combinations. It's a classical BaZi concept
    from the lunar-python library's LunarUtil.NAYIN mapping.

    Args:
        stem (str): Heavenly Stem (e.g., "甲", "乙", etc.)
        branch (str): Earthly Branch (e.g., "子", "丑", etc.)

    Returns:
        str: Nayin descriptive name (e.g., "海中金", "炉中火") or "Unknown"
    """
    gan_zhi = stem + branch
    return LunarUtil.NAYIN.get(gan_zhi, "Unknown")


# ============================================================================
# LIFE STAGE TABLE (地势) - Chang Sheng 12 Stages
# ============================================================================

# Complete mapping table for 12 Life Stages (十二运星)
# (CHANG_SHENG imported from EightChar library)
# Maps (Day Master Stem, Da Yun Branch) -> Life Stage
# Stages: 长生,沐浴,冠带,临官,帝旺,衰,病,死,墓,绝,胎,养
DI_SHI_TABLE = {
    # Yang Stems (clockwise progression)
    "甲": {
        "亥": "长生",
        "子": "沐浴",
        "丑": "冠带",
        "寅": "临官",
        "卯": "帝旺",
        "辰": "衰",
        "巳": "病",
        "午": "死",
        "未": "墓",
        "申": "绝",
        "酉": "胎",
        "戌": "养",
    },
    "丙": {
        "寅": "长生",
        "卯": "沐浴",
        "辰": "冠带",
        "巳": "临官",
        "午": "帝旺",
        "未": "衰",
        "申": "病",
        "酉": "死",
        "戌": "墓",
        "亥": "绝",
        "子": "胎",
        "丑": "养",
    },
    "戊": {
        "寅": "长生",
        "卯": "沐浴",
        "辰": "冠带",
        "巳": "临官",
        "午": "帝旺",
        "未": "衰",
        "申": "病",
        "酉": "死",
        "戌": "墓",
        "亥": "绝",
        "子": "胎",
        "丑": "养",
    },
    "庚": {
        "巳": "长生",
        "午": "沐浴",
        "未": "冠带",
        "申": "临官",
        "酉": "帝旺",
        "戌": "衰",
        "亥": "病",
        "子": "死",
        "丑": "墓",
        "寅": "绝",
        "卯": "胎",
        "辰": "养",
    },
    "壬": {
        "申": "长生",
        "酉": "沐浴",
        "戌": "冠带",
        "亥": "临官",
        "子": "帝旺",
        "丑": "衰",
        "寅": "病",
        "卯": "死",
        "辰": "墓",
        "巳": "绝",
        "午": "胎",
        "未": "养",
    },
    # Yin Stems (counter-clockwise progression)
    "乙": {
        "午": "长生",
        "巳": "沐浴",
        "辰": "冠带",
        "卯": "临官",
        "寅": "帝旺",
        "丑": "衰",
        "子": "病",
        "亥": "死",
        "戌": "墓",
        "酉": "绝",
        "申": "胎",
        "未": "养",
    },
    "丁": {
        "酉": "长生",
        "申": "沐浴",
        "未": "冠带",
        "午": "临官",
        "巳": "帝旺",
        "辰": "衰",
        "卯": "病",
        "寅": "死",
        "丑": "墓",
        "子": "绝",
        "亥": "胎",
        "戌": "养",
    },
    "己": {
        "酉": "长生",
        "申": "沐浴",
        "未": "冠带",
        "午": "临官",
        "巳": "帝旺",
        "辰": "衰",
        "卯": "病",
        "寅": "死",
        "丑": "墓",
        "子": "绝",
        "亥": "胎",
        "戌": "养",
    },
    "辛": {
        "子": "长生",
        "亥": "沐浴",
        "戌": "冠带",
        "酉": "临官",
        "申": "帝旺",
        "未": "衰",
        "午": "病",
        "巳": "死",
        "辰": "墓",
        "卯": "绝",
        "寅": "胎",
        "丑": "养",
    },
    "癸": {
        "卯": "长生",
        "寅": "沐浴",
        "丑": "冠带",
        "子": "临官",
        "亥": "帝旺",
        "戌": "衰",
        "酉": "病",
        "申": "死",
        "未": "墓",
        "午": "绝",
        "巳": "胎",
        "辰": "养",
    },
}


# ============================================================================
# TEN GODS (十神) - Relational Categories and Hidden Stem Analysis
# ============================================================================


def _get_shi_shen_for_stem_pair(day_stem: str, target_stem: str) -> str:
    """
    Calculate Ten God (十神) for a Stem pair (Day Stem vs Target Stem).

    Args:
        day_stem (str): Day Stem (日干) - the reference point
        target_stem (str): Target Stem to compare against

    Returns:
        str: The Ten God name (e.g., "正财", "七杀")
    """
    stem_pair = day_stem + target_stem
    return LunarUtil.SHI_SHEN.get(stem_pair, "Unknown")


def _get_hidden_stems_shi_shen(day_stem: str, branch: str) -> dict:
    """
    Calculate Ten Gods for all hidden stems in an Earthly Branch.

    Args:
        day_stem (str): Day Stem (日干) - the reference point
        branch (str): Earthly Branch (地支)

    Returns:
        dict: Organized hidden stem Ten Gods with detailed structure
        {
            "本气": {
                "天干": "甲",      # Main Qi Stem
                "十神": "七杀"     # Main Qi Ten God
            },
            "中气": {...},  # Middle Qi (if exists)
            "余气": {...}   # Residual Qi (if exists)
        }
    """
    hidden_stems = LunarUtil.ZHI_HIDE_GAN.get(branch, [])
    labels = ["本气", "中气", "余气"]
    result = {}

    for i, stem in enumerate(hidden_stems):
        if i < len(labels):
            shi_shen = _get_shi_shen_for_stem_pair(day_stem, stem)
            result[labels[i]] = {"天干": stem, "十神": shi_shen}

    return result


# ============================================================================
# LIFE STAGE CALCULATION (地势) - Based on Day Master Stem
# ============================================================================


def _get_di_shi(day_stem: str, da_yun_branch: str) -> str:
    """
    Calculate 地势 (Life Stage from Chang Sheng 12 system) for a Da Yun.

    Uses a complete lookup table based on the Day Master Stem and Da Yun Branch.
    The path differs for Yang Stems (clockwise) vs Yin Stems (counter-clockwise).

    The 12 Life Stages represent a complete life cycle:
    长生(Birth) → 沐浴 → 冠带 → 临官 → 帝旺(Peak) → 衰(Decline) → 病 → 死 →
    墓(Storage) → 绝(Low Point) → 胎 → 养(Nourishing)

    Args:
        day_stem (str): Day Stem (日干) from birth chart - the reference point
        da_yun_branch (str): Earthly Branch (地支) of the Da Yun cycle

    Returns:
        str: The life stage name (e.g., "长生", "帝旺", "衰", etc.)
    """
    if day_stem not in DI_SHI_TABLE:
        return "Unknown"

    stem_table = DI_SHI_TABLE[day_stem]
    return stem_table.get(da_yun_branch, "Unknown")


# Helper dictionaries for string-to-Enum conversion
STR_STEM = {s.value: s for s in Stem}
STR_BRANCH = {b.value: b for b in Branch}


# ============================================================================
# MAIN DA YUN CALCULATION
# ============================================================================


def get_da_yun(lunar_birthday: Lunar, gender: int) -> dict:
    """
    Calculate Big Luck Cycles (Da Yun) from lunar birthday and gender.

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male

    Returns:
        dict: Structured JSON with Da Yun cycles and timing information
    """
    # Get the EightChar (八字) object
    bazi = lunar_birthday.getEightChar()

    # Get the Day Stem (日干) - this is the reference for all Ten Gods calculations
    day_stem = bazi.getDayGan()

    # Extract birth chart pillars for interaction detection
    birth_chart = {
        "year": {
            "stem": bazi.getYearGan(),
            "branch": bazi.getYearZhi(),
        },
        "month": {
            "stem": bazi.getMonthGan(),
            "branch": bazi.getMonthZhi(),
        },
        "day": {
            "stem": bazi.getDayGan(),
            "branch": bazi.getDayZhi(),
        },
        "hour": {
            "stem": bazi.getTimeGan(),
            "branch": bazi.getTimeZhi(),
        },
    }

    # Calculate 起运 (start of luck cycle) based on gender
    yun = bazi.getYun(gender)

    # Get the solar date when 起运 begins
    qi_yun_date = yun.getStartSolar()

    # Get all 大运 (Big Luck Cycles) - default 10 cycles
    da_yun_list = yun.getDaYun()

    # Process each 大运 into structured format
    da_yun_data = []
    for i, da_yun in enumerate(da_yun_list):
        gan_zhi = da_yun.getGanZhi()

        # Extract Gan (stem) and Zhi (branch) for Ten Gods analysis
        # Gan-Zhi format is like "戊子", "己丑", etc.
        da_yun_stem = gan_zhi[0] if len(gan_zhi) > 0 else ""
        da_yun_branch = gan_zhi[1] if len(gan_zhi) > 1 else ""

        # Calculate Ten Gods for this 大运
        if i > 0:  # Skip first cycle (no Gan-Zhi)
            # Stem Ten God (天干十神) - the primary life theme
            stem_shi_shen = _get_shi_shen_for_stem_pair(day_stem, da_yun_stem)

            # Branch Ten Gods (地支十神) - hidden themes from hidden stems
            branch_shi_shen = _get_hidden_stems_shi_shen(day_stem, da_yun_branch)

            # Life Stage (地势) for the Da Yun branch using birth day stem as reference
            di_shi = _get_di_shi(day_stem, da_yun_branch)

            # Five Elements (五行) for Stem and Branch
            stem_wu_xing = _get_stem_wu_xing(da_yun_stem)
            branch_wu_xing = _get_branch_wu_xing(da_yun_branch)

            # Nayin (纳音) for the Da Yun stem-branch pair
            nayin = _get_nayin(da_yun_stem, da_yun_branch)

            # Detect interactions (作用) with birth chart using sophisticated 1x4 scan
            interactions_result = _detect_da_yun_interactions(
                da_yun_stem, da_yun_branch, birth_chart
            )
            interactions = interactions_result.get("作用", [])
        else:
            stem_shi_shen = "未行大运"
            branch_shi_shen = "未行大运"
            di_shi = "未行大运"
            stem_wu_xing = {"五行": "未行大运", "阴阳": "未行大运"}
            branch_wu_xing = {"五行": "未行大运", "阴阳": "未行大运"}
            nayin = "未行大运"
            interactions = "未行大运"

        da_yun_info = {
            "序号": (
                "未行大运" if i == 0 else i
            ),  # Index/sequence number (0 = before start)
            "开始年份": da_yun.getStartYear(),  # Start calendar year
            "结束年份": da_yun.getEndYear(),  # End calendar year
            "开始年龄": da_yun.getStartAge(),  # Start age (from birth)
            "结束年龄": da_yun.getEndAge(),  # End age (from birth)
            "周期": f"{da_yun.getStartAge()}-{da_yun.getEndAge()}岁",  # Age range display
            "干支": gan_zhi if i > 0 else "未行大运",  # Gan-Zhi (empty for first cycle)
            "旬": da_yun.getXun() if i > 0 else "未行大运",  # Xun (10-day cycle)
            "旬空": (
                da_yun.getXunKong() if i > 0 else "未行大运"
            ),  # Xun Kong (void periods)
            "五行": {
                "干": stem_wu_xing,  # Stem Five Element and Polarity
                "支": branch_wu_xing,  # Branch Five Element and Polarity
            },
            "纳音": nayin,  # Nayin element (harmonic resonance)
            "地势": di_shi,  # Life Stage (长生十二神)
            "十神": {
                "主题": (
                    stem_shi_shen if i > 0 else "未行大运"
                ),  # Primary life theme (Stem Ten God)
                "天干十神": (
                    stem_shi_shen if i > 0 else "未行大运"
                ),  # Stem Ten God (for clarity)
                "地支十神": (
                    branch_shi_shen if i > 0 else "未行大运"
                ),  # Hidden themes (Main/Middle/Residual)
            },
            "作用": interactions,  # Branch and Stem interactions with birth chart
        }
        da_yun_data.append(da_yun_info)

    # Compile the complete da_yun structure
    return {
        "大运": {
            "起运": {
                "性别": "男" if gender == 1 else "女",
                "出生阳历": lunar_birthday.getSolar().toYmdHms(),
                "出生农历": f"{lunar_birthday.getYear()}-{lunar_birthday.getMonth():02d}-{lunar_birthday.getDay():02d} {lunar_birthday.getHour():02d}:{lunar_birthday.getMinute():02d}:{lunar_birthday.getSecond():02d}",
                "起运时间": qi_yun_date.toYmdHms(),
                "起运前时间": f"{yun.getStartYear()}年{yun.getStartMonth()}月{yun.getStartDay()}天{yun.getStartHour()}小时",
                "顺逆": "顺推" if yun.isForward() else "逆推",
            },
            "大运周期": da_yun_data,
        }
    }


# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    import json
    from datetime import datetime
    from lunar_python import Solar
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
    from src.astronomer_calculations.bazi_pillars import get_bazi_pillars

    # python -m src.astronomer_calculations.da_yun

    # Desmond's birthday example - Female test
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)
    tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)

    # Corinne's birthday example
    # solar_birthday = Solar.fromYmdHms(
    #     1987, 6, 3, 12, 6, 0
    # )  # Create solar date June 3, 1987 at 12:06 PM
    # tst_birthday, inputs_report = get_true_solar_time(
    #     datetime(1987, 6, 3, 12, 6, 0), 1.4759, 103.808053
    # )
    lunar_birthday = tst_birthday.getLunar()

    bazi_json = get_bazi_pillars(tst_birthday.getLunar())
    print(f"八字: {bazi_json}")

    # print("=== Female (Gender=0) ===")
    # result = get_da_yun(lunar_birthday, gender=0)
    # print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n=== Male (Gender=1) ===")
    result = get_da_yun(lunar_birthday, gender=1)
    print(json.dumps(result, ensure_ascii=False, indent=2))
