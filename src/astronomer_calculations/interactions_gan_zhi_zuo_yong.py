"""
This module calculates and analyzes the interactions between Heavenly Stems (天干) and
Earthly Branches (地支) in a BaZi (八字) chart based on the lunar birthday. It detects
various types of relationships including clashes, harms, harmonies, combinations, and
punishments.

Key Features:
    - Earthly Branch Interactions: Detects clashes (冲), harms (害), six-harmonies (合),
      full triple combinations (全三合), directional combinations (三会), and partial combinations (半合)
    - Half-Harmony Strength Assessment: Differentiates between Strong (强) and Weak (弱) half-harmonies
      based on cardinal branch presence (Growing+Cardinal or Cardinal+Graveyard = Strong;
      Growing+Graveyard = Weak)
    - Heavenly Stem Interactions: Identifies stem combinations (天干合) and clashes (天干克)
    - Punishment Detection: Recognizes full/partial three-punishment patterns (三刑) with distinction
      between Ungrateful (恩将仇报), Bullying (欺负), Uncivilized (无礼), and Self-Punishments (自刑)
    - Pillar-based Analysis: Provides interaction details for Year, Month, Day, and Hour pillars

INTERACTION PRIORITY (in order of checking):
    1. San Hui (三会) - Directional seasonal combinations (highest precedence)
    2. San He (三合) - Full triple element combinations
    3. Clash (冲) - Direct opposition (evaluated first in pairwise checks)
    4. Liu He (六合) - Six harmonies/pairwise combinations
    5. San Xing (三刑) - Punishments with full/partial distinction
    6. Harm (害) - Damage relationships
    7. Liu Po (六破) - Six destructions
    8. Half San He (半合) - Partial/half triple combinations (with strength markers)
    9. An He (暗合) - Hidden stem combinations (secret interactions)

Note: All applicable interactions are evaluated and accumulated in priority order. This allows
"double-whammy" relationships to display all relevant interactions (e.g., a Clash that also
has a Punishment will show both: "冲 刑"). The order reflects which interaction is checked
first and thus appears first in the display string.

Interaction Maps:
    - clash_map: Maps branches to their clash (opposing) partners
    - harm_map: Maps branches to their harm (harmful) partners
    - six_he_map: Maps branches to their harmonious partners
    - triple_he: Groups branches by element with positions (Cardinal/成, Growing/旺, Graveyard/墓)
    - cardinal_branches: Maps elements to their stability/cardinal branches
    - directional_he: Groups branches by season/direction (directional combinations)
    - break_map: Maps branches to their destruction partners (六破)
    - hidden_stem_he: Maps branches to hidden stem combination partners
    - punishments: Maps branch pairs to punishment types (三刑)
    - stem_combines: Maps stems to their harmonious partners
    - stem_clashes: Maps stems to their polar-opposite partners (true clashes)

Main Function:
    get_interactions(lunar_birthday): Extracts and analyzes all pillar interactions
        from a BaZi chart, returning interaction descriptions, stems, and branches.

Dependencies:
    - lunar_python: For lunar calendar conversion and BaZi chart extraction
    - datetime: For date/time handling
    - src.solar_lunar_time: For true solar time calculations
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

# Triple Combination Map (Needs 2 out of 3 for a "Partial" or 3 for "Full")
# Structure: Element -> {Cardinal (成), Growing (旺), Graveyard (墓)}
triple_he = {
    "水": {"申", "子", "辰"},  # Cardinal: 子 | Growing: 申 | Graveyard: 辰
    "木": {"亥", "卯", "未"},  # Cardinal: 卯 | Growing: 亥 | Graveyard: 未
    "火": {"寅", "午", "戌"},  # Cardinal: 午 | Growing: 寅 | Graveyard: 戌
    "金": {"巳", "酉", "丑"},  # Cardinal: 酉 | Growing: 巳 | Graveyard: 丑
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


def get_interactions(lunar_birthday):
    """
    Extract pillar interactions from the BaZi chart and return structured LLM-ready JSON.
    Detects clashes, harms, harmonies, punishments, and stem combinations.

    Args:
        lunar_birthday: Lunar object from BaZi chart

    Returns:
        dict: Structured interaction data organized by pillar dynamics and priority tiers
    """
    baZi = lunar_birthday.getEightChar()
    gans = [baZi.getYearGan(), baZi.getMonthGan(), baZi.getDayGan(), baZi.getTimeGan()]
    zhis = [baZi.getYearZhi(), baZi.getMonthZhi(), baZi.getDayZhi(), baZi.getTimeZhi()]

    pillar_names_cn = ["年柱", "月柱", "日柱", "时柱"]
    pillar_names = ["年", "月", "日", "时"]

    # Track interactions by type for priority categorization
    interactions_by_type = {
        "三会": [],
        "三合": [],
        "天干合": [],
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
    strs = ["", "", "", ""]
    interaction_shens = []

    # Branch Lock System: Track indices locked in Tier 1 structures to prevent Zombie Interactions
    # (e.g., avoid showing 六破 between branches already in 三会 or 三合)
    locked_branches = (
        set()
    )  # Track pillar indices (0, 1, 2, 3) occupied by high-order harmonies

    # --- Earthly Branch Interactions ---
    # PRIORITY 1: Directional Combinations (San Hui) - Highest Priority
    for direction, group in directional_he.items():
        if all(branch in zhis for branch in group):
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
            for idx, branch in enumerate(zhis):
                if branch in group:
                    strs[idx] = f"{strs[idx]} 会({direction}局)".strip()
                    pillar_dynamics[idx]["structural"].append(display_text)
                    locked_branches.add(
                        idx
                    )  # Lock these branches (三会 = Tier 1 Structural)

    # PRIORITY 2: Full Triple Combinations (San He)
    for element, group in triple_he.items():
        if all(branch in zhis for branch in group):
            display_text = f"三合{element}局"
            interaction_summary.append(display_text)
            interaction_shens.append(f"全三合{element}局")
            interactions_by_type["三合"].append(display_text)
            for idx, branch in enumerate(zhis):
                if branch in group:
                    strs[idx] = f"{strs[idx]} 合({element}局)".strip()
                    pillar_dynamics[idx]["structural"].append(display_text)
                    locked_branches.add(
                        idx
                    )  # Lock these branches (三合 = Tier 1 Structural)

    # Check pairwise interactions - Evaluate all conditions in priority order
    # SHORT-CIRCUIT LOGIC: Use if/elif for mutually exclusive relationships to prevent LLM confusion
    # INDEPENDENT CHECKS: Use if (not elif) for Punishments & Hidden Combinations - they add "flavor" to primary relationships
    for i in range(4):
        for j in range(i + 1, 4):
            b_i, b_j = zhis[i], zhis[j]
            pair_key = "".join(sorted([b_i, b_j]))

            # === SHORT-CIRCUIT CHAIN: Only one of these will be processed per pair ===
            # Priority 1: Six Harmonies (Liu He) - Highest tier, locks out minor frictions
            if six_he_map.get(b_i) == b_j:
                strs[i] = f"{strs[i]} 合({pillar_names[j]})".strip()
                strs[j] = f"{strs[j]} 合({pillar_names[i]})".strip()
                interaction_shens.append(f"{pillar_names[i]}{pillar_names[j]}合")
                display_text = f"六合({pillar_names_cn[j]}{b_j}{branch_elements.get(b_j, '')})"
                pillar_dynamics[i]["structural"].append(display_text)
                pillar_dynamics[j]["structural"].append(f"六合({pillar_names_cn[i]}{b_i}{branch_elements.get(b_i, '')})")
                interactions_by_type["六合"].append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j})地支相合"
                )
                interaction_summary.append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j})地支相合"
                )
            # Priority 2: Clashes (冲) - High priority, locks out minor frictions
            elif clash_map.get(b_i) == b_j:
                strs[i] = f"{strs[i]} 冲({pillar_names[j]})".strip()
                strs[j] = f"{strs[j]} 冲({pillar_names[i]})".strip()
                interaction_shens.append(f"{pillar_names[i]}{pillar_names[j]}冲")
                display_text = f"六冲({pillar_names_cn[j]}{b_j}{branch_elements.get(b_j, '')})"
                pillar_dynamics[i]["frictional"].append(display_text)
                pillar_dynamics[j]["frictional"].append(f"六冲({pillar_names_cn[i]}{b_i}{branch_elements.get(b_i, '')})")
                interactions_by_type["六冲"].append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j})地支相冲"
                )
                interaction_summary.append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j})地支相冲"
                )
            # Priority 3: Harms (害) - Medium tier, only checked if no Harmony or Clash
            elif (
                harm_map.get(b_i) == b_j
                and i not in locked_branches
                and j not in locked_branches
            ):
                strs[i] = f"{strs[i]} 害({pillar_names[j]})".strip()
                strs[j] = f"{strs[j]} 害({pillar_names[i]})".strip()
                interaction_shens.append(f"{pillar_names[i]}{pillar_names[j]}害")
                display_i = f"六害({pillar_names_cn[j]}{b_j}{branch_elements.get(b_j, '')})"
                display_j = f"六害({pillar_names_cn[i]}{b_i}{branch_elements.get(b_i, '')})"
                pillar_dynamics[i]["frictional"].append(display_i)
                pillar_dynamics[j]["frictional"].append(display_j)
                interactions_by_type["六害"].append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j})地支相害"
                )
                interaction_summary.append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j})地支相害"
                )
            # Priority 4: Liu Po (Six Destructions) - Lowest tier, only checked if no higher-tier relationships
            elif (
                break_map.get(b_i) == b_j
                and i not in locked_branches
                and j not in locked_branches
            ):
                strs[i] = f"{strs[i]} 破({pillar_names[j]})".strip()
                strs[j] = f"{strs[j]} 破({pillar_names[i]})".strip()
                interaction_shens.append(f"{pillar_names[i]}{pillar_names[j]}破")
                display_i = f"六破({pillar_names_cn[j]}{b_j}{branch_elements.get(b_j, '')})"
                display_j = f"六破({pillar_names_cn[i]}{b_i}{branch_elements.get(b_i, '')})"
                pillar_dynamics[i]["frictional"].append(display_i)
                pillar_dynamics[j]["frictional"].append(display_j)
                interactions_by_type["六破"].append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j})地支相破"
                )
                interaction_summary.append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j})地支相破"
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
                if ungrateful_count == 3:
                    label_cn = "刑(恩将仇报)"
                else:
                    label_cn = "刑(半恩将仇报)"
                strs[i] = f"{strs[i]} {label_cn}".strip()
                strs[j] = f"{strs[j]} {label_cn}".strip()
                interaction_shens.append(
                    f"{pillar_names[i]}{pillar_names[j]}{label_cn}"
                )
                pillar_dynamics[i]["frictional"].append(
                    f"{label_cn}({pillar_names_cn[j]}{b_j}{branch_elements.get(b_j, '')})"
                )
                pillar_dynamics[j]["frictional"].append(
                    f"{label_cn}({pillar_names_cn[i]}{b_i}{branch_elements.get(b_i, '')})"
                )
                interactions_by_type["三刑"].append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j}){label_cn}"
                )
                interaction_summary.append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j}){label_cn}"
                )

            # Check for Full/Partial Bullying Punishment (丑-未-戌)
            if (
                b_i in bullying_punishment_branches
                and b_j in bullying_punishment_branches
            ):
                bullying_count = sum(
                    1 for branch in zhis if branch in bullying_punishment_branches
                )
                if bullying_count == 3:
                    label_cn = "刑(欺负)"
                else:
                    label_cn = "刑(半欺负)"
                strs[i] = f"{strs[i]} {label_cn}".strip()
                strs[j] = f"{strs[j]} {label_cn}".strip()
                interaction_shens.append(
                    f"{pillar_names[i]}{pillar_names[j]}{label_cn}"
                )
                pillar_dynamics[i]["frictional"].append(
                    f"{label_cn}({pillar_names_cn[j]}{b_j}{branch_elements.get(b_j, '')})"
                )
                pillar_dynamics[j]["frictional"].append(
                    f"{label_cn}({pillar_names_cn[i]}{b_i}{branch_elements.get(b_i, '')})"
                )
                interactions_by_type["三刑"].append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j}){label_cn}"
                )
                interaction_summary.append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j}){label_cn}"
                )

            # Check for Uncivilized Punishment (子-卯)
            if pair_key in uncivilized_punishment_pairs:
                label_cn = "刑(无礼)"
                strs[i] = f"{strs[i]} {label_cn}".strip()
                strs[j] = f"{strs[j]} {label_cn}".strip()
                interaction_shens.append(
                    f"{pillar_names[i]}{pillar_names[j]}{label_cn}"
                )
                pillar_dynamics[i]["frictional"].append(
                    f"{label_cn}({pillar_names_cn[j]}{b_j}{branch_elements.get(b_j, '')})"
                )
                pillar_dynamics[j]["frictional"].append(
                    f"{label_cn}({pillar_names_cn[i]}{b_i}{branch_elements.get(b_i, '')})"
                )
                interactions_by_type["三刑"].append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j}){label_cn}"
                )
                interaction_summary.append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j}){label_cn}"
                )

            # Check for Self-Punishment (辰-辰, 午-午, 酉-酉, 亥-亥)
            if pair_key in punishments and "自刑" in punishments.get(pair_key, ""):
                label_cn = punishments[pair_key]
                strs[i] = f"{strs[i]} {label_cn}({pillar_names[j]})".strip()
                strs[j] = f"{strs[j]} {label_cn}({pillar_names[i]})".strip()
                interaction_shens.append(
                    f"{pillar_names[i]}{pillar_names[j]}{label_cn}"
                )
                pillar_dynamics[i]["frictional"].append(
                    f"{label_cn}({pillar_names_cn[j]}{b_j}{branch_elements.get(b_j, '')})"
                )
                pillar_dynamics[j]["frictional"].append(
                    f"{label_cn}({pillar_names_cn[i]}{b_i}{branch_elements.get(b_i, '')})"
                )
                interactions_by_type["三刑"].append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j}){label_cn}"
                )
                interaction_summary.append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j}){label_cn}"
                )

            # Priority 8: Partial Triple Combinations (Half San He) - With strength assessment
            # Guards: Skip if branches are in locked structures, or already in Six Harmony/Clash
            for element, group in triple_he.items():
                if (
                    b_i in group
                    and b_j in group
                    and i not in locked_branches
                    and j not in locked_branches
                    and six_he_map.get(b_i) != b_j  # Not in Six Harmony
                    and clash_map.get(b_i) != b_j
                ):  # Not in Clash
                    if "局" not in strs[i] and "会" not in strs[i]:
                        # Check half-harmony strength based on cardinal branch presence
                        cardinal = cardinal_branches.get(element)
                        if cardinal in zhis:
                            # Cardinal present: Strong half-harmony (Growing + Cardinal OR Cardinal + Graveyard)
                            strength_cn = "强"
                            strength_en = "Strong"
                        else:
                            # Cardinal missing: Weak half-harmony (Growing + Graveyard arch)
                            strength_cn = "弱"
                            strength_en = "Weak"

                        label_cn = f"半合{element}局({strength_cn})"
                        strs[i] = f"{strs[i]} {label_cn}".strip()
                        strs[j] = f"{strs[j]} {label_cn}".strip()
                        display_i = f"{label_cn}({pillar_names_cn[j]}{b_j}{branch_elements.get(b_j, '')})"
                        display_j = f"{label_cn}({pillar_names_cn[i]}{b_i}{branch_elements.get(b_i, '')})"
                        pillar_dynamics[i]["structural"].append(display_i)
                        pillar_dynamics[j]["structural"].append(display_j)

                    interaction_shens.append(
                        f"{pillar_names[i]}{pillar_names[j]}半合{element}局"
                    )
                    interactions_by_type["六合"].append(
                        f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j})半合{element}局"
                    )
                    interaction_summary.append(
                        f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j})半合{element}局"
                    )
                    break

            # Priority 9: Hidden Stem Combinations (An He) - Secret interactions
            # Guards: Skip if branches are in locked structures or Clash
            if (
                hidden_stem_he.get(b_i) == b_j
                and i not in locked_branches
                and j not in locked_branches
                and clash_map.get(b_i) != b_j
            ):  # Clash takes precedence
                strs[i] = f"{strs[i]} 暗合({pillar_names[j]})".strip()
                strs[j] = f"{strs[j]} 暗合({pillar_names[i]})".strip()
                interaction_shens.append(f"{pillar_names[i]}{pillar_names[j]}暗合")
                display_i = f"暗合({pillar_names_cn[j]}{b_j}{branch_elements.get(b_j, '')})"
                display_j = f"暗合({pillar_names_cn[i]}{b_i}{branch_elements.get(b_i, '')})"
                pillar_dynamics[i]["structural"].append(display_i)
                pillar_dynamics[j]["structural"].append(display_j)
                interactions_by_type["暗合"].append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j})地支暗合"
                )
                interaction_summary.append(
                    f"{pillar_names[i]}{pillar_names[j]}({b_i}{b_j})地支暗合"
                )

    # --- Heavenly Stem Interactions ---
    for i in range(4):
        for j in range(i + 1, 4):
            g_i, g_j = gans[i], gans[j]

            # Stem Combine (Harmony)
            if stem_combines.get(g_i) == g_j:
                strs[i] = f"{strs[i]} 合化({pillar_names[j]})".strip()
                strs[j] = f"{strs[j]} 合化({pillar_names[i]})".strip()
                interaction_shens.append(f"{pillar_names[i]}{pillar_names[j]}天干合")
                display_i = f"天干合({pillar_names_cn[j]}{g_j}{stem_elements.get(g_j, '')})"
                display_j = f"天干合({pillar_names_cn[i]}{g_i}{stem_elements.get(g_i, '')})"
                pillar_dynamics[i]["structural"].append(display_i)
                pillar_dynamics[j]["structural"].append(display_j)
                interactions_by_type["天干合"].append(
                    f"{pillar_names[i]}{pillar_names[j]}({g_i}{g_j})天干合化"
                )
                interaction_summary.append(
                    f"{pillar_names[i]}{pillar_names[j]}({g_i}{g_j})天干合化"
                )

            # Stem Clash (Friction)
            if stem_clashes.get(g_i) == g_j:
                # We skip showing '克' if they are already showing '合化' (Combination priority)
                if "合化" not in strs[i]:
                    strs[i] = f"{strs[i]} 天干克({pillar_names[j]})".strip()
                    strs[j] = f"{strs[j]} 天干克({pillar_names[i]})".strip()
                interaction_shens.append(f"{pillar_names[i]}{pillar_names[j]}天干克")
                display_i = f"天干克({pillar_names_cn[j]}{g_j}{stem_elements.get(g_j, '')})"
                display_j = f"天干克({pillar_names_cn[i]}{g_i}{stem_elements.get(g_i, '')})"
                pillar_dynamics[i]["frictional"].append(display_i)
                pillar_dynamics[j]["frictional"].append(display_j)
                interactions_by_type["六冲"].append(
                    f"{pillar_names[i]}{pillar_names[j]}({g_i}{g_j})天干相克"
                )
                interaction_summary.append(
                    f"{pillar_names[i]}{pillar_names[j]}({g_i}{g_j})天干相克"
                )

    # Build the final structured JSON with all three tiers
    # Define tier filter keywords for reusability
    tier1_keywords = ["三会", "三合", "六合", "半合", "天干合", "暗合"]
    tier2_keywords = ["六冲", "天干克"]
    tier3_keywords = ["三刑", "六害", "六破"]

    # Build 柱位动态 dynamically using dictionary comprehension to eliminate repetition
    pillar_dynamics_dict = {
        pillar_names_cn[k]: {
            "第一梯队_纲领层": list(
                dict.fromkeys(
                    [
                        item
                        for item in pillar_dynamics[k]["structural"]
                        if any(tier1 in item for tier1 in tier1_keywords)
                    ]
                )
            ),
            "第二梯队_气势层": list(
                dict.fromkeys(
                    [
                        item
                        for item in pillar_dynamics[k]["frictional"]
                        if any(t in item for t in tier2_keywords)
                    ]
                )
            ),
            "第三梯队_琐碎层": list(
                dict.fromkeys(
                    [
                        item
                        for item in pillar_dynamics[k]["frictional"]
                        if any(t in item for t in tier3_keywords)
                    ]
                )
            ),
        }
        for k in range(4)
    }

    result = {
        "关系总览": list(dict.fromkeys(interaction_summary)),
        "柱位动态": pillar_dynamics_dict,
        "判定优先级": {
            "第一梯队_纲领层": [
                "三会",
                "三合",
                "六合",
                "半合",
                "天干合",
                "暗合",
            ],
            "第二梯队_气势层": [
                "六冲",
                "天干克",
            ],
            "第三梯队_琐碎层": [
                "三刑",
                "六害",
                "六破",
            ],
        },
    }

    return {"作用": result}


# --- EXECUTION ---

if __name__ == "__main__":
    import json

    # python -m src.astronomer_calculations.interactions_gan_zhi_zuo_yong

    # Desmond's birthday example
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    tst_birthday, _ = get_true_solar_time(
        datetime_birthday, 1.3253, 103.808053
    )  # Get true solar time

    print("阳历生日: " + solar_birthday.toYmdHms())
    print("真太阳时生日: " + tst_birthday.toYmdHms())

    lunar_birthday = tst_birthday.getLunar()  # Convert to lunar calendar

    # Get interactions in LLM-ready JSON format
    result = get_interactions(lunar_birthday)

    print(f"\n--- JSON Output for LLM ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))
