"""
Liu Nian & Liu Yue (流年 & 流月 - Annual & Monthly Luck Cycles) Calculation Module

This module calculates the Annual Luck Cycles (Liu Nian) and Monthly Luck Cycles (Liu Yue)
for a given lunar birthday and gender.

Each Liu Nian cycle lasts 1 year and represents annual fortune during a 大运 (Da Yun) period.
Liu Yue cycles last 1 month and represent monthly fortune within each Liu Nian.

Structure mirrors 大运 and 小运:
1. 序号 (Sequence Number): Annual/Monthly index
2. 干支 (Heavenly Stem & Earthly Branch): Year/Month's sexagenary pair
3. 旬/旬空 (Sexagenary Cycle & Void Days): Based on stem-branch pair
4. 五行 (Five Elements): Stem and branch elements with polarity (阳/阴)
5. 纳音 (Nayin - Harmonic Resonance Element): Descriptive element for stem-branch pair
6. 地势 (Life Stage): 12-stage positional strength from 长生十二宫 system
7. 十神 (Ten Gods): Primary theme (Year/Month Stem) + Hidden themes (Hidden Stems in Branch)
8. 作用 (Interactions): Branch and Stem interactions with birth chart (1x4 scan)

Key Functions:
    get_liu_nian(lunar_birthday, gender, start_year=None, num_years=10):
        Calculates Annual Luck Cycles analysis.

    get_liu_yue(lunar_birthday, gender, year_index=0):
        Calculates Monthly Luck Cycles for a specific annual period.

    get_liu_nian_ye(lunar_birthday, gender, start_year=None, num_years=10):
        Calculates complete Liu Nian and Liu Yue combined analysis.

Output Format:
    All dictionary keys and values use Chinese characters for consistency.
    Integrates lunar-python library data for accuracy and reliability.
    Interactions are actionable event alerts for each period.
"""

from lunar_python import Lunar, Solar
from lunar_python.util import LunarUtil
from lunar_python.EightChar import EightChar
from datetime import datetime, timedelta
from typing import Optional

# Import shared maps, functions, and constants from da_yun module
from src.astronomer_calculations.da_yun import (
    # Helper functions
    _get_stem_wu_xing,
    _get_branch_wu_xing,
    _get_nayin,
    _get_di_shi,
    _get_shi_shen_for_stem_pair,
    _get_hidden_stems_shi_shen,
    _detect_da_yun_interactions,
    DI_SHI_TABLE,
    STR_STEM,
    STR_BRANCH,
)

from src.astronomer_calculations.wu_xing import (
    Pillar,
    Stem,
    Branch,
)

# Inline nine-star thin-wrapper (lunar-python canonical fields + project 描述/关键词)
_NINE_STAR_DESCRIPTIONS = {
    1: {
        "描述": "桃花星，主人缘、姻缘、社交。利感情发展，旺人脉关系。",
        "关键词": ["桃花", "人缘", "姻缘", "社交", "大吉", "水"],
        "宜": ["婚恋", "社交", "签约", "交友"],
        "忌": []
    },
    2: {
        "描述": "病符星，主疾病、灾祸、伤痛。易有健康问题，需注意身体。",
        "关键词": ["病符", "疾病", "灾祸", "伤痛", "大凶", "土"],
        "宜": ["静养", "祈福", "体检"],
        "忌": ["动土", "装修", "嘈杂"]
    },
    3: {
        "描述": "是非星，主口舌、官非、争斗。易有纠纷争执，需谨言慎行。",
        "关键词": ["是非", "官非", "争斗", "口舌", "凶", "木"],
        "宜": ["低调", "忍耐", "独处"],
        "忌": ["争吵", "诉讼", "冲动"]
    },
    4: {
        "描述": "文昌星，主学业、考试、功名。利读书进取，旺文采才华。",
        "关键词": ["文昌", "学业", "考试", "功名", "吉", "木"],
        "宜": ["读书", "考试", "创作", "学习"],
        "忌": []
    },
    5: {
        "描述": "五黄煞，主凶灾、意外、破败。最凶之星，诸事不宜，宜静不宜动。",
        "关键词": ["五黄", "凶灾", "意外", "破败", "大凶", "土"],
        "宜": ["静养", "避让", "祈福"],
        "忌": ["动土", "搬迁", "开工", "重大决策"]
    },
    6: {
        "描述": "偏财星，主武贵、偏财、远行。利出差远行，旺偏财机遇。",
        "关键词": ["偏财", "武贵", "远行", "晋升", "吉", "金"],
        "宜": ["投资", "出差", "晋升", "求偏财"],
        "忌": []
    },
    7: {
        "描述": "破军星，主破财、盗贼、损失。易有财物损失，需防盗防骗。",
        "关键词": ["破财", "盗贼", "损失", "破坏", "凶", "金"],
        "宜": ["清理", "整顿", "断舍离"],
        "忌": ["投资", "借贷", "担保"]
    },
    8: {
        "描述": "正财星，主事业、置业、财运。利求财创业，旺事业成就。",
        "关键词": ["正财", "事业", "置业", "财运", "大吉", "土"],
        "宜": ["求财", "置业", "开业", "求正财"],
        "忌": []
    },
    9: {
        "描述": "喜庆星，主喜事、庆典、姻缘。利婚嫁喜事，旺家庭和睦。",
        "关键词": ["喜庆", "喜事", "庆典", "姻缘", "吉", "火"],
        "宜": ["婚嫁", "聚会", "庆典", "喜事"],
        "忌": []
    }
}


def get_nine_star(nine_star_obj) -> dict:
    """
    Convert a lunar-python NineStar object into a JSON-ready dict.
    """
    if nine_star_obj is None:
        return {}

    # 1. Extract all raw data first
    number = nine_star_obj.getNumber()
    index = nine_star_obj.getIndex() + 1  # Convert 0-based index to 1-based for descriptions

    # 2. Build structured Qi Men data
    qi_men = _build_qi_men_data(nine_star_obj)

    # 3. Build the base star data
    star_data = {
        "序号": number,
        "名称": nine_star_obj.toFullString(),
        "颜色": nine_star_obj.getColor(),
        "方位": f"{nine_star_obj.getPosition()} ({nine_star_obj.getPositionDesc()})",
        "五行": nine_star_obj.getWuXing(),
        "北斗": nine_star_obj.getNameInBeiDou(),
        "太乙": {
            "名称": nine_star_obj.getNameInTaiYi(),
            "类型": nine_star_obj.getTypeInTaiYi()
        },
        "玄空": {
            "名称": nine_star_obj.getNameInXuanKong(),
            "吉凶": nine_star_obj.getLuckInXuanKong()
        },
        "奇门": qi_men,
        "描述": _NINE_STAR_DESCRIPTIONS[index]["描述"],
        "关键词": _NINE_STAR_DESCRIPTIONS[index]["关键词"],
        "宜": _NINE_STAR_DESCRIPTIONS[index]["宜"],
        "忌": _NINE_STAR_DESCRIPTIONS[index]["忌"]
    }

    return star_data


