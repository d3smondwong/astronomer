"""
空亡 Xun Kong / Void

Each of the 60 Jiazi pillars belongs to one of six Xun (旬) cycles.
Each cycle leaves two 地支 unused — those are the void (空亡) branches.

Returns the raw two-character void-pair string from the lunar-python library
for each of the Four Pillars (年柱, 月柱, 日柱, 时柱). Example: "戌亥".

Two void conditions are checked by check_pillar_void_status():
  主空 Primary Void  — Day pillar's pair voids 年柱, 月柱, 时柱.
  倒空 Reverse Void  — Year pillar's pair voids 日柱 (roots not supporting the flower).
"""


def get_void_xun_kong(bazi) -> dict:
    """
    Return the 空亡 void-branch pair for each of the Four Pillars.

    Args:
        bazi: EightChar object from lunar_birthday.getEightChar()

    Returns:
        dict keyed by 年柱, 月柱, 日柱, 时柱.
        Each value is a two-character 地支 pair string (e.g. "戌亥").
    """
    return {
        "年柱": bazi.getYearXunKong(),
        "月柱": bazi.getMonthXunKong(),
        "日柱": bazi.getDayXunKong(),
        "时柱": bazi.getTimeXunKong(),
    }


def check_pillar_void_status(void_pairs: dict, pillars: dict) -> dict:
    """
    Check three void conditions for each of the Four Pillars.

    主空 Primary Void  — Day pillar's xun kong pair voids 年柱, 月柱, 时柱.
    倒空 Reverse Void  — Year pillar's xun kong pair voids 日柱 specifically
                         ("roots not supporting the flower").

    Args:
        void_pairs: Result of get_void_xun_kong() — two-char void pair per pillar.
        pillars:    Result of get_bazi_pillars()  — contains 天干 and 地支 per pillar.

    Returns:
        dict keyed by 年柱, 月柱, 日柱, 时柱. Each value contains:
          "主空": True/False, or None for 日柱 (not self-checked).
          "倒空": True/False for 日柱 only; None for all other pillars.
    """
    day_void  = void_pairs["日柱"]
    year_void = void_pairs["年柱"]

    def branch(key: str) -> str:
        return pillars[key]["地支"]

    return {
        "年柱": {
            "主空": branch("年柱") in day_void,
            "倒空": None,
        },
        "月柱": {
            "主空": branch("月柱") in day_void,
            "倒空": None,
        },
        "日柱": {
            "主空": None,
            "倒空": branch("日柱") in year_void,
        },
        "时柱": {
            "主空": branch("时柱") in day_void,
            "倒空": None,
        },
    }
