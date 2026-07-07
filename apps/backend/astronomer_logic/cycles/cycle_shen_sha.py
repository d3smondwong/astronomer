"""
岁运神煞 Cycle Pillar Shen Sha — single-pillar evaluation against natal anchors.

Evaluates which 神煞 a transiting (大运/流年) pillar activates. All lookup
tables are imported from natal_shen_sha.py (they are module-level constants —
natal files are untouched, so natal output stays byte-identical). The
evaluator itself is fresh: the natal ShenShaCalculator is hard-wired to loop
`for i in range(4)` over the four natal pillars and cannot take a fifth.

Output is a flat list of entries — no 年系/月系/日系/杂项 grouping. Each
entry's "来源" (年支/月支/日支/日干/年干/纳音/四柱/自柱/组合/节气/运柱干支 …)
already names the derivation mechanism; a coarser wrapper category added no
information beyond what "来源" carries, since every entry in this evaluator
is discovered via the same single guest pillar.

Entries carry {"名称", "来源"} (+"细节" where meaningful). The natal
interpretation texts in interpretation_shen_sha.py are positional prose
(keyed 年柱/月柱/日柱/时柱) and do NOT apply to a transiting pillar, so cycle
entries deliberately omit 解读 — the interpretation layer reads the star name
in cycle context instead.

Natal SELF_EXCLUSION rules are intentionally skipped: they prevent a star
from landing on the pillar that derives it, which is meaningless for a
transiting pillar (it is never its own anchor).
"""

from apps.backend.astronomer_logic.bazi_pillars import _YANG_STEMS
from apps.backend.astronomer_logic.cycles.cycle_pillars import NatalContext
from apps.backend.astronomer_logic.natal_interactions import clash_map
from apps.backend.astronomer_logic.natal_shen_sha import (
    GUA_JIAN_METAL_FULL,
    GUA_JIAN_METAL_TRIO,
    SIXTY_JIAZI,
    THREE_WONDERS_TRIOS,
    TIAN_HUO_FIRE_STEMS,
    TIAN_HUO_FIRE_TRINE,
    TIAN_HUO_WATER_BRANCHES,
    TIAN_HUO_WATER_STEMS,
    XUE_TANG_NAYIN_MAP,
    XUE_TANG_STEM_MAP,
    _JIAN_FENG_SHA_XUN,
    _PO_SHA_PAIRS,
    _TIAN_TU_SHA_DAY_HOUR,
    _ZI_YI_SHA_PAIRS,
    an_jin_de_sha_map,
    an_lu_map,
    branch_six_combinations,
    ci_guan_nayin_map,
    ci_guan_stem_map,
    day_stem_only_shens,
    day_year_earthly_branches_shens,
    dexiu_map,
    fei_lian_map,
    ge_jiao_sha_map_day_time,
    ge_jiao_sha_map_year_day,
    month_earthly_branches_shens,
    nayin_to_element,
    pillar_shens,
    seasons_map,
    stem_partners,
    year_day_heavenly_stem_shens,
    year_earthly_branches_shens,
    yuan_chen_map,
)

# 天干 / 地支 canonical order — used for 剑锋煞 旬首 index math.
_GAN_ORDER = "甲乙丙丁戊己庚辛壬癸"
_ZHI_ORDER = "子丑寅卯辰巳午未申酉戌亥"

# Pillar labels for 组合明细 (which pillars form a set); index-aligned with ctx.zhis/gans.
_PILLAR_LABELS = ("年柱", "月柱", "日柱", "时柱")


def _natal_pillars_with_branch(ctx: NatalContext, branch_set: set) -> list:
    """Natal pillar labels whose branch is in branch_set (for 组合明细)."""
    return [_PILLAR_LABELS[i] for i, z in enumerate(ctx.zhis) if z in branch_set]

# month_earthly_branches_shens entries keyed by SEASON (not month branch)
_SEASONAL_STAR_NAMES = ("天赦", "天转", "地转", "季节性退神")

# 自禄: the cycle pillar's own stem sits in 临官 on its own branch
_SELF_LU_PILLARS = frozenset({"甲寅", "乙卯", "庚申", "辛酉"})

