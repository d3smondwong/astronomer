"""
Relationship Interpretive Insights

Pre-computes structured BaZi relationship patterns from raw aggregator data and returns
labeled facts for LLM injection across three domains:

  感情    — Romantic partner patterns
  原生家庭 — Family of origin patterns
  朋友人际 — Friendship & peer patterns

Output structure:
    {
        "命盘关系格局": {
            "感情":    [...],   # natal romance patterns
            "原生家庭": [...],  # natal family patterns
            "朋友人际": [...],  # natal friendship patterns
        },
        "大运感情动态": [        # one entry per decade
            {
                "大运":    str,
                "运势":    str,
                "感情":    {"运势": str, "解读": str},
                "原生家庭": {"运势": str, "解读": str},
                "朋友人际": {"运势": str, "解读": str},
            },
            ...
        ],
        "无格局提示": str | None
    }

Usage:
    from src.astronomer_calculations.interpretive_insights_relationships import extract_relationship_insights
    relationship_insights = extract_relationship_insights(raw_data)
"""

from datetime import date

from src.astronomer_calculations.shen_sha import (
    year_earthly_branches_shens,
    day_earthly_branches_shens,
)

# ── Constants ──────────────────────────────────────────────────────────────────

PILLARS = ["年柱", "月柱", "日柱", "时柱"]
BRANCH_TIERS = ["本气", "中气", "余气"]

SEAL_STARS = {"正印", "偏印"}
PEER_STARS = {"比肩", "劫财"}
EXPRESSION_STARS = {"食神", "伤官"}
OFFICIAL_STARS = {"正官", "七杀"}  # spouse star for female DM
WEALTH_STARS = {"正财", "偏财"}  # spouse star for male DM
TOMB_BRANCHES = {"辰", "戌", "丑", "未"}
PEACH_BLOSSOM_BRANCHES = {"子", "午", "卯", "酉"}  # universal 桃花 branches

ACTIVE_STRENGTHS = {"强势主流", "显著影响", "中等影响"}
CLASH_HARM_TYPES = {"六冲", "六害", "六破", "无恩之刑", "恃势之刑", "无礼之刑", "自刑"}
HARMONY_TYPES = {"六合", "三合", "三会"}

# Cycle-specific interaction types (from cycle_interactions.py)
# 六合 (争合) intentionally excluded — contested harmony is not a clean activation
CYCLE_CLASH_TYPES = {"六冲", "六冲 (争冲)", "反吟"}
CYCLE_HARMONY_TYPES = HARMONY_TYPES  # same set; alias for clarity at call sites
CYCLE_STAGNATION_TYPES = {"伏吟"}
CYCLE_VAULT_TYPES = {"开库", "开库 (争库)"}

# Pillar where family-related ten gods matter most
YEAR_PILLAR = "年柱"
MONTH_PILLAR = "月柱"
DAY_PILLAR = "日柱"
HOUR_PILLAR = "时柱"

# Branch → pillar label for interaction lookups
BRANCH_LABEL_TO_PILLAR = {
    "年支": "年柱",
    "月支": "月柱",
    "日支": "日柱",
    "时支": "时柱",
}

# Branches that form 自刑 when the same branch appears twice in the chart
SELF_PUNISHMENT_BRANCHES = {"辰", "午", "酉", "亥"}

# ── Shared helpers ─────────────────────────────────────────────────────────────


def _get_branch_chars(bazi: dict) -> dict:
    ba_zi = bazi["八字"]
    return {
        "年支": ba_zi["年柱"]["地支"],
        "月支": ba_zi["月柱"]["地支"],
        "日支": ba_zi["日柱"]["地支"],
        "时支": ba_zi["时柱"]["地支"],
    }


def _void_branch_positions(branch_chars: dict, xun_kong: dict) -> set:
    """Returns set of branch position keys (e.g. {"月支"}) that fall in their own pillar's 旬空."""
    voided = set()
    for branch_key, branch_char in branch_chars.items():
        pillar_key = branch_key[:1] + "柱"
        xun_kong_str = xun_kong.get("旬空", {}).get(pillar_key, {}).get("旬空", "")
        if branch_char in xun_kong_str:
            voided.add(branch_key)
    return voided


def _pillar_shen_sha(shen_sha: dict, pillar: str) -> list[str]:
    """Returns the list of star names on the given natal pillar."""
    return shen_sha.get("神煞", {}).get("柱位神煞", {}).get(pillar, {}).get("神煞", [])


def _find_star_pillars(shen_sha: dict, star_name: str) -> list[str]:
    """Returns which natal pillars carry the named star."""
    return [p for p in PILLARS if star_name in _pillar_shen_sha(shen_sha, p)]


def _ten_god_positions(shi_shen: dict, god_set: set) -> dict:
    """
    Scans all four pillars for ten gods in god_set.
    Returns {"in_stems": [...], "in_branches": [...], "all": [...]}.
    """
    in_stems, in_branches = [], []
    for pillar in PILLARS:
        p = shi_shen.get(pillar, {})
        if p.get("天干十神") in god_set:
            in_stems.append(pillar[:1] + "干")
        for tier in BRANCH_TIERS:
            if p.get("地支十神", {}).get(tier) in god_set:
                in_branches.append(pillar[:1] + "支" + tier)
    return {
        "in_stems": in_stems,
        "in_branches": in_branches,
        "all": in_stems + in_branches,
    }


def _has_interaction_on_pillar(
    pillar: str, interactions: dict, types: set, strengths: set = ACTIVE_STRENGTHS
) -> bool:
    pillar_data = interactions.get("作用", {}).get("柱位动态", {}).get(pillar, {})
    for tier_items in pillar_data.values():
        for item in tier_items:
            if item.get("类型") in types and item.get("强度") in strengths:
                return True
    return False


def _interaction_types_on_pillar(pillar: str, interactions: dict) -> set[str]:
    types = set()
    pillar_data = interactions.get("作用", {}).get("柱位动态", {}).get(pillar, {})
    for tier_items in pillar_data.values():
        for item in tier_items:
            if item.get("强度") in ACTIVE_STRENGTHS:
                types.add(item.get("类型", ""))
    return types


def _cycle_branch(cycle: dict) -> str:
    return cycle.get("运柱", {}).get("地支", "")


def _cycle_branch_void(cycle: dict) -> bool:
    run_zhu = cycle.get("运柱", {})
    branch = run_zhu.get("地支", "")
    xun_kong_str = run_zhu.get("旬空", "")
    return bool(branch and branch in xun_kong_str)


def _wu_xing_tier(wu_xing: dict, elem: str) -> str:
    return wu_xing.get(elem, {}).get("能级", {}).get("名称", "")


# Element generation and control cycles (for spouse star quality)
_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CONTROLS = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
_ELEM_OF_STEM = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}


# ── Romance natal patterns ─────────────────────────────────────────────────────


def _check_peach_blossom(shen_sha: dict, branch_chars: dict) -> list[dict]:
    patterns = []

    all_peach_pillars = _find_star_pillars(shen_sha, "桃花")
    bath_pillars = _find_star_pillars(shen_sha, "沐浴桃花")

    # Multiple peach blossoms (≥2 pillars) — highest promiscuity signal, check first
    if len(all_peach_pillars) >= 2:
        patterns.append(
            {
                "格局编号": "multiple_peach_blossom",
                "格局名称": "多桃花",
                "解读": "命盘桃花出现于两处或以上，异性缘极旺，四方皆有桃花，感情经历丰富但也容易同时吸引多段感情，专一度较低，需警惕多角关系或感情纠纷。",
                "依据": f"桃花位于: {all_peach_pillars}",
            }
        )

    # 沐浴桃花 (amplified)
    if bath_pillars:
        patterns.append(
            {
                "格局编号": "bath_peach_blossom",
                "格局名称": "沐浴桃花",
                "解读": "桃花坐于日主沐浴之地，魅力天成，异性缘极强。感情来得自然，往往不费力便令人倾心；但也易招来复杂的情感纠葛。",
                "依据": f"沐浴桃花: {bath_pillars}",
            }
        )

    # 墙内桃花 (year / month pillar — stable, domestic)
    inner_pillars = [p for p in all_peach_pillars if p in (YEAR_PILLAR, MONTH_PILLAR)]
    if inner_pillars:
        patterns.append(
            {
                "格局编号": "inner_peach_blossom",
                "格局名称": "墙内桃花",
                "解读": "桃花位于年柱或月柱，感情缘份偏向稳定的长期关系，适合在家庭或熟悉的社交圈中找到伴侣。",
                "依据": f"桃花位于: {inner_pillars}",
            }
        )

    # 墙外桃花 (day / hour pillar — external, potentially unstable)
    outer_pillars = [p for p in all_peach_pillars if p in (DAY_PILLAR, HOUR_PILLAR)]
    if outer_pillars:
        patterns.append(
            {
                "格局编号": "outer_peach_blossom",
                "格局名称": "墙外桃花",
                "解读": "桃花位于日柱或时柱，感情缘份偏向外遇或婚后桃花，情感经历较为复杂，需留意感情的界限与专一度。",
                "依据": f"桃花位于: {outer_pillars}",
            }
        )

    # 日支带桃花 — day branch itself is a universal peach blossom branch (子午卯酉)
    day_branch = branch_chars.get("日支", "")
    if day_branch in PEACH_BLOSSOM_BRANCHES:
        patterns.append(
            {
                "格局编号": "day_branch_peach_blossom",
                "格局名称": "日支坐桃花",
                "解读": "日支本身为桃花之地（子午卯酉），配偶宫天生带桃花气息。本人魅力出众，婚后仍持续吸引异性，伴侣亦可能有相似特质，感情关系中需留意界限。",
                "依据": f"日支({day_branch})为桃花支",
            }
        )

    if (
        not all_peach_pillars
        and not bath_pillars
        and day_branch not in PEACH_BLOSSOM_BRANCHES
    ):
        patterns.append(
            {
                "格局编号": "no_peach_blossom",
                "格局名称": "无桃花",
                "解读": "命盘无桃花星，感情缘份不靠天然吸引力，需主动经营，缘份多因共同目标或稳定交际而来。",
                "依据": "命盘四柱均无桃花星",
            }
        )

    return patterns


