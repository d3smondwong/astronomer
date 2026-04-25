"""
Astronomer Data Orchestrator

Accepts raw birth input, runs the True Solar Time conversion, then calls
each astronomer_logic module in the correct sequence and assembles the
complete chart dict.

Output is organised by pillar under the top-level key 四柱实体:

  {
    "四柱实体": {
      "年柱": { heavenly_stem, earthly_branch, primary_qi, middle_qi, residual_qi,
                life_stage, void, ten_gods, na_yin },
      "月柱": { ... },
      "日柱": { ... },
      "时柱": { ... },
    }
  }
"""

import json
from datetime import datetime

from lunar_python import Solar
from apps.backend.astronomer_logic.true_solar_time import get_true_solar_time
from apps.backend.astronomer_logic.bazi_pillars import get_bazi_pillars
from apps.backend.astronomer_logic.twelve_life_stages import get_twelve_life_stages
from apps.backend.astronomer_logic.void_xun_kong import get_void_xun_kong, check_pillar_void_status
from apps.backend.astronomer_logic.ten_gods import get_ten_gods
from apps.backend.astronomer_logic.na_yin import get_na_yin
from apps.backend.astronomer_logic.tai_ming_shen import get_san_yuan
from apps.backend.astronomer_logic.classical_texts import get_classical_texts
from apps.backend.astronomer_logic.natal_shen_sha import get_shen_sha
from apps.backend.astronomer_logic.interpretation_shen_sha import get_shen_sha_interpretations
from apps.backend.astronomer_logic.natal_interactions import get_natal_interactions

_PILLAR_KEYS = ["年柱", "月柱", "日柱", "时柱"]

def calculate_natal_chart(
    birth_datetime: datetime,
    latitude: float,
    longitude: float,
    gender: int,
    use_solar_time_correction: bool = False,
) -> dict:
    """
    Run the full Phase 1 natal chart calculation.

    Args:
        birth_datetime:          Wall-clock birth datetime (naive).
        latitude:                Birth location latitude in decimal degrees.
        longitude:               Birth location longitude in decimal degrees.
        gender:                  1 = male, 0 = female.
        use_solar_time_correction: If True, applies True Solar Time conversion.
                                  If False, uses standard clock time directly.

    Returns:
        Dict with top-level key 四柱实体 containing 年柱, 月柱, 日柱, 时柱.
        Each pillar contains all Phase 1 data for that pillar.
    """
    # Get lunar date - either via TST conversion or directly from standard time
    if use_solar_time_correction:
        # Convert to True Solar Time
        tst_solar = get_true_solar_time(birth_datetime, latitude, longitude)
        lunar_birthday = tst_solar.getLunar()
    else:
        # Use standard clock time directly
        solar_date = Solar.fromYmdHms(
            birth_datetime.year,
            birth_datetime.month,
            birth_datetime.day,
            birth_datetime.hour,
            birth_datetime.minute,
            birth_datetime.second,
        )
        lunar_birthday = solar_date.getLunar()

    lunar_time = lunar_birthday.getTime()
    bazi = lunar_birthday.getEightChar()

    # Modules keyed by 年柱/月柱/日柱/时柱
    pillars        = get_bazi_pillars(bazi)
    life_stages    = get_twelve_life_stages(bazi, pillars)
    void           = get_void_xun_kong(bazi)
    pillar_void    = check_pillar_void_status(void, pillars)
    ten_gods       = get_ten_gods(bazi)
    na_yin         = get_na_yin(bazi)
    classical_texts_data = get_classical_texts(pillars)

    # Merge all module outputs per pillar
    si_zhu = {
        key: {
            "天干":     pillars[key]["天干"],
            "根基强度": pillars[key]["根基强度"],
            "通根于":     pillars[key]["通根于"],
            "天干十神": ten_gods[key]["天干十神"],
            "地支":     pillars[key]["地支"],
            "藏干":     pillars[key]["藏干"],
            "藏干十神": ten_gods[key]["藏干十神"],
            "十二长生": life_stages[key],
            "空亡地支": void[key],
            **pillar_void[key],
            "纳音":     na_yin[key],
        }
        for key in _PILLAR_KEYS
    }

    # Merge 藏干十神 into pillars so natal_interactions can read ten gods without recomputing
    for k in _PILLAR_KEYS:
        pillars[k]["藏干十神"] = ten_gods[k]["藏干十神"]

    # Individual Modules
    natal_interactions_data = get_natal_interactions(pillars, void)
    tai_ming_shen = get_san_yuan(lunar_birthday)
    shen_sha = get_shen_sha(bazi, na_yin, gender)
    shen_sha_with_interpretations = get_shen_sha_interpretations(shen_sha)

    return {
        "农历生日": lunar_birthday.toString() + f" {birth_datetime.hour:02d}:{birth_datetime.minute:02d} ({lunar_time})",
        "性别": "男" if gender == 1 else "女",
        "生肖": lunar_birthday.getYearShengXiao(),
        "生时节气": lunar_birthday.getJieQi(),
        "四柱实体": si_zhu,
        **shen_sha_with_interpretations,
        **tai_ming_shen,
        **classical_texts_data,
        **natal_interactions_data,
    }


# --- Verification ---

if __name__ == "__main__":
    # python -m apps.backend.orchestrator.astronomer_data_orchestrator
    # Cross-check output against the TypeScript baziOrchestrator for the same birth date.

    from src.utils.logging import configure_logging

    logger = configure_logging()

    birth = datetime(1985, 11, 25, 17, 7, 0)
    lat, lng = 1.3253, 103.8080

    chart = calculate_natal_chart(birth, lat, lng, gender=1)
    logger.info("Natal chart output:\n%s", json.dumps(chart, ensure_ascii=False, indent=2))
