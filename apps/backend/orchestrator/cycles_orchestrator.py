"""
Cycles Orchestrator — 大运 (10-year luck pillars) + 流年 (annual pillars).

Accepts the same birth input as the natal orchestrator, rebuilds the minimal
natal context (same module order as calculate_natal_chart so the effective
day master and DM strength verdicts match /natal exactly), then enumerates
the 大运 via lunar-python's Yun/DaYun chain and runs the per-pillar cycle
analysis (运柱 / 作用 / 神煞 / 五行动态) for each.

流年 are computed lazily: only the decade selected by da_yun_index carries a
populated 流年 list. Every 流年 entry carries an empty "流月" list — the
reserved seam for the future monthly layer.

Timeline — TWO INDEPENDENT AXES, and conflating them is the classic error:

    大运 boundaries are INDIVIDUAL. A decade begins at the 起运 instant and every
    10 years on that anniversary (交运). Desmond: 1991-11-04 16:14:27, then
    2001-11-04, 2011-11-04 …
    流年 boundaries are UNIVERSAL. A year begins at 立春 — the same instant for
    everyone alive. 2021: 2021-02-03 22:58:48 → 2022-02-04 04:50:47.

Nothing aligns the two. A 流年 straddling a 交运 is therefore lived partly under
each decade and appears in BOTH decades' 流年 lists, flagged 交运年 — analysed
once per decade, with that decade as its companion, which is exactly the classical
"read the 交运 year against both decades" and needs no extra machinery.

This is why lunar-python's DaYun.getLiuNian() is NOT used: it groups years by
calendar year counted off the decade's start year (1991-2000 for a decade that
actually runs Nov 1991 → Nov 2001), silently snapping the individual axis onto the
universal one. The years are enumerated here instead — see _overlapping_liu_nian_years.

Ages are ENDPOINT ages, read at the period's own boundaries, so a decade's
结束虚岁 equals the next decade's 开始虚岁 exactly as their instants coincide.
虚岁 is anchored on 立春 (see _xu_sui), not on the calendar year.

All instants are naive datetimes in the same frame as the (TST-corrected) birth
instant and every 节气 lunar-python reports — they are never mixed with wall-clock
UTC, and callers comparing "now" against them must convert first.

岁运: a 大运 is analysed against the natal chart alone (1×4) — a decade exists
independently of any year inside it. A 流年 is analysed against the natal chart
PLUS its enclosing 大运 (1×5), and carries an extra "岁运" block: the classical
reading of that relationship (岁运并临 / 反吟 / 运犯岁君 …) and, crucially, which of
the decade's actions on the 命局 are suppressed this year (a 大运 bound by the year
does not deliver its 冲). See cycles/sui_yun.py.

Determinism: no datetime.now(), no "当运" flag — the response depends only on
the birth instant + gender (+ da_yun_index), so the frontend derives "current
decade/year" from the year ranges.

Caching: 起运 timing depends on the exact birth instant, which chart_key
deliberately excludes — cycle responses must NOT be cached under chart_key.
The chart_key returned here is for log correlation only.
"""

import json
from dataclasses import dataclass, replace
from datetime import datetime
from functools import lru_cache

from lunar_python import Solar
from lunar_python.util import LunarUtil

from apps.backend.astronomer_logic.bazi_key import encode_bazi_key
from apps.backend.astronomer_logic.bazi_pillars import get_bazi_pillars
from apps.backend.astronomer_logic.cycles.cycle_interactions import (
    get_cycle_interactions,
)
from apps.backend.astronomer_logic.cycles.cycle_pillars import (
    CompanionPillar,
    NatalContext,
    build_cycle_pillar,
    build_natal_context,
)
from apps.backend.astronomer_logic.cycles.cycle_shen_sha import get_cycle_shen_sha
from apps.backend.astronomer_logic.cycles.sui_yun import analyse_sui_yun
from apps.backend.astronomer_logic.cycles.cycle_wu_xing import (
    classify_with_transiting,
    get_cycle_wu_xing,
    get_cycle_yun_shi,
)
from apps.backend.astronomer_logic.cycles.cycle_interpretation_shen_sha import (
    get_cycle_shen_sha_interpretations,
)
from apps.backend.astronomer_logic.natal_interactions import (
    break_map,
    clash_map,
    harm_map,
    is_valid_punishment,
)
from apps.backend.astronomer_logic.day_master_strength import get_day_master_strength
from apps.backend.astronomer_logic.na_yin import get_na_yin
from apps.backend.astronomer_logic.natal_five_elements import (
    QualitativeFiveElementsClassifier,
    get_pillar_five_elements,
)
from apps.backend.astronomer_logic.natal_interactions import get_natal_interactions
from apps.backend.astronomer_logic.ten_gods import (
    apply_heavenlystem_tranformation_tengods,
    get_ten_gods,
)
from apps.backend.astronomer_logic.twelve_life_stages import get_twelve_life_stages
from apps.backend.astronomer_logic.void_xun_kong import (
    check_pillar_void_status,
    get_void_xun_kong,
)
from apps.backend.orchestrator.astronomer_data_orchestrator import get_lunar_birthday

