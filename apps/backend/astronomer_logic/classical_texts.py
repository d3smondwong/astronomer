"""
古籍注解 Classical Text Lookups

Provides lookup functions for three classical BaZi texts.
Each function accepts the pillars dict (output of get_bazi_pillars)
and returns a Chinese prose string or None if no match exists.

Sources:
  - 六十日用法口诀 (sixty_days_classification)  — Day Pillar pair
  - 穷通宝鉴       (qiong_tong_bao_jian)       — Day Stem + Month Branch
  - 三命通会       (san_ming_tong_hui)          — Day Stem + Hour Pillar pair
"""

import apps.backend.data.sixty_days_classification as sixty_days
import apps.backend.data.qiong_tong_bao_jian as qtbj
import apps.backend.data.san_ming_tong_hui as smth


def get_classical_texts(pillars: dict) -> dict:
    """
    Return classical text commentary keyed under 古籍注解.

    Args:
        pillars: dict from get_bazi_pillars(), keyed by 年柱/月柱/日柱/时柱.
                 Each pillar has 天干 and 地支 sub-keys.

    Returns:
        dict with a single key 古籍注解 containing three classical text values.
        Each value is a Chinese prose string, or None if no match in the source dict.
    """
    day_stem     = pillars["日柱"]["天干"]
    day_branch   = pillars["日柱"]["地支"]
    month_branch = pillars["月柱"]["地支"]
    hour_stem    = pillars["时柱"]["天干"]
    hour_branch  = pillars["时柱"]["地支"]

    return {
        "古籍注解": {
            "六十日用法": sixty_days.get(day_stem + day_branch),
            "穷通宝鉴":   qtbj.get(day_stem + month_branch),
            "三命通会":   smth.get(day_stem + "日" + hour_stem + hour_branch),
        }
    }
