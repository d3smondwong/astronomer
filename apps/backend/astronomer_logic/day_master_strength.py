"""
Day Master Strength (日主 strength) Module

Standalone calculation module for BaZi Day Master analysis.
Also serves as the canonical source for shared BaZi constants imported by
wu_xing.py and natal_interactions.py.

Key Exports (shared constants):
    HIDDEN_STEM_MULTIPLIER, VISIBLE_STEM_MULTIPLIER  — seasonal multiplier tables
    SeasonalFactors, get_seasonal_factors()          — seasonal strength system
    BRANCH_HIDDEN_STEM_ROOTING                       — hidden stem weight table (single source of truth)
    get_stem_element()                               — delegates to LunarUtil.WU_XING_GAN

Main Function:
    get_day_master_strength(bazi, pillars, ten_gods, natal_interactions, pillar_void=None) → dict

    pillar_void (optional): result of check_pillar_void_status(). When the Day Branch falls
    into the Month or Hour Pillar's void pair (被月柱空 / 被时柱空), the Day Branch's rooting
    contribution to 得地 is nullified. Voided by Year (被年柱空) is ignored per classical rule —
    ancestral emptiness does not weaken the self's core vitality.

Output structure:
    {
        "日主": {
            "天干": "癸",
            "五行": "火",        # transformed element if 化气格; original otherwise
            "阴阳": "阴",
            "十二长生": "墓",
            "得令": { "状态": str, "分数": float },         # graded 旺4 相3 休1.5 囚1 死0 (+1 得生)
            "得地": { "通根": str, "分数": float },          # 分数: 0 | 1.0 | 2.0 | 4.0
            "得势": { "得势层级": str, "分数": float },      # 分数: 0 | 1.0 | 2.0 | 4.0
            "强弱分数": float,   # weighted 0–4: 得令×40% + 得地×30% + 得势×17.5% + combo×12.5%
            "强弱": "极旺"|"旺"|"中和"|"弱"|"极弱",
        }
    }
"""

from dataclasses import dataclass
from typing import Dict, List
from lunar_python.util import LunarUtil
from apps.backend.astronomer_logic.bazi_pillars import _YANG_STEMS
from apps.backend.astronomer_logic.wu_xing_relations import (
    CONTROLS as _CONTROLS,
    GENERATES as _GENERATES,
)

# ─────────────────────────────────────────────
# Hidden stems — single source of truth
# Derived from 三命通会; order = 本气, 中气, 余气
# ─────────────────────────────────────────────

BRANCH_HIDDEN_STEM_ROOTING: dict[str, list[tuple[str, float]]] = {
    "子": [("癸", 1.0)],
    "丑": [("己", 0.6), ("癸", 0.3), ("辛", 0.1)],
    "寅": [("甲", 0.6), ("丙", 0.3), ("戊", 0.1)],
    "卯": [("乙", 1.0)],
    "辰": [("戊", 0.6), ("乙", 0.3), ("癸", 0.1)],
    "巳": [("丙", 0.6), ("庚", 0.3), ("戊", 0.1)],
    "午": [("丁", 0.7), ("己", 0.3)],
    "未": [("己", 0.6), ("丁", 0.3), ("乙", 0.1)],
    "申": [("庚", 0.6), ("壬", 0.3), ("戊", 0.1)],
    "酉": [("辛", 1.0)],
    "戌": [("戊", 0.6), ("辛", 0.3), ("丁", 0.1)],
    "亥": [("壬", 0.7), ("甲", 0.3)],
}


def get_stem_element(stem: str) -> str:
    """Get element for a heavenly stem using lunar-python library."""
    return LunarUtil.WU_XING_GAN[stem]


_ROOT_DEPTH_LABELS: list[str] = ["本气根", "中气根", "余气根"]

_STATE_DESCRIPTIONS: dict = {
    "旺": "旺 (最强)",
    "相": "相 (次强)",
    "囚": "囚 (弱)",
    "休": "休 (气弱)",
    "死": "死 (极弱)",
}

# ─────────────────────────────────────────────
# Seasonal factors  (exported — used by wu_xing, natal_interactions)
# ─────────────────────────────────────────────

HIDDEN_STEM_MULTIPLIER: Dict[str, float] = {
    "旺": 1.00,
    "相": 0.80,
    "休": 0.60,
    "囚": 0.40,
    "死": 0.20,
}

VISIBLE_STEM_MULTIPLIER: Dict[str, float] = {
    "旺": 1.00,
    "相": 0.80,
    "休": 0.60,
    "囚": 0.50,
    "死": 0.40,
}

# Refactor this for full 12 month Grid.
_SEASONAL_TABLE: dict = {
    "spring": {"木": "旺", "火": "相", "土": "死", "金": "囚", "水": "休"},
    "summer": {"木": "休", "火": "旺", "土": "相", "金": "死", "水": "囚"},
    "autumn": {"木": "死", "火": "囚", "土": "休", "金": "旺", "水": "相"},
    "winter": {"木": "相", "火": "死", "土": "囚", "金": "休", "水": "旺"},
}

