"""
Health Interpretive Insights

Pre-computes structural BaZi health patterns from raw aggregator data and returns
labeled facts for LLM injection. Health is multi-factorial — no single dominant pattern.
Instead, the module provides a list of patterns across 5 tiers, plus a simplified summary.

Output structure:
    {
        "健康综合评估": {
            "整体体质": str,
            "主要风险": list,
            "有利因素": list,
            "综合解读": str
        },
        "命盘健康格局": [...],     # natal patterns — always true
        "大运健康动态": [...],     # temporal layer — only cycles with health effects
        "无格局提示": str | None
    }
"""

from datetime import date

# ───────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ───────────────────────────────────────────────────────────────────────────────

PILLARS = ["年柱", "月柱", "日柱", "时柱"]
BRANCH_TIERS = ["本气", "中气", "余气"]
ACTIVE_STRENGTHS = {"强势主流", "显著影响", "中等影响"}

# 十二长生 vitality classification (not used in health module but kept for reference)
STRONG_VITALITY_STAGES = {"长生", "沐浴", "冠带", "临官", "帝旺"}
WEAK_VITALITY_STAGES = {"衰", "病", "死", "墓", "绝"}

# Element derivation maps (from wealth module)
YIN_ELEMENT_MAP = {"木": "水", "火": "木", "土": "火", "金": "土", "水": "金"}  # 印星
FOOD_GOD_MAP = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}  # 食伤
WEALTH_MAP = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}  # 财星
CONTROLS_DM_MAP = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}  # 官杀

