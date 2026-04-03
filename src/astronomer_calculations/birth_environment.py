"""
Birth Environment (出生环境) Calculation Module

This module extracts comprehensive birth environment information including
geographical luck, auspicious/inauspicious times, and environmental factors.

Core Concepts:
    - 二十八星宿 (Twenty-Eight Constellations): Celestial markers correlating with
      earthly locations, directions, and fates
    - 方位 (Directional Positions): Geographic locations for luck activities
    - 彭祖百忌 (Peng Zu Taboos): Traditional prohibitions by Gan and Zhi
    - 冲煞 (Clashes & Harmfulness): Conflicting energies to avoid
    - 宜忌 (Auspicious & Inauspicious): Actions to pursue or avoid
    - 天神 (Heavenly Deities): Divine forces governing specific times

The Birth Environment encompasses:
    1. **Constellation & Spiritual Background**
       - 星宿 (Constellation): Twenty-eight stars mapping to fate
       - 星宿诗诀 (Constellation Poem): Traditional wisdom verse
       - 方位/宫曜 (Direction/Palace): Geographic location of luck

    2. **Geographic Luck Directions**
       - 财神方位 (Wealth Direction): Best direction for wealth activities
       - 喜神方位 (Joy Direction): Direction of happiness
       - 福神方位 (Fortune Direction): Direction of blessings
       - 阳贵/阴贵 (Noble Directions): High-luck directions

    3. **Heavenly Deities**
       - 日值天神 (Day Deity): Guardian deity of the day
       - 时值天神 (Hour Deity): Guardian deity of the hour

    4. **Auspicious & Inauspicious Actions**
       - 日宜 (Day Auspicious): Good actions for the day
       - 日忌 (Day Inauspicious): Actions to avoid
       - 日吉神宜趋 (Day Auspicious Deities): Gods to approach
       - 日凶煞宜忌 (Day Inauspicious Sha): Evil forces to avoid
       - 时宜 (Hour Auspicious): Good actions for the hour
       - 时忌 (Hour Inauspicious): Actions to avoid for the hour

    5. **Taboos & Clashes**
       - 彭祖百忌 (Peng Zu Taboos): Actions to avoid
       - 日冲 (Daily Clash): Conflicting zodiac signs
       - 日煞 (Daily Sha): Harmful energies
       - 时冲 (Hour Clash): Hour-specific clash with zodiac
       - 时煞 (Hour Sha): Hour-specific harmful energies

    6. **Seasonal & Environmental Context**
       - 月相 (Moon Phase): Lunar phase information
       - 节日 (Festivals): Traditional celebrations
       - 季节 (Season): Current season

    7. **Seasonal Divisions & Energy Cycles**
       - 三伏 (Three Fu): Summer heat periods (Dog Days)
       - 数九 (Shu Jiu): Winter energy counting (Nine Days of Winter)
       - 六曜 (Liu Yao): Six bright stars/weekday system

    8. **Phenological & Astronomical Data**
       - 物候 (Wu Hou): Phenology describing nature's activity
       - 候 (Hou): Seasonal phase or sub-seasonal marker
       - 日禄 (Day Lu): Day prosperity/wealth marker

    9. **Spiritual Calendar Systems**
       - 佛历 (Foto): Buddhist calendar and dates
       - 道历 (Tao): Taoist calendar and dates

    10. **Qi Markers & Solar Terms**
       - 前气令 (Previous Qi): Previous solar term marker with timing
       - 下个气令 (Next Qi): Next solar term marker with timing
       - Marks seasonal transitions and energy shifts

    11. **Jie Markers & Mid-Month Solar Terms**
       - 前节 (Previous Jie): Previous mid-month solar term marker with timing
       - 下个节 (Next Jie): Next mid-month solar term marker with timing
       - Complements Qi markers for complete seasonal tracking

    12. **Nine Star Energy & Feng Shui**
       - 年九星 (Year Star): Calculated by Li Chun boundary (parameter 3)
       - 月九星 (Month Star): Based on lunar month
       - 日九星 (Day Star): Determined by Solstice proximity
       - 时九星 (Time Star): Hour-specific nine star

    13. **Tai Sui Positions**
       - 年太岁 (Year Tai Sui): Year Tai Sui position relative to deity (12 positions)
       - 月太岁 (Month Tai Sui): Month Tai Sui position relative to deity (12 positions)
       - 日太岁 (Day Tai Sui): Day Tai Sui position relative to deity (12 positions)

Professional Applications:
    - Choosing auspicious directions for major activities
    - Planning when to avoid certain actions
    - Understanding environmental influences on birth
    - Selecting directions for home/business placement
    - Determining favorable times for significant events
"""