_BRANCH_ELEMENT = {
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
    "子": "水",
    "丑": "土",
}

_SPRING_BRANCHES = frozenset({"寅", "卯", "辰"})
_SUMMER_BRANCHES = frozenset({"巳", "午", "未"})
_AUTUMN_BRANCHES = frozenset({"申", "酉", "戌"})
_WINTER_BRANCHES = frozenset({"亥", "子", "丑"})


@dataclass
class SeasonalFactors:
    season: str
    states: Dict[str, str]

    def multiplier_hidden_stems(self, element: str) -> float:
        """Seasonal multiplier for hidden stems — full range 0.20 to 1.00."""
        return HIDDEN_STEM_MULTIPLIER.get(self.states.get(element, "囚"), 0.40)

    def multiplier_visible_stems(self, element: str) -> float:
        """Seasonal multiplier for a visible (transparent) heavenly stem."""
        return VISIBLE_STEM_MULTIPLIER.get(self.states.get(element, "囚"), 0.50)


def get_seasonal_factors(month_branch: str) -> SeasonalFactors:
    """Map month branch → SeasonalFactors for all five elements."""
    if month_branch in _SPRING_BRANCHES:
        season = "spring"
    elif month_branch in _SUMMER_BRANCHES:
        season = "summer"
    elif month_branch in _AUTUMN_BRANCHES:
        season = "autumn"
    else:
        season = "winter"
    return SeasonalFactors(season=season, states=_SEASONAL_TABLE[season])


# ─────────────────────────────────────────────
# Scoring constants
# ─────────────────────────────────────────────

# 得令 quantitative scores — GRADED, following the classical ordering 旺 > 相 > 休 > 囚 > 死.
#
# These were {旺:4, 相:2, 休:0, 囚:0, 死:0} — collapsing THREE distinct states into a single
# zero, in the term that carries the most weight. 休 (the DM generates the ruler — merely
# drained) is not the same condition as 死 (the ruler controls the DM — actively attacked),
# and flattening them discarded real signal: 55% of charts scored 得令 0, which is why half
# of all charts came out 极弱.
#
#   相 raised 2 → 3: 相 is the element the ruler generates — "prime minister", next in line.
#                    Scoring it at half of 旺 undervalued it.
#   死 stays 0:      得令 measures SEASONAL SUPPORT, and a season that is controlling the day
#                    master supplies none. A nonzero floor would hand credit to charts with
#                    genuinely nothing (甲 in 酉月: pure 辛金, no 印, no root) purely to flatter
#                    the average. Strength for a 死-month chart must come from real 通根 /
#                    党众 / 局 — which, after Phases 1–2, it now can.
_SEASONAL_SCORES: dict[str, float] = {"旺": 4.0, "相": 3.0, "休": 1.5, "囚": 1.0, "死": 0.0}

# Ten-god categories for 得势 analysis
_SUPPORTING_GODS: frozenset = frozenset({"比肩", "劫财", "偏印", "正印"})
_OPPOSING_GODS: frozenset = frozenset({"正官", "七杀"})
_DRAINING_GODS: frozenset = frozenset({"食神", "伤官", "正财", "偏财"}) # Not used due to else state, but defined for clarity

# ── 燥土 / 湿土 — the four earth branches are NOT equivalent roots for an EARTH day master ──
#
# For 木/火/金/水 a 墓库 root is ALREADY scored 0.1 (余气) by the table above — "stored qi is
# weak" is baked in. The over-credit exists only for a 土 day master, where 辰戌丑未 本气 土
# scores a full 0.6 apiece. And 辰/丑 are not even 戊's 墓 (戌 is): for 土 these are its own
# seats (土旺四季). So the weakness is not structural 墓库 — it is CLIMATIC, and the branches
# say so themselves:
#
#     燥土 未 / 戌  — carry 丁火. Warm, dry. Sound footing.
#     湿土 辰 / 丑  — carry 癸水. Waterlogged; in a WINTER month, 冻土 — frozen solid.
#
# 墓库根，如物之入库，虽存而无力 — a vault root exists but cannot act. Frozen wet earth is
# present on the chart and inert in practice, which is exactly why 戊 born in 亥 has 调候
# 甲丙: 丙 to thaw the ground and 甲 to break it open. Scoring 丑/辰 at full 本气 weight in a
# water month credits the day master with a foundation the classics say cannot hold him up.
#
# This is 身弱 caused BY 寒湿 — the two axes are orthogonal, and this is where they meet.
_WET_EARTH = frozenset({"辰", "丑"})            # hold 癸水
_COLD_MONTHS = frozenset({"亥", "子", "丑"})     # winter — 冻土
_WET_EARTH_FACTOR = 0.7                         # 湿土: soft, waterlogged footing
_FROZEN_EARTH_FACTOR = 0.5                      # 冻土: present but inert