def _check_peach_blossom_with_danger(
    shen_sha: dict, shi_shen: dict, wu_xing: dict, dm_elem: str, interactions: dict
) -> list[dict]:
    """桃花带杀 / 带劫 / 印弱 — peach blossom combined with destabilising factors.

    Classical 桃花带杀/带劫 requires the dangerous ten god to be on the same pillar
    as 桃花, or directly interacting with a 桃花 pillar (六合, 三合, etc.).
    """
    patterns = []
    peach_pillars = _find_star_pillars(shen_sha, "桃花") + _find_star_pillars(
        shen_sha, "沐浴桃花"
    )
    if not peach_pillars:
        return patterns

    def _interacts_with_peach(pillar: str) -> bool:
        """True if `pillar` directly interacts with any peach blossom pillar."""
        for item in interactions.get("_raw_priority_list", []):
            if item.get("强度") not in ACTIVE_STRENGTHS:
                continue
            detail = item.get("组合明细", {})
            if pillar in detail and any(pp in detail for pp in peach_pillars):
                return True
        return False

    all_sha = [p for p in PILLARS if shi_shen.get(p, {}).get("天干十神") == "七杀"]
    all_jie = [p for p in PILLARS if shi_shen.get(p, {}).get("天干十神") == "劫财"]

    # Keep only pillars co-located with 桃花 or directly interacting with a 桃花 pillar
    sha_pillars = [p for p in all_sha if p in peach_pillars or _interacts_with_peach(p)]
    jie_pillars = [p for p in all_jie if p in peach_pillars or _interacts_with_peach(p)]

    if sha_pillars:
        patterns.append(
            {
                "格局编号": "peach_blossom_with_sha",
                "格局名称": "桃花带杀",
                "解读": "桃花与七杀同入命盘，感情缘份中带有危险性。所吸引的对象往往强势、控制欲强，感情关系可能伴随纠纷、冲突甚至伤害，需高度警惕偏激或占有型伴侣。",
                "依据": f"桃花: {peach_pillars}；七杀: {sha_pillars}",
            }
        )
    if jie_pillars:
        patterns.append(
            {
                "格局编号": "peach_blossom_with_jie",
                "格局名称": "桃花带劫",
                "解读": "桃花与劫财同入命盘，感情中易有竞争者或被友人介入的风险。感情关系中的第三者往往来自身边熟人，需留意朋友或同伴对感情的干扰，亦有因感情而破财的信号。",
                "依据": f"桃花: {peach_pillars}；劫财: {jie_pillars}",
            }
        )

    # 印星弱 + 桃花 — lack of moral restraint amplifies peach blossom energy
    # 印星 element = element that generates DM (reverse of _GENERATES)
    seal_elem = {v: k for k, v in _GENERATES.items()}.get(dm_elem, "")
    seal_tier = _wu_xing_tier(wu_xing, seal_elem) if seal_elem else ""
    seal_weak = seal_tier in {"极弱", "偏弱"} or not seal_tier
    ip = _ten_god_positions(shi_shen, SEAL_STARS)
    if seal_weak and not ip["all"]:
        patterns.append(
            {
                "格局编号": "weak_seal_promiscuity",
                "格局名称": "印弱桃花旺",
                "解读": "命盘印星缺失或极弱，缺乏道德约束与声誉意识，桃花能量因此得不到节制。感情观趋于自由奔放，对感情界限的重视度偏低，在桃花旺盛的大运中尤需自律。",
                "依据": f"印星: 无；印星元素({seal_elem})旺度: {seal_tier or '无'}；桃花: {peach_pillars}",
            }
        )
    elif seal_weak and ip["all"]:
        patterns.append(
            {
                "格局编号": "weak_seal_promiscuity",
                "格局名称": "印弱桃花旺",
                "解读": "印星虽入命但元素偏弱，对桃花能量的约束力有限。感情表达较为直接，对感情规范的坚守不稳定，桃花旺运时易冲动行事，感情界限需主动维护。",
                "依据": f"印星位置: {ip['all']}；印星元素({seal_elem})旺度: {seal_tier}；桃花: {peach_pillars}",
            }
        )

    return patterns


def _check_marriage_stars(shen_sha: dict) -> list[dict]:
    red_luan_pillars = _find_star_pillars(shen_sha, "红鸾")
    heavenly_joy_pillars = _find_star_pillars(shen_sha, "天喜")

    if red_luan_pillars and heavenly_joy_pillars:
        return [
            {
                "格局编号": "both_marriage_stars",
                "格局名称": "红鸾天喜同现",
                "解读": "红鸾与天喜同入命盘，婚姻喜庆之气极旺。命盘有明确的结婚或喜事信号，感情运与婚姻运均属上乘。",
                "依据": f"红鸾: {red_luan_pillars}；天喜: {heavenly_joy_pillars}",
            }
        ]

    patterns = []
    if red_luan_pillars:
        patterns.append(
            {
                "格局编号": "red_luan_present",
                "格局名称": "红鸾入命",
                "解读": "红鸾入命，主姻缘与感情运良好，有天然的婚配缘份，感情较易开花结果。",
                "依据": f"红鸾位于: {red_luan_pillars}",
            }
        )
    if heavenly_joy_pillars:
        patterns.append(
            {
                "格局编号": "heavenly_joy_present",
                "格局名称": "天喜入命",
                "解读": "天喜入命，主喜庆与欢乐，婚嫁或喜事易在人生关键节点浮现。",
                "依据": f"天喜位于: {heavenly_joy_pillars}",
            }
        )
    return patterns


def _check_isolation_stars(shen_sha: dict) -> list[dict]:
    gu_chen_pillars = _find_star_pillars(shen_sha, "孤辰")
    gua_su_pillars = _find_star_pillars(shen_sha, "寡宿")

    if gu_chen_pillars and gua_su_pillars:
        return [
            {
                "格局编号": "both_isolation_stars",
                "格局名称": "孤辰寡宿并见",
                "解读": "孤辰与寡宿同入命盘，孤独之气较重。感情路上容易感到孤立或遭遇分离，晚婚或独处时间较长的倾向明显。",
                "依据": f"孤辰: {gu_chen_pillars}；寡宿: {gua_su_pillars}",
            }
        ]

    patterns = []
    if gu_chen_pillars:
        patterns.append(
            {
                "格局编号": "gu_chen_present",
                "格局名称": "孤辰入命",
                "解读": "孤辰入命，有一定的孤独倾向，感情路上可能经历较长的单身期或不易找到深度连结的伴侣。",
                "依据": f"孤辰位于: {gu_chen_pillars}",
            }
        )
    if gua_su_pillars:
        patterns.append(
            {
                "格局编号": "gua_su_present",
                "格局名称": "寡宿入命",
                "解读": "寡宿入命，有分离或孤寡倾向，婚姻感情中易有聚少离多、中晚年孤独的信号。",
                "依据": f"寡宿位于: {gua_su_pillars}",
            }
        )
    return patterns


def _check_expression_strength(wu_xing: dict, dm_elem: str) -> list[dict]:
    """食伤旺 — strong expression element signals open/expressive romantic nature."""
    ep_elem = _GENERATES.get(dm_elem, "")
    ep_elem_tier = _wu_xing_tier(wu_xing, ep_elem) if ep_elem else ""
    if ep_elem_tier in {"偏旺", "极旺", "极亢"}:
        return [
            {
                "格局编号": "expression_strong",
                "格局名称": "食伤旺盛",
                "解读": "食伤元素旺盛，感情表达力与魅力出众，对感情与感官体验有强烈的追求，感情观较为开放自由，异性缘旺但也需留意感情界限，避免多段感情同时发展。",
                "依据": f"食伤元素({ep_elem})旺度: {ep_elem_tier}",
            }
        ]
    return []


