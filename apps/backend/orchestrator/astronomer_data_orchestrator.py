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
from apps.backend.astronomer_logic.bazi_key import encode_bazi_key
from apps.backend.astronomer_logic.twelve_life_stages import get_twelve_life_stages
from apps.backend.astronomer_logic.void_xun_kong import get_void_xun_kong, check_pillar_void_status
from apps.backend.astronomer_logic.ten_gods import get_ten_gods, apply_heavenlystem_tranformation_tengods, apply_qi_sha_transformation, apply_shi_shen_transformation, get_effective_stem
from apps.backend.astronomer_logic.na_yin import get_na_yin
from apps.backend.astronomer_logic.tai_ming_shen import get_san_yuan
from apps.backend.astronomer_logic.classical_texts import get_classical_texts
from apps.backend.astronomer_logic.natal_shen_sha import get_shen_sha
from apps.backend.astronomer_logic.natal_interpretation_shen_sha import get_shen_sha_interpretations
from apps.backend.astronomer_logic.natal_interactions import get_natal_interactions
from apps.backend.astronomer_logic.day_master_strength import get_day_master_strength
from apps.backend.astronomer_logic.natal_five_elements import QualitativeFiveElementsClassifier, get_pillar_five_elements
from apps.backend.astronomer_logic.yong_shen import get_yong_shen
from apps.backend.astronomer_logic.interaction_natal_chart import get_natal_interpretations

_PILLAR_KEYS = ["年柱", "月柱", "日柱", "时柱"]


def get_lunar_birthday(
    birth_datetime: datetime,
    latitude: float,
    longitude: float,
    use_solar_time_correction: bool,
):
    """
    Convert a wall-clock birth datetime to the lunar-python Lunar object,
    optionally applying the True Solar Time correction.

    Shared by the natal and cycles orchestrators so TST handling can never
    drift between the two endpoints.
    """
    if use_solar_time_correction:
        # Convert to True Solar Time
        tst_solar = get_true_solar_time(birth_datetime, latitude, longitude)
        return tst_solar.getLunar()
    # Use standard clock time directly
    solar_date = Solar.fromYmdHms(
        birth_datetime.year,
        birth_datetime.month,
        birth_datetime.day,
        birth_datetime.hour,
        birth_datetime.minute,
        birth_datetime.second,
    )
    return solar_date.getLunar()


