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

import copy

from lunar_python.util import LunarUtil

_YANG_STEMS = frozenset("甲丙戊庚壬")
_ELEMENT_YANG_STEM: dict[str, str] = {"木": "甲", "火": "丙", "土": "戊", "金": "庚", "水": "壬"}
_ELEMENT_YIN_STEM:  dict[str, str] = {"木": "乙", "火": "丁", "土": "己", "金": "辛", "水": "癸"}


def _ten_god_for_transformed(original_stem: str, transformed_element: str, dm_stem: str) -> str:
    """Ten god for a stem whose element has transformed to transformed_element, relative to dm_stem.

    Preserves the original stem's yin/yang polarity when selecting the effective stem.
    Uses LunarUtil.SHI_SHEN for the final lookup.
    """
    effective_stem = (
        _ELEMENT_YANG_STEM[transformed_element]
        if original_stem in _YANG_STEMS
        else _ELEMENT_YIN_STEM[transformed_element]
    )
    return LunarUtil.SHI_SHEN.get(dm_stem + effective_stem, "无")


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


def apply_he_hua_overrides(
    ten_gods: dict,
    si_zhu: dict,
    interactions_data: dict,
    day_master_stem: str,
) -> tuple[dict, dict]:
    """
    Returns (updated_ten_gods, updated_si_zhu) with 合化/化气格 ten god overrides applied.

    合化  — update 天干十神 for the two affected pillars only; 藏干十神 unchanged
            (DM and hidden stems are both unaffected, so their relationship is the same).
    化气格 — DM element changes; recalculate 天干十神 + 藏干十神 for ALL non-DM pillars.
    假化 / 合绊 / 遥合 — no change.
    """
    ten_gods = copy.deepcopy(ten_gods)
    si_zhu   = copy.deepcopy(si_zhu)

    for interaction in interactions_data["作用"]["柱位动态"]:
        if interaction.get("类型") != "天干合":
            continue
        形态 = interaction.get("形态")
        if 形态 not in ("合化", "化气格"):
            continue

        transformed_element = interaction["合化条件"]["合化元素"]

        if 形态 == "化气格":
            # DM transforms → derive the new effective DM stem (same polarity, new element)
            new_dm_stem = (
                _ELEMENT_YANG_STEM[transformed_element]
                if day_master_stem in _YANG_STEMS
                else _ELEMENT_YIN_STEM[transformed_element]
            )
            original_dm_element = LunarUtil.WU_XING_GAN.get(day_master_stem, "无")
            si_zhu["日柱"]["化气格信息"] = {"原五行": original_dm_element, "现五行": transformed_element}

            for pillar in ("年柱", "月柱", "日柱", "时柱"):
                orig_tg      = ten_gods[pillar]["天干十神"]
                orig_藏干十神 = dict(ten_gods[pillar]["藏干十神"])

                if pillar != "日柱":
                    stem = si_zhu[pillar]["天干"]
                    new_tg = LunarUtil.SHI_SHEN.get(new_dm_stem + stem, "无")
                    ten_gods[pillar]["天干十神"] = new_tg
                    si_zhu[pillar]["天干十神"]   = new_tg

                for tier in ("本气", "中气", "余气"):
                    hidden_stem = si_zhu[pillar]["藏干"].get(tier, "无")
                    if hidden_stem and hidden_stem != "无":
                        hs_tg = LunarUtil.SHI_SHEN.get(new_dm_stem + hidden_stem, "无")
                        ten_gods[pillar]["藏干十神"][f"{tier}十神"] = hs_tg
                        si_zhu[pillar]["藏干十神"][f"{tier}十神"]   = hs_tg

                if orig_tg != ten_gods[pillar]["天干十神"] or orig_藏干十神 != ten_gods[pillar]["藏干十神"]:
                    si_zhu[pillar]["化气格变化"] = {
                        "原天干十神": orig_tg,
                        "原藏干十神": orig_藏干十神,
                    }

        else:
            # 合化 (non-DM) → update 天干十神 for affected pillars only
            orig_ten_gods: dict[str, str] = {}
            for pillar, stem in interaction["组合明细"].items():
                if pillar == "日柱":
                    continue
                orig_ten_gods[pillar] = ten_gods[pillar]["天干十神"]
                new_tg = _ten_god_for_transformed(stem, transformed_element, day_master_stem)
                ten_gods[pillar]["天干十神"] = new_tg
                si_zhu[pillar]["天干十神"]   = new_tg
                # 藏干十神 unchanged — DM and hidden stems are unaffected

            for pillar in interaction["组合明细"]:
                si_zhu[pillar]["合化信息"] = {
                    "类型": 形态,
                    "合化元素": transformed_element,
                    "参与柱位": list(interaction["组合明细"].keys()),
                    "原天干十神": orig_ten_gods.get(pillar, ""),
                }

    return ten_gods, si_zhu