def earth_root_factor(branch: str, day_elem: str, month_branch: str) -> float:
    """Potency multiplier for an EARTH day master's 土 qi in a 湿土 branch (辰/丑).

    Returns 1.0 for every other day master and for the 燥土 branches (未/戌) — this narrows
    strictly to the one case the weight table over-credits. Applied to 得地 (can it root me?)
    AND 得势 (can it stand with me?): earth too frozen to root is equally too frozen to ally.
    """
    if day_elem != "土" or branch not in _WET_EARTH:
        return 1.0
    return _FROZEN_EARTH_FACTOR if month_branch in _COLD_MONTHS else _WET_EARTH_FACTOR


# 得地 root depth thresholds on raw weighted score (evaluated top-down)
_ROOT_DEPTH_THRESHOLDS: list[tuple[float, str]] = [
    (1.2, "深根"),
    (0.6, "中根"),
    (0.1, "浅根"),
]

# Root depth → 0–4 score contribution (matches 得令 scale)
_ROOT_DEPTH_SCORES: dict[str, float] = {
    "深根": 4.0,
    "中根": 2.0,
    "浅根": 1.0,
    "无根": 0.0,
}

# 得势 tier thresholds on linear score (evaluated top-down; fallback = 失势)
_DE_SHI_TIERS: list[tuple[float, str]] = [
    (2.0, "强"),
    (1.0, "中"),
    (0.01, "弱"),
]

# 得势 tier → 分数 (mirrors 得令/得地 scale)
_DE_SHI_SCORES: dict[str, float] = {
    "强": 4.0,
    "中": 2.0,
    "弱": 1.0,
    "失": 0.0,
}

# Month branch seasonal power downgrade from 六冲
_SEASONAL_DOWNGRADE: dict[str, str] = {
    "旺": "相",
    "相": "休",
    "休": "死",
    "囚": "死",
    "死": "死",
}

# Final 强弱 verdict thresholds on weighted 0–4 total score (evaluated top-down)
# Weights: 得令 50%, 得地 25%, 得势 12.5%, Combo 12.5%
_STRENGTH_VERDICTS: list[tuple[float, str]] = [
    (3.2, "极旺"),
    (2.4, "旺"),
    (1.6,  "中和"),
    (0.8, "弱"),
    (0.0,  "极弱"),
]

_PILLAR_LABELS = ["年柱", "月柱", "日柱", "时柱"]


def _classify_for_dm(elem: str, day_elem: str) -> str:
    """Map a five-element string to its support category relative to the Day Master."""
    if elem == day_elem:
        return "supporting"  # same element (比/劫)
    if _GENERATES.get(elem) == day_elem:
        return "supporting"  # generates DM (印)
    if _CONTROLS.get(elem) == day_elem:
        return "opposing"  # controls DM (官/杀)
    if _CONTROLS.get(day_elem) == elem:
        return "draining"  # DM controls (财)
    if _GENERATES.get(day_elem) == elem:
        return "draining"  # DM generates (食/伤)
    return "neutral"


# ─────────────────────────────────────────────
# Core calculation functions
# ─────────────────────────────────────────────


