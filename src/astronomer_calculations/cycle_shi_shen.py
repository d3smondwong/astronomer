from lunar_python.util import LunarUtil

def get_shi_shen_for_stem_pair(natal_day_stem: str, cycle_stem: str) -> str:
    """
    Calculate Ten God (十神) for a Stem pair (Day Stem vs Target Stem).

    Args:
        natal_day_stem (str): Natal Day Stem (日干) - the reference point
        target_stem (str): Target Stem to compare against

    Returns:
        str: The Ten God name (e.g., "正财", "七杀")
    """
    stem_pair = natal_day_stem + cycle_stem
    return LunarUtil.SHI_SHEN.get(stem_pair, "Unknown")


def get_hidden_stems_shi_shen(natal_day_stem: str, cycle_branch: str) -> dict:
    """
    Calculate Ten Gods for all hidden stems in an Earthly Branch.

    Args:
        natal_day_stem (str): Natal Day Stem (日干) - the reference point
        cycle_branch (str): Cycle Earthly Branch (地支)

    Returns:
        dict: Organized hidden stem Ten Gods with detailed structure
        {
            "本气": {
                "天干": "甲",      # Main Qi Stem
                "十神": "七杀"     # Main Qi Ten God
            },
            "中气": {...},  # Middle Qi (if exists)
            "余气": {...}   # Residual Qi (if exists)
        }
    """
    hidden_stems = LunarUtil.ZHI_HIDE_GAN.get(cycle_branch, [])
    labels = ["本气", "中气", "余气"]
    result = {}

    for i, hidden_stem in enumerate(hidden_stems):
        if i < len(labels):
            shi_shen = get_shi_shen_for_stem_pair(natal_day_stem, hidden_stem)
            result[labels[i]] = {"天干": hidden_stem, "十神": shi_shen}

    return result