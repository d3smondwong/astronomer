from src.astronomer_calculations.shen_sha import (
    stem_partners,
    bath_position,
    seasons_map,
    year_earthly_branches_shens,
    month_earthly_branches_shens,
    day_earthly_branches_shens,
    day_heavenly_stem_shens,
    pillar_shens,
    SELF_EXCLUSION_STARS,
)

# ============================================================================
# SHEN SHA (SPIRITUAL STARS) FOR CYCLES
# ============================================================================

def get_cycle_shen_sha(cycle_stem, cycle_branch, natal_chart):
    """
    Extract Shen Sha (神煞) stars for a single cycle stem-branch pair.
    Designed to be reusable for Da Yun, Xiao Yun, Liu Nian cycles.

    Args:
        cycle_stem (str): The stem of the cycle (e.g., "甲")
        cycle_branch (str): The branch of the cycle (e.g., "寅")
        natal_chart (dict): Natal chart with structure:
            {
                "year": {"stem": str, "branch": str},
                "month": {"stem": str, "branch": str},
                "day": {"stem": str, "branch": str},
                "hour": {"stem": str, "branch": str},
            }

    Returns:
        dict: Categorized shen_sha stars with keys "日系", "年系", "月系", "杂项"
    """
    shen_sha_list = []
    year_shens = set()  # Year branch based
    month_shens = set()  # Month branch based
    day_shens = set()  # Day branch + day stem based
    misc_shens = set()  # Pillar/seasonal/void

    def add_shen(shen_name):
        "Helper to add unique shen (uncategorized fallback)"
        if shen_name not in shen_sha_list:
            shen_sha_list.append(shen_name)

    def add_year_shen(shen_name):
        "Helper to add shen from year branch origin (年系神煞)"
        if shen_name not in shen_sha_list:
            shen_sha_list.append(shen_name)
            year_shens.add(shen_name)

    def add_month_shen(shen_name):
        "Helper to add shen from month branch origin (月系神煞)"
        if shen_name not in shen_sha_list:
            shen_sha_list.append(shen_name)
            month_shens.add(shen_name)

    def add_day_shen(shen_name):
        "Helper to add shen from day branch/stem origin (日系神煞)"
        if shen_name not in shen_sha_list:
            shen_sha_list.append(shen_name)
            day_shens.add(shen_name)

    def add_misc_shen(shen_name):
        "Helper to add shen from pillar/seasonal/void (杂项)"
        if shen_name not in shen_sha_list:
            shen_sha_list.append(shen_name)
            misc_shens.add(shen_name)

    # Extract components from natal_chart
    day_stem = natal_chart["day"]["stem"]
    day_branch = natal_chart["day"]["branch"]
    month_branch = natal_chart["month"]["branch"]
    year_branch = natal_chart["year"]["branch"]
    day_pillar = day_stem + day_branch

    # Compute season for seasonal checks (四废, 天赦, 童子煞)
    birth_season = seasons_map.get(month_branch)

    # ========================================================================
    # 1. YEAR BRANCH LOOKUPS (if year_branch provided) → 年系
    # ========================================================================
    if year_branch:
        for shen_name, mapping in year_earthly_branches_shens.items():
            lookup = mapping.get(year_branch, "")
            if cycle_branch in lookup:
                if shen_name == "桃花":
                    add_year_shen("桃花")
                else:
                    add_year_shen(shen_name)

    # ========================================================================
    # 2. MONTH BRANCH LOOKUPS - Virtue Stars (anchored to month_branch) → 月系
    # ========================================================================
    for shen_name, mapping in month_earthly_branches_shens.items():
        if shen_name == "天赦":
            continue

        lookup = mapping.get(month_branch, "")
        if isinstance(lookup, str):
            if shen_name in ["天医", "血刃"]:
                # These are strictly Earthly Branch interactions
                if cycle_branch in lookup:
                    add_month_shen(shen_name)
            else:
                # For virtue stars, lookup returns stem(s), so check if cycle_stem matches
                if cycle_stem in lookup:
                    add_month_shen(shen_name)

    # --- Virtue Unions (天德合, 月德合) → 月系 ---
    tian_de_stem = month_earthly_branches_shens["天德"].get(month_branch)
    if tian_de_stem:
        partner_stem = stem_partners.get(tian_de_stem)
        if partner_stem and cycle_stem == partner_stem:
            add_month_shen("天德合")

    yue_de_stem = month_earthly_branches_shens["月德"].get(month_branch)
    if yue_de_stem:
        partner_stem = stem_partners.get(yue_de_stem)
        if partner_stem and cycle_stem == partner_stem:
            add_month_shen("月德合")

    # --- Combined Virtue Union (天月德合) → 月系 ---
    if tian_de_stem and yue_de_stem:
        tian_partner = stem_partners.get(tian_de_stem)
        yue_partner = stem_partners.get(yue_de_stem)
        if (
            tian_partner
            and yue_partner
            and tian_partner == yue_partner
            and cycle_stem == tian_partner
        ):
            add_month_shen("天月德合")

    # ========================================================================
    # 3. DAY BRANCH LOOKUPS - Movement Stars (anchored to natal day_branch) → 日系
    # ========================================================================
    # These stars (驿马, 桃花, 劫煞, etc.) are derived from the natal day branch.
    # We check if the incoming cycle branch is a trigger for those stars.
    for shen_name, mapping in day_earthly_branches_shens.items():
        lookup = mapping.get(day_branch, "")  # Use NATAL day_branch as anchor
        if lookup and cycle_branch in lookup:
            if shen_name == "桃花":
                add_day_shen("桃花")
            else:
                add_day_shen(shen_name)

    # --- Peach Blossom "Bath" Activation (沐浴桃花) → 日系 ---
    # Use Day Master (Stem) to find its specific "Bath" (沐浴) stage
    my_bath_branch = bath_position.get(day_stem)
    if "桃花" in shen_sha_list and cycle_branch == my_bath_branch:
        add_day_shen("沐浴桃花")

    # ========================================================================
    # 4. STEM-BASED LOOKUPS - Personal Stars (anchored to natal day_stem) → 日系
    # ========================================================================
    # These stars define what the NATIVE person is like.
    # We check if the incoming cycle brings the target branch(es) for that native stem.
    for shen_name, mapping in day_heavenly_stem_shens.items():
        lookup = mapping.get(day_stem, "")  # Use NATAL day_stem as anchor
        if not lookup:
            continue

        if shen_name == "词馆":
            # 词馆: Can match full pillar or single branch
            for entry in lookup:
                if len(entry) == 2:  # Full pillar check
                    if (cycle_stem + cycle_branch) == entry:
                        add_day_shen(shen_name)
                else:  # Single branch check
                    if cycle_branch == entry:
                        add_day_shen(shen_name)
        else:
            # For other stem-based stars: check if cycle_branch is in the mapped branches
            if cycle_branch in lookup:
                add_day_shen(shen_name)

    # --- Yin Blade (阴刃) → 日系 ---
    yin_blade_data = day_heavenly_stem_shens.get("阴刃", {}).get(day_stem, "")
    if yin_blade_data and cycle_branch in yin_blade_data:
        add_day_shen("阴刃")

    # --- Yang Blade Pairing (阳刃伏藏) → 日系 ---
    # Day Master has a Yang Blade branch; if cycle stem is the partner and brings that branch
    yang_ren_branch = day_heavenly_stem_shens["阳刃"].get(day_stem, "")
    if yang_ren_branch:
        partner_stem = stem_partners.get(day_stem)
        if (
            partner_stem
            and cycle_stem == partner_stem
            and cycle_branch in yang_ren_branch
        ):
            add_day_shen("阳刃伏藏")

    # ========================================================================
    # 5. PILLAR CHECKS (for full pillar, check special formations) → 杂项
    # ========================================================================
    cycle_pillar = cycle_stem + cycle_branch

    # --- Void (Kong Wang) → 杂项 ---
    if day_pillar:
        void_branches = pillar_shens["空亡"].get(day_pillar, "")
        if cycle_branch in void_branches:
            add_day_shen("空亡")

    # --- Day Pillar Specials (Natal-specific, not cyclic + cycle-applicable) → 杂项 ---
    day_checks = {
        "阴阳差错": pillar_shens.get("阴阳差错", []),
        "十恶大败": pillar_shens.get("十恶大败", []),
        "魁罡": pillar_shens.get("魁罡", []),
        "扩展魁罡": pillar_shens.get("扩展魁罡", []),
        "十灵": pillar_shens.get("十灵", []),
    }

    for shen_name, target_list in day_checks.items():
        if cycle_pillar in target_list:
            add_day_shen(shen_name)

    # --- Seasonal Day Pillar Check (四废 - Four Wastes) → 杂项 ---
    if birth_season and cycle_pillar in pillar_shens["四废"].get(birth_season, []):
        add_misc_shen("四废")

    # --- Child Sha (童子煞) - Seasonal → 杂项 ---
    if birth_season in ["夏", "冬"]:
        if cycle_branch in "卯辰未":
            add_misc_shen("童子煞")

    # ========================================================================
    # 6. HEAVENLY PARDON (天赦) – full pillar check based on natal month → 月系
    # ========================================================================
    if birth_season:
        pardon_pillar = month_earthly_branches_shens.get("天赦", {}).get(birth_season)
        if pardon_pillar and (cycle_stem + cycle_branch) == pardon_pillar:
            add_month_shen("天赦")

    # Categorize results into 4 categories
    return {
        "日系": [s for s in shen_sha_list if s in day_shens],
        "年系": [s for s in shen_sha_list if s in year_shens],
        "月系": [s for s in shen_sha_list if s in month_shens],
        "杂项": [s for s in shen_sha_list if s in misc_shens],
    }