# 童子煞 nayin rule: year-pillar nayin element → triggering branches
_NAYIN_TONG_ZI = {
    "金": {"午", "卯"},
    "木": {"午", "卯"},
    "水": {"酉", "戌"},
    "火": {"酉", "戌"},
    "土": {"辰", "巳"},
}


def _virtue_union(virtue_value: str, cycle_stem: str, cycle_branch: str) -> bool:
    """天德合/月德合: the cycle carries the combining PARTNER of the virtue's
    target — stem partner for a stem target, 六合 partner for a branch target."""
    if not virtue_value:
        return False
    partner_stem = stem_partners.get(virtue_value)
    if partner_stem:
        return cycle_stem == partner_stem
    partner_branch = branch_six_combinations.get(virtue_value)
    return bool(partner_branch) and cycle_branch == partner_branch


def get_cycle_shen_sha(cycle_stem: str, cycle_branch: str, ctx: NatalContext) -> list:
    """
    Evaluate the 神煞 activated by one cycle pillar.

    Args:
        cycle_stem/cycle_branch: the transiting pillar.
        ctx: NatalContext (raw natal stems/branches, gender, na_yin).

    Returns:
        [...] — flat list of entries {"名称": str, "来源": str}
        (+"细节" where meaningful).
    """
    year_branch, month_branch, day_branch = ctx.zhis[0], ctx.zhis[1], ctx.zhis[2]
    year_stem, day_stem = ctx.gans[0], ctx.day_stem
    cycle_pillar = cycle_stem + cycle_branch
    season = seasons_map.get(month_branch, "")

    entries: list = []
    seen: set[tuple] = set()

    def add(
        name: str,
        source: str,
        detail: str = "",
        zuhe: list | None = None,
    ) -> None:
        key = (name, source)
        if key in seen:
            return
        seen.add(key)
        entry: dict[str, object] = {"名称": name, "来源": source}
        if detail:
            entry["细节"] = detail
        if zuhe:
            entry["组合明细"] = zuhe
        entries.append(entry)

    # ── 年系 — natal year-branch anchored ────────────────────────────────
    for name, mapping in year_earthly_branches_shens.items():
        if name == "勾绞煞":
            continue  # D2: split into 勾煞/绞煞 by gender + yin/yang below (natal _calc_gou_jiao)
        if cycle_branch in mapping.get(year_branch, ""):
            add(name, "年支")

    # 元辰 — gender + year yin/yang dependent (阳年男/阴年女 → first target)
    is_yang_year = year_stem in _YANG_STEMS
    is_male = ctx.gender == 1
    yuan_chen_target = yuan_chen_map[year_branch][0 if is_yang_year == is_male else 1]
    if cycle_branch == yuan_chen_target:
        add("元辰", "年支")

    # 勾煞 / 绞煞 — 前三辰 + 六冲(后三辰), labels swapped by gender + year yin/yang
    #   (mirrors natal _calc_gou_jiao; natal never emits the merged name "勾绞煞").
    qian = year_earthly_branches_shens.get("勾绞煞", {}).get(year_branch, "")
    hou = clash_map.get(qian, "") if qian else ""
    if qian and hou:
        yang_male_or_yin_female = (is_male and is_yang_year) or (
            not is_male and not is_yang_year
        )
        gou_branch, jiao_branch = (
            (qian, hou) if yang_male_or_yin_female else (hou, qian)
        )
        if cycle_branch == gou_branch:
            add("勾煞", "年支")
        if cycle_branch == jiao_branch:
            add("绞煞", "年支")

    # day_year table doubles as a year-branch source (将星/华盖/驿马/桃花 by year)
    for name, mapping in day_year_earthly_branches_shens.items():
        if cycle_branch in mapping.get(year_branch, ""):
            add(name, "年支")

    # year_day stem table — year-stem sourced nobles
    for name, mapping in year_day_heavenly_stem_shens.items():
        if cycle_branch in mapping.get(year_stem, ""):
            add(name, "年干")

    # ── 月系 — natal month-branch anchored ───────────────────────────────
    for name, mapping in month_earthly_branches_shens.items():
        if name in _SEASONAL_STAR_NAMES:
            if season and cycle_pillar == mapping.get(season, ""):
                add(name, "月支")
            continue
        lookup = mapping.get(month_branch, "")
        if lookup and (cycle_stem in lookup or cycle_branch in lookup):
            add(name, "月支")

    # Virtue unions — the cycle carries the virtue target's combining partner
    tian_de_value = month_earthly_branches_shens["天德贵人"].get(month_branch, "")
    yue_de_value = month_earthly_branches_shens["月德贵人"].get(month_branch, "")
    if _virtue_union(tian_de_value, cycle_stem, cycle_branch):
        add("天德合", "月支")
    if _virtue_union(yue_de_value, cycle_stem, cycle_branch):
        add("月德合", "月支")
    if (
        tian_de_value in stem_partners
        and yue_de_value in stem_partners
        and stem_partners[tian_de_value] == stem_partners[yue_de_value]
        and cycle_stem == stem_partners[tian_de_value]
    ):
        add("天月德合", "月支")

    # 德秀贵人 — natal _calc_virtue_elegance requires BOTH 德 AND 秀 (conjunction).
    #   With the guest as a 5th stem: 德 = a 德-stem among natal (year/day/hour) ∪ guest;
    #   秀 = a 秀 pair complete across natal stems ∪ guest. Fire only if both hold and the
    #   guest participates (supplies the 德 stem or completes the 秀 pair).
    de_stems, xiu_pairs = dexiu_map.get(month_branch, ("", []))
    if de_stems or xiu_pairs:
        # natal 德-stems checked in year/day/hour (non-month), per natal
        natal_de_stems = {ctx.gans[i] for i in (0, 2, 3)}
        stems_with_guest = set(ctx.gans) | {cycle_stem}
        has_de = bool((natal_de_stems | {cycle_stem}) & set(de_stems))
        has_xiu = any(a in stems_with_guest and b in stems_with_guest for a, b in xiu_pairs)
        guest_is_de = cycle_stem in de_stems
        guest_completes_xiu = any(
            (cycle_stem == a and b in ctx.gans) or (cycle_stem == b and a in ctx.gans)
            for a, b in xiu_pairs
        )
        if has_de and has_xiu and (guest_is_de or guest_completes_xiu):
            add("德秀贵人", "月支", detail="德" if guest_is_de else "秀")

    # ── 日系 — natal day-branch / day-stem anchored ──────────────────────
    for name, mapping in day_year_earthly_branches_shens.items():
        if cycle_branch in mapping.get(day_branch, ""):
            add(name, "日支")

    for name, mapping in year_day_heavenly_stem_shens.items():
        if cycle_branch in mapping.get(day_stem, ""):
            add(name, "日干")

    for name, mapping in day_stem_only_shens.items():
        if cycle_branch in mapping.get(day_stem, ""):
            add(name, "日干")

    # 阳刃伏藏 — the day master's combining partner arrives carrying the blade branch
    blade = day_stem_only_shens["羊刃"].get(day_stem, "")
    if blade and cycle_stem == stem_partners.get(day_stem) and cycle_branch in blade:
        add("阳刃伏藏", "日干")

    # 暗禄 — 六合 partner of the day master's 禄神 branch
    if cycle_branch == an_lu_map.get(day_stem):
        add("暗禄", "日干")

    # X命自禄 — the cycle pillar itself sits on its own 禄. Natal _calc_self_lu emits
    #   branch-specific names 寅/卯/申/酉命自禄 with source 自柱.
    if cycle_pillar in _SELF_LU_PILLARS:
        add(f"{cycle_branch}命自禄", "自柱")

    # ── 杂项 — whole-pillar formations & chart-conditioned traps ─────────
    for name, targets in pillar_shens.items():
        if name == "四废":
            continue
        if cycle_pillar in targets:
            add(name, "运柱干支")

    if season and cycle_pillar in pillar_shens["四废"].get(season, []):
        add("四废", "运柱干支")

    # 童子煞 — seasonal rule (natal _calc_tong_zi_sha): season → target branch set.
    if season in ("春", "秋"):
        tong_zi_targets = {"寅", "子"}
    elif season in ("夏", "冬"):
        tong_zi_targets = {"卯", "未", "辰"}
    else:
        tong_zi_targets = set()
    if cycle_branch in tong_zi_targets:
        add("童子煞", "节气")
    # 童子煞 — nayin rule (year-pillar nayin element)
    year_nayin_elem = nayin_to_element(ctx.na_yin.get("年柱", ""))
    if cycle_branch in _NAYIN_TONG_ZI.get(year_nayin_elem, set()):
        add("童子煞", "纳音")

    # 天罗 / 地网 — branch-pair completion (natal _calc_tian_luo_di_wang): independent,
    #   can coexist; the nayin restriction is an interpretation concern, not derivation.
    natal_branches = set(ctx.zhis)
    for _name, _pair in (("天罗", {"戌", "亥"}), ("地网", {"辰", "巳"})):
        if cycle_branch in _pair and (_pair - {cycle_branch}) <= natal_branches:
            _subtype = "增力" if _pair <= natal_branches else "引动成局"
            add(_name, "四柱", detail=_subtype,
                zuhe=["运柱"] + _natal_pillars_with_branch(ctx, _pair))

    # ════════════════════════════════════════════════════════════════════════
    # Phase 1 — single-anchor stars (guest lands on a natal-derived target)
    # ════════════════════════════════════════════════════════════════════════
    natal_stems = set(ctx.gans)
    hour_branch = ctx.zhis[3]

    # 吟呻 / 破碎 / 白衣 (暗金的煞) — year branch → (target branch, name)
    _aj = an_jin_de_sha_map.get(year_branch)
    if _aj and cycle_branch == _aj[0]:
        add(_aj[1], "年支")

    # 飞廉 — year branch → target branch
    if cycle_branch == fei_lian_map.get(year_branch):
        add("飞廉", "年支")

    # 剑锋煞 — year pillar 旬首 → (剑枝, 锋枝)
    _xun_shou = _ZHI_ORDER[
        (_ZHI_ORDER.index(year_branch) - _GAN_ORDER.index(year_stem)) % 12
    ]
    _jf = _JIAN_FENG_SHA_XUN.get(_xun_shou)
    if _jf and cycle_branch in _jf:
        add("剑锋煞", "年支")

    # 真词馆 — day / year STEM → exact target 干支
    if cycle_pillar == ci_guan_stem_map.get(day_stem):
        add("真词馆", "日干")
    if cycle_pillar == ci_guan_stem_map.get(year_stem):
        add("真词馆", "年干")

    # 正词馆 — year-nayin element → exact target 干支
    if cycle_pillar == ci_guan_nayin_map.get(year_nayin_elem):
        add("正词馆", "纳音")

    # 学堂 — year-nayin → branch (年纳音); day-stem → branch (日干)
    if cycle_branch == XUE_TANG_NAYIN_MAP.get(year_nayin_elem):
        add("学堂", "年纳音")
    if cycle_branch == XUE_TANG_STEM_MAP.get(day_stem):
        add("学堂", "日干")

    # 文誉贵 — cycle 干支 is ±2 in the 60 甲子 from the natal day pillar
    _day_gz = day_stem + day_branch
    if _day_gz in SIXTY_JIAZI:
        _dp = SIXTY_JIAZI.index(_day_gz)
        if cycle_pillar in (SIXTY_JIAZI[(_dp - 2) % 60], SIXTY_JIAZI[(_dp + 2) % 60]):
            add("文誉贵", "日柱")

    # 隔角煞 — directional, both insertions per path (natal _calc_ge_jiao_sha).
    #   Path 1 (day→hour, +2): natal places on BOTH Day and Hour, so the guest carries it.
    if ge_jiao_sha_map_day_time.get(day_branch) == cycle_branch:
        add("隔角煞", "日支", zuhe=["运柱", "日柱"])   # guest as Hour
    elif ge_jiao_sha_map_day_time.get(cycle_branch) == hour_branch:
        add("隔角煞", "日支", zuhe=["运柱", "时柱"])   # guest as Day
    #   Path 2 (year↔day opposition): natal places on Day ONLY (Year anchor never carries).
    if ge_jiao_sha_map_year_day.get(year_branch) == cycle_branch:
        add("隔角煞", "年支", zuhe=["运柱"])           # guest as Day → carries
    elif ge_jiao_sha_map_year_day.get(cycle_branch) == day_branch:
        add("隔角煞", "年支", zuhe=["日柱"])           # guest as Year → excluded

    # ════════════════════════════════════════════════════════════════════════
    # Phase 2 — set-based stars (guest completes / reinforces a set)
    # ════════════════════════════════════════════════════════════════════════
    # 三奇 — guest-involving consecutive triples (NOT pure set-presence).
    _Y, _M, _D, _H = ctx.gans[0], ctx.gans[1], ctx.gans[2], ctx.gans[3]
    _G = cycle_stem
    _guest_triples = [
        (_G, _Y, _M), (_Y, _G, _M), (_Y, _M, _G),
        (_G, _M, _D), (_M, _G, _D), (_M, _D, _G),
        (_G, _D, _H), (_D, _G, _H), (_D, _H, _G),
    ]
    _san_qi_natal = [(0, 1)] * 3 + [(1, 2)] * 3 + [(2, 3)] * 3
    _natal_windows = [(_Y, _M, _D), (_M, _D, _H)]
    for _trio, _sq_name in THREE_WONDERS_TRIOS:
        _variants = (_trio, _trio[::-1])
        _matched = next(
            (nat for tr, nat in zip(_guest_triples, _san_qi_natal)
             if list(tr) in _variants),
            None,
        )
        if _matched is not None:
            _natal_has = any(list(w) in _variants for w in _natal_windows)
            add(_sq_name, "组合",
                detail="增力" if _natal_has else "引动成局",
                zuhe=["运柱"] + [_PILLAR_LABELS[p] for p in _matched])

    # 自缢煞 / 破煞 — whole-chart branch-pair completion (guest supplies one half).
    for _pairs, _sha in ((_ZI_YI_SHA_PAIRS, "自缢煞"), (_PO_SHA_PAIRS, "破煞")):
        for _pair in _pairs:
            if cycle_branch in _pair and (_pair - {cycle_branch}) <= natal_branches:
                add(_sha, "四柱",
                    detail="增力" if _pair <= natal_branches else "引动成局",
                    zuhe=["运柱"] + _natal_pillars_with_branch(ctx, _pair))
                break

    # 挂剑煞 (从革) — combined 5-pillar metal formation; guest must be metal to contribute.
    if cycle_branch in GUA_JIAN_METAL_FULL:
        _combined = list(ctx.zhis) + [cycle_branch]
        _all_metal = all(z in GUA_JIAN_METAL_FULL for z in _combined)
        _heavy = sum(1 for z in _combined if z in GUA_JIAN_METAL_TRIO) >= 3
        if _all_metal or _heavy:
            _natal_all = all(z in GUA_JIAN_METAL_FULL for z in ctx.zhis)
            _natal_heavy = sum(1 for z in ctx.zhis if z in GUA_JIAN_METAL_TRIO) >= 3
            add("挂剑煞", "四柱",
                detail="增力" if (_natal_all or _natal_heavy) else "引动成局",
                zuhe=["运柱"] + _natal_pillars_with_branch(ctx, GUA_JIAN_METAL_FULL))

    # 天火煞 — combined fire frame; a guest bringing water VOIDS it.
    _cb = natal_branches | {cycle_branch}
    _cs = natal_stems | {cycle_stem}
    if (
        TIAN_HUO_FIRE_TRINE <= _cb
        and (_cs & TIAN_HUO_FIRE_STEMS)
        and not (_cs & TIAN_HUO_WATER_STEMS)
        and not (_cb & TIAN_HUO_WATER_BRANCHES)
        and (cycle_branch in TIAN_HUO_FIRE_TRINE or cycle_stem in TIAN_HUO_FIRE_STEMS)
    ):
        _natal_fire = (
            TIAN_HUO_FIRE_TRINE <= natal_branches
            and (natal_stems & TIAN_HUO_FIRE_STEMS)
            and not (natal_stems & TIAN_HUO_WATER_STEMS)
            and not (natal_branches & TIAN_HUO_WATER_BRANCHES)
        )
        add("天火煞", "四柱",
            detail="增力" if _natal_fire else "引动成局",
            zuhe=["运柱"] + _natal_pillars_with_branch(ctx, TIAN_HUO_FIRE_TRINE))

    # 天屠煞 — directional day↔hour pair; guest inserts as Day or Hour only.
    if cycle_branch == _TIAN_TU_SHA_DAY_HOUR.get(day_branch):
        add("天屠煞", "日支", detail="引动成局", zuhe=["运柱", "日柱"])
    elif cycle_branch == _TIAN_TU_SHA_DAY_HOUR.get(hour_branch):
        add("天屠煞", "日支", detail="引动成局", zuhe=["运柱", "时柱"])

    return entries