_PILLAR_KEYS = ["年柱", "月柱", "日柱", "时柱"]

_BRANCH_SHENG_XIAO = dict(zip("子丑寅卯辰巳午未申酉戌亥", "鼠牛虎兔龙蛇马羊猴鸡狗猪"))

# lunar-python's Yun.getDaYun() default — index 0 is the pre-运 stub.
_DA_YUN_COUNT = 10

# Instant format, matching lunar-python's Solar.toYmdHms() so 起运阳历 and every
# boundary emitted here read identically.
_TS = "%Y-%m-%d %H:%M:%S"

# A date solidly inside a solar year, used to probe lunar-python for that year's facts.
# Jan/Feb probes sit either side of 立春 and land in an ambiguous lunar year; a mid-year
# probe never does.
_MID_YEAR = (6, 1, 12, 0, 0)


# ── timeline primitives (see the two-axes note in the module docstring) ──────


def _to_datetime(solar) -> datetime:
    """lunar-python Solar → naive datetime, in the chart's own (TST-shifted) frame."""
    return datetime(
        solar.getYear(), solar.getMonth(), solar.getDay(),
        solar.getHour(), solar.getMinute(), solar.getSecond(),
    )


@lru_cache(maxsize=None)
def _li_chun(year: int) -> datetime:
    """The 立春 instant that OPENS solar `year` — the universal 流年 boundary."""
    month, day, hour, minute, second = _MID_YEAR
    jie_qi = (
        Solar.fromYmdHms(year, month, day, hour, minute, second)
        .getLunar()
        .getJieQiTable()["立春"]
    )
    return _to_datetime(jie_qi)


@lru_cache(maxsize=None)
def _year_gan_zhi(year: int) -> str:
    """干支 of the 立春-year opening in solar `year` (立春-exact, never calendar-exact)."""
    month, day, hour, minute, second = _MID_YEAR
    return (
        Solar.fromYmdHms(year, month, day, hour, minute, second)
        .getLunar()
        .getYearInGanZhiExact()
    )


def _li_chun_year(moment: datetime) -> int:
    """The 立春-year containing `moment` — i.e. the year whose 立春 has already passed."""
    return moment.year if moment >= _li_chun(moment.year) else moment.year - 1


def _plus_years(moment: datetime, years: int) -> datetime:
    """`moment` shifted by whole years; a 2-29 anniversary clamps to 2-28.

    Every decade boundary is computed from 起运 with its FULL offset (not by repeatedly
    adding 10 to the previous one), so a clamp can never accumulate into drift.
    """
    try:
        return moment.replace(year=moment.year + years)
    except ValueError:
        return moment.replace(year=moment.year + years, day=28)


def _zhou_sui(birth: datetime, moment: datetime) -> int:
    """周岁 — completed years lived at `moment`. Birthday-accurate, not calendar-year.

    `年份 - 出生年` (what lunar-python's age arithmetic reduces to) answers a different
    question: the age ATTAINED during that year. At 立春 2021 a subject born 1985-11-25
    is 35 and turns 36 that November, so the coherent partner of 虚岁 37 is 35, not 36.
    """
    years = moment.year - birth.year
    if _plus_years(birth, years) > moment:
        years -= 1
    return years