def _check_day_pillar_quality(
    interactions: dict, xun_kong: dict, branch_chars: dict
) -> list[dict]:
    patterns = []
    day_branch_key = "日支"
    day_branch_char = branch_chars.get(day_branch_key, "")
    void_positions = _void_branch_positions(branch_chars, xun_kong)
    day_types = _interaction_types_on_pillar(DAY_PILLAR, interactions)

    if "六冲" in day_types or any(
        t in day_types for t in {"无恩之刑", "恃势之刑", "无礼之刑"}
    ):
        patterns.append(
            {
                "格局编号": "day_pillar_clashed",
                "格局名称": "日柱受冲",
                "解读": "配偶宫（日柱）受冲克，婚姻关系容易动荡不安，与伴侣之间摩擦较多，关系稳定性受到结构性挑战。",
                "依据": f"日柱互动类型: {sorted(day_types & (CLASH_HARM_TYPES))}",
            }
        )

    if day_branch_key in void_positions:
        patterns.append(
            {
                "格局编号": "day_pillar_void",
                "格局名称": "配偶宫落空",
                "解读": "日支旬空，配偶宫力场虚浮。婚姻或感情关系看似存在，实则缺乏实质根基，伴侣缘份不深，或晚婚、感情有名无实。",
                "依据": f"日支({day_branch_char})落旬空",
            }
        )

    if "六害" in day_types:
        patterns.append(
            {
                "格局编号": "day_pillar_harmed",
                "格局名称": "日柱六害",
                "解读": "日柱六害，配偶宫受暗伤。感情关系中易有暗地里的摩擦或彼此损耗，关系看似平静，实则内部有裂缝。",
                "依据": "日柱含六害互动",
            }
        )

    if any(t in day_types for t in HARMONY_TYPES):
        harmony = sorted(day_types & HARMONY_TYPES)
        # Check if the day branch is combined away to a non-DM pillar (六合 only — branch-to-branch)
        combined_away_from_dm = False
        combined_away_detail: dict = {}
        if "六合" in harmony:
            for item in interactions.get("_raw_priority_list", []):
                if (
                    item.get("类型") != "六合"
                    or item.get("强度") not in ACTIVE_STRENGTHS
                ):
                    continue
                detail = item.get("组合明细", {})
                if DAY_PILLAR in detail:
                    other_pillars = [p for p in detail if p != DAY_PILLAR]
                    if other_pillars and other_pillars[0] != DAY_PILLAR:
                        combined_away_from_dm = True
                        combined_away_detail = detail
                    break
        if combined_away_from_dm:
            patterns.append(
                {
                    "格局编号": "day_branch_combined_away",
                    "格局名称": "日支逢合他柱",
                    "解读": "日支（配偶宫）与非日主的其他柱形成六合，配偶宫被他柱牵引。伴侣的注意力或情感可能被其他人或事物占据，感情中容易有第三方介入或伴侣情感分散的风险。",
                    "依据": f"日支六合他柱: {list(combined_away_detail.keys())}",
                }
            )
        else:
            patterns.append(
                {
                    "格局编号": "day_pillar_harmonious",
                    "格局名称": "日柱合局",
                    "解读": "配偶宫（日支）与其他柱形成合局，婚姻感情有稳定的结合力，与伴侣之间有天然的和谐共鸣。",
                    "依据": f"日柱互动类型: {harmony}",
                }
            )

    # Day branch 伏吟 — same branch appears in another pillar (not self-punishment)
    if day_branch_char and day_branch_char not in SELF_PUNISHMENT_BRANCHES:
        other_branches = [v for k, v in branch_chars.items() if k != day_branch_key]
        if day_branch_char in other_branches:
            patterns.append(
                {
                    "格局编号": "day_branch_fu_yin",
                    "格局名称": "日支伏吟",
                    "解读": "日支与其他柱同一地支，配偶宫伏吟。感情关系容易重复同一模式，可能经历再婚或与性格相似的伴侣；亦主感情停滞，不易突破既有格局。",
                    "依据": f"日支({day_branch_char})重见于其他柱",
                }
            )

    # Day branch self-punishment
    if day_branch_char in SELF_PUNISHMENT_BRANCHES:
        all_branches = list(branch_chars.values())
        if all_branches.count(day_branch_char) >= 2:
            patterns.append(
                {
                    "格局编号": "day_branch_self_punishment",
                    "格局名称": "日支自刑",
                    "解读": "日支自刑，感情中常自我设障，容易因过度思虑或内心矛盾而制造不必要的感情压力，情绪内耗影响亲密关系。",
                    "依据": f"日支({day_branch_char})重见自刑",
                }
            )

    return patterns


