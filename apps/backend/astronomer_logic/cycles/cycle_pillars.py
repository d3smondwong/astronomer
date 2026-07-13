"""
运柱 Cycle Pillar Enrichment — shared by 大运 / 流年 (future 流月).

Builds the per-pillar analysis block for a single transiting (cycle) pillar,
mirroring the natal 四柱实体 per-pillar shape so the frontend can reuse its
pillar rendering. All level-specific traversal (Yun/DaYun/LiuNian objects,
ages, years) lives in the cycles orchestrator — this module only knows one
(cycle_stem, cycle_branch) pair plus the natal context.

Ten-god policy (see .claude/CLAUDE.md): cycle-pillar ten gods are RAW
LunarUtil.SHI_SHEN lookups — the natal 七杀→偏官 / 食神→伤官 relabeling is
adjacency-based, and adjacency is undefined for a transiting pillar. Instead
a 制化 annotation notes when the natal chart (chart-wide, revealed stems)
contains taming gods for an incoming 七杀 / a lurking 偏印 for an incoming
食神.

空亡 decomposes into three distinct checks (a pillar's own branch can never
sit inside its own 旬空):
  本柱旬空     — the cycle pillar's own void pair (reference data + the seam
                 for the future 流年-vs-大运 layer).
  落入命局空亡 — cycle branch ∈ natal 日柱 void pair (classical 岁运临空亡).
                 The dominant reading is 填实 — the void fills and the dormant
                 palace activates — so this is an annotation, not a weakness.
  命局逢运空   — natal branches ∈ the cycle's own void pair. School-dependent
                 (some reject 运论空亡 entirely); reported as data only and
                 never drives strength downgrades.
"""

from dataclasses import dataclass

from lunar_python.util import LunarUtil

from apps.backend.astronomer_logic.bazi_pillars import (
    _YANG_BRANCHES,
    _YANG_STEMS,
    _yin_yang,
    compute_single_stem_rooting,
)
from apps.backend.astronomer_logic.day_master_strength import (
    _STATE_DESCRIPTIONS,
    SeasonalFactors,
    get_seasonal_factors,
    get_stem_element,
)
from apps.backend.astronomer_logic.ten_gods import get_effective_stem
from apps.backend.astronomer_logic.twelve_life_stages import _self_seated_stage
from apps.backend.astronomer_logic.yong_shen import get_yong_shen

_NATAL_PILLAR_KEYS = ["年柱", "月柱", "日柱", "时柱"]
_HIDE_TIERS = ("本气", "中气", "余气")

# Ten gods that tame an incoming 七杀 when revealed in the natal chart
_QI_SHA_FOOD_TAMERS = frozenset({"食神"})
_QI_SHA_SEAL_TAMERS = frozenset({"正印", "偏印"})


@dataclass(frozen=True)
class NatalContext:
    """Immutable snapshot of the natal chart facts every cycle module needs.

    Built once per request by build_natal_context(); passed to every
    build_cycle_pillar / get_cycle_interactions / get_cycle_shen_sha /
    get_cycle_wu_xing call so 大运 and 流年 analysis share one natal view.
    """

    gans: tuple[str, ...]                  # (年干, 月干, 日干, 时干)
    zhis: tuple[str, ...]                  # (年支, 月支, 日支, 时支)
    hides: tuple[tuple[str, ...], ...]     # per pillar, ordered [本气, 中气, 余气]
    day_stem: str                          # raw 日干
    effective_day_stem: str                # differs only under natal 化气格
    gender: int                            # 1 = male, 0 = female
    natal_void: dict                       # get_void_xun_kong(bazi): {"年柱": "戌亥", ...}
    na_yin: dict                           # get_na_yin(bazi)
    dm_strength: str                       # 日主.强弱 verdict (matches /natal)
    dm_rooting: str                        # 日主.得地.通根 tier
    seasonal: SeasonalFactors              # natal month branch anchoring
    revealed_gods: frozenset               # visible-stem ten gods (透出), excl. 日主
    # Inputs the cycle five-elements reclassification needs (see cycle_wu_xing):
    natal_si_zhu: dict                     # 4-pillar entity dict (classifier input shape)
    natal_interactions: dict               # get_natal_interactions() output ({"作用": {"柱位动态": ...}})
    lunar_birthday: object                 # lunar_python Lunar object (土旺用事); may be None
    natal_five_elements: dict              # natal-only 旺衰 baseline: {element: {"状态": ...}}
    yong_shen: dict                        # get_yong_shen() verdict (调候 + 扶抑), chart-fixed


