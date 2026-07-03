"""
Shen Sha (神煞) Calculation Module - Class-Based Architecture

This module calculates and identifies Shen Sha (Auspicious & Inauspicious Stars) in BaZi charts.
Shen Sha are additional spiritual stars used in Chinese astrology to provide deeper insights
into a person's character, destiny, relationships, and challenges.

Key Methodology:
- Year Branch (年系) → 龙德, 红鸾, 天喜, 孤辰, 寡宿, 病符, 吊客, 丧门, 白虎,
                       勾绞煞, 披头, 披麻, 元辰, 卷舌, 六厄
                       暗金的煞 → 吟呻 (子午卯酉年), 破碎 (寅申巳亥年), 白衣 (辰戌丑未年)
                         └─ checked on Day & Hour Pillars only
                       飞廉 ("天瞽") → checked on Day & Hour Pillars only
- Month Branch (月系) → 天德贵人, 月德贵人, 天医, 月空, 血刃, 天赦, 天转, 地转, 季节性退神
                        天德合, 月德合, 天月德合, 德秀贵人
- Day & Year Branch (日/年系) → 将星, 华盖, 驿马, 劫煞, 亡神, 桃花, 灾煞
- Day & Year Stem (日/年干系) → 昼天乙贵人, 夜天乙贵人, 文昌, 学堂, 太极贵人, 禄神,
                                金舆, 国印, 福星, 真词馆 (stem→exact pillar),
                                天厨贵人, 飞刃, 天官贵人, 阳刃, 阴刃
- Day Stem only (日干系) → 红艳, 流霞
                                正词馆 (Year Nayin→exact pillar, via _calc_ci_guan)
- Day Pillar (日柱) → 阴阳差错, 十恶大败, 魁罡, 进神, 六秀, 八专, 九丑, 孤鸾, 退气神煞,
                      四废, 金神, 十灵, 天罗, 地网, 童子煞
- Inter-Pillar (组合) → 三奇贵人 (天上/地下/人中), 自禄, 隔角煞
- Relational (关系) → 暗禄

Architecture:
- ShenShaCalculator class encapsulates full natal chart analysis
- Gender-dependent calculations (元辰)
- Results cached within the instance after first call to calculate()
- Deduplication by (name, source) pair — same star from two sources appears twice in JSON
  but the frontend deduplicates by name for display purposes

Public API:
    get_shen_sha(bazi, na_yin, gender): Main entry point for natal chart analysis.

    Returns: {
        "神煞": {
            "柱位神煞": {
                "年柱": {"神煞": [{"名称": str, "来源": str}, ...]},
                "月柱": {"神煞": [...]},
                "日柱": {"神煞": [...]},
                "时柱": {"神煞": [...]}
            }
        }
    }
"""

from __future__ import annotations

import json
from typing import Dict, List, Any, Optional


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
        "寅": "巳",
        "卯": "申",
        "辰": "未",
        "巳": "午",
        "午": "未",
        "未": "申",
        "申": "酉",
        "酉": "戌",
        "戌": "子",
        "亥": "卯",
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
    "病符": {
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
    "天空": {
        "子": "丑",
        "丑": "寅",
        "寅": "卯",
        "卯": "辰",
        "辰": "巳",
        "巳": "午",
        "午": "未",
        "未": "申",
        "申": "酉",
        "酉": "戌",
        "戌": "亥",
        "亥": "子",
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
        "子": "辰",
        "丑": "卯",
        "寅": "寅",
        "卯": "丑",
        "辰": "子",
        "巳": "亥",
        "午": "戌",
        "未": "酉",
        "申": "申",
        "酉": "未",
        "戌": "午",
        "亥": "巳",
    },
    "六厄": {
        "申": "卯",
        "子": "卯",
        "辰": "卯",
        "寅": "酉",
        "午": "酉",
        "戌": "酉",
        "亥": "午",
        "卯": "午",
        "未": "午",
        "巳": "子",
        "酉": "子",
        "丑": "子",
    },
}

# --- 暗金的煞 (Dark Gold Malefic) ---
# Year Branch → (target_branch, star_name)
# Target must appear in the Day or Hour Pillar only.
an_jin_de_sha_map = {
    "子": ("巳", "吟呻"),
    "午": ("巳", "吟呻"),
    "卯": ("巳", "吟呻"),
    "酉": ("巳", "吟呻"),
    "寅": ("酉", "破碎"),
    "申": ("酉", "破碎"),
    "巳": ("酉", "破碎"),
    "亥": ("酉", "破碎"),
    "辰": ("丑", "白衣"),
    "戌": ("丑", "白衣"),
    "丑": ("丑", "白衣"),
    "未": ("丑", "白衣"),
}

# --- 飞廉 (FEI LIAN / "Heavenly Blindness" Star) ---
# Year Branch Method (Primary — San Ming Tong Hui health chapter: "飞廉名天瞽")
# Year Branch → Fei Lian target branch. Star is placed only on Day/Hour Pillar
# (checked the same way as 暗金的煞, not via the generic all-4-pillar loop).
fei_lian_map = {
    "子": "申",
    "丑": "酉",
    "寅": "戌",
    "卯": "巳",
    "辰": "午",
    "巳": "未",
    "午": "寅",
    "未": "卯",
    "申": "辰",
    "酉": "亥",
    "戌": "子",
    "亥": "丑",
}

# --- 词馆 (Literary Academy Star) Lookup Tables ---
# Method 1: Year Nayin element → exact target pillar → 正词馆
# 金命见申(壬申), 木命见寅(庚寅), 水命见亥(癸亥), 土命见亥(丁亥), 火命见巳(乙巳)
ci_guan_nayin_map = {
    "金": "壬申",
    "木": "庚寅",
    "水": "癸亥",
    "土": "丁亥",
    "火": "乙巳",
}

# Method 2: Day/Year Stem → exact target pillar → 真词馆
ci_guan_stem_map = {
    "甲": "庚寅",
    "乙": "辛卯",
    "丙": "乙巳",
    "丁": "戊午",
    "戊": "丁巳",
    "己": "庚午",
    "庚": "壬申",
    "辛": "癸酉",
    "壬": "癸亥",
    "癸": "壬戌",
}

