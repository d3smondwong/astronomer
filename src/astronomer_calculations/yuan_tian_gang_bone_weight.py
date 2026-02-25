# This module defines the bone weights for the Yuan Tian Gang system based on the lunar birthday.

# Mapping of Earthly Branches (地支) to Western hour names
# The 12 earthly branches (地支) are: 子, 丑, 寅, 卯, 辰, 巳, 午, 未, 申, 酉, 戌, 亥
# These map to: Zi, Chou, Yin, Mao, Chen, Si, Wu, Wei, Shen, You, Xu, Hai
ZHI_TO_HOUR_NAME = {
        "子": "Zi", "丑": "Chou", "寅": "Yin", "卯": "Mao",
        "辰": "Chen", "巳": "Si", "午": "Wu", "未": "Wei",
        "申": "Shen", "酉": "You", "戌": "Xu", "亥": "Hai"
    }

# Bone weights for years, months, days, and hours based on the Yuan Tian Gang system
YUAN_TIAN_GANG_BONE_WEIGHTS = {
    "years": {
        0: 1.2, 1: 0.9, 2: 0.6, 3: 0.7, 4: 1.2, 5: 0.4, 6: 0.9, 7: 0.8, 8: 0.7, 9: 0.8,
        10: 1.5, 11: 0.9, 12: 1.6, 13: 0.8, 14: 0.8, 15: 1.9, 16: 1.2, 17: 0.6, 18: 0.8, 19: 0.7,
        20: 0.5, 21: 1.5, 22: 0.6, 23: 1.6, 24: 0.7, 25: 0.8, 26: 0.9, 27: 0.7, 28: 1.0, 29: 0.7,
        30: 1.5, 31: 0.6, 32: 0.5, 33: 1.4, 34: 1.4, 35: 0.9, 36: 0.7, 37: 0.7, 38: 0.9, 39: 1.2,
        40: 0.8, 41: 0.7, 42: 1.3, 43: 0.5, 44: 1.4, 45: 0.5, 46: 1.9, 47: 1.7, 48: 0.5, 49: 0.7,
        50: 1.2, 51: 0.8, 52: 0.8, 53: 0.6, 54: 1.9, 55: 0.6, 56: 0.8, 57: 0.5, 58: 1.0, 59: 0.7
    },
    "months": {
        1: 0.6, 2: 0.7, 3: 1.8, 4: 0.9, 5: 0.5, 6: 1.6,
        7: 0.9, 8: 1.5, 9: 1.5, 10: 0.8, 11: 0.9, 12: 0.5
    },
    "days": {
        1: 0.5, 2: 1.0, 3: 0.8, 4: 1.5, 5: 1.6, 6: 1.5, 7: 0.8, 8: 1.6, 9: 0.8, 10: 1.6,
        11: 0.9, 12: 1.7, 13: 0.8, 14: 1.7, 15: 1.0, 16: 0.8, 17: 0.9, 18: 1.8, 19: 0.5, 20: 1.5,
        21: 1.0, 22: 0.9, 23: 0.8, 24: 0.9, 25: 1.5, 26: 1.8, 27: 0.7, 28: 0.8, 29: 1.6, 30: 0.6
    },
    "hours": {
        "Zi": 1.6, "Chou": 0.6, "Yin": 0.7, "Mao": 1.0, "Chen": 0.9, "Si": 1.6,
        "Wu": 1.0, "Wei": 0.8, "Shen": 0.8, "You": 0.9, "Xu": 0.6, "Hai": 0.6
    }
}

def calculate_yuan_tian_gang_bone_weight(lunar_birthday):
    """
    Calculate the Yuan Tian Gang bone weight based on lunar birthday.

    Args:
        lunar_birthday: A Lunar object with lunar date information
        bone_weights: Dictionary with 'years', 'months', 'days', 'hours' keys containing weight mappings

    Returns:
        A dictionary with breakdown and total bone weight
    """

    # 1. Extract Year and map to 0-59 range (60-year sexagenary cycle)
    # Starting reference: 1984 = Index 0 (Jiazi 甲子 - Rat Year)
    year = lunar_birthday.getYear()
    year_index = (year - 1924) % 60
    if year_index not in YUAN_TIAN_GANG_BONE_WEIGHTS["years"]:
        raise ValueError(f"Year index {year_index} (year {year}) not found in YUAN_TIAN_GANG_BONE_WEIGHTS['years']")
    year_weight = YUAN_TIAN_GANG_BONE_WEIGHTS["years"][year_index]

    # 2. Extract Month (1-12)
    month = lunar_birthday.getMonth()
    if month not in YUAN_TIAN_GANG_BONE_WEIGHTS["months"]:
        raise ValueError(f"Month {month} not found in bone_weights['months']")
    month_weight = YUAN_TIAN_GANG_BONE_WEIGHTS["months"][month]

    # 3. Extract Day (1-30)
    day = lunar_birthday.getDay()
    if day not in YUAN_TIAN_GANG_BONE_WEIGHTS["days"]:
        raise ValueError(f"Day {day} not found in YUAN_TIAN_GANG_BONE_WEIGHTS['days']")
    day_weight = YUAN_TIAN_GANG_BONE_WEIGHTS["days"][day]

    # 4. Extract Hour and convert to Western name
    # Get the earthly branch (Zhi) of the hour from the BaZi eight character
    hour_zhi = lunar_birthday.getEightChar().getTimeZhi()
    if hour_zhi not in ZHI_TO_HOUR_NAME:
        raise ValueError(f"Hour earthly branch '{hour_zhi}' not recognized")
    hour_name = ZHI_TO_HOUR_NAME[hour_zhi]
    if hour_name not in YUAN_TIAN_GANG_BONE_WEIGHTS["hours"]:
        raise ValueError(f"Hour '{hour_name}' not found in bone_weights['hours']")
    hour_weight = YUAN_TIAN_GANG_BONE_WEIGHTS["hours"][hour_name]

    # 5. Calculate total bone weight
    total_weight = year_weight + month_weight + day_weight + hour_weight

    return {
        "lunar_date": lunar_birthday.toString(),
        "year": year,
        "year_index": year_index,
        "year_weight": year_weight,
        "month": month,
        "month_weight": month_weight,
        "day": day,
        "day_weight": day_weight,
        "hour": hour_zhi + "时",
        "hour_name": hour_name,
        "hour_weight": hour_weight,
        "total_weight": round(total_weight, 1),
        "breakdown": f"{year_weight} + {month_weight} + {day_weight} + {hour_weight} = {round(total_weight, 1)}"
    }