def calculate_natal_chart(
    birth_datetime: datetime,
    latitude: float,
    longitude: float,
    gender: int,
    use_solar_time_correction: bool = False,
) -> tuple[dict, str]:
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
        (chart, chart_key) where:
          - chart: dict with top-level key 四柱实体 containing 年柱, 月柱, 日柱, 时柱
                   (each pillar holds all Phase 1 data), plus the other top-level fields.
          - chart_key: the 八字-based cache key (see bazi_key.encode_bazi_key) — identical
                   for everyone with the same four pillars + gender.
    """
    # Get lunar date - either via TST conversion or directly from standard time
    lunar_birthday = get_lunar_birthday(
        birth_datetime, latitude, longitude, use_solar_time_correction
    )

    lunar_time = lunar_birthday.getTime()
    bazi = lunar_birthday.getEightChar()

    # 八字-based cache key — identical for everyone with the same four pillars + gender.
    chart_key = encode_bazi_key(bazi, gender)

    # Modules keyed by 年柱/月柱/日柱/时柱
    pillars        = get_bazi_pillars(bazi)
    life_stages    = get_twelve_life_stages(bazi, pillars)
    void           = get_void_xun_kong(bazi)
    pillar_void    = check_pillar_void_status(void, pillars)
    ten_gods       = get_ten_gods(bazi)
    na_yin         = get_na_yin(bazi)
    classical_texts_data = get_classical_texts(pillars)
    pillar_elements = get_pillar_five_elements(pillars)

    # Enrich pillars 藏干 with 十神 — consumed by get_natal_interactions
    for k in _PILLAR_KEYS:
        for tier, info in pillars[k]["藏干"].items():
            info["十神"] = ten_gods[k]["藏干十神"][tier]

    # Merge all module outputs per pillar
    si_zhu = {
        key: {
            "天干": {
                "天干":    pillars[key]["天干"],
                "阴阳":    pillars[key]["天干阴阳"],
                "五行":    pillar_elements[key]["天干五行"],
                "根基强度": pillars[key]["根基强度"],
                "通根于":  pillars[key]["通根于"],
                "十神":    ten_gods[key]["天干十神"],
            },
            "地支": {
                "地支": pillars[key]["地支"],
                "阴阳": pillars[key]["地支阴阳"],
                "五行": pillar_elements[key]["地支五行"],
            },
            "藏干": {
                tier: {
                    **info,  # 天干, 阴阳, 十神
                    "五行": pillar_elements[key]["藏干五行"][tier],
                }
                for tier, info in pillars[key]["藏干"].items()
            },
            "十二长生": life_stages[key],
            "空亡": {
                "本柱旬空": void[key],
                **pillar_void[key],
            },
            "纳音":    na_yin[key],
        }
        for key in _PILLAR_KEYS
    }

    # Individual Modules
    natal_interactions_data = get_natal_interactions(pillars, void)
    ten_gods, si_zhu = apply_heavenlystem_tranformation_tengods(ten_gods, si_zhu, natal_interactions_data, pillars["日柱"]["天干"])
    day_master_data = get_day_master_strength(bazi, pillars, ten_gods, natal_interactions_data, pillar_void)
    ten_gods, si_zhu = apply_qi_sha_transformation(ten_gods, si_zhu, day_master_data)
    ten_gods, si_zhu = apply_shi_shen_transformation(ten_gods, si_zhu)
    five_elements_data = QualitativeFiveElementsClassifier(si_zhu, natal_interactions_data, lunar_birthday=lunar_birthday).classify_all()
    # 格局 detection needs 力量 (raw pre-cap strength) to find which force a surrendered
    # chart follows. The response payload above deliberately stays 力量-free, so compute
    # the strength-bearing map separately rather than widening the /natal contract.
    five_elements_strength = QualitativeFiveElementsClassifier(
        si_zhu, natal_interactions_data, lunar_birthday=lunar_birthday
    ).classify_all(include_strength=True)["五行"]
    # 调候 is indexed by the EFFECTIVE day stem. Under a 化气格 the chart's climate is
    # experienced by the 化神, not by the stem it used to be — a 丁火 in 巳月 lives in a
    # different world than a 癸水 in 巳月, and the 经典 prose we hand the LLM must describe
    # the day master the chart actually has. No-op on a 正格 chart.
    effective_day_stem = get_effective_stem(
        bazi.getDayGan(), day_master_data["日主"]["五行"]
    )
    yong_shen_data = get_yong_shen(
        effective_day_stem,
        day_master_data["日主"]["五行"],
        bazi.getMonthZhi(),
        day_master_data,
        five_elements_strength,
        natal_interactions_data,
    )
    tai_ming_shen = get_san_yuan(lunar_birthday)
    shen_sha = get_shen_sha(bazi, na_yin, gender)
    shen_sha_with_interpretations = get_shen_sha_interpretations(shen_sha)

    # Build partial chart for the classical-text interpretation layer.
    # 胎命身 is included so the interpretation engine can address 胎元 as the mother
    # palace (论六亲); without it build_chart_context would see no 胎元 data.
    partial_chart = {
        "性别": "男" if gender == 1 else "女",
        "四柱实体": si_zhu,
        "_lunar_birthday": lunar_birthday,
        **day_master_data,
        **five_elements_data,
        **shen_sha_with_interpretations,
        **tai_ming_shen,
        **natal_interactions_data,
    }
    natal_interpretations_data = get_natal_interpretations(partial_chart)

    chart = {
        # No raw wall-clock time here: this dict is shared across everyone with the same
        # 八字, so it must hold only BaZi-deterministic content (lunar date + 时辰). The
        # exact birth time is per-profile and shown from the profile record, not from here.
        "农历生日": f"{lunar_birthday.toString()} ({lunar_time})",
        "性别": "男" if gender == 1 else "女",
        "生肖": lunar_birthday.getYearShengXiao(),
        "生时节气": lunar_birthday.getJieQi() or (lunar_birthday.getPrevJieQi().getName() if lunar_birthday.getPrevJieQi() else ""),
        "四柱实体": si_zhu,
        **day_master_data,
        **five_elements_data,
        "用神": yong_shen_data,
        **shen_sha_with_interpretations,
        **tai_ming_shen,
        **classical_texts_data,
        **natal_interactions_data,
        **natal_interpretations_data,
    }

    return chart, chart_key


# ============================================================================
# EXECUTION
# python -m apps.backend.orchestrator.astronomer_data_orchestrator
# ============================================================================
if __name__ == "__main__":
    # Cross-check output against the TypeScript baziOrchestrator for the same birth date.

    from apps.utils.logging import configure_logging, get_logger
    from datetime import datetime as dt

    logger = configure_logging()
    logger = get_logger(__name__)

    # ── Subjects ──────────────────────────────────────────────────────────────
    subjects = {
        # "Desmond": (dt(1985, 11, 25, 17, 7, 0), 1.3253, 103.808053, 1),
        "Corinne": (dt(1987, 6, 3, 12, 6, 0), 1.4759, 103.808053, 0),
        # "Lara":    (dt(2025,  7, 31,  9, 10, 0), 1.3253,  103.808053, 0),
        # "Waifu": (dt(1985, 2, 11, 10, 15, 0), 1.3253, 103.808053, 1),
        # "Ayden": (dt(2020, 2, 23, 00, 34, 0), 1.3253, 103.808053, 1),
    }

    for name, (birthday, lat, lon, gender) in subjects.items():
        logger.info("=" * 60)
        logger.info("Subject: %s  (%s)", name, birthday.strftime("%Y-%m-%d %H:%M"))

        chart, chart_key = calculate_natal_chart(birthday, lat, lon, gender=gender, use_solar_time_correction=True)
        logger.info("chart_key: %s", chart_key)
        logger.info("Natal chart output:\n%s", json.dumps(chart, ensure_ascii=False, indent=2))
