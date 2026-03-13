from lunar_python.util import LunarUtil
def get_nayin(stem: str, branch: str) -> str:
    """
    Get Nayin Element (纳音) for a Stem-Branch pair.

    Nayin (纳音) represents the harmonic resonance element associated with each
    of the 60 sexagenary stem-branch combinations. It's a classical BaZi concept
    from the lunar-python library's LunarUtil.NAYIN mapping.

    Args:
        stem (str): Heavenly Stem (e.g., "甲", "乙", etc.)
        branch (str): Earthly Branch (e.g., "子", "丑", etc.)

    Returns:
        str: Nayin descriptive name (e.g., "海中金", "炉中火") or "Unknown"
    """
    gan_zhi = stem + branch
    return LunarUtil.NAYIN.get(gan_zhi, "Unknown")