def apply_interactions(
    day_elem: str,
    month_branch: str,
    natal_interactions: dict,
) -> dict:
    """
    Derives interaction-based adjustments for Day Master strength.

    Priority tiers (higher tier overrides lower for shared branches):
      Tier 0: 三会  — +4.0 if matches DM, +2.0 if generates DM
      Tier 1: 三合  — +3.0 if matches DM, +1.5 if generates DM
      Tier 2: 六冲  — nullifies branch roots; downgrades month seasonal power
      Tier 3: 六合  — +0.5 if result element matches DM
      Tier 4: 半合  — +1.0 if partial-triad element matches DM

    Returns:
        {
            "组合加分": float,
            "冲克消根支": list[str],  # branches nullified by 六冲
            "月令降级": str | None,   # downgraded seasonal state if month clashed
            "已合支": list[str],      # branches consumed by 三会/三合
            "活跃互动": list[str],    # human-readable summaries
        }
    """
    unique: list[dict] = natal_interactions.get("作用", {}).get("柱位动态", [])

    consumed: set[str] = (
        set()
    )  # branches in combos — excluded from individual root calc
    clashed: set[str] = set()  # branches in 六冲/天克地冲 — roots nullified
    combo_bonus: float = 0.0
    month_degraded: str | None = None
    summaries: list[str] = []

    stem_cancelled: set[str] = set()  # pillar labels whose stem is neutralised
    stem_weakened: set[str] = set()  # pillar labels whose stem contribution is halved
    stem_combined: dict = {}  # pillar label → {"合化元素": elem} for full 合化
    dm_hua_qi_ge: dict | None = None  # set when 化气格 involves the day master
    vault_opened: dict[str, str] = {}  # branch char → released stem char (冲开/刑开 only)

    # natal_interactions already de-conflicts overlapping interactions via apply_bazi_master_priority,
    # so we trust the output and assign scores directly without re-checking priority.
    for ix in unique:
        if ix.get("强度") == "消融吸收":
            continue  # fully absorbed by a higher-priority interaction; skip

        ix_type = ix.get("类型", "")
        elem = ix.get("元素", "")
        branches = set(ix.get("组合明细", {}).values())

        # 已合支 (consumed) strips a branch's rooting contribution in compute_de_di. That is
        # right ONLY when the combo transmutes the branches into a DIFFERENT element:
        # 申子辰 三合水局 genuinely consumes 辰's 乙木 余气 into 水, so 辰 can no longer root
        # a 甲 day master.
        #
        # It is BACKWARDS when the combo IS the day master's own element. 寅卯辰 三会东方木
        # does not stop those branches being wood — it makes them MORE wood. Consuming them
        # deleted 得地 (weight 25%) and repaid it only through combo_bonus (12.5%), a net
        # LOSS: completing the strongest possible formation scored WEAKER than leaving it as
        # two loose roots. That inverted 滴天髓's 活法 case — 甲木 born 申月 with 支成寅卯辰 is
        # 身旺 — into a 弱 verdict, and is why no 失令 chart could ever reach 旺.
        #
        # Corroboration: 六合/半合 below never consumed, so WEAKER formations were already
        # being treated better than the strongest one. A 局 is more than the sum of its
        # roots, not a substitute for them — so same-element combos now keep their roots and
        # the bonus rides on top.
        if ix_type == "三会":
            if elem == day_elem:
                combo_bonus += 4.0
                summaries.append(f"三会{elem}局 (+4.0)")
            elif _GENERATES.get(elem) == day_elem:
                combo_bonus += 2.0
                consumed |= branches
                summaries.append(f"三会{elem}生{day_elem} (+2.0)")

        elif ix_type == "三合":
            if elem == day_elem:
                combo_bonus += 3.0
                summaries.append(f"三合{elem}局 (+3.0)")
            elif _GENERATES.get(elem) == day_elem:
                combo_bonus += 1.5
                consumed |= branches
                summaries.append(f"三合{elem}生{day_elem} (+1.5)")

        elif ix_type in ("六冲", "天克地冲"):
            clashed |= branches
            summaries.append(f"{ix_type}({'−'.join(sorted(branches))}): 消根")
            if ix_type == "天克地冲":
                # stem component is 天干冲 (mutual) — both pillars' stems cancel each other
                for pillar_label in ix.get("组合明细", {}).keys():
                    stem_cancelled.add(pillar_label)

        elif ix_type == "六合":
            if elem == day_elem:
                combo_bonus += 0.5
                summaries.append(f"六合{elem} (+0.5)")

        elif ix_type == "半合":
            if elem == day_elem:
                combo_bonus += 1.0
                summaries.append(f"半合{elem} (+1.0)")

        elif ix_type == "天干合":
            forma = ix.get("形态", "")
            if forma == "化气格":
                dm_hua_qi_ge = {"合化元素": elem}
                for pillar_label in ix.get("组合明细", {}).keys():
                    stem_combined[pillar_label] = {"合化元素": elem}
                summaries.append(f"化气格{elem} (日主化气)")
            elif forma == "合化":
                for pillar_label in ix.get("组合明细", {}).keys():
                    stem_combined[pillar_label] = {"合化元素": elem}
                summaries.append(f"天干合化{elem} (合化)")
            else:
                # 假化 / 合绊 / 遥合 → stems neutralised, no element change
                for pillar_label in ix.get("组合明细", {}).keys():
                    stem_cancelled.add(pillar_label)
                summaries.append(f"天干合{elem} ({forma}，双干消效)")

        elif ix_type == "天干克":
            controller = ix.get("主动方", "")
            for pillar_label in ix.get("组合明细", {}).keys():
                if pillar_label != controller:
                    stem_weakened.add(pillar_label)
            summaries.append(f"天干克: {controller}克对方 (受克半效)")

        elif ix_type == "天干冲":
            for pillar_label in ix.get("组合明细", {}).keys():
                stem_cancelled.add(pillar_label)
            summaries.append(f"天干冲: 相互消除")

    # Vault-opening supersedes standard clash-nullification for those branches.
    # Only 冲开/刑开 need a root override — 透干开 roots already count at full weight.
    for vs in natal_interactions.get("作用", {}).get("库位状态", []):
        if vs.get("是否开库") and any(m in ("冲开", "刑开") for m in vs.get("开库机制", [])):
            vault_opened[vs["库支"]] = vs["释放"]
    clashed -= set(vault_opened.keys())

    # Downgrade month seasonal power if month branch was clashed
    if month_branch in clashed:
        sf = get_seasonal_factors(month_branch)
        current = sf.states.get(day_elem, "囚")
        month_degraded = _SEASONAL_DOWNGRADE[current]
        summaries.append(f"月令{current}→{month_degraded} (冲降级)")

    return {
        "组合加分": round(combo_bonus, 2),
        "冲克消根支": sorted(clashed),
        "月令降级": month_degraded,
        "已合支": sorted(consumed),
        "天干调整": {
            "消除天干": sorted(stem_cancelled),
            "受克天干": sorted(stem_weakened),
            "合化天干": stem_combined,
        },
        "日主化气格": dm_hua_qi_ge,
        "库开支": vault_opened,
        "活跃互动": summaries,
    }