def build_natal_context(
    bazi,
    gender: int,
    day_master_data: dict,
    ten_gods: dict,
    natal_void: dict,
    na_yin: dict,
    natal_si_zhu: dict,
    natal_interactions: dict,
    lunar_birthday,
    natal_five_elements: dict,
) -> NatalContext:
    """
    Assemble the NatalContext from already-computed natal module outputs.

    Args:
        bazi:            EightChar object from lunar_birthday.getEightChar()
        gender:          1 = male, 0 = female
        day_master_data: get_day_master_strength() output — its 日主.五行 already
                         reflects a natal 化气格, so the effective day stem is
                         derived from it (same polarity, transformed element).
        ten_gods:        ten gods AFTER apply_heavenlystem_tranformation_tengods
                         but BEFORE the 七杀/食神 relabeling passes, so 食神/印
                         detection for the 制化 annotation sees raw labels.
        natal_void:      get_void_xun_kong(bazi)
        na_yin:          get_na_yin(bazi)
        natal_si_zhu:    4-pillar entity dict (QualitativeFiveElementsClassifier input shape);
                         reused by get_cycle_wu_xing to append the transiting pillar.
        natal_interactions: get_natal_interactions() output; merged with cycle interactions
                         for the combined 4+1 reclassification.
        lunar_birthday:  lunar_python Lunar object (for 土旺用事); may be None.
        natal_five_elements: natal-only 旺衰 baseline {element: {"状态": ...}}, computed once
                         so each cycle pillar can report its delta (变化) against it.
    """
    gans = (bazi.getYearGan(), bazi.getMonthGan(), bazi.getDayGan(), bazi.getTimeGan())
    zhis = (bazi.getYearZhi(), bazi.getMonthZhi(), bazi.getDayZhi(), bazi.getTimeZhi())
    hides = tuple(
        tuple(h)
        for h in (
            bazi.getYearHideGan(),
            bazi.getMonthHideGan(),
            bazi.getDayHideGan(),
            bazi.getTimeHideGan(),
        )
    )

    day_stem = bazi.getDayGan()
    dm = day_master_data["日主"]

    # 化气格: 日主.五行 is the transformed element; keep the raw stem's polarity.
    effective_element = dm["五行"]
    effective_day_stem = get_effective_stem(day_stem, effective_element)

    revealed_gods = frozenset(
        ten_gods[k]["天干十神"]
        for k in _NATAL_PILLAR_KEYS
        if ten_gods[k]["天干十神"] not in ("日主", "无")
    )

    return NatalContext(
        gans=gans,
        zhis=zhis,
        hides=hides,
        day_stem=day_stem,
        effective_day_stem=effective_day_stem,
        gender=gender,
        natal_void=natal_void,
        na_yin=na_yin,
        dm_strength=dm["强弱"],
        dm_rooting=dm["得地"]["通根"],
        seasonal=get_seasonal_factors(zhis[1]),
        revealed_gods=revealed_gods,
        natal_si_zhu=natal_si_zhu,
        natal_interactions=natal_interactions,
        lunar_birthday=lunar_birthday,
        natal_five_elements=natal_five_elements,
        # 用神 is chart-fixed. It carries 格局 (正格/从格/专旺/化气), which decides whether 喜忌
        # come from 扶抑+调候 or from the surrendered structure — so it needs the day-master
        # foundations, the 力量-bearing 五行 map, and the interactions.
        #
        # The EFFECTIVE stem indexes 调候: under a 化气格 the chart's climate is experienced
        # by the 化神, not by the stem it used to be. A 丁火 in 巳月 lives in a different
        # world than a 癸水 in 巳月.
        yong_shen=get_yong_shen(
            effective_day_stem,
            effective_element,
            zhis[1],
            day_master_data,
            natal_five_elements,
            natal_interactions,
        ),
    )


def _cycle_hidden_stems(cycle_branch: str) -> list[str]:
    """Hidden stems of the cycle branch, ordered [本气, 中气, 余气] (no padding)."""
    return list(LunarUtil.ZHI_HIDE_GAN.get(cycle_branch, []))


def _zhi_hua_annotation(stem_god: str, ctx: NatalContext) -> str | None:
    """制化 annotation for the cycle stem's raw ten god (chart-wide, no adjacency)."""
    if stem_god == "七杀":
        if ctx.revealed_gods & _QI_SHA_FOOD_TAMERS:
            return "命局食神透出，岁运七杀有制（食神制杀）"
        if ctx.revealed_gods & _QI_SHA_SEAL_TAMERS:
            return "命局印星透出，岁运七杀可化（印化杀）"
        return "命局无明显制化，岁运七杀直临"
    if stem_god == "食神" and "偏印" in ctx.revealed_gods:
        return "命局偏印透出，岁运食神防枭神夺食（枭夺提示）"
    return None