def _check_spouse_star(
    shi_shen: dict,
    interactions: dict,
    xun_kong: dict,
    branch_chars: dict,
    gender: int,
    score: int,
    wu_xing: dict,
    dm_elem: str,
) -> list[dict]:
    """
    Checks all spouse star patterns for the given gender.
    Female: spouse star = 官星 (正官/七杀); Male: spouse star = 财星 (正财/偏财).
    """
    spouse_gods = OFFICIAL_STARS if gender == 0 else WEALTH_STARS
    spouse_label = "官星" if gender == 0 else "财星"
    zheng = "正官" if gender == 0 else "正财"
    pian = "七杀" if gender == 0 else "偏财"

    sp = _ten_god_positions(shi_shen, spouse_gods)
    void_positions = _void_branch_positions(branch_chars, xun_kong)
    patterns = []

    if not sp["all"]:
        patterns.append(
            {
                "格局编号": "no_spouse_star",
                "格局名称": f"无{spouse_label}",
                "解读": f"命盘无{spouse_label}，感情缘份不由命盘主动给予，需靠大运或流年带入，婚姻缘份偏晚或需主动寻求。",
                "依据": f"四柱天干及地支均无{spouse_label}",
            }
        )
        return patterns

    # Visibility — for female DM differentiate 正官 (stable) from 七杀 (intense)
    if sp["in_stems"] and not sp["in_branches"]:
        if gender == 0:
            stem_gods = [
                shi_shen.get(pos[0] + "柱", {}).get("天干十神", "")
                for pos in sp["in_stems"]
            ]
            if "七杀" in stem_gods and "正官" not in stem_gods:
                jiedu = "七杀透干，所吸引的伴侣往往强势、主导性强，感情热烈但关系张力明显，易有控制或压迫感。"
            elif "正官" in stem_gods and "七杀" not in stem_gods:
                jiedu = "正官透干，感情态度认真稳重，所吸引的伴侣通常成熟可靠，有婚姻承诺意愿。"
            else:
                jiedu = f"{spouse_label}透干，感情态度主动外显，对伴侣的期待清晰。"
        else:
            jiedu = f"{spouse_label}透干，感情态度较为主动外显，对伴侣有明确的期望与吸引方向。"
        patterns.append(
            {
                "格局编号": "spouse_star_visible",
                "格局名称": f"{spouse_label}透干",
                "解读": jiedu,
                "依据": f"{spouse_label}天干位置: {sp['in_stems']}",
            }
        )
    elif sp["in_branches"] and not sp["in_stems"]:
        patterns.append(
            {
                "格局编号": "spouse_star_hidden",
                "格局名称": f"{spouse_label}藏支",
                "解读": f"{spouse_label}藏于地支，感情内敛，对伴侣的渴望不轻易表露，伴侣往往在较深入的交往后才显现真实价值。",
                "依据": f"{spouse_label}地支位置: {sp['in_branches']}",
            }
        )

    # Mixed spouse stars — use the pre-computed sp positions to detect both 正 and 偏
    sp_zheng = _ten_god_positions(shi_shen, {zheng})
    sp_pian = _ten_god_positions(shi_shen, {pian})
    if sp_zheng["all"] and sp_pian["all"]:
        label = "官杀混杂" if gender == 0 else "财星混杂"
        patterns.append(
            {
                "格局编号": "mixed_spouse_stars",
                "格局名称": label,
                "解读": f"正与偏{spouse_label}同入命盘（{label}），感情经历较为丰富，有可能经历多段认真的感情或再婚，择偶时容易在两类性格截然不同的伴侣之间徘徊。",
                "依据": f"{zheng}: {sp_zheng['all']}；{pian}: {sp_pian['all']}",
            }
        )

    # Void
    voided_sp = [pos for pos in sp["in_branches"] if pos[:2] in void_positions]
    if voided_sp:
        patterns.append(
            {
                "格局编号": "spouse_star_void",
                "格局名称": f"{spouse_label}落空",
                "解读": f"{spouse_label}落旬空，配偶缘份底气不足。婚姻时机不确定，或感情有名无实，伴侣关系难以完全落地生根。",
                "依据": f"落空{spouse_label}: {voided_sp}",
            }
        )

    # Clashed
    sp_pillars = {BRANCH_LABEL_TO_PILLAR[pos[:2]] for pos in sp["in_branches"]}
    sp_pillars |= {pos[0] + "柱" for pos in sp["in_stems"]}
    clashed_sp = [
        p for p in sp_pillars if _has_interaction_on_pillar(p, interactions, {"六冲"})
    ]
    if clashed_sp:
        patterns.append(
            {
                "格局编号": "spouse_star_clashed",
                "格局名称": f"{spouse_label}受冲",
                "解读": f"{spouse_label}受命盘六冲，伴侣关系容易经历冲突或分离，感情稳定性结构性偏弱，需借助大运化解冲力。",
                "依据": f"受冲{spouse_label}柱位: {clashed_sp}",
            }
        )

    # Combined away (天干合 not involving day master)
    combined_away = []
    for item in interactions.get("_raw_priority_list", []):
        if item.get("类型") != "天干合" or item.get("强度") not in ACTIVE_STRENGTHS:
            continue
        detail = item.get("组合明细", {})
        if DAY_PILLAR in detail:
            continue
        pillars_in = list(detail.keys())
        if len(pillars_in) != 2:
            continue
        sp_pillar = next(
            (
                p
                for p in pillars_in
                if shi_shen.get(p, {}).get("天干十神") in spouse_gods
            ),
            None,
        )
        if sp_pillar:
            other = next(p for p in pillars_in if p != sp_pillar)
            combined_away.append(f"{sp_pillar} 合 {other}")
    if combined_away:
        patterns.append(
            {
                "格局编号": "spouse_star_combined_away",
                "格局名称": f"{spouse_label}被合",
                "解读": f"{spouse_label}天干被合占，伴侣的注意力或精力被工作、家庭或他人所牵引，难以全心投入这段感情。",
                "依据": f"{spouse_label}被合: {combined_away}",
            }
        )

    # In tomb
    tomb_sp = [
        pos
        for pos in sp["in_branches"]
        if branch_chars.get(pos[:2], "") in TOMB_BRANCHES
    ]
    if tomb_sp:
        patterns.append(
            {
                "格局编号": "spouse_star_in_tomb",
                "格局名称": f"{spouse_label}入墓",
                "解读": f"{spouse_label}藏入墓库，伴侣缘份来得较晚，或对方的真实才华与价值需要时间才能显现，晚婚而美满的信号。",
                "依据": f"{spouse_label}入墓位置: {tomb_sp}",
            }
        )

    # 官杀争合 — female only: both 正官 AND 七杀 each form 天干合 with the DM's 日干
    # Classical 争合 requires the DM stem to be the contested party, not just any
    # two 官星 forming unrelated combinations elsewhere in the chart.
    if gender == 0 and sp_zheng["all"] and sp_pian["all"]:
        dm_zhenguan_combine = False
        dm_sha_combine = False
        for item in interactions.get("_raw_priority_list", []):
            if item.get("类型") != "天干合" or item.get("强度") not in ACTIVE_STRENGTHS:
                continue
            detail = item.get("组合明细", {})
            if DAY_PILLAR not in detail:
                continue
            for p in detail:
                if p == DAY_PILLAR:
                    continue
                god = shi_shen.get(p, {}).get("天干十神", "")
                if god == "正官":
                    dm_zhenguan_combine = True
                elif god == "七杀":
                    dm_sha_combine = True
        if dm_zhenguan_combine and dm_sha_combine:
            patterns.append(
                {
                    "格局编号": "guan_sha_competing",
                    "格局名称": "官杀争合",
                    "解读": "正官与七杀各自与日主天干形成天干合，两股男性力量同时争夺日主，感情选择极为复杂，易在两段截然不同性格的关系间徘徊，亦有多段认真感情并存的信号。",
                    "依据": f"正官与七杀均与日柱形成天干合",
                }
            )

    # Quality: elemental relationship + DM strength + spouse star element strength
    # Derive spouse star element: female → element that controls DM; male → element DM controls
    sp_elem = (
        _CONTROLS.get(dm_elem, "")
        if gender == 0
        else {v: k for k, v in _CONTROLS.items()}.get(dm_elem, "")
    )
    sp_elem_tier = _wu_xing_tier(wu_xing, sp_elem) if sp_elem else ""
    sp_elem_strong = sp_elem_tier in {"偏旺", "极旺", "极亢"}
    sp_elem_weak = sp_elem_tier in {"极弱", "偏弱"}

    if gender == 0:  # Female — 官星 controls DM
        only_sha = sp_pian["all"] and not sp_zheng["all"]
        beneficial_threshold = 4 if only_sha else 3
        draining_threshold = 2 if only_sha else 1
        if score >= beneficial_threshold:
            label_detail = "七杀" if only_sha else "正官"
            if sp_elem_strong:
                jiedu = f"日主强健且{label_detail}元素旺盛，伴侣气场强大，关系充满张力但也充满推动力，能激发你持续成长，须保持自身意志以维持平衡。"
            elif sp_elem_weak:
                jiedu = f"日主强健而{label_detail}元素偏弱，官星约束力温和，伴侣关系平和稳定，彼此尊重，无过多压力。"
            else:
                jiedu = (
                    f"日主极强，能驾御{label_detail}所带来的约束力，伴侣虽然强势但能为你的人生带来真实的推力与稳定感，关系反而成为成长的助力。"
                    if only_sha
                    else f"日主强健，{label_detail}的约束适度，伴侣成熟可靠、带来正向规范，感情有稳定的结构与承诺基础。"
                )
            patterns.append(
                {
                    "格局编号": "spouse_star_beneficial",
                    "格局名称": f"{spouse_label}为喜用神",
                    "解读": jiedu,
                    "依据": f"日主强弱分数 {score}/5 ≥ {beneficial_threshold}，{label_detail}元素({sp_elem})旺度: {sp_elem_tier or '中'}",
                }
            )
        elif score <= draining_threshold:
            label_detail = "七杀" if only_sha else "官星"
            if sp_elem_strong:
                jiedu = (
                    f"日主偏弱且七杀元素极旺，克制之力双重叠加，感情关系中压迫感极重，须待大运大幅扶身或印星制杀方有转机。"
                    if only_sha
                    else f"日主偏弱且官星元素旺盛，约束力过强，感情关系中长期承压，须以大运补强日主方能从容应对。"
                )
            else:
                jiedu = (
                    f"日主偏弱，七杀的强克力远超日主承受范围，感情中容易遭遇强势控制或压迫，伴侣关系反成消耗，须待大运扶身或印星制杀方能化解。"
                    if only_sha
                    else f"日主力量不足以承受官星的约束，感情关系中压力较重，容易感到束缚或被责任所困，需大运补强日主才能从容经营婚姻。"
                )
            patterns.append(
                {
                    "格局编号": "spouse_star_draining",
                    "格局名称": f"{spouse_label}为忌神",
                    "解读": jiedu,
                    "依据": f"日主强弱分数 {score}/5 ≤ {draining_threshold}，{label_detail}元素({sp_elem})旺度: {sp_elem_tier or '中'}，制压日主",
                }
            )
        else:  # Neutral — score in mid-range (e.g. 2 for 正官, 3 for 七杀)
            label_detail = "七杀" if only_sha else "官星"
            if sp_elem_strong:
                jiedu = f"日主中等，{label_detail}元素偏旺，感情关系有一定张力，伴侣带来适度压力，需持续自我强化方能维持平衡。"
            elif sp_elem_weak:
                jiedu = f"日主中等而{label_detail}元素偏弱，官星约束力温和，感情尚属稳定，但双方动力均不强，关系需主动经营。"
            else:
                jiedu = (
                    f"日主中等，七杀约束力与日主力量大致相当，感情关系有张力也有推动力，能否良性发展取决于大运的扶助方向。"
                    if only_sha
                    else f"日主中等，官星约束适中，感情关系尚属平衡，伴侣既带来规范也带来压力，整体属于可经营的格局。"
                )
            patterns.append(
                {
                    "格局编号": "spouse_star_neutral",
                    "格局名称": f"{spouse_label}半喜半忌",
                    "解读": jiedu,
                    "依据": f"日主强弱分数 {score}/5（中等），{label_detail}元素({sp_elem})旺度: {sp_elem_tier or '中'}",
                }
            )
    else:  # Male — 财星 controlled by DM (DM expends energy on partner)
        only_pian = sp_pian["all"] and not sp_zheng["all"]
        if score >= 3:
            if sp_elem_strong:
                jiedu = f"日主强健，财星元素旺盛，感情生活丰富多彩，但也需留意财多身弱的边界——财星过旺仍会分散精力，宜专注经营而非追求数量。"
            elif sp_elem_weak:
                jiedu = (
                    "日主强健而偏财元素偏弱，感情经历相对平淡稳定，伴侣温和低调，关系以踏实为主。"
                    if only_pian
                    else "日主强健而财星元素偏弱，对伴侣的付出轻松自如，感情关系平和，婚姻稳固但缺乏强烈的激情。"
                )
            else:
                jiedu = (
                    "日主强健，能坦然承担对感情的付出，偏财带来丰富的感情体验与情趣，感情生活活泼多姿。"
                    if only_pian
                    else "日主强健，财星为喜用神，对伴侣的付出游刃有余，感情为人生加分，婚姻关系有实质的经营基础。"
                )
            patterns.append(
                {
                    "格局编号": "spouse_star_beneficial",
                    "格局名称": f"{spouse_label}为喜用神",
                    "解读": jiedu,
                    "依据": f"日主强弱分数 {score}/5 ≥ 3，{spouse_label}元素({sp_elem})旺度: {sp_elem_tier or '中'}，受日主驾驭",
                }
            )
        elif score <= 1:
            if sp_elem_strong:
                jiedu = (
                    "日主偏弱且偏财元素极旺，感情中对新鲜感与感官享受的追求远超日主承受能力，财多身弱之下极易在关系中被情绪与物质消耗殆尽，须大运大力扶身方有改善。"
                    if only_pian
                    else "日主偏弱且财星元素极旺，财多身弱，感情与婚姻的重量远超日主承受能力，极易在关系中被消耗殆尽，须大运大力扶身方有改善。"
                )
            else:
                jiedu = (
                    "日主偏弱且偏财独旺，感情中易因追求新鲜刺激或感官享受而过度消耗，关系带来的情绪与财务波动远超日主承受能力，需大运补强日主方能健康经营感情。"
                    if only_pian
                    else "日主偏弱，财星耗身过重。感情与婚姻对你而言是明显的精力消耗，伴侣关系可能带来额外的经济或情绪负担，需大运补强日主方能健康经营感情。"
                )
            patterns.append(
                {
                    "格局编号": "spouse_star_draining",
                    "格局名称": f"{spouse_label}为忌神",
                    "解读": jiedu,
                    "依据": f"日主强弱分数 {score}/5 ≤ 1，{spouse_label}元素({sp_elem})旺度: {sp_elem_tier or '中'}，耗身",
                }
            )
        else:  # score == 2 — moderate, borderline
            if sp_elem_strong:
                jiedu = f"日主中等而财星元素偏旺，感情付出略显吃力，伴侣关系带来的消耗不容忽视，大运若再泄身则压力明显增加。"
            elif sp_elem_weak:
                jiedu = (
                    "日主中等而偏财元素偏弱，感情经历尚可，付出与回报大致平衡，关系稳定但缺乏强烈的推动力。"
                    if only_pian
                    else "日主中等而财星元素偏弱，感情关系尚属平衡，付出不重，婚姻可维持但需主动经营。"
                )
            else:
                jiedu = (
                    "日主中等，偏财消耗与日主力量大致相当，感情生活有起伏，能否游刃有余取决于大运是否进一步扶身。"
                    if only_pian
                    else "日主中等，财星消耗尚在可承受范围内，感情关系属于可经营的格局，大运扶身则感情顺遂，大运泄身则略感吃力。"
                )
            patterns.append(
                {
                    "格局编号": "spouse_star_neutral",
                    "格局名称": f"{spouse_label}半喜半忌",
                    "解读": jiedu,
                    "依据": f"日主强弱分数 {score}/5（中等），{spouse_label}元素({sp_elem})旺度: {sp_elem_tier or '中'}",
                }
            )

    return patterns