def _build_qi_men_data(nine_star_obj) -> dict:
    """Build structured Qi Men data from NineStar object."""
    qi_men = {
        "九星": nine_star_obj.getNameInQiMen(),
        "九星吉凶": nine_star_obj.getLuckInQiMen()
    }

    # Handle 八门 (BaMen) if available
    if hasattr(nine_star_obj, "getBaMenInQiMen"):
        ba_men = nine_star_obj.getBaMenInQiMen()
        if ba_men:
            # Convert to string if it's a list/tuple
            if isinstance(ba_men, (list, tuple)):
                ba_men = "".join(map(str, ba_men))

            qi_men["八门"] = str(ba_men)

            # Add Yin/Yang if available
            if hasattr(nine_star_obj, "getYinYangInQiMen"):
                yin_yang = nine_star_obj.getYinYangInQiMen()
                if yin_yang:
                    qi_men["八门阴阳"] = yin_yang

    return qi_men


# ============================================================================
# 财神 (Wealth), 喜神 (Joy), 福神 (Blessing), 贵人 (Noble) CONSTANTS & MAPPINGS
# ============================================================================

STEM_POSITION_CAI_XI_FU_GUI_MAPPING = {
    "甲": {
        "财神": "东北",
        "喜神": "东北",
        "福神": "正北",
        "阳贵": "西南",
        "阴贵": "东北",
    },
    "乙": {
        "财神": "东北",
        "喜神": "西北",
        "福神": "西南",
        "阳贵": "正北",
        "阴贵": "西南",
    },
    "丙": {
        "财神": "正西",
        "喜神": "西南",
        "福神": "正东",
        "阳贵": "正西",
        "阴贵": "西北",
    },
    "丁": {
        "财神": "正西",
        "喜神": "正南",
        "福神": "正东",
        "阳贵": "西北",
        "阴贵": "正西",
    },
    "戊": {
        "财神": "正北",
        "喜神": "东南",
        "福神": "正北",
        "阳贵": "西南",
        "阴贵": "东北",
    },
    "己": {
        "财神": "正北",
        "喜神": "东北",
        "福神": "正南",
        "阳贵": "正北",
        "阴贵": "西南",
    },
    "庚": {
        "财神": "正东",
        "喜神": "西北",
        "福神": "西南",
        "阳贵": "东北",
        "阴贵": "西南",
    },
    "辛": {
        "财神": "正东",
        "喜神": "西南",
        "福神": "西南",
        "阳贵": "东北",
        "阴贵": "正南",
    },
    "壬": {
        "财神": "正南",
        "喜神": "正南",
        "福神": "西北",
        "阳贵": "正东",
        "阴贵": "东南",
    },
    "癸": {
        "财神": "正南",
        "喜神": "东南",
        "福神": "正西",
        "阳贵": "东南",
        "阴贵": "正东",
    },
}

# ============================================================================
# 财神 (Wealth), 喜神 (Joy), 福神 (Blessing), 贵人 (Noble) Functions
# ============================================================================


def _get_cai_xi_fu_gui_positions(stem: str) -> dict:
    """
    Get Cai Shen, Xi Shen, Fu Shen, and Gui Ren (noble) positions for a given heavenly stem.

    These represent auspicious directions for wealth, joy, blessings, and noble support.

    Args:
        stem (str): Heavenly stem (e.g., "甲", "乙", etc.)

    Returns:
        dict: Dictionary with positions for 财神, 喜神, 福神, 阳贵, 阴贵
    """
    if stem not in STEM_POSITION_CAI_XI_FU_GUI_MAPPING:
        return {
            "财神": "未知",
            "喜神": "未知",
            "福神": "未知",
            "阳贵": "未知",
            "阴贵": "未知",
        }

    positions = STEM_POSITION_CAI_XI_FU_GUI_MAPPING[stem]
    return {
        "财神": positions.get("财神", "未知"),
        "喜神": positions.get("喜神", "未知"),
        "福神": positions.get("福神", "未知"),
        "阳贵": positions.get("阳贵", "未知"),
        "阴贵": positions.get("阴贵", "未知"),
    }


def _get_cai_xi_fu_gui_guidance(stem: str) -> dict:
    """
    Get guidance descriptions for Cai Shen, Xi Shen, Fu Shen, and Gui Ren, personalized by stem and position.

    Args:
        stem (str): Heavenly stem (e.g., "甲", "乙", etc.)

    Returns:
        dict: Dictionary with descriptions for each position type, including the actual positions
    """
    if stem not in STEM_POSITION_CAI_XI_FU_GUI_MAPPING:
        return {
            "财神": "未知",
            "喜神": "未知",
            "福神": "未知",
            "阳贵": "未知",
            "阴贵": "未知",
        }

    pos = STEM_POSITION_CAI_XI_FU_GUI_MAPPING[stem]

    return {
        "财神": f"财位在{pos['财神']}。建议在此方位处理财务或办公，以增强商业直觉。",
        "喜神": f"喜神在{pos['喜神']}。利于在此方位进行社交、相亲或商谈喜庆之事。",
        "福神": f"福神在{pos['福神']}。适合在此方位休息或安放床铺，主身体健康、神清气爽。",
        "阳贵": f"白天的事务若遇阻碍，向{pos['阳贵']}方寻求帮助，易获上司或长辈提携。",
        "阴贵": f"暗中化解难题之星。晚间或私下协调事务，宜向{pos['阴贵']}方寻求助力。",
    }


def _get_cai_xi_fu_gui_analysis(stem: str) -> dict:
    """
    Get 方位分析 (Auspicious Position Analysis) for a given heavenly stem.

    For each fortune type (财神, 喜神, 福神, 阳贵, 阴贵), provides both the auspicious
    direction and interpretive guidance.

    Args:
        stem (str): Heavenly stem (e.g., "甲", "乙", etc.)

    Returns:
        dict: Dictionary keyed by fortune type, each containing:
            - 方位: Auspicious direction
            - 指引: Interpretive guidance message
    """
    positions = _get_cai_xi_fu_gui_positions(stem)
    guidance = _get_cai_xi_fu_gui_guidance(stem)

    return {
        "财神": {
            "方位": positions["财神"],
            "指引": guidance["财神"],
        },
        "喜神": {
            "方位": positions["喜神"],
            "指引": guidance["喜神"],
        },
        "福神": {
            "方位": positions["福神"],
            "指引": guidance["福神"],
        },
        "阳贵": {
            "方位": positions["阳贵"],
            "指引": guidance["阳贵"],
        },
        "阴贵": {
            "方位": positions["阴贵"],
            "指引": guidance["阴贵"],
        },
    }


# ============================================================================
# TAI SUI CONSTANTS & MAPPINGS
# ============================================================================


# Tai Sui position by zodiac (年干支 -> 太岁位置). Use the lunar-python library's getYearPositionTaiSuiDesc() for accurate position, but this is the traditional mapping for reference:
_TAI_SUI_POSITIONS = {
    "鼠": "正北",
    "牛": "东北",
    "虎": "东北",
    "兔": "正东",
    "龙": "东南",
    "蛇": "东南",
    "马": "正南",
    "羊": "西南",
    "猴": "西南",
    "鸡": "正西",
    "狗": "西北",
    "猪": "西北",
}

# Sui Po (Opposite of Tai Sui, 180 degrees)
_SUI_PO_OPPOSITES = {
    "鼠": "正南",
    "马": "正北",
    "牛": "西南",
    "羊": "东北",
    "虎": "西南",
    "猴": "东北",
    "兔": "正西",
    "鸡": "正东",
    "龙": "西北",
    "狗": "东南",
    "蛇": "西北",
    "猪": "东南",
}