def _xu_sui(birth_li_chun_year: int, moment: datetime) -> int:
    """虚岁 at `moment`: 1 throughout the 立春-year of birth, +1 at every 立春.

    Anchored on 立春, NOT on the calendar year. lunar-python derives 虚岁 as
    `year - 出生年 + 1` (DaYun.getStartAge, inherited by LiuNian.getAge), which agrees
    for anyone born after 立春 but is off by one for LIFE for a January-born subject —
    whose birth 立春-year is the PREVIOUS solar year.
    """
    return _li_chun_year(moment) - birth_li_chun_year + 1


def _overlapping_liu_nian_years(start: datetime, end: datetime) -> range:
    """The 立春-years whose own window overlaps the period [start, end).

    A decade normally touches ELEVEN of them: 交运 falls mid-立春-year at both ends, so
    the first and last are partial and are shared with the neighbouring decade. Only a
    起运 landing exactly on 立春 yields a clean ten.
    """
    first = _li_chun_year(start)
    last = _li_chun_year(end)
    if _li_chun(last) >= end:
        # The period ends exactly on a 立春 — that year opens with the NEXT period.
        last -= 1
    return range(first, last + 1)


@dataclass(frozen=True)
class _DecadeContext:
    """The enclosing 大运's facts a 流年 needs to be read 岁运并临.

    pillar:   (大运 stem, 大运 branch) — added as a pillar in the 流年 reclassification.
    dynamics: the 大运's 柱位动态. Built RAW (decade vs natal) once per decade — but inside
              _analyse_cycle_pillar the context is rebound (dataclasses.replace) to the
              year's view, where this field holds the dynamics re-resolved under that year's
              岁运 locks. Downstream layers therefore always read the decade as the year
              actually experiences it; the raw list has no name in that scope.
    baseline: the decade's 五行 力量 map (natal + 大运) — the fixed reference each of the
              decade's 10 years measures its 变化 against, so the delta isolates the year's
              own contribution. Never re-derived per year: the yardstick must not move with
              the thing being measured.
    rooting:  the 大运 stem's 根基强度 — so the 岁运 scan reads the decade's rooting from
              the decade's own pillar rather than recomputing it.
    xun_kong: the 大运's own void pair.
    """

    pillar: tuple[str, str]
    dynamics: tuple
    baseline: dict
    rooting: str
    xun_kong: str

    def as_companion(self) -> CompanionPillar:
        """The decade as a fifth opponent for the year's interaction scan."""
        return CompanionPillar(
            stem=self.pillar[0],
            branch=self.pillar[1],
            label="大运",
            stem_rooting=self.rooting,
            xun_kong=self.xun_kong,
        )


def _build_decade_context(
    ctx: NatalContext,
    da_yun_stem: str,
    da_yun_branch: str,
    da_yun_interactions: dict,
    da_yun_pillar: dict,
    da_yun_xun_kong: str,
) -> _DecadeContext:
    """Compute the decade context once per expanded 大运 (shared by all its 流年)."""
    dynamics = tuple(da_yun_interactions.get("柱位动态", []))
    baseline = classify_with_transiting(ctx, ((da_yun_stem, da_yun_branch, "大运"),), dynamics)
    return _DecadeContext(
        pillar=(da_yun_stem, da_yun_branch),
        dynamics=dynamics,
        baseline=baseline,
        rooting=da_yun_pillar["天干"]["根基强度"],
        xun_kong=da_yun_xun_kong,
    )