def compute_de_ling(
    day_elem: str, month_branch: str, natal_interactions_transformation: dict
) -> dict:
    """
    得令: Does the Day Master receive seasonal authority from the month branch?

    得令 = effective month branch state is 旺 or 相 for DM element.
    得生 = month branch's earthly element produces the DM element.
    Downgrade from natal_interactions_transformation["月令降级"] (六冲/天克地冲 on month branch) is applied here.

    Returns { "得令": bool, "得生": bool, "状态": str, "分数": int }
    """
    sf = get_seasonal_factors(month_branch)
    state = sf.states.get(day_elem, "囚")

    # Classical 得生: month branch's own element generates Day Master
    month_elem = _BRANCH_ELEMENT.get(month_branch, "")
    de_sheng = (_GENERATES.get(month_elem) == day_elem) if month_elem else False

    # Use clashed-downgraded state if present; fall back to natural seasonal state
    effective_state = natal_interactions_transformation.get("月令降级") or state
    de_ling = effective_state in ("旺", "相")
    score = _SEASONAL_SCORES[effective_state]

    if de_sheng and not de_ling:
        score += 1

    return {
        # "得令": de_ling,
        # "得生": de_sheng,
        "状态": _STATE_DESCRIPTIONS.get(effective_state),
        "分数": score,
    }


def compute_de_di(
    day_elem: str,
    all_branches: list[str],
    natal_interactions_transformation: dict,
    void_excluded_day_branch: bool = False,
    vault_opened: dict[str, str] | None = None,
) -> dict:
    """
    得地: Does the Day Master element appear as hidden stems in the four branches?

    Branch rooting is absolute — raw BRANCH_HIDDEN_ROOTING weights used directly
    (no seasonal multiplier; rooting strength does not change with season).
    Branches clashed or consumed by combos (from natal_interactions_transformation) contribute 0 to raw rooting.
    Returns:
        {
            "通根": str,   # tier: 深根|中根|浅根|无根
            "分数": float, # 0 | 1.0 | 2.0 | 4.0 (rooting only; combo bonus added by caller)
        }
    """
    # 1. Derive exclusions from interaction adjustments.
    # "冲克消根支": list of branches nullified by clash (六冲/天克地冲).
    # "已合支": list of branches consumed by 三会 or 三合 (they also lose root contribution).
    excluded = set(natal_interactions_transformation.get("冲克消根支", [])) | set(
        natal_interactions_transformation.get("已合支", [])
    )
    root_score = 0.0  # Accumulator for total root weight across all branches
    detail = {}  # Stores per-pillar root info for debugging/transparency

    # all_branches is ordered [年, 月, 日, 时] — the 月令 governs whether 湿土 is merely wet
    # or frozen solid (see earth_root_factor).
    month_branch = all_branches[1] if len(all_branches) > 1 else ""

    # 2. Iterate through each of the four pillars (year, month, day, hour)
    for branch, label in zip(all_branches, _PILLAR_LABELS):
        # 2a. If this branch is excluded (clashed or consumed by a higher-tier combo),
        #     skip root calculation entirely and record zero contribution.
        if branch in excluded:
            detail[label] = {"根类": "无根", "贡献": 0.0, "备注": "冲/合消根"}
            continue

        # Classical void rule: Day Branch voided by Month or Hour Pillar loses its root.
        # Voided by Year is ignored — ancestral emptiness does not weaken the self.
        if void_excluded_day_branch and label == "日柱":
            detail[label] = {"根类": "无根", "贡献": 0.0, "备注": "空亡消根"}
            continue

        # Vault-opening (冲开/刑开): the vault is disrupted but not destroyed.
        # The treasure stem is released at half the 余气 weight if it matches the DM element.
        # (透干开 vaults are not in vault_opened — their roots count at full weight below.)
        if vault_opened and branch in vault_opened:
            released_stem = vault_opened[branch]
            released_elem = get_stem_element(released_stem)
            if released_elem == day_elem:
                yu_qi_weight = BRANCH_HIDDEN_STEM_ROOTING[branch][-1][1]
                partial = round(yu_qi_weight * 0.5, 2)
                root_score += partial
                detail[label] = {"根类": "余气根(库开)", "贡献": partial, "备注": "库开释放"}
            else:
                detail[label] = {"根类": "无根", "贡献": 0.0, "备注": "库开非我用"}
            continue

        # 2b. Prepare per-branch variables
        found_root = "无根"  # Will become "本气根", "中气根", or "余气根"
        contribution = 0.0  # Weight of the strongest matching hidden stem

        # 2c. Get the list of hidden stems for this branch.
        #     BRANCH_HIDDEN_STEM_ROOTING is a dict: branch -> list of (stem, weight)
        #     Example: "寅" -> [("甲", 0.6), ("丙", 0.3), ("戊", 0.1)]
        hidden_stem_list = BRANCH_HIDDEN_STEM_ROOTING[branch]

        # 2d. Scan hidden stems in order (本气 first, then 中气, then 余气)
        for idx, (stem, weight) in enumerate(hidden_stem_list):
            # Convert stem character to its five-element (e.g., "甲" → "木")
            stem_elem = get_stem_element(stem)

            # If this hidden stem's element matches the Day Master's element,
            # and we have a label for this depth index (0,1,2), take it.
            if stem_elem == day_elem and idx < len(_ROOT_DEPTH_LABELS):
                found_root = _ROOT_DEPTH_LABELS[idx]  # e.g., "本气根"
                # 湿土/冻土: a 土 day master rooting in 辰/丑 gets less than the raw 本气
                # weight — waterlogged, and inert outright in a winter month. See
                # earth_root_factor. Every other case multiplies by 1.0.
                factor = earth_root_factor(branch, day_elem, month_branch)
                contribution = round(weight * factor, 3)
                root_score += contribution
                if factor < 1.0:
                    found_root += "(冻土)" if month_branch in _COLD_MONTHS else "(湿土)"
                break  # stop at first (strongest) match per branch

        # 2e. Store per-pillar result for later inspection
        detail[label] = {"根类": found_root, "贡献": round(contribution, 2)}

    # 3. Determine the overall "root depth" category based on the sum of weights.
    tier = next(
        (name for thresh, name in _ROOT_DEPTH_THRESHOLDS if root_score >= thresh),
        "无根",
    )

    tier_score = _ROOT_DEPTH_SCORES[tier]

    return {
        # "得地": tier_score > 0,
        "通根": tier,
        "分数": round(tier_score, 2),
        # "详情": detail,
    }