# San Sha (Three Killings) by element group (三合)
# Triple Combination groups: Fire (寅午戌), Water (申子辰), Wood (亥卯未), Metal (巳酉丑)
_SAN_SHA_BY_ELEMENT = {
    # Fire years (寅午戌) -> San Sha in North (亥, 子, 丑)
    "虎": "正北 (亥子丑)",
    "马": "正北 (亥子丑)",
    "狗": "正北 (亥子丑)",
    # Water years (申子辰) -> San Sha in South (巳, 午, 未)
    "猴": "正南 (巳午未)",
    "鼠": "正南 (巳午未)",
    "龙": "正南 (巳午未)",
    # Wood years (亥卯未) -> San Sha in West (申, 酉, 戌)
    "猪": "正西 (申酉戌)",
    "兔": "正西 (申酉戌)",
    "羊": "正西 (申酉戌)",
    # Metal years (巳酉丑) -> San Sha in East (寅, 卯, 辰)
    "蛇": "正东 (寅卯辰)",
    "鸡": "正东 (寅卯辰)",
    "牛": "正东 (寅卯辰)",
}

# Branch to Zodiac Animal mapping (支 -> 生肖)
_BRANCH_TO_ZODIAC = {
    "子": "鼠",
    "丑": "牛",
    "寅": "虎",
    "卯": "兔",
    "辰": "龙",
    "巳": "蛇",
    "午": "马",
    "未": "羊",
    "申": "猴",
    "酉": "鸡",
    "戌": "狗",
    "亥": "猪",
}

# Conflict relationship definitions
_DIRECT_CLASH = {
    "鼠": "马",
    "马": "鼠",
    "牛": "羊",
    "羊": "牛",
    "虎": "猴",
    "猴": "虎",
    "兔": "鸡",
    "鸡": "兔",
    "龙": "狗",
    "狗": "龙",
    "蛇": "猪",
    "猪": "蛇",
}

_HARM_CLASH = {
    "鼠": "羊",
    "羊": "鼠",
    "牛": "马",
    "马": "牛",
    "虎": "蛇",
    "蛇": "虎",
    "兔": "龙",
    "龙": "兔",
    "猴": "猪",
    "猪": "猴",
    "鸡": "狗",
    "狗": "鸡",
}

_DESTRUCTION_CLASH = {
    "鼠": "鸡",
    "鸡": "鼠",
    "兔": "马",
    "马": "兔",
    "虎": "猪",
    "猪": "虎",
    "龙": "牛",
    "牛": "龙",
    "蛇": "猴",
    "猴": "蛇",
    "羊": "狗",
    "狗": "羊",
}

# Complete punishment relationships
_PUNISHMENT_TRIOS = {
    # 无恩之刑 - 寅巳申
    "寅巳申": {
        "name": "无恩之刑",
        "meaning": "忘恩负义，以怨报德，易有官非诉讼",
        "members": ["虎", "蛇", "猴"],
        "severity": {
            1: "轻微影响，多指情绪波动",
            2: "明显冲突，易有口舌是非",
            3: "严重刑伤，官非诉讼或健康问题",
        },
    },
    # 恃势之刑 - 丑未戌
    "丑未戌": {
        "name": "恃势之刑",
        "meaning": "恃势凌人，家庭不和，易有财务纠纷",
        "members": ["牛", "羊", "狗"],
        "severity": {
            1: "轻微固执，沟通不畅",
            2: "明显争执，家庭矛盾",
            3: "严重纠纷，财务损失",
        },
    },
    # 无礼之刑 - 子卯
    "子卯": {
        "name": "无礼之刑",
        "meaning": "言行无礼，桃花纠纷，情绪失控",
        "members": ["鼠", "兔"],
        "severity": {1: "情绪波动，小摩擦", 2: "严重时，桃花劫或人际关系紧张"},
    },
}

# Self-punishment signs (when alone)
_SELF_PUNISHMENT = {
    "龙": "自刑，自我施压，容易钻牛角尖",
    "马": "自刑，躁动不安，容易决策失误",
    "鸡": "自刑，追求完美，易自我否定",
    "猪": "自刑，慵懒放纵，易错失良机",
}

# Store all signs that are in punishment relationships
_ALL_PUNISHMENT_SIGNS = set(
    ["虎", "蛇", "猴", "牛", "羊", "狗", "鼠", "兔"] + list(_SELF_PUNISHMENT.keys())
)

# Direction-specific guidance mappings
_DIRECTION_GUIDANCE = {
    "正北": "北方位",
    "东北": "东北方位",
    "正东": "东方位",
    "东南": "东南方位",
    "正南": "南方位",
    "西南": "西南方位",
    "正西": "西方位",
    "西北": "西北方位",
}

_TAI_SUI_RECOMMENDATIONS = {
    "值太岁 + 自刑": "双重伏吟与自寻烦恼。心理压力极大，易固执己见导致失误。建议：深层身心调理、拜太岁、祈福",
    "值太岁": "岁星入命，运势起伏。处于转换期，宜静不宜动。建议：保持谦逊、年度祈福、稳守现状",
    "直冲": "岁运对垒，正面碰撞。易有地域搬迁、职位变动或意外冲击。建议：主动求变（如出差/搬家）、化解口舌",
    "相害": "背后中伤，小人作祟。提防合作不欢而散或亲友反目。建议：谨言慎行、调理人际、法律文书多检查",
    "相破": "无形损耗，关系裂痕。小心财物损坏或计划中断。建议：修补关系、定期体检、防微杜渐",
    "相刑": "纪律约束，文书纷争。易受官非、罚单或职场规则掣肘。建议：遵纪守法、财务透明、克制情绪",
    "无": "岁运平和。无重大冲突，适合按部就班执行计划。",
}

_PILLAR_DOMAINS = {
    "年柱": "祖辈、长辈、外部名声、社交圈、大环境影响力",
    "月柱": "事业发展、职场人际、父母关系、核心财运、自我成就",
    "日柱": "个人身心、配偶关系、家庭内部核心、居家安全",
    "时柱": "子女运势、晚辈/下属、偏财/投资、晚年规划、秘密/隐私",
}


# ============================================================================
# TAI SUI HELPER FUNCTIONS
# ============================================================================


