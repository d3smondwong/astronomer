"""
Three Palaces (胎命身) Calculation Module

This module calculates the Three Palaces (胎命身) for BaZi charts.

Core Concepts:
    - 胎命身 (Tai Ming Shen): Three Palaces representing key life areas

    The Three Palaces are:
    1. 胎元 (Tai Yuan - Conception Palace): Represents one's conception and gestation
       - Derived from month pillar and hour pillar
       - Used for fortune during early childhood and family influence
       - Shows ancestral karma and inherited destiny

    2. 命宫 (Ming Gong - Life Palace): Represents one's overall life destiny
       - Derived from the hour pillar
       - Most important palace in Four Pillars system
       - Shows personality, career path, and major life direction

    3. 身宫 (Shen Gong - Body/Action Palace): Represents one's immediate circumstances
       - Derived from day pillar
       - Shows physical health and day-to-day experiences
       - Reflects how destiny is actively manifested

Each palace has:
    - 干支 (Gan Zhi): Heavenly Stem and Earthly Branch combination
    - 纳音 (Na Yin): Five Elements classification of the palace

Professional Applications:
    - Timing of significant life events
    - Determining favorable periods for major decisions
    - Assessing family legacy and childhood influences
    - Understanding physical health and vitality
"""

from lunar_python import Lunar
from lunar_python.util import LunarUtil

from apps.backend.astronomer_logic.bazi_pillars import _YANG_STEMS, _YANG_BRANCHES, _yin_yang
from apps.backend.astronomer_logic.twelve_life_stages import _self_seated_stage

_HIDDEN_TIERS = ("本气", "中气", "余气")


def _enrich_palace(gan_zhi: str, day_gan: str) -> dict:
    """Build a 四柱实体-shaped pillar entity for a palace (胎元/命宫/身宫).

    The palace already carries 干支 + 纳音; this derives the same per-pillar fields the
    Four Pillars expose — 天干 (with 十神 vs Day Master), 地支, 藏干 (with 十神), and the
    日干/自坐 十二长生 — so the palace can be addressed as a pillar by the interpretation
    engine (e.g. 胎元 = mother palace in 论六亲). 十神 uses LunarUtil.SHI_SHEN keyed by
    Day-Master stem + target stem; 十二长生(日干) reuses _self_seated_stage with the Day
    Master's stem (there is no library Di Shi for palaces).
    """
    if not gan_zhi or len(gan_zhi) < 2:
        return {}
    gan, zhi = gan_zhi[0], gan_zhi[1]

    cang_gan = {}
    for tier, stem in zip(_HIDDEN_TIERS, LunarUtil.ZHI_HIDE_GAN.get(zhi, [])):
        cang_gan[tier] = {
            "天干": stem,
            "阴阳": _yin_yang(stem, _YANG_STEMS),
            "五行": LunarUtil.WU_XING_GAN.get(stem),
            "十神": LunarUtil.SHI_SHEN.get(day_gan + stem, "无"),
        }

    return {
        "天干": {
            "天干": gan,
            "阴阳": _yin_yang(gan, _YANG_STEMS),
            "五行": LunarUtil.WU_XING_GAN.get(gan),
            "十神": LunarUtil.SHI_SHEN.get(day_gan + gan, "无"),
        },
        "地支": {
            "地支": zhi,
            "阴阳": _yin_yang(zhi, _YANG_BRANCHES),
            "五行": LunarUtil.WU_XING_ZHI.get(zhi),
        },
        "藏干": cang_gan,
        "十二长生": {
            "日干": _self_seated_stage(day_gan, zhi),
            "自坐": _self_seated_stage(gan, zhi),
        },
    }


def get_san_yuan(lunar_birthday: Lunar):
    """
    Extract Three Palaces (胎命身) for a given lunar birthday.

    Calculates the Conception, Life, and Body Palaces along with their
    Na Yin (Five Elements) classifications.

    Args:
        lunar_birthday: Lunar object from lunar_python library

    Returns:
        Dictionary with three palaces data in professional BaZi format:
        {
            "胎命身": {
                "胎元": {"干支": "...", "纳音": "..."},
                "命宫": {"干支": "...", "纳音": "..."},
                "身宫": {"干支": "...", "纳音": "..."}
            }
        }
    """

    baZi = lunar_birthday.getEightChar()
    day_gan = baZi.getDayGan()  # Day Master — reference stem for 十神 / 十二长生

    # Extract three palaces and their na yin
    tai_yuan = baZi.getTaiYuan()
    tai_yuan_na_yin = baZi.getTaiYuanNaYin()

    ming_gong = baZi.getMingGong()
    ming_gong_na_yin = baZi.getMingGongNaYin()

    shen_gong = baZi.getShenGong()
    shen_gong_na_yin = baZi.getShenGongNaYin()

    # Build structured result. Each palace carries its 干支 + 纳音 and the derived
    # per-pillar fields (天干/地支/藏干/十二长生) so it can be addressed as a pillar
    # by the classical-text interpretation engine (胎元 = mother palace in 论六亲).
    result = {
        "胎命身": {
            "胎元": {
                "干支": tai_yuan,
                "纳音": tai_yuan_na_yin,
                **_enrich_palace(tai_yuan, day_gan),
            },
            "命宫": {
                "干支": ming_gong,
                "纳音": ming_gong_na_yin,
                **_enrich_palace(ming_gong, day_gan),
            },
            "身宫": {
                "干支": shen_gong,
                "纳音": shen_gong_na_yin,
                **_enrich_palace(shen_gong, day_gan),
            },
        }
    }

    return result


