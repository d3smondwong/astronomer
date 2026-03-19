"""
Shen Sha (神煞) Calculation Module - Class-Based Architecture

This module calculates and identifies Shen Sha (Auspicious & Inauspicious Stars) in BaZi charts.
Shen Sha are additional spiritual stars used in Chinese astrology to provide deeper insights
into a person's character, destiny, relationships, and challenges.

Key Methodology:
- Year Branch (年系) → Relationships, social connections
- Month Branch (月系) → Virtues, protection, seasonal influences
- Day Branch (日系) → Command capacity, spiritual gifts, movement
- Day Stem (Personal) → Career, talent, wealth, personality
- Year Stem (Secondary) → Heavenly Noble (天乙贵人) only
- Pillar Combinations (杂项) → Special voids, seasonal formations

Architecture:
- ShenShaCalculator class encapsulates full natal chart analysis
- Supports both natal charts and cycle stem-branch lookups (da yun, xiao yun, etc.)
- Gender-dependent calculations (元辰, for example)

Public API:
    get_shen_sha(lunar_birthday, gender): Main entry point for natal chart analysis.

    Returns: {
        "神煞": {
            "柱位神煞": {
                "年柱": {"神煞": [...]},
                "月柱": {"神煞": [...]},
                "日柱": {"神煞": [...]},
                "时柱": {"神煞": [...]}
            },
            "系统神煞": {
                "互禄明细": [...],       # Mutual lu (互禄) pairs
                "虚邀禄": [...],         # Virtual lu (拱禄/夹禄) formations
                "虚邀贵": [...],         # Virtual noble (拱贵/夹贵) formations
                "禄元互换": [...],       # Present only if activated
                "进退真禄": [...],       # Present only if activated
                "德秀贵人": {...},       # Present only if activated
                "暗禄": {...}            # Present only if activated
            }
        }
    }

    ShenShaCalculator.get_cycle_shen_sha(cycle_stem, cycle_branch): Cycle analysis.

    Returns: {
        "日系": [...],   # Day-branch and day-stem derived stars
        "年系": [...],   # Year-branch derived stars
        "月系": [...],   # Month-branch derived stars
        "杂项": [...]    # Pillar-specific and seasonal formations
    }
"""

from __future__ import annotations

import json
from typing import Dict, List, Any, Optional

from lunar_python import Solar, Lunar
from lunar_python.util import LunarUtil
from datetime import datetime
from src.astronomer_calculations.solar_lunar_time import get_true_solar_time


# ============================================================================
# DATA LAYER - ALL LOOKUP TABLES & MAPPINGS
# ============================================================================

# --- HEAVENLY STEMS & EARTHLY BRANCHES ---
# Constants for elegant type checking
HEAVENLY_STEMS = frozenset("甲乙丙丁戊己庚辛壬癸")
EARTHLY_BRANCHES = frozenset("子丑寅卯辰巳午未申酉戌亥")

