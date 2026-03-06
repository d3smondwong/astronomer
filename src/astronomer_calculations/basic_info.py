"""
Basic Information Extraction Module

This module extracts fundamental birth information including solar/lunar dates,
time adjustments, and seasonal context (Jie Qi - Solar Terms).
"""

from datetime import datetime
from lunar_python import Solar
from src.astronomer_calculations.solar_lunar_time import get_true_solar_time

# Legend:
# 旺 (Wang): Strongest (Season's Element)
# 相 (Xiang): Strong (Produced by Season)
# 休 (Xiu): Weakening (Produces the Season - 'exhausted mother')
# 囚 (Qiu): Weak (Produced by what counters the Season)
# 死 (Si): Weakest (Countered by the Season)
seasonal_info = {
    "寅": {
        "season": "初春",
        "旺": "木",
        "相": "火",
        "休": "水",
        "囚": "金",
        "死": "土",
        "climate": "余寒",
        "needs": "火",
    },
    "卯": {
        "season": "仲春",
        "旺": "木",
        "相": "火",
        "休": "水",
        "囚": "金",
        "死": "土",
        "climate": "温",
        "needs": "平衡",
    },
    "辰": {
        "season": "季春",
        "旺": "土",
        "相": "金",
        "休": "火",
        "囚": "木",
        "死": "水",
        "climate": "湿",
        "needs": "木, 金",
    },
    "巳": {
        "season": "初夏",
        "旺": "火",
        "相": "土",
        "休": "木",
        "囚": "水",
        "死": "金",
        "climate": "炎",
        "needs": "水",
    },
    "午": {
        "season": "仲夏",
        "旺": "火",
        "相": "土",
        "休": "木",
        "囚": "水",
        "死": "金",
        "climate": "燥",
        "needs": "水",
    },
    "未": {
        "season": "季夏",
        "旺": "土",
        "相": "金",
        "休": "火",
        "囚": "木",
        "死": "水",
        "climate": "暑",
        "needs": "水",
    },
    "申": {
        "season": "初秋",
        "旺": "金",
        "相": "水",
        "休": "土",
        "囚": "火",
        "死": "木",
        "climate": "凉",
        "needs": "平衡",
    },
    "酉": {
        "season": "仲秋",
        "旺": "金",
        "相": "水",
        "休": "土",
        "囚": "火",
        "死": "木",
        "climate": "清",
        "needs": "平衡",
    },
    "戌": {
        "season": "季秋",
        "旺": "土",
        "相": "金",
        "休": "火",
        "囚": "木",
        "死": "水",
        "climate": "燥",
        "needs": "水",
    },
    "亥": {
        "season": "孟冬",
        "旺": "水",
        "相": "木",
        "休": "金",
        "囚": "土",
        "死": "火",
        "climate": "寒",
        "needs": "火",
    },
    "子": {
        "season": "仲冬",
        "旺": "水",
        "相": "木",
        "休": "金",
        "囚": "土",
        "死": "火",
        "climate": "严寒",
        "needs": "火",
    },
    "丑": {
        "season": "季冬",
        "旺": "土",
        "相": "金",
        "休": "火",
        "囚": "木",
        "死": "水",
        "climate": "湿冷",
        "needs": "火",
    },
}


def get_seasonal_info(month_branch: str):
    """
    Returns the specific seasonal information based on the Earthly Branch of the month.
    """
    return seasonal_info.get(month_branch, {})


def get_basic_info(
    standard_solar_birthday: datetime, latitude: float, longitude: float, gender: int
) -> dict:
    """
    Extract basic birth information including solar/lunar conversion and seasonal context.

    Args:
        standard_solar_birthday (datetime): Birth datetime in standard/wall clock time
        latitude (float): Birth location latitude in decimal degrees
        longitude (float): Birth location longitude in decimal degrees
        gender (int): Gender of the person (0 for Female, 1 for Male). Optional.

    Returns:
        dict: Comprehensive birth information including:
            - Solar and lunar dates
            - Gender (if provided)
            - Time adjustment reasons (timezone, equation of time, longitude correction)
            - Seasonal context (current season and adjacent solar terms)
    """
    # Get True Solar Time and conversion details
    true_solar_birthday, conversion_details = get_true_solar_time(
        standard_solar_birthday, latitude, longitude
    )

    # Get lunar calendar
    lunar_birthday = true_solar_birthday.getLunar()

    lunar_hour = lunar_birthday.getHour()
    lunar_minute = lunar_birthday.getMinute()
    lunar_time_str = f"{lunar_hour:02d}:{lunar_minute:02d}"

    lunar_date_str = lunar_birthday.toFullString()

    # Get BaZi pillars for seasonal context
    bazi = lunar_birthday.getEightChar()
    month_branch = bazi.getMonthZhi()

    # Get Five Element seasonal info based on month branch
    seasonal_info = get_seasonal_info(month_branch)

    # Extract adjustment details
    adjustment_reason = {
        "timezone": conversion_details.get("timezone", ""),
        "longitude": conversion_details.get("longitude", ""),
        "utc_offset_hours": round(conversion_details.get("utc_offset_hours", 0), 2),
        "equation_of_time_minutes": round(
            conversion_details.get("equation_of_time_minutes", 0), 2
        ),
        "longitude_correction_minutes": round(
            conversion_details.get("longitude_correction_minutes", 0), 2
        ),
        "total_adjustment_minutes": round(
            conversion_details.get("total_adjustment_minutes", 0), 2
        ),
    }

    lunar_date_str = lunar_birthday.toFullString()

    season_context = {
        "时令": seasonal_info.get("season"),
        "月令地支": month_branch,
        "五行旺度": f"{seasonal_info.get('旺')}旺",
        "五行状态": {
            "旺": seasonal_info.get("旺"),
            "相": seasonal_info.get("相"),
            "休": seasonal_info.get("休"),
            "囚": seasonal_info.get("囚"),
            "死": seasonal_info.get("死"),
        },
        "调候分析": {
            "气候状态": seasonal_info.get("climate"),
            "调节药方": seasonal_info.get("needs"),
            "调节紧迫性": (
                "高"
                if seasonal_info.get("climate")
                in ["严寒", "寒", "湿冷", "炎", "燥", "暑"]
                else "中"
            ),
        },
    }

    return {
        "阳历生日": standard_solar_birthday.strftime("%Y-%m-%d %H:%M:%S"),
        "调整阳历生日": true_solar_birthday.toYmdHms(),
        "调整阳历生日校正依据": adjustment_reason,
        "农历生日": lunar_birthday.toString() + f" {lunar_time_str}",
        "天命大盘": lunar_date_str,
        "性别": "男" if gender == 1 else "女",
        "时令": season_context,
    }


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from datetime import datetime

    # python -m src.astronomer_calculations.basic_info

    # Desmond's birthday example
    standard_solar = datetime(1985, 11, 25, 17, 7, 0)
    latitude = 1.3253
    longitude = 103.808053

    result = get_basic_info(standard_solar, latitude, longitude, gender=1)
    print(json.dumps(result, ensure_ascii=False, indent=2))