def compute_de_shi(
    day_elem: str,
    ten_gods: dict,
    pillars: dict,
    natal_interactions_transformation: dict,
) -> dict:
    """
    得势 (党众): is the Day Master surrounded by allies — in the STEMS and in the BRANCHES?

    势 classically means 党众 (one's party), which lives in both halves of the chart. This
    function used to read the three heavenly stems ONLY, which left a hole big enough to
    invert real charts:

      • 得地 counts only the DM's OWN element in the branches (比劫 roots).
      • 得势 counted only the stems.
      ⇒ 印星 hidden in the BRANCHES was invisible to every foundation. 丙 born in 亥月 could
        not see the 甲 inside 亥 — even though 穷通宝鉴's own 丙亥 entry turns on it
        ("得见甲戊庚出干，可云科甲") and 亥 is 甲's 长生. The engine scored it 得令 0 (死),
        得地 0 (no 火 in 亥), 得势 0 (stems only) — nothing, from a month that genuinely feeds it.

    So the branch 藏干 are now read too, using the existing BRANCH_HIDDEN_STEM_ROOTING
    weights. Those weights (本气 .6 / 中气 .3 / 余气 .1) already encode how exposed a hidden
    stem is, so hidden support is naturally discounted against a visible stem (1.0) — no
    invented factor is needed.

    Both 印 AND 比劫 藏干 count. 得地 SATURATES (深根 = 4.0 for one root or three), so 通根
    (a quality question — do I have a root?) and 党众 (a quantity one — how many allies?)
    are different measurements, not the same one twice.

    Accounting is SYMMETRIC: branch 印/比劫 add, branch 官杀/财/食伤 subtract, on the same
    terms as the stems. Counting only the allies would inflate every chart.
    Branches nullified by 冲 or transmuted by a combo (已合支) are skipped, exactly as 得地
    skips them — a root that is dead for rooting is dead for support too.

    Applies stem-level interaction adjustments from natal_interactions_transformation["天干调整"]:
      - 消除天干: neutralised stems (天干冲, 天克地冲, 合而不化) → skipped
      - 受克天干: controlled stems (天干克 target) → weight 0.5
      - 合化天干: fully transformed stems (天干合 合化) → reclassify by new element

    Returns:
        {
            "得势层级": str,  # "强"|"中"|"弱"|"失"
            "分数": float,   # 0 | 1.0 | 2.0 | 4.0
        }
    """
    adj = natal_interactions_transformation.get("天干调整", {})
    cancelled = set(adj.get("消除天干", []))
    weakened = set(adj.get("受克天干", []))
    combined = adj.get("合化天干", {})

    supporting: list = []
    opposing: list = []
    draining: list = []

    for pillar in ("年柱", "月柱", "时柱"):
        stem = pillars.get(pillar, {}).get("天干", "")
        tg = ten_gods.get(pillar, {}).get("天干十神", "")

        if not tg or pillar in cancelled:
            continue

        if pillar in combined:
            new_elem = combined[pillar]["合化元素"]
            category = _classify_for_dm(new_elem, day_elem)
            entry = {"天干": stem, "十神": tg, "合化": new_elem}
        else:
            if tg in _SUPPORTING_GODS:
                category = "supporting"
            elif tg in _OPPOSING_GODS:
                category = "opposing"
            else:
                category = "draining"
            entry = {"天干": stem, "十神": tg}

        weight = 0.5 if pillar in weakened else 1.0
        entry["权重"] = weight
        if category == "supporting":
            supporting.append(entry)
        elif category == "opposing":
            opposing.append(entry)
        else:
            draining.append(entry)

    # ── 地支党众: the 藏干 of all four branches ────────────────────────────────────
    # Skip branches the interaction layer has already killed (clashed) or transmuted into
    # another element (已合支) — the same exclusions compute_de_di honours.
    dead_branches = set(
        natal_interactions_transformation.get("冲克消根支", [])
    ) | set(natal_interactions_transformation.get("已合支", []))

    month_branch = pillars.get("月柱", {}).get("地支", "")

    for pillar in _PILLAR_LABELS:
        branch = pillars.get(pillar, {}).get("地支", "")
        if not branch or branch in dead_branches:
            continue
        # 湿土/冻土 applies here too: earth too frozen to ROOT the day master is equally too
        # frozen to STAND WITH it. Applying the discount to 得地 alone would let the same
        # inert 丑/辰 come back as full-strength 比劫 through the 党众 door.
        factor = earth_root_factor(branch, day_elem, month_branch)
        for hidden_stem, raw_weight in BRANCH_HIDDEN_STEM_ROOTING.get(branch, []):
            stem_elem = get_stem_element(hidden_stem)
            category = _classify_for_dm(stem_elem, day_elem)
            # only the DM's own (inert) 土 qi is discounted — 印/官杀/财 in that branch are
            # unaffected by whether the EARTH can hold the day master up.
            weight = raw_weight * factor if stem_elem == day_elem else raw_weight
            if category == "supporting":
                # 比劫 AND 印 both count. It is tempting to skip 比劫 here as "already in
                # 得地", but that is wrong: 得地 SATURATES — 深根 is 4.0 whether the DM has one
                # root or three. 通根 asks a quality question (do I have a root at all?);
                # 党众 asks a quantity one (how many allies stand with me?). They are not the
                # same measurement, and skipping 比劫 made a day master sitting in a full
                # 三会 of its OWN element score 得势 = 失 — no party, while standing in it.
                supporting.append({"藏干": hidden_stem, "支": branch, "权重": weight})
            elif category == "opposing":
                opposing.append({"藏干": hidden_stem, "支": branch, "权重": weight})
            elif category == "draining":
                draining.append({"藏干": hidden_stem, "支": branch, "权重": weight})

    w_sup = sum(e.get("权重", 1.0) for e in supporting)
    w_opp = sum(e.get("权重", 1.0) for e in opposing)
    w_drn = sum(e.get("权重", 1.0) for e in draining)

    # For 得势, supporting allies contribute positively, while opposing and draining ones detract.
    linear = round(max(w_sup - w_opp * 0.5 - w_drn * 0.3, 0.0), 2)
    tier = next((name for thresh, name in _DE_SHI_TIERS if linear >= thresh), "失")
    de_shi = tier in ("强", "中")

    return {
        # "得势": de_shi,
        "得势层级": tier,
        # "支持天干": supporting,
        # "反对天干": opposing,
        # "耗泄天干": draining,
        "分数": _DE_SHI_SCORES[tier],
    }