def _check_punishment_clash(
    person_zodiac: str, year_zodiac: str, third_sign: Optional[str] = None
) -> tuple:
    """
    Advanced punishment clash detection.

    Args:
        person_zodiac: Person's zodiac (from pillar or main zodiac)
        year_zodiac: Year's zodiac (Tai Sui)
        third_sign: Optional third sign (e.g., from another pillar)

    Returns:
        tuple: (is_punished: bool, punishment_type: str, severity: int, details: str)
    """

    # Check if both signs are in punishment system
    if (
        person_zodiac not in _ALL_PUNISHMENT_SIGNS
        or year_zodiac not in _ALL_PUNISHMENT_SIGNS
    ):
        return (False, "无", 0, "")

    # Get the set of signs involved
    involved_signs = {person_zodiac, year_zodiac}
    if third_sign:
        involved_signs.add(third_sign)

    # Check each punishment type
    for trio_key, trio_data in _PUNISHMENT_TRIOS.items():
        trio_members = set(trio_data["members"])

        # Check if all involved signs belong to this punishment group
        if involved_signs.issubset(trio_members):
            # Check how many of this trio are present
            present_count = len(involved_signs.intersection(trio_members))

            # Determine if it's a punishment
            if present_count >= 2:
                # It's a punishment!
                severity = present_count  # 2 or 3
                severity_desc = trio_data["severity"].get(severity, "中度影响")

                # Determine specific type
                if present_count == 2:
                    if trio_key == "子卯":
                        punishment_type = "子卯相刑"
                    elif "寅" in involved_signs and "巳" in involved_signs:
                        punishment_type = "寅巳相刑"
                    elif "巳" in involved_signs and "申" in involved_signs:
                        punishment_type = "巳申相刑"
                    elif "寅" in involved_signs and "申" in involved_signs:
                        punishment_type = "寅申相刑"  # This is actually 相冲, not 相刑!
                        # Note: 寅申 is actually 直冲, so this case shouldn't happen
                        return (False, "无", 0, "")
                    elif "丑" in involved_signs and "未" in involved_signs:
                        punishment_type = "丑未相刑"
                    elif "未" in involved_signs and "戌" in involved_signs:
                        punishment_type = "未戌相刑"
                    elif "丑" in involved_signs and "戌" in involved_signs:
                        punishment_type = "丑戌相刑"
                    else:
                        punishment_type = f"{''.join(involved_signs)}相刑"
                else:  # present_count == 3
                    punishment_type = f"{trio_key}三刑"

                details = f"{punishment_type}：{trio_data['meaning']}。{severity_desc}"
                return (True, punishment_type, severity, details)
    return (False, "无", 0, "")


def _get_sui_po_guidance(position: str) -> str:
    """
    Get position-specific guidance for Sui Po (岁破).

    Args:
        position (str): Direction (e.g., "正北", "正东")

    Returns:
        str: Position-specific guidance
    """
    direction_desc = _DIRECTION_GUIDANCE.get(position, position)
    return f"{direction_desc} - 太岁180度对冲，该方位不宜进行重大活动和决策"


def _get_san_sha_guidance(position: str) -> str:
    """
    Get position-specific guidance for San Sha (三煞).

    Args:
        position (str): Direction (e.g., "正北", "正东")

    Returns:
        str: Position-specific guidance
    """
    direction_desc = _DIRECTION_GUIDANCE.get(position, position)
    return f"{direction_desc} - 该方位不宜动土、建筑、开工等重大工程活动"


def _get_sui_po_position(year_zodiac: str) -> str:
    """
    Get Sui Po (Opposite direction of Tai Sui, 180 degrees).

    Args:
        year_zodiac (str): Year's zodiac animal

    Returns:
        str: Direction of Sui Po (e.g., "正南", "正北", etc.)
    """
    return _SUI_PO_OPPOSITES.get(year_zodiac, "未知")


def _get_san_sha_position(year_zodiac: str) -> str:
    """
    Get San Sha (Three Killings) position based on year zodiac element group.

    San Sha indicates the sector that should be avoided for major activities.
    Based on Triple Combination (三合) element groupings.

    Args:
        year_zodiac (str): Year's zodiac animal

    Returns:
        str: Direction of San Sha (e.g., "正北", "正南", etc.)
    """
    return _SAN_SHA_BY_ELEMENT.get(year_zodiac, "未知")


def _check_fan_tai_sui(
    person_zodiac: str, year_zodiac: str, other_pillars: Optional[list] = None
) -> tuple:
    """
    Check if person offends Tai Sui and determine conflict type.

    Checks for: self_clash (值太岁), direct_clash (直冲), harm_clash (相害),
    destruction_clash (相破), punishment_clash (相刑)

    Args:
        person_zodiac (str): Person's zodiac animal
        year_zodiac (str): Year's zodiac animal
        other_pillars (list): List of other zodiacs present in the chart (for complete 三刑)

    Returns:
        tuple: (is_conflicted: bool, conflict_type: str, details: str)
    """
    # 1. Self clash (值太岁) - Highest priority
    if person_zodiac == year_zodiac:
        if person_zodiac in _SELF_PUNISHMENT:
            return (
                True,
                "值太岁 + 自刑",
                f"本命年值太岁，且{person_zodiac}本身带自刑。{_SELF_PUNISHMENT[person_zodiac]}",
            )
        return (True, "值太岁", "本命年值太岁，运势起伏较大")

    # 2. Direct clash (直冲) - Opposite signs
    if _DIRECT_CLASH.get(person_zodiac) == year_zodiac:
        return (True, "直冲", "岁运对垒，正面碰撞，易有重大变动")

    # 3. Harm clash (相害)
    if _HARM_CLASH.get(person_zodiac) == year_zodiac:
        return (True, "相害", "小人作祟，背后中伤，人际关系紧张")

    # 4. Destruction clash (相破)
    if _DESTRUCTION_CLASH.get(person_zodiac) == year_zodiac:
        return (True, "相破", "无形损耗，关系裂痕，易有财物损失")

    # 5. Punishment clash (相刑) - Most complex
    # Check if we have other pillars to determine complete 三刑
    if other_pillars:
        # Look for a third sign that completes a punishment trio
        for third_sign in other_pillars:
            is_punished, p_type, severity, details = _check_punishment_clash(
                person_zodiac, year_zodiac, third_sign
            )
            if is_punished:
                return (True, p_type, details)

    # Check two-way punishment (without third sign)
    is_punished, p_type, severity, details = _check_punishment_clash(
        person_zodiac, year_zodiac
    )
    if is_punished:
        return (True, p_type, details)

    return (False, "无", "岁运平和")


def _check_all_pillars_tai_sui(pillars_dict: dict, year_zodiac: str) -> dict:
    """
    Check Tai Sui conflicts for all 4 pillars with enhanced punishment logic.

    Args:
        pillars_dict (dict): Dictionary with pillar names as keys and zodiac animals as values.
                             Expected keys: "年柱", "月柱", "日柱", "时柱"
        year_zodiac (str): Year's zodiac animal

    Returns:
        dict: Dictionary keyed by pillar name, each containing conflict info and details
    """
    all_pillar_statuses = {}

    # Get all pillar zodiacs for complete punishment checking
    all_zodiacs = list(pillars_dict.values())

    for pillar_name, pillar_zodiac in pillars_dict.items():

        # Create list of other pillars (excluding current one)
        other_pillars = [z for p, z in pillars_dict.items() if p != pillar_name]

        is_conflicted, conflict_type, details = _check_fan_tai_sui(
            pillar_zodiac, year_zodiac, other_pillars
        )

        # Get appropriate recommendation
        if is_conflicted:
            if "三刑" in conflict_type:
                advice = "三刑齐全，刑伤最重。需特别注意官非、健康、人际关系。建议全面化解，可考虑专业风水调理。"
            elif "相刑" in conflict_type:
                advice = "相刑之年，易有口舌是非、纪律约束。建议遵纪守法、克制情绪。"
            else:
                advice = _TAI_SUI_RECOMMENDATIONS.get(conflict_type, "")
        else:
            advice = _TAI_SUI_RECOMMENDATIONS["无"]

        all_pillar_statuses[pillar_name] = {
            "生肖": pillar_zodiac,
            "是否冲犯": is_conflicted,
            "冲克类型": conflict_type if is_conflicted else "无",
            "详细解读": details if is_conflicted else "无特殊冲犯",
            "影响领域": _PILLAR_DOMAINS.get(pillar_name, "综合领域"),
            "建议": advice,
        }

    return all_pillar_statuses


