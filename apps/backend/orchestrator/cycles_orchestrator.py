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
from dataclasses import dataclass
from datetime import datetime

from apps.backend.astronomer_logic.bazi_key import encode_bazi_key
from apps.backend.astronomer_logic.bazi_pillars import get_bazi_pillars
from apps.backend.astronomer_logic.cycles.cycle_interactions import (
    CompanionPillar,
    get_cycle_interactions,
)
from apps.backend.astronomer_logic.cycles.cycle_pillars import (
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


@dataclass(frozen=True)
class _DecadeContext:
    """The enclosing 大运's facts a 流年 needs to be read 岁运并临.

    pillar:   (大运 stem, 大运 branch) — added as a pillar in the 流年 reclassification.
    dynamics: the 大运's 柱位动态 — merged into the 流年 reclassification, and the list the
              年's 岁运 layer re-resolves under its 合绊 locks.
    baseline: the decade's 五行 力量 map (natal + 大运) — the baseline the 流年 变化 is
              measured against, so the delta isolates the year's own contribution.
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
    pillar = build_cycle_pillar(cycle_stem, cycle_branch, cycle_xun_kong, ctx, cycle_label)
    interactions = get_cycle_interactions(
        cycle_stem,
        cycle_branch,
        ctx,
        cycle_label=cycle_label,
        cycle_xun_kong=cycle_xun_kong,
        cycle_stem_rooting=pillar["天干"]["根基强度"],
        companion=decade.as_companion() if decade else None,
    )

    yun_shi = get_cycle_yun_shi(cycle_branch, ctx.yong_shen, cycle_stem)

    sui_yun = None
    # decade_dynamics defaults to the decade's raw (unconstrained) list; the 岁运 layer
    # replaces it with the version re-resolved under this year's 合绊 locks, so the 五行
    # layer and the 岁运 layer never disagree about whether the 大运 actually acted.
    decade_dynamics = decade.dynamics if decade else ()
    if decade:
        sui_yun, decade_dynamics = analyse_sui_yun(
            cycle_stem,
            cycle_branch,
            decade.pillar[0],
            decade.pillar[1],
            interactions,
            decade.dynamics,
            ctx,
        )
        # 警示 is intensity/delivery (岁运并临, 反吟, 运犯岁君); 评级 stays a 五行-favourability
        # verdict. Orthogonal axes — collapsing them into one score destroys both.
        if sui_yun["警示"]:
            yun_shi = {**yun_shi, "警示": sui_yun["警示"]}

    entry = {
        "运柱": pillar,
        "作用": interactions,
        "神煞": get_cycle_shen_sha_interpretations(
            get_cycle_shen_sha(cycle_stem, cycle_branch, ctx), cycle_label
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
            decade_dynamics=decade_dynamics,
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
    liu_nian, birth_year: int, ctx: NatalContext, decade: _DecadeContext | None = None
) -> dict:
    """One fully-analysed 流年 entry (read 岁运并临 inside its `decade`).

    decade is None only for the pre-起运 stub (未行大运) — there is no 大运 yet, so the
    year acts on the natal chart alone (natal + 流年) with 变化 measured against birth,
    and carries no 岁运 block: there is nothing for it to relate to.
    """
    gan_zhi = liu_nian.getGanZhi()
    stem, branch = gan_zhi[0], gan_zhi[1]
    entry = {
        "年份": liu_nian.getYear(),
        "虚岁": liu_nian.getAge(),
        "周岁": liu_nian.getYear() - birth_year,
        "干支": gan_zhi,
        "生肖": _BRANCH_SHENG_XIAO.get(branch, ""),
        **_analyse_cycle_pillar(stem, branch, liu_nian.getXunKong(), ctx, "流年", decade=decade),
        "太岁": _tai_sui_check(branch, ctx),
        "流月": [],  # reserved seam for the future monthly layer
    }
    return entry


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
    birth_year = lunar_birthday.getSolar().getYear()

    da_yun_entries = []
    for da_yun in yun.getDaYun(_DA_YUN_COUNT):
        i = da_yun.getIndex()
        base = {
            "序号": i,
            "干支": da_yun.getGanZhi(),
            "开始年份": da_yun.getStartYear(),
            "结束年份": da_yun.getEndYear(),
            "开始年龄": da_yun.getStartAge(),
            "结束年龄": da_yun.getEndAge(),
            "周期": f"{da_yun.getStartAge()}-{da_yun.getEndAge()}岁",
        }

        if i == 0:
            # Pre-运 stub: lunar-python returns GanZhi == "" for index 0.
            # Its 流年 (birth → 起运) are still analysable when requested.
            stub = {**base, "阶段": "未行大运", "流年": []}
            if da_yun_index == 0:
                stub["流年"] = [
                    _liu_nian_entry(ln, birth_year, ctx) for ln in da_yun.getLiuNian()
                ]
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
            decade = _build_decade_context(
                ctx, stem, branch, entry["作用"], entry["运柱"], da_yun.getXunKong()
            )
            entry["流年"] = [
                _liu_nian_entry(ln, birth_year, ctx, decade) for ln in da_yun.getLiuNian()
            ]

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