# ─────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────


def get_day_master_strength(
    bazi,
    pillars: dict,
    ten_gods: dict,
    natal_interactions: dict,
    pillar_void: dict | None = None,
) -> dict:
    """
    Compute full Day Master strength analysis.

    Args:
        bazi:               EightChar object from lunar_birthday.getEightChar()
        pillars:            Pre-computed pillar data from get_bazi_pillars()
        ten_gods:           Already-transformed ten gods from apply_heavenlystem_tranformation_tengods()
        natal_interactions: Pre-computed interactions from get_natal_interactions()
        pillar_void:        Optional result of check_pillar_void_status(). When provided,
                            Day Branch voided by Month or Hour Pillar loses its 得地 root
                            contribution. Voided by Year is ignored (classical rule).

    If 化气格 is detected in natal_interactions, the day master's effective element is
    overridden to the transformed element before computing 得令, 得地, and 得势.

    Returns { "日主": { ... } } — see module docstring for full shape.
    """
    day_stem = bazi.getDayGan()
    month_branch = bazi.getMonthZhi()
    all_branches = [
        bazi.getYearZhi(),
        bazi.getMonthZhi(),
        bazi.getDayZhi(),
        bazi.getTimeZhi(),
    ]

    day_elem = get_stem_element(day_stem)
    yin_yang = "阳" if day_stem in _YANG_STEMS else "阴"
    sheng_wang = bazi.getDayDiShi()  # self-seated life stage via lunar-python

    # ── Step 1: interaction adjustments ──────────────────────────────────────
    natal_interactions_transformation = apply_interactions(
        day_elem, month_branch, natal_interactions
    )

    # If 化气格 occurred, the day master's effective element changes to the transformed element.
    dm_hua = natal_interactions_transformation.get("日主化气格")
    if dm_hua:
        day_elem = dm_hua["合化元素"]

    # ── Steps 2–4: each compute function owns its own scoring ────────────────
    de_ling = compute_de_ling(day_elem, month_branch, natal_interactions_transformation)

    # Classical void rule: Day Branch voided by Month or Hour Pillar reduces 得地.
    # Voided by Year is ignored — year represents ancestral roots, not the self's vitality.
    day_void_info = (pillar_void or {}).get("日柱", {})
    day_branch_void_active = (
        day_void_info.get("被月柱空", "无") != "无"
        or day_void_info.get("被时柱空", "无") != "无"
    )

    # Vault-opened branches (冲开/刑开 only) get partial root credit instead of zero.
    vault_opened = natal_interactions_transformation.get("库开支", {})

    de_di = compute_de_di(
        day_elem, all_branches, natal_interactions_transformation,
        day_branch_void_active, vault_opened,
    )
    de_shi = compute_de_shi(
        day_elem, ten_gods, pillars, natal_interactions_transformation
    )

    # Combo bonus carries its own weight (12.5%) separate from rooting tier (25%)
    de_di_tier = de_di["分数"]
    combo_bonus = natal_interactions_transformation.get("组合加分", 0.0)

    # ── Step 5: weighted aggregate and verdict ────────────────────────────────
    # 得令 40% | 得地 30% | 得势 17.5% | Combo 12.5%
    #
    # Was 50/25/12.5/12.5. At 50%, 得令 was heavy enough that 通根 could NEVER overcome a bad
    # season: an out-of-season day master was capped at 中和 no matter how deeply rooted, and
    # across 3000 real charts not one 失令 chart ever reached 旺. That is a flat contradiction
    # of 滴天髓 — "得时俱为旺论，失时便作衰看，虽是至理，亦有活法" — whose whole point is that a
    # rooted-but-out-of-season chart CAN be 旺.
    #
    # 40/30/17.5/12.5 follows the common modern 子平 split (月令 ~40, 通根 ~30, 党众 ~20). It
    # keeps 月令 the single heaviest term — 提纲 still rules — while leaving 通根 + 党众 + 局
    # enough combined mass to carry a 失令 chart to 旺 when the roots genuinely warrant it.
    # The guard holds: an unrooted 失令 chart still scores ~0 and stays 极弱, so no strength
    # is manufactured — only real 通根 is allowed to count.
    total = round(max(
        de_ling["分数"] * 0.40 +
        de_di_tier      * 0.30 +
        de_shi["分数"]  * 0.175 +
        combo_bonus     * 0.125,
        0.0,
    ), 2)
    verdict = next(
        (label for threshold, label in _STRENGTH_VERDICTS if total >= threshold),
        "极弱",
    )

    return {
        "日主": {
            "天干": day_stem,
            "五行": day_elem,
            "阴阳": yin_yang,
            "十二长生": sheng_wang,
            "得令": de_ling,
            "得地": de_di,
            "得势": de_shi,
            "强弱分数": total,
            "强弱": verdict,
        }
    }