def _check_divorce_remarriage(
    shi_shen: dict,
    interactions: dict,
    branch_chars: dict,
    gender: int,
) -> list[dict]:
    """
    Compound patterns for divorce risk and remarriage indication.
    Individual components (日支受冲, 配偶星受冲, 官杀混杂, 日支伏吟) are already
    detected separately; this function fires only when multiple signals combine.
    """
    patterns = []
    spouse_gods = OFFICIAL_STARS if gender == 0 else WEALTH_STARS
    zheng = "正官" if gender == 0 else "正财"
    pian = "七杀" if gender == 0 else "偏财"
    spouse_label = "官星" if gender == 0 else "财星"

    sp = _ten_god_positions(shi_shen, spouse_gods)
    sp_zheng = _ten_god_positions(shi_shen, {zheng})
    sp_pian = _ten_god_positions(shi_shen, {pian})

    # ── Divorce risk: day pillar clashed + spouse star clashed (both required) ──
    day_clashed = _has_interaction_on_pillar(DAY_PILLAR, interactions, {"六冲"})
    sp_pillars = {BRANCH_LABEL_TO_PILLAR[pos[:2]] for pos in sp["in_branches"]}
    sp_pillars |= {pos[0] + "柱" for pos in sp["in_stems"]}
    sp_clashed = any(
        _has_interaction_on_pillar(p, interactions, {"六冲"}) for p in sp_pillars
    )

    if day_clashed and sp_clashed:
        patterns.append(
            {
                "格局编号": "divorce_risk",
                "格局名称": "婚姻分离风险",
                "解读": "配偶宫（日支）与配偶星同时受到命盘六冲，婚姻结构受到双重冲击。感情关系中的分离或婚姻破裂风险明显偏高，需大运行至合局或印星扶持方能稳固。",
                "依据": f"日柱受冲；{spouse_label}受冲柱位: {sorted(sp_pillars)}",
            }
        )

    # ── Remarriage sign: requires mixed spouse stars plus at least one more signal ──
    mixed = bool(sp_zheng["all"] and sp_pian["all"])

    day_branch_char = branch_chars.get("日支", "")
    other_branches = [v for k, v in branch_chars.items() if k != "日支"]
    day_fu_yin = (
        bool(day_branch_char)
        and day_branch_char in other_branches
        and day_branch_char not in SELF_PUNISHMENT_BRANCHES
    )

    if mixed and day_clashed:
        patterns.append(
            {
                "格局编号": "remarriage_sign",
                "格局名称": "婚姻多变倾向",
                "解读": f"{spouse_label}混杂加日支受冲，命盘同时具备多段认真感情与配偶宫不稳的双重格局，感情路上可能经历多次重要关系，第二段感情往往与第一段性质迥异。后天经营与大运配合可以减缓此倾向。",
                "依据": f"{zheng}: {sp_zheng['all']}；{pian}: {sp_pian['all']}；日柱受冲",
            }
        )
    elif mixed and day_fu_yin:
        patterns.append(
            {
                "格局编号": "remarriage_sign",
                "格局名称": "婚姻多变倾向",
                "解读": f"{spouse_label}混杂加日支伏吟，感情模式容易在不同的伴侣身上重复，有经历多段认真感情的倾向，须留意是否陷入同一类感情困局，自我觉察有助于打破惯性。",
                "依据": f"{zheng}: {sp_zheng['all']}；{pian}: {sp_pian['all']}；日支伏吟",
            }
        )
    elif len(sp["all"]) >= 3:
        # Spouse star saturates the chart — three or more positions
        patterns.append(
            {
                "格局编号": "remarriage_sign",
                "格局名称": "婚姻多变倾向",
                "解读": f"{spouse_label}多见于三处或以上，感情缘份广而复杂，命盘具备多段认真感情的结构性倾向，未必一定再婚，但感情经历较常人丰富，需在每段关系中保持清醒的自我认知。",
                "依据": f"{spouse_label}位置: {sp['all']}",
            }
        )

    return patterns


# ── Family natal patterns ──────────────────────────────────────────────────────


def _check_mother_patterns(
    shi_shen: dict,
    interactions: dict,
    xun_kong: dict,
    branch_chars: dict,
    wu_xing: dict,
    dm_elem: str,
) -> list[dict]:
    """母亲 (印星 — 正印/偏印)"""
    ip = _ten_god_positions(shi_shen, SEAL_STARS)
    void_positions = _void_branch_positions(branch_chars, xun_kong)
    patterns = []

    if not ip["all"]:
        patterns.append(
            {
                "格局编号": "no_mother_star",
                "格局名称": "无印星",
                "解读": "命盘无印星，母亲的存在感或情感支持在命盘中没有结构性根基。成长过程中母亲的陪伴或教育可能较为缺失，或与母亲的情感连结较为疏远，需靠大运带入印星方能弥补。",
                "依据": "四柱天干及地支均无印星（正印/偏印）",
            }
        )
        return patterns

    # Strong / close mother
    if ip["in_stems"]:
        patterns.append(
            {
                "格局编号": "mother_strong",
                "格局名称": "印星透干",
                "解读": "印星透干，母亲的影响力在你的成长中清晰可见，关系紧密，母亲给予的教育与情感支持较为直接。",
                "依据": f"印星天干位置: {ip['in_stems']}",
            }
        )
    elif ip["in_branches"] and not ip["in_stems"]:
        patterns.append(
            {
                "格局编号": "mother_hidden",
                "格局名称": "印星藏支",
                "解读": "印星藏支，母亲虽在身边，但情感表达内敛，关系有一定距离感，或母亲以低调方式默默支持。",
                "依据": f"印星地支位置: {ip['in_branches']}",
            }
        )

    # Clashed mother
    ip_pillars = {BRANCH_LABEL_TO_PILLAR[pos[:2]] for pos in ip["in_branches"]}
    ip_pillars |= {pos[0] + "柱" for pos in ip["in_stems"]}
    clashed = [
        p for p in ip_pillars if _has_interaction_on_pillar(p, interactions, {"六冲"})
    ]
    if clashed:
        patterns.append(
            {
                "格局编号": "mother_clashed",
                "格局名称": "印星受冲",
                "解读": "印星受冲，与母亲的关系有明显的摩擦或张力，成长过程中母亲关系可能经历分离、争执或情绪波动。",
                "依据": f"受冲印星柱位: {clashed}",
            }
        )

    # Void mother
    voided_ip = [pos for pos in ip["in_branches"] if pos[:2] in void_positions]
    if voided_ip:
        patterns.append(
            {
                "格局编号": "mother_void",
                "格局名称": "印星落空",
                "解读": "印星落旬空，母亲的陪伴或情感支持有一种「在却不实在」的感觉，或早年与母亲关系有明显的情感缺位。",
                "依据": f"落空印星: {voided_ip}",
            }
        )

    return patterns


def _check_father_patterns(
    shi_shen: dict, interactions: dict, xun_kong: dict, branch_chars: dict
) -> list[dict]:
    """父亲 (偏财 for most schools)"""
    fp = _ten_god_positions(shi_shen, {"偏财"})
    void_positions = _void_branch_positions(branch_chars, xun_kong)
    patterns = []

    if not fp["all"]:
        patterns.append(
            {
                "格局编号": "no_father_star",
                "格局名称": "无偏财",
                "解读": "命盘无偏财，父亲的影响力在命盘中缺乏结构性支撑。成长过程中父亲的陪伴或榜样作用可能较为有限，或父亲形象较为淡薄，父系资源需依赖大运激活方能显现。",
                "依据": "四柱天干及地支均无偏财",
            }
        )
        return patterns

    if fp["in_stems"]:
        patterns.append(
            {
                "格局编号": "father_strong",
                "格局名称": "偏财透干",
                "解读": "偏财透干，父亲的存在感与影响力明显，父亲通常性格外向、慷慨或善于应酬，在成长中扮演积极角色。",
                "依据": f"偏财天干位置: {fp['in_stems']}",
            }
        )
    elif fp["in_branches"] and not fp["in_stems"]:
        patterns.append(
            {
                "格局编号": "father_hidden",
                "格局名称": "偏财藏支",
                "解读": "偏财藏于地支，父亲存在但影响力较为低调，父亲的支持或付出不易直接察觉，关系需深入才能感受其价值。",
                "依据": f"偏财地支位置: {fp['in_branches']}",
            }
        )

    fp_pillars = {BRANCH_LABEL_TO_PILLAR[pos[:2]] for pos in fp["in_branches"]}
    fp_pillars |= {pos[0] + "柱" for pos in fp["in_stems"]}
    clashed = [
        p for p in fp_pillars if _has_interaction_on_pillar(p, interactions, {"六冲"})
    ]
    if clashed:
        patterns.append(
            {
                "格局编号": "father_clashed",
                "格局名称": "偏财受冲",
                "解读": "偏财受冲，与父亲的关系有明显摩擦，成长过程中可能经历父亲的缺席、离家或亲子关系紧张。",
                "依据": f"受冲偏财柱位: {clashed}",
            }
        )

    voided_fp = [pos for pos in fp["in_branches"] if pos[:2] in void_positions]
    if voided_fp:
        patterns.append(
            {
                "格局编号": "father_void",
                "格局名称": "偏财落空",
                "解读": "偏财落旬空，父亲的陪伴或支持感觉虚浮，父亲形象可能缺位或影响力有限。",
                "依据": f"落空偏财: {voided_fp}",
            }
        )

    return patterns


