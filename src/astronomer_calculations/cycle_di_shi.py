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
# LIFE STAGE CALCULATION (地势) - Based on Natal Day Stem and Cycle Branch
# ============================================================================

def get_di_shi(natal_day_stem: str, cycle_branch: str) -> str:
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
    if natal_day_stem not in DI_SHI_TABLE:
        return "Unknown"

    stem_table = DI_SHI_TABLE[natal_day_stem]
    return stem_table.get(cycle_branch, "Unknown")


# # Helper dictionaries for string-to-Enum conversion
# STR_STEM = {s.value: s for s in Stem}
# STR_BRANCH = {b.value: b for b in Branch}