def _build_context(bazi, gender: int, lunar_birthday=None) -> NatalContext:
    """Rebuild the minimal natal subset in the SAME order as calculate_natal_chart
    so effective_day_stem / dm_strength match what /natal reports.

    lunar_birthday feeds only the 五行 baseline's 土旺用事 window; when omitted (unit
    tests that don't exercise five-elements) that upgrade is simply skipped."""
    pillars = get_bazi_pillars(bazi)
    life_stages = get_twelve_life_stages(bazi, pillars)
    void = get_void_xun_kong(bazi)
    pillar_void = check_pillar_void_status(void, pillars)
    ten_gods = get_ten_gods(bazi)
    na_yin = get_na_yin(bazi)
    pillar_elements = get_pillar_five_elements(pillars)

    # Enrich pillars 藏干 with 十神 — consumed by get_natal_interactions
    for k in _PILLAR_KEYS:
        for tier, info in pillars[k]["藏干"].items():
            info["十神"] = ten_gods[k]["藏干十神"][tier]

    # Minimal si_zhu — same construction as the natal orchestrator; consumed by
    # apply_heavenlystem_tranformation_tengods (化气格 detection).
    si_zhu = {
        key: {
            "天干": {
                "天干": pillars[key]["天干"],
                "阴阳": pillars[key]["天干阴阳"],
                "五行": pillar_elements[key]["天干五行"],
                "根基强度": pillars[key]["根基强度"],
                "通根于": pillars[key]["通根于"],
                "十神": ten_gods[key]["天干十神"],
            },
            "地支": {
                "地支": pillars[key]["地支"],
                "阴阳": pillars[key]["地支阴阳"],
                "五行": pillar_elements[key]["地支五行"],
            },
            "藏干": {
                tier: {
                    **info,
                    "五行": pillar_elements[key]["藏干五行"][tier],
                }
                for tier, info in pillars[key]["藏干"].items()
            },
            "十二长生": life_stages[key],
            "空亡": {
                "本柱旬空": void[key],
                **pillar_void[key],
            },
            "纳音": na_yin[key],
        }
        for key in _PILLAR_KEYS
    }

    natal_interactions_data = get_natal_interactions(pillars, void)
    ten_gods, si_zhu = apply_heavenlystem_tranformation_tengods(
        ten_gods, si_zhu, natal_interactions_data, pillars["日柱"]["天干"]
    )
    day_master_data = get_day_master_strength(
        bazi, pillars, ten_gods, natal_interactions_data, pillar_void
    )

    # Natal-only 旺衰 baseline (matches /natal's 五行 verdict). Computed once here so
    # every cycle pillar can report its delta (变化) against it without recomputing.
    # The classifier reads only 天干/地支/藏干/空亡 from si_zhu — the 七杀/食神 relabels
    # (which touch 十神 only) are irrelevant, so the pre-relabel si_zhu is correct here.
    natal_five_elements = QualitativeFiveElementsClassifier(
        si_zhu, natal_interactions_data, lunar_birthday=lunar_birthday
    ).classify_all(include_strength=True)["五行"]

    # NOTE: 七杀→偏官 / 食神→伤官 relabeling is deliberately NOT applied here —
    # the 制化 annotation in build_cycle_pillar needs raw natal god labels.
    return build_natal_context(
        bazi,
        gender,
        day_master_data,
        ten_gods,
        void,
        na_yin,
        natal_si_zhu=si_zhu,
        natal_interactions=natal_interactions_data,
        lunar_birthday=lunar_birthday,
        natal_five_elements=natal_five_elements,
    )


