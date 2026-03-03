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
        "年": bazi.getYearZhi(),
        "月": bazi.getMonthZhi(),
        "日": bazi.getDayZhi(),
        "时": bazi.getTimeZhi(),
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
            potential_map[name] = {"合": partner, "化": elem}

    for i in range(len(zhis)):
        for j in range(i + 1, len(zhis)):
            if six_he_map.get(zhis[i]) == zhis[j]:
                pair_key = (zhis[i], zhis[j])
                elem = six_he_element_map.get(pair_key, {}).get("primary", "")
                active_six_he.append(
                    {
                        "组合": f"{pillar_names[i]}-{pillar_names[j]}",
                        "地支": [zhis[i], zhis[j]],
                        "结果": f"化{elem}",
                    }
                )

    # Three Harmonies (Triangles)
    for element, group in san_he_groups.items():
        matches = [
            {"name": pillar_names[k], "zhi": zhis[k]}
            for k, zhi in enumerate(zhis)
            if zhi in group
        ]
        unique_zhis = set(m["zhi"] for m in matches)
        if len(unique_zhis) >= 2:
            status = "三合全局" if len(unique_zhis) == 3 else "半合局"
            active_san_he.append(
                {
                    "元素": element,
                    "组合": "-".join([m["name"] for m in matches]),
                    "地支": [m["zhi"] for m in matches],
                    "状态": status,
                }
            )

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
                    "地支": [m["zhi"] for m in matches],
                    "状态": status,
                }
            )

    # --- 2. CONFLICT (Clash, Harm, Punishment) + 1 Harmony (暗合) ---
    active_chong = []
    active_hai = []
    active_xing = []
    active_po = []
    active_an_he = []

    for i in range(len(zhis)):
        for j in range(i + 1, len(zhis)):
            b1, b2 = zhis[i], zhis[j]
            p1_n, p2_n = pillar_names[i], pillar_names[j]

            # 六冲 Clashes (Direct Opposition)
            if six_chong_map.get(b1) == b2:
                active_chong.append({"组合": f"{p1_n}-{p2_n}", "地支": [b1, b2]})

            # Harms (Interference)
            if six_hai_map.get(b1) == b2:
                active_hai.append({"组合": f"{p1_n}-{p2_n}", "地支": [b1, b2]})

            # 六破 (Destructive Friction) - Subtle but significant wear and tear on the branches' energy
            if six_po_map.get(b1) == b2:
                active_po.append({"组合": f"{p1_n}-{p2_n}", "地支": [b1, b2]})

            # 暗合 Dark Harmonies (Underground Attractions)
            if an_he_map.get(b1) == b2:
                active_an_he.append({"组合": f"{p1_n}-{p2_n}", "地支": [b1, b2]})

            # 三刑 Punishments (Friction)
            for group in san_xing_groups:
                if group["name"] == "自刑":
                    # Only trigger if the same branch appears twice (b1 == b2)
                    if b1 == b2 and b1 in group["zhis"]:
                        active_xing.append(
                            {
                                "类型": group["name"],
                                "组合": f"{p1_n}-{p2_n}",
                                "地支": [b1, b2],
                            }
                        )
                else:
                    # Standard Punishments (寅巳申, 丑戌未, 子卯)
                    # These are NOT self-punishments, so they can be different branches
                    if b1 in group["zhis"] and b2 in group["zhis"]:
                        active_xing.append(
                            {
                                "类型": group["name"],
                                "组合": f"{p1_n}-{p2_n}",
                                "地支": [b1, b2],
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

    # python -m src.astronomer_calculations.branch_energy

    # # Desmond's birthday example
    # solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    # datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    # tst_birthday, _ = get_true_solar_time(
    #     datetime_birthday, 1.3253, 103.808053
    # )  # Get true solar time

    # Sample birthday example
    solar_birthday = Solar.fromYmdHms(1996, 8, 20, 9, 30, 0)  # Create solar date
    datetime_birthday = datetime(1996, 8, 20, 9, 30, 0)  # Create datetime object
    tst_birthday, _ = get_true_solar_time(
        datetime_birthday, 1.3253, 103.808053
    )  # Get true solar time

    print("阳历生日: " + solar_birthday.toYmdHms())
    print("真太阳时生日: " + tst_birthday.toYmdHms())

    lunar_birthday = tst_birthday.getLunar()  # Convert to lunar calendar

    # Get Six Harmonies (六合)
    six_harmonies_result = get_branch_energy(lunar_birthday)

    print(f"\n--- JSON Output for LLM ---")
    print(json.dumps(six_harmonies_result, ensure_ascii=False, indent=2))
