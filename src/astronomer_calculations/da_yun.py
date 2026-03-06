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

8. 作用 (Interactions - Event Triggers):
   - Branch interactions: 冲(clash), 害(harm), 合(combine), 刑(punishment)
   - Stem interactions: 冲(clash), 合(combine)
   - Triple Punishments (三刑): [寅巳申] (Tiger-Snake-Monkey) and [丑戌未] (Ox-Dog-Goat)
   - Self-Punishment (自刑): Duplicate branches in self-punishment set
   - Each interaction flagged with description and warning level (高/中/低)

Key Function:
    get_da_yun(lunar_birthday, gender): Calculates complete Big Luck Cycles analysis.

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male

    Returns:
        dict: Comprehensive Da Yun analysis in JSON format with:
        - 起运 metadata: timing, direction, gender, cycle count
        - 大运周期: array of 10 cycles, each containing:
            * 序号: cycle number (0-9)
            * 干支: stem-branch pair
            * 旬/旬空: sexagenary and void information
            * 五行: stem and branch five elements with polarity
            * 纳音: nayin descriptive element name
            * 地势: life stage
            * 十神: primary theme + hidden stem analysis
            * 作用: all detected interactions with birth chart
            * Year and age range data

Output Format:
    All dictionary keys and values use Chinese characters for consistency.
    Integrates lunar-python library data for accuracy and reliability.
    Interactions are actionable event alerts for period interpretation.
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


# ============================================================================
# INTERACTION MAPPINGS (作用) - Comprehensive Branch and Stem Relationships
# ============================================================================

# Branch Clash (六冲) - Opposing pairs
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

# Branch Harm (六害) - Betrayal or health issues
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

# Six Combinations (六合) - Harmony pairs
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

# Triple Combination (三合) - Full element triads
triple_he = {
    "水": {"申", "子", "辰"},
    "木": {"亥", "卯", "未"},
    "火": {"寅", "午", "戌"},
    "金": {"巳", "酉", "丑"},
}

# Cardinal Branches - Stability points for half-harmony assessment
cardinal_branches = {
    "水": "子",
    "木": "卯",
    "火": "午",
    "金": "酉",
}

# Directional Combinations (三会) - Seasonal combinations
directional_he = {
    "Wood": {"寅", "卯", "辰"},
    "Fire": {"巳", "午", "未"},
    "Metal": {"申", "酉", "戌"},
    "Water": {"亥", "子", "丑"},
}

# Six Destructions (六破) - Breaking relationships
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

# Hidden Stem Combinations (暗合) - Secret interactions
hidden_stem_he = {
    "寅": "丑",
    "丑": "寅",
    "午": "亥",
    "亥": "午",
    "卯": "申",
    "申": "卯",
}

# Three Punishments (三刑) - Ungrateful + Bullying patterns
ungrateful_punishment_branches = {"寅", "巳", "申"}
bullying_punishment_branches = {"丑", "未", "戌"}
uncivilized_punishment_pairs = {
    "子卯": "刑",
    "卯子": "刑",
}
self_punishment_branches = {"辰", "午", "酉", "亥"}

punishments = {
    "寅巳": "刑",
    "巳申": "刑",
    "申寅": "刑",
    "丑未": "刑",
    "未戌": "刑",
    "戌丑": "刑",
    "子卯": "刑",
    "卯子": "刑",
    "辰辰": "自刑",
    "午午": "自刑",
    "酉酉": "自刑",
    "亥亥": "自刑",
}