def _analyse_cycle_pillar(
    cycle_stem: str,
    cycle_branch: str,
    cycle_xun_kong: str,
    ctx: NatalContext,
    cycle_label: str,
    *,
    decade: "_DecadeContext | None" = None,
) -> dict:
    """Run the full per-pillar cycle analysis. Shared by 大运 and 流年.

    `decade` is set only for 流年: it carries the enclosing 大运 (pillar + 柱位动态 +
    五行 力量 baseline) so the year's 五行 is read 岁运并临 (natal + 大运 + 流年) and its
    变化 is measured against the decade rather than birth.

    It also makes the year's interaction scan a 1×5 — the decade joins the four natal
    pillars as an opponent — and unlocks the 岁运 layer. A 大运 has no enclosing decade,
    so it is scanned 1×4 and carries no 岁运 block: a decade exists independently of any
    particular year inside it.
    """
    # One companion, shared by every layer that can see the decade: the interaction scan
    # (1×5), the 制化 annotation + 岁运互空 in the 运柱, and the set-completion 神煞.
    companion = decade.as_companion() if decade else None

    pillar = build_cycle_pillar(
        cycle_stem, cycle_branch, cycle_xun_kong, ctx, cycle_label, companion
    )
    interactions = get_cycle_interactions(
        cycle_stem,
        cycle_branch,
        ctx,
        cycle_label=cycle_label,
        cycle_xun_kong=cycle_xun_kong,
        cycle_stem_rooting=pillar["天干"]["根基强度"],
        companion=companion,
    )

    yun_shi = get_cycle_yun_shi(cycle_branch, ctx.yong_shen, cycle_stem)

    sui_yun = None
    if decade:
        sui_yun, constrained = analyse_sui_yun(
            cycle_stem,
            cycle_branch,
            decade.pillar[0],
            decade.pillar[1],
            interactions,
            decade.dynamics,
            ctx,
        )
        # REBIND `decade` to this year's view of it. Past this line the decade's raw
        # 柱位动态 are unreachable by design: a 大运 the year has bound (合绊) did not act,
        # and every downstream layer must agree on that. Handing the raw list to
        # get_cycle_wu_xing would make the 五行 layer report a 冲 that the 岁运 layer, in the
        # same response, says never landed — and nothing would raise. There is now exactly
        # one `decade` name in scope and it always holds the correct list.
        #
        # `baseline` is deliberately NOT re-derived: it is the decade's own 五行 力量 map,
        # the fixed reference each of its 10 years measures its 变化 against. Constraining it
        # per-year would make the yardstick move with the thing being measured.
        decade = replace(decade, dynamics=constrained)

        # 警示 is intensity/delivery (岁运并临, 反吟, 运犯岁君); 评级 stays a 五行-favourability
        # verdict. Orthogonal axes — collapsing them into one score destroys both.
        if sui_yun["警示"]:
            yun_shi = {**yun_shi, "警示": sui_yun["警示"]}

    entry = {
        "运柱": pillar,
        "作用": interactions,
        "神煞": get_cycle_shen_sha_interpretations(
            get_cycle_shen_sha(cycle_stem, cycle_branch, ctx, companion), cycle_label
        ),
        # Headline 喜运/平运/忌运 for the period — read it against the 五行动态 detail below.
        # The stem is passed for 非正格 charts: a 忌 stem attacks a fragile structure directly
        # (透干破格) and drags the verdict down a step. 正格 charts remain branch-only — the
        # 金不换 表 is a 方位 table, and directions are branches.
        "运势": yun_shi,
        "五行动态": get_cycle_wu_xing(
            cycle_stem,
            cycle_branch,
            ctx,
            interactions,
            pillar,
            cycle_label,
            decade_pillar=decade.pillar if decade else None,
            decade_dynamics=decade.dynamics if decade else (),
            baseline=decade.baseline if decade else None,
        ),
    }
    if sui_yun is not None:
        entry["岁运"] = sui_yun
    return entry


def _tai_sui_check(liu_nian_branch: str, ctx: NatalContext) -> dict:
    """Compact 太岁 check — the 流年 branch vs the natal 年支 (本命/生肖 anchor).

    值太岁 (same), 冲太岁 (六冲), 刑太岁 (三刑/自刑), 害太岁 (六害), 破太岁 (六破).
    Multiple relations can coexist (e.g. 刑+破)."""
    natal_year_branch = ctx.zhis[0]
    relations: list[str] = []
    if liu_nian_branch == natal_year_branch:
        relations.append("值太岁")
    if clash_map.get(liu_nian_branch) == natal_year_branch:
        relations.append("冲太岁")
    if is_valid_punishment(liu_nian_branch, natal_year_branch):
        relations.append("刑太岁")
    if harm_map.get(liu_nian_branch) == natal_year_branch:
        relations.append("害太岁")
    if break_map.get(liu_nian_branch) == natal_year_branch:
        relations.append("破太岁")

    if not relations:
        return {"关系": "无", "说明": "流年与本命年支无犯，太岁平顺"}
    joined = "、".join(relations)
    return {
        "关系": joined,
        "说明": f"流年支{liu_nian_branch}与本命年支{natal_year_branch}相犯（{joined}），岁君临身，宜守不宜攻",
    }


