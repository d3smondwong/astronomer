"""
Branch Energy & Interactions (地支能量系统) Module

This module calculates comprehensive branch interactions in a BaZi chart, including:

RESONANCE (共鸣):
- 六合 (Six Harmonies): Direct harmony pairs
- 三合 (Three Harmonies): Elemental triangle combinations
- 暗合 (Dark Harmonies): Underground attractions between branches
- 三会 (Three Meetings): Strongest seasonal directional forces

CONFLICT (冲突):
- 六冲 (Six Clashes): Direct 180° oppositions
- 六害 (Six Harms): Subtle interference/friction
- 六破 (Six Destructions): Wear and tear on branch energy
- 三刑 (Three Punishments): Systemic stress patterns

Returns a comprehensive energy map showing all resonances and conflicts for the four pillars.
"""

from lunar_python import Lunar

# 六合 Six Harmonies Map: Each branch maps to its harmony partner
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

# 六合 Six Harmonies Resultant Element Mapping
# Double-mapping: Both directions explicitly defined for safety
six_he_element_map = {
    ("丑", "子"): {"primary": "土"},
    ("子", "丑"): {"primary": "土"},
    ("亥", "寅"): {"primary": "木"},
    ("寅", "亥"): {"primary": "木"},
    ("卯", "戌"): {"primary": "火"},
    ("戌", "卯"): {"primary": "火"},
    ("辰", "酉"): {"primary": "金"},
    ("酉", "辰"): {"primary": "金"},
    ("巳", "申"): {"primary": "水"},
    ("申", "巳"): {"primary": "水"},
    ("午", "未"): {"primary": "土", "secondary": "火"},
    ("未", "午"): {"primary": "土", "secondary": "火"},
}

# 三合 The four elemental triangles
san_he_groups = {
    "水": ["申", "子", "辰"],  # Water: Birth (申), Peak (子), Storage (辰)
    "木": ["亥", "卯", "未"],  # Wood: Birth (亥), Peak (卯), Storage (未)
    "火": ["寅", "午", "戌"],  # Fire: Birth (寅), Peak (午), Storage (戌)
    "金": ["巳", "酉", "丑"],  # Metal: Birth (巳), Peak (酉), Storage (丑)
}

