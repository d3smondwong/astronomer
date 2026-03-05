"""
Shen Sha (神煞) Calculation Module

This module calculates and identifies Shen Sha (Auspicious & Inauspicious Stars) in BaZi charts.
Shen Sha are additional spiritual stars used in Chinese astrology to provide deeper insights
into a person's character, destiny, relationships, and challenges.

The module contains five main categories of Shen Sha determined by:
1. Year Branch - affects relationships and social connections
2. Month Branch - affects virtues, protection, and seasonal influences
3. Day Branch - determines command capacity and spiritual gifts
4. Heavenly Stems - relates to career, talent, and wealth
5. Pillar Combinations - special voids and unfavorable configurations

Key Function:
    get_shen_sha(lunar_birthday): Extracts all applicable Shen Sha stars from a lunar birth chart.

    Returns:
        - strs: List of stars for each pillar [Year, Month, Day, Hour]
        - all_found_shens: List of all unique stars found
        - gans: Heavenly Stems [Year, Month, Day, Hour]
        - zhis: Earthly Branches [Year, Month, Day, Hour]
"""

from lunar_python import Solar, Lunar
from datetime import datetime
from src.astronomer_calculations.solar_lunar_time import get_true_solar_time

# --- STEM & BRANCH PARTNERSHIPS ---
# Yin-Yang stem partnerships (for derived stars like 天德合)
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

