"""
四柱 BaZi Pillars — Four Pillars Extraction

Extracts the Four Pillars (年柱, 月柱, 日柱, 时柱) from an EightChar (八字) object.
Each pillar contains:
  - 天干 — Heavenly Stem
  - 地支 — Earthly Branch
  - 本气 — Primary hidden stem (first, always present)
  - 中气 — Middle hidden stem (second, or "无" if absent)
  - 余气 — Residual hidden stem (third, or "无" if absent)

Also computes 根基 (stem rooting) for all four pillars.
"""
from lunar_python.util import LunarUtil

_ROOT_DEPTH_LABELS: list[str] = ["本气", "中气", "余气"]

_PILLAR_NAMES_CN = ["年柱", "月柱", "日柱", "时柱"]

_YANG_STEMS    = frozenset("甲丙戊庚壬")   # even-index stems in the 10-stem cycle
_YANG_BRANCHES = frozenset("子寅辰午申戌") # even-index branches in the 12-branch cycle


def _yin_yang(char: str, yang_set: frozenset) -> str:
    return "阳" if char in yang_set else "阴"


def _hidden_stems(hide_gan: list) -> tuple:
    """Unpack up to 3 hidden stems from the library list, padding with "无"."""
    stems = list(hide_gan) + ["无", "无", "无"]
    return (stems[0] if stems[0] else "无",
            stems[1] if stems[1] else "无",
            stems[2] if stems[2] else "无")


def compute_pillar_rooting(
    gans: list[str],
    zhis: list[str],
    hides: list[list[str]],
    pillar_cn: list[str] | None = None,
) -> dict:
    """
    Qualitative 根基 computation for any set of pillars.

    Tier determined by deepest root type found across all branches:
    本气 → 深根 | 中气 → 中根 | 余气 → 浅根 | none → 无根

    Args:
        gans:     stems in order
        zhis:     branches in order, parallel to gans (used in descriptions)
        hides:    hidden stem lists in order, parallel to gans
                  each entry is ordered [本气, 中气, 余气] as returned by bazi.getXxxHideGan()
        pillar_cn: pillar display names used as result keys
                   (default: ["年柱","月柱","日柱","时柱"]).
                   "柱" is stripped when building branch descriptions.

    Returns:
        {"年柱": {"根基强度": "中根", "通根于": "月支亥(中气)"}, ...}
    """
    if pillar_cn is None:
        pillar_cn = _PILLAR_NAMES_CN

    def _short(label: str) -> str:
        return label[:-1] if label.endswith("柱") else label

    result = {}
    for gan, col in zip(gans, pillar_cn):
        elem = LunarUtil.WU_XING_GAN.get(gan)
        best_idx = len(_ROOT_DEPTH_LABELS)  # sentinel: no match
        matches: list[str] = []

        for j, (zhi, hide) in enumerate(zip(zhis, hides)):
            for idx, hidden_stem in enumerate(hide):
                if not hidden_stem or hidden_stem == "无":
                    continue
                if LunarUtil.WU_XING_GAN.get(hidden_stem) == elem:
                    if idx < best_idx:
                        best_idx = idx
                    matches.append(f"{_short(pillar_cn[j])}支{zhi}({_ROOT_DEPTH_LABELS[idx]})")
                    break

        if best_idx == 0:
            strength = "深根"
        elif best_idx == 1:
            strength = "中根"
        elif best_idx == 2:
            strength = "浅根"
        else:
            strength = "无根"

        result[col] = {
            "根基强度": strength,
            "通根于": "、".join(matches) if matches else "无根浮干",
        }
    return result



def get_bazi_pillars(bazi) -> dict:
    """
    Extract the Four Pillars and stem rooting from an EightChar object.

    Args:
        bazi: EightChar object from lunar_birthday.getEightChar()

    Returns:
        dict keyed by 年柱, 月柱, 日柱, 时柱 (each with 天干, 地支, 藏干)
        plus a top-level "根基" key with per-pillar stem rooting.
    """
    gans  = [bazi.getYearGan(),  bazi.getMonthGan(), bazi.getDayGan(),  bazi.getTimeGan()]
    zhis  = [bazi.getYearZhi(),  bazi.getMonthZhi(), bazi.getDayZhi(),  bazi.getTimeZhi()]
    hides = [bazi.getYearHideGan(), bazi.getMonthHideGan(), bazi.getDayHideGan(), bazi.getTimeHideGan()]

    rooting = compute_pillar_rooting(gans, zhis, hides)

    pillars = {}
    for name, gan, zhi, hide in zip(_PILLAR_NAMES_CN, gans, zhis, hides):
        ben, zhong, yu = _hidden_stems(hide)
        pillars[name] = {
            "天干": gan,
            "天干阴阳": _yin_yang(gan, _YANG_STEMS),
            "根基强度": rooting[name]["根基强度"],
            "通根于": rooting[name]["通根于"],
            "地支": zhi,
            "地支阴阳": _yin_yang(zhi, _YANG_BRANCHES),
            "藏干": {
                tier: {"天干": stem, "阴阳": _yin_yang(stem, _YANG_STEMS)}
                for tier, stem in zip(("本气", "中气", "余气"), (ben, zhong, yu))
                if stem != "无"
            },
        }

    return pillars