def _check_parental_harmony(bazi: dict, interactions: dict) -> list[dict]:
    """年支与月支的合冲关系反映父母关系"""
    year_branch = bazi["八字"]["年柱"]["地支"]
    month_branch = bazi["八字"]["月柱"]["地支"]
    patterns = []

    # Check 月柱 interactions for presence of 年柱
    month_types = _interaction_types_on_pillar(MONTH_PILLAR, interactions)
    year_types = _interaction_types_on_pillar(YEAR_PILLAR, interactions)

    has_clash = "六冲" in month_types or "六冲" in year_types
    has_harmony = bool(HARMONY_TYPES & (month_types | year_types))

    # Look for year-month direct interaction
    for item in interactions.get("_raw_priority_list", []):
        detail = item.get("组合明细", {})
        if YEAR_PILLAR in detail and MONTH_PILLAR in detail:
            itype = item.get("类型", "")
            if item.get("强度") in ACTIVE_STRENGTHS:
                if itype in HARMONY_TYPES:
                    has_harmony = True
                elif itype in {"六冲"} | {t for t in CLASH_HARM_TYPES if "刑" in t}:
                    has_clash = True

    if has_clash:
        patterns.append(
            {
                "格局编号": "parents_clashing",
                "格局名称": "年月柱相冲",
                "解读": "年柱与月柱存在冲克，父母之间的关系有明显摩擦或价值观冲突，成长环境缺乏和谐，幼年家庭氛围有一定压力。",
                "依据": f"年支({year_branch})与月支({month_branch})存在冲克互动",
            }
        )
    elif has_harmony:
        patterns.append(
            {
                "格局编号": "parents_harmonious",
                "格局名称": "年月柱相合",
                "解读": "年柱与月柱形成合局，父母关系较为和谐融洽，成长环境稳定，家庭给予的支持感较强。",
                "依据": f"年支({year_branch})与月支({month_branch})形成合局",
            }
        )

    return patterns


def _check_upbringing_quality(shen_sha: dict, shi_shen: dict) -> list[dict]:
    """幼年成长质量 — 年柱神煞与十神"""
    patterns = []
    year_stars = _pillar_shen_sha(shen_sha, YEAR_PILLAR)

    if "孤辰" in year_stars or "寡宿" in year_stars:
        which = [s for s in ("孤辰", "寡宿") if s in year_stars]
        patterns.append(
            {
                "格局编号": "childhood_isolated",
                "格局名称": "幼年孤独",
                "解读": "孤辰或寡宿现于年柱，幼年有孤独感，即使家庭完整，内心仍有一份难以言说的疏离，较早学会独立面对生活。",
                "依据": f"年柱含: {which}",
            }
        )

    noble_stars = {"天德", "月德", "天乙贵人", "昼天乙", "夜天乙"}
    found_noble = [s for s in year_stars if s in noble_stars]
    if found_noble:
        patterns.append(
            {
                "格局编号": "childhood_prestigious",
                "格局名称": "幼年贵气",
                "解读": "年柱带贵人星，幼年受到良好的庇护与福泽，成长环境中有贵人相助，家庭背景或教育条件偏向优质。",
                "依据": f"年柱贵人星: {found_noble}",
            }
        )

    # 七杀 on year pillar stem without seal control
    year_stem_god = shi_shen.get(YEAR_PILLAR, {}).get("天干十神", "")
    if year_stem_god == "七杀":
        has_seal = any(
            shi_shen.get(p, {}).get("天干十神") in SEAL_STARS
            or any(
                shi_shen.get(p, {}).get("地支十神", {}).get(t) in SEAL_STARS
                for t in BRANCH_TIERS
            )
            for p in PILLARS
        )
        if not has_seal:
            patterns.append(
                {
                    "格局编号": "childhood_burdened",
                    "格局名称": "幼年负担重",
                    "解读": "年柱七杀透干且无印星制化，幼年承受较大的压力与责任，成长环境要求较高，可能较早承担家庭负担或面对严格管教。",
                    "依据": "年柱天干七杀，命盘无印星制化",
                }
            )

    return patterns


# ── Friendship natal patterns ──────────────────────────────────────────────────


def _check_friendship_patterns(
    shi_shen: dict, wu_xing: dict, dm_elem: str, shen_sha: dict, interactions: dict
) -> list[dict]:
    patterns = []

    ep = _ten_god_positions(shi_shen, EXPRESSION_STARS)
    pp = _ten_god_positions(shi_shen, PEER_STARS)
    wp = _ten_god_positions(shi_shen, WEALTH_STARS)

    # Social ease / expression
    if ep["in_stems"]:
        patterns.append(
            {
                "格局编号": "expression_visible",
                "格局名称": "食伤透干",
                "解读": "食伤透干，表达力强，天生善于展示自我，与人接触时自然流露魅力，交友轻松，容易扩展人际圈。",
                "依据": f"食伤天干位置: {ep['in_stems']}",
            }
        )
    elif ep["in_branches"] and not ep["in_stems"]:
        patterns.append(
            {
                "格局编号": "expression_hidden",
                "格局名称": "食伤藏支",
                "解读": "食伤藏支，内在表达力丰富，但需熟悉的环境才能展现，一旦建立信任则能成为真诚深厚的朋友。",
                "依据": f"食伤地支位置: {ep['in_branches']}",
            }
        )

    # Expression element strength — how powerful the social output is, regardless of visibility
    # Only fire if 食伤 is completely absent from stems AND branches (ep["all"] empty),
    # or if the elemental tier is explicitly known. Never infer weakness from a missing
    # tier value when 食伤 is already visible in stems (透干 proves the element exists).
    ep_elem = _GENERATES.get(dm_elem, "")
    ep_elem_tier = _wu_xing_tier(wu_xing, ep_elem) if ep_elem else ""
    if ep_elem_tier in {"偏旺", "极旺", "极亢"}:
        patterns.append(
            {
                "格局编号": "expression_strong_social",
                "格局名称": "食伤元素旺盛",
                "解读": "食伤元素旺盛，表达能量充沛，天生话多、才华外露，在人群中容易成为话题中心或创意输出者。社交吸引力强，但也需留意表达过度或言多失慎，以免在人际中树敌。",
                "依据": f"食伤元素({ep_elem})旺度: {ep_elem_tier}",
            }
        )
    elif ep_elem_tier in {"极弱", "偏弱"} and not ep["in_stems"]:
        # Only label as weak when the tier is explicitly weak AND 食伤 is not already
        # transparent in a stem — transparency contradicts elemental absence/weakness.
        patterns.append(
            {
                "格局编号": "expression_weak_social",
                "格局名称": "食伤元素偏弱",
                "解读": "食伤元素偏弱，社交表达较为克制，不擅主动破冰，但言辞往往精炼有力，在小圈子中更能展现真实的深度与魅力。",
                "依据": f"食伤元素({ep_elem})旺度: {ep_elem_tier}",
            }
        )

    # Friend circle depth
    peer_elem_tier = _wu_xing_tier(wu_xing, dm_elem)  # 比劫 = same element as DM
    if peer_elem_tier in {"偏旺", "极旺", "极亢"}:
        patterns.append(
            {
                "格局编号": "peer_strong",
                "格局名称": "比劫旺盛",
                "解读": "比劫元素旺盛，社交圈广泛，人缘较好，喜欢群体活动，但也需留意是否过于依赖他人或忽略个人界限。",
                "依据": f"比劫({dm_elem})旺度: {peer_elem_tier}",
            }
        )
    elif peer_elem_tier in {"极弱", "偏弱"}:
        patterns.append(
            {
                "格局编号": "peer_weak",
                "格局名称": "比劫微弱",
                "解读": "比劫元素偏弱，社交圈偏小而精，朋友不多但情谊深厚，独立自主，不依赖朋友，有时显得有些孤高。",
                "依据": f"比劫({dm_elem})旺度: {peer_elem_tier}",
            }
        )

    # Reciprocity: 比劫夺财 — peers steal wealth
    if pp["all"] and wp["all"]:
        peer_strong_enough = peer_elem_tier in {"偏旺", "极旺", "极亢"}
        if peer_strong_enough:
            patterns.append(
                {
                    "格局编号": "peer_steals_wealth",
                    "格局名称": "比劫夺财",
                    "解读": "比劫旺而财星同现，友情中付出与回报容易失衡，朋友关系中你往往是付出更多的一方，需留意在人际中保护自己的资源。",
                    "依据": f"比劫({dm_elem})旺度 {peer_elem_tier}，财星: {wp['all']}",
                }
            )

    # Trust / betrayal: 比劫 on month pillar clashed
    if any(pos.startswith("月") for pos in pp["in_branches"] + pp["in_stems"]):
        month_types = _interaction_types_on_pillar(MONTH_PILLAR, interactions)
        if "六冲" in month_types or "六害" in month_types:
            clash_found = sorted(month_types & {"六冲", "六害"})
            patterns.append(
                {
                    "格局编号": "peer_clashed",
                    "格局名称": "月柱比劫受冲",
                    "解读": "月柱比劫受冲，人生中有被朋友背叛或友情破裂的信号，需提防以友情为名的利益侵占，建立清晰的人际界限。",
                    "依据": f"月柱比劫受{clash_found}",
                }
            )

    # Social magnetism: 食伤 + 桃花 combo
    peach_pillars = _find_star_pillars(shen_sha, "桃花") or _find_star_pillars(
        shen_sha, "沐浴桃花"
    )
    if ep["all"] and peach_pillars:
        patterns.append(
            {
                "格局编号": "charm_combo",
                "格局名称": "食伤配桃花",
                "解读": "食伤与桃花并见，魅力与表达力相辅相成，天生具备让人印象深刻的气质，社交场合中不费力便能吸引他人注意。",
                "依据": f"食伤: {ep['all']}；桃花: {peach_pillars}",
            }
        )

    return patterns