def _void_block(
    cycle_branch: str, cycle_xun_kong: str, ctx: NatalContext, cycle_label: str
) -> dict:
    """The three-check 空亡 block (see module docstring). Data + 填实 annotation only —
    strength modulation lives in cycle_interactions' void pass."""
    day_void = ctx.natal_void.get("日柱", "")

    if cycle_branch in day_void:
        into_natal_void = (
            f"{cycle_label}支{cycle_branch}落入命局日柱空亡（{day_void}），"
            f"岁运临空，逢之填实——空亡之宫因{cycle_label}引动而应事"
        )
    else:
        into_natal_void = "无"

    natal_into_cycle_void = [
        f"{_NATAL_PILLAR_KEYS[i]}支{zhi}"
        for i, zhi in enumerate(ctx.zhis)
        if cycle_xun_kong and zhi in cycle_xun_kong
    ]

    return {
        "本柱旬空": cycle_xun_kong or "无",
        "落入命局空亡": into_natal_void,
        "命局逢运空": natal_into_cycle_void if natal_into_cycle_void else "无",
    }


def build_cycle_pillar(
    cycle_stem: str,
    cycle_branch: str,
    cycle_xun_kong: str,
    ctx: NatalContext,
    cycle_label: str = "大运",
) -> dict:
    """
    Build the 运柱 analysis block for one cycle pillar.

    Args:
        cycle_stem:     transiting 天干 (e.g. "丙")
        cycle_branch:   transiting 地支 (e.g. "戌")
        cycle_xun_kong: the cycle pillar's own void pair from
                        DaYun/LiuNian.getXunKong() (e.g. "午未")
        ctx:            NatalContext from build_natal_context()
        cycle_label:    "大运" | "流年" (future "流月") — used in rooting labels
                        and 空亡 descriptions.

    Returns:
        dict mirroring the natal 四柱实体 per-pillar shape (天干/地支/藏干/
        十二长生/纳音/空亡) plus 季节状态 and an optional 制化 annotation.
    """
    stem_god = LunarUtil.SHI_SHEN.get(ctx.effective_day_stem + cycle_stem, "无")

    # 5-branch rooting: 4 natal branches + the cycle branch itself (自坐通根).
    # Labels are built from cycle_label and MUST stay index-aligned with the lists.
    cycle_hide = _cycle_hidden_stems(cycle_branch)
    rooting = compute_single_stem_rooting(
        get_stem_element(cycle_stem),
        list(ctx.zhis) + [cycle_branch],
        [list(h) for h in ctx.hides] + [cycle_hide],
        _NATAL_PILLAR_KEYS + [f"{cycle_label}柱"],
    )

    hidden = {
        tier: {
            "天干": stem,
            "阴阳": _yin_yang(stem, _YANG_STEMS),
            "五行": LunarUtil.WU_XING_GAN.get(stem, "无"),
            "十神": LunarUtil.SHI_SHEN.get(ctx.effective_day_stem + stem, "无"),
        }
        for tier, stem in zip(_HIDE_TIERS, cycle_hide)
    }

    stem_element = LunarUtil.WU_XING_GAN.get(cycle_stem, "无")
    branch_element = LunarUtil.WU_XING_ZHI.get(cycle_branch, "无")

    pillar = {
        "天干": {
            "天干": cycle_stem,
            "阴阳": _yin_yang(cycle_stem, _YANG_STEMS),
            "五行": stem_element,
            "十神": stem_god,
            "根基强度": rooting["根基强度"],
            "通根于": rooting["通根于"],
        },
        "地支": {
            "地支": cycle_branch,
            "阴阳": _yin_yang(cycle_branch, _YANG_BRANCHES),
            "五行": branch_element,
        },
        "藏干": hidden,
        "十二长生": {
            # 日干-relative stage uses the RAW day stem — same convention as the
            # natal library stages (bazi.getXxxDiShi), even under 化气格.
            "日干": _self_seated_stage(ctx.day_stem, cycle_branch),
            "自坐": _self_seated_stage(cycle_stem, cycle_branch),
        },
        "纳音": LunarUtil.NAYIN.get(cycle_stem + cycle_branch, "无"),
        "空亡": _void_block(cycle_branch, cycle_xun_kong, ctx, cycle_label),
        # Seasonal state vs the NATAL month branch (the chart's climate anchor).
        "季节状态": {
            "天干": _STATE_DESCRIPTIONS.get(ctx.seasonal.states.get(stem_element, "囚")),
            "地支本气": _STATE_DESCRIPTIONS.get(ctx.seasonal.states.get(branch_element, "囚")),
        },
    }

    zhi_hua = _zhi_hua_annotation(stem_god, ctx)
    if zhi_hua:
        pillar["制化"] = zhi_hua

    return pillar
