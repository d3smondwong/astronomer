"""
古籍文献 Classical Text Lookups (Orchestrator)

Orchestrates lookups for three classical BaZi texts from Ming Dynasty sources.
Returns structured interpretations keyed under 古籍文献.

Sources:
  - 三命通会_日时断 (san_ming_tong_hui_day_hour)  — Day & Hour Pillar combination (720 interpretations)
  - 穷通宝鉴       (qiong_tong_bao_jian)         — Day Stem + Month Branch (seasonal fortune)
  - 六十日用法     (sixty_days_classification)   — Day Pillar pair (day character)
"""

import apps.backend.data.sixty_days_classification as sixty_days
import apps.backend.data.qiong_tong_bao_jian as qtbj
from apps.backend.data.san_ming_tong_hui_v89_day_hour_pillar import (
    san_ming_tong_hui_day_hour_pillar_interpretation as _SMTH,
)
from apps.backend.data.san_ming_tong_hui_v1 import volume_1_60_jia_zi_nature_pillar as _V1_NATURE

# Flatten list-of-single-key-dicts → {"甲子": "...", "乙丑": "...", ...} for O(1) lookup
_JIAZI_NATURE: dict[str, str] = {k: v for entry in _V1_NATURE for k, v in entry.items()}


def _extract_san_ming_tong_hui_day_hour(day_pillar: dict, hour_pillar: dict) -> dict:
    """
    Extract San Ming Tong Hui commentary for Day Stem × Hour Pillar combination.

    The hour pillar governs later life, children's fate, and innermost motivations.
    Lookup uses nested dict structure: day_stem → hour_stem+hour_branch+时 → day_stem+day_branch+日.

    Args:
        day_pillar:  Raw pillar dict with 天干 and 地支 keys
        hour_pillar: Raw pillar dict with 天干 and 地支 keys

    Returns:
        Structured dict with 日柱, 时柱, 时柱解读 (诗句/解释/总结诗词), and 日柱解读.
        Returns gracefully with None values if no matching entry exists.
    """
    day_stem    = day_pillar["天干"]
    day_branch  = day_pillar["地支"]
    hour_stem   = hour_pillar["天干"]
    hour_branch = hour_pillar["地支"]

    hour_key = f"{hour_stem}{hour_branch}时"
    day_key  = f"{day_stem}{day_branch}日"

    stem_entry = _SMTH.get(day_stem)
    hour_entry = stem_entry.get(hour_key) if stem_entry else None

    if hour_entry is None:
        return {
            "日柱": {"干支": f"{day_stem}{day_branch}"},
            "时柱": {"干支": f"{hour_stem}{hour_branch}"},
            "时柱解读": {"诗句": None, "解释": None, "总结诗词": []},
            "日柱解读": None,
        }

    return {
        "日柱": {"干支": f"{day_stem}{day_branch}"},
        "时柱": {"干支": f"{hour_stem}{hour_branch}"},
        "时柱解读": {
            "诗句":    hour_entry.get("诗句"),
            "解释":    hour_entry.get("解释"),
            "总结诗词": hour_entry.get("总结诗词", []),
        },
        "日柱解读": hour_entry.get("日柱", {}).get(day_key),
    }


def _extract_san_ming_tong_hui_pillar_nature(pillars: dict) -> dict:
    """
    Extract San Ming Tong Hui Vol.1 nature commentary for each of the four pillars.

    Looks up the 干支 combination of each pillar against the 60-jiazi nature table,
    which describes the innate character, elemental quality, and auspicious/inauspicious
    conditions for each ganzhi pair.

    Args:
        pillars: dict from get_bazi_pillars(), keyed by 年柱/月柱/日柱/时柱.

    Returns:
        dict keyed by pillar name, each containing:
          - 干支: the ganzhi string (e.g. "甲子")
          - 纳音性质: the classical nature text, or None if not found
    """
    result = {}
    for pillar_name in ("年柱", "月柱", "日柱", "时柱"):
        pillar = pillars[pillar_name]
        ganzhi = pillar["天干"] + pillar["地支"]
        result[pillar_name] = {
            "干支": ganzhi,
            "纳音性质": _JIAZI_NATURE.get(ganzhi),
        }
    return result


def get_classical_texts(pillars: dict) -> dict:
    """
    Orchestrate all classical text lookups and return an LLM-ready dict.

    Args:
        pillars: dict from get_bazi_pillars(), keyed by 年柱/月柱/日柱/时柱.

    Returns:
        dict with single key 古籍文献 containing three classical text entries:
          - 三命通会_日时断: Structured dict with day+hour interpretation
          - 穷通宝鉴: Raw string (or None if no match)
          - 六十日用法: Raw string (or None if no match)
    """
    day_pillar   = pillars["日柱"]
    hour_pillar  = pillars["时柱"]
    day_stem     = day_pillar["天干"]
    day_branch   = day_pillar["地支"]
    month_branch = pillars["月柱"]["地支"]

    return {
        "古籍文献": {
            "三命通会_日时断":   _extract_san_ming_tong_hui_day_hour(day_pillar, hour_pillar),
            "三命通会_纳音性质": _extract_san_ming_tong_hui_pillar_nature(pillars),
            # "穷通宝鉴":       qtbj.get(day_stem + month_branch),
            # "六十日用法":     sixty_days.get(day_stem + day_branch),
        }
    }