# ── Cycle event evaluators ─────────────────────────────────────────────────────


def _evaluate_romance_for_cycle(
    cycle: dict,
    natal_year_branch: str,
    natal_day_branch: str,
    shi_shen: dict,
    interactions: dict,
    gender: int,
    xun_kong: dict,
    branch_chars: dict,
    dm_elem: str,
) -> dict:
    """Evaluate romance domain for a single 大运 cycle."""
    cycle_branch = _cycle_branch(cycle)
    cycle_void = _cycle_branch_void(cycle)
    zhu_wei = cycle.get("作用", {}).get("柱位动态", {})
    status_parts: list[str] = []
    jiedu_parts: list[str] = []
    _seen: set[str] = set()

    def _add(status: str, jiedu: str) -> None:
        if status not in _seen:
            _seen.add(status)
            status_parts.append(status)
            jiedu_parts.append(jiedu)

    # Check romance stars activated by cycle branch
    romance_activations = []
    if cycle_branch:
        if cycle_branch == year_earthly_branches_shens.get("红鸾", {}).get(
            natal_year_branch
        ):
            romance_activations.append("红鸾")
        if cycle_branch == year_earthly_branches_shens.get("天喜", {}).get(
            natal_year_branch
        ):
            romance_activations.append("天喜")
        pb_year = year_earthly_branches_shens.get("桃花", {}).get(natal_year_branch)
        pb_day = day_earthly_branches_shens.get("桃花", {}).get(natal_day_branch)
        if cycle_branch in (pb_year, pb_day):
            romance_activations.append("桃花")

    if romance_activations:
        star_str = "、".join(romance_activations)
        _add(
            f"{star_str}激活",
            f"大运支激活{star_str}，此运感情缘份旺盛，有机会遇到重要的伴侣或令既有关系迈向新阶段。",
        )

    # 大运引动食伤 — cycle stem carries expression star (increases romantic expressiveness/libido)
    run_zhu = cycle.get("运柱", {})
    cycle_stem_god = run_zhu.get("十神", {}).get("天干", {}).get("十神", "")
    if cycle_stem_god in EXPRESSION_STARS:
        _add(
            "食伤入运",
            "大运天干带食伤，此运感情表达欲旺盛，对新鲜感与感官体验的追求增强，感情生活活跃，但也需留意感情界限，避免冲动行事。",
        )

    # Day pillar interactions in this cycle
    day_pillar_interactions = set()
    for tier_items in zhu_wei.get(DAY_PILLAR, {}).values():
        for item in tier_items:
            if item.get("强度") in ACTIVE_STRENGTHS:
                day_pillar_interactions.add(item.get("类型", ""))

    if (CYCLE_CLASH_TYPES & day_pillar_interactions) or any(
        "刑" in t for t in day_pillar_interactions
    ):
        if "反吟" in day_pillar_interactions:
            _add(
                "配偶宫反吟",
                "大运支与日支反吟，配偶宫受到强烈的逆向冲击，感情关系面临重大考验或转折，婚姻可能经历重组或突变。",
            )
        else:
            _add(
                "配偶宫受冲",
                "大运冲击日柱（配偶宫），感情关系经历明显波动，可能有分离、争执或关系重组。",
            )

    elif CYCLE_HARMONY_TYPES & day_pillar_interactions:
        if "六合" in day_pillar_interactions and not (
            {"三合", "三会"} & day_pillar_interactions
        ):
            _add(
                "配偶宫被合动",
                "大运支与日支形成六合，配偶宫被大运牵引向外，此运本人或伴侣均有向外发展感情的倾向，需留意感情专一度。",
            )
        else:
            _add(
                "配偶宫合局",
                "大运与日柱形成三合或三会，配偶宫受到结构性正向激活，此运感情顺畅，亲密关系趋于稳定深化。",
            )

    elif CYCLE_STAGNATION_TYPES & day_pillar_interactions:
        _add(
            "配偶宫伏吟",
            "大运支与日支伏吟，配偶宫重叠停滞，感情关系在此运缺乏新鲜动力，易原地踏步或感情趋于平淡。",
        )

    # Spouse star activated or suppressed
    spouse_gods = OFFICIAL_STARS if gender == 0 else WEALTH_STARS
    sp = _ten_god_positions(shi_shen, spouse_gods)
    sp_branch_pillars = {BRANCH_LABEL_TO_PILLAR[pos[:2]] for pos in sp["in_branches"]}
    for pillar in sp_branch_pillars:
        for tier_items in zhu_wei.get(pillar, {}).values():
            for item in tier_items:
                if item.get("强度") in ACTIVE_STRENGTHS:
                    itype = item.get("类型", "")
                    if itype in {"天干合", "六合"}:
                        _add(
                            "配偶星被合走",
                            f"大运与{pillar}配偶星形成{itype}，伴侣的注意力或精力在此运被大运牵引，容易移情或对外发展，感情关系面临第三方介入的风险。",
                        )
                    elif itype in {"三合", "三会"}:
                        _add(
                            "配偶星激活",
                            f"大运{itype}{pillar}配偶星，感情星得到结构性激活，此运有机会开花结果。",
                        )
                    elif itype in CYCLE_VAULT_TYPES:
                        _add(
                            "配偶星出库",
                            f"大运开{pillar}库，配偶星从墓库中释放，原本延迟的感情缘份在此运得到激活，有机会遇到重要伴侣。",
                        )
                    elif itype in CYCLE_CLASH_TYPES:
                        _add(
                            "配偶星受冲",
                            f"大运冲{pillar}配偶星，感情关系受到冲击，现有感情可能面临考验。",
                        )

    if cycle_void and not jiedu_parts:
        _add(
            "运支落空",
            "大运支落旬空，感情缘份底气略显不足，此运感情发展缓慢或缘份有名无实。",
        )

    if not status_parts:
        return {
            "运势": "平稳",
            "解读": "此运配偶宫与感情星无明显触动，感情状态延续既有格局，无显著突破也无明显冲击。",
        }

    return {"运势": "、".join(status_parts), "解读": "；".join(jiedu_parts)}


def _evaluate_family_for_cycle(
    cycle: dict,
    shi_shen: dict,
    interactions: dict,
    bazi: dict,
) -> dict:
    """Evaluate family domain for a single 大运 cycle."""
    zhu_wei = cycle.get("作用", {}).get("柱位动态", {})
    status_parts: list[str] = []
    jiedu_parts: list[str] = []
    _seen: set[str] = set()

    def _add(status: str, jiedu: str) -> None:
        if status not in _seen:
            _seen.add(status)
            status_parts.append(status)
            jiedu_parts.append(jiedu)

    # Seal (mother) activations / suppressions
    ip = _ten_god_positions(shi_shen, SEAL_STARS)
    ip_pillars = {BRANCH_LABEL_TO_PILLAR[pos[:2]] for pos in ip["in_branches"]}
    ip_pillars |= {pos[0] + "柱" for pos in ip["in_stems"]}
    for pillar in ip_pillars:
        for tier_items in zhu_wei.get(pillar, {}).values():
            for item in tier_items:
                if item.get("强度") in ACTIVE_STRENGTHS:
                    itype = item.get("类型", "")
                    if itype in CYCLE_HARMONY_TYPES:
                        _add(
                            "印星激活",
                            f"大运与{pillar}印星形成合局，与母亲或家庭的联系在此运得到修复或加深。",
                        )
                    elif itype in CYCLE_VAULT_TYPES:
                        _add(
                            "印星出库",
                            f"大运开{pillar}库，印星从墓库释放，与母亲或家庭的情感连结在此运重新浮现或修复。",
                        )
                    elif itype in CYCLE_CLASH_TYPES:
                        msg = (
                            "大运反吟冲击印星，家庭关系经历强烈动荡，与母亲或原生家庭可能有突发性的分离或变故。"
                            if itype == "反吟"
                            else f"大运冲{pillar}印星，此运与母亲或家庭关系可能面临摩擦、分离或变故。"
                        )
                        _add("印星受冲", msg)
                    elif itype in CYCLE_STAGNATION_TYPES:
                        _add(
                            "印星伏吟",
                            f"大运与{pillar}印星伏吟，家庭关系在此运停滞，与母亲的互动缺乏新的突破，维持现状为主。",
                        )

    # 偏财 (father) activations / suppressions
    fp = _ten_god_positions(shi_shen, {"偏财"})
    fp_pillars = {BRANCH_LABEL_TO_PILLAR[pos[:2]] for pos in fp["in_branches"]}
    fp_pillars |= {pos[0] + "柱" for pos in fp["in_stems"]}
    for pillar in fp_pillars:
        for tier_items in zhu_wei.get(pillar, {}).values():
            for item in tier_items:
                if item.get("强度") in ACTIVE_STRENGTHS:
                    itype = item.get("类型", "")
                    if itype in CYCLE_HARMONY_TYPES:
                        _add(
                            "父星激活",
                            f"大运与{pillar}偏财形成合局，与父亲或父系家庭的关系此运有正向发展。",
                        )
                    elif itype in CYCLE_VAULT_TYPES:
                        _add(
                            "父星出库",
                            f"大运开{pillar}库，偏财从墓库释放，与父亲的关系或父系资源在此运重新激活。",
                        )
                    elif itype in CYCLE_CLASH_TYPES:
                        msg = (
                            "大运反吟冲击偏财，与父亲或父系家庭的关系经历强烈变动，可能有突发性的冲突或分离。"
                            if itype == "反吟"
                            else f"大运冲{pillar}偏财，此运与父亲或父系关系可能经历变故或关系紧张。"
                        )
                        _add("父星受冲", msg)
                    elif itype in CYCLE_STAGNATION_TYPES:
                        _add(
                            "父星伏吟",
                            f"大运与{pillar}偏财伏吟，与父亲的关系停滞，此运父系互动缺乏新发展。",
                        )

    if not status_parts:
        return {
            "运势": "平稳",
            "解读": "此运家庭星无明显触动，原生家庭关系延续既有模式，无显著变化。",
        }

    return {"运势": "、".join(status_parts), "解读": "；".join(jiedu_parts)}