# Stem Interactions (天干作用)
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
    da_yun_stem: str, da_yun_branch: str, birth_chart: dict
) -> dict:
    """
    Detect sophisticated Da Yun interactions with birth chart using 1x4 scan.

    The Da Yun pillar acts as an External Trigger entering the birth chart system.
    Implements Tier 0 (Fan Fu & Fu Yin), Tier 1 (Structural), and Tier 2/3 (Frictional) checks.

    Tier 0 Priority Checks:
    - Fan Fu (反吟): Total Opposition - Da Yun stem and branch both clash with natal pillar
    - Fu Yin (伏吟): Total Identity - Da Yun pillar exactly matches a natal pillar

    Tier 2 Special Case - Opening the Storehouse (开库):
    - Earth branch clashes (辰-戌 or 丑-未) are treated differently from regular clashes
    - Instead of predictable "high warning disorder," opening the storehouse releases the
      hidden stems (天干魂气) and their ten gods within that natal branch
    - Outcome depends on what's released: wealth stars = financial gain, officer stars = power shift,
      printing stars = mentor appearance
    - Warning level reduced from 高 to 中 due to nuanced interpretive potential

    Args:
        da_yun_stem (str): Da Yun heavenly stem
        da_yun_branch (str): Da Yun earthly branch
        birth_chart (dict): Birth chart with keys "year", "month", "day", "hour"
                           Each containing "stem" and "branch" strings

    Returns:
        dict: Organized interactions by pillar and tier
              Special 开库 interactions include "释放天干" and "释放十神" fields
    """
    if not da_yun_stem or not da_yun_branch:
        return {"作用": []}

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

    interactions = []
    locked_branches = set()  # Prevent zombie interactions
    combined_pillars = (
        set()
    )  # Track Tier 1 (San Hui/San He) bindings - highest priority
    harmonized_pillars = set()  # Track Tier 2A (Liu He) bindings - strong priority
    clashed_pillars = (
        set()
    )  # Track Tier 2B (Liu Chong) bindings - can break punishments

    # === PRE-SCAN: Check if Da Yun branch is globally bound by triple combinations ===
    # This MUST happen before the main 1x4 loop so that Key vs Lock logic is correct
    global_binding_info = _detect_global_triple_combinations(da_yun_branch, zhis)
    da_yun_branch_bound = global_binding_info["is_bound"]  # Global binding status
    globally_bound_pillars = global_binding_info[
        "affected_indices"
    ]  # Which pillars participate

    # Report global San Hui/San He combination (Tier 1A/1B - reported once globally)
    if da_yun_branch_bound:
        combination_type = global_binding_info.get("combination_type")
        element = global_binding_info.get("element", "")

        if combination_type == "三会":
            direction_cn = {
                "Wood": "木",
                "Fire": "火",
                "Metal": "金",
                "Water": "水",
            }.get(element, element)
            interactions.append(
                {
                    "优先级": "1_三会",
                    "柱": "全局",
                    "类型": f"三会{direction_cn}局",
                    "描述": f"大运{da_yun_branch}与八字三会{direction_cn}局，该方位事业/学业易有突破",
                    "警告等级": "无",
                }
            )
        elif combination_type == "三合":
            interactions.append(
                {
                    "优先级": "1_三合",
                    "柱": "全局",
                    "类型": f"三合{element}局",
                    "描述": f"大运{da_yun_branch}与八字三合{element}局，合力促进相关运势",
                    "警告等级": "无",
                }
            )

    # 1x4 SCAN: Da Yun pillar vs each birth pillar
    for i in range(4):
        target_gan = gans[i]
        target_zhi = zhis[i]
        pillar = pillar_names[i]

        # === TIER 0: Fan Fu (反吟) - Total Opposition ===
        if (
            clash_map.get(da_yun_branch) == target_zhi
            and stem_clashes.get(da_yun_stem) == target_gan
        ):
            interactions.append(
                {
                    "优先级": "0_反吟",
                    "柱": pillar,
                    "类型": "反吟",
                    "描述": f"大运与{pillar}干支皆反，主该柱位发生重大转折（若日柱则婚姻/健康危机）",
                    "警告等级": "极高",
                }
            )
            locked_branches.add(i)
            continue

        # === TIER 0B: Fu Yin (伏吟) - Total Identity ===
        # Sui Yun Bing Lin (岁运并临): Da Yun pillar matches natal pillar exactly
        # Warning severity depends on which pillar is affected:
        # - Day Pillar (日柱): "极高" - directly impacts the self
        # - Year Pillar (年柱): "高" - ancestral/family level impact
        # - Other pillars (月/时): "高" - standard impact
        if da_yun_stem == target_gan and da_yun_branch == target_zhi:
            # Adjust warning level based on pillar type
            if i == 2:  # i=2 is Day Pillar (日柱)
                warning_level = "极高"
                description = f"大运与{pillar}干支完全相同（伏吟并临），主该十年自我心绪极度不宁、事倍功半，身心俱疲，或有呻吟之忧。直接作用于日主本身，影响深远。"
            else:  # Year Pillar (i=0), Month Pillar (i=1), or Hour Pillar (i=3)
                warning_level = "高"
                description = f"大运与{pillar}干支完全相同（伏吟），主该十年该柱位心绪不宁、事倍功半，或有呻吟之忧。"

            interactions.append(
                {
                    "优先级": "0_伏吟",
                    "柱": pillar,
                    "类型": "伏吟",
                    "描述": description,
                    "警告等级": warning_level,
                }
            )
            locked_branches.add(i)
            continue

        # === TIER 2A: Liu He (六合) - Pairwise harmony ===
        if six_he_map.get(da_yun_branch) == target_zhi:
            interactions.append(
                {
                    "优先级": "2_六合",
                    "柱": pillar,
                    "类型": "六合",
                    "描述": f"大运与{pillar}六合，稳定或被约束该柱位",
                    "警告等级": "无",
                }
            )
            locked_branches.add(i)
            harmonized_pillars.add(i)  # Mark as consumed by Tier 2A harmony
            # Note: da_yun_branch_bound was already determined by pre-scan
            continue  # Short-circuit to prevent lower tiers

        # === TIER 2B: Liu Chong (六冲) - Direct opposition ===
        # Special case: Earth branch clashes (辰-戌 or 丑-未) = "Opening the Storehouse" (开库)
        if clash_map.get(da_yun_branch) == target_zhi and i not in locked_branches:
            # Check if this is an Earth branch clash (开库)
            earth_branch_clashes = {
                "辰": "戌",
                "戌": "辰",
                "丑": "未",
                "未": "丑",
            }

            if target_zhi in earth_branch_clashes:
                # This is an Earth branch clash - "Opening the Storehouse" (开库)
                # Key vs Lock Logic: Da Yun branch is the KEY. If it's bound (busy), it lacks force.
                #
                # If the Key (Da Yun branch) is bound by beneficial combinations (San Hui/San He/Liu He),
                # it has no energy to "bump" open the Lock (natal tomb). The 开库 manifestation is suppressed.
                #
                # If the Key is free, it can open the Lock fully.

                if da_yun_branch_bound:
                    # Key is busy - cannot open the Lock properly
                    description = f"大运{da_yun_branch}与{pillar}{target_zhi}相冲形成开库之象，但大运{da_yun_branch}已被高优先级组合所占用，缺乏剩余力量撬开该柱位。库象虽存在，冲击力大幅减弱，难以真正释放内部力量。"
                    warning_level = "低"
                else:
                    # Key is free - can open the Lock fully
                    # Get hidden stems from the natal branch being opened
                    hidden_stems = LunarUtil.ZHI_HIDE_GAN.get(target_zhi, [])
                    hidden_stem_names = (
                        "、".join(hidden_stems) if hidden_stems else "未知"
                    )
                    hidden_stem_ten_gods = [
                        _get_shi_shen_for_stem_pair(day_stem, stem)
                        for stem in hidden_stems
                    ]
                    ten_god_names = (
                        "、".join(hidden_stem_ten_gods)
                        if hidden_stem_ten_gods
                        else "未知"
                    )

                    description = f"大运{da_yun_branch}与{pillar}{target_zhi}相冲形成开库，释放该柱位的隐藏天干（{hidden_stem_names}）及其十神力量（{ten_god_names}）。若释放财星，可能财运亨通；若释放官星，可能权力变化；若释放印星，可能贵人现身。"
                    warning_level = "中"

                interactions.append(
                    {
                        "优先级": "2_开库",
                        "柱": pillar,
                        "类型": "开库",
                        "描述": description,
                        "警告等级": warning_level,
                        "释放天干": (
                            "、".join(LunarUtil.ZHI_HIDE_GAN.get(target_zhi, []))
                            if not da_yun_branch_bound
                            else "(被组合所占用，释放力减弱)"
                        ),
                        "释放十神": (
                            "、".join(
                                [
                                    _get_shi_shen_for_stem_pair(day_stem, stem)
                                    for stem in LunarUtil.ZHI_HIDE_GAN.get(
                                        target_zhi, []
                                    )
                                ]
                            )
                            if not da_yun_branch_bound
                            else "(被组合所占用，释放力减弱)"
                        ),
                    }
                )
            else:
                # Regular clash for non-Earth branches (no Key vs Lock logic needed)
                interactions.append(
                    {
                        "优先级": "2_六冲",
                        "柱": pillar,
                        "类型": "六冲",
                        "描述": f"大运与{pillar}相冲，该柱位可能有破位、搬家、工作变动",
                        "警告等级": "高",
                    }
                )

            locked_branches.add(i)
            clashed_pillars.add(
                i
            )  # Mark as consumed by Tier 2B clash - can break punishments
            continue

        # === TIER 3A: Ban He (半合) - Partial triple ===
        for element, group in triple_he.items():
            if da_yun_branch in group and target_zhi in group:
                cardinal = cardinal_branches.get(element)
                # Check if cardinal is present in birth chart OR if Da Yun IS the cardinal
                branches_with_da_yun = zhis + [da_yun_branch]
                strength = "强" if cardinal in branches_with_da_yun else "弱"
                interactions.append(
                    {
                        "优先级": "3_半合",
                        "柱": pillar,
                        "类型": f"半合{element}局({strength})",
                        "描述": f"大运与{pillar}半合{element}局({strength})，部分促进作用",
                        "警告等级": "无",
                    }
                )
                break

        # === TIER 3B: Liu Hai (六害) - Damage relationships ===
        # Principle: Harm is weakened if the branch is consumed by Tier 1 (combination) or Tier 2A (harmony)
        if harm_map.get(da_yun_branch) == target_zhi and i not in locked_branches:
            if i in combined_pillars or i in harmonized_pillars:
                # Branch is "happy" with its binding, weakens the Harm manifestation
                warning_level = "低"
                description = f"大运与{pillar}相害，但该柱位已被较高优先级的组合或和谐所吸收，冲击力减弱"
            else:
                # Normal Harm manifestation
                warning_level = "中"
                description = f"大运与{pillar}相害，该柱位易有背叛、健康问题或冲突"

            interactions.append(
                {
                    "优先级": "3_六害",
                    "柱": pillar,
                    "类型": "六害",
                    "描述": description,
                    "警告等级": warning_level,
                }
            )
            continue

        # === TIER 3C: Liu Po (六破) - Breaking relationships ===
        # Principle: Break is weakened if the branch is consumed by Tier 1 (combination) or Tier 2A (harmony)
        if break_map.get(da_yun_branch) == target_zhi and i not in locked_branches:
            if i in combined_pillars or i in harmonized_pillars:
                # Branch is "busy" with its binding, further weakens the Break manifestation
                warning_level = "极低"
                description = f"大运与{pillar}相破，但该柱位已被较高优先级的组合或和谐所吸收，实际影响微弱"
            else:
                # Normal Break manifestation
                warning_level = "低"
                description = f"大运与{pillar}相破，该柱位有隐性损害或裂痕"

            interactions.append(
                {
                    "优先级": "3_六破",
                    "柱": pillar,
                    "类型": "六破",
                    "描述": description,
                    "警告等级": warning_level,
                }
            )
            continue

        # === TIER 4: San Xing (三刑) - Punishments ===
        # Principle: Clash (Tier 2B) can break/transform Punishments (Tier 4)
        # If Liu Chong exists on this pillar, the Punishment is "shattered" by external force

        # Ungrateful Punishment (恩将仇报)
        if (
            da_yun_branch in ungrateful_punishment_branches
            and target_zhi in ungrateful_punishment_branches
        ):
            # Skip if this pillar is already shattered by a Clash
            if i in clashed_pillars:
                continue  # The Clash takes center stage, Punishment is transformed/broken

            count = sum(1 for z in zhis if z in ungrateful_punishment_branches)
            label = "三刑(恩将仇报)" if count == 3 else "半刑(恩将仇报)"
            interactions.append(
                {
                    "优先级": "4_三刑",
                    "柱": pillar,
                    "类型": label,
                    "描述": f"大运与{pillar}{label}，该柱位易显现忘恩负义或被背叛",
                    "警告等级": "高",
                }
            )

        # Bullying Punishment (欺负)
        if (
            da_yun_branch in bullying_punishment_branches
            and target_zhi in bullying_punishment_branches
        ):
            # Skip if this pillar is already shattered by a Clash
            if i in clashed_pillars:
                continue  # The Clash takes center stage, Punishment is transformed/broken

            count = sum(1 for z in zhis if z in bullying_punishment_branches)
            label = "三刑(欺负)" if count == 3 else "半刑(欺负)"
            interactions.append(
                {
                    "优先级": "4_三刑",
                    "柱": pillar,
                    "类型": label,
                    "描述": f"大运与{pillar}{label}，该柱位易显现欺凌或被欺凌",
                    "警告等级": "高",
                }
            )

        # Self-Punishment (自刑)
        pair_key = "".join(sorted([da_yun_branch, target_zhi]))
        if pair_key in ["辰辰", "午午", "酉酉", "亥亥"]:
            # Self-Punishment nuance: Even if pillar is clashed, still report as internal psychological state
            if i in clashed_pillars:
                # Clash takes center stage: Self-Punishment becomes internal doubt/sabotage from external conflict
                interactions.append(
                    {
                        "优先级": "4_自刑",
                        "柱": pillar,
                        "类型": "自刑",
                        "描述": f"因受冲力影响，自刑之象转化为外部冲突带来的自我怀疑。大运与{pillar}相冲时产生的内在心理冲突，表现为自我否定或自我破坏行为",
                        "警告等级": "低",
                    }
                )
            else:
                # Free pillar: Pure self-punishment as internal psychological state
                interactions.append(
                    {
                        "优先级": "4_自刑",
                        "柱": pillar,
                        "类型": "自刑",
                        "描述": f"大运与{pillar}自刑，该柱位易引发自伤行为或内疚",
                        "警告等级": "中",
                    }
                )

        # === TIER 5: Hidden Stem Combinations (暗合) ===
        if hidden_stem_he.get(da_yun_branch) == target_zhi:
            interactions.append(
                {
                    "优先级": "5_暗合",
                    "柱": pillar,
                    "类型": "暗合",
                    "描述": f"大运与{pillar}暗合，私下或隐性的和谐作用",
                    "警告等级": "无",
                }
            )

        # === Stem Interactions (Heavenly Stems) ===
        # Stem Combine
        if stem_combines.get(da_yun_stem) == target_gan:
            # Special Case: Day Master Being Joined (日主被合) - Double-edged sword
            if i == 2:  # i=2 is the Day Pillar (Day Master/Self)
                # Check branch rooting (is the combination "tight" or "loose"?)
                rooting_info = _check_branch_rooting(da_yun_stem, da_yun_branch)

                # Construct detailed interaction record
                interactions.append(
                    {
                        "优先级": "1_日主被合",
                        "柱": pillar,
                        "类型": "天干合(日主)",
                        "描述": f"大运天干与日主相合，主该十年与人事物深度绑定。可能婚配、重大合作或执着沉溺，需警惕失去独立性。根基状态：{rooting_info['strength']}。",
                        "警告等级": "中",
                        "根基强度": rooting_info["strength"],
                        "根基说明": rooting_info["interpretation"],
                    }
                )
            else:
                # Regular stem combine with other pillars
                interactions.append(
                    {
                        "优先级": "2_天干合",
                        "柱": pillar,
                        "类型": "天干合",
                        "描述": f"大运干与{pillar}干相合，该柱位性格或行动更协调",
                        "警告等级": "无",
                    }
                )

        # Stem Clash
        if stem_clashes.get(da_yun_stem) == target_gan:
            # Special Case: Day Master Under Attack (日主受克) - Highest severity
            if i == 2:  # i=2 is the Day Pillar (Day Master/Self)
                # Check branch rooting (is the attack "strong" or "weak"?)
                rooting_info = _check_branch_rooting(da_yun_stem, da_yun_branch)

                interactions.append(
                    {
                        "优先级": "0_日主受克",
                        "柱": pillar,
                        "类型": "天干克(日主)",
                        "描述": f"大运天干直接克制日主，主该十年压力极大。需关注身体健康与意外。根基状态：{rooting_info['strength']}。",
                        "警告等级": "极高",
                        "根基强度": rooting_info["strength"],
                        "根基说明": rooting_info["interpretation"],
                    }
                )
            else:
                # Regular stem clash with other pillars
                interactions.append(
                    {
                        "优先级": "2_天干克",
                        "柱": pillar,
                        "类型": "天干克",
                        "描述": f"大运干与{pillar}干相克，该柱位性格或行动有冲突",
                        "警告等级": "低",
                    }
                )

    return {"作用": interactions}


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
    start_solar = yun.getStartSolar()

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
            "开始年份": da_yun.getStartYear(),  # Start calendar year
            "结束年份": da_yun.getEndYear(),  # End calendar year
            "开始年龄": da_yun.getStartAge(),  # Start age (from birth)
            "结束年龄": da_yun.getEndAge(),  # End age (from birth)
            "周期": f"{da_yun.getStartAge()}-{da_yun.getEndAge()}岁",  # Age range display
        }
        da_yun_data.append(da_yun_info)

    # Compile the complete da_yun structure
    return {
        "大运": {
            "起运": {
                "性别": "男" if gender == 1 else "女",
                "出生地阳历": lunar_birthday.getSolar().toYmdHms(),
                "起运时间": start_solar.toYmdHms(),
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
    # solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)
    # datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)
    # tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)


    # Corinne's birthday example
    solar_birthday= Solar.fromYmdHms(1987, 6, 3, 12, 6, 0)  # Create solar date June 3, 1987 at 12:06 PM
    tst_birthday, inputs_report = get_true_solar_time(datetime(1987, 6, 3, 12, 6, 0), 1.4759, 103.808053)
    lunar_birthday = tst_birthday.getLunar()

    print("八字")
    bazi_json = get_bazi_pillars(tst_birthday.getLunar())
    print(f"八字: {bazi_json}")

    # print("=== Female (Gender=0) ===")
    # result = get_da_yun(lunar_birthday, gender=0)
    # print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n=== Male (Gender=1) ===")
    result = get_da_yun(lunar_birthday, gender=0)
    print(json.dumps(result, ensure_ascii=False, indent=2))
