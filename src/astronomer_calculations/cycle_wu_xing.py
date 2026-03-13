from lunar_python.util import LunarUtil

def get_stem_wu_xing(cycle_stem: str) -> dict:
    """
    Get Five Element (五行) info for a Heavenly Stem (天干).

    Uses lunar_python library data which maps stems to elements.
    Polarity (阳/阴) is derived from the stem's index position:
    - Odd indices (甲丙戊庚壬) = 阳 (Yang)
    - Even indices (乙丁己辛癸) = 阴 (Yin)

    Args:
        cycle_stem (str): Heavenly Stem (e.g., "甲", "乙", etc.)

    Returns:
        dict: {"五行": "木/火/土/金/水", "阴阳": "阳/阴"}
    """
    element = LunarUtil.WU_XING_GAN.get(cycle_stem, "Unknown")

    if element == "Unknown":
        return {"五行": "Unknown", "阴阳": "Unknown"}

    # Find index to determine polarity (odd=Yang, even=Yin)
    try:
        index = LunarUtil.GAN.index(cycle_stem)
        polarity = "阳" if index % 2 == 1 else "阴"
    except ValueError:
        polarity = "Unknown"

    return {"五行": element, "阴阳": polarity}


def get_branch_wu_xing(cycle_branch: str) -> dict:
    """
    Get Five Element (五行) info for an Earthly Branch (地支).

    Uses lunar_python library data which maps branches to elements.
    Polarity (阳/阴) is derived from the branch's index position:
    - Odd indices (子寅辰午申戌) = 阳 (Yang)
    - Even indices (丑卯巳未酉亥) = 阴 (Yin)

    Args:
        cycle_branch (str): Earthly Branch (e.g., "子", "丑", etc.)

    Returns:
        dict: {"五行": "木/火/土/金/水", "阴阳": "阳/阴"}
    """
    element = LunarUtil.WU_XING_ZHI.get(cycle_branch, "Unknown")

    if element == "Unknown":
        return {"五行": "Unknown", "阴阳": "Unknown"}

    # Find index to determine polarity (odd=Yang, even=Yin)
    try:
        index = LunarUtil.ZHI.index(cycle_branch)
        polarity = "阳" if index % 2 == 1 else "阴"
    except ValueError:
        polarity = "Unknown"

    return {"五行": element, "阴阳": polarity}
