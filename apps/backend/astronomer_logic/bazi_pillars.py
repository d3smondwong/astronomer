"""
四柱 BaZi Pillars — Four Pillars Extraction

Extracts the Four Pillars (年柱, 月柱, 日柱, 时柱) from an EightChar (八字) object.
Each pillar contains:
  - 天干 — Heavenly Stem
  - 地支 — Earthly Branch
  - 本气 — Primary hidden stem (first, always present)
  - 中气 — Middle hidden stem (second, or "无" if absent)
  - 余气 — Residual hidden stem (third, or "无" if absent)
"""


def _hidden_stems(hide_gan: list) -> tuple:
    """Unpack up to 3 hidden stems from the library list, padding with "无"."""
    stems = list(hide_gan) + ["无", "无", "无"]
    return (stems[0] if stems[0] else "无",
            stems[1] if stems[1] else "无",
            stems[2] if stems[2] else "无")


def get_bazi_pillars(bazi) -> dict:
    """
    Extract the Four Pillars from an EightChar object.

    Args:
        bazi: EightChar object from lunar_birthday.getEightChar()

    Returns:
        dict keyed by 年柱, 月柱, 日柱, 时柱.
        Each pillar contains: 天干, 地支, 本气, 中气, 余气.
    """
    def make_pillar(stem_fn, branch_fn, hide_fn) -> dict:
        primary_qi_stem, middle_qi_stem, residual_qi_stem = _hidden_stems(hide_fn())
        return {
            "天干": stem_fn(),
            "地支": branch_fn(),
            "藏干": {
                "本气": primary_qi_stem,
                "中气": middle_qi_stem,
                "余气": residual_qi_stem,
            },
        }

    return {
        "年柱": make_pillar(bazi.getYearGan,  bazi.getYearZhi,  bazi.getYearHideGan),
        "月柱": make_pillar(bazi.getMonthGan, bazi.getMonthZhi, bazi.getMonthHideGan),
        "日柱": make_pillar(bazi.getDayGan,   bazi.getDayZhi,   bazi.getDayHideGan),
        "时柱": make_pillar(bazi.getTimeGan,  bazi.getTimeZhi,  bazi.getTimeHideGan),
    }