# --- STEM & BRANCH PARTNERSHIPS ---
# Yin-Yang stem partnerships for derived stars (天德合, 月德合, 阳刃伏藏)
stem_partners = {
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

# --- BATH POSITION (DAY STEM → BATH BRANCH) ---
# Maps Day Master stem to its "Bath" (沐浴) stage
# Used for 沐浴桃花 activation (Peach Blossom at Bath position = amplified)
bath_position = {
    "甲": "子",
    "乙": "巳",
    "丙": "卯",
    "丁": "申",
    "戊": "卯",
    "己": "申",
    "庚": "午",
    "辛": "亥",
    "壬": "酉",
    "癸": "寅",
}

# --- SEASONAL MAPPING ---
# Maps month branch to Chinese season
seasons_map = {
    "寅": "春",
    "卯": "春",
    "辰": "春",
    "巳": "夏",
    "午": "夏",
    "未": "夏",
    "申": "秋",
    "酉": "秋",
    "戌": "秋",
    "亥": "冬",
    "子": "冬",
    "丑": "冬",
}

# --- 元辰 (YUAN CHEN) - GENDER & YEAR YIN/YANG DEPENDENT ---
# Formula: Year Branch + (Gender & Year Yin/Yang)
# Yang year + Male OR Yin year + Female → first element
# Yin year + Male OR Yang year + Female → second element
yuan_chen_map = {
    "子": ("未", "巳"),
    "丑": ("申", "午"),
    "寅": ("酉", "未"),
    "卯": ("戌", "申"),
    "辰": ("亥", "酉"),
    "巳": ("子", "戌"),
    "午": ("丑", "亥"),
    "未": ("寅", "子"),
    "申": ("卯", "丑"),
    "酉": ("辰", "寅"),
    "戌": ("巳", "卯"),
    "亥": ("午", "辰"),
}

# --- YEAR BRANCH BASED SHENS ---
year_earthly_branches_shens = {
    "龙德": {
        "子": "未",
        "丑": "申",
        "寅": "酉",
        "卯": "戌",
        "辰": "亥",
        "巳": "子",
        "午": "丑",
        "未": "寅",
        "申": "卯",
        "酉": "辰",
        "戌": "巳",
        "亥": "午",
    },
    # --- ROMANCE & SOCIAL ---
    "红鸾": {
        "子": "卯",
        "丑": "寅",
        "寅": "丑",
        "卯": "子",
        "辰": "亥",
        "巳": "戌",
        "午": "酉",
        "未": "申",
        "申": "未",
        "酉": "午",
        "戌": "巳",
        "亥": "辰",
    },
    "天喜": {
        "子": "酉",
        "丑": "申",
        "寅": "未",
        "卯": "午",
        "辰": "巳",
        "巳": "辰",
        "午": "卯",
        "未": "寅",
        "申": "丑",
        "酉": "子",
        "戌": "亥",
        "亥": "戌",
    },
    "桃花": {
        "子": "酉",
        "丑": "午",
        "寅": "卯",
        "卯": "子",
        "辰": "酉",
        "巳": "午",
        "午": "卯",
        "未": "子",
        "申": "酉",
        "酉": "午",
        "戌": "卯",
        "亥": "子",
    },
    # --- CHALLENGING / SHA ---
    "孤辰": {
        "子": "寅",
        "丑": "寅",
        "寅": "巳",
        "卯": "巳",
        "辰": "巳",
        "巳": "申",
        "午": "申",
        "未": "申",
        "申": "亥",
        "酉": "亥",
        "戌": "亥",
        "亥": "寅",
    },
    "寡宿": {
        "子": "戌",
        "丑": "戌",
        "寅": "丑",
        "卯": "丑",
        "辰": "丑",
        "巳": "辰",
        "午": "辰",
        "未": "辰",
        "申": "未",
        "酉": "未",
        "戌": "未",
        "亥": "戌",
    },
    "大耗": {
        "子": "午",
        "丑": "未",
        "寅": "申",
        "卯": "酉",
        "辰": "戌",
        "巳": "亥",
        "午": "子",
        "未": "丑",
        "申": "寅",
        "酉": "卯",
        "戌": "辰",
        "亥": "巳",
    },
    "吊客": {
        "子": "戌",
        "丑": "亥",
        "寅": "子",
        "卯": "丑",
        "辰": "寅",
        "巳": "卯",
        "午": "辰",
        "未": "巳",
        "申": "午",
        "酉": "未",
        "戌": "申",
        "亥": "酉",
    },
    "丧门": {
        "子": "寅",
        "丑": "卯",
        "寅": "辰",
        "卯": "巳",
        "辰": "午",
        "巳": "未",
        "午": "申",
        "未": "酉",
        "申": "戌",
        "酉": "亥",
        "戌": "子",
        "亥": "丑",
    },
    "白虎": {
        "子": "申",
        "丑": "酉",
        "寅": "戌",
        "卯": "亥",
        "辰": "子",
        "巳": "丑",
        "午": "寅",
        "未": "卯",
        "申": "辰",
        "酉": "巳",
        "戌": "午",
        "亥": "未",
    },
    "卷舌": {
        "子": "酉",
        "丑": "戌",
        "寅": "亥",
        "卯": "子",
        "辰": "丑",
        "巳": "寅",
        "午": "卯",
        "未": "辰",
        "申": "巳",
        "酉": "午",
        "戌": "未",
        "亥": "申",
    },
    "披麻": {
        "子": "酉",
        "丑": "戌",
        "寅": "亥",
        "卯": "子",
        "辰": "丑",
        "巳": "寅",
        "午": "卯",
        "未": "辰",
        "申": "巳",
        "酉": "午",
        "戌": "未",
        "亥": "申",
    },
    "勾绞煞": {
        "子": "卯",
        "丑": "辰",
        "寅": "巳",
        "卯": "午",
        "辰": "未",
        "巳": "申",
        "午": "酉",
        "未": "戌",
        "申": "亥",
        "酉": "子",
        "戌": "丑",
        "亥": "寅",
    },
    "披头": {
        "子": "酉",
        "丑": "戌",
        "寅": "亥",
        "卯": "午",
        "辰": "未",
        "巳": "申",
        "午": "酉",
        "未": "戌",
        "申": "亥",
        "酉": "子",
        "戌": "丑",
        "亥": "寅",
    },
    "破碎": {
        "子": "巳",
        "丑": "丑",
        "寅": "酉",
        "卯": "巳",
        "辰": "丑",
        "巳": "酉",
        "午": "巳",
        "未": "丑",
        "申": "酉",
        "酉": "巳",
        "戌": "丑",
        "亥": "酉",
    },
}

# --- MONTH BRANCH BASED SHENS ---
month_earthly_branches_shens = {
    # --- VIRTUES ---
    "天德": {
        "子": "巳",
        "丑": "庚",
        "寅": "丁",
        "卯": "申",
        "辰": "壬",
        "巳": "辛",
        "午": "亥",
        "未": "甲",
        "申": "癸",
        "酉": "寅",
        "戌": "丙",
        "亥": "乙",
    },
    "月德": {
        "子": "壬",
        "丑": "庚",
        "寅": "丙",
        "卯": "甲",
        "辰": "壬",
        "巳": "庚",
        "午": "丙",
        "未": "甲",
        "申": "壬",
        "酉": "庚",
        "戌": "丙",
        "亥": "甲",
    },
    # --- PROTECTION & HEALTH ---
    "天医": {
        "子": "亥",
        "丑": "子",
        "寅": "丑",
        "卯": "寅",
        "辰": "卯",
        "巳": "辰",
        "午": "巳",
        "未": "午",
        "申": "未",
        "酉": "申",
        "戌": "酉",
        "亥": "戌",
    },
    "月空": {
        "寅": "壬",
        "卯": "庚",
        "辰": "丙",
        "巳": "甲",
        "午": "壬",
        "未": "庚",
        "申": "丙",
        "酉": "甲",
        "戌": "壬",
        "亥": "庚",
        "子": "丙",
        "丑": "甲",
    },
    "血刃": {
        "子": "戌",
        "丑": "酉",
        "寅": "申",
        "卯": "未",
        "辰": "午",
        "巳": "巳",
        "午": "辰",
        "未": "卯",
        "申": "寅",
        "酉": "丑",
        "戌": "子",
        "亥": "亥",
    },
    # --- SEASONAL ---
    "天赦": {"春": "戊寅", "夏": "甲午", "秋": "戊申", "冬": "甲子"},
}

# --- DAY BRANCH BASED SHENS ---
day_earthly_branches_shens = {
    "将星": {
        "子": "子",
        "丑": "酉",
        "寅": "午",
        "卯": "卯",
        "辰": "子",
        "巳": "酉",
        "午": "午",
        "未": "卯",
        "申": "子",
        "酉": "酉",
        "戌": "午",
        "亥": "卯",
    },
    "华盖": {
        "子": "辰",
        "丑": "丑",
        "寅": "戌",
        "卯": "未",
        "辰": "辰",
        "巳": "丑",
        "午": "戌",
        "未": "未",
        "申": "辰",
        "酉": "丑",
        "戌": "戌",
        "亥": "未",
    },
    "驿马": {
        "子": "寅",
        "丑": "亥",
        "寅": "申",
        "卯": "巳",
        "辰": "寅",
        "巳": "亥",
        "午": "申",
        "未": "巳",
        "申": "寅",
        "酉": "亥",
        "戌": "申",
        "亥": "巳",
    },
    "劫煞": {
        "子": "巳",
        "丑": "寅",
        "寅": "亥",
        "卯": "申",
        "辰": "巳",
        "巳": "寅",
        "午": "亥",
        "未": "申",
        "申": "巳",
        "酉": "寅",
        "戌": "亥",
        "亥": "申",
    },
    "亡神": {
        "子": "亥",
        "丑": "申",
        "寅": "巳",
        "卯": "寅",
        "辰": "亥",
        "巳": "申",
        "午": "巳",
        "未": "寅",
        "申": "亥",
        "酉": "申",
        "戌": "巳",
        "亥": "寅",
    },
    "桃花": {
        "子": "酉",
        "丑": "午",
        "寅": "卯",
        "卯": "子",
        "辰": "酉",
        "巳": "午",
        "午": "卯",
        "未": "子",
        "申": "酉",
        "酉": "午",
        "戌": "卯",
        "亥": "子",
    },
}

# --- HEAVENLY STEM BASED SHENS (STEM-UNIVERSAL: PRIMARY DAY MASTER, SECONDARY YEAR STEM) ---
# Maps any stem (甲-癸) to their derived stars (nobles, academics, wealth, etc.)
# Used by both _calc_day_stem_shens() and _calc_year_stem_nobles()
heavenly_stem_shens = {
    # --- NOBLES & ACADEMICS ---
    "昼天乙": {
        "甲": "丑",
        "乙": "申",
        "丙": "亥",
        "丁": "酉",
        "戊": "丑",
        "己": "子",
        "庚": "未",
        "辛": "午",
        "壬": "卯",
        "癸": "巳",
    },
    "夜天乙": {
        "甲": "未",
        "乙": "子",
        "丙": "酉",
        "丁": "亥",
        "戊": "未",
        "己": "申",
        "庚": "丑",
        "辛": "寅",
        "壬": "巳",
        "癸": "卯",
    },
    "文昌": {
        "甲": "巳",
        "乙": "午",
        "丙": "申",
        "丁": "酉",
        "戊": "申",
        "己": "酉",
        "庚": "亥",
        "辛": "子",
        "壬": "寅",
        "癸": "卯",
    },
    "学堂": {
        "甲": "亥",
        "乙": "午",
        "丙": "寅",
        "丁": "酉",
        "戊": "寅",
        "己": "酉",
        "庚": "巳",
        "辛": "子",
        "壬": "申",
        "癸": "卯",
    },
    "太极": {
        "甲": "子午",
        "乙": "子午",
        "丙": "卯酉",
        "丁": "卯酉",
        "戊": "辰戌丑未",
        "己": "辰戌丑未",
        "庚": "寅亥",
        "辛": "寅亥",
        "壬": "巳申",
        "癸": "巳申",
    },
    # --- WEALTH & STATUS ---
    "禄神": {
        "甲": "寅",
        "乙": "卯",
        "丙": "巳",
        "丁": "午",
        "戊": "巳",
        "己": "午",
        "庚": "申",
        "辛": "酉",
        "壬": "亥",
        "癸": "子",
    },
    "金舆": {
        "甲": "辰",
        "乙": "巳",
        "丙": "未",
        "丁": "申",
        "戊": "未",
        "己": "申",
        "庚": "戌",
        "辛": "亥",
        "壬": "丑",
        "癸": "寅",
    },
    "国印": {
        "甲": "戌",
        "乙": "亥",
        "丙": "丑",
        "丁": "寅",
        "戊": "丑",
        "己": "寅",
        "庚": "辰",
        "辛": "巳",
        "壬": "未",
        "癸": "申",
    },
    "福星": {
        "甲": "寅子",
        "乙": "亥丑",
        "丙": "戌申",
        "丁": "未巳",
        "戊": "申",
        "己": "未",
        "庚": "午",
        "辛": "巳",
        "壬": "辰",
        "癸": "卯",
    },
    # --- PERSONALITY & TALENT ---
    "词馆": {
        "甲": ["庚寅"],
        "乙": ["辛卯"],
        "丙": ["乙巳"],
        "丁": ["甲午", "巳"],
        "戊": ["乙巳", "庚申"],
        "己": ["甲午"],
        "庚": ["壬申"],
        "辛": ["癸酉"],
        "壬": ["丁亥"],
        "癸": ["丙子"],
    },
    "红艳": {
        "甲": "午",
        "乙": "午",
        "丙": "寅",
        "丁": "未",
        "戊": "辰",
        "己": "辰",
        "庚": "戌",
        "辛": "酉",
        "壬": "子",
        "癸": "申",
    },
    "天厨": {
        "甲": "巳",
        "乙": "午",
        "丙": "巳",
        "丁": "午",
        "戊": "申",
        "己": "酉",
        "庚": "亥",
        "辛": "子",
        "壬": "寅",
        "癸": "卯",
    },
    "飞刃": {
        "甲": "酉",
        "乙": "戌",
        "丙": "子",
        "丁": "丑",
        "戊": "子",
        "己": "丑",
        "庚": "卯",
        "辛": "辰",
        "壬": "午",
        "癸": "巳",
    },
    "天官贵人": {
        "甲": "未",
        "乙": "辰",
        "丙": "巳",
        "丁": "申",
        "戊": "辰",
        "己": "卯",
        "庚": "亥",
        "辛": "酉",
        "壬": "寅",
        "癸": "午",
    },
    "阳刃": {
        "甲": "卯",
        "丙": "午",
        "戊": "午",
        "庚": "酉",
        "壬": "子",
    },
    "阴刃": {
        "乙": "寅",
        "丁": "巳",
        "己": "巳",
        "辛": "申",
        "癸": "亥",
    }
}

# --- PILLAR SPECIAL FORMATIONS & VOIDS ---
pillar_shens = {
    # --- VOID ---
    "空亡": {
        "甲子": "戌亥",
        "乙丑": "戌亥",
        "丙寅": "戌亥",
        "丁卯": "戌亥",
        "戊辰": "戌亥",
        "己巳": "戌亥",
        "庚午": "戌亥",
        "辛未": "戌亥",
        "壬申": "戌亥",
        "癸酉": "戌亥",
        "甲戌": "申酉",
        "乙亥": "申酉",
        "丙子": "申酉",
        "丁丑": "申酉",
        "戊寅": "申酉",
        "己卯": "申酉",
        "庚辰": "申酉",
        "辛巳": "申酉",
        "壬午": "申酉",
        "癸未": "申酉",
        "甲申": "午未",
        "乙酉": "午未",
        "丙戌": "午未",
        "丁亥": "午未",
        "戊子": "午未",
        "己丑": "午未",
        "庚寅": "午未",
        "辛卯": "午未",
        "壬辰": "午未",
        "癸巳": "午未",
        "甲午": "辰巳",
        "乙未": "辰巳",
        "丙申": "辰巳",
        "丁酉": "辰巳",
        "戊戌": "辰巳",
        "己亥": "辰巳",
        "庚子": "辰巳",
        "辛丑": "辰巳",
        "壬寅": "辰巳",
        "癸卯": "辰巳",
        "甲辰": "寅卯",
        "乙巳": "寅卯",
        "丙午": "寅卯",
        "丁未": "寅卯",
        "戊申": "寅卯",
        "己酉": "寅卯",
        "庚戌": "寅卯",
        "辛亥": "寅卯",
        "壬子": "寅卯",
        "癸丑": "寅卯",
        "甲寅": "子丑",
        "乙卯": "子丑",
        "丙辰": "子丑",
        "丁巳": "子丑",
        "戊午": "子丑",
        "己未": "子丑",
        "庚申": "子丑",
        "辛酉": "子丑",
        "壬戌": "子丑",
        "癸亥": "子丑",
    },
    # --- PILLAR SPECIFIC ---
    "阴阳差错": [
        "丙子",
        "丁丑",
        "戊寅",
        "辛卯",
        "壬辰",
        "癸巳",
        "丙午",
        "丁未",
        "戊申",
        "辛酉",
        "壬戌",
        "癸亥",
    ],
    "十恶大败": [
        "甲辰",
        "乙巳",
        "丙申",
        "丁亥",
        "戊戌",
        "己丑",
        "庚辰",
        "辛巳",
        "壬申",
        "癸亥",
    ],
    "魁罡": ["庚辰", "庚戌", "戊戌", "壬辰"],
    "扩展魁罡": ["戊辰", "壬戌"],
    "金神": ["癸酉", "己巳", "乙丑"],
    "福禄双美": ["丁卯", "癸未", "甲寅"],
    "十灵": [
        "甲辰",
        "乙亥",
        "丙辰",
        "丁酉",
        "戊午",
        "庚戌",
        "庚寅",
        "辛亥",
        "壬寅",
        "癸未",
    ],
    "四废": {
        "春": ["庚申", "辛酉"],
        "夏": ["壬子", "癸亥"],
        "秋": ["甲寅", "乙卯"],
        "冬": ["丙午", "丁未"],
    },
}

# --- VIRTUES & ELEGANCE STARS ---
# 德秀贵人 - Virtue & Elegance Noble (month branch defines element frame, checks for matching stems)
dexiu_map = {
    "寅": "丙丁戊癸",  # Fire frame (南方)
    "午": "丙丁戊癸",
    "戌": "丙丁戊癸",
    "申": "壬癸戊丙辛甲己",  # Water frame (北方)
    "子": "壬癸戊丙辛甲己",
    "辰": "壬癸戊丙辛甲己",
    "亥": "甲乙丁壬",  # Wood frame (東方)
    "卯": "甲乙丁壬",
    "未": "甲乙丁壬",
    "巳": "庚辛乙",  # Metal frame (西方)
    "酉": "庚辛乙",
    "丑": "庚辛乙",
}

# --- DARK LU (AN LU) ---
# 暗禄 = 六合 partner of 禄神
# Formula: Day Master's 禄神 branch → its 六合 partner
an_lu_map = {
    "甲": "亥",  # 甲禄在寅, 寅亥合
    "乙": "戌",  # 乙禄在卯, 卯戌合
    "丙": "申",  # 丙禄在巳, 巳申合
    "丁": "未",  # 丁禄在午, 午未合
    "戊": "申",  # 戊禄在巳, 巳申合
    "己": "未",  # 己禄在午, 午未合
    "庚": "巳",  # 庚禄在申, 申巳合
    "辛": "辰",  # 辛禄在酉, 酉辰合
    "壬": "寅",  # 壬禄在亥, 亥寅合
    "癸": "丑",  # 癸禄在子, 子丑合
}

# --- EXCLUSION RULES ---
# These stars derive from a pillar and should NOT appear on that same pillar
SELF_EXCLUSION_STARS = {
    "桃花",  # Year & Day branch derived; not on year/day pillar
    "孤辰",  # Year branch derived; not on year pillar
    "寡宿",  # Year branch derived; not on year pillar
    "驿马",  # Day branch derived; not on day pillar
    "劫煞",  # Day branch derived; not on day pillar
    "亡神",  # Day branch derived; not on day pillar
    "将星",  # Day branch derived; not on day pillar
    "华盖",  # Day branch derived; not on day pillar
}

# --- NAYIN ELEMENT EXTRACTION ---
# All Nayin names follow the pattern: [descriptor][element]
# where element is always one of: 金, 木, 水, 火, 土
# Rule: Extract the last character (the element) from the Nayin name
# This covers all 60 Jiazi Nayin without maintaining a large lookup map
def nayin_to_element(nayin_name: str) -> str:
    """
    Extract element from Nayin name by its final character.

    Args:
        nayin_name: Full Nayin name (e.g., "海中金", "大林木")

    Returns:
        Element (金/木/水/火/土) or empty string if not found
    """
    if not nayin_name:
        return ""
    last_char = nayin_name[-1]
    element_map = {"金": "金", "木": "木", "水": "水", "火": "火", "土": "土"}
    return element_map.get(last_char, "")

branch_six_combinations = {
    "子": "丑", "丑": "子",
    "寅": "亥", "亥": "寅",
    "卯": "戌", "戌": "卯",
    "辰": "酉", "酉": "辰",
    "巳": "申", "申": "巳",
    "午": "未", "未": "午",
}

# ============================================================================
# MODULE-LEVEL HELPER
# ============================================================================


def add_shen(
    pillar_idx: int, shen_name: str, strs: List[str], all_found_shens: List[str]
) -> None:
    """
    Add shen to a pillar and track unique shens.

    Args:
        pillar_idx (int): Pillar index (0=Year, 1=Month, 2=Day, 3=Hour)
        shen_name (str): Name of the shen to add
        strs (list): Accumulator for per-pillar stars
        all_found_shens (list): Accumulator for unique stars
    """
    if shen_name not in strs[pillar_idx]:
        strs[pillar_idx] = f"{strs[pillar_idx]} {shen_name}".strip()
        if shen_name not in all_found_shens:
            all_found_shens.append(shen_name)


# ============================================================================
# SHEN SHA CALCULATOR CLASS
# ============================================================================


class ShenShaCalculator:
    """
    Encapsulates all shen sha calculations for a BaZi natal chart.

    Supports both:
    - Natal chart analysis: calculate()
    - Cycle (da yun, xiao yun, liu nian, liu yue) analysis: get_cycle_shen_sha(cycle_stem, cycle_branch)

    Architecture:
    - __init__ extracts and caches all natal state (8-char, gender, season, etc.)
    - _from_natal_dict() constructs from a pre-parsed natal_chart dict (used by cycle callers)
    - Shared derived state used by all _calc_*() methods (no parameter passing)
    - ~20 _calc_*() methods compute specific shen groups, organized by derivation source
    - calculate() orchestrates all _calc_*() methods and caches the result
    - get_cycle_shen_sha() checks a single cycle pillar against cached natal state

    Gender convention: 0 = Female, 1 = Male (consistent with BaZi library)
    """

    def __init__(self, lunar_birthday: Lunar, gender: int) -> None:
        """
        Initialize calculator from lunar birthday and gender.

        Args:
            lunar_birthday (Lunar): Lunar calendar object (from lunar_python)
            gender (int): 0 for Female, 1 for Male

        Raises:
            ValueError: if gender not in (0, 1)
        """
        if gender not in (0, 1):
            raise ValueError(f"gender must be 0 (Female) or 1 (Male), got {gender}")

        self.gender = gender
        self.is_male = gender == 1

        # Cache for calculation results
        self._result_cache: Optional[Dict[str, Any]] = None

        # Extract 8-character from lunar birthday
        baZi = lunar_birthday.getEightChar()
        self.gans = [
            baZi.getYearGan(),
            baZi.getMonthGan(),
            baZi.getDayGan(),
            baZi.getTimeGan(),
        ]
        self.zhis = [
            baZi.getYearZhi(),
            baZi.getMonthZhi(),
            baZi.getDayZhi(),
            baZi.getTimeZhi(),
        ]

        # Initialize derived state
        self._init_derived()

    def _init_derived(self) -> None:
        """
        Compute and cache all derived state from gans & zhis.
        Called by both __init__ and _from_natal_dict.
        """
        self.me = self.gans[2]  # Day Master (Day Stem)
        self.year_stem = self.gans[0]
        self.year_pillar = self.gans[0] + self.zhis[0]
        self.day_pillar = self.gans[2] + self.zhis[2]
        self.hour_pillar = self.gans[3] + self.zhis[3]
        self.birth_season = seasons_map.get(self.zhis[1])

        # Year pillar's Nayin element (for 天罗地网 calculation)
        self.year_nayin = nayin_to_element(LunarUtil.NAYIN.get(self.year_pillar, ""))

        # Year yin/yang determined by Year Stem (not Branch)
        # Yang stems: 甲, 丙, 戊, 庚, 壬; Yin stems: 乙, 丁, 己, 辛, 癸
        _yang_stems = {"甲", "丙", "戊", "庚", "壬"}
        self.is_yang_year = self.gans[0] in _yang_stems

        # Helper collections
        self.pillar_names = ["年柱", "月柱", "日柱", "时柱"]
        self.branch_order = [
            "子",
            "丑",
            "寅",
            "卯",
            "辰",
            "巳",
            "午",
            "未",
            "申",
            "酉",
            "戌",
            "亥",
        ]

        # Accumulators for natal shens
        self.strs = ["", "", "", ""]
        self.all_found_shens = []

        # Accumulators for relational shens
        self.hu_lu_results = []
        self.jia_gong_lu_results = []
        self.jia_gong_gui_results = []
        self.lu_yuan_results = []          # 禄元互换 results
        self.advancing_retreating_results = []   # 进退真禄 results
        self.de_xiu_result = {}
        self.an_lu_result = {}

        # Cache for cycle shen sha results, keyed by (cycle_stem, cycle_branch)
        self._cycle_cache: Dict[tuple, Dict[str, List[str]]] = {}

    @classmethod
    def _from_natal_dict(
        cls, natal_chart: Dict[str, Dict[str, str]], gender: int
    ) -> "ShenShaCalculator":
        """
        Construct calculator from a pre-parsed natal_chart dictionary.
        Used by cycle calculations (da_yun, xiao_yun, liu_nian, liu_yue).

        Args:
            natal_chart (dict): {
                "year": {"stem": str, "branch": str},
                "month": {"stem": str, "branch": str},
                "day": {"stem": str, "branch": str},
                "hour": {"stem": str, "branch": str},
            }
            gender (int): 0 for Female, 1 for Male

        Returns:
            ShenShaCalculator instance
        """
        instance = cls.__new__(cls)
        instance.gender = gender
        instance.is_male = gender == 1
        instance.gans = [
            natal_chart[p]["stem"] for p in ("year", "month", "day", "hour")
        ]
        instance.zhis = [
            natal_chart[p]["branch"] for p in ("year", "month", "day", "hour")
        ]
        instance._init_derived()
        return instance

    def _add_shen(self, pillar_idx: int, shen_name: str) -> None:
        """Convenience wrapper for add_shen using instance accumulators."""
        add_shen(pillar_idx, shen_name, self.strs, self.all_found_shens)

    # ========================================================================
    # SECTION 1: YEAR BRANCH DERIVED STARS (年系)
    # ========================================================================

    def _calc_year_branch_shens(self) -> None:
        """
        Year Branch Derived Stars (年系).

        Derives stars from the Year Branch (年支) and applies them to all 4 pillars.

        Self-Exclusion Rule (Source-Specific):
        - Stars in SELF_EXCLUSION_STARS cannot self-trigger on the Year Pillar (i==0)
        - This prevents a year-derived star from artificially appearing on its source pillar
        - IMPORTANT: These same stars CAN appear on other pillars (Month, Day, Hour)
        - And they CAN appear on the Year Pillar if triggered by a DIFFERENT source
          (e.g., 桃花 from Day Branch can appear on Year Pillar)

        Special Cases:
        - 卷舌, 披麻: Handled separately (same formula as other year shens, but distinct)
        - 元辰: Handled separately (requires gender/yin-yang logic)
        - 桃花: Includes wall classification (墙内/墙外) based on pillar position
        """
        for shen_name, mapping in year_earthly_branches_shens.items():
            # Handle 卷舌 and 披麻 separately (same formula, different stars)
            if shen_name in ("卷舌", "披麻"):
                continue

            lookup = mapping.get(self.zhis[0], "")
            for i in range(4):
                # Self-exclusion: year-branch-derived stars cannot appear on year pillar
                if shen_name in SELF_EXCLUSION_STARS and i == 0:
                    continue

                if self.zhis[i] in lookup:
                    # Special case: Peach Blossom has wall classification
                    if shen_name == "桃花":
                        # Add base star for 沐浴桃花 detection, then add wall-classified variant
                        self._add_shen(i, "桃花")
                        wall_type = "墙内桃花" if i < 2 else "墙外桃花"
                        self._add_shen(i, wall_type)
                    else:
                        self._add_shen(i, shen_name)

    def _calc_yuan_chen(self) -> None:
        """
        元辰 (Origin Star) - Gender and year yin/yang dependent.
        Formula: Year Branch + Gender + Year Yin/Yang → target branch

        Yang year + Male OR Yin year + Female → first tuple element
        Yin year + Male OR Yang year + Female → second tuple element
        """
        if (self.is_yang_year and self.is_male) or (
            not self.is_yang_year and not self.is_male
        ):
            target_branch = yuan_chen_map[self.zhis[0]][0]
        else:
            target_branch = yuan_chen_map[self.zhis[0]][1]

        for i in range(4):
            if self.zhis[i] == target_branch:
                self._add_shen(i, "元辰")

    def _calc_juan_she(self) -> None:
        """
        卷舌 (Curled Tongue / Gossip Sha) - Year branch derived.
        Same formula as 披麻 (3 positions forward) but semantically distinct.
        """
        juan_she_map = year_earthly_branches_shens.get("卷舌", {})
        lookup = juan_she_map.get(self.zhis[0], "")
        for i in range(4):
            # Skip self-exclusion stars on their source pillar
            if "卷舌" in SELF_EXCLUSION_STARS and i == 0:
                continue

            if self.zhis[i] in lookup:
                self._add_shen(i, "卷舌")

    def _calc_pi_ma(self) -> None:
        """
        披麻 (Mourning Garment Sha) - Year branch derived.
        Same formula as 卷舌 (3 positions forward) but semantically distinct.
        """
        pi_ma_map = year_earthly_branches_shens.get("披麻", {})
        lookup = pi_ma_map.get(self.zhis[0], "")
        for i in range(4):
            # Skip self-exclusion stars on their source pillar
            if "披麻" in SELF_EXCLUSION_STARS and i == 0:
                continue

            if self.zhis[i] in lookup:
                self._add_shen(i, "披麻")

    # ========================================================================
    # SECTION 2: MONTH BRANCH DERIVED STARS (月系)
    # ========================================================================

    def _calc_month_branch_shens(self) -> None:
        """
        Generic loop for month_earthly_branches_shens (excluding 天赦).
        Checks branches for 天医 & 血刃; checks stems for virtue stars.
        """
        for shen_name, mapping in month_earthly_branches_shens.items():
            if shen_name == "天赦":  # Handled separately (seasonal pillar check)
                continue

            lookup = mapping.get(self.zhis[1], "")
            if isinstance(lookup, str):
                for i in range(4):
                    # 天医 & 血刃 check branches only
                    if shen_name in ("天医", "血刃"):
                        if self.zhis[i] in lookup:
                            self._add_shen(i, shen_name)
                    # Virtue stars (天德, 月德, 月空) check stems or branches
                    else:
                        if self.gans[i] in lookup or self.zhis[i] in lookup:
                            self._add_shen(i, shen_name)

    def _calc_tian_she(self) -> None:
        """
        天赦 (Heavenly Pardon) - Seasonal full-pillar check.
        Only triggers on specific season + specific pillar combination.
        """
        if not self.birth_season:
            return

        target_pillar = month_earthly_branches_shens["天赦"].get(self.birth_season)
        if not target_pillar:
            return

        for i in range(4):
            if (self.gans[i] + self.zhis[i]) == target_pillar:
                self._add_shen(i, "天赦")

    def _calc_virtue_unions(self):
        """
        天德合 (Heavenly Virtue Union) - Classical formula from 三命通会

        When 天德 is a STEM → partner is the 五合 (five-combination) stem
        When 天德 is a BRANCH → partner is the 六合 (six-combination) branch

        Also handles 月德合 (Month Virtue Union) and 天月德合 (Combined Virtue Union)
        """
        month_branch = self.zhis[1]

        # --- 天德合 (Heavenly Virtue Union) ---
        tian_de_value = month_earthly_branches_shens["天德"].get(month_branch)
        if tian_de_value:
            # Check if tian_de_value is a stem or branch
            if tian_de_value in HEAVENLY_STEMS:  # It's a stem
                partner_stem = stem_partners.get(tian_de_value)
                if partner_stem:
                    for i in range(4):
                        if self.gans[i] == partner_stem:
                            self._add_shen(i, "天德合")
            else:  # It's a branch
                # Get the six-combination partner of the branch
                partner_branch = branch_six_combinations.get(tian_de_value)  # You'll need this map
                if partner_branch:
                    for i in range(4):
                        if self.zhis[i] == partner_branch:
                            self._add_shen(i, "天德合")

        # --- 月德合 (Month Virtue Union) ---
        yue_de_value = month_earthly_branches_shens["月德"].get(month_branch)
        if yue_de_value:
            if yue_de_value in HEAVENLY_STEMS:  # It's always stem
                partner_stem = stem_partners.get(yue_de_value)
                if partner_stem:
                    for i in range(4):
                        if self.gans[i] == partner_stem:
                            self._add_shen(i, "月德合")

        # --- 天月德合 (Combined Virtue Union) ---
        if tian_de_value and yue_de_value:
            # Both are stems and their partners match
            if tian_de_value in HEAVENLY_STEMS and yue_de_value in HEAVENLY_STEMS:
                tian_partner = stem_partners.get(tian_de_value)
                yue_partner = stem_partners.get(yue_de_value)
                if tian_partner and yue_partner and tian_partner == yue_partner:
                    for i in range(4):
                        if self.gans[i] == tian_partner:
                            self._add_shen(i, "天月德合")

    # ========================================================================
    # SECTION 3: DAY BRANCH DERIVED STARS (日系)
    # ========================================================================

    def _calc_day_branch_shens(self) -> None:
        """
        Day Branch Derived Stars (日系).

        Derives stars from the Day Branch (日支) and applies them to all 4 pillars.

        Self-Exclusion Rule (Source-Specific):
        - Stars in SELF_EXCLUSION_STARS cannot self-trigger on the Day Pillar (i==2)
        - This prevents a day-derived star from artificially appearing on its source pillar
        - IMPORTANT: These same stars CAN appear on other pillars (Year, Month, Hour)
        - And they CAN appear on the Day Pillar if triggered by a DIFFERENT source
          (e.g., 桃花 from Year Branch can appear on Day Pillar)

        Special Cases:
        - 桃花: Includes wall classification (墙内/墙外) based on pillar position
        - 沐浴桃花: Detected by checking if 桃花 is already present and branch matches
                   Day Master's bath position
        """
        for shen_name, mapping in day_earthly_branches_shens.items():
            lookup = mapping.get(self.zhis[2], "")
            for i in range(4):
                # Self-exclusion: day-branch-derived stars cannot appear on day pillar
                if shen_name in SELF_EXCLUSION_STARS and i == 2:
                    continue

                if self.zhis[i] in lookup:
                    # Special case: Peach Blossom has wall classification
                    if shen_name == "桃花":
                        # Add base star for 沐浴桃花 detection, then add wall-classified variant
                        self._add_shen(i, "桃花")
                        wall_type = "墙内桃花" if i < 2 else "墙外桃花"
                        self._add_shen(i, wall_type)
                    else:
                        self._add_shen(i, shen_name)

    def _calc_bath_peach_blossom(self) -> None:
        """
        沐浴桃花 (Bath-Activated Peach Blossom).
        Triggers when 桃花 is already present AND the branch is the Day Master's bath position.
        """
        my_bath_branch = bath_position.get(self.me)

        for i in range(4):
            if "桃花" in self.strs[i] and self.zhis[i] == my_bath_branch:
                self._add_shen(i, "沐浴桃花")

    # ========================================================================
    # SECTION 4: DAY STEM DERIVED STARS (PRIMARY PERSONAL, 日系)
    # ========================================================================

    def _calc_day_stem_shens(self) -> None:
        """
        Generic loop for heavenly_stem_shens.
        Most stars check if pillar branch is in the mapped branches.
        词馆 is special: can match full pillar (2 chars) or branch only (1 char).
        """
        for shen_name, mapping in heavenly_stem_shens.items():
            lookup = mapping.get(self.me, "")
            if not lookup:
                continue

            for i in range(4):
                if shen_name == "词馆":
                    # 词馆 has list of pillar strings and/or branches
                    pillar_str = self.gans[i] + self.zhis[i]
                    for entry in lookup:
                        if len(entry) == 2:  # Full pillar match
                            if pillar_str == entry:
                                self._add_shen(i, shen_name)
                        else:  # Single branch match
                            if self.zhis[i] == entry:
                                self._add_shen(i, shen_name)
                else:
                    # Standard branch check
                    if self.zhis[i] in lookup:
                        self._add_shen(i, shen_name)

    # ========================================================================
    # SECTION 5: YEAR STEM SECONDARY STARS (年系 SECONDARY)
    # ========================================================================

    def _calc_year_stem_nobles(self) -> None:
        """
        Year Stem derived 天乙贵人 (Heavenly Noble).
        Labeled 年属昼天乙 / 年属夜天乙 to distinguish from Day Stem derivation.
        """
        for star_type in ("昼天乙", "夜天乙"):
            lookup = heavenly_stem_shens[star_type].get(self.year_stem, "")
            if not lookup:
                continue

            shen_name = f"年属{star_type}"
            for i in range(4):
                if self.zhis[i] in lookup:
                    self._add_shen(i, shen_name)

    # ========================================================================
    # SECTION 6: DERIVED & SPECIAL COMBINATION STARS
    # ========================================================================

    def _calc_blade_pairing(self) -> None:
        """
        阳刃伏藏 (Yang Blade Pairing - Hidden Blade).
        Triggers when Day Master has Yang Blade AND its partner stem appears
        in a pillar with the Yang Blade branch.
        """
        yang_ren_branch = heavenly_stem_shens["阳刃"].get(self.me, "")
        if not yang_ren_branch:
            return

        partner_stem = stem_partners.get(self.me)
        if not partner_stem:
            return

        for i in range(4):
            if self.zhis[i] in yang_ren_branch and self.gans[i] == partner_stem:
                self._add_shen(i, "阳刃伏藏")

    def _calc_fortune_virtue(self) -> None:
        """
        福禄双美 (Fortune & Virtue Double Beauty).
        Dual activation paths:
        1. Pillar-specific (inherited): exact pillar in list
        2. Combination (earned): both 福星 and 禄神 present in same pillar
        """
        fu_lu_special_pillars = pillar_shens.get("福禄双美", [])

        for i in range(4):
            current_pillar = self.gans[i] + self.zhis[i]
            is_special_pillar = current_pillar in fu_lu_special_pillars
            has_combo = "福星" in self.strs[i] and "禄神" in self.strs[i]

            if is_special_pillar or has_combo:
                self._add_shen(i, "福禄双美")

    def _calc_three_wonders(self) -> None:
        """
        三奇贵人 (Three Wonders / Three Stems Noble).
        Triggers when three consecutive pillars have stems matching one of:
        - 甲 戊 庚 (天上三奇 - Heaven's Three Wonders)
        - 乙 丙 丁 (地下三奇 - Earth's Three Wonders)
        - 辛 壬 癸 (人中三奇 - Human's Three Wonders)
        """
        trios = [
            (["甲", "戊", "庚"], "天上三奇"),
            (["乙", "丙", "丁"], "地下三奇"),
            (["辛", "壬", "癸"], "人中三奇"),
        ]

        # Check Year-Month-Day (indices 0,1,2) and Month-Day-Hour (indices 1,2,3)
        for sequence in [(0, 1, 2), (1, 2, 3)]:
            current_stems = [self.gans[idx] for idx in sequence]
            for trio_stems, name in trios:
                if current_stems == trio_stems:
                    for idx in sequence:
                        self._add_shen(idx, name)

    def _calc_self_lu(self):
        """Adds 自禄 (Self‑Lu) for pillars where the stem’s Lu matches the branch."""
        self_lu_map = {
            "甲寅": "寅命自禄",
            "乙卯": "卯命自禄",
            "庚申": "申命自禄",
            "辛酉": "酉命自禄",
        }
        for i in range(4):
            pillar = self.gans[i] + self.zhis[i]
            if pillar in self_lu_map:
                self._add_shen(i, self_lu_map[pillar])

    def _calc_hidden_stem_revelations(self):
        """Adds 藏干 revelations for specific pillars."""
        hidden_map = {
            "丁巳": "巳中藏丙",
            "癸亥": "亥中藏壬",
        }
        for i in range(4):
            pillar = self.gans[i] + self.zhis[i]
            if pillar in hidden_map:
                self._add_shen(i, hidden_map[pillar])

    # ========================================================================
    # SECTION 7: PILLAR-LEVEL & SEASONAL STARS (杂项)
    # ========================================================================

    def _calc_void(self) -> None:
        """
        空亡 (Kong Wang - Void / Empty Void).
        Classical Bazi practice: check both day pillar void (日基空亡) and year pillar void (年基空亡).

        Rules:
        - A pillar cannot be void of its own stream.
        - Year Pillar is checked against Day Void.
        - Day Pillar is checked against Year Void.
        - Month and Hour Pillars are checked against both.
        """
        void_branches_day = pillar_shens["空亡"].get(self.day_pillar, "")
        void_branches_year = pillar_shens["空亡"].get(self.year_pillar, "")

        # Convert to sets for O(1) lookup
        void_set_day = set(void_branches_day) if void_branches_day else set()
        void_set_year = set(void_branches_year) if void_branches_year else set()

        for i in range(4):
            # 1. Check Day-derived Void (Applies to Year, Month, Hour)
            if i != 2 and self.zhis[i] in void_set_day:
                self._add_shen(i, "空亡")

            # 2. Check Year-derived Void (Applies to Month, Day, Hour)
            # Note: _add_shen() prevents duplicates if a branch is void by both streams
            if i != 0 and self.zhis[i] in void_set_year:
                self._add_shen(i, "空亡")

    def _calc_day_pillar_specials(self) -> None:
        """
        Day pillar special formations: 阴阳差错, 十恶大败, 魁罡, 扩展魁罡.
        """
        day_checks = {
            "阴阳差错": pillar_shens.get("阴阳差错", []),
            "十恶大败": pillar_shens.get("十恶大败", []),
            "魁罡": pillar_shens.get("魁罡", []),
            "扩展魁罡": pillar_shens.get("扩展魁罡", []),
        }

        for shen_name, target_list in day_checks.items():
            if self.day_pillar in target_list:
                self._add_shen(2, shen_name)

    def _calc_four_wastes(self) -> None:
        """
        四废 (Four Wastes) - Seasonal day pillar check.
        Only valid for certain seasons and specific day pillars.
        """
        if not self.birth_season:
            return

        if self.day_pillar in pillar_shens["四废"].get(self.birth_season, []):
            self._add_shen(2, "四废")

    def _calc_jin_shen(self) -> None:
        """
        金神 (Golden Spirit / Metal Spirit) - Hour pillar only.
        """
        if self.hour_pillar in pillar_shens["金神"]:
            self._add_shen(3, "金神")

    def _calc_shi_ling(self) -> None:
        """
        十灵 (Ten Spirits) - Pillar-specific formation check.
        """
        for i in range(4):
            pillar = self.gans[i] + self.zhis[i]
            if pillar in pillar_shens.get("十灵", []):
                self._add_shen(i, "十灵")

    def _calc_tian_luo_di_wang(self) -> None:
        """
        Classical 天罗地网 calculation based on year pillar Nayin and mutual encounters.

        Rules:
        - 天罗: Fire Nayin year + 戌亥 both present in the four pillars.
        - 地网: Water/Earth Nayin year + 辰巳 both present in the four pillars.
        - Gender weighting: 男怕天罗, 女怕地网 (more severe for the respective gender).
        - Metal/Wood Nayin are exempt.
        """
        if not self.year_nayin:
            return

        # Check for mutual encounters
        branches_set = set(self.zhis)
        has_xu = "戌" in branches_set
        has_hai = "亥" in branches_set
        has_chen = "辰" in branches_set
        has_si = "巳" in branches_set

        # 天罗: Fire Nayin + 戌亥 mutual presence
        if self.year_nayin == "火" and has_xu and has_hai:
            # Add to pillars with 戌 or 亥
            for i in range(4):
                if self.zhis[i] in ("戌", "亥"):
                    self._add_shen(i, "天罗")

        # 地网: Water/Earth Nayin + 辰巳 mutual presence
        elif self.year_nayin in ("水", "土") and has_chen and has_si:
            # Add to pillars with 辰 or 巳
            for i in range(4):
                if self.zhis[i] in ("辰", "巳"):
                    self._add_shen(i, "地网")

    def _calc_tong_zi_sha(self) -> None:
        """
        童子煞 (Child Sha) – combined seasonal and Nayin rules.

        Combined seasonal rules - Two-step detection.

        Step 1: Native carries it if birth season is Summer/Winter
                AND day or hour branch is 卯/辰/未.
        Step 2: If native carries it, add to pillars with those branches.

        Nayin rules:

        Based on the Nayin element of the year pillar:
        - 金 / 木 (Metal/Wood) → 午 (Horse) or 卯 (Rabbit)
        - 水 / 火 (Water/Fire) → 酉 (Rooster) or 戌 (Dog)
        - 土 (Earth)          → 辰 (Dragon) or 巳 (Snake)
        """
        # ----- Seasonal rule (春秋寅子贵，冬夏卯辰未) -----
        if self.birth_season in ("夏", "冬"):
            # Step 1: Identify native's 童子 branches from day or hour pillar
            native_tong_zi = set()
            for idx in (2, 3):  # Day and Hour only
                if self.zhis[idx] in "卯辰未":
                    native_tong_zi.add(self.zhis[idx])

            # Step 2: Add to all pillars matching those branches
            for i in range(4):
                if self.zhis[i] in native_tong_zi:
                    self._add_shen(i, "童子煞")

        # ----- Nayin rule (based on year pillar Nayin) -----
        if self.year_nayin:
            nayin_to_tongzi = {
                "金": {"午", "卯"},
                "木": {"午", "卯"},
                "水": {"酉", "戌"},
                "火": {"酉", "戌"},
                "土": {"辰", "巳"},
            }
            target_branches = nayin_to_tongzi.get(self.year_nayin, set())
            for i in range(4):
                if self.zhis[i] in target_branches:
                    self._add_shen(i, "童子煞")

    # ========================================================================
    # SECTION 8: RELATIONAL STARS - INTER-PILLAR INTERACTIONS
    # ========================================================================

    def _calc_mutual_lu(self) -> None:
        """
        互禄 (Mutual Lu / Reciprocal Salary).
        Triggers when two pillars exchange lu branches:
        - Pillar A's master has lu at Pillar B's branch
        - Pillar B's master has lu at Pillar A's branch

        Tracks both adjacent (紧贴) and distant (遥) pairings.
        """
        lu_map = heavenly_stem_shens["禄神"]
        pillar_names_cn = self.pillar_names

        for i in range(4):
            for j in range(i + 1, 4):
                if (
                    lu_map.get(self.gans[i]) == self.zhis[j]
                    and lu_map.get(self.gans[j]) == self.zhis[i]
                ):
                    is_adj = abs(i - j) == 1
                    self.hu_lu_results.append(
                        {
                            "组合": f"{pillar_names_cn[i]}-{pillar_names_cn[j]}",
                            "紧贴": is_adj,
                            "状态": "正互" if is_adj else "遥互",
                            "描述": f"{self.gans[i]}{self.zhis[i]}与{self.gans[j]}{self.zhis[j]}互换禄神",
                        }
                    )

    def _calc_virtual_lu(self) -> None:
        """
        虚邀禄 (Virtual Lu / Aspiring Lu).
        Triggers when the Day Master's lu branch is NOT physically in the chart,
        but is flanked by adjacent branches.

        Distinguishes 拱禄 (Day-Hour position) from 夹禄 (others).
        """
        lu_map = heavenly_stem_shens["禄神"]
        my_lu = lu_map.get(self.me)

        if not my_lu or my_lu in self.zhis:
            return

        idx = self.branch_order.index(my_lu)
        prev_n = self.branch_order[(idx - 1) % 12]
        next_n = self.branch_order[(idx + 1) % 12]

        if prev_n in self.zhis and next_n in self.zhis:
            # Collect all indices for each branch (handles duplicates)
            prev_indices = [i for i, zh in enumerate(self.zhis) if zh == prev_n]
            next_indices = [i for i, zh in enumerate(self.zhis) if zh == next_n]

            # Check all pairs for adjacency
            for p1 in prev_indices:
                for p2 in next_indices:
                    is_adj = abs(p1 - p2) == 1
                    is_gong = p1 >= 2 and p2 >= 2  # Day-Hour position
                    label = "拱禄" if is_gong else "夹禄"
                    prefix = "正" if is_adj else "遥"

                    p_min, p_max = min(p1, p2), max(p1, p2)
                    self.jia_gong_lu_results.append(
                        {
                            "虚邀地支": my_lu,
                            "紧贴": is_adj,
                            "状态": f"{prefix}{label}",
                            "来源柱": [self.pillar_names[p_min], self.pillar_names[p_max]],
                            "说明": f"{self.pillar_names[p_min]}与{self.pillar_names[p_max]}{prefix}{label}出{my_lu}",
                        }
                    )

    def _calc_lu_yuan_exchange(self):
        """
        禄元互换 (Lu Yuan Exchange)
        Classical day‑hour combinations from San Ming Tong Hui:
        - 戊申日 + 乙卯时
        - 丁酉日 + 壬寅时
        - 丙子日 + 癸巳时
        - 庚子日 + 丁亥时
        Adds '禄元互换' to both day and hour pillars when the exact pair appears.
        """
        # Valid day‑hour pairs (day pillar, hour pillar)
        lu_yuan_pairs = [
            ("戊申", "乙卯"),
            ("丁酉", "壬寅"),
            ("丙子", "癸巳"),
            ("庚子", "丁亥"),
        ]

        day_pillar = self.gans[2] + self.zhis[2]   # 日柱
        hour_pillar = self.gans[3] + self.zhis[3]  # 时柱

        for day, hour in lu_yuan_pairs:
            if day_pillar == day and hour_pillar == hour:
                # Add star to both pillars
                self._add_shen(2, "禄元互换")
                self._add_shen(3, "禄元互换")
                # Store in relational results
                self.lu_yuan_results.append({
                    "组合": f"{day_pillar}日 {hour_pillar}时",
                    "说明": "禄元互换，贵格"
                })
                break   # Only one pair can match

    def _calc_advancing_retreating_lu(self):
        """
        进退真禄 (Advancing/Retreating True Lu)
        Based on San Ming Tong Hui, the order is critical:
        - Advancing pairs (Day → Hour): 戊辰‑丁巳, 丙辰‑癸巳, 癸亥‑甲子, 壬戌‑癸亥
        - Retreating pairs (Day → Hour): 戊午‑丁巳, 丙午‑癸巳, 癸丑‑甲子, 壬子‑癸亥

        The star is added to both the day and hour pillars **only when** the day pillar
        exactly matches the first element and the hour pillar exactly matches the second.
        The reversed order does not count as Advancing or Retreating True Lu.
        """
        day_pillar = self.gans[2] + self.zhis[2]
        hour_pillar = self.gans[3] + self.zhis[3]

        advancing_pairs = [
            ("戊辰", "丁巳"),
            ("丙辰", "癸巳"),
            ("癸亥", "甲子"),
            ("壬戌", "癸亥"),
        ]
        retreating_pairs = [
            ("戊午", "丁巳"),
            ("丙午", "癸巳"),
            ("癸丑", "甲子"),
            ("壬子", "癸亥"),
        ]

        # Check advancing pairs (exact order)
        for p1, p2 in advancing_pairs:
            if day_pillar == p1 and hour_pillar == p2:
                self._add_shen(2, "进真禄")
                self._add_shen(3, "进真禄")
                self.advancing_retreating_results.append({
                    "组合": f"{p1}-{p2}",
                    "类型": "进真禄"
                })
                break  # Only one advancing pair can match

        # Check retreating pairs (exact order)
        for p1, p2 in retreating_pairs:
            if day_pillar == p1 and hour_pillar == p2:
                self._add_shen(2, "退真禄")
                self._add_shen(3, "退真禄")
                self.advancing_retreating_results.append({
                    "组合": f"{p1}-{p2}",
                    "类型": "退真禄"
                })
                break  # Only one retreating pair can match

    def _calc_virtual_noble(self) -> None:
        """
        虚邀贵 (Virtual Noble / Aspiring Noble).
        Similar to 虚邀禄 but for 天乙贵人 (Heavenly Noble).
        Checks both 昼天乙 and 夜天乙.
        """
        noble_branches = list(
            set(
                [
                    heavenly_stem_shens["昼天乙"].get(self.me),
                    heavenly_stem_shens["夜天乙"].get(self.me),
                ]
            )
        )

        for nb in noble_branches:
            if not nb or nb in self.zhis:
                continue

            idx = self.branch_order.index(nb)
            p_nb = self.branch_order[(idx - 1) % 12]
            n_nb = self.branch_order[(idx + 1) % 12]

            if p_nb in self.zhis and n_nb in self.zhis:
                # Collect all indices for each branch (handles duplicates)
                p_indices = [i for i, zh in enumerate(self.zhis) if zh == p_nb]
                n_indices = [i for i, zh in enumerate(self.zhis) if zh == n_nb]

                # Check all pairs for adjacency
                for p1 in p_indices:
                    for p2 in n_indices:
                        is_adj = abs(p1 - p2) == 1
                        is_gong = p1 >= 2 and p2 >= 2
                        label = "拱贵" if is_gong else "夹贵"
                        prefix = "正" if is_adj else "遥"

                        p_min, p_max = min(p1, p2), max(p1, p2)
                        self.jia_gong_gui_results.append(
                            {
                                "虚邀贵人": nb,
                                "紧贴": is_adj,
                                "状态": f"{prefix}{label}",
                                "说明": f"{self.pillar_names[p_min]}与{self.pillar_names[p_max]}{prefix}{label}出天乙贵人{nb}",
                            }
                        )

    # ========================================================================
    # SECTION 9: ADVANCED RELATIONAL STARS
    # ========================================================================

    def _calc_virtue_elegance(self) -> None:
        """
        德秀贵人 (Virtue & Elegance Noble).
        Determined by month branch's element frame; stems in that frame activate it.
        """
        month_req = dexiu_map.get(self.zhis[1], "")
        if not month_req:
            return

        dexiu_distribution = {}
        for i in range(4):
            if self.gans[i] in month_req:
                self._add_shen(i, "德秀")
                dexiu_distribution[self.pillar_names[i]] = self.gans[i]

        if dexiu_distribution:
            self.de_xiu_result = {
                "激活": True,
                "触发月令": self.zhis[1],
                "分布明细": dexiu_distribution,
            }

    def _calc_dark_lu(self) -> None:
        """
        暗禄 (Dark Lu / Hidden Salary).
        The 六合 partner branch of Day Master's 禄神.
        Example: 甲禄在寅, 寅亥合, so 甲的暗禄在亥.
        """
        target_zhi = an_lu_map.get(self.me)
        if not target_zhi:
            return

        an_lu_distribution = {}
        for i in range(4):
            if self.zhis[i] == target_zhi:
                self._add_shen(i, "暗禄")
                an_lu_distribution[self.pillar_names[i]] = self.zhis[i]

        if an_lu_distribution:
            self.an_lu_result = {
                "激活": True,
                "触发日干": self.me,
                "对应支": target_zhi,
                "分布明细": an_lu_distribution,
            }

    # ========================================================================
    # ORCHESTRATOR & RESULT ASSEMBLY
    # ========================================================================

    def calculate(self) -> Dict[str, Any]:
        """
        Orchestrate all shen sha calculations for the natal chart.

        Calls all _calc_*() methods in logical order, grouped by derivation source:
        年系, 月系, 日系, 日干, 年干, 衍生特殊, 柱位/季节, 关系, 高级关系.
        Results are cached within the instance to avoid redundant recalculation.

        Returns:
            dict: {"神煞": {"柱位神煞": {...}, "系统神煞": {...}}}
        """
        if self._result_cache is not None:
            return self._result_cache

        # YEAR BRANCH (Year系)
        self._calc_year_branch_shens()
        self._calc_yuan_chen()
        self._calc_juan_she()
        self._calc_pi_ma()

        # MONTH BRANCH (Month系)
        self._calc_month_branch_shens()
        self._calc_tian_she()
        self._calc_virtue_unions()

        # DAY BRANCH (Day系)
        self._calc_day_branch_shens()
        self._calc_bath_peach_blossom()

        # DAY STEM (Core Personal, Day系)
        self._calc_day_stem_shens()

        # YEAR STEM (Secondary, Year系)
        self._calc_year_stem_nobles()

        # DERIVED & SPECIAL
        self._calc_blade_pairing()
        self._calc_fortune_virtue()
        self._calc_three_wonders()
        self._calc_self_lu()
        self._calc_hidden_stem_revelations()

        # PILLAR & SEASONAL (Miscellaneous)
        self._calc_void()
        self._calc_day_pillar_specials()
        self._calc_four_wastes()
        self._calc_jin_shen()
        self._calc_shi_ling()
        self._calc_tian_luo_di_wang()
        self._calc_tong_zi_sha()

        # RELATIONAL (Inter-pillar interactions)
        self._calc_mutual_lu()
        self._calc_lu_yuan_exchange()
        self._calc_advancing_retreating_lu()
        self._calc_virtual_lu()
        self._calc_virtual_noble()

        # ADVANCED RELATIONAL
        self._calc_virtue_elegance()
        self._calc_dark_lu()

        self._result_cache = self._build_result()
        return self._result_cache

    def _build_result(self) -> Dict[str, Any]:
        """
        Assemble final output structure.
        Maintains backward compatibility with formatter:
        {"神煞": {"柱位神煞": {...}, "系统神煞": {...}}}
        """
        # Per-pillar shen stars
        pillar_dynamics = {
            self.pillar_names[i]: {
                "神煞": self.strs[i].split() if self.strs[i] else [],
            }
            for i in range(4)
        }

        # Relational / system-level shens (mixed list and dict values)
        relational_shens: dict = {}  # type: ignore
        relational_shens["互禄明细"] = self.hu_lu_results
        relational_shens["虚邀禄"] = self.jia_gong_lu_results
        relational_shens["虚邀贵"] = self.jia_gong_gui_results

        if self.lu_yuan_results:
            relational_shens["禄元互换"] = self.lu_yuan_results
        if self.advancing_retreating_results:
            relational_shens["进退真禄"] = self.advancing_retreating_results
        if self.de_xiu_result:
            relational_shens["德秀贵人"] = self.de_xiu_result
        if self.an_lu_result:
            relational_shens["暗禄"] = self.an_lu_result

        return {
            "神煞": {
                "柱位神煞": pillar_dynamics,
                "系统神煞": relational_shens,
            }
        }

    def get_cycle_shen_sha(
        self, cycle_stem: str, cycle_branch: str
    ) -> Dict[str, List[str]]:
        """
        Compute shen sha for a single cycle pillar (da yun, xiao yun, liu nian, liu yue).

        Reuses cached natal state (day master, month branch, year branch, season, etc.)
        but does NOT modify natal state.

        Returns categorized shens: {"日系": [...], "年系": [...], "月系": [...], "杂项": [...]}

        Args:
            cycle_stem (str): Cycle pillar stem (e.g., "甲")
            cycle_branch (str): Cycle pillar branch (e.g., "寅")

        Returns:
            dict: {"日系": [...], "年系": [...], "月系": [...], "杂项": [...]}
        """
        cache_key = (cycle_stem, cycle_branch)
        if cache_key in self._cycle_cache:
            return self._cycle_cache[cache_key]

        # Use sets throughout to automatically handle deduplication
        # Convert to lists only in final result
        year_shens, month_shens, day_shens, misc_shens = set(), set(), set(), set()

        def add_year(name: str) -> None:
            year_shens.add(name)

        def add_month(name: str) -> None:
            month_shens.add(name)

        def add_day(name: str) -> None:
            day_shens.add(name)

        def add_misc(name: str) -> None:
            misc_shens.add(name)

        # 1. YEAR-BRANCH LOOKUPS (年系)
        for shen_name, mapping in year_earthly_branches_shens.items():
            # Skip 卷舌, 披麻 and 元辰 (handled separately)
            if shen_name in ("卷舌", "披麻", "元辰"):
                continue
            lookup = mapping.get(self.zhis[0], "")
            if cycle_branch in lookup:
                add_year("桃花" if shen_name == "桃花" else shen_name)

        # 卷舌
        juan_she_map = year_earthly_branches_shens.get("卷舌", {})
        if cycle_branch in juan_she_map.get(self.zhis[0], ""):
            add_year("卷舌")

        # 披麻
        pi_ma_map = year_earthly_branches_shens.get("披麻", {})
        if cycle_branch in pi_ma_map.get(self.zhis[0], ""):
            add_year("披麻")

        # 元辰
        if (self.is_yang_year and self.is_male) or (
            not self.is_yang_year and not self.is_male
        ):
            yuan_chen_target = yuan_chen_map[self.zhis[0]][0]
        else:
            yuan_chen_target = yuan_chen_map[self.zhis[0]][1]
        if cycle_branch == yuan_chen_target:
            add_year("元辰")

        # 2-3. MONTH-BRANCH LOOKUPS + VIRTUE UNIONS (月系)
        for shen_name, mapping in month_earthly_branches_shens.items():
            if shen_name == "天赦":
                continue
            lookup = mapping.get(self.zhis[1], "")
            if isinstance(lookup, str):
                if shen_name in ("天医", "血刃"):
                    if cycle_branch in lookup:
                        add_month(shen_name)
                else:
                    if cycle_stem in lookup or cycle_branch in lookup:
                        add_month(shen_name)

        # Virtue unions — mirror natal _calc_virtue_unions() branch/stem handling
        tian_de_value = month_earthly_branches_shens["天德"].get(self.zhis[1])
        if tian_de_value:
            if tian_de_value in HEAVENLY_STEMS:
                partner = stem_partners.get(tian_de_value)
                if partner and cycle_stem == partner:
                    add_month("天德合")
            else:  # It's a branch
                partner_branch = branch_six_combinations.get(tian_de_value)
                if partner_branch and cycle_branch == partner_branch:
                    add_month("天德合")

        yue_de_value = month_earthly_branches_shens["月德"].get(self.zhis[1])
        if yue_de_value:
            if yue_de_value in HEAVENLY_STEMS:
                partner = stem_partners.get(yue_de_value)
                if partner and cycle_stem == partner:
                    add_month("月德合")
            else:  # It's a branch
                partner_branch = branch_six_combinations.get(yue_de_value)
                if partner_branch and cycle_branch == partner_branch:
                    add_month("月德合")

        if tian_de_value and yue_de_value:
            if tian_de_value in HEAVENLY_STEMS and yue_de_value in HEAVENLY_STEMS:
                tp = stem_partners.get(tian_de_value)
                yp = stem_partners.get(yue_de_value)
                if tp and yp and tp == yp and cycle_stem == tp:
                    add_month("天月德合")

        # 德秀贵人 (Virtue & Elegance Noble) - month-branch derived
        month_req = dexiu_map.get(self.zhis[1], "")
        if month_req and cycle_stem in month_req:
            add_month("德秀")

        # 4-5. DAY-BRANCH LOOKUPS + BATH PEACH BLOSSOM (日系)
        for shen_name, mapping in day_earthly_branches_shens.items():
            lookup = mapping.get(self.zhis[2], "")
            if lookup and cycle_branch in lookup:
                add_day("桃花" if shen_name == "桃花" else shen_name)

        if ("桃花" in year_shens or "桃花" in month_shens or
            "桃花" in day_shens or "桃花" in misc_shens):
            if cycle_branch == bath_position.get(self.me):
                add_day("沐浴桃花")

        # 6. DAY-STEM LOOKUPS (日系)
        for shen_name, mapping in heavenly_stem_shens.items():
            lookup = mapping.get(self.me, "")
            if not lookup:
                continue
            if shen_name == "词馆":
                for entry in lookup:
                    if len(entry) == 2 and (cycle_stem + cycle_branch) == entry:
                        add_day(shen_name)
                    elif len(entry) == 1 and cycle_branch == entry:
                        add_day(shen_name)
            else:
                if cycle_branch in lookup:
                    add_day(shen_name)

        # 7. YANG BLADE PAIRING (日系)
        yang_ren = heavenly_stem_shens["阳刃"].get(self.me, "")
        if yang_ren:
            partner = stem_partners.get(self.me)
            if partner and cycle_stem == partner and cycle_branch in yang_ren:
                add_day("阳刃伏藏")

        # 7b. DARK LU (日系) — Day Master's 禄神 six-combination partner branch
        dark_lu_branch = an_lu_map.get(self.me)
        if dark_lu_branch and cycle_branch == dark_lu_branch:
            add_day("暗禄")

        # 8. VOID (日系/年系) — check both day pillar (日基空亡) and year pillar (年基空亡)
        # Categorize by source: day-derived void → 日系, year-derived void → 年系
        void_set_day = set(pillar_shens["空亡"].get(self.day_pillar, ""))
        void_set_year = set(pillar_shens["空亡"].get(self.year_pillar, ""))

        if cycle_branch in void_set_day:
            add_day("空亡")  # Day-derived void (日空) → 日系
        if cycle_branch in void_set_year:
            add_year("空亡")  # Year-derived void (年空) → 年系

        # 8b. SELF-LU (日系) — cycle pillar carries 自禄 if stem's lu matches its own branch
        self_lu_map = {
            "甲寅": "寅命自禄",
            "乙卯": "卯命自禄",
            "庚申": "申命自禄",
            "辛酉": "酉命自禄",
        }
        cycle_pillar = cycle_stem + cycle_branch
        if cycle_pillar in self_lu_map:
            add_day(self_lu_map[cycle_pillar])

        # 9. PILLAR SPECIALS (杂项)
        for shen_name, target_list in {
            "阴阳差错": pillar_shens.get("阴阳差错", []),
            "十恶大败": pillar_shens.get("十恶大败", []),
            "魁罡": pillar_shens.get("魁罡", []),
            "扩展魁罡": pillar_shens.get("扩展魁罡", []),
            "十灵": pillar_shens.get("十灵", []),
        }.items():
            if cycle_pillar in target_list:
                add_misc(shen_name)

        # 10. FOUR WASTES (杂项)
        if self.birth_season and cycle_pillar in pillar_shens["四废"].get(
            self.birth_season, []
        ):
            add_misc("四废")

        # 11. 天赦 (月系)
        if self.birth_season:
            pardon = month_earthly_branches_shens.get("天赦", {}).get(self.birth_season)
            if pardon and cycle_pillar == pardon:
                add_month("天赦")

        # 12. 童子煞 (杂项) - Seasonal and Nayin rules
        # Seasonal rule: Summer/Winter + Day/Hour branch in 卯辰未
        if self.birth_season in ("夏", "冬"):
            native_tong_zi = {self.zhis[i] for i in (2, 3) if self.zhis[i] in "卯辰未"}
            if cycle_branch in native_tong_zi:
                add_misc("童子煞")

        # Nayin rule: Year Nayin determines which branches trigger 童子煞
        # 金/木 (Metal/Wood) → 午 or 卯
        # 水/火 (Water/Fire) → 酉 or 戌
        # 土 (Earth) → 辰 or 巳
        if self.year_nayin:
            nayin_to_tongzi = {
                "金": {"午", "卯"},
                "木": {"午", "卯"},
                "水": {"酉", "戌"},
                "火": {"酉", "戌"},
                "土": {"辰", "巳"},
            }
            nayin_branches = nayin_to_tongzi.get(self.year_nayin, set())
            if cycle_branch in nayin_branches:
                add_misc("童子煞")

        # 13. 天罗地网 (杂项) - Nayin-restricted
        if self.year_nayin == "火" and "戌" in self.zhis and "亥" in self.zhis:
            # Fire Nayin + 戌亥 mutual presence → 天罗 trap
            if cycle_branch in ("戌", "亥"):
                add_misc("天罗")
        elif (
            self.year_nayin in ("水", "土") and "辰" in self.zhis and "巳" in self.zhis
        ):
            # Water/Earth Nayin + 辰巳 mutual presence → 地网 trap
            if cycle_branch in ("辰", "巳"):
                add_misc("地网")

        result = {
            "日系": sorted(list(day_shens)),
            "年系": sorted(list(year_shens)),
            "月系": sorted(list(month_shens)),
            "杂项": sorted(list(misc_shens)),
        }
        self._cycle_cache[cache_key] = result
        return result


# ============================================================================
# PUBLIC API
# ============================================================================


def get_shen_sha(lunar_birthday: Lunar, gender: int) -> Dict[str, Any]:
    """
    Public entry point for natal shen sha calculation.

    Args:
        lunar_birthday (Lunar): Lunar calendar object from lunar_python library
        gender (int): 0 for Female, 1 for Male (consistent with BaZi library convention)

    Returns:
        dict: {
            "神煞": {
                "柱位神煞": {
                    "年柱": {"神煞": [...]},
                    "月柱": {"神煞": [...]},
                    "日柱": {"神煞": [...]},
                    "时柱": {"神煞": [...]}
                },
                "系统神煞": {
                    "互禄明细": [...],       # always present (may be empty)
                    "虚邀禄": [...],         # always present (may be empty)
                    "虚邀贵": [...],         # always present (may be empty)
                    "禄元互换": [...],       # present only if activated
                    "进退真禄": [...],       # present only if activated
                    "德秀贵人": {...},       # present only if activated
                    "暗禄": {...}            # present only if activated
                }
            }
        }

    Raises:
        ValueError: if gender not in (0, 1)
    """
    return ShenShaCalculator(lunar_birthday, gender).calculate()


# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    from src.utils.logging import configure_logging, get_logger
    from src.astronomer_calculations.bazi_pillars import get_bazi_pillars
    import json

    # python -m src.astronomer_calculations.shen_sha

    # Initialize logging
    logger = configure_logging()
    log = get_logger(__name__)

    # Example: Desmond's birth chart (1985-11-25, 17:07)
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)
    tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)

    log.info("=" * 60)
    log.info("阳历生日: " + solar_birthday.toYmdHms())
    log.info("真太阳时生日: " + tst_birthday.toYmdHms())
    log.info("=" * 60)

    lunar_birthday = tst_birthday.getLunar()

    bazi_json = get_bazi_pillars(tst_birthday.getLunar())
    logger.info(f"八字: {bazi_json}")

    # Test male
    log.info("\n[男性神煞]")
    result_male = get_shen_sha(lunar_birthday, gender=1)
    log.info(json.dumps(result_male, ensure_ascii=False, indent=2))

    # # Test female
    # log.info("\n[女性神煞]")
    # result_female = get_shen_sha(lunar_birthday, gender=0)
    # log.info(json.dumps(result_female, ensure_ascii=False, indent=2))

    # Test cycle shens
    log.info("\n[Da Yun Test - 甲子 cycle]")
    calc = ShenShaCalculator(lunar_birthday, gender=1)
    cycle_result = calc.get_cycle_shen_sha("甲", "子")
    log.info(json.dumps(cycle_result, ensure_ascii=False, indent=2))