def get_comprehensive_tai_sui_analysis(
    year_zodiac: str,
    person_zodiac: str,
    bazi: EightChar,
    lunar_date: Lunar,
) -> dict:
    """
    Get comprehensive Tai Sui analysis including:
    - House afflictions (Tai Sui position, Sui Po, San Sha)
    - Personal clashes (check all 4 pillars against year zodiac)

    Args:
        year_zodiac (str): Year's zodiac animal
        person_zodiac (str): Person's birth zodiac animal
        bazi (EightChar): Birth chart (Eight Character) object
        lunar_date (Lunar): Lunar date object for the year (used to get Tai Sui position from library)

    Returns:
        dict: Comprehensive analysis with house afflictions and personal clashes
    """
    # House-level afflictions (fixed positions)
    # Use the passed lunar_date to get accurate Tai Sui position from library
    tai_sui_pos = lunar_date.getYearPositionTaiSuiDesc()
    sui_po_pos = _get_sui_po_position(year_zodiac)
    san_sha_pos = _get_san_sha_position(year_zodiac)

    house_afflictions = {
        "太岁位置": {
            "方位": tai_sui_pos,
            "含义": "流年主亮点，该方位宜布局生旺之事",
        },
        "岁破位置": {
            "方位": sui_po_pos,
            "含义": _get_sui_po_guidance(sui_po_pos),
        },
        "三煞位置": {
            "方位": san_sha_pos,
            "含义": _get_san_sha_guidance(san_sha_pos),
        },
    }

    # Personal pillar conflicts (convert branches to zodiac animals)
    pillars_dict = {
        "年柱": _BRANCH_TO_ZODIAC.get(bazi.getYearZhi(), "未知"),
        "月柱": _BRANCH_TO_ZODIAC.get(bazi.getMonthZhi(), "未知"),
        "日柱": _BRANCH_TO_ZODIAC.get(bazi.getDayZhi(), "未知"),
        "时柱": _BRANCH_TO_ZODIAC.get(bazi.getTimeZhi(), "未知"),
    }

    personal_clashes = _check_all_pillars_tai_sui(pillars_dict, year_zodiac)

    return {
        "流年": year_zodiac,
        "命主生肖": person_zodiac,
        "宫位冲犯": house_afflictions,
        "柱位冲犯": personal_clashes,
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_current_date_range_liu_nian(reference_date: datetime = None) -> tuple:
    """
    Calculate date range for Liu Nian: 5 years past + 5 years future from reference date.

    Args:
        reference_date (datetime): Reference date (default: today)

    Returns:
        tuple: (start_year, num_years) where num_years = 10 (5 past + 5 future)
    """
    if reference_date is None:
        reference_date = datetime.now()

    current_year = reference_date.year
    start_year = current_year - 5  # 5 years in the past
    num_years = 10  # 5 past + 5 future (current year is year 5)

    return (start_year, num_years)


def _filter_liu_yue_by_date_range(
    liu_yue_array: list, reference_date: datetime = None
) -> list:
    """
    Filter Liu Yue to include past 12 months + next 24 months from reference date.

    Args:
        liu_yue_array (list): Array of Liu Yue cycle data dicts
        reference_date (datetime): Reference date (default: today)

    Returns:
        list: Filtered Liu Yue array
    """
    if reference_date is None:
        reference_date = datetime.now()

    # Calculate date boundaries
    past_12_months = reference_date - timedelta(days=365)
    next_24_months = reference_date + timedelta(days=730)

    # Filter cycles (this is a simple filter; if actual month dates are needed,
    # they would need to be extracted from liu_yue_obj)
    # For now, we'll include all cycles and let the caller handle date filtering
    # if they have actual liu_yue dates available
    return liu_yue_array


def _get_xun_and_xun_kong_from_object(liu_yun_obj) -> tuple:
    """
    Get Xun (旬) and Xun Kong (旬空) from a Liu Yun object.

    Args:
        liu_yun_obj: Liu Yun object (Liu Nian or Liu Yue) from lunar-python library

    Returns:
        tuple: (xun_name: str, xun_kong_pair: str)
    """
    try:
        xun = liu_yun_obj.getXun() if hasattr(liu_yun_obj, "getXun") else "Unknown"
        xun_kong = (
            liu_yun_obj.getXunKong()
            if hasattr(liu_yun_obj, "getXunKong")
            else "Unknown"
        )
        return (xun, xun_kong)
    except Exception:
        return ("Unknown", "Unknown")


def _detect_liu_nian_interactions(
    liu_nian_stem: str, liu_nian_branch: str, birth_chart: dict
) -> dict:
    """
    Detect Liu Nian interactions with birth chart using same 1x4 scan as Da Yun.

    The Liu Nian pillar acts as an External Trigger entering the birth chart system.
    Uses the same Tier-based priority checks and Key vs Lock logic.

    Args:
        liu_nian_stem (str): Liu Nian heavenly stem (year stem)
        liu_nian_branch (str): Liu Nian earthly branch (year branch)
        birth_chart (dict): Birth chart with keys "year", "month", "day", "hour"

    Returns:
        dict: Organized interactions by pillar and tier
    """
    # Leverage the existing Da Yun interaction detection function
    # Pass "流年" as pillar_prefix to replace "大运" in the output
    return _detect_da_yun_interactions(
        liu_nian_stem, liu_nian_branch, birth_chart, pillar_prefix="流年"
    )


def _detect_liu_yue_interactions(
    liu_yue_stem: str, liu_yue_branch: str, birth_chart: dict
) -> dict:
    """
    Detect Liu Yue interactions with birth chart using same 1x4 scan as Da Yun.

    The Liu Yue pillar acts as an External Trigger entering the birth chart system.
    Uses the same Tier-based priority checks and Key vs Lock logic.

    Args:
        liu_yue_stem (str): Liu Yue heavenly stem (month stem)
        liu_yue_branch (str): Liu Yue earthly branch (month branch)
        birth_chart (dict): Birth chart with keys "year", "month", "day", "hour"

    Returns:
        dict: Organized interactions by pillar and tier
    """
    # Leverage the existing Da Yun interaction detection function
    # Pass "流月" as pillar_prefix to replace "大运" in the output
    return _detect_da_yun_interactions(
        liu_yue_stem, liu_yue_branch, birth_chart, pillar_prefix="流月"
    )


def _get_jieqi_info_for_lunar_month(year: int, month: int, day: int = 15) -> dict:
    """
    Get solar term (节气) information for a given lunar month.

    Args:
        year (int): Lunar year
        month (int): Lunar month (1-12)
        day (int): Day within the month (default 15 for middle of month)

    Returns:
        dict: Solar term information including name, start date, and end date
    """
    try:
        # Create a lunar date in the middle of the month to find which solar term period it's in
        lunar_date = Lunar.fromYmdHms(year, month, day, 12, 0, 0)

        # Get the solar term boundaries for this month
        curr_jie = (
            lunar_date.getPrevJie()
        )  # Current/governing solar term (start of current lunar month)
        next_jie = (
            lunar_date.getNextJie()
        )  # Next solar term (start of next lunar month)

        if not curr_jie or not next_jie:
            return {"节气": "未知", "公历起点": "未知", "公历终点": "未知"}

        # Convert to Solar calendar for precise dates
        curr_jie_solar = curr_jie.getSolar()
        next_jie_solar = next_jie.getSolar()

        curr_jie_solar_date = curr_jie_solar.toYmdHms()
        next_jie_solar_date = next_jie_solar.toYmdHms()

        return {
            "节气": curr_jie.getName(),
            "公历起点": curr_jie_solar_date,
            "公历终点": next_jie_solar_date,
            "下个节气": next_jie.getName(),
        }
    except Exception as e:
        return {
            "节气": "获取失败",
            "公历起点": "未知",
            "公历终点": "未知",
            "错误": str(e),
        }


def _get_month_strength(branch: str, birth_chart: dict) -> str:
    """
    Get the strength/status of a month branch relative to the birth chart.

    Evaluates how strong or influential the month branch is based on its
    relationship to the birth chart pillars (particularly the day stem and branches).

    Args:
        branch (str): Earthly branch of the month (e.g., "寅", "卯", etc.)
        birth_chart (dict): Birth chart with pillars

    Returns:
        str: Strength assessment (e.g., "旺月", "中神", "衰月", etc.)
    """
    if not branch or not birth_chart or "day" not in birth_chart:
        return "中等"

    day_stem = birth_chart["day"].get("stem", "")
    day_branch = birth_chart["day"].get("branch", "")

    # Simple evaluation: check if month branch is in harmony with day pillars
    # This can be expanded with more sophisticated logic later
    if branch == day_branch:
        return "旺月"
    elif day_stem in ["甲", "乙"] and branch in ["寅", "卯"]:
        return "旺月"
    elif day_stem in ["丙", "丁"] and branch in ["巳", "午"]:
        return "旺月"
    elif day_stem in ["戊", "己"] and branch in ["辰", "戌", "丑", "未"]:
        return "旺月"
    elif day_stem in ["庚", "辛"] and branch in ["申", "酉"]:
        return "旺月"
    elif day_stem in ["壬", "癸"] and branch in ["亥", "子"]:
        return "旺月"
    else:
        return "中等"


# ============================================================================
# MAIN LIU NIAN CALCULATION
# ============================================================================


def get_liu_nian(
    lunar_birthday: Lunar,
    gender: int,
    start_year: int = None,
    num_years: int = None,
    reference_date: datetime = None,
) -> dict:
    """
    Calculate Annual Luck Cycles (Liu Nian) from lunar birthday and gender.

    If start_year and num_years are both None, uses reference_date to calculate
    a 10-year range (5 years past + 5 years future).

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male
        start_year (int): Optional calendar year to start from. If None, auto-calculated.
        num_years (int): Number of years to calculate. If None, auto-calculated.
        reference_date (datetime): Reference date for auto-calculation (default: today)

    Returns:
        dict: Structured JSON with Liu Nian cycles and timing information
    """
    # Auto-calculate date range if not provided
    if start_year is None and num_years is None:
        start_year, num_years = _get_current_date_range_liu_nian(reference_date)
    elif reference_date is not None:
        # If start_year is provided but num_years is not, still respect start_year
        if num_years is None:
            num_years = 10
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
    qi_yun_date = yun.getStartSolar()
    qi_yun_start_year = yun.getStartYear()

    # Determine starting year for Liu Nian calculation
    if start_year is None:
        start_year = qi_yun_start_year

    # Get all Liu Nian cycles starting from the specified year
    # We need to use the Da Yun object to access Liu Nian
    da_yun_array = yun.getDaYun()

    # Collect Liu Nian data from all Da Yun cycles
    liu_nian_data = []
    total_liu_nian_count = 0

    for da_yun_obj in da_yun_array:
        liu_nian_array = da_yun_obj.getLiuNian()

        if not liu_nian_array:
            continue

        for i, liu_nian_obj in enumerate(liu_nian_array):
            gan_zhi = liu_nian_obj.getGanZhi()
            lunar_calendar_year = liu_nian_obj.getYear()
            age = liu_nian_obj.getAge()

            if gan_zhi == "Unknown" or len(gan_zhi) < 2:
                continue

            # Skip years before our start_year or after our range
            if lunar_calendar_year < start_year or total_liu_nian_count >= num_years:
                if lunar_calendar_year < start_year:
                    continue
                else:
                    break

            liu_nian_stem = gan_zhi[0]
            liu_nian_branch = gan_zhi[1]

            # Calculate Ten Gods for this 流年
            stem_shi_shen = _get_shi_shen_for_stem_pair(day_stem, liu_nian_stem)
            branch_shi_shen = _get_hidden_stems_shi_shen(day_stem, liu_nian_branch)

            # Life Stage (地势) for the Liu Nian branch using birth day stem as reference
            di_shi = _get_di_shi(day_stem, liu_nian_branch)

            # Five Elements (五行) for Stem and Branch
            stem_wu_xing = _get_stem_wu_xing(liu_nian_stem)
            branch_wu_xing = _get_branch_wu_xing(liu_nian_branch)

            # Nayin (纳音) for the Liu Nian stem-branch pair
            nayin = _get_nayin(liu_nian_stem, liu_nian_branch)

            # Get Xun (旬) and Xun Kong (旬空)
            xun, xun_kong = _get_xun_and_xun_kong_from_object(liu_nian_obj)

            # Detect interactions (作用) with birth chart
            interactions_result = _detect_liu_nian_interactions(
                liu_nian_stem, liu_nian_branch, birth_chart
            )
            interactions = interactions_result.get("作用", [])

            # Get person's birth zodiac and year zodiac for Tai Sui comparison
            person_zodiac = lunar_birthday.getYearShengXiao()
            # Extract year zodiac directly from the branch (most reliable source)
            year_zodiac = _BRANCH_TO_ZODIAC.get(liu_nian_branch, "未知")

            # Random date in the middle of the Liu Nian year to get accurate Tai Sui position from library
            lunar_date_random = Lunar.fromYmdHms(lunar_calendar_year, 6, 15, 12, 0, 0)

            # Get comprehensive Tai Sui analysis (house + pillar + personal layers)
            tai_sui_info = get_comprehensive_tai_sui_analysis(
                year_zodiac, person_zodiac, bazi, lunar_date_random
            )

            # Get Nine Star Energy (九星能量与风水) for this Liu Nian
            year_star = lunar_date_random.getYearNineStar()
            nine_star_energy_info = get_nine_star(year_star)

            # Auspicious positions and guidance
            cai_xi_fu_gui_info = _get_cai_xi_fu_gui_analysis(liu_nian_stem)

            liu_nian_info = {
                # "序号": total_liu_nian_count + 1,  # 1-based sequence number
                "年龄": age,  # Age at start of year (from library)
                "日历年份": lunar_calendar_year,  # Lunar calendar year
                "当前大运": da_yun_obj.getGanZhi(),  # Current Da Yun stem-branch
                "传统节日": lunar_date_random.getFestivals(),
                "其他节日": lunar_date_random.getOtherFestivals(),
                # Intrinsic Properties - What this cycle IS (cycle's own nature)
                "命理属性": {
                    "年生肖": year_zodiac,  # Zodiac animal for the year. Use a temp date in the middle of the year to get the correct zodiac.
                    "干支": gan_zhi,  # Gan-Zhi (stem-branch pair)
                    "五行": {
                        "干": stem_wu_xing,  # Stem Five Element and Polarity
                        "支": branch_wu_xing,  # Branch Five Element and Polarity
                    },
                    "纳音": nayin,  # Nayin element (harmonic resonance)
                    "旬": xun,  # Xun (10-day cycle)
                    "旬空": xun_kong,  # Xun Kong (void periods)
                },
                # Relational Properties - How it affects the person (measured vs Day Stem)
                "核心分析": {
                    # Tai Sui conflict and recommendations
                    "太岁分析": tai_sui_info,
                    # Ten Gods
                    "十神": {
                        "天干十神": stem_shi_shen,  # Year Stem Ten God (for clarity)
                        "地支十神": branch_shi_shen,  # Hidden themes (Main/Middle/Residual)
                    },
                    # Life Stage (地势)
                    "地势": di_shi,  # Life Stage (长生十二神)
                    # Nine Star Energy (九星能量与风水)
                    "九星能量与风水": nine_star_energy_info,
                    # Wealth, Joy, Blessing, Noble support positions based on the Liu Nian stem
                    "方位分析": cai_xi_fu_gui_info,
                    "作用": interactions,  # Branch and Stem interactions with birth chart
                },
            }
            liu_nian_data.append(liu_nian_info)
            total_liu_nian_count += 1

        # Stop if we've collected enough years
        if total_liu_nian_count >= num_years:
            break

    # Compile the complete liu_nian structure
    return {
        "流年": {
            "元信息": {
                "出生阳历": lunar_birthday.getSolar().toYmdHms(),
                "出生农历": f"{lunar_birthday.getYear()}-{lunar_birthday.getMonth()}-{lunar_birthday.getDay()}",
                "起运时间": qi_yun_date.toYmdHms(),
                "起运年份": qi_yun_start_year,
                "生肖": lunar_birthday.getYearShengXiao(),  # Zodiac from Year Pillar, not Time Pillar
                "命主日元": day_stem,  # Birth Day Stem
                "开始年份": start_year,
                "计算年数": num_years,
                "流年周期数": len(liu_nian_data),
            },
            "流年周期": liu_nian_data,
        }
    }


# ============================================================================
# MAIN LIU YUE CALCULATION
# ============================================================================


def get_liu_yue(
    lunar_birthday: Lunar,
    gender: int,
    year_index: int = None,
    reference_date: datetime = None,
) -> dict:
    """
    Calculate Monthly Luck Cycles (Liu Yue) for a specific annual period.

    When used within get_liu_nian_ye(), months are automatically filtered to include
    only those within the past 12 months + next 24 months range from reference_date.

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male
        year_index (int): Which year within the Liu Nian cycles to get monthly for (0-based)
        reference_date (datetime): Reference date for month range filtering (default: today)

    Returns:
        dict: Structured JSON with Liu Yue cycles for the specified range
    """
    if reference_date is None:
        reference_date = datetime.now()
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

    # Get all Da Yun cycles and find the Liu Nian at year_index
    da_yun_array = yun.getDaYun()

    # Use year_index=0 as default if not provided
    if year_index is None:
        year_index = 0

    # Flatten all Liu Nian and find the one at year_index
    total_liu_nian_count = 0
    target_liu_nian_obj = None
    target_calendar_year = None
    target_age = None
    target_da_yun_obj = None

    for da_yun_obj in da_yun_array:
        liu_nian_array = da_yun_obj.getLiuNian()

        if not liu_nian_array:
            continue

        for liu_nian_obj in liu_nian_array:
            if total_liu_nian_count == year_index:
                target_liu_nian_obj = liu_nian_obj
                target_calendar_year = liu_nian_obj.getYear()
                target_age = liu_nian_obj.getAge()
                target_da_yun_obj = da_yun_obj
                break

            total_liu_nian_count += 1

        if target_liu_nian_obj:
            break

    # Get Liu Yue array for this Liu Nian
    liu_yue_array = target_liu_nian_obj.getLiuYue() if target_liu_nian_obj else []

    # Calculate date boundaries for month filtering (past 12 months + next 24 months)
    past_12_months = reference_date - timedelta(days=365)
    next_24_months = reference_date + timedelta(days=730)

    # Process each 流月 (month) within this year
    liu_yue_data = []

    for i, liu_yue_obj in enumerate(liu_yue_array):
        gan_zhi = liu_yue_obj.getGanZhi()

        if gan_zhi == "Unknown" or len(gan_zhi) < 2:
            continue

        # Try to get the month number from the Liu Yue object
        # The month is typically the index i (0-11 for Jan-Dec)
        month_num = i + 1  # 1-based month number

        # Create a date representation for filtering
        # Use the target year and the month number
        try:
            month_date = datetime(target_calendar_year, month_num, 1)
        except ValueError:
            # If month_num is invalid, skip this entry
            continue

        # Filter: only include months within past 12 months + next 24 months
        if month_date < past_12_months or month_date > next_24_months:
            continue

        liu_yue_stem = gan_zhi[0]
        liu_yue_branch = gan_zhi[1]

        # Calculate Ten Gods for this 流月
        stem_shi_shen = _get_shi_shen_for_stem_pair(day_stem, liu_yue_stem)
        branch_shi_shen = _get_hidden_stems_shi_shen(day_stem, liu_yue_branch)

        # Life Stage (地势) for the Liu Yue branch using birth day stem as reference
        di_shi = _get_di_shi(day_stem, liu_yue_branch)

        # Five Elements (五行) for Stem and Branch
        stem_wu_xing = _get_stem_wu_xing(liu_yue_stem)
        branch_wu_xing = _get_branch_wu_xing(liu_yue_branch)

        # Nayin (纳音) for the Liu Yue stem-branch pair
        nayin = _get_nayin(liu_yue_stem, liu_yue_branch)

        # Get Xun (旬) and Xun Kong (旬空)
        xun, xun_kong = _get_xun_and_xun_kong_from_object(liu_yue_obj)

        # Detect interactions (作用) with birth chart
        interactions_result = _detect_liu_yue_interactions(
            liu_yue_stem, liu_yue_branch, birth_chart
        )
        interactions = interactions_result.get("作用", [])

        # Auspicious positions and guidance for this month
        cai_xi_fu_gui_info = _get_cai_xi_fu_gui_analysis(liu_yue_stem)

        # Get Nine Star Energy (九星能量与风水) for this Liu Yue
        lunar_date_month = Lunar.fromYmdHms(
            target_calendar_year, month_num, 15, 12, 0, 0
        )
        month_nine_star = lunar_date_month.getMonthNineStar()
        nine_star_energy = {
            "月九星": (get_nine_star(month_nine_star) if month_nine_star else {}),
        }

        # Seasonal Divisions & Energy Cycles (季节能量周期)
        fu = lunar_date_month.getFu()
        shujiu = lunar_date_month.getShuJiu()
        seasonal_cycles = {
            "三伏": fu if fu else "非三伏天",
            "数九": shujiu if shujiu else "非数九天",
        }

        # Get month info
        month_name = (
            liu_yue_obj.getMonthInChinese()
            if hasattr(liu_yue_obj, "getMonthInChinese")
            else f"第{i+1}个月"
        )

        # Get jieqi information for this lunar month
        jieqi_info = _get_jieqi_info_for_lunar_month(target_calendar_year, month_num)

        liu_yue_info = {
            "月份索引": month_name,  # Month name in Chinese
            "节气": jieqi_info.get("节气", "未知"),  # Solar term name (e.g., "清明")
            "公历起点": jieqi_info.get(
                "公历起点", "未知"
            ),  # Gregorian start date of solar term
            "公历终点": jieqi_info.get(
                "公历终点", "未知"
            ),  # Gregorian end date (next solar term)
            "日历区间": f"{jieqi_info.get('公历起点', '未知')} 至 {jieqi_info.get('公历终点', '未知')}",  # Date range
            "农历范围": f"{target_calendar_year}年农历{month_num}月",  # Lunar date range
            "月相": lunar_date_month.getYueXiang(),
            "季节": lunar_date_month.getSeason(),
            "时令": seasonal_cycles,
            # Intrinsic Properties - What this cycle IS (cycle's own nature)
            "命理属性": {
                "月生肖": _BRANCH_TO_ZODIAC.get(
                    liu_yue_branch, "未知"
                ),  # Zodiac animal for the month
                "干支": gan_zhi,  # Gan-Zhi (stem-branch pair)
                "五行": {
                    "干": stem_wu_xing,  # Stem Five Element and Polarity
                    "支": branch_wu_xing,  # Branch Five Element and Polarity
                },
                "纳音": nayin,  # Nayin element (harmonic resonance)
                "旬": xun,  # Xun (10-day cycle)
                "旬空": xun_kong,  # Xun Kong (void periods)
            },
            # Relational Properties - How it affects the person (measured vs Day Stem)
            "核心分析": {
                "月令强度": _get_month_strength(
                    liu_yue_branch, birth_chart
                ),  # Strength of the month branch in the birth chart
                "十神": {
                    "天干十神": stem_shi_shen,  # Year Stem Ten God (for clarity)
                    "地支十神": branch_shi_shen,  # Hidden themes (Main/Middle/Residual)
                },
                "地势": di_shi,  # Life Stage (长生十二神)
                "九星能量与风水": nine_star_energy,  # Nine Star Energy for this month
                "方位分析": cai_xi_fu_gui_info,  # Auspicious positions and guidance for this month
                "作用": interactions,  # Branch and Stem interactions with birth chart
            },
        }
        liu_yue_data.append(liu_yue_info)

    # Compile the complete liu_yue structure
    return {
        "流月": {
            "元信息": {
                "流年": f"{target_calendar_year}年" if target_calendar_year else "未知",
                "年龄": f"{target_age}岁" if target_age else "未知",
                "命主日元": day_stem if day_stem else "未知",
                "流月周期数": len(liu_yue_data),
                "年干支": (
                    target_liu_nian_obj.getGanZhi() if target_liu_nian_obj else "未知"
                ),
                "当前大运": (
                    target_da_yun_obj.getGanZhi() if target_da_yun_obj else "未知"
                ),
            },
            "流月周期": liu_yue_data,
        }
    }


# ============================================================================
# COMBINED LIU NIAN & LIU YUE
# ============================================================================


def get_liu_nian_ye(
    lunar_birthday: Lunar,
    gender: int,
    start_year: int = None,
    num_years: int = None,
    reference_date: datetime = None,
) -> dict:
    """
    Calculate complete Liu Nian (Annual Luck) and Liu Yue (Monthly Luck) combined analysis.

    If start_year and num_years are both None, uses reference_date to calculate
    a 10-year range (5 years past + 5 years future).
    For each Liu Nian year, includes its Liu Yue (monthly cycles).

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male
        start_year (int): Optional calendar year to start from
        num_years (int): Number of years to calculate
        reference_date (datetime): Reference date for auto-calculation (default: today)

    Returns:
        dict: Structured JSON with Liu Nian cycles, each containing Liu Yue data
    """
    if reference_date is None:
        reference_date = datetime.now()

    # First get Liu Nian data with date awareness
    liu_nian_result = get_liu_nian(
        lunar_birthday, gender, start_year, num_years, reference_date
    )

    # Now add Liu Yue data for each Liu Nian
    liu_nian_cycles = liu_nian_result["流年"]["流年周期"]

    for idx, liu_nian_cycle in enumerate(liu_nian_cycles):
        # Get Liu Yue data for this year
        liu_yue_result = get_liu_yue(lunar_birthday, gender, idx, reference_date)
        liu_nian_cycle["流月周期"] = liu_yue_result["流月"]["流月周期"]

    return liu_nian_result


# ============================================================================
# CONVENIENCE FUNCTIONS - DATE-FOCUSED ANALYSIS
# ============================================================================


def get_liu_nian_current_focus(lunar_birthday: Lunar, gender: int) -> dict:
    """
    Get Liu Nian focused on current date: 5 years past + 5 years future.

    Convenience wrapper around get_liu_nian() with automatic date range calculation.

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male

    Returns:
        dict: Liu Nian cycles for the current date-focused range
    """
    return get_liu_nian(lunar_birthday, gender, reference_date=datetime.now())


def get_liu_yue_current_focus(
    lunar_birthday: Lunar, gender: int, year_index: int = 0
) -> dict:
    """
    Get Liu Yue for a specific year with current date context.

    Convenience wrapper around get_liu_yue() with automatic date reference.

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male
        year_index (int): Which year to analyze (0-based)

    Returns:
        dict: Liu Yue cycles for that year
    """
    return get_liu_yue(
        lunar_birthday, gender, year_index, reference_date=datetime.now()
    )


def get_liu_nian_ye_current_focus(lunar_birthday: Lunar, gender: int) -> dict:
    """
    Get complete Liu Nian & Liu Yue analysis focused on current date.

    Convenience wrapper for comprehensive analysis with automatic date range.
    - Liu Nian: 5 years past + 5 years future from today
    - Liu Yue: All months for those years

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male

    Returns:
        dict: Combined Liu Nian + Liu Yue cycles with current date focus
    """
    return get_liu_nian_ye(lunar_birthday, gender, reference_date=datetime.now())


# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    import json
    import sys
    import logging
    from io import StringIO
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
    from src.astronomer_calculations.bazi_pillars import get_bazi_pillars
    from src.utils.logging import configure_logging, get_logger

    # python -m src.astronomer_calculations.liu_nian_ye

    # Set encoding to UTF-8 for proper Chinese character output
    if sys.stdout.encoding != "utf-8":
        sys.stdout = StringIO() if sys.platform == "win32" else sys.stdout

    # Configure logging with timestamped directory
    logger = configure_logging(log_level=logging.INFO, logs_base_dir="logs")

    # Get current datetime
    now = datetime.now()
    logger.info(f"当前日期时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    # Desmond's birthday example
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)

    # Example: Lara's birthday
    # solar_birthday = Solar.fromYmdHms(2025, 7, 31, 9, 10, 0)
    # tst_birthday, inputs_report = get_true_solar_time(
    #     datetime(2025, 7, 31, 9, 10, 0), 1.4759, 103.808053
    # )
    lunar_birthday = tst_birthday.getLunar()

    logger.info("八字")
    bazi_json = get_bazi_pillars(lunar_birthday)
    logger.info(f"八字: {json.dumps(bazi_json, ensure_ascii=False)}")

    logger.info(f"流年 5年过去 + 5年未来 (今日: {now.year}-{now.month}-{now.day})")
    result = get_liu_nian(lunar_birthday, gender=0, reference_date=now)
    logger.info(f"流年分析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

    # print(f"\n=== 流月 第1个年份 (女, Gender=0) ===", file=sys.stderr)
    # result = get_liu_yue(lunar_birthday, gender=0, year_index=0, reference_date=now)
    # print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)

    # print(
    #     f"\n=== 流年 & 流月 组合分析 (女, Gender=0) - 自动日期范围 ===", file=sys.stderr
    # )
    # result = get_liu_nian_ye(lunar_birthday, gender=0, reference_date=now)
    # print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
