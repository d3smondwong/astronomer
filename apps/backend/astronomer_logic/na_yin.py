"""
纳音 Na Yin — Sound Classification of the 60 Jiazi Pillars

Each of the 60 Heavenly Stem + Earthly Branch combinations maps to one of
30 Na Yin phrases representing an elemental sound archetype (e.g. "海中金").

Returns the raw Na Yin string from the lunar-python library for each
of the Four Pillars (年柱, 月柱, 日柱, 时柱).
"""


def get_na_yin(bazi) -> dict:
    """
    Return the 纳音 Na Yin phrase for each of the Four Pillars.

    Args:
        bazi: EightChar object from lunar_birthday.getEightChar()

    Returns:
        dict keyed by 年柱, 月柱, 日柱, 时柱.
        Each value is the raw Chinese Na Yin string (e.g. "海中金").
    """
    return {
        "年柱": bazi.getYearNaYin(),
        "月柱": bazi.getMonthNaYin(),
        "日柱": bazi.getDayNaYin(),
        "时柱": bazi.getTimeNaYin(),
    }
