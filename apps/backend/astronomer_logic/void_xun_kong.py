"""
空亡 Xun Kong / Void

Each of the 60 Jiazi pillars belongs to one of six Xun (旬) cycles.
Each cycle leaves two 地支 unused — those are the void (空亡) branches.

Returns the raw two-character void-pair string from the lunar-python library
for each of the Four Pillars (年柱, 月柱, 日柱, 时柱). Example: "戌亥".

Two void conditions are checked by check_pillar_void_status():
  日柱空亡 Primary Void  — Day pillar's pair voids 年柱, 月柱, 时柱.
  互换空亡 Reverse Void  — Year pillar's pair voids 日柱 (roots not supporting the flower).
"""


_VOID_INTERPRETATIONS: dict[tuple[str, str], str] = {
    ("年柱", "日柱空亡"): "年柱落于空亡。祖基薄弱，早年与父母缘分较淡，先天福泽不足。",
    ("月柱", "日柱空亡"): "月柱落于空亡。事业根基不稳，兄弟姊妹情缘疏离，中年发展易逢瓶颈。",
    ("时柱", "日柱空亡"): "时柱落于空亡。与子女缘薄，晚年少人扶持，个人志向难以完全实现。",
    ("日柱", "互换空亡"): "日柱与年柱互换空亡。根不养花——自身缺乏祖荫庇护，性格趋向离散与精神追求。",
}


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

    日柱空亡 Primary Void  — Day pillar's xun kong pair voids 年柱, 月柱, 时柱.
    互换空亡 Reverse Void  — Year pillar's xun kong pair voids 日柱 specifically
                         ("roots not supporting the flower").

    Args:
        void_pairs: Result of get_void_xun_kong() — two-char void pair per pillar.
        pillars:    Result of get_bazi_pillars()  — contains 天干 and 地支 per pillar.

    Returns:
        dict keyed by 年柱, 月柱, 日柱, 时柱. Each value contains:
          "日柱空亡": Descriptive Chinese string when void applies; "无" otherwise.
          "互换空亡": Descriptive Chinese string when void applies; "无" otherwise.
    """
    day_void  = void_pairs["日柱"]
    year_void = void_pairs["年柱"]

    def branch(key: str) -> str:
        return pillars[key]["地支"]

    def _void_value(condition: bool, pillar: str, void_type: str) -> str:
        """Return descriptive string when condition met, else '无'."""
        if not condition:
            return "无"
        return _VOID_INTERPRETATIONS.get((pillar, void_type), "无")

    return {
        "年柱": {
            "日柱空亡": _void_value(branch("年柱") in day_void, "年柱", "日柱空亡"),
            "互换空亡": "无",
        },
        "月柱": {
            "日柱空亡": _void_value(branch("月柱") in day_void, "月柱", "日柱空亡"),
            "互换空亡": "无",
        },
        "日柱": {
            "日柱空亡": "无",
            "互换空亡": _void_value(branch("日柱") in year_void, "日柱", "互换空亡"),
        },
        "时柱": {
            "日柱空亡": _void_value(branch("时柱") in day_void, "时柱", "日柱空亡"),
            "互换空亡": "无",
        },
    }