def _liu_nian_entry(
    year: int,
    period: tuple[datetime, datetime],
    birth: datetime,
    birth_li_chun_year: int,
    ctx: NatalContext,
    decade: _DecadeContext | None = None,
) -> dict:
    """One fully-analysed 流年 entry (read 岁运并临 inside its `decade`).

    `period` is the enclosing 大运's [起始, 结束) window — used ONLY to decide 交运年.
    The year's own 起始/结束 are its 立春 pair and owe nothing to the decade: the two
    axes are independent (module docstring).

    decade is None only for the pre-起运 stub (未行大运) — there is no 大运 yet, so the
    year acts on the natal chart alone (natal + 流年) with 变化 measured against birth,
    and carries no 岁运 block: there is nothing for it to relate to.
    """
    start, end = _li_chun(year), _li_chun(year + 1)
    period_start, period_end = period
    gan_zhi = _year_gan_zhi(year)
    stem, branch = gan_zhi[0], gan_zhi[1]
    # Ages are read at the moment the subject actually ENTERS the year. That is 立春 for
    # every year but one: the birth year's 立春 predates birth, and measuring there would
    # report 周岁 -1 (and 虚岁 0) for a person not yet born.
    aged_at = max(start, birth)
    return {
        "年份": year,
        "起始": start.strftime(_TS),
        "结束": end.strftime(_TS),
        # The year's 立春 window is not wholly inside this period — it straddles a 交运,
        # so the year is shared with the neighbouring decade and appears in both lists.
        # On the pre-起运 stub the two partial years are cut by birth and by 起运 instead.
        "交运年": start < period_start or end > period_end,
        "虚岁": _xu_sui(birth_li_chun_year, aged_at),
        "周岁": _zhou_sui(birth, aged_at),
        "干支": gan_zhi,
        "生肖": _BRANCH_SHENG_XIAO.get(branch, ""),
        **_analyse_cycle_pillar(
            stem, branch, LunarUtil.getXunKong(gan_zhi), ctx, "流年", decade=decade
        ),
        "太岁": _tai_sui_check(branch, ctx),
        "流月": [],  # reserved seam for the future monthly layer
    }


def _liu_nian_list(
    period: tuple[datetime, datetime],
    birth: datetime,
    birth_li_chun_year: int,
    ctx: NatalContext,
    decade: _DecadeContext | None = None,
) -> list[dict]:
    """Every 流年 overlapping `period`, each analysed inside `decade`.

    Normally ELEVEN entries: the two 交运 years are partial and are also carried by the
    neighbouring decade, where they are analysed again against THAT companion.
    """
    return [
        _liu_nian_entry(year, period, birth, birth_li_chun_year, ctx, decade)
        for year in _overlapping_liu_nian_years(*period)
    ]