# --- SHEN SHA DICTIONARIES ---
year_shens = {
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
    },  # Red Luan Star: Indicates romance, marriage, and social connections. It is considered a favorable star for relationships and social interactions.
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
    },  # Heavenly Happiness Star: Represents joy, celebrations, and auspicious events. It is associated with positive occasions such as weddings, promotions, and other happy events.
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
    },  # Peach Blossom Star: Symbolizes attractiveness, charm, and romantic opportunities. It is often associated with love and relationships, but can also indicate social popularity and charisma.
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
    },  # Lonely Star: Indicates isolation, loneliness, and a lack of support. It can suggest challenges in forming close relationships and may indicate a tendency towards solitude.
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
    "元辰": {
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

month_shens = {
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
    # --- SPECIAL SEASONAL ---
    "天赦": {"春": "戊寅", "夏": "甲午", "秋": "戊申", "冬": "甲子"},
}

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

day_heavenly_stem_shens = {
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
        # Values: Lists of full pillars (2 chars) or single branches (1 char)
        # Full pillar = stem+branch check; Single branch = branch-only check
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
    "天官": {
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
    "阳刃": {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"},
    "阴刃": {
        "乙": "辰",  # Guan Dai stage for Yin Wood
        "丁": "未",  # Guan Dai stage for Yin Fire
        "己": "未",  # Guan Dai stage for Yin Earth
        "辛": "戌",  # Guan Dai stage for Yin Metal
        "癸": "丑",  # Guan Dai stage for Yin Water
    },
}

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

# Stars that are NOT allowed to land on their own trigger pillar
SELF_EXCLUSION_STARS = {"桃花", "孤辰", "寡宿", "驿马", "劫煞", "亡神"}


def add_shen(pillar_idx, shen_name, strs, all_found_shens):
    """Helper to add shen to pillar and track unique shens"""
    if shen_name not in strs[pillar_idx]:
        strs[pillar_idx] = f"{strs[pillar_idx]} {shen_name}".strip()
        if shen_name not in all_found_shens:
            all_found_shens.append(shen_name)


def get_shen_sha(lunar_birthday):
    """
    Extract basic Shen Sha (神煞) stars from a BaZi chart using lookup tables.
    Sections 1-5: Year/Month/Day/Stem-based stars and pillar specials.

    Returns:
    - strs: [Year_Stars, Month_Stars, Day_Stars, Hour_Stars]
    - unique_shens: List of unique stars found
    - gans: Heavenly Stems [Y, M, D, H]
    - zhis: Earthly Branches [Y, M, D, H]
    """
    baZi = lunar_birthday.getEightChar()

    gans = [baZi.getYearGan(), baZi.getMonthGan(), baZi.getDayGan(), baZi.getTimeGan()]
    zhis = [baZi.getYearZhi(), baZi.getMonthZhi(), baZi.getDayZhi(), baZi.getTimeZhi()]

    me = gans[2]  # Day Stem (Day Master)
    year_stem = gans[0]  # Year Stem
    day_pillar = gans[2] + zhis[2]
    hour_pillar = gans[3] + zhis[3]

    # Map month branches to Chinese seasons for '天赦' and '四废'
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
    birth_season = seasons_map.get(zhis[1])

    strs = ["", "", "", ""]
    all_found_shens = []

    # ============================================================
    # 1. YEAR BRANCH BASED (Year Branch -> Other Pillars)
    # ============================================================
    for item, mapping in year_shens.items():
        lookup = mapping.get(zhis[0], "")
        for i in range(4):
            # Skip if the star is in exclusion list and we are looking at the trigger pillar
            if item in SELF_EXCLUSION_STARS and i == 0:
                continue

            if zhis[i] in lookup:
                # Special handling for Peach Blossom
                if item == "桃花":
                    wall_type = "墙内桃花" if i < 2 else "墙外桃花"
                    add_shen(i, wall_type, strs, all_found_shens)
                else:
                    add_shen(i, item, strs, all_found_shens)

    # ============================================================
    # 2. MONTH BRANCH BASED (Month Branch -> All Pillars)
    # ============================================================
    for item, mapping in month_shens.items():

        if item == "天赦":
            target_pillar = mapping.get(birth_season)
            for i in range(4):
                if (gans[i] + zhis[i]) == target_pillar:
                    add_shen(i, "天赦", strs, all_found_shens)

        else:
            lookup = mapping.get(zhis[1], "")
            if isinstance(lookup, str):
                for i in range(4):
                    # Only check Branches for specific health/sha stars
                    if item in ["天医", "血刃"]:
                        if zhis[i] in lookup:
                            add_shen(i, item, strs, all_found_shens)
                    # Check Stems for Virtues
                    else:
                        if gans[i] in lookup or zhis[i] in lookup:
                            add_shen(i, item, strs, all_found_shens)

    # --- Virtue Union (Tian De He) - Dynamic Computation ---
    # Logic: If a stem is the partner of the Heavenly Virtue (天德) for this month,
    # and that partner stem appears anywhere in the chart, add 天德合
    tian_de_stem = month_shens["天德"].get(zhis[1])  # Get virtue stem for this month
    if tian_de_stem:
        partner_stem = stem_partners.get(tian_de_stem)  # Get its partner
        if partner_stem:
            for i in range(4):
                if gans[i] == partner_stem:
                    add_shen(i, "天德合", strs, all_found_shens)

    # --- Month Virtue Union (Yue De He) - Dynamic Computation ---
    # 月德
    yue_de_stem = month_shens["月德"].get(zhis[1])  # Get month virtue stem
    if yue_de_stem:
        partner_stem = stem_partners.get(yue_de_stem)
        if partner_stem:
            for i in range(4):
                if gans[i] == partner_stem:
                    add_shen(i, "月德合", strs, all_found_shens)

    # --- Combined Virtue Union (Tian Yue De He) - Dynamic Computation ---
    # Both 天德合 and 月德合 partners appear in the same pillar
    if tian_de_stem and yue_de_stem:
        tian_partner = stem_partners.get(tian_de_stem)
        yue_partner = stem_partners.get(yue_de_stem)
        if tian_partner and yue_partner and tian_partner == yue_partner:
            # Same partner for both virtues - rare but powerful
            for i in range(4):
                if gans[i] == tian_partner:
                    add_shen(i, "天月德合", strs, all_found_shens)

    # ============================================================
    # 3. DAY BRANCH BASED (Day Branch -> All Pillars)
    # ============================================================
    for item, mapping in day_earthly_branches_shens.items():
        lookup = mapping.get(zhis[2], "")
        for i in range(4):
            # Skip if the star is in exclusion list and we are looking at the trigger pillar
            if item in SELF_EXCLUSION_STARS and i == 2:
                continue

            if zhis[i] in lookup:
                # Special handling for Peach Blossom
                if item == "桃花":
                    wall_type = "墙内桃花" if i < 2 else "墙外桃花"
                    add_shen(i, wall_type, strs, all_found_shens)
                else:
                    add_shen(i, item, strs, all_found_shens)

    # --- Peach Blossom "Bath" Activation ---
    # Map Day Master (Stem) to its specific "Bath" (沐浴) branch
    bath_map = {
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
    my_bath_branch = bath_map.get(me)

    for i in range(4):
        if "桃花" in strs[i] and zhis[i] == my_bath_branch:
            # You can either rename it or add a special tag
            add_shen(i, "沐浴桃花", strs, all_found_shens)

    # ============================================================
    # 4. STEM BASED (PROFESSIONAL: Day Stem as Primary Driver)
    # ============================================================

    # PRIMARY LOOP: Day Stem derived stars (Standard professional approach)
    for item, mapping in day_heavenly_stem_shens.items():
        lookup = mapping.get(me, "")  # Day Stem only
        if not lookup:
            continue
        for i in range(4):
            if item == "词馆":
                pillar_str = gans[i] + zhis[i]
                # lookup is now a list of pillars/branches
                for entry in lookup:
                    if len(entry) == 2:  # Full pillar match (e.g., "庚寅")
                        if pillar_str == entry:
                            add_shen(i, item, strs, all_found_shens)
                    else:  # Single branch match (e.g., "巳")
                        if zhis[i] == entry:
                            add_shen(i, item, strs, all_found_shens)
            else:
                if zhis[i] in lookup:
                    add_shen(i, item, strs, all_found_shens)

    # SECONDARY LOOP: Year Stem derived stars (Historical/optional, with distinct labeling)
    # Only apply Year Stem to Heavenly Nobles - these traditionally recognize both sources
    year_stem_only_stars = {"昼天乙", "夜天乙"}

    for item, mapping in day_heavenly_stem_shens.items():
        if item not in year_stem_only_stars:
            continue
        lookup = mapping.get(year_stem, "")  # Year Stem only, for specific stars
        if not lookup:
            continue
        for i in range(4):
            if zhis[i] in lookup:
                # Label these distinctly to show they come from ancestry (Year Stem)
                shen_name = f"年属{item}"
                # Only add if not already present from Day Stem derivation
                if shen_name not in strs[i]:
                    add_shen(i, shen_name, strs, all_found_shens)

    # --- Yin Blade (阴刃) ---
    yin_blade_data = day_heavenly_stem_shens.get("阴刃", {}).get(me, "")
    if yin_blade_data:
        for i in range(4):
            # Using 'in' allows for strings like "卯" or even multiple "卯辰"
            if zhis[i] in yin_blade_data:
                add_shen(i, "阴刃", strs, all_found_shens)

    # ============================================================
    # 5 DERIVED STARS (Relationship-Based)
    # ============================================================

    # --- Yang Blade Pairing (阳刃伏藏) ---
    # Check if Day Stem has Yang Blade, and its partner appears
    yang_ren_branch = day_heavenly_stem_shens["阳刃"].get(me, "")
    if yang_ren_branch:
        partner_stem = stem_partners.get(me)
        if partner_stem:
            for i in range(4):
                if zhis[i] in yang_ren_branch and gans[i] == partner_stem:
                    add_shen(i, "阳刃伏藏", strs, all_found_shens)

    # --- Fortune & Virtue (福禄双美) ---
    # Two activation pathways: inherited (pillar list) OR earned (Fu Xing + Lu Shen combo)
    fu_lu_special_pillars = ["丁卯", "癸未", "甲寅"]  # Pillar-specific list

    for i in range(4):
        current_pillar = gans[i] + zhis[i]

        # Path 1: Pillar-specific inheritance (Section 5 legacy check)
        is_special_pillar = current_pillar in fu_lu_special_pillars

        # Path 2: Operative combination check (both Fu Xing and Lu Shen present)
        has_combo = "福星" in strs[i] and "禄神" in strs[i]

        # Unified activation: Either pathway triggers the star
        if is_special_pillar or has_combo:
            add_shen(i, "福禄双美", strs, all_found_shens)

    # --- Three Wonders (三奇贵人) - Sequential Stem Patterns ---
    # Check if three consecutive pillars have stems in specific sequential order
    trios = [
        (["甲", "戊", "庚"], "天上三奇"),  # Heaven's Three Wonders
        (["乙", "丙", "丁"], "地下三奇"),  # Earth's Three Wonders
        (["辛", "壬", "癸"], "人中三奇"),  # Human's Three Wonders
    ]

    # Check sequences: Year-Month-Day (0,1,2) or Month-Day-Hour (1,2,3)
    for sequence in [(0, 1, 2), (1, 2, 3)]:
        current_stems = [gans[i] for i in sequence]
        for trio_stems, name in trios:
            if current_stems == trio_stems:
                for i in sequence:
                    add_shen(i, name, strs, all_found_shens)

    # ============================================================
    # 6. SPECIAL SINGLE-PILLAR FORMATIONS
    # ============================================================

    special_formations_map = {
        "戊辰": "巳命互禄",
        "己未": "午命互禄",
        "丙辰": "巳命互禄",
        "丁未": "午命互禄",
        "甲寅": "寅命自禄",
        "乙卯": "卯命自禄",
        "庚申": "申命自禄",
        "辛酉": "酉命自禄",
        "癸子": "子命自禄",
        "壬亥": "亥命自禄",
        "壬戌": "亥命互禄",
        "庚戌": "申命互禄",
        "甲辰": "寅命互禄",
        "乙未": "卯命互禄",
        "丁巳": "巳中藏丙",
        "癸亥": "亥中藏壬",
    }

    for i in range(4):
        current_pillar = gans[i] + zhis[i]
        if current_pillar in special_formations_map:
            formation_name = special_formations_map[current_pillar]
            add_shen(i, formation_name, strs, all_found_shens)

    # ============================================================
    # 7. PILLAR & SPECIALS
    # ============================================================

    # --- Kong Wang (Void) ---
    void_branches = pillar_shens["空亡"].get(day_pillar, "")
    for i in (0, 1, 3):
        if zhis[i] in void_branches:
            add_shen(i, "空亡", strs, all_found_shens)

    # --- Day Pillar Specials ---
    day_checks = {
        "阴阳差错": pillar_shens.get("阴阳差错", []),
        "十恶大败": pillar_shens.get("十恶大败", []),
        "魁罡": pillar_shens.get("魁罡", []),
        "扩展魁罡": pillar_shens.get("扩展魁罡", []),
    }
    for item, target_list in day_checks.items():
        if day_pillar in target_list:
            add_shen(2, item, strs, all_found_shens)

    # --- Seasonal Day Pillar Check (Si Fei) ---
    if day_pillar in pillar_shens["四废"].get(birth_season, []):
        add_shen(2, "四废", strs, all_found_shens)

    # --- Hour Pillar Check (Jin Shen) ---
    if hour_pillar in pillar_shens["金神"]:
        add_shen(3, "金神", strs, all_found_shens)

    # --- Ten Spirits (Shi Ling) - Pillar Specific ---
    for i in range(4):
        pillar = gans[i] + zhis[i]
        if pillar in pillar_shens.get("十灵", []):
            add_shen(i, "十灵", strs, all_found_shens)

    # --- Child Sha (Tong Zi Sha) - Seasonal ---
    if birth_season in ["夏", "冬"]:
        for i in range(4):
            if zhis[i] in "卯辰未":
                add_shen(i, "童子煞", strs, all_found_shens)

    # ============================================================
    # 8. RELATIONAL STARS (Inter-Pillar Interactions)
    # ============================================================

    hu_lu_results = []
    jia_gong_lu_results = []  # Consolidated Virtual Lu
    jia_gong_gui_results = []  # Consolidated Virtual Noble

    pillar_names_cn = ["年柱", "月柱", "日柱", "时柱"]
    branch_order = [
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
    lu_map = day_heavenly_stem_shens["禄神"]
    my_lu = lu_map.get(me)

    # --- 1. Hu Lu (互禄) Check (Physical Exchange) ---
    for i in range(4):
        for j in range(i + 1, 4):
            if lu_map.get(gans[i]) == zhis[j] and lu_map.get(gans[j]) == zhis[i]:
                is_adj = abs(i - j) == 1
                hu_lu_results.append(
                    {
                        "组合": f"{pillar_names_cn[i]}-{pillar_names_cn[j]}",
                        "紧贴": is_adj,
                        "状态": "正互" if is_adj else "遥互",
                        "描述": f"{gans[i]}{zhis[i]}与{gans[j]}{zhis[j]}互换禄神",
                    }
                )

    # --- 2. Virtual Lu Check (Jia/Gong Lu) ---
    # Note: Classical recommendation - Only summon if not physically in the chart
    if my_lu and my_lu not in zhis:
        idx = branch_order.index(my_lu)
        prev_n, next_n = branch_order[(idx - 1) % 12], branch_order[(idx + 1) % 12]

        if prev_n in zhis and next_n in zhis:
            p1, p2 = zhis.index(prev_n), zhis.index(next_n)
            is_adj = abs(p1 - p2) == 1
            # Methodology: Day-Hour is Gong (拱), others are Jia (夹)
            is_gong = p1 >= 2 and p2 >= 2
            label = "拱禄" if is_gong else "夹禄"
            prefix = "正" if is_adj else "遥"

            # Order pillars chronologically for description
            p_min, p_max = min(p1, p2), max(p1, p2)

            jia_gong_lu_results.append(
                {
                    "虚邀地支": my_lu,
                    "紧贴": is_adj,
                    "状态": f"{prefix}{label}",
                    "来源柱": [pillar_names_cn[p_min], pillar_names_cn[p_max]],
                    "说明": f"{pillar_names_cn[p_min]}与{pillar_names_cn[p_max]}{prefix}{label}出{my_lu}",
                }
            )

    # --- 3. Virtual Noble Check (Jia/Gong Gui) ---
    noble_branches = list(
        set(
            [
                day_heavenly_stem_shens["昼天乙"].get(me),
                day_heavenly_stem_shens["夜天乙"].get(me),
            ]
        )
    )

    for nb in noble_branches:
        if nb and nb not in zhis:
            idx = branch_order.index(nb)
            p_nb, n_nb = branch_order[(idx - 1) % 12], branch_order[(idx + 1) % 12]

            if p_nb in zhis and n_nb in zhis:
                p1, p2 = zhis.index(p_nb), zhis.index(n_nb)
                is_adj = abs(p1 - p2) == 1
                is_gong = p1 >= 2 and p2 >= 2
                label = "拱贵" if is_gong else "夹贵"
                prefix = "正" if is_adj else "遥"

                # Order pillars chronologically for description
                p_min, p_max = min(p1, p2), max(p1, p2)

                jia_gong_gui_results.append(
                    {
                        "虚邀贵人": nb,
                        "紧贴": is_adj,
                        "状态": f"{prefix}{label}",
                        "说明": f"{pillar_names_cn[p_min]}与{pillar_names_cn[p_max]}{prefix}{label}出天乙贵人{nb}",
                    }
                )

    # Final assembly into the relational_shens object
    relational_shens = {
        "互禄": hu_lu_results,
        "虚邀禄": jia_gong_lu_results,
        "虚邀贵": jia_gong_gui_results,
    }

    # ============================================================
    # 9. ADVANCED RELATIONAL (De Xiu & An Lu)
    # ============================================================

    # --- De Xiu Gui Ren (德秀贵人) ---
    de_xiu_result = {}
    dexiu_map = {
        "寅": "丙丁戊癸",
        "午": "丙丁戊癸",
        "戌": "丙丁戊癸",  # Fire
        "申": "壬癸戊癸丙辛甲己",
        "子": "壬癸戊癸丙辛甲己",
        "辰": "壬癸戊癸丙辛甲己",  # Water
        "亥": "甲乙丁壬",
        "卯": "甲乙丁壬",
        "未": "甲乙丁壬",  # Wood
        "巳": "庚辛乙庚",
        "酉": "庚辛乙庚",
        "丑": "庚辛乙庚",  # Metal
    }

    month_req = dexiu_map.get(zhis[1], "")
    dexiu_distribution = {}

    if month_req:
        for i in range(4):
            if gans[i] in month_req:
                add_shen(i, "德秀", strs, all_found_shens)
                dexiu_distribution[pillar_names_cn[i]] = gans[i]

    if dexiu_distribution:
        de_xiu_result = {
            "激活": True,
            "触发月令": zhis[1],
            "分布明细": dexiu_distribution,
        }

    # --- An Lu (暗禄) ---
    an_lu_map = {
        "甲": "亥",
        "乙": "戌",
        "丙": "申",
        "丁": "未",
        "戊": "申",
        "己": "未",
        "庚": "巳",
        "辛": "辰",
        "壬": "寅",
        "癸": "丑",
    }

    target_zhi = an_lu_map.get(me)
    an_lu_distribution = {}
    an_lu_result = {}

    if target_zhi:
        for i in range(4):
            if zhis[i] == target_zhi:
                add_shen(i, "暗禄", strs, all_found_shens)
                an_lu_distribution[pillar_names_cn[i]] = zhis[i]

    if an_lu_distribution:
        an_lu_result = {
            "激活": True,
            "触发日干": me,
            "对应支": target_zhi,
            "分布明细": an_lu_distribution,
        }

    # --- Build structured JSON output ---
    pillar_dynamics = {
        pillar_names_cn[i]: {
            "天干": gans[i],
            "地支": zhis[i],
            "神煞": strs[i].split() if strs[i] else [],
        }
        for i in range(4)
    }

    # Combine all findings into the final relational object
    relational_shens = {
        "互禄明细": hu_lu_results,
        "虚邀禄": jia_gong_lu_results,  # From consolidated Section 6
        "虚邀贵": jia_gong_gui_results,  # From consolidated Section 6
    }

    # Only add these if they were actually triggered
    if de_xiu_result:
        relational_shens["德秀贵人"] = de_xiu_result

    if an_lu_result:
        relational_shens["暗禄"] = an_lu_result

    # Final structure
    result = {
        "柱位神煞": pillar_dynamics,
        "关系神煞": relational_shens,
    }

    return {"神煞": result}


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from src.astronomer_calculations.bazi_pillars import get_bazi_pillars

    # python -m src.astronomer_calculations.shen_sha

    # Desmond's birthday example
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)

    # Sample birthday example
    # solar_birthday = Solar.fromYmdHms(1990, 1, 30, 4, 0, 0)  # Create solar date
    # datetime_birthday = datetime(1990, 1, 30, 4, 0, 0)  # Create datetime object
    # tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)

    print("=" * 60)
    print("阳历生日: " + solar_birthday.toYmdHms())
    print("真太阳时生日: " + tst_birthday.toYmdHms())
    print("=" * 60)

    print("")
    print("八字")
    bazi_json = get_bazi_pillars(tst_birthday.getLunar())
    print(f"八字: {bazi_json}")

    lunar_birthday = tst_birthday.getLunar()
    result = get_shen_sha(lunar_birthday)

    # Print JSON output
    print("\n```json")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("```\n")