STEM_ELEMENT_MAP = {
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

BRANCH_ELEMENT_MAP = {
    "子": "水",
    "亥": "水",
    "寅": "木",
    "卯": "木",
    "巳": "火",
    "午": "火",
    "申": "金",
    "酉": "金",
    "辰": "土",
    "戌": "土",
    "丑": "土",
    "未": "土",
}

# Element tier classification
EXCESS_TIERS = {"偏旺", "极旺", "极亢"}
DEFICIENCY_TIERS = {"极弱", "缺失"}
STRONG_TIERS = {"偏旺", "极旺", "极亢", "中和"}
WEAK_TIERS = {"偏弱", "极弱", "缺失"}

ELEMENT_BODY_MAP = {
    "木": "肝胆、神经系统、筋腱",
    "火": "心脏、小肠、循环系统、视力",
    "土": "脾胃、消化系统、肌肉",
    "金": "肺、大肠、皮肤、呼吸系统",
    "水": "肾脏、膀胱、骨骼、内分泌、腰椎",
}

# Shen sha sets
HEALING_STARS = {"天医", "天乙贵人", "天德贵人", "月德贵人", "天德", "月德"}
INJURY_STARS = {"血刃", "白虎"}
ILLNESS_STARS = {"丧门", "吊客", "病符"}

# Pattern taxonomy
PROTECTIVE_IDS = {
    "dm_strong",
    "seal_strong",
    "tian_yi_health",
    "tian_doctor",
    "tian_de_yue_de",
}

RISK_IDS = {
    "dm_weak",
    "fire_excess",
    "water_excess",
    "wood_excess",
    "metal_excess",
    "earth_excess",
    "fire_deficient",
    "water_deficient",
    "wood_deficient",
    "metal_deficient",
    "earth_deficient",
    "official_excess",
    "expression_excess",
    "expression_weak",
    "peer_excess",
    "wealth_excess",
    "seal_weak",
    "day_pillar_clashed",
    "day_pillar_harmed",
    "day_pillar_punished",
    "day_pillar_void",
    "day_pillar_self_punishment",
    "xue_ren",
    "diao_ke",
    "sang_men",
    "bai_hu",
    "bing_fu",
}

NEUTRAL_IDS = {"dm_moderate", "day_branch_weak_element"}


# ───────────────────────────────────────────────────────────────────────────────
# SHARED HELPERS (from wealth/career modules)
# ───────────────────────────────────────────────────────────────────────────────


def _get_branch_chars(bazi: dict) -> dict:
    """Extract branch characters from all four pillars."""
    zhu_entities = bazi.get("八字", {})
    return {
        "年支": zhu_entities.get("年柱", {}).get("地支", ""),
        "月支": zhu_entities.get("月柱", {}).get("地支", ""),
        "日支": zhu_entities.get("日柱", {}).get("地支", ""),
        "时支": zhu_entities.get("时柱", {}).get("地支", ""),
    }


def _void_branch_positions(branch_chars: dict, xun_kong: dict) -> set:
    """Identify which branch positions are in旬空."""
    voided = set()
    pillar_keys = ["年支", "月支", "日支", "时支"]
    for pillar_key in pillar_keys:
        branch_char = branch_chars.get(pillar_key, "")
        xun_kong_str = xun_kong.get("旬空", {}).get(pillar_key, {}).get("旬空", "")
        if branch_char in xun_kong_str:
            voided.add(pillar_key)
    return voided


def _has_chong_xing_on_pillar(pillar_name: str, interactions: dict) -> bool:
    """Check if a pillar has active 六冲 or 三刑."""
    pillar_data = interactions.get("作用", {}).get("柱位动态", {}).get(pillar_name, {})
    for tier_list in pillar_data.values():
        if not isinstance(tier_list, list):
            continue
        for item in tier_list:
            interaction_type = item.get("类型", "")
            strength = item.get("强度", "")
            clash_types = {"六冲", "无恩之刑", "恃势之刑", "无礼之刑", "自刑"}
            if interaction_type in clash_types and strength in ACTIVE_STRENGTHS:
                return True
    return False


def _get_shen_sha_for_pillar(shen_sha_raw: dict, pillar: str) -> list:
    """Return shen sha list for a given pillar."""
    return shen_sha_raw.get("柱位神煞", {}).get(pillar, {}).get("神煞", [])


# ───────────────────────────────────────────────────────────────────────────────
# TIER 1 — CONSTITUTIONAL STRENGTH
# ───────────────────────────────────────────────────────────────────────────────


def _pattern_dm_strength(day_master: dict) -> list:
    """Return constitutional strength patterns based on DM score."""
    score = day_master.get("强弱分数", 0)
    candidates = []

    if score >= 3:
        candidates.append(
            (
                "dm_strong",
                "先天体质强",
                {
                    "解读": "日主强旺，先天体质强健，精力充沛，恢复力佳，适应力强。",
                    "依据": f"强弱分数: {score}/5",
                },
            )
        )
    elif score == 2:
        candidates.append(
            (
                "dm_moderate",
                "体质中和",
                {
                    "解读": "日主中等强度，体质平稳，健康随大运与生活习惯起伏。",
                    "依据": f"强弱分数: {score}/5",
                },
            )
        )
    else:  # score <= 1
        candidates.append(
            (
                "dm_weak",
                "先天体质偏弱",
                {
                    "解读": "日主弱，先天体质偏弱，易疲劳，需注重养生、保守为主。",
                    "依据": f"强弱分数: {score}/5",
                },
            )
        )

    return candidates


def _pattern_element_imbalance(wu_xing_analysis: dict) -> list:
    """Return element excess/deficiency patterns."""
    candidates = []
    elements = ["木", "火", "土", "金", "水"]

    for elem in elements:
        elem_data = wu_xing_analysis.get(elem, {})
        pct = elem_data.get("百分比", 0.0)
        tier = elem_data.get("能级", {}).get("名称", "")
        body_system = ELEMENT_BODY_MAP.get(elem, "相关脏腑系统")

        if tier in EXCESS_TIERS:
            excess_texts = {
                "火": f"五行火偏旺（{pct:.1f}%，{tier}），心脏、循环、血压易有问题，易上火、失眠、情绪急躁。",
                "水": "五行水偏旺，肾气虚寒、易水肿、手脚冰凉、膀胱功能负荷重。",
                "木": "五行木偏旺，肝胆压力大、易紧张焦虑、筋腱僵硬。",
                "金": "五行金偏旺，肺与大肠易有问题，皮肤敏感、呼吸道阻塞、情绪压抑。",
                "土": "五行土偏旺，脾胃负荷重、消化不良、体重增长趋势、肌肉酸胀。",
            }
            candidates.append(
                (
                    f"{elem}_excess",
                    f"{elem}旺",
                    {
                        "解读": excess_texts.get(
                            elem, f"五行{elem}过旺，{body_system}功能亢进。"
                        ),
                        "依据": f"五行{elem}: {pct:.1f}% ({tier})",
                    },
                )
            )

        elif tier in DEFICIENCY_TIERS:
            deficiency_texts = {
                "火": "五行火不足，循环偏差、手脚易冷、心气弱，情绪易低落。",
                "水": "五行水不足，肾气偏虚、腰背易酸痛、内分泌偏弱。",
                "木": "五行木不足，肝血弱、视力易疲劳、筋腱弹性差。",
                "金": "五行金不足，肺气弱、免疫力偏低、皮肤易干燥。",
                "土": "五行土不足，脾胃虚弱、营养吸收差、肌肉力量弱。",
            }
            candidates.append(
                (
                    f"{elem}_deficient",
                    f"{elem}缺",
                    {
                        "解读": deficiency_texts.get(
                            elem, f"五行{elem}缺失，{body_system}功能低下。"
                        ),
                        "依据": f"五行{elem}: {pct:.1f}% ({tier})",
                    },
                )
            )

    return candidates


# ───────────────────────────────────────────────────────────────────────────────
# TIER 2 — TEN-GOD HEALTH INDICATORS
# ───────────────────────────────────────────────────────────────────────────────


def _pattern_ten_god_health(
    wu_xing_analysis: dict, dm_elem: str, dm_score: int
) -> list:
    """Return ten-god health patterns (seal, official, expression, peer, wealth).

    Interpretations are nuanced by constitutional strength (dm_score) to reflect
    real-world health manifestations rather than absolute worst-case scenarios.
    """
    candidates = []

    if not dm_elem:
        return candidates

    # Seal (印星) — interpretation nuanced by constitutional strength
    seal_elem = YIN_ELEMENT_MAP.get(dm_elem)
    if seal_elem:
        seal_tier = wu_xing_analysis.get(seal_elem, {}).get("能级", {}).get("名称", "")
        if seal_tier in STRONG_TIERS:
            candidates.append(
                (
                    "seal_strong",
                    "印星有力",
                    {
                        "解读": "印星元素充足，免疫力佳，患病恢复快，易获医疗与家人支持。",
                        "依据": f"印星{seal_elem}: {seal_tier}",
                    },
                )
            )
        elif seal_tier in WEAK_TIERS:
            # Nuance seal_weak interpretation based on constitutional strength
            if dm_score >= 3:
                seal_interpretation = (
                    "印星元素偏弱，但因日主强健，表现为慢性、局部性的免疫薄弱环节"
                    "（如呼吸道敏感、消化偏弱、易疲劳），而非频繁大病；恢复能力尚可。"
                )
            elif dm_score <= 1:
                seal_interpretation = (
                    "印星元素偏弱，自愈力弱，免疫偏低，患病后恢复缓慢，缺乏照护资源，"
                    "健康基础脆弱，需重视预防与调理。"
                )
            else:  # dm_score == 2
                seal_interpretation = (
                    "印星元素偏弱，自愈力与免疫力有所不足，患病后恢复较慢，"
                    "需注意呼吸、消化系统保健。"
                )

            candidates.append(
                (
                    "seal_weak",
                    "印星不足",
                    {
                        "解读": seal_interpretation,
                        "依据": f"印星{seal_elem}: {seal_tier}；日主强弱分数: {dm_score}/5",
                    },
                )
            )

    # Official/Killing (官杀) — stress impact nuanced by constitution
    official_elem = CONTROLS_DM_MAP.get(dm_elem)
    if official_elem:
        official_tier = (
            wu_xing_analysis.get(official_elem, {}).get("能级", {}).get("名称", "")
        )
        if official_tier in EXCESS_TIERS:
            # Nuance official_excess based on DM ability to absorb pressure
            if dm_score >= 3:
                official_interpretation = (
                    "官杀元素过旺，日主受压制，但因体质强健，可较好应对压力环境，"
                    "主要表现为工作效率下降、情绪波动，而非重症；需定期放松缓压。"
                )
            elif dm_score <= 1:
                official_interpretation = (
                    "官杀元素过旺，日主被持续压制，体质脆弱无力对抗，易焦虑、抑郁、"
                    "高血压、免疫下降，需尽快改善压力环境，调理刻不容缓。"
                )
            else:  # dm_score == 2
                official_interpretation = (
                    "官杀元素过旺，日主受压制，慢性压力明显，易焦虑、情绪耗竭，"
                    "需主动减压与体质调理相结合。"
                )

            candidates.append(
                (
                    "official_excess",
                    "官杀过旺",
                    {
                        "解读": official_interpretation,
                        "依据": f"官杀{official_elem}: {official_tier}；日主强弱分数: {dm_score}/5",
                    },
                )
            )

    # Expression/Talent (食伤) — talent overflow nuanced by constitution
    food_elem = FOOD_GOD_MAP.get(dm_elem)
    if food_elem:
        food_tier = wu_xing_analysis.get(food_elem, {}).get("能级", {}).get("名称", "")
        if food_tier in EXCESS_TIERS:
            # Nuance expression_excess based on DM ability to manage talent overflow
            if dm_score >= 3:
                expression_excess_interpretation = (
                    "食伤元素过旺，创意充沛、想法多，但日主强健可驾驭此创造力，"
                    "主要表现为思虑过多、偶有失眠，通过规律作息与适度放松可调节。"
                )
            elif dm_score <= 1:
                expression_excess_interpretation = (
                    "食伤元素过旺，泄耗日主元气，新陈代谢亢进，易失眠、神经过敏、"
                    "慢性疲劳，体质难以承载此消耗，需严格规律作息与修养。"
                )
            else:  # dm_score == 2
                expression_excess_interpretation = (
                    "食伤元素过旺，泄耗日主元气，新陈代谢亢进，易失眠、神经过敏、"
                    "需注意调节作息与放松。"
                )

            candidates.append(
                (
                    "expression_excess",
                    "食伤过旺",
                    {
                        "解读": expression_excess_interpretation,
                        "依据": f"食伤{food_elem}: {food_tier}；日主强弱分数: {dm_score}/5",
                    },
                )
            )
        elif food_tier in DEFICIENCY_TIERS:
            # Nuance expression_weak based on constitutional support
            if dm_score >= 3:
                expression_weak_interpretation = (
                    "食伤元素不足，消化与代谢基础偏弱，但因日主强健，整体功能尚可维持，"
                    "主要表现为消化敏感、偶有便秘，通过适度运动与调整饮食可改善。"
                )
            elif dm_score <= 1:
                expression_weak_interpretation = (
                    "食伤元素不足，消化与代谢严重偏弱，易便秘、体力迟钝、食欲不佳、"
                    "情绪压抑，需从脾胃调理着手，逐步恢复代谢能力。"
                )
            else:  # dm_score == 2
                expression_weak_interpretation = (
                    "食伤元素不足，消化与代谢偏弱，易便秘、体力迟钝，"
                    "需重视脾胃保健与适度运动。"
                )

            candidates.append(
                (
                    "expression_weak",
                    "食伤不足",
                    {
                        "解读": expression_weak_interpretation,
                        "依据": f"食伤{food_elem}: {food_tier}；日主强弱分数: {dm_score}/5",
                    },
                )
            )

    # Peer (比劫) — overactivity nuanced by constitution
    peer_tier = wu_xing_analysis.get(dm_elem, {}).get("能级", {}).get("名称", "")
    if peer_tier in EXCESS_TIERS:
        # Nuance peer_excess based on DM ability to manage overactivity
        if dm_score >= 3:
            peer_interpretation = (
                "比劫元素过旺，体能旺盛、竞争心强，但因日主强健，可良好驾驭此能量，"
                "主要表现为好胜、活力充沛，受伤风险较低，需适度分散竞争压力。"
            )
        elif dm_score <= 1:
            peer_interpretation = (
                "比劫元素过旺，体能过度消耗、好强逞能，体质难以支撑此频繁较量，"
                "易在竞争或运动中受伤、劳损，甚至积累成慢性疾患，需适度退避、积蓄内力。"
            )
        else:  # dm_score == 2
            peer_interpretation = (
                "比劫元素过旺，体能亢进、好强逞能，易在竞争或运动中受伤，"
                "需注意强度的适度与恢复时间的安排。"
            )

        candidates.append(
            (
                "peer_excess",
                "比劫过旺",
                {
                    "解读": peer_interpretation,
                    "依据": f"比劫{dm_elem}: {peer_tier}；日主强弱分数: {dm_score}/5",
                },
            )
        )

    # Wealth (财星) — excessive pursuit nuanced by constitution
    wealth_elem = WEALTH_MAP.get(dm_elem)
    if wealth_elem:
        wealth_tier = (
            wu_xing_analysis.get(wealth_elem, {}).get("能级", {}).get("名称", "")
        )
        if wealth_tier in EXCESS_TIERS:
            # Nuance wealth_excess based on DM resilience under stress
            if dm_score >= 3:
                wealth_interpretation = (
                    "财星元素过旺，物质追求心切、思虑繁重，但因日主强健，可较好应对工作压力，"
                    "主要表现为精神紧张、偶有疲劳，通过适度放松与调理可恢复，"
                    "劳损与代谢性疾患风险相对较低。"
                )
            elif dm_score <= 1:
                wealth_interpretation = (
                    "财星元素过旺，日主难以驾驭，思虑过多、操劳过度，体质脆弱易积累劳损，"
                    "易患代谢性疾患（血糖、血脂异常）与脾胃虚弱，需严格控制工作强度、定期调理。"
                )
            else:  # dm_score == 2
                wealth_interpretation = (
                    "财星元素过旺，日主难以驾驭，思虑过多、操劳过度，易有劳损与代谢性疾患，"
                    "需注意工作与休息的平衡、饮食管理。"
                )

            candidates.append(
                (
                    "wealth_excess",
                    "财星过旺",
                    {
                        "解读": wealth_interpretation,
                        "依据": f"财星{wealth_elem}: {wealth_tier}；日主强弱分数: {dm_score}/5",
                    },
                )
            )

    return candidates


# ───────────────────────────────────────────────────────────────────────────────
# TIER 3 — DAY PILLAR HEALTH INDICATORS
# ───────────────────────────────────────────────────────────────────────────────


def _pattern_day_pillar_interactions(interactions: dict, dm_score: int) -> list:
    """Return day pillar clash/harm/punishment patterns, nuanced by constitutional strength.

    Args:
        interactions: Pillar interaction data
        dm_score: Day Master strength (0-5), used to modulate interpretation severity
    """
    candidates = []

    pillar_data = interactions.get("作用", {}).get("柱位动态", {}).get("日柱", {})
    for tier_list in pillar_data.values():
        if not isinstance(tier_list, list):
            continue
        for item in tier_list:
            interaction_type = item.get("类型", "")
            strength = item.get("强度", "")

            if strength not in ACTIVE_STRENGTHS:
                continue

            if interaction_type == "六冲":
                # Nuance clash interpretation by constitutional strength
                if dm_score >= 3:
                    clash_interpretation = (
                        "日柱受冲，身宫受压，虽有突发健康危机、意外事故或手术风险，"
                        "但因体质强健，通常能较快康复，需防范但不必过度忧虑。"
                    )
                elif dm_score <= 1:
                    clash_interpretation = (
                        "日柱受冲，身宫受压，易有严重突发健康危机、意外事故或手术，"
                        "康复时间长、易留后遗症，需格外小心谨慎。"
                    )
                else:  # dm_score == 2
                    clash_interpretation = (
                        "日柱受冲，身宫受压，易有突发健康危机、意外事故或手术，"
                        "需加强防范意识与定期检查。"
                    )

                candidates.append(
                    (
                        "day_pillar_clashed",
                        "日柱受冲",
                        {
                            "解读": clash_interpretation,
                            "依据": f"日柱受六冲；日主强弱分数: {dm_score}/5",
                        },
                    )
                )
            elif interaction_type == "六害":
                # Nuance harm interpretation by constitutional strength
                if dm_score >= 3:
                    harm_interpretation = (
                        "日柱受害，慢性隐患多，疾病易反复，但因体质基础良好，"
                        "可通过主动调理与规律养生缓解，预后相对较佳。"
                    )
                elif dm_score <= 1:
                    harm_interpretation = (
                        "日柱受害，慢性隐患多，疾病易久治不愈或反复发作，"
                        "康复困难，需长期耐心调理与医学监测。"
                    )
                else:  # dm_score == 2
                    harm_interpretation = (
                        "日柱受害，慢性隐患多，疾病易久治不愈或反复发作，"
                        "需注意预防与定期检查。"
                    )

                candidates.append(
                    (
                        "day_pillar_harmed",
                        "日柱受害",
                        {
                            "解读": harm_interpretation,
                            "依据": f"日柱受六害；日主强弱分数: {dm_score}/5",
                        },
                    )
                )
            elif interaction_type in {"无恩之刑", "恃势之刑", "无礼之刑"}:
                # Nuance punishment interpretation by constitutional strength
                if dm_score >= 3:
                    punishment_interpretation = (
                        "日柱受刑，心身冲突，易有身心性疾患、自律神经失调，"
                        "但因体质强韧，可通过心理调适与运动缓解，不至于长期困扰。"
                    )
                elif dm_score <= 1:
                    punishment_interpretation = (
                        "日柱受刑，心身冲突，易有严重身心性疾患、自律神经失调、免疫问题，"
                        "体质脆弱难以自愈，需重视心理疏导与身体调理相结合。"
                    )
                else:  # dm_score == 2
                    punishment_interpretation = (
                        "日柱受刑，心身冲突，易有身心性疾患、自律神经失调、免疫问题，"
                        "需注意情绪管理与身体保养。"
                    )

                candidates.append(
                    (
                        "day_pillar_punished",
                        "日柱受刑",
                        {
                            "解读": punishment_interpretation,
                            "依据": f"日柱受{interaction_type}；日主强弱分数: {dm_score}/5",
                        },
                    )
                )
            elif interaction_type == "自刑":
                # Nuance self-punishment interpretation by constitutional strength
                if dm_score >= 3:
                    self_punishment_interpretation = (
                        "日柱自刑，易因自我忽视或过度消耗而伤身，但因体质强健，"
                        "只要提高自觉性、及时修正行为，恢复较快，预防价值高。"
                    )
                elif dm_score <= 1:
                    self_punishment_interpretation = (
                        "日柱自刑，健康问题易由自我忽视或过度消耗引起，"
                        "体质脆弱易形成积累性伤害，需格外提高自我警觉与主动调理。"
                    )
                else:  # dm_score == 2
                    self_punishment_interpretation = (
                        "日柱自刑，健康问题易由自我忽视或过度消耗引起，"
                        "需主动警觉与及时修正。"
                    )

                candidates.append(
                    (
                        "day_pillar_self_punishment",
                        "日柱自刑",
                        {
                            "解读": self_punishment_interpretation,
                            "依据": f"日柱自刑；日主强弱分数: {dm_score}/5",
                        },
                    )
                )

    return candidates


def _pattern_day_pillar_void(branch_chars: dict, xun_kong: dict) -> tuple | None:
    """Fires if Day Branch is in旬空."""
    voided = _void_branch_positions(branch_chars, xun_kong)
    if "日支" not in voided:
        return None
    day_branch = branch_chars.get("日支", "")
    return (
        "day_pillar_void",
        "日支落空",
        {
            "解读": f"日支{day_branch}落旬空，身宫地支虚浮—先天体力底气不足，精力容易不济、体质看似正常实则内虚。",
            "依据": f"日支{day_branch}落旬空",
        },
    )


def _pattern_day_branch_weak_element(
    bazi: dict, wu_xing_analysis: dict
) -> tuple | None:
    """Fires if Day Branch's element is weak in five-element distribution."""
    day_branch = bazi.get("八字", {}).get("日柱", {}).get("地支", "")
    if not day_branch:
        return None

    branch_elem = BRANCH_ELEMENT_MAP.get(day_branch)
    if not branch_elem:
        return None

    elem_tier = wu_xing_analysis.get(branch_elem, {}).get("能级", {}).get("名称", "")
    if elem_tier not in WEAK_TIERS:
        return None

    body_system = ELEMENT_BODY_MAP.get(branch_elem, "相关脏腑系统")
    return (
        "day_branch_weak_element",
        f"日支{branch_elem}弱",
        {
            "解读": f"日支地支元素{branch_elem}不足，对应{body_system}为先天薄弱环节。",
            "依据": f"日支{day_branch}对应元素{branch_elem}: {elem_tier}",
        },
    )


# ───────────────────────────────────────────────────────────────────────────────
# TIER 4 — SHEN SHA HEALTH INDICATORS
# ───────────────────────────────────────────────────────────────────────────────


def _pattern_shen_sha_health(shen_sha_raw: dict, dm_score: int) -> list:
    """Return shen sha health indicators, nuanced by constitutional strength.

    Args:
        shen_sha_raw: Shen sha data
        dm_score: Day Master strength (0-5), used to modulate interpretation severity
    """
    # Gather all unique stars across all 4 pillars first
    found_stars = set()
    for pillar in PILLARS:
        found_stars.update(_get_shen_sha_for_pillar(shen_sha_raw, pillar))

    candidates = []

    # Process injury stars (血刃, 白虎) with constitutional nuance
    if "血刃" in found_stars:
        if dm_score >= 3:
            xue_ren_interpretation = (
                "血刃入命，一生中血液相关事件风险偏高（手术、外伤、妇科），"
                "但因体质强健，若发生此类事件，恢复迅速，预后良好。"
            )
        elif dm_score <= 1:
            xue_ren_interpretation = (
                "血刃入命，一生中血液相关事件风险偏高（手术、外伤、妇科），"
                "体质脆弱易因此类事件引发后遗症，需特别防范与谨慎调理。"
            )
        else:  # dm_score == 2
            xue_ren_interpretation = (
                "血刃入命，一生中血液相关事件风险偏高（手术、外伤、妇科），"
                "需加强防范意识与术后调理。"
            )

        candidates.append(
            (
                "xue_ren",
                "血刃",
                {
                    "解读": xue_ren_interpretation,
                    "依据": f"命局带有血刃；日主强弱分数: {dm_score}/5",
                },
            )
        )

    if "白虎" in found_stars:
        if dm_score >= 3:
            bai_hu_interpretation = (
                "白虎入命，外伤与手术风险偏高，"
                "但因体质强健，防范得当可降低事件风险，若发生也能较快康复。"
            )
        elif dm_score <= 1:
            bai_hu_interpretation = (
                "白虎入命，外伤与手术风险偏高，体质脆弱易因此类伤痛引发长期影响，"
                "需特别防范意外撞击与有创医疗，防范刻不容缓。"
            )
        else:  # dm_score == 2
            bai_hu_interpretation = (
                "白虎入命，外伤与手术风险偏高，" "需防意外撞击与有创医疗，谨慎为上。"
            )

        candidates.append(
            (
                "bai_hu",
                "白虎",
                {
                    "解读": bai_hu_interpretation,
                    "依据": f"命局带有白虎；日主强弱分数: {dm_score}/5",
                },
            )
        )

    # Process illness stars (吊客, 丧门, 病符) with constitutional nuance
    if "吊客" in found_stars:
        if dm_score >= 3:
            diao_ke_interpretation = (
                "吊客入命，一生中易有重病阶段或因亲人离丧影响心理，"
                "但因体质强健，渡过难期后恢复较快，不至于长期困扰。"
            )
        elif dm_score <= 1:
            diao_ke_interpretation = (
                "吊客入命，一生中易有重病阶段或因亲人离丧影响健康心理，"
                "体质脆弱易导致心病化生理病，哀伤对体质的累积损耗严重，需长期心理调适。"
            )
        else:  # dm_score == 2
            diao_ke_interpretation = (
                "吊客入命，一生中易有重病阶段或因亲人离丧影响健康心理，"
                "需留意哀伤对体质的累积损耗。"
            )

        candidates.append(
            (
                "diao_ke",
                "吊客",
                {
                    "解读": diao_ke_interpretation,
                    "依据": f"命局带有吊客；日主强弱分数: {dm_score}/5",
                },
            )
        )

    if "丧门" in found_stars:
        if dm_score >= 3:
            sang_men_interpretation = (
                "丧门入命，易遭遇大病或丧亲悲痛事件，"
                "但因体质强健，可较好承受压力与悲痛，恢复能力强。"
            )
        elif dm_score <= 1:
            sang_men_interpretation = (
                "丧门入命，易遭遇大病或丧亲悲痛，体质脆弱难以抵挡此类打击，"
                "哀伤对体质的累积损耗严重，易引发长期病患，需格外注意预防与调理。"
            )
        else:  # dm_score == 2
            sang_men_interpretation = (
                "丧门入命，易遭遇大病或丧亲悲痛，" "需留意哀伤对体质的累积损耗。"
            )

        candidates.append(
            (
                "sang_men",
                "丧门",
                {
                    "解读": sang_men_interpretation,
                    "依据": f"命局带有丧门；日主强弱分数: {dm_score}/5",
                },
            )
        )

    if "病符" in found_stars:
        if dm_score >= 3:
            bing_fu_interpretation = (
                "病符入命，慢性病与反复发作的健康问题风险偏高，"
                "但因体质强健，定期检查与预防保健可有效降低风险。"
            )
        elif dm_score <= 1:
            bing_fu_interpretation = (
                "病符入命，慢性病与反复发作的健康问题风险偏高，"
                "体质脆弱易导致小病频繁复发、难以根治，需重视定期检查与长期调理。"
            )
        else:  # dm_score == 2
            bing_fu_interpretation = (
                "病符入命，慢性病与反复发作的健康问题风险偏高，"
                "需注重定期检查与预防保健。"
            )

        candidates.append(
            (
                "bing_fu",
                "病符",
                {
                    "解读": bing_fu_interpretation,
                    "依据": f"命局带有病符；日主强弱分数: {dm_score}/5",
                },
            )
        )

    # Process healing stars (天医, 天乙贵人, 天德/月德) — no nuance needed as they are protective
    if "天医" in found_stars:
        candidates.append(
            (
                "tian_doctor",
                "天医护体",
                {
                    "解读": "天医入命，具备天然自愈能力，患病时易遇良医，健康恢复力强。",
                    "依据": "命局带有天医",
                },
            )
        )

    if "天乙贵人" in found_stars:
        candidates.append(
            (
                "tian_yi_health",
                "天乙贵人",
                {
                    "解读": "天乙贵人入命，医缘佳，危难时有贵人（医生/亲属）出手相助。",
                    "依据": "命局带有天乙贵人",
                },
            )
        )

    # Handle the combined group for Tiande / Yuede
    if found_stars.intersection({"天德贵人", "月德贵人", "天德", "月德"}):
        candidates.append(
            (
                "tian_de_yue_de",
                "天德月德护体",
                {
                    "解读": "天德/月德入命，具有强大护佑力，大病中能化险为夷，康复力佳。",
                    "依据": "命局带有天德/月德",
                },
            )
        )

    return candidates


# ───────────────────────────────────────────────────────────────────────────────
# TIER 5 — CYCLE EVENTS (大运健康动态)
# ───────────────────────────────────────────────────────────────────────────────


def _modulate_effect_by_constitution(effect: dict, dm_score: int) -> dict:
    """Modulate effect 解读 and 强度 based on constitutional strength.

    Args:
        effect: Health effect dict with ' 解读' and '强度' keys
        dm_score: Day Master strength (0-5)

    Returns:
        Modified effect dict with constitutional context added to 解读 and adjusted 强度
    """
    modified = effect.copy()
    original_jieyue = modified.get("解读", "")

    if dm_score <= 1:
        # Weak constitution: amplify risk, upgrade severity
        modified["解读"] = (
            original_jieyue + " 因先天体质偏弱，此影响更为显著，需格外防范与调理。"
        )
        # Upgrade severity caps: 中等 → 显著, 显著 → 强势
        strength = modified.get("强度", "")
        if strength == "中等影响":
            modified["强度"] = "显著影响"
        elif strength == "显著影响":
            modified["强度"] = "强势主流"

    elif dm_score >= 3:
        # Strong constitution: emphasize resilience, downgrade severity
        modified["解读"] = (
            original_jieyue + " 因体质强健，此影响尚在可控范围，恢复较快。"
        )
        # Downgrade severity: 强势 → 显著, 显著 → 中等, 中等 → 大幅衰减
        strength = modified.get("强度", "")
        if strength == "强势主流":
            modified["强度"] = "显著影响"
        elif strength == "显著影响":
            modified["强度"] = "中等影响"
        elif strength == "中等影响":
            modified["强度"] = "大幅衰减"

    # dm_score == 2 (moderate): no adjustment, use as-is

    return modified


def _get_cycle_health_events(
    da_yun: dict, dm_elem: str, dm_score: int, branch_chars: dict
) -> list:
    """Collect health effects from each decade cycle, modulated by DM score (constitution).

    Args:
        da_yun: Decade cycle data
        dm_elem: Day Master element
        dm_score: Constitutional strength (0-5)
        branch_chars: Branch character positions

    DM score modulation:
        - score <= 1 (weak): upgrade severity, emphasize vulnerability
        - score == 2 (moderate): neutral, no adjustment
        - score >= 3 (strong): downgrade severity, emphasize resilience
    """
    today_year = date.today().year
    cycles = da_yun.get("大运", {}).get("大运周期", [])[1:]  # skip placeholder
    events = []

    for cycle in cycles:
        effects = []

        # Element-based effects
        run_stem = cycle.get("运柱", {}).get("天干", "")
        run_branch = cycle.get("运柱", {}).get("地支", "")
        run_stem_elem = STEM_ELEMENT_MAP.get(run_stem, "")
        run_branch_elem = BRANCH_ELEMENT_MAP.get(run_branch, "")

        # Check if cycle weakens DM (克我)
        control_elem = CONTROLS_DM_MAP.get(dm_elem, "")
        if control_elem and (
            run_stem_elem == control_elem or run_branch_elem == control_elem
        ):
            effects.append(
                {
                    "作用类型": "体质承压",
                    "互动类型": "克我",
                    "强度": "中等影响",
                    "解读": "此大运克我，体质承受压力，易有亚健康或疾病倾向，需强化养生。",
                }
            )

        # Check if cycle drains DM (我生泄耗)
        drain_elem = FOOD_GOD_MAP.get(dm_elem, "")
        if drain_elem and (
            run_stem_elem == drain_elem or run_branch_elem == drain_elem
        ):
            effects.append(
                {
                    "作用类型": "精力耗泄",
                    "互动类型": "我生泄耗",
                    "强度": "中等影响",
                    "解读": "此大运泄耗日主，精力损耗较大，易感疲劳，需补充营养与休息。",
                }
            )

        # Check if cycle supports DM (生我)
        support_elem = YIN_ELEMENT_MAP.get(dm_elem, "")
        if support_elem and (
            run_stem_elem == support_elem or run_branch_elem == support_elem
        ):
            effects.append(
                {
                    "作用类型": "体质恢复",
                    "互动类型": "生我",
                    "强度": "中等影响",
                    "解读": "此大运生我，体质恢复力增强，患病时易康复，是调理身体的好时期。",
                }
            )

        # Check if cycle strengthens DM (比劫助身)
        if run_stem_elem == dm_elem or run_branch_elem == dm_elem:
            effects.append(
                {
                    "作用类型": "体力增强",
                    "互动类型": "比劫助身",
                    "强度": "中等影响",
                    "解读": "此大运比劫助身，体力与免疫力上升，整体精力充足，适合健身与运动。",
                }
            )

        # Interaction-based effects (six clash, six harm on day pillar)
        zuo_yong = cycle.get("作用", {})
        if isinstance(zuo_yong, dict):
            pillar_data = zuo_yong.get("柱位动态", {}).get("日柱", {})
            for tier_list in pillar_data.values():
                if not isinstance(tier_list, list):
                    continue
                for item in tier_list:
                    interaction_type = item.get("类型", "")
                    strength = item.get("强度", "")

                    if interaction_type == "六冲" and strength in ACTIVE_STRENGTHS:
                        effects.append(
                            {
                                "作用类型": "躯体冲击",
                                "互动类型": "六冲",
                                "强度": strength,
                                "解读": "此大运冲击日柱，身宫受压，易有外伤、手术或体质骤降，需防范。",
                            }
                        )
                    elif interaction_type == "六害" and strength in ACTIVE_STRENGTHS:
                        effects.append(
                            {
                                "作用类型": "慢性积损",
                                "互动类型": "六害",
                                "强度": strength,
                                "解读": "此大运害日柱，慢性疾患易积累或复发，需定期检查与预防。",
                            }
                        )

        # Shen sha in cycle
        cycle_shen = cycle.get("神煞", {})
        if isinstance(cycle_shen, dict):
            all_stars = []
            for stars_list in cycle_shen.values():
                if isinstance(stars_list, list):
                    all_stars.extend(stars_list)

            if "天医" in all_stars or "天乙贵人" in all_stars:
                effects.append(
                    {
                        "作用类型": "健康护佑",
                        "互动类型": "天医/贵人入运",
                        "强度": "显著影响",
                        "解读": "此大运有天医或贵人入运，自愈力增强，患病时易遇良医扶持。",
                    }
                )

            if "血刃" in all_stars or "白虎" in all_stars:
                effects.append(
                    {
                        "作用类型": "外伤风险",
                        "互动类型": "白虎血刃入运",
                        "强度": "显著影响",
                        "解读": "此大运白虎/血刃入运，外伤与手术风险上升，需特别留意意外与医疗事件。",
                    }
                )

        # Void vitality in cycle
        run_zhu = cycle.get("运柱", {})
        branch_char = run_zhu.get("地支", "")
        xun_kong_str = run_zhu.get("旬空", "")
        if branch_char and branch_char in xun_kong_str:
            effects.append(
                {
                    "作用类型": "体力虚浮",
                    "互动类型": "旬空",
                    "强度": "中等衰减",
                    "解读": f"此大运地支{branch_char}落旬空，体力投入难以转化为实质恢复，以休养为主。",
                }
            )

        # Only include cycles with effects
        if effects:
            # Modulate all effects by constitutional strength
            modulated_effects = [
                _modulate_effect_by_constitution(eff, dm_score) for eff in effects
            ]

            # Determine temporal state
            if cycle.get("当运"):
                state = "当运"
            elif cycle.get("结束年份", 9999) < today_year:
                state = "已过"
            else:
                state = "未来"

            events.append(
                {
                    "大运": cycle.get("周期", ""),
                    "运势": state,
                    "健康作用": modulated_effects,
                }
            )

    return events


# ───────────────────────────────────────────────────────────────────────────────
# SYNTHESIS & SUMMARY
# ───────────────────────────────────────────────────────────────────────────────


def _build_health_summary(fired: dict) -> dict:
    """Build the health synthesis summary."""
    constitution = "先天体质中等"
    if "dm_strong" in fired:
        constitution = "先天体质强"
    elif "dm_weak" in fired:
        constitution = "先天体质偏弱"

    # Filter out constitution patterns from risks and protectors to avoid repetition in the summary
    risks = [
        fired[p]["格局名称"] for p in fired if p in RISK_IDS and not p.startswith("dm_")
    ]
    protectors = [
        fired[p]["格局名称"]
        for p in fired
        if p in PROTECTIVE_IDS and not p.startswith("dm_")
    ]

    # Combine interpretations dynamically
    constitution_label = constitution.replace("先天体质", "")  # "强" / "中等" / "偏弱"
    parts = [f"先天体质{constitution_label}"]

    risks_str = "、".join(risks[:3])
    protectors_str = "、".join(protectors[:2])

    if risks and protectors:
        parts.append(f"主要风险为{risks_str}，但{protectors_str}有所护佑")
    elif risks:
        parts.append(f"需留意{risks_str}等健康风险")
    elif protectors:
        parts.append(f"{protectors_str}提供健康护佑，整体有利")
    else:
        parts.append("命盘健康格局平稳，注重日常养生即可")

    return {
        "整体体质": constitution,
        "主要风险": risks,
        "有利因素": protectors,
        "综合解读": "，".join(parts) + "。",
    }


# ───────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ───────────────────────────────────────────────────────────────────────────────


def extract_health_insights(raw_data: dict) -> dict:
    """Main entry point for health insights extraction."""
    day_master = raw_data.get("day_master", {}).get("日主", {})
    wu_xing = raw_data.get("wu_xing", {}).get("五行力量", {})
    bazi = raw_data.get("bazi", {})
    da_yun = raw_data.get("da_yun", {})
    interactions = raw_data.get("interactions", {})
    xun_kong = raw_data.get("xun_kong", {})
    shen_sha_raw = raw_data.get("shen_sha", {}).get("神煞", {})

    dm_elem = day_master.get("五行", "")
    wu_xing_analysis = wu_xing.get("五行力量分析", {})
    branch_chars = _get_branch_chars(bazi)

    # Build candidates from all tiers
    candidates = []
    dm_score = day_master.get("强弱分数", 0)

    candidates += _pattern_dm_strength(day_master)  # Tier 1
    candidates += _pattern_element_imbalance(wu_xing_analysis)  # Tier 1
    candidates += _pattern_ten_god_health(wu_xing_analysis, dm_elem, dm_score)  # Tier 2
    candidates += _pattern_day_pillar_interactions(interactions, dm_score)  # Tier 3
    if p := _pattern_day_pillar_void(branch_chars, xun_kong):
        candidates.append(p)
    if p := _pattern_day_branch_weak_element(bazi, wu_xing_analysis):
        candidates.append(p)
    candidates += _pattern_shen_sha_health(shen_sha_raw, dm_score)  # Tier 4

    # Build patterns list
    patterns = [
        {"格局编号": pid, "格局名称": name, **r}
        for pid, name, r in candidates
        if r is not None
    ]
    fired = {p["格局编号"]: p for p in patterns}

    return {
        "健康综合评估": _build_health_summary(fired),
        "命盘健康格局": patterns,
        "大运健康动态": _get_cycle_health_events(
            da_yun, dm_elem, dm_score, branch_chars
        ),
        "无格局提示": (
            "命盘健康格局结构不显著，体质走向主要依赖大运与生活习惯调节。"
            if not patterns
            else None
        ),
    }


# ───────────────────────────────────────────────────────────────────────────────
# Execution Code
# ───────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    from datetime import datetime as dt
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
    from src.services.astronomer_data_aggregator import AstroDataAggregator
    from src.utils.logging import configure_logging, get_logger

    configure_logging()
    logger = get_logger(__name__)

    # python -m src.astronomer_calculations.interpretive_insights_health

    subjects = {
        "Desmond": (dt(1985, 11, 25, 17, 7, 0), 1.3253, 103.808053, 1),
    }

    for name, (birthday, lat, lon, gender) in subjects.items():
        logger.info("=" * 60)
        logger.info("Subject: %s  (%s)", name, birthday.strftime("%Y-%m-%d %H:%M"))

        tst_birthday, _ = get_true_solar_time(birthday, lat, lon)
        lunar_birthday = tst_birthday.getLunar()

        raw_data = AstroDataAggregator().collect_data(
            lunar_birthday=lunar_birthday,
            birth_datetime=birthday,
            latitude=lat,
            longitude=lon,
            gender=gender,
        )

        insights = extract_health_insights(raw_data)
        logger.info(json.dumps(insights, ensure_ascii=False, indent=2))