def calculate_cycles(
    birth_datetime: datetime,
    latitude: float,
    longitude: float,
    gender: int,
    use_solar_time_correction: bool = True,
    da_yun_index: int | None = None,
) -> tuple[dict, str]:
    """
    Compute the 大运 timeline (all decades fully analysed) and, when
    da_yun_index is given, that decade's 流年.

    Args:
        birth_datetime:            Wall-clock birth datetime (naive).
        latitude:                  Birth location latitude in decimal degrees.
        longitude:                 Birth location longitude in decimal degrees.
        gender:                    1 = male, 0 = female.
        use_solar_time_correction: If True, applies True Solar Time conversion.
        da_yun_index:              大运 index (0-9); when set, that decade's
                                   流年 list is populated.

    Returns:
        (cycles, chart_key) where cycles = {"起运": {...}, "大运": [...]}.
        chart_key is for log correlation only — cycles depend on the exact
        birth instant and must never be cached under it.
    """
    lunar_birthday = get_lunar_birthday(
        birth_datetime, latitude, longitude, use_solar_time_correction
    )
    bazi = lunar_birthday.getEightChar()
    chart_key = encode_bazi_key(bazi, gender)

    ctx = _build_context(bazi, gender, lunar_birthday)

    yun = bazi.getYun(gender)
    qi_yun_solar = yun.getStartSolar()

    # The individual axis. Every decade boundary is 起运 + a whole multiple of 10 years;
    # the pre-运 stub runs from birth to 起运.
    birth_dt = _to_datetime(lunar_birthday.getSolar())
    qi_yun = _to_datetime(qi_yun_solar)
    birth_li_chun_year = _li_chun_year(birth_dt)

    da_yun_entries = []
    for da_yun in yun.getDaYun(_DA_YUN_COUNT):
        i = da_yun.getIndex()
        start, end = (
            (birth_dt, qi_yun) if i == 0
            else (_plus_years(qi_yun, (i - 1) * 10), _plus_years(qi_yun, i * 10))
        )
        # Endpoint ages, read at the period's own boundaries — so 结束虚岁 equals the next
        # decade's 开始虚岁, exactly as their instants coincide.
        start_xu, end_xu = (
            _xu_sui(birth_li_chun_year, start),
            _xu_sui(birth_li_chun_year, end),
        )
        base = {
            "序号": i,
            "干支": da_yun.getGanZhi(),
            "起始": start.strftime(_TS),
            "结束": end.strftime(_TS),
            "开始虚岁": start_xu,
            "结束虚岁": end_xu,
            "开始周岁": _zhou_sui(birth_dt, start),
            "结束周岁": _zhou_sui(birth_dt, end),
            "周期": f"{start_xu}-{end_xu}岁",  # 虚岁, endpoint to endpoint
        }

        if i == 0:
            # Pre-运 stub: lunar-python returns GanZhi == "" for index 0.
            # Its 流年 (birth → 起运) are still analysable when requested.
            stub = {**base, "阶段": "未行大运", "流年": []}
            if da_yun_index == 0:
                stub["流年"] = _liu_nian_list(
                    (start, end), birth_dt, birth_li_chun_year, ctx
                )
            da_yun_entries.append(stub)
            continue

        gan_zhi = da_yun.getGanZhi()
        stem, branch = gan_zhi[0], gan_zhi[1]
        entry = {
            **base,
            **_analyse_cycle_pillar(stem, branch, da_yun.getXunKong(), ctx, "大运"),
            "流年": [],
        }

        if da_yun_index is not None and i == da_yun_index:
            entry["流年"] = _liu_nian_list(
                (start, end),
                birth_dt,
                birth_li_chun_year,
                ctx,
                _build_decade_context(
                    ctx, stem, branch, entry["作用"], entry["运柱"], da_yun.getXunKong()
                ),
            )

        da_yun_entries.append(entry)

    cycles = {
        "起运": {
            "顺逆": "顺推" if yun.isForward() else "逆推",
            "起运阳历": qi_yun_solar.toYmdHms(),
            "起运计岁": (
                f"出生后{yun.getStartYear()}年"
                f"{yun.getStartMonth()}个月"
                f"{yun.getStartDay()}天"
                f"{yun.getStartHour()}小时"
            ),
            "性别": "男" if gender == 1 else "女",
        },
        # Chart-fixed 用神 (调候 + 扶抑) — the 喜忌 anchor each pillar's 五行动态 references.
        "用神": ctx.yong_shen,
        "大运": da_yun_entries,
    }
    return cycles, chart_key


# ============================================================================
# EXECUTION
# python -m apps.backend.orchestrator.cycles_orchestrator
# ============================================================================
if __name__ == "__main__":
    from datetime import datetime as dt

    from apps.utils.logging import configure_logging, get_logger

    logger = configure_logging()
    logger = get_logger(__name__)

    # ── Subjects ──────────────────────────────────────────────────────────────
    subjects = {
        "Desmond": (dt(1985, 11, 25, 17, 7, 0), 1.3253, 103.808053, 1),
        # "Corinne": (dt(1987, 6, 3, 12, 6, 0), 1.4759, 103.808053, 0),
        # "Lara":    (dt(2025,  7, 31,  9, 10, 0), 1.3253,  103.808053, 0),
        # "Waifu": (dt(1985, 2, 11, 10, 15, 0), 1.3253, 103.808053, 1),
        # "Ayden": (dt(2020, 2, 23, 00, 34, 0), 1.3253, 103.808053, 1),
    }

    for name, (birthday, lat, lon, gender) in subjects.items():
        logger.info("=" * 60)
        logger.info("Subject: %s  (%s)", name, birthday.strftime("%Y-%m-%d %H:%M"))

        cycles, chart_key = calculate_cycles(
            birthday, lat, lon, gender=gender, use_solar_time_correction=True, da_yun_index=4
        )


        logger.info("chart_key: %s", chart_key)
        logger.info("Cycles output:\n%s", json.dumps(cycles, ensure_ascii=False, indent=2))
