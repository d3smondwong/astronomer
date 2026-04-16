"""
十神 Ten Gods (Shi Shen)

Returns the Ten God relationship for each stem position across the Four Pillars
(年柱, 月柱, 日柱, 时柱). Each pillar contains:
  - heavenly_stem_ten_god — Ten God of the 天干
  - primary_qi_ten_god    — Ten God of the 本气 hidden stem (or None)
  - middle_qi_ten_god     — Ten God of the 中气 hidden stem (or None)
  - residual_qi_ten_god   — Ten God of the 余气 hidden stem (or None)

The 日柱 天干 is always "日主" (Day Master — the self reference).
"""


def _hidden_ten_gods(shi_shen_zhi: list) -> tuple:
    """Unpack up to 3 Ten Gods for the hidden stems (本气, 中气, 余气), padding with "无"."""
    gods = list(shi_shen_zhi) + ["无", "无", "无"]
    return gods[0] or "无", gods[1] or "无", gods[2] or "无"


def get_ten_gods(bazi) -> dict:
    """
    Return the Ten Gods for each of the Four Pillars.

    Args:
        bazi: EightChar object from lunar_birthday.getEightChar()

    Returns:
        dict keyed by 年柱, 月柱, 日柱, 时柱.
        Each pillar contains: heavenly_stem_ten_god, primary_qi_ten_god,
                              middle_qi_ten_god, residual_qi_ten_god.
        Hidden stem Ten Gods that are not present are returned as "无".
    """
    def make_pillar(heavenly_stem_ten_god: str, zhi_gods_fn) -> dict:
        primary_qi_ten_god, middle_qi_ten_god, residual_qi_ten_god = _hidden_ten_gods(zhi_gods_fn())
        return {
            "天干十神": heavenly_stem_ten_god,
            "藏干十神": {
                "本气十神": primary_qi_ten_god,
                "中气十神": middle_qi_ten_god,
                "余气十神": residual_qi_ten_god,
            },
        }

    return {
        "年柱": make_pillar(bazi.getYearShiShenGan(),  bazi.getYearShiShenZhi),
        "月柱": make_pillar(bazi.getMonthShiShenGan(), bazi.getMonthShiShenZhi),
        "日柱": make_pillar("日主",                     bazi.getDayShiShenZhi),
        "时柱": make_pillar(bazi.getTimeShiShenGan(),  bazi.getTimeShiShenZhi),
    }