from lunar_python import Lunar
from datetime import datetime


def get_birth_environment(lunar_birthday: Lunar) -> dict:
    """
    Extract comprehensive birth environment information.

    Captures geographical luck, directional auspiciousness, taboos,
    auspicious/inauspicious actions, and celestial context.

    Args:
        lunar_birthday: Lunar object from lunar_python library

    Returns:
        Dictionary with birth environment data organized by 14 categories:
        {
            "出生环境": {
                "星宿与神性背景": {...},
                "方位与地理运气": {...},
                "天神与护佑": {...},
                "宜忌与行动指导": {...},
                "禁忌与冲煞": {...},
                "季节与节日": {...},
                "季节能量周期": {...},
                "物候与天文": {...},
                "灵性历源": {...},
                "气令与节气": {...},
                "节令与中气": {...},
                "九星能量与风水": {...},
                "出生时刻方位": {...},
                "太岁位置": {...}
            }
        }
    """

    # 1. Constellation & Spiritual Background (二十八星宿与神性背景)
    constellation = {
        "星宿": lunar_birthday.getXiu()
        + lunar_birthday.getZheng()
        + lunar_birthday.getAnimal(),
        "星宿运势": lunar_birthday.getXiuLuck(),
        "星宿诗诀": lunar_birthday.getXiuSong(),
        "方位": lunar_birthday.getGong() + "方" + lunar_birthday.getShou(),
    }

    # 2. Geographic Luck Directions (方位与地理运气)
    directions = {
        "财神方位": {
            "方向": lunar_birthday.getDayPositionCaiDesc(),
            "方位": lunar_birthday.getDayPositionCai(),
        },
        "喜神方位": {
            "方向": lunar_birthday.getDayPositionXiDesc(),
            "方位": lunar_birthday.getDayPositionXi(),
        },
        "福神方位": {
            "方向": lunar_birthday.getDayPositionFuDesc(),
            "方位": lunar_birthday.getDayPositionFu(),
        },
        "阳贵神方位": {
            "方向": lunar_birthday.getDayPositionYangGuiDesc(),
            "方位": lunar_birthday.getDayPositionYangGui(),
        },
        "阴贵神方位": {
            "方向": lunar_birthday.getDayPositionYinGuiDesc(),
            "方位": lunar_birthday.getDayPositionYinGui(),
        },
    }

    # 3. Heavenly Deities (天神与护佑)
    deities = {
        "日值天神": {
            "天神": lunar_birthday.getDayTianShen(),
            "运势": lunar_birthday.getDayTianShenLuck(),
        },
        "时值天神": {
            "天神": lunar_birthday.getTimeTianShen(),
            "运势": lunar_birthday.getTimeTianShenLuck(),
        },
    }

    # 4. Auspicious & Inauspicious Actions (宜忌与行动指导)
    auspicious_actions = {
        "日宜": lunar_birthday.getDayYi(),
        "日忌": lunar_birthday.getDayJi(),
        "日吉神宜趋": lunar_birthday.getDayJiShen(),
        "日凶煞宜忌": lunar_birthday.getDayXiongSha(),
        "时宜": lunar_birthday.getTimeYi(),
        "时忌": lunar_birthday.getTimeJi(),
    }

    # 5. Taboos & Clashes (禁忌与冲煞)
    taboos_clashes = {
        "彭祖百忌": {
            "干": lunar_birthday.getPengZuGan(),
            "支": lunar_birthday.getPengZuZhi(),
        },
        "日冲": lunar_birthday.getChongDesc(),
        "日柱冲克": lunar_birthday.getDayChongDesc(),
        "日煞": lunar_birthday.getSha(),
        "日柱方位煞": lunar_birthday.getDaySha(),
        "时冲": lunar_birthday.getTimeChongDesc(),
        "时煞": lunar_birthday.getTimeSha(),
    }

    # 6. Seasonal & Festival Context (季节与节日)
    seasonal = {
        "月相": lunar_birthday.getYueXiang(),
        "季节": lunar_birthday.getSeason(),
        "传统节日": lunar_birthday.getFestivals(),
        "其他节日": lunar_birthday.getOtherFestivals(),
    }

    # 7. Seasonal Divisions & Energy Cycles (季节能量周期)
    fu = lunar_birthday.getFu()
    shujiu = lunar_birthday.getShuJiu()
    seasonal_cycles = {
        "三伏": fu.toFullString() if fu else "非三伏天",
        "数九": shujiu.toFullString() if shujiu else "非数九天",
        "六曜": lunar_birthday.getLiuYao(),
    }

    # 8. Phenological & Astronomical Data (物候与天文)
    phenology = {
        "物候": lunar_birthday.getWuHou(),
        "候": lunar_birthday.getHou(),
        "日禄": lunar_birthday.getDayLu(),
    }

    # 9. Spiritual Calendar Systems (灵性历源)
    foto = lunar_birthday.getFoto()
    tao = lunar_birthday.getTao()
    spiritual_calendars = {
        "佛历": foto.toFullString() if foto else "N/A",
        "道历": tao.toFullString() if tao else "N/A",
    }

    # 10. Qi Markers & Solar Terms (气令与节气)
    prev_qi = lunar_birthday.getPrevQi()
    next_qi = lunar_birthday.getNextQi()

    # Calculate progress percentage for qi markers
    qi_progress = None
    if prev_qi and next_qi:
        prev_solar = prev_qi.getSolar()
        next_solar = next_qi.getSolar()
        current_solar = lunar_birthday.getSolar()

        prev_dt = datetime(
            prev_solar.getYear(),
            prev_solar.getMonth(),
            prev_solar.getDay(),
            prev_solar.getHour(),
            prev_solar.getMinute(),
            prev_solar.getSecond(),
        )
        next_dt = datetime(
            next_solar.getYear(),
            next_solar.getMonth(),
            next_solar.getDay(),
            next_solar.getHour(),
            next_solar.getMinute(),
            next_solar.getSecond(),
        )
        current_dt = datetime(
            current_solar.getYear(),
            current_solar.getMonth(),
            current_solar.getDay(),
            current_solar.getHour(),
            current_solar.getMinute(),
            current_solar.getSecond(),
        )

        total_seconds = (next_dt - prev_dt).total_seconds()
        elapsed_seconds = (current_dt - prev_dt).total_seconds()

        if total_seconds > 0:
            qi_progress = round((elapsed_seconds / total_seconds) * 100, 2)

    qi_markers = {
        "前气令": {
            "名称": prev_qi.getName() if prev_qi else "N/A",
            "时间": prev_qi.getSolar().toYmdHms() if prev_qi else "N/A",
        },
        "下个气令": {
            "名称": next_qi.getName() if next_qi else "N/A",
            "时间": next_qi.getSolar().toYmdHms() if next_qi else "N/A",
        },
        "进度百分比": f"{qi_progress}%" if qi_progress is not None else "N/A",
    }

    # 11. Jie Markers & Mid-Month Solar Terms (节令与中气)
    prev_jie = lunar_birthday.getPrevJie()
    next_jie = lunar_birthday.getNextJie()

    # Calculate progress percentage for jie markers
    jie_progress = None
    if prev_jie and next_jie:
        prev_solar = prev_jie.getSolar()
        next_solar = next_jie.getSolar()
        current_solar = lunar_birthday.getSolar()

        prev_dt = datetime(
            prev_solar.getYear(),
            prev_solar.getMonth(),
            prev_solar.getDay(),
            prev_solar.getHour(),
            prev_solar.getMinute(),
            prev_solar.getSecond(),
        )
        next_dt = datetime(
            next_solar.getYear(),
            next_solar.getMonth(),
            next_solar.getDay(),
            next_solar.getHour(),
            next_solar.getMinute(),
            next_solar.getSecond(),
        )
        current_dt = datetime(
            current_solar.getYear(),
            current_solar.getMonth(),
            current_solar.getDay(),
            current_solar.getHour(),
            current_solar.getMinute(),
            current_solar.getSecond(),
        )

        total_seconds = (next_dt - prev_dt).total_seconds()
        elapsed_seconds = (current_dt - prev_dt).total_seconds()

        if total_seconds > 0:
            jie_progress = round((elapsed_seconds / total_seconds) * 100, 2)

    jie_markers = {
        "前节": {
            "名称": prev_jie.getName() if prev_jie else "N/A",
            "时间": prev_jie.getSolar().toYmdHms() if prev_jie else "N/A",
        },
        "下个节": {
            "名称": next_jie.getName() if next_jie else "N/A",
            "时间": next_jie.getSolar().toYmdHms() if next_jie else "N/A",
        },
        "进度百分比": f"{jie_progress}%" if jie_progress is not None else "N/A",
    }

    # 12. Nine Star Energy & Feng Shui (九星能量与风水)
    # Parameter 3 = Solar Term (exact minute and second based on Li Chun transition)
    year_star = lunar_birthday.getYearNineStar(3)
    month_star = lunar_birthday.getMonthNineStar(3)
    day_star = lunar_birthday.getDayNineStar()
    time_star = lunar_birthday.getTimeNineStar()
    nine_star_feng_shui = {
        "年九星": year_star.toFullString() if year_star else "N/A",
        "月九星": month_star.toFullString() if month_star else "N/A",
        "日九星": day_star.toFullString() if day_star else "N/A",
        "时九星": time_star.toFullString() if time_star else "N/A",
    }

    # 13. Tai Sui Positions (太岁位置)
    tai_sui_positions = {
        "年太岁": {
            "位置": lunar_birthday.getYearPositionTaiSui(),
            "描述": lunar_birthday.getYearPositionTaiSuiDesc(),
        },
        "月太岁": {
            "位置": lunar_birthday.getMonthPositionTaiSui(),
            "描述": lunar_birthday.getMonthPositionTaiSuiDesc(),
        },
        "日太岁": {
            "位置": lunar_birthday.getDayPositionTaiSui(),
            "描述": lunar_birthday.getDayPositionTaiSuiDesc(),
        },
    }

    # Build complete result
    result = {
        "出生环境": {
            "系统初始化参数": "以下数据代表系统初始化瞬间的‘宇宙背景辐射’与‘环境系数’。请注意，这些并非人格特质，而是影响五行初始流动的‘大气条件’与‘场域摩擦力点’。",
            "星宿与神性背景": constellation,
            "方位与地理运气": directions,
            "天神与护佑": deities,
            "宜忌与行动指导": auspicious_actions,
            "禁忌与冲煞": taboos_clashes,
            "季节与节日": seasonal,
            "季节能量周期": seasonal_cycles,
            "物候与天文": phenology,
            "灵性历源": spiritual_calendars,
            "气令与节气": qi_markers,
            "节令与中气": jie_markers,
            "九星能量与风水": nine_star_feng_shui,
            "太岁位置": tai_sui_positions,
        }
    }

    return result


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from src.astronomer_calculations.bazi_pillars import get_bazi_pillars
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
    from datetime import datetime
    from lunar_python import Solar

    # python -m src.astronomer_calculations.birth_environment

    # Desmond's birthday example
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)

    # Sample birthday example
    # solar_birthday = Solar.fromYmdHms(1990, 1, 30, 4, 0, 0)
    # datetime_birthday = datetime(1990, 1, 30, 4, 0, 0)
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
    result = get_birth_environment(lunar_birthday)

    # Print JSON output
    print("\n```json")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("```\n")