def _evaluate_friendship_for_cycle(
    cycle: dict,
    shi_shen: dict,
    interactions: dict,
    dm_elem: str,
) -> dict:
    """Evaluate friendship domain for a single 大运 cycle."""
    zhu_wei = cycle.get("作用", {}).get("柱位动态", {})
    run_zhu = cycle.get("运柱", {})
    cycle_stem_god = run_zhu.get("十神", {}).get("天干", {}).get("十神", "")
    status_parts: list[str] = []
    jiedu_parts: list[str] = []
    _seen: set[str] = set()

    def _add(status: str, jiedu: str) -> None:
        if status not in _seen:
            _seen.add(status)
            status_parts.append(status)
            jiedu_parts.append(jiedu)

    # Cycle carries 比劫 — social expansion
    if cycle_stem_god in PEER_STARS:
        _add(
            "比劫入运",
            "大运天干带比劫，此运社交活跃，朋友圈扩展，但也需留意朋友利益纠纷或竞争关系。",
        )

    # Cycle carries 食伤 — social expression
    if cycle_stem_god in EXPRESSION_STARS:
        _add(
            "食伤入运",
            "大运天干带食伤，此运社交表达力强，适合拓展人际、公开展示才华，人缘进入上升期。",
        )

    # Month pillar (social domain) interactions in this cycle
    pp = _ten_god_positions(shi_shen, PEER_STARS)
    month_has_peer = any(
        pos.startswith("月") for pos in pp["in_branches"] + pp["in_stems"]
    )
    if month_has_peer:
        for tier_items in zhu_wei.get(MONTH_PILLAR, {}).values():
            for item in tier_items:
                if item.get("强度") in ACTIVE_STRENGTHS:
                    itype = item.get("类型", "")
                    if itype in CYCLE_CLASH_TYPES:
                        msg = (
                            "大运反吟冲击月柱，人际关系经历剧烈动荡，朋友圈可能有突发性的背叛或重大决裂。"
                            if itype == "反吟"
                            else "大运冲月柱比劫，此运人际关系出现明显动荡，朋友圈可能有背叛或决裂，需审慎择友。"
                        )
                        _add("月柱受冲", msg)
                    elif itype in CYCLE_HARMONY_TYPES:
                        _add(
                            "月柱合局",
                            "大运与月柱形成合局，此运人际关系顺畅，与朋友的合作或交流带来积极成果。",
                        )
                    elif itype in CYCLE_STAGNATION_TYPES:
                        _add(
                            "月柱伏吟",
                            "大运与月柱伏吟，社交关系停滞，朋友圈缺乏新鲜流动，旧有关系维持但难有突破。",
                        )

    if not status_parts:
        return {
            "运势": "平稳",
            "解读": "此运朋友人际无明显触动，社交格局延续既有模式。",
        }

    return {"运势": "、".join(status_parts), "解读": "；".join(jiedu_parts)}


def _get_cycle_relationship_events(
    da_yun: dict,
    shen_sha: dict,
    bazi: dict,
    shi_shen: dict,
    interactions: dict,
    gender: int,
    xun_kong: dict,
    branch_chars: dict,
    dm_elem: str,
) -> list[dict]:
    """
    Iterates all 大运 cycles and produces one entry per cycle with three domain assessments.
    Skips the index-0 placeholder ("未行大运").
    """
    today_year = date.today().year
    natal_year_branch = bazi["八字"]["年柱"]["地支"]
    natal_day_branch = bazi["八字"]["日柱"]["地支"]
    cycles = da_yun.get("大运", {}).get("大运周期", [])[1:]
    events = []

    for cycle in cycles:
        if not isinstance(cycle.get("作用"), dict):
            continue  # skip placeholder

        if cycle.get("当运"):
            status = "当运"
        elif cycle.get("结束年份", 9999) < today_year:
            status = "已过"
        else:
            status = "未来"

        events.append(
            {
                "大运": cycle.get("周期", ""),
                "运势": status,
                "感情": _evaluate_romance_for_cycle(
                    cycle,
                    natal_year_branch,
                    natal_day_branch,
                    shi_shen,
                    interactions,
                    gender,
                    xun_kong,
                    branch_chars,
                    dm_elem,
                ),
                "原生家庭": _evaluate_family_for_cycle(
                    cycle, shi_shen, interactions, bazi
                ),
                "朋友人际": _evaluate_friendship_for_cycle(
                    cycle, shi_shen, interactions, dm_elem
                ),
            }
        )

    return events


# ── Public API ────────────────────────────────────────────────────────────────


def extract_relationship_insights(raw_data: dict) -> dict:
    """
    Pre-compute structural relationship patterns from raw aggregator output.

    Args:
        raw_data: Output of AstroDataAggregator.collect_data()

    Returns:
        {
            "命盘关系格局": {
                "感情":    list[dict],
                "原生家庭": list[dict],
                "朋友人际": list[dict],
            },
            "大运感情动态": list[dict],
            "无格局提示":   str | None
        }
    """
    shi_shen = raw_data["shi_shen"]["十神"]
    ri_zhu = raw_data["day_master"]["日主"]
    bazi = raw_data["bazi"]
    wu_xing = raw_data["wu_xing"]["五行力量"]["五行力量分析"]
    da_yun = raw_data["da_yun"]
    interactions = raw_data["interactions"]
    xun_kong = raw_data["xun_kong"]
    shen_sha = raw_data["shen_sha"]
    gender = 1 if raw_data["basic_info"]["性别"] == "男" else 0
    dm_elem = ri_zhu["五行"]
    score = ri_zhu["强弱分数"]

    branch_chars = _get_branch_chars(bazi)

    # ── Natal patterns ───────────────────────────────────────────────────────
    romance_patterns = (
        _check_peach_blossom(shen_sha, branch_chars)
        + _check_peach_blossom_with_danger(
            shen_sha, shi_shen, wu_xing, dm_elem, interactions
        )
        + _check_marriage_stars(shen_sha)
        + _check_isolation_stars(shen_sha)
        + _check_day_pillar_quality(interactions, xun_kong, branch_chars)
        + _check_spouse_star(
            shi_shen,
            interactions,
            xun_kong,
            branch_chars,
            gender,
            score,
            wu_xing,
            dm_elem,
        )
        + _check_expression_strength(wu_xing, dm_elem)
        + _check_divorce_remarriage(shi_shen, interactions, branch_chars, gender)
    )

    family_patterns = (
        _check_mother_patterns(
            shi_shen, interactions, xun_kong, branch_chars, wu_xing, dm_elem
        )
        + _check_father_patterns(shi_shen, interactions, xun_kong, branch_chars)
        + _check_parental_harmony(bazi, interactions)
        + _check_upbringing_quality(shen_sha, shi_shen)
    )

    friendship_patterns = _check_friendship_patterns(
        shi_shen, wu_xing, dm_elem, shen_sha, interactions
    )

    all_patterns = romance_patterns + family_patterns + friendship_patterns

    # ── Cycle events ─────────────────────────────────────────────────────────
    cycle_events = _get_cycle_relationship_events(
        da_yun,
        shen_sha,
        bazi,
        shi_shen,
        interactions,
        gender,
        xun_kong,
        branch_chars,
        dm_elem,
    )

    return {
        "命盘关系格局": {
            "感情": romance_patterns,
            "原生家庭": family_patterns,
            "朋友人际": friendship_patterns,
        },
        "大运感情动态": cycle_events,
        "无格局提示": (
            "关系格局特征不显著，关系运走向主要依赖大运与自身经营。"
            if not all_patterns
            else None
        ),
    }


# ============================================================================
# EXECUTION
# python -m src.astronomer_calculations.interpretive_insights_relationships
# ============================================================================

if __name__ == "__main__":
    import json
    from datetime import datetime as dt
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
    from src.services.astronomer_data_aggregator import AstroDataAggregator
    from src.utils.logging import configure_logging, get_logger

    configure_logging()
    logger = get_logger(__name__)

    # python -m src.astronomer_calculations.interpretive_insights_relationships

    subjects = {
        "Desmond": (dt(1985, 11, 25, 17, 7, 0), 1.3253, 103.808053, 1),
    }

    for name, (birthday, lat, lon, gender) in subjects.items():
        logger.info("=" * 60)
        logger.info("Subject: %s  (%s)", name, birthday.strftime("%Y-%m-%d %H:%M"))

        tst_birthday, _ = get_true_solar_time(birthday, lat, lon)
        lunar_birthday = tst_birthday.getLunar()

        raw_data = AstroDataAggregator().collect_data(
            lunar_birthday,
            birth_datetime=birthday,
            latitude=lat,
            longitude=lon,
            gender=gender,
        )

        insights = extract_relationship_insights(raw_data)
        logger.info(json.dumps(insights, ensure_ascii=False, indent=2))
