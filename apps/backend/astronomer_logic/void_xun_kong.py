"""
空亡 Xun Kong / Void. Using the Xu Zi Ping's (徐子平) method of void calculation, which is the most commonly used method in Chinese astrology.

Each of the 60 Jiazi pillars belongs to one of six Xun (旬) cycles.
Each cycle leaves two 地支 unused — those are the void (空亡) branches.

Returns the raw two-character void-pair string from the lunar-python library
for each of the Four Pillars (年柱, 月柱, 日柱, 时柱). Example: "戌亥".

Two void conditions are checked by check_pillar_void_status():
  空亡 Primary Void  — Day pillar's pair voids 年柱, 月柱, 时柱.
  年日互换空亡 Mutual Void (Roots)     — Day pillar's pair voids 年柱 AND year pillar's pair voids 日柱 (both directions active).
  月日互换空亡 Mutual Void (Life Path) — Day pillar's pair voids 月柱 AND month pillar's pair voids 日柱 (both directions active).
  日时互换空亡 Mutual Void (Legacy)    — Day pillar's pair voids 时柱 AND hour pillar's pair voids 日柱 (both directions active).
"""


_VOID_INTERPRETATIONS: dict[tuple[str, str], str] = {
    ("年柱", "空亡"): "年柱落于空亡。祖基薄弱，早年与父母缘分较淡，先天福泽不足。",
    ("月柱", "空亡"): "月柱落于空亡。事业根基不稳，兄弟姊妹情缘疏离，中年发展易逢瓶颈。",
    ("时柱", "空亡"): "时柱落于空亡。与子女缘薄，晚年少人扶持，个人志向难以完全实现。",
    ("年柱", "年日互换空亡"): "年柱与日柱互换空亡。根不养花——祖荫与自身命格互相落空，先天根基无法滋养日元。",
    ("日柱", "年日互换空亡"): "日柱与年柱互换空亡。根不养花——自身缺乏祖荫庇护，性格趋向离散与精神追求，漂泊不定，六亲缘薄。",
    ("月柱", "月日互换空亡"): "月柱与日柱互换空亡。路不载人——事业格局与自身命格互相落空，中年发展之路易逢阻断。",
    ("日柱", "月日互换空亡"): "日柱与月柱互换空亡。路不载人——自身与事业格局互相落空，兄弟姊妹缘薄，中年发展之路易逢转折与飘零。",
    ("日柱", "日时互换空亡"): "日柱与时柱互换空亡。花不结果——自身命格与子嗣宫互相落空，晚年根基无力延续。",
    ("时柱", "日时互换空亡"): "日柱与时柱互换空亡。花不结果——与子女及后辈缘薄，晚年积累易耗散，志业难以传承。",
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

    空亡 Primary Void          — Day pillar's xun kong pair voids 年柱, 月柱, 时柱.
    年日互换空亡 Mutual Void (Roots)     — Both conditions must hold simultaneously:
                                           1. Day pillar's void pair voids 年柱.
                                           2. Year pillar's void pair voids 日柱.
    月日互换空亡 Mutual Void (Life Path)  — Both conditions must hold simultaneously:
                                           1. Day pillar's void pair voids 月柱.
                                           2. Month pillar's void pair voids 日柱.
    日时互换空亡 Mutual Void (Legacy)     — Both conditions must hold simultaneously:
                                           1. Day pillar's void pair voids 时柱.
                                           2. Hour pillar's void pair voids 日柱.

    Args:
        void_pairs: Result of get_void_xun_kong() — two-char void pair per pillar.
        pillars:    Result of get_bazi_pillars()  — contains 天干 and 地支 per pillar.

    Returns:
        dict keyed by 年柱, 月柱, 日柱, 时柱. Each value contains:
          "空亡":        Descriptive Chinese string when void applies; "无" otherwise.
          "年日互换空亡": Descriptive Chinese string when void applies; "无" otherwise.
          "月日互换空亡": Descriptive Chinese string when void applies; "无" otherwise.
          "日时互换空亡": Descriptive Chinese string when void applies; "无" otherwise.
    """
    day_void   = void_pairs["日柱"]
    year_void  = void_pairs["年柱"]
    month_void = void_pairs["月柱"]
    time_void  = void_pairs["时柱"]

    def branch(key: str) -> str:
        return pillars[key]["地支"]

    def _void_value(condition: bool, pillar: str, void_type: str) -> str:
        """Return descriptive string when condition met, else '无'."""
        if not condition:
            return "无"
        return _VOID_INTERPRETATIONS.get((pillar, void_type), "无")

    def _mutual(condition: bool, pillar: str, void_type: str) -> dict:
        """Return {void_type: interpretation} only when the condition is active."""
        val = _void_value(condition, pillar, void_type)
        return {void_type: val} if val != "无" else {}

    # 年日互换空亡: day voids year AND year voids day
    year_day_mutual  = (branch("年柱") in day_void) and (branch("日柱") in year_void)
    # 月日互换空亡: day voids month AND month voids day
    month_day_mutual = (branch("月柱") in day_void) and (branch("日柱") in month_void)
    # 日时互换空亡: day voids hour AND hour voids day
    day_time_mutual  = (branch("时柱") in day_void) and (branch("日柱") in time_void)

    return {
        "年柱": {
            "空亡": _void_value(branch("年柱") in day_void, "年柱", "空亡"),
            **_mutual(year_day_mutual, "年柱", "年日互换空亡"),
        },
        "月柱": {
            "空亡": _void_value(branch("月柱") in day_void, "月柱", "空亡"),
            **_mutual(month_day_mutual, "月柱", "月日互换空亡"),
        },
        "日柱": {
            "空亡": "无",
            **_mutual(year_day_mutual,  "日柱", "年日互换空亡"),
            **_mutual(month_day_mutual, "日柱", "月日互换空亡"),
            **_mutual(day_time_mutual,  "日柱", "日时互换空亡"),
        },
        "时柱": {
            "空亡": _void_value(branch("时柱") in day_void, "时柱", "空亡"),
            **_mutual(day_time_mutual, "时柱", "日时互换空亡"),
        },
    }
