"""
八字 cache key — a deterministic, content-addressed id for a BaZi chart.

The four pillars (年月日时) plus gender fully determine the natal chart and its
interpretation, so two people with the same 八字 + gender share one cached chart and
one set of insights — regardless of how precisely their birthplace was picked (the
pillars are computed after True Solar Time, so coordinate noise and the TST flag are
already absorbed).

The key encodes the eight GanZhi as ASCII letters (2 per pillar, in 年月日时 order) with
gender appended — Firestore-doc-id / URL safe, and decodable by eye since case
distinguishes stem from branch:

    stems  甲乙丙丁戊己庚辛壬癸 → a b c d e f g h i j   (lowercase)
    branch 子丑寅卯辰巳午未申酉戌亥 → A B C D E F G H I J K L (uppercase)

    乙丑 丁亥 壬午 己酉  (male)  →  "bBdLiGfJ" + "M"  →  "bBdLiGfJM"
"""

# 天干 (heavenly stems) → lowercase a–j, in the standard 10-stem cycle order.
_STEM_LETTERS = {
    "甲": "a", "乙": "b", "丙": "c", "丁": "d", "戊": "e",
    "己": "f", "庚": "g", "辛": "h", "壬": "i", "癸": "j",
}

# 地支 (earthly branches) → uppercase A–L, in the standard 12-branch cycle order.
_BRANCH_LETTERS = {
    "子": "A", "丑": "B", "寅": "C", "卯": "D", "辰": "E", "巳": "F",
    "午": "G", "未": "H", "申": "I", "酉": "J", "戌": "K", "亥": "L",
}


def encode_bazi_key(bazi, gender: int) -> str:
    """Encode an EightChar (八字) + gender into the cache key.

    Args:
        bazi:   EightChar object from ``lunar_birthday.getEightChar()``.
        gender: 1 = male, 0 = female.

    Returns:
        9-char ASCII key: 8 GanZhi letters (年月日时, stem+branch per pillar) + 'M'/'F'.

    Raises:
        ValueError: if a stem/branch isn't recognised (guards against an unexpected
                    library output rather than silently producing a wrong key).
    """
    stems = [bazi.getYearGan(), bazi.getMonthGan(), bazi.getDayGan(), bazi.getTimeGan()]
    branches = [bazi.getYearZhi(), bazi.getMonthZhi(), bazi.getDayZhi(), bazi.getTimeZhi()]

    chars: list[str] = []
    for stem, branch in zip(stems, branches):
        try:
            chars.append(_STEM_LETTERS[stem])
            chars.append(_BRANCH_LETTERS[branch])
        except KeyError as e:
            raise ValueError(f"Unrecognised GanZhi component in 八字: {e}") from e

    chars.append("M" if gender == 1 else "F")
    return "".join(chars)