# 六冲 Six Clashes (Direct 180° Oppositions)
six_chong_map = {
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

# 六害 Six Harms (Interference/Friction)
six_hai_map = {
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

# 三刑 Three Punishments (Systemic Stress)
# These are often groups of three, but we check for any two existing together.
san_xing_groups = [
    {"name": "无恩之刑", "zhis": ["寅", "巳", "申"]},
    {"name": "恃势之刑", "zhis": ["丑", "戌", "未"]},
    {"name": "无礼之刑", "zhis": ["子", "卯"]},
    {
        "name": "自刑",
        "zhis": ["辰", "午", "酉", "亥"],
    },  # Occurs when the same branch repeats
]

# 六破 Six Destructions (Subtle cracks/wear and tear)
six_po_map = {
    "子": "酉",
    "酉": "子",
    "卯": "午",
    "午": "卯",
    "申": "巳",
    "巳": "申",
    "寅": "亥",
    "亥": "寅",
    "辰": "丑",
    "丑": "辰",
    "戌": "未",
    "未": "戌",
}

# 暗合 Dark Harmonies (Underground Attractions - Hidden Stem Resonances)
# These represent subtle "underground" attractions between branch pairs
an_he_map = {
    "寅": "丑",
    "丑": "寅",  # Tiger + Ox
    "卯": "申",
    "申": "卯",  # Rabbit + Monkey
    "午": "亥",
    "亥": "午",  # Horse + Pig
}

# 三会 Three Meetings (Strongest seasonal directional force)
san_hui_groups = {
    "木(东方)": ["寅", "卯", "辰"],
    "火(南方)": ["巳", "午", "未"],
    "金(西方)": ["申", "酉", "戌"],
    "水(北方)": ["亥", "子", "丑"],
}


def get_branch_energy(lunar_birthday: Lunar) -> dict:
    bazi = lunar_birthday.getEightChar()

    # Extract branches
    branches = {
        "年柱": bazi.getYearZhi(),
        "月柱": bazi.getMonthZhi(),
        "日柱": bazi.getDayZhi(),
        "时柱": bazi.getTimeZhi(),
    }

    pillar_names = list(branches.keys())
    zhis = list(branches.values())

    # --- 1. RESONANCE (Harmonies) ---
    potential_map = {}
    active_six_he = []
    active_san_he = []

    # Potential & Six Harmonies
    for name, zhi in branches.items():
        partner = six_he_map.get(zhi)
        if partner:
            pair_key = (zhi, partner)
            elem = six_he_element_map.get(pair_key, {}).get("primary", "")
            potential_map[name] = {"合": partner, "化": elem, "潜在": True}

    for i in range(len(zhis)):
        for j in range(i + 1, len(zhis)):
            if six_he_map.get(zhis[i]) == zhis[j]:

                is_adjacent = j - i == 1
                pair_key = (zhis[i], zhis[j])
                elem = six_he_element_map.get(pair_key, {}).get("primary", "")
                active_six_he.append(
                    {
                        "组合": f"{pillar_names[i]}-{pillar_names[j]}",
                        "组合明细": {
                            pillar_names[i]: zhis[i],
                            pillar_names[j]: zhis[j],
                        },
                        "结果": f"化{elem}",
                        "紧贴": is_adjacent,
                        "状态": "正合" if is_adjacent else "遥合",
                    }
                )

    # Three Harmonies (Triangles)
    # Define the Peak (Cardinal) branch for each trio
    peak_branches = {"水": "子", "木": "卯", "火": "午", "金": "酉"}

    # PRE-CALCULATE CLASH RELATIONSHIPS FOR INTERFERENCE DETECTION
    # Map each pillar to its clashing partner (if any exists in chart)
    clash_map_pillars = {}  # { index: (other_index, clashing_zhi, other_name) }
    for i in range(len(zhis)):
        for j in range(i + 1, len(zhis)):
            if six_chong_map.get(zhis[i]) == zhis[j]:
                clash_map_pillars[i] = (j, zhis[j], pillar_names[j])
                clash_map_pillars[j] = (i, zhis[i], pillar_names[i])

    for element, group in san_he_groups.items():
        # Get all matches and their original indices [0, 1, 2, 3]
        matches = [
            {"name": pillar_names[k], "zhi": zhis[k], "index": k}
            for k, zhi in enumerate(zhis)
            if zhi in group
        ]

        unique_zhis = set(m["zhi"] for m in matches)
        peak = peak_branches[element]

        # Only process if at least 2 unique branches from the trio are present
        if len(unique_zhis) >= 2:
            # CHECK FOR ADJACENCY:
            # We look for at least one pair of matching pillars that are side-by-side
            indices = sorted([m["index"] for m in matches])
            adjacent = any(
                indices[i + 1] - indices[i] == 1 for i in range(len(indices) - 1)
            )

            # GAPPED COMBINATION (隔合) HANDLING:
            # Include gapped combinations but mark them differently.
            # They exist but are weakened by distance.
            if not adjacent and len(unique_zhis) < 3:
                # Include but label as gapped - these still have influence, just weaker
                pass  # Continue to process with 隔合 status

            # CHECK FOR CLASH INTERFERENCE (冲突干扰):
            # If any member of this harmony is being clashed, the harmony is weakened/broken
            interference_data = None
            for match in matches:
                if match["index"] in clash_map_pillars:
                    other_idx, other_zhi, other_name = clash_map_pillars[match["index"]]
                    interference_data = {
                        "被冲支": match["zhi"],
                        "所在柱": match["name"],
                        "冲克者": other_zhi,
                        "冲克者柱": other_name,
                        "说明": "此通道被破坏，合局力量减弱",
                    }
                    break

            # Determine Status
            if len(unique_zhis) == 3:
                status = "三合全局"
            else:
                if peak in unique_zhis:
                    is_birth = group[0] in unique_zhis
                    status = "生地半合" if is_birth else "墓地半合"
                else:
                    status = "拱合局"

            # For non-adjacent 2-branch cases, add gapped label
            if not adjacent and len(unique_zhis) < 3:
                status = f"{status}(隔合)"

            # Determine 邀出 (Invited) value based on status
            if "拱合局" in status:
                yao_chu = peak  # Show the invited (arched) peak branch
            elif "三合全局" in status:
                yao_chu = "已全"  # Frame is already complete
            else:
                yao_chu = "无"  # No branch being invited

            result = {
                "元素": element,
                "组合": "-".join([m["name"] for m in matches]),
                "组合明细": {m["name"]: m["zhi"] for m in matches},
                "状态": status,
                "邀出": yao_chu,
                "紧贴": adjacent,  # True if branches are side-by-side
            }

            # Add interference info if any member is being clashed
            if interference_data:
                result["冲突干扰"] = interference_data

            active_san_he.append(result)

    # Three Meetings (Directional Force)
    active_san_hui = []
    for direction, group in san_hui_groups.items():
        matches = [
            {"name": pillar_names[k], "zhi": zhis[k]}
            for k, zhi in enumerate(zhis)
            if zhi in group
        ]
        unique_zhis = set(m["zhi"] for m in matches)
        if len(unique_zhis) >= 2:
            status = "三会成局" if len(unique_zhis) == 3 else "半会局"
            active_san_hui.append(
                {
                    "方位": direction,
                    "组合": "-".join([m["name"] for m in matches]),
                    "组合明细": {m["name"]: m["zhi"] for m in matches},
                    "状态": status,
                }
            )

    # --- 2. CONFLICT (Clash, Harm, Punishment, Destruction) ---
    active_chong = []
    active_hai = []
    active_xing = []
    active_po = []
    active_an_he = []

    for i in range(len(zhis)):
        for j in range(i + 1, len(zhis)):
            b1, b2 = zhis[i], zhis[j]
            p1_n, p2_n = pillar_names[i], pillar_names[j]

            # ADJACENCY CHECK: index difference must be exactly 1
            is_adjacent = j - i == 1

            # 1. Six Clashes (六冲) - Show all, but label by proximity
            # Direct Clash (正冲): Adjacent pillars with clash relationship
            # Remote Clash (遥冲): Non-adjacent pillars with clash relationship
            if six_chong_map.get(b1) == b2:
                active_chong.append(
                    {
                        "组合": f"{p1_n}-{p2_n}",
                        "组合明细": {p1_n: b1, p2_n: b2},
                        "紧贴": is_adjacent,
                        "状态": "正冲" if is_adjacent else "遥冲",
                    }
                )

            # 2. Six Harms (六害) - Show all, but label by proximity
            # Direct Harm (正害): Adjacent pillars with harm relationship
            # Remote Harm (遥害): Non-adjacent pillars with harm relationship
            if six_hai_map.get(b1) == b2:
                active_hai.append(
                    {
                        "组合": f"{p1_n}-{p2_n}",
                        "组合明细": {p1_n: b1, p2_n: b2},
                        "紧贴": is_adjacent,
                        "状态": "正害" if is_adjacent else "遥害",
                    }
                )

            # 3. Six Destructions (六破) - Show all, but label by proximity
            # Direct Destruction (正破): Adjacent pillars with destruction relationship
            # Remote Destruction (遥破): Non-adjacent pillars with destruction relationship
            if six_po_map.get(b1) == b2:
                active_po.append(
                    {
                        "组合": f"{p1_n}-{p2_n}",
                        "组合明细": {p1_n: b1, p2_n: b2},
                        "紧贴": is_adjacent,
                        "状态": "正破" if is_adjacent else "遥破",
                    }
                )

            # 4. Dark Harmonies (暗合) - Underground Attractions
            # Note: These are positive, so we keep them regardless of adjacency
            if an_he_map.get(b1) == b2:
                active_an_he.append(
                    {"组合": f"{p1_n}-{p2_n}", "组合明细": {p1_n: b1, p2_n: b2}}
                )

            # 5. Three Punishments (三刑)
            # Note: Punishments are treated with high quality standards here.
            # Self-punishment can occur anywhere in chart, but standard punishments
            # require adjacency for practical relevance.
            # 无恩之刑 and 恃势之刑 are handled by GLOBAL CHECK below (to avoid duplicates)
            for group in san_xing_groups:
                if group["name"] == "自刑":
                    # Self-punishment: Only trigger if same branch appears twice
                    if b1 == b2 and b1 in group["zhis"]:
                        active_xing.append(
                            {
                                "类型": "自刑",
                                "组合": f"{p1_n}-{p2_n}",
                                "组合明细": {p1_n: b1, p2_n: b2},
                                "紧贴": is_adjacent,
                                "状态": "正刑" if is_adjacent else "遥刑",
                            }
                        )
                elif group["name"] == "无礼之刑":
                    if b1 in group["zhis"] and b2 in group["zhis"]:
                        active_xing.append(
                            {
                                "类型": "无礼之刑",
                                "组合": f"{p1_n}-{p2_n}",
                                "组合明细": {p1_n: b1, p2_n: b2},
                                "紧贴": is_adjacent,
                                "状态": "正刑" if is_adjacent else "遥刑",
                            }
                        )

    # GLOBAL CHECK FOR TRIPLE PUNISHMENTS (无恩之刑, 恃势之刑)
    # These are checked chart-wide, not pairwise, to detect complete/half patterns
    unique_zhis_set = set(zhis)
    for group in san_xing_groups:
        if group["name"] in ["无恩之刑", "恃势之刑"]:
            # Count how many of the 3 branches are present in the chart
            matches = [z for z in group["zhis"] if z in unique_zhis_set]

            if len(matches) == 3:
                # TRIPLE PUNISHMENT COMPLETE
                active_xing.append(
                    {
                        "类型": group["name"],
                        "状态": "三刑全",
                        "组合": "-".join(
                            [
                                pillar_names[k]
                                for k, zhi in enumerate(zhis)
                                if zhi in matches
                            ]
                        ),
                        "组合明细": {
                            pillar_names[k]: zhi
                            for k, zhi in enumerate(zhis)
                            if zhi in matches
                        },
                        "说明": "三刑支位全见，主能量系统剧烈变动",
                    }
                )
            elif len(matches) == 2:
                # HALF PUNISHMENT
                missing = [z for z in group["zhis"] if z not in unique_zhis_set][0]
                active_xing.append(
                    {
                        "类型": group["name"],
                        "状态": "半刑",
                        "组合": "-".join(
                            [
                                pillar_names[k]
                                for k, zhi in enumerate(zhis)
                                if zhi in matches
                            ]
                        ),
                        "组合明细": {
                            pillar_names[k]: zhi
                            for k, zhi in enumerate(zhis)
                            if zhi in matches
                        },
                        "邀位": missing,
                        "说明": f"半刑局，逢{missing}岁运需注意能量波动",
                    }
                )

    return {
        "能量系统": {
            "共鸣": {
                "六合特性": potential_map,
                "六合实际": active_six_he,
                "三合实际": active_san_he,
                "暗合实际": active_an_he,
                "三会实际": active_san_hui,
            },
            "冲突": {
                "六冲实际": active_chong,
                "六害实际": active_hai,
                "三刑实际": active_xing,
                "六破实际": active_po,
            },
        }
    }


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from datetime import datetime
    from lunar_python import Solar
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
    from src.astronomer_calculations.bazi_pillars import get_bazi_pillars

    # python -m src.astronomer_calculations.branch_energy

    # # Desmond's birthday example
    # solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    # datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    # tst_birthday, _ = get_true_solar_time(
    #     datetime_birthday, 1.3253, 103.808053
    # )  # Get true solar time

    # Sample birthday example
    solar_birthday = Solar.fromYmdHms(1988, 2, 14, 10, 00, 0)  # Create solar date
    datetime_birthday = datetime(1988, 2, 14, 10, 00, 0)  # Create datetime object
    tst_birthday, _ = get_true_solar_time(
        datetime_birthday, 1.3253, 103.808053
    )  # Get true solar time

    print("阳历生日: " + solar_birthday.toYmdHms())
    print("真太阳时生日: " + tst_birthday.toYmdHms())

    print("")
    print("八字")
    bazi_json = get_bazi_pillars(tst_birthday.getLunar())
    print(f"八字: {bazi_json}")

    lunar_birthday = tst_birthday.getLunar()  # Convert to lunar calendar

    # Get Six Harmonies (六合)
    six_harmonies_result = get_branch_energy(lunar_birthday)

    print(f"\n--- JSON Output for LLM ---")
    print(json.dumps(six_harmonies_result, ensure_ascii=False, indent=2))