# --- MONTH BRANCH BASED SHENS ---
month_earthly_branches_shens = {
    # --- VIRTUES ---
    "天德贵人": {
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
    "月德贵人": {
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
        "寅": "丑",
        "卯": "未",
        "辰": "寅",
        "巳": "申",
        "午": "卯",
        "未": "酉",
        "申": "辰",
        "酉": "戌",
        "戌": "巳",
        "亥": "亥",
        "子": "午",
        "丑": "子",
    },
    "月厌": {   # retrograde sequence 戌酉申未午巳辰卯寅丑子亥 for months 寅→丑
        "寅": "戌",
        "卯": "酉",
        "辰": "申",
        "巳": "未",
        "午": "午",
        "未": "巳",
        "申": "辰",
        "酉": "卯",
        "戌": "寅",
        "亥": "丑",
        "子": "子",
        "丑": "亥",
    },
    "月煞": {   # 四季三合组 → 库支 (丑戌未辰)
        "寅": "丑",  "午": "丑",  "戌": "丑",
        "亥": "戌",  "卯": "戌",  "未": "戌",
        "申": "未",  "子": "未",  "辰": "未",
        "巳": "辰",  "酉": "辰",  "丑": "辰",
    },
    # --- SEASONAL ---
    "天赦": {"春": "戊寅", "夏": "甲午", "秋": "戊申", "冬": "甲子"},
    "天转": {"春": "乙卯", "夏": "丙午", "秋": "辛酉", "冬": "壬子"},
    "地转": {"春": "辛卯", "夏": "戊午", "秋": "癸酉", "冬": "丙子"},
    "季节性退神": {"春": "丁丑", "夏": "丁未", "秋": "壬辰", "冬": "壬戌"},
}

# --- DAY BRANCH BASED SHENS ---
day_year_earthly_branches_shens = {
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
    "灾煞": {
        "子": "午",
        "丑": "卯",
        "寅": "子",
        "卯": "酉",
        "辰": "午",
        "巳": "卯",
        "午": "子",
        "未": "酉",
        "申": "午",
        "酉": "卯",
        "戌": "子",
        "亥": "酉",
    },
}

# --- HEAVENLY STEM BASED SHENS (STEM-UNIVERSAL: PRIMARY YEAR STEM, SECONDARY DAY STEM) ---
# Maps any stem (甲-癸) to their derived stars (nobles, academics, wealth, etc.)
# Using San Ming Tong Hui (三命通会) - Symmetry Model
year_day_heavenly_stem_shens = {
    # --- NOBLES & ACADEMICS ---
    "昼天乙贵人": {  # 阳贵 (Yang Noble)
        "甲": "未",
        "乙": "申",
        "丙": "酉",
        "丁": "亥",
        "戊": "丑",  # Some San Ming versions use 未 for Wu, but 丑 is the standard Symmetry start
        "己": "子",
        "庚": "丑",
        "辛": "寅",
        "壬": "卯",
        "癸": "巳",
    },
    "夜天乙贵人": {  # 阴贵 (Yin Noble)
        "甲": "丑",
        "乙": "子",
        "丙": "亥",
        "丁": "酉",
        "戊": "未",
        "己": "申",
        "庚": "未",
        "辛": "午",
        "壬": "巳",
        "癸": "卯",
    },
    "文昌贵人": {
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
    "太极贵人": {
        "甲": "子午",
        "乙": "子午",
        "丙": "卯酉",
        "丁": "卯酉",
        "戊": "申辰戌丑未",
        "己": "申辰戌丑未",
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
        "丙": "寅子",
        "乙": "卯丑",
        "癸": "卯丑",
        "戊": "申",
        "己": "未",
        "丁": "亥",
        "庚": "午",
        "辛": "巳",
        "壬": "辰",
    },
    "天厨贵人": {
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
    "天官贵人": {
        "甲": "未",
        "乙": "辰",
        "丙": "巳",
        "丁": "酉",
        "戊": "戌",
        "己": "卯",
        "庚": "丑",
        "辛": "申",
        "壬": "寅",
        "癸": "午",
    },
}

# --- DAY STEM ONLY SHENS ---
# Stars that derive exclusively from the Day Stem (日干), never the Year Stem.
day_stem_only_shens = {
    "红艳": {
        "甲": "午",
        "乙": "午",
        "丙": "寅",
        "丁": "未",
        "戊": "子",
        "己": "辰",
        "庚": "戌",
        "辛": "酉",
        "壬": "巳",
        "癸": "申",
    },
    "流霞": {
        "甲": "酉",
        "乙": "戌",
        "丙": "未",
        "丁": "申",
        "戊": "巳",
        "己": "午",
        "庚": "辰",
        "辛": "卯",
        "壬": "亥",
        "癸": "寅",
    },
    "文昌贵": {
        "甲": "巳", "乙": "亥", "丙": "戌", "丁": "辰", "戊": "申",
        "己": "午", "庚": "寅", "辛": "未", "壬": "卯", "癸": "丑",
    },
    "文星贵": {
        "甲": "午", "乙": "巳", "丙": "申", "丁": "酉", "戊": "申",
        "己": "酉", "庚": "戌", "辛": "亥", "壬": "寅", "癸": "卯",
    },
    "天印贵": {
        "甲": "寅", "乙": "亥", "丙": "戌", "丁": "酉", "戊": "申",
        "己": "未", "庚": "午", "辛": "巳", "壬": "辰", "癸": "卯",
    },
    "羊刃": {
        # Yang stems
        "甲": "卯",
        "丙": "午",
        "戊": "午",
        "庚": "酉",
        "壬": "子",
        # # Yin stems
        # "乙": "辰",
        # "丁": "未",
        # "己": "未",
        # "辛": "戌",
        # "癸": "丑",
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
        "癸": "未",
    },
}

# --- PILLAR SPECIAL FORMATIONS & VOIDS ---
pillar_shens = {
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
    "金神": ["癸酉", "己巳", "乙丑"],
    "进神": ["甲子", "甲午", "己卯", "己酉"],
    "六秀": ["丙午", "丁未", "戊子", "戊午", "己丑", "己未"],
    "八专": ["甲寅", "乙卯", "丁未", "戊戌", "己未", "庚申", "辛酉", "癸丑"],
    "九丑": ["丁酉", "戊子", "戊午", "己卯", "己酉", "辛卯", "辛酉", "壬子", "壬午"],
    "孤鸾": ["甲寅", "乙巳", "丙午", "丁巳", "戊申", "戊午", "辛亥", "壬子"],
    # 进-交-退-伏 four-star cycle (San Ming Tong Hui)
    "退气神煞": ["丁丑", "丁未", "壬辰", "壬戌"],
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
        "冬": ["丙午", "丁巳"],
    },
}

# --- 自缢煞 / 破煞 branch-pair sets ---
# 自缢煞: 6 pairs — if BOTH branches of a pair appear anywhere in the 4 pillars, both are marked
_ZI_YI_SHA_PAIRS: list[frozenset] = [
    frozenset({"戌", "巳"}), frozenset({"辰", "亥"}), frozenset({"寅", "未"}),
    frozenset({"卯", "申"}), frozenset({"午", "丑"}), frozenset({"子", "酉"}),
]
# 破煞: 4 pairs (寅申巳亥 excluded per text — they form 三合 so are not taken)
_PO_SHA_PAIRS: list[frozenset] = [
    frozenset({"卯", "午"}), frozenset({"丑", "辰"}),
    frozenset({"子", "酉"}), frozenset({"未", "戌"}),
]

# --- 天屠煞 (TIAN TU SHA) ---
# Day Branch → Hour Branch: 5 mutual pairs where branch indices sum to 12.
# 子↔午 (sum=6) explicitly excluded by classical text.
_TIAN_TU_SHA_DAY_HOUR: dict[str, str] = {
    "丑": "亥", "亥": "丑",
    "寅": "戌", "戌": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "申", "申": "辰",
    "巳": "未", "未": "巳",
}

# --- 剑锋煞 (JIAN FENG SHA) ---
# Year pillar's 旬首 branch → (剑枝, 锋枝)
_JIAN_FENG_SHA_XUN: dict[str, tuple[str, str]] = {
    "子": ("辰", "戌"),  # 甲子旬: 剑辰, 锋戌
    "戌": ("寅", "子"),  # 甲戌旬: 剑寅, 锋子
    "申": ("子", "寅"),  # 甲申旬: 剑子, 锋寅
    "午": ("戌", "辰"),  # 甲午旬: 剑戌, 锋辰
    "辰": ("申", "午"),  # 甲辰旬: 剑申, 锋午
    "寅": ("午", "申"),  # 甲寅旬: 剑午, 锋申
}

# --- 隔角煞 (GE JIAO SHA) ---
# Day Branch → target Time Branch (exactly two steps ahead in branch cycle)
ge_jiao_sha_map_day_time = {
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
}
# Year Branch ↔ Day Branch mutual opposition pairs
ge_jiao_sha_map_year_day = {
    "子": "亥",
    "亥": "子",
    "丑": "戌",
    "戌": "丑",
    "寅": "酉",
    "酉": "寅",
    "卯": "申",
    "申": "卯",
    "辰": "未",
    "未": "辰",
    "巳": "午",
    "午": "巳",
}

# --- VIRTUES & ELEGANCE STARS ---
# 德秀贵人 - Virtue & Elegance Noble
# Structure: month branch → (de_stems, xiu_pairs)
# de_stems: virtue stems — determines which pillars receive the star
# xiu_pairs: elegance combinations — both stems must appear in Year/Day/Hour for condition to pass
dexiu_map = {
    "寅": ("丙丁", [("戊", "癸")]),  # Fire frame
    "午": ("丙丁", [("戊", "癸")]),
    "戌": ("丙丁", [("戊", "癸")]),
    "申": ("壬癸戊己", [("丙", "辛"), ("甲", "己")]),  # Water frame
    "子": ("壬癸戊己", [("丙", "辛"), ("甲", "己")]),
    "辰": ("壬癸戊己", [("丙", "辛"), ("甲", "己")]),
    "巳": ("庚辛", [("乙", "庚")]),  # Metal frame
    "酉": ("庚辛", [("乙", "庚")]),
    "丑": ("庚辛", [("乙", "庚")]),
    "亥": ("甲乙", [("丁", "壬")]),  # Wood frame
    "卯": ("甲乙", [("丁", "壬")]),
    "未": ("甲乙", [("丁", "壬")]),
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

# ============================================================================
# MODULE-LEVEL HELPER
# ============================================================================


def add_shen_on_pillar(
    pillar_idx: int,
    shen_name: str,
    strs: List[list],
    all_found_shens: List[str],
    source: str = "",
    detail: str = "",
) -> None:
    """
    Add shen to a pillar as a dict and track unique shen names.

    Args:
        pillar_idx (int): Pillar index (0=Year, 1=Month, 2=Day, 3=Hour)
        shen_name (str): Name of the shen to add
        strs (list): Accumulator for per-pillar stars (list of list of dicts)
        all_found_shens (list): Accumulator for unique star names
        source (str): Derivation source
        detail (str): Optional subtype detail (e.g. specific day pillar for 进神)
    """
    already_in_pillar = any(
        d["名称"] == shen_name and d["来源"] == source for d in strs[pillar_idx]
    )
    if not already_in_pillar:
        entry: dict = {"名称": shen_name, "来源": source}
        if detail:
            entry["细节"] = detail
        strs[pillar_idx].append(entry)
        if shen_name not in all_found_shens:
            all_found_shens.append(shen_name)


# ============================================================================
# SHEN SHA CALCULATOR CLASS
# ============================================================================


class ShenShaCalculator:
    """
    Encapsulates all shen sha calculations for a BaZi natal chart.

    Architecture:
    - __init__ accepts pre-computed bazi and na_yin from the orchestrator
    - Shared derived state used by all _calc_*() methods (no parameter passing)
    - _calc_*() methods are grouped by derivation source (year branch, month branch,
      stems, pillar formations, inter-pillar combinations, relational)
    - calculate() orchestrates all _calc_*() methods and caches the result

    Derivation sources used as the `来源` field in output:
      "年支", "月支", "日支", "日干", "年干", "日柱", "时柱",
      "自柱", "组合", "纳音", "节气"

    Gender convention: 0 = Female, 1 = Male (consistent with BaZi library)
    """

    def __init__(self, bazi, na_yin: dict, gender: int) -> None:
        """
        Initialize calculator from pre-computed backend data.

        Args:
            bazi: EightChar object from lunar_python (lunar_birthday.getEightChar())
            na_yin (dict): Output of get_na_yin(bazi) — {"年柱": "海中金", ...}
            gender (int): 0 for Female, 1 for Male

        Raises:
            ValueError: if gender not in (0, 1)
        """
        if gender not in (0, 1):
            raise ValueError(f"gender must be 0 (Female) or 1 (Male), got {gender}")

        self.gender = gender
        self.is_male = gender == 1
        self.na_yin = na_yin

        # Cache for calculation results
        self._result_cache: Optional[Dict[str, Any]] = None

        # Extract stems and branches from bazi
        self.gans = [
            bazi.getYearGan(),
            bazi.getMonthGan(),
            bazi.getDayGan(),
            bazi.getTimeGan(),
        ]
        self.zhis = [
            bazi.getYearZhi(),
            bazi.getMonthZhi(),
            bazi.getDayZhi(),
            bazi.getTimeZhi(),
        ]

        # Initialize derived state
        self._init_derived()

    def _init_derived(self) -> None:
        """
        Compute and cache all derived state from gans, zhis, and na_yin.
        """
        self.me = self.gans[2]  # Day Master (Day Stem)
        self.year_stem = self.gans[0]
        self.year_pillar = self.gans[0] + self.zhis[0]
        self.day_pillar = self.gans[2] + self.zhis[2]
        self.hour_pillar = self.gans[3] + self.zhis[3]
        self.birth_season = seasons_map.get(self.zhis[1])

        self.year_nayin = nayin_to_element(self.na_yin.get("年柱", ""))

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
        self.strs: List[list] = [[], [], [], []]
        self.all_found_shens = []

        # Accumulators for relational shens

    def _add_shen(
        self, pillar_idx: int, shen_name: str, source: str = "", detail: str = ""
    ) -> None:
        """Convenience wrapper for add_shen_on_pillar using instance accumulators."""
        add_shen_on_pillar(
            pillar_idx, shen_name, self.strs, self.all_found_shens, source, detail
        )

    def _has_shen(self, pillar_idx: int, shen_name: str) -> bool:
        """Check if any entry in pillar has the given 名称, regardless of 来源."""
        return any(d["名称"] == shen_name for d in self.strs[pillar_idx])

    # ========================================================================
    # SECTION 1: YEAR BRANCH DERIVED STARS (年系)
    # ========================================================================

    def _calc_year_branch_shens(self) -> None:
        """
        Year Branch Derived Stars (年系) — generic loop over year_earthly_branches_shens.

        Derives stars from the Year Branch (年支) and checks all 4 pillars.

        Self-Exclusion Rule:
        - Stars in SELF_EXCLUSION_STARS cannot self-trigger on the Year Pillar (i==0).
        - These stars CAN appear on the Year Pillar if triggered by a different source.

        Stars handled separately (not in this loop):
        - 卷舌, 披麻: same lookup formula but semantically distinct → _calc_juan_she / _calc_pi_ma
        - 元辰: requires gender + year yin/yang logic → _calc_yuan_chen
        - 桃花: generates wall-classified variants (墙内/墙外) → inline special case below
        - 暗金的煞 (吟呻/破碎/白衣): Day & Hour only, three variants → _calc_an_jin_de_sha
        """
        for shen_name, mapping in year_earthly_branches_shens.items():
            # Handle separately: 卷舌/披麻 (semantic split), 勾绞煞 (gender-dependent labeling)
            if shen_name in ("卷舌", "披麻", "勾绞煞"):
                continue

            lookup = mapping.get(self.zhis[0], "")
            for i in range(4):
                # Self-exclusion: year-branch-derived stars cannot appear on year pillar
                if shen_name in SELF_EXCLUSION_STARS and i == 0:
                    continue

                if self.zhis[i] in lookup:
                    self._add_shen(i, shen_name, source="年支")

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
                self._add_shen(i, "元辰", source="年支")

    def _calc_gou_jiao(self) -> None:
        """
        勾绞煞 (Hook & Entangle Sha) — gender + year yin/yang dependent.

        前三辰 (+3 from year branch) and 后三辰 (its 六冲) are labelled 勾煞/绞煞
        depending on gender and year yin/yang:
          阳男 or 阴女 → 前三辰 = 勾煞, 后三辰 = 绞煞
          阴男 or 阳女 → 前三辰 = 绞煞, 后三辰 = 勾煞
        """
        _liu_chong = {"子": "午", "午": "子", "丑": "未", "未": "丑",
                      "寅": "申", "申": "寅", "卯": "酉", "酉": "卯",
                      "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
        gou_jiao_map = year_earthly_branches_shens.get("勾绞煞", {})
        qian = gou_jiao_map.get(self.zhis[0], "")   # 前三辰
        hou = _liu_chong.get(qian, "")               # 后三辰 (六冲 of 前三辰)
        if not qian or not hou:
            return

        yang_male_or_yin_female = (self.is_male and self.is_yang_year) or (
            not self.is_male and not self.is_yang_year
        )
        if yang_male_or_yin_female:
            gou_branch, jiao_branch = qian, hou
        else:
            gou_branch, jiao_branch = hou, qian

        for i in range(4):
            if self.zhis[i] == gou_branch:
                self._add_shen(i, "勾煞", source="年支")
            if self.zhis[i] == jiao_branch:
                self._add_shen(i, "绞煞", source="年支")

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
                self._add_shen(i, "卷舌", source="年支")

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
                self._add_shen(i, "披麻", source="年支")

    def _calc_an_jin_de_sha(self) -> None:
        """
        暗金的煞 (Dark Gold Malefic) - Year branch derived, Day/Hour Pillar only.

        Three variants determined by the Year Branch group:
        - 子午卯酉 year → target 巳 → 吟呻
        - 寅申巳亥 year → target 酉 → 破碎
        - 辰戌丑未 year → target 丑 → 白衣

        Star is placed only on Day (index 2) or Hour (index 3) Pillars.
        """
        entry = an_jin_de_sha_map.get(self.zhis[0])
        if not entry:
            return
        target_branch, star_name = entry
        for i in (2, 3):  # Day and Hour Pillars only
            if self.zhis[i] == target_branch:
                self._add_shen(i, star_name, source="年支")

    def _calc_fei_lian(self) -> None:
        """
        飞廉 ("Heavenly Blindness" Star) - Year Branch Method, Day/Hour Pillar only.

        San Ming Tong Hui health chapter: "飞廉名天瞽".
        Year Branch → target branch; star placed only if the target appears
        in the Day or Hour Pillar (not Year or Month).
        """
        target_branch = fei_lian_map.get(self.zhis[0])
        if not target_branch:
            return
        for i in (2, 3):  # Day and Hour Pillars only
            if self.zhis[i] == target_branch:
                self._add_shen(i, "飞廉", source="年支")

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
                            self._add_shen(i, shen_name, source="月支")
                    # 月空 checks stems only (target is always a heavenly stem)
                    elif shen_name == "月空":
                        if self.gans[i] == lookup:
                            self._add_shen(i, shen_name, source="月支")
                    # Virtue stars (天德贵人, 月德贵人) check stems or branches
                    else:
                        if self.gans[i] in lookup or self.zhis[i] in lookup:
                            self._add_shen(i, shen_name, source="月支")

    def _calc_tian_she(self) -> None:
        """
        天赦 (Heavenly Pardon) - Seasonal Day Pillar check.
        Anchor: month branch (season). Check: Day Pillar full stem-branch pair.
        Only triggers on the Day Pillar (index 2).
        """
        if not self.birth_season:
            return

        target_pillar = month_earthly_branches_shens["天赦"].get(self.birth_season)
        if not target_pillar:
            return

        if self.day_pillar == target_pillar:
            self._add_shen(2, "天赦", source="月支")

    def _calc_tian_zhuan(self) -> None:
        """
        天转 (Heavenly Turn) - Seasonal Day Pillar check.
        Anchor: month branch (season). Check: Day Pillar full stem-branch pair.
        Only triggers on the Day Pillar (index 2).
        """
        if not self.birth_season:
            return
        target_pillar = month_earthly_branches_shens["天转"].get(self.birth_season)
        if not target_pillar:
            return
        if self.day_pillar == target_pillar:
            self._add_shen(2, "天转", source="月支")

    def _calc_di_zhuan(self) -> None:
        """
        地转 (Earthly Turn) - Seasonal Day Pillar check.
        Anchor: month branch (season). Check: Day Pillar full stem-branch pair.
        Only triggers on the Day Pillar (index 2).
        """
        if not self.birth_season:
            return
        target_pillar = month_earthly_branches_shens["地转"].get(self.birth_season)
        if not target_pillar:
            return
        if self.day_pillar == target_pillar:
            self._add_shen(2, "地转", source="月支")

    def _calc_seasonal_tui_shen(self) -> None:
        """
        季节性退神 (Seasonal Retreating Spirit) - Seasonal Day Pillar check.
        Anchor: month branch (season). Check: Day Pillar full stem-branch pair.
        Distinct from the 进交退伏 退神 (which derives from the Day Pillar directly).
        Only triggers on the Day Pillar (index 2).
        """
        if not self.birth_season:
            return
        target_pillar = month_earthly_branches_shens["季节性退神"].get(
            self.birth_season
        )
        if not target_pillar:
            return
        if self.day_pillar == target_pillar:
            self._add_shen(2, "季节性退神", source="月支")

    def _calc_virtue_unions(self):
        """
        天德合 (Heavenly Virtue Union) - Classical formula from 三命通会

        When 天德 is a STEM → partner is the 五合 (five-combination) stem
        When 天德 is a BRANCH → partner is the 六合 (six-combination) branch

        Also handles 月德合 (Month Virtue Union) and 天月德合 (Combined Virtue Union)
        """
        month_branch = self.zhis[1]

        # --- 天德合 (Heavenly Virtue Union) ---
        tian_de_value = month_earthly_branches_shens["天德贵人"].get(month_branch)
        if tian_de_value:
            # Check if tian_de_value is a stem or branch
            if tian_de_value in HEAVENLY_STEMS:  # It's a stem
                partner_stem = stem_partners.get(tian_de_value)
                if partner_stem:
                    for i in range(4):
                        if self.gans[i] == partner_stem:
                            self._add_shen(i, "天德合", source="月支")
            else:  # It's a branch
                # Get the six-combination partner of the branch
                partner_branch = branch_six_combinations.get(
                    tian_de_value
                )  # You'll need this map
                if partner_branch:
                    for i in range(4):
                        if self.zhis[i] == partner_branch:
                            self._add_shen(i, "天德合", source="月支")

        # --- 月德合 (Month Virtue Union) ---
        yue_de_value = month_earthly_branches_shens["月德贵人"].get(month_branch)
        if yue_de_value:
            if yue_de_value in HEAVENLY_STEMS:  # It's always stem
                partner_stem = stem_partners.get(yue_de_value)
                if partner_stem:
                    for i in range(4):
                        if self.gans[i] == partner_stem:
                            self._add_shen(i, "月德合", source="月支")

        # --- 天月德合 (Combined Virtue Union) ---
        if tian_de_value and yue_de_value:
            # Both are stems and their partners match
            if tian_de_value in HEAVENLY_STEMS and yue_de_value in HEAVENLY_STEMS:
                tian_partner = stem_partners.get(tian_de_value)
                yue_partner = stem_partners.get(yue_de_value)
                if tian_partner and yue_partner and tian_partner == yue_partner:
                    for i in range(4):
                        if self.gans[i] == tian_partner:
                            self._add_shen(i, "天月德合", source="月支")

    # ========================================================================
    # SECTION 3: DAY & YEAR BRANCH DERIVED STARS (日支 + 年支)
    # ========================================================================

    def _calc_day_year_branch_shens(self) -> None:
        """
        Branch derived stars from day_year_earthly_branches_shens.
        Derives 将星, 华盖, 驿马, 劫煞, 亡神, 桃花 from both:
        - Year Branch (年支) → source="年支", self-exclusion on Year Pillar (i==0)
        - Day Branch (日支) → source="日支", self-exclusion on Day Pillar (i==2)
        桃花 includes wall classification (墙内/墙外) based on pillar position.
        """
        branch_sources = [
            (self.zhis[0], "年支", 0),  # Year Branch
            (self.zhis[2], "日支", 2),  # Day Branch
        ]

        for source_branch, source_label, exclusion_idx in branch_sources:
            for shen_name, mapping in day_year_earthly_branches_shens.items():
                lookup = mapping.get(source_branch, "")
                if not lookup:
                    continue

                for i in range(4):
                    if shen_name in SELF_EXCLUSION_STARS and i == exclusion_idx:
                        continue

                    if self.zhis[i] in lookup:
                        self._add_shen(i, shen_name, source=source_label)

    # ========================================================================
    # SECTION 4: DAY & YEAR STEM DERIVED STARS (日干 + 年干)
    # ========================================================================

    def _calc_day_year_stem_shens(self) -> None:
        """
        Stem derived stars from year_day_heavenly_stem_shens (干系).
        Derives all stars from both:
        - Day Stem (日干, self.me)         → source="日干"
        - Year Stem (年干, self.year_stem) → source="年干"
        词馆 is handled separately in _calc_ci_guan().
        """
        stem_sources = [
            (self.me, "日干"),  # Day Stem
            (self.year_stem, "年干"),  # Year Stem
        ]

        for source_stem, source_label in stem_sources:
            for shen_name, mapping in year_day_heavenly_stem_shens.items():
                lookup = mapping.get(source_stem, "")
                if not lookup:
                    continue
                for i in range(4):
                    if self.zhis[i] in lookup:
                        self._add_shen(i, shen_name, source=source_label)

    def _calc_ci_guan(self) -> None:
        """
        词馆 (Literary Academy Star) — two activation methods.

        Method 1 (正词馆): Year Nayin element → exact target pillar.
          The Year Pillar Nayin element maps to a specific stem-branch pair;
          if that pillar appears anywhere in the chart, 正词馆 is placed on it.
          金→壬申, 木→庚寅, 水→癸亥, 土→丁亥, 火→乙巳
          (水 and 土 both target branch 亥, distinguished by stem.)
          source="纳音"

        Method 2 (真词馆): Day Stem or Year Stem → exact target pillar.
          Each stem maps to a unique stem-branch pair; if that pillar appears
          anywhere in the chart, 真词馆 is placed on it.
          source="日干" or "年干"
        """
        # Method 1: Year Nayin → 正词馆
        target = ci_guan_nayin_map.get(self.year_nayin)
        if target:
            for i in range(4):
                if self.gans[i] + self.zhis[i] == target:
                    self._add_shen(i, "正词馆", source="纳音")

        # Method 2: Day Stem + Year Stem → 真词馆
        for source_stem, source_label in ((self.me, "日干"), (self.year_stem, "年干")):
            target = ci_guan_stem_map.get(source_stem)
            if target:
                for i in range(4):
                    if self.gans[i] + self.zhis[i] == target:
                        self._add_shen(i, "真词馆", source=source_label)

    def _calc_xue_tang(self) -> None:
        """
        学堂 (Academic Hall) — two derivation methods combined.

        Method 1 (查法一): Year Nayin element → branch, checked against Month/Day/Hour pillars.
          金→巳, 木→亥, 水→申, 土→申, 火→寅   source="年纳音"
        Method 2 (查法二): Day Stem → branch, checked against all 4 pillars.
          甲→亥, 乙→午, 丙→寅, 丁→酉, 戊→寅,
          己→酉, 庚→巳, 辛→子, 壬→申, 癸→卯   source="日干"
        """
        _nayin_map = {"金": "巳", "木": "亥", "水": "申", "土": "申", "火": "寅"}
        _stem_map = {
            "甲": "亥", "乙": "午", "丙": "寅", "丁": "酉", "戊": "寅",
            "己": "酉", "庚": "巳", "辛": "子", "壬": "申", "癸": "卯",
        }
        # Method 1: Year Nayin → Month/Day/Hour pillars only (skip Year pillar)
        branch1 = _nayin_map.get(self.year_nayin, "")
        if branch1:
            for i in range(1, 4):
                if self.zhis[i] == branch1:
                    self._add_shen(i, "学堂", source="年纳音")

        # Method 2: Day Stem → all 4 pillars
        branch2 = _stem_map.get(self.me, "")
        if branch2:
            for i in range(4):
                if self.zhis[i] == branch2:
                    self._add_shen(i, "学堂", source="日干")

    # ========================================================================
    # SECTION 5: DAY STEM ONLY DERIVED STARS (日干系)
    # ========================================================================

    def _calc_day_stem_only_shens(self) -> None:
        """Stars derived exclusively from the Day Stem (日干), checked against all 4 branches."""
        for shen_name, mapping in day_stem_only_shens.items():
            lookup = mapping.get(self.me, "")
            if not lookup:
                continue
            for i in range(4):
                if self.zhis[i] == lookup:
                    self._add_shen(i, shen_name, source="日干")

    def _calc_wen_yu_gui(self) -> None:
        """文誉贵: mark any pillar whose ganzhi is ±2 positions in the 60-cycle from day pillar."""
        _s = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        _b = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        sixty = [_s[i % 10] + _b[i % 12] for i in range(60)]
        day_gz = self.me + self.zhis[2]
        try:
            day_pos = sixty.index(day_gz)
        except ValueError:
            return
        targets = {sixty[(day_pos - 2) % 60], sixty[(day_pos + 2) % 60]}
        for i in range(4):
            if self.gans[i] + self.zhis[i] in targets:
                self._add_shen(i, "文誉贵", source="日柱")

    # ========================================================================
    # SECTION 6: DERIVED & SPECIAL COMBINATION STARS
    # ========================================================================

    def _calc_three_wonders(self) -> None:
        """
        三奇贵人 (Three Wonders / Three Stems Noble).
        Triggers when three consecutive pillars have stems matching one of
        (forward or reverse order):
        - 乙 丙 丁 (天上三奇 - Heaven's Three Wonders: sun/moon/star per 《玉霄宝鉴》)
        - 甲 戊 庚 (地下三奇 - Earth's Three Wonders: wood/earth/metal per 《三车一览》)
        - 辛 壬 癸 (人间三奇 - Human's Three Wonders: consecutive stems 8→9→10 per 《太乙经》)
        """
        trios = [
            (["乙", "丙", "丁"], "天上三奇"),
            (["甲", "戊", "庚"], "地下三奇"),
            (["辛", "壬", "癸"], "人间三奇"),
        ]

        # Check Year-Month-Day (indices 0,1,2) and Month-Day-Hour (indices 1,2,3)
        # Both forward and reverse order are valid (顺排或逆排)
        for sequence in [(0, 1, 2), (1, 2, 3)]:
            current_stems = [self.gans[idx] for idx in sequence]
            for trio_stems, name in trios:
                if current_stems == trio_stems or current_stems == trio_stems[::-1]:
                    for idx in sequence:
                        self._add_shen(idx, name, source="组合")

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
                self._add_shen(i, self_lu_map[pillar], source="自柱")

    # ========================================================================
    # SECTION 7: PILLAR-LEVEL & SEASONAL STARS (杂项)
    # ========================================================================

    def _calc_day_pillar_specials(self) -> None:
        """
        Day pillar special formations: 阴阳差错, 十恶大败, 魁罡.
        """
        day_checks = {
            "十恶大败": pillar_shens.get("十恶大败", []),
            "六秀": pillar_shens.get("六秀", []),
            "八专": pillar_shens.get("八专", []),
            "九丑": pillar_shens.get("九丑", []),
            "孤鸾": pillar_shens.get("孤鸾", []),
            "退气神煞": pillar_shens.get("退气神煞", []),
        }

        for shen_name, target_list in day_checks.items():
            if self.day_pillar in target_list:
                self._add_shen(2, shen_name, source="日柱")

        # 进神 handled separately to record the specific day pillar as 细节
        if self.day_pillar in pillar_shens.get("进神", []):
            self._add_shen(2, "进神", source="日柱", detail=self.day_pillar)

    def _calc_yin_yang_cha_cuo(self) -> None:
        """
        阴阳差错 — checked on ALL four pillars, not just the day pillar.
        Classical text: '月日时两重或三重犯之，极重' — month, day, and time pillars
        can all carry this star independently for severity grading.
        Day pillar uses source '日柱' (preserves interpretation lookup).
        Other pillars use source '自柱' (severity handled at DSL layer).
        """
        target = pillar_shens.get("阴阳差错", [])
        for i in range(4):
            pillar = self.gans[i] + self.zhis[i]
            if pillar in target:
                source = "日柱"
                self._add_shen(i, "阴阳差错", source=source)

    def _calc_four_wastes(self) -> None:
        """
        四废 (Four Wastes) - Seasonal day pillar check.
        Only valid for certain seasons and specific day pillars.
        """
        if not self.birth_season:
            return

        if self.day_pillar in pillar_shens["四废"].get(self.birth_season, []):
            self._add_shen(2, "四废", source="日柱")

    def _calc_jin_shen(self) -> None:
        """
        金神 (Golden Spirit / Metal Spirit) - Hour pillar only.
        """
        if self.hour_pillar in pillar_shens["金神"]:
            self._add_shen(3, "金神", source="时柱")

    def _calc_shi_ling(self) -> None:
        """
        十灵 (Ten Spirits) - Day Pillar only.
        Star is placed on index 2 if the Day Pillar stem-branch pair matches the list.
        Other pillars with the same pair do not receive the star.
        """
        if self.day_pillar in pillar_shens.get("十灵", []):
            self._add_shen(2, "十灵", source="日柱")

    def _calc_tian_luo_di_wang(self) -> None:
        """
        天罗地网 — both net branches present anywhere in the four pillars.

        天罗 (Heavenly Net): 戌 AND 亥 both appear across the four pillars.
        地网 (Earthly Net):  辰 AND 巳 both appear across the four pillars.

        The star is placed on every pillar carrying the relevant branch.
        This means 天罗 and 地网 can coexist when all four branches appear.
        Gender-specific effects, severity grading, and Nayin modifiers are
        handled at the interpretation layer (DSL rules), not here.
        """
        all_zhis = set(self.zhis)

        if {"戌", "亥"} <= all_zhis:
            for i in range(4):
                if self.zhis[i] in ("戌", "亥"):
                    self._add_shen(i, "天罗", source="四柱")

        if {"辰", "巳"} <= all_zhis:
            for i in range(4):
                if self.zhis[i] in ("辰", "巳"):
                    self._add_shen(i, "地网", source="四柱")

    def _calc_zi_yi_sha(self) -> None:
        """
        自缢煞 — branch-pair interaction: if both branches of any of the 6 pairs appear
        anywhere in the four pillars, mark every pillar carrying either branch.
        Pairs: 戌↔巳, 辰↔亥, 寅↔未, 卯↔申, 午↔丑, 子↔酉
        """
        all_zhis = set(self.zhis)
        for pair in _ZI_YI_SHA_PAIRS:
            if pair <= all_zhis:
                for i in range(4):
                    if self.zhis[i] in pair:
                        self._add_shen(i, "自缢煞", source="四柱")

    def _calc_po_sha(self) -> None:
        """
        破煞 — branch-pair breaks: if both branches of a pair appear anywhere in the four
        pillars, mark every pillar carrying either branch.
        Pairs: 卯↔午, 丑↔辰, 子↔酉, 未↔戌 (寅申巳亥 excluded — they form 三合).
        """
        all_zhis = set(self.zhis)
        for pair in _PO_SHA_PAIRS:
            if pair <= all_zhis:
                for i in range(4):
                    if self.zhis[i] in pair:
                        self._add_shen(i, "破煞", source="四柱")

    def _calc_gua_jian_sha(self) -> None:
        """
        挂剑煞 — full-metal branch formation (从革).
        Trigger 1 (纯全): all 4 pillar branches ∈ {巳,酉,丑,申}.
        Trigger 2 (重带): ≥ 3 occurrences of branches from {巳,酉,丑} across the 4 pillars.
        Star placed on every pillar whose branch ∈ {巳,酉,丑,申}.
        """
        metal_full = {"巳", "酉", "丑", "申"}
        metal_trio = {"巳", "酉", "丑"}
        all_in_metal = all(z in metal_full for z in self.zhis)
        heavy_trio = sum(1 for z in self.zhis if z in metal_trio) >= 3
        if all_in_metal or heavy_trio:
            for i in range(4):
                if self.zhis[i] in metal_full:
                    self._add_shen(i, "挂剑煞", source="四柱")

    def _calc_tian_huo_sha(self) -> None:
        """
        天火煞 — complete fire frame with no water.
        Conditions: {寅,午,戌} all present in branches + {丙 or 丁} in stems + no water
        (no 壬/癸 in stems, no 子/亥 in branches). Star placed on pillars with 寅,午,戌.
        """
        all_zhis = set(self.zhis)
        all_gans = set(self.gans)
        if not ({"寅", "午", "戌"} <= all_zhis):
            return
        if not (all_gans & {"丙", "丁"}):
            return
        if (all_gans & {"壬", "癸"}) or (all_zhis & {"子", "亥"}):
            return
        for i in range(4):
            if self.zhis[i] in ("寅", "午", "戌"):
                self._add_shen(i, "天火煞", source="四柱")

    def _calc_tong_zi_sha(self) -> None:
        """
        童子煞 (Child Sha) — seasonal + Nayin rules, checked on Day and Hour branches only.

        Seasonal rules (month branch determines season):
        - Spring / Autumn → Day or Hour branch is 寅 or 子
        - Winter / Summer → Day or Hour branch is 卯, 未, or 辰

        Nayin rules (Year Pillar Nayin element):
        - 金 / 木 (Metal/Wood) → Day or Hour branch is 午 or 卯
        - 水 / 火 (Water/Fire) → Day or Hour branch is 酉 or 戌
        - 土 (Earth)           → Day or Hour branch is 辰 or 巳

        Star is placed on the Day or Hour Pillar that carries the matching branch.
        """
        # ----- Seasonal rule -----
        if self.birth_season in ("春", "秋"):
            target_branches = {"寅", "子"}
        elif self.birth_season in ("夏", "冬"):
            target_branches = {"卯", "未", "辰"}
        else:
            target_branches = set()

        if target_branches:
            for idx in (2, 3):  # Day and Hour only
                if self.zhis[idx] in target_branches:
                    self._add_shen(idx, "童子煞", source="节气")

        # ----- Nayin rule (based on Year Pillar Nayin) -----
        if self.year_nayin:
            nayin_to_tongzi = {
                "金": {"午", "卯"},
                "木": {"午", "卯"},
                "水": {"酉", "戌"},
                "火": {"酉", "戌"},
                "土": {"辰", "巳"},
            }
            nayin_branches = nayin_to_tongzi.get(self.year_nayin, set())
            for idx in (2, 3):  # Day and Hour only
                if self.zhis[idx] in nayin_branches:
                    self._add_shen(idx, "童子煞", source="纳音")

    def _calc_ge_jiao_sha(self) -> None:
        """
        隔角煞 (Separated-Corner Sha) - two activation paths:
        1. Day Branch vs Hour Branch: Hour Branch is two steps ahead of Day Branch.
           Star placed on both Day Pillar and Hour Pillar.
        2. Year Branch vs Day Branch: Day Branch is the opposition pair of Year Branch.
           Star placed on Day Pillar.
        """
        # Path 1: Day Branch → Hour Branch
        target_dt = ge_jiao_sha_map_day_time.get(self.zhis[2])
        if target_dt and self.zhis[3] == target_dt:
            self._add_shen(2, "隔角煞", source="日支")
            self._add_shen(3, "隔角煞", source="日支")

        # Path 2: Year Branch → Day Branch
        if ge_jiao_sha_map_year_day.get(self.zhis[0]) == self.zhis[2]:
            self._add_shen(2, "隔角煞", source="年支")

    def _calc_tian_tu_sha(self) -> None:
        """
        天屠煞 — day branch and hour branch form one of 5 mutual pairs (branch indices sum to 12).
        子↔午 (sum=6) explicitly excluded by classical text.
        Star placed on both Day Pillar (i=2) and Hour Pillar (i=3).
        """
        expected_hour = _TIAN_TU_SHA_DAY_HOUR.get(self.zhis[2])
        if expected_hour and self.zhis[3] == expected_hour:
            self._add_shen(2, "天屠煞", source="日支")
            self._add_shen(3, "天屠煞", source="日支")

    def _calc_jian_feng_sha(self) -> None:
        """
        剑锋煞 — derived from the YEAR pillar's 旬.
        Derives 旬首 branch via (year_branch_idx - year_stem_idx) % 12 (no bazi object needed).
        All 4 pillars carrying either the 剑枝 or 锋枝 receive the star. Source = '年支'.
        """
        _TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        _DI_ZHI   = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        year_stem_idx   = _TIAN_GAN.index(self.gans[0])
        year_branch_idx = _DI_ZHI.index(self.zhis[0])
        xun_shou_branch = _DI_ZHI[(year_branch_idx - year_stem_idx) % 12]
        targets = _JIAN_FENG_SHA_XUN.get(xun_shou_branch)
        if not targets:
            return
        jian_branch, feng_branch = targets
        for i in range(4):
            if self.zhis[i] in (jian_branch, feng_branch):
                self._add_shen(i, "剑锋煞", source="年支")

    # ========================================================================
    # SECTION 8: RELATIONAL STARS - INTER-PILLAR INTERACTIONS
    # ========================================================================

    # ========================================================================
    # SECTION 9: ADVANCED RELATIONAL STARS
    # ========================================================================

    def _calc_virtue_elegance(self) -> None:
        """
        德秀贵人 (Virtue & Elegance Noble).
        Two conditions must both be met (checked against Year/Day/Hour only, not Month):
        1. De (德): at least one virtue stem present in Year, Day, or Hour.
        2. Xiu (秀): at least one elegance combination has both stems present.
        Star is placed only on pillars whose stem matches the virtue stem list.
        """
        entry = dexiu_map.get(self.zhis[1])
        if not entry:
            return
        de_stems, xiu_pairs = entry

        non_month = [0, 2, 3]  # Year, Day, Hour indices
        non_month_stems = {self.gans[i] for i in non_month}
        all_stems = set(self.gans)  # all 4 pillars for 秀 combination check

        has_de = any(s in de_stems for s in non_month_stems)
        if not has_de:
            return

        has_xiu = any(s1 in all_stems and s2 in all_stems for s1, s2 in xiu_pairs)
        if not has_xiu:
            return

        for i in non_month:
            if self.gans[i] in de_stems:
                self._add_shen(i, "德秀贵人", source="月支")

    def _calc_dark_lu(self) -> None:
        """
        暗禄 (Dark Lu / Hidden Salary).
        The 六合 partner branch of Day Master's 禄神.
        Example: 甲禄在寅, 寅亥合, so 甲的暗禄在亥.
        """
        target_zhi = an_lu_map.get(self.me)
        if not target_zhi:
            return

        for i in range(4):
            if self.zhis[i] == target_zhi:
                self._add_shen(i, "暗禄", source="日干")

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
        self._calc_gou_jiao()
        self._calc_juan_she()
        self._calc_pi_ma()
        self._calc_an_jin_de_sha()
        self._calc_fei_lian()

        # MONTH BRANCH (Month系)
        self._calc_month_branch_shens()
        self._calc_tian_she()
        self._calc_tian_zhuan()
        self._calc_di_zhuan()
        self._calc_seasonal_tui_shen()
        self._calc_virtue_unions()

        # DAY BRANCH (Day系)
        self._calc_day_year_branch_shens()

        # STEMS (Day + Year, 干系)
        self._calc_day_year_stem_shens()
        self._calc_xue_tang()
        self._calc_day_stem_only_shens()
        self._calc_wen_yu_gui()
        self._calc_ci_guan()

        # DERIVED & SPECIAL
        self._calc_three_wonders()
        self._calc_self_lu()

        # PILLAR & SEASONAL (Miscellaneous)
        self._calc_day_pillar_specials()
        self._calc_yin_yang_cha_cuo()
        self._calc_four_wastes()
        self._calc_jin_shen()
        self._calc_shi_ling()
        self._calc_tian_luo_di_wang()
        self._calc_zi_yi_sha()
        self._calc_po_sha()
        self._calc_gua_jian_sha()
        self._calc_tian_huo_sha()
        self._calc_tong_zi_sha()
        self._calc_ge_jiao_sha()
        self._calc_tian_tu_sha()
        self._calc_jian_feng_sha()

        # ADVANCED RELATIONAL
        self._calc_virtue_elegance()
        self._calc_dark_lu()

        self._result_cache = self._build_result()
        return self._result_cache

    def _build_result(self) -> Dict[str, Any]:
        """
        Assemble final output structure.
        {"神煞": {"年柱": {"神煞": [...]}, "月柱": {...}, "日柱": {...}, "时柱": {...}}}
        """
        return {
            "神煞": {
                self.pillar_names[i]: {"神煞": self.strs[i]}
                for i in range(4)
            }
        }


# ============================================================================
# PUBLIC API
# ============================================================================


def get_shen_sha(bazi, na_yin: dict, gender: int) -> Dict[str, Any]:
    """
    Public entry point for natal shen sha calculation.

    Args:
        bazi: EightChar object from lunar_python (lunar_birthday.getEightChar())
        na_yin (dict): Output of get_na_yin(bazi) — {"年柱": "海中金", ...}
        gender (int): 0 for Female, 1 for Male (consistent with BaZi library convention)

    Returns:
        dict: {
            "神煞": {
                "年柱": {"神煞": [{"名称": str, "来源": str}, ...]},
                "月柱": {"神煞": [...]},
                "日柱": {"神煞": [...]},
                "时柱": {"神煞": [...]}
            }
        }

    Raises:
        ValueError: if gender not in (0, 1)
    """
    return ShenShaCalculator(bazi, na_yin, gender).calculate()


# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    from datetime import datetime as dt
    from apps.backend.astronomer_logic.true_solar_time import get_true_solar_time
    from apps.backend.astronomer_logic.na_yin import get_na_yin
    import json

    # python -m apps.backend.astronomer_logic.natal_shen_sha

    # Example: Desmond's birth chart (1985-11-25, 17:07)
    birth_dt = dt(1985, 11, 25, 17, 7, 0)
    tst_birthday = get_true_solar_time(birth_dt, 1.3253, 103.808053)

    lunar_birthday = tst_birthday.getLunar()
    bazi = lunar_birthday.getEightChar()
    na_yin = get_na_yin(bazi)

    # Test male
    print("\n[男性神煞]")
    result_male = get_shen_sha(bazi, na_yin, gender=1)
    print(json.dumps(result_male, ensure_ascii=False, indent=2))
