"""
五行 (Wu Xing) — Five Elements

Calculates the distribution and strength of the five elements (wood, fire, earth, metal, water)
from the four pillars (stems and branches). Determines lucky and unlucky elements based on
which elements are deficient.
"""

from typing import Dict, Any


# Element mappings for stems (Heavenly Stems / 天干)
STEM_ELEMENT_MAP = {
    "甲": "木",  # Wood
    "乙": "木",  # Wood
    "丙": "火",  # Fire
    "丁": "火",  # Fire
    "戊": "土",  # Earth
    "己": "土",  # Earth
    "庚": "金",  # Metal
    "辛": "金",  # Metal
    "壬": "水",  # Water
    "癸": "水",  # Water
}

# Element mappings for branches (Earthly Branches / 地支)
BRANCH_ELEMENT_MAP = {
    "子": "水",  # Water
    "丑": "土",  # Earth
    "寅": "木",  # Wood
    "卯": "木",  # Wood
    "辰": "土",  # Earth
    "巳": "火",  # Fire
    "午": "火",  # Fire
    "未": "土",  # Earth
    "申": "金",  # Metal
    "酉": "金",  # Metal
    "戌": "土",  # Earth
    "亥": "水",  # Water
}

# Element order for display and lucky/unlucky logic
ELEMENT_ORDER = ["木", "火", "土", "金", "水"]
ELEMENT_NAMES = {
    "木": "Wood",
    "火": "Fire",
    "土": "Earth",
    "金": "Metal",
    "水": "Water",
}


def get_wu_xing(si_zhu: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate five elements distribution and lucky/unlucky elements from the four pillars.

    Args:
        si_zhu: Dict with keys 年柱, 月柱, 日柱, 时柱. Each contains:
                - 天干: heavenly stem (e.g., "甲")
                - 地支: earthly branch (e.g., "子")

    Returns:
        Dict with:
        - counts: {木, 火, 土, 金, 水} — element counts (0-8)
        - lucky_elements: list of 1-2 elements to strengthen
        - unlucky_elements: list of 1-2 elements to avoid
        - element_names: English names for display
    """
    # Initialize counts
    counts = {element: 0 for element in ELEMENT_ORDER}

    # Pillar keys in order
    pillar_keys = ["年柱", "月柱", "日柱", "时柱"]

    # Count stems and branches
    for key in pillar_keys:
        pillar = si_zhu.get(key, {})

        # Heavenly stem
        stem = pillar.get("天干", "")
        if stem in STEM_ELEMENT_MAP:
            element = STEM_ELEMENT_MAP[stem]
            counts[element] += 1

        # Earthly branch
        branch = pillar.get("地支", "")
        if branch in BRANCH_ELEMENT_MAP:
            element = BRANCH_ELEMENT_MAP[branch]
            counts[element] += 1

    # Determine lucky and unlucky elements
    # Lucky elements are the two most deficient (lowest counts)
    # Unlucky elements are the two most abundant (highest counts)
    sorted_by_count = sorted(counts.items(), key=lambda x: x[1])
    lucky_elements = [elem for elem, _ in sorted_by_count[:2]]
    unlucky_elements = [elem for elem, _ in sorted_by_count[-2:]]

    # Remove duplicates and keep only valid elements
    lucky_elements = list(dict.fromkeys(lucky_elements))
    unlucky_elements = list(dict.fromkeys(unlucky_elements))

    return {
        "counts": {element: counts[element] for element in ELEMENT_ORDER},
        "lucky_elements": lucky_elements,
        "unlucky_elements": unlucky_elements,
        "element_names": ELEMENT_NAMES,
    }