#################################################################################################
# Execution Code
 # python -m apps.backend.astronomer_logic.day_master_strength
#################################################################################################

if __name__ == "__main__":
    import json
    from lunar_python import Solar
    from apps.backend.astronomer_logic.bazi_pillars import get_bazi_pillars
    from apps.backend.astronomer_logic.ten_gods import get_ten_gods, apply_heavenlystem_tranformation_tengods
    from apps.backend.astronomer_logic.void_xun_kong import get_void_xun_kong
    from apps.backend.astronomer_logic.natal_interactions import get_natal_interactions
    from apps.utils.logging import configure_logging, get_logger
    from datetime import datetime as dt
    from apps.backend.astronomer_logic.true_solar_time import get_true_solar_time

    configure_logging()
    logger = get_logger(__name__)

    # ── Subjects ──────────────────────────────────────────────────────────────
    subjects = {
        # "Desmond": (dt(1985, 11, 25, 17, 7, 0), 1.3253, 103.808053, 1),
        "Corinne": (dt(1987,  6,  3, 12, 6, 0),  1.4759,  103.808053, 0),
        # "Lara":    (dt(2025,  7, 31,  9, 10, 0), 1.3253,  103.808053, 0),
    }

    for name, (birthday, lat, lon, gender) in subjects.items():
        logger.info("=" * 60)
        logger.info("Subject: %s  (%s)", name, birthday.strftime("%Y-%m-%d %H:%M"))

        tst_birthday = get_true_solar_time(birthday, lat, lon)
        lunar_birthday = tst_birthday.getLunar()

        _bazi = lunar_birthday.getEightChar()
        _pillars = get_bazi_pillars(_bazi)
        _void = get_void_xun_kong(_bazi)
        _ten_gods = get_ten_gods(_bazi)

        # Enrich 藏干 with 十神 so natal_interactions can read ten gods
        for k in ["年柱", "月柱", "日柱", "时柱"]:
            for tier, info in _pillars[k]["藏干"].items():
                info["十神"] = _ten_gods[k]["藏干十神"][tier]

        _interactions = get_natal_interactions(_pillars, _void)
        _ten_gods, _ = apply_heavenlystem_tranformation_tengods(
            _ten_gods, _pillars, _interactions, _bazi.getDayGan()
        )
        result = get_day_master_strength(_bazi, _pillars, _ten_gods, _interactions)
        logger.info(json.dumps(result, ensure_ascii=False, indent=2))
