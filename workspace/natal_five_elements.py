from typing import Dict, List, Tuple, Set, Any, Optional
from dataclasses import dataclass
from lunar_python.util import LunarUtil
from apps.backend.astronomer_logic.day_master_strength import BRANCH_HIDDEN_STEM_ROOTING

# ----------------------------------------------------------------------
# 1. Constants and mappings
# ----------------------------------------------------------------------

ELEMENTS = ["木", "火", "土", "金", "水"]
STEM_ELEMENT   = LunarUtil.WU_XING_GAN        # {stem → element}
BRANCH_ELEMENT = LunarUtil.WU_XING_ZHI        # {branch → element}
HIDDEN_STEMS   = BRANCH_HIDDEN_STEM_ROOTING   # {branch → [(stem, weight)]}

SEASONAL_STATES = {
    # Spring
    ("春", "木"): 1.5, ("春", "火"): 1.3, ("春", "水"): 1.0, ("春", "土"): 0.7, ("春", "金"): 0.4,
    # Summer
    ("夏", "火"): 1.5, ("夏", "土"): 1.3, ("夏", "木"): 1.0, ("夏", "水"): 0.7, ("夏", "金"): 0.4,
    # Autumn
    ("秋", "金"): 1.5, ("秋", "水"): 1.3, ("秋", "土"): 1.0, ("秋", "木"): 0.7, ("秋", "火"): 0.4,
    # Winter
    ("冬", "水"): 1.5, ("冬", "木"): 1.3, ("冬", "金"): 1.0, ("冬", "火"): 0.7, ("冬", "土"): 0.4,
}

MONTH_SEASON = {
    "寅": "春", "卯": "春", "辰": "春",
    "巳": "夏", "午": "夏", "未": "夏",
    "申": "秋", "酉": "秋", "戌": "秋",
    "亥": "冬", "子": "冬", "丑": "冬",
}

# Interaction strength tier → numeric weight for scaling reductions and bonuses
STRENGTH_WEIGHTS: Dict[str, float] = {
    "强势主流": 1.0,
    "显著影响": 0.75,
    "中等衰减": 0.50,
    "大幅衰减": 0.25,
    "消融吸收": 0.0,   # fully neutralised — interaction has no effect
}

# Combo bonus base scores (before seasonal multiplier and strength scaling)
COMBO_SCORES: Dict[str, float] = {
    "三会": 1.0,
    "三合": 0.8,
    "半合": 0.4,
    "六合": 0.3,
    "干支透合": 0.3,
    "拱合": 0.2,
    "拱会": 0.2,
    "暗合": 0.1,
}

# Clash base reduction factors (applied to branch + hidden stems)
CLASH_REDUCTION: Dict[str, Any] = {
    "六冲": (0.3, 0.7),   # (weak roots, strong roots factor)
    "六害": 0.6,
    "六破": 0.8,
    "三刑": 0.7,
    "自刑": 0.9,
    "天克地冲": (0.3, 0.6),
}

STEM_CLASH_REDUCTION = 0.5   # base factor for 天干克 / 天干冲
VOID_MULTIPLIER      = 0.5   # branch + stem halved when in 空亡

STEM_ROOT_MULTIPLIER: Dict[str, float] = {
    "深根": 1.4,   # rooted via chief qi (本气)
    "中根": 1.2,   # rooted via middle qi (中气)
    "浅根": 1.0,   # rooted via residual qi (余气) — neutral
    "无根": 0.8,   # floating stem penalised
}

_PILLAR_KEYS = ["年柱", "月柱", "日柱", "时柱"]
_ROOT_RANK: Dict[str, int] = {"深根": 3, "中根": 2, "浅根": 1, "无根": 0}
_HIDDEN_DEPTH_WEIGHT: Dict[str, float] = {"本气": 0.6, "中气": 0.3, "余气": 0.1}

# ----------------------------------------------------------------------
# 2. Data structures
# ----------------------------------------------------------------------

@dataclass
class Pillar:
    stem: str
    branch: str

@dataclass
class Interaction:
    type: str
    form: str
    pillars: List[str]
    element: str
    interaction_strength: float                  # 0.0–1.0 from STRENGTH_WEIGHTS
    root_strength: Optional[Tuple[str, str]] = None  # (weaker_pillar, stronger_pillar) for 六冲
    depth_weight: float = 1.0                    # 干支透合 only: hidden stem tier weight

@dataclass
class SeasonalFactors:
    season: str
    multipliers: Dict[str, float]

# ----------------------------------------------------------------------
# 3. Helper functions
# ----------------------------------------------------------------------

def get_seasonal_factors(month_branch: str) -> SeasonalFactors:
    season = MONTH_SEASON[month_branch]
    mult = {elem: SEASONAL_STATES[(season, elem)] for elem in ELEMENTS}
    return SeasonalFactors(season=season, multipliers=mult)

def _effective_reduction(base_factor: float, interaction_strength: float) -> float:
    """Scale a clash reduction by interaction strength.

    At interaction_strength=1.0 the base factor is applied unchanged.
    At interaction_strength=0.0 no reduction is applied (returns 1.0).
    """
    return 1.0 - (1.0 - base_factor) * interaction_strength

# ----------------------------------------------------------------------
# 4. Core scoring engine
# ----------------------------------------------------------------------

class FiveElementsAnalyzer:
    """Computes weighted five-element distribution for a natal BaZi chart.

    Accepts the merged si_zhu dict from the orchestrator and the raw
    natal_interactions_data, converting both into internal types before
    running the 5-step scoring pipeline.
    """

    def __init__(
        self,
        si_zhu: Dict[str, Any],
        natal_interactions_data: Dict[str, Any],
    ):
        self.pillars     = self._build_pillars(si_zhu)
        self.interactions = self._convert_interactions(natal_interactions_data)
        self.sf          = get_seasonal_factors(si_zhu["月柱"]["地支"])
        self.void_map    = {key: si_zhu[key].get("空亡", "无") != "无" for key in _PILLAR_KEYS}
        self.root_map    = {key: si_zhu[key].get("根基强度", "无根") for key in _PILLAR_KEYS}

        # Step 1 accumulators
        self.stem_scores:   Dict[str, float] = {e: 0.0 for e in ELEMENTS}
        self.branch_scores: Dict[str, float] = {e: 0.0 for e in ELEMENTS}
        self.hidden_scores: Dict[str, float] = {e: 0.0 for e in ELEMENTS}
        # Step 4 accumulator
        self.combo_bonus: Dict[str, float] = {e: 0.0 for e in ELEMENTS}

        # Per-pillar adjustment factors (Steps 2 & 3)
        self.branch_reduction: Dict[str, float] = {k: 1.0 for k in self.pillars}
        self.stem_reduction:   Dict[str, float] = {k: 1.0 for k in self.pillars}

        # Stem element overrides from 天干合
        self.stem_transform:  Dict[str, str]  = {}   # pillar → new element
        self.stem_cancelled:  Set[str]         = set() # pillars whose stem contributes 0

    # ------------------------------------------------------------------
    # Private conversion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_pillars(si_zhu: Dict[str, Any]) -> Dict[str, Pillar]:
        return {
            key: Pillar(
                stem=si_zhu[key]["天干"],
                branch=si_zhu[key]["地支"],
            )
            for key in _PILLAR_KEYS
        }

    @staticmethod
    def _convert_interactions(natal_interactions_data: Dict[str, Any]) -> List[Interaction]:
        result: List[Interaction] = []
        items = natal_interactions_data.get("作用", {}).get("柱位动态", [])

        for item in items:
            type_    = item.get("类型", "")
            form     = item.get("形态", "")
            pillars  = list(item.get("组合明细", {}).keys())
            element  = item.get("元素", "")
            interaction_strength = STRENGTH_WEIGHTS.get(item.get("强度", "强势主流"), 1.0)
            if interaction_strength == 0.0:
                continue

            depth_weight = 1.0
            if type_ == "干支透合":
                tier = item.get("藏干详情", {}).get("藏干层", "本气")
                depth_weight = _HIDDEN_DEPTH_WEIGHT.get(tier, 1.0)

            root_strength: Optional[Tuple[str, str]] = None
            if type_ in ("六冲", "天克地冲") and len(pillars) == 2:
                根基 = item.get("根基", {})
                if 根基:
                    ranks = {p: _ROOT_RANK.get(根基.get(p, "无根"), 0) for p in pillars}
                    if ranks[pillars[0]] != ranks[pillars[1]]:
                        weaker   = min(pillars, key=lambda p: ranks[p])
                        stronger = max(pillars, key=lambda p: ranks[p])
                        root_strength = (weaker, stronger)

            result.append(Interaction(
                type=type_, form=form, pillars=pillars,
                element=element, interaction_strength=interaction_strength, root_strength=root_strength,
                depth_weight=depth_weight,
            ))

        return result

    # ------------------------------------------------------------------
    # Scoring pipeline
    # ------------------------------------------------------------------

    def apply_interactions(self) -> None:
        """Steps 2–4: collect reductions and combo bonuses from interactions."""
        for inter in self.interactions:
            self._process_interaction(inter)
        for inter in self.interactions:
            self._add_combo_bonus(inter)

    def _process_interaction(self, inter: Interaction) -> None:
        """Apply branch/stem reductions (Steps 2–3) and stem transforms."""
        type = inter.type
        form = inter.form
        interaction_strength = inter.interaction_strength

        # Combinations — no branch reduction; bonuses handled in _add_combo_bonus
        if type in ("三会", "三合", "半合", "六合", "拱合", "拱会", "暗合"):
            return

        # ── Branch clashes (Step 2) ────────────────────────────────────
        if type == "六冲":
            weaker, _ = inter.root_strength if inter.root_strength else (inter.pillars[0], None)
            for p in inter.pillars:
                base = CLASH_REDUCTION["六冲"][0] if p == weaker else CLASH_REDUCTION["六冲"][1]
                eff = _effective_reduction(base, interaction_strength)
                self.branch_reduction[p] = min(self.branch_reduction[p], eff)
            return

        if type == "六害":
            eff = _effective_reduction(CLASH_REDUCTION["六害"], interaction_strength)
            for p in inter.pillars:
                self.branch_reduction[p] = min(self.branch_reduction[p], eff)
            return

        if type == "六破":
            eff = _effective_reduction(CLASH_REDUCTION["六破"], interaction_strength)
            for p in inter.pillars:
                self.branch_reduction[p] = min(self.branch_reduction[p], eff)
            return

        if type in ("无恩之刑", "恃势之刑", "无礼之刑"):
            eff = _effective_reduction(CLASH_REDUCTION["三刑"], interaction_strength)
            for p in inter.pillars:
                self.branch_reduction[p] = min(self.branch_reduction[p], eff)
            return

        if type == "自刑":
            eff = _effective_reduction(CLASH_REDUCTION["自刑"], interaction_strength)
            for p in inter.pillars:
                self.branch_reduction[p] = min(self.branch_reduction[p], eff)
            return

        if type == "天克地冲":
            weaker, _ = inter.root_strength if inter.root_strength else (inter.pillars[0], None)
            for p in inter.pillars:
                base = CLASH_REDUCTION["天克地冲"][0] if p == weaker else CLASH_REDUCTION["天克地冲"][1]
                eff = _effective_reduction(base, interaction_strength)
                self.branch_reduction[p] = min(self.branch_reduction[p], eff)
            return

        # ── Stem interactions (Step 3) ─────────────────────────────────
        if type == "天干合":
            if form in ("合化", "化气格") and inter.element:
                # Both stems transform to the combined element
                for p in inter.pillars:
                    self.stem_transform[p] = inter.element
            elif form == "合绊":
                # Both stems neutralised — contribute 0
                for p in inter.pillars:
                    self.stem_cancelled.add(p)
            # 假化, 遥合: stems retain original element — no action
            return

        if type in ("天干克", "天干冲"):
            eff = _effective_reduction(STEM_CLASH_REDUCTION, interaction_strength)
            for p in inter.pillars:
                self.stem_reduction[p] = min(self.stem_reduction[p], eff)
            return

        # 干支透合: bonus only, handled in _add_combo_bonus
        # 比和, 伏吟, 残会: no reduction

    def _add_combo_bonus(self, inter: Interaction) -> None:
        """Step 4: add generated-element bonus from combinations."""
        type = inter.type

        if type in ("三会", "三合", "半合", "六合", "拱合", "拱会", "暗合"):
            if inter.element in ELEMENTS:
                base  = COMBO_SCORES.get(type, 0.0)
                bonus = base * inter.interaction_strength * self.sf.multipliers[inter.element]
                self.combo_bonus[inter.element] += bonus

        elif type == "干支透合" and inter.element in ELEMENTS:
            base  = COMBO_SCORES["干支透合"]
            bonus = base * inter.depth_weight * inter.interaction_strength * self.sf.multipliers[inter.element]
            self.combo_bonus[inter.element] += bonus

    def compute_baseline_scores(self) -> None:
        """Step 1: baseline stem + branch + hidden scores with seasonal and void factors."""
        for key, pillar in self.pillars.items():
            void_mult  = VOID_MULTIPLIER if self.void_map[key] else 1.0
            branch_red = self.branch_reduction[key]
            stem_red   = self.stem_reduction[key]

            # Stem (Step 3 reduction already computed)
            if key not in self.stem_cancelled:
                stem_elem = self.stem_transform.get(key, STEM_ELEMENT.get(pillar.stem))
                if stem_elem:
                    root_mult = STEM_ROOT_MULTIPLIER.get(self.root_map[key], 1.0)
                    self.stem_scores[stem_elem] += (
                        self.sf.multipliers[stem_elem] * void_mult * stem_red * root_mult
                    )

            # Visible branch (Step 2 reduction already computed)
            branch_elem = BRANCH_ELEMENT.get(pillar.branch)
            if branch_elem:
                self.branch_scores[branch_elem] += (
                    self.sf.multipliers[branch_elem] * void_mult * branch_red
                )

            # Hidden stems share the branch's reduction
            for hidden_stem, base_weight in HIDDEN_STEMS.get(pillar.branch, []):
                h_elem = STEM_ELEMENT.get(hidden_stem)
                if h_elem:
                    self.hidden_scores[h_elem] += (
                        base_weight * self.sf.multipliers[h_elem] * void_mult * branch_red
                    )

    def get_totals(self) -> Dict[str, float]:
        """Step 5: sum all accumulators."""
        return {
            e: self.stem_scores[e] + self.branch_scores[e]
               + self.hidden_scores[e] + self.combo_bonus[e]
            for e in ELEMENTS
        }

    @staticmethod
    def get_five_elements_tier(percentage: float) -> Dict[str, str]:
        """
        Categorize Five Elements percentage into a tier with contextual description.

        Tiers (ordered by energy intensity):
        - 缺失 (Absent): 0%
        - 极弱 (Critical Deficit): 0.1% - 10%
        - 偏弱 (Subdued): 10.1% - 20%
        - 中和 (Balanced): 20.1% - 35%
        - 偏旺 (Robust): 35.1% - 50%
        - 极旺 (Overwhelming): 50.1% - 70%
        - 极亢 (Absolute Monopoly): > 70%

        Args:
            percentage: Float value representing the element's percentage of total power

        Returns:
            dict: Tier information with name, range, state description, and core advice
        """
        if percentage == 0:
            return {
                "名称": "缺失",
                "范围": "0%",
                "状态描述": "绝对真空，物质缺失。该谱线能量在系统演化中完全缺失，缺乏相应的物理机制支持。",
                "核心建议": '外部引力，人工介入。本系统无法自发产生此项能量。需通过外部环境的"引力摄动"或特定的后天参数注入，方能补足该维度的缺失。',
            }
        elif percentage <= 10:
            return {
                "名称": "极弱",
                "范围": "0.01% - 10%",
                "状态描述": "热寂边缘，能量脉冲微弱。能量丰度极低，处于核聚变熄灭的边缘，极易被主星风暴吞噬。",
                "核心建议": '精密维护，防止坍缩。此为系统中最脆弱的反馈回路。必须严格限制外界对该能量的消耗（克泄），通过低熵环境进行定向"光泵浦"增益，维系其微弱的运行。',
            }
        elif percentage <= 20:
            return {
                "名称": "偏弱",
                "范围": "10.01% - 20%",
                "状态描述": "轨道不稳，能量辐射受限。虽有物质基础，但质量不足以形成稳恒的自持反应，处于系统的边缘地带。",
                "核心建议": "轨道提升，质能累积。不建议承担高强度的系统负荷。需通过同频率的能量共振（生扶）来增加其质量密度，逐步将其推向核心环绕轨道。",
            }
        elif percentage <= 35:
            return {
                "名称": "中和",
                "范围": "20.01% - 35%",
                "状态描述": "稳恒态演化，动态平衡。系统熵增率处于理想区间，能量转换效率极高且具备极强的自修复能力。",
                "核心建议": "参数锁死，惯性运行。这是系统演化的最佳黄金期。避免大幅度的参数扰动，维持现有的动态平衡，确保系统的长周期稳定运行。",
            }
        elif percentage <= 50:
            return {
                "名称": "偏旺",
                "范围": "35.01% - 50%",
                "状态描述": "活跃恒星，热核反应激增。该项能量已成为系统的主要引力源，释放出强烈的能量辐射，并开始干扰其他弱能级轨道。",
                "核心建议": "能量泄压，负载均衡。系统输出已过载。宜通过高效的能量转换界面（泄）或逆向热力学补偿（耗）来分散其压力，防止核心因能量过剩导致热失控。",
            }
        elif percentage <= 70:
            return {
                "名称": "极旺",
                "范围": "50.01% - 70%",
                "状态描述": "引力坍缩，黑洞效应初现。能量丰度已达到临界点，形成极强的引力陷阱，系统正被该单一变量强行锁定，面临失衡风险。",
                "核心建议": "紧急降维，广域排干。严禁任何形式的能量注资。必须建立大容量的泄流管道，将过剩的能量强行传导至外部耗散层，以缓解核心区域巨大的压强。",
            }
        else:
            return {
                "名称": "极亢",
                "范围": "> 70%",
                "状态描述": "奇点降临，时空曲率极限。该能量已彻底统治整个物理场。系统规律已被重写，传统力学平衡逻辑彻底失效。",
                "核心建议": '顺应奇点，整体同步。当能量达到绝对垄断时，任何对抗尝试都会导致系统瞬间瓦解。最优策略是顺从该能量的流动矢向，让系统整体进入"单极演化"模式。',
            }

    def analyze(self) -> Dict[str, Any]:
        """Run the full 5-step pipeline and return the element distribution dict."""
        self.apply_interactions()
        self.compute_baseline_scores()
        totals = self.get_totals()
        total_sum = sum(totals.values())
        percentages = (
            {e: round(v / total_sum * 100, 2) for e, v in totals.items()}
            if total_sum
            else {e: 0.0 for e in ELEMENTS}
        )

        return {
            "五行": {
                element: {
                    "百分比": pct,
                    "能级": FiveElementsAnalyzer.get_five_elements_tier(pct),
                }
                for element, pct in percentages.items()
            }
        }


# ============================================================================
# EXECUTION
# python -m apps.backend.astronomer_logic.natal_five_elements
# ============================================================================

if __name__ == "__main__":
    import json
    from datetime import datetime as dt
    from apps.backend.astronomer_logic.true_solar_time import get_true_solar_time
    from apps.backend.astronomer_logic.bazi_pillars import get_bazi_pillars
    from apps.backend.astronomer_logic.void_xun_kong import get_void_xun_kong
    from apps.backend.astronomer_logic.ten_gods import get_ten_gods
    from apps.backend.astronomer_logic.natal_interactions import get_natal_interactions
    from src.utils.logging import configure_logging, get_logger

    configure_logging()
    logger = get_logger(__name__)

    # ── Subjects ──────────────────────────────────────────────────────────────
    subjects = {
        "Desmond": (dt(1985, 11, 25, 17, 7, 0), 1.3253, 103.808053, 1),
        # "Corinne": (dt(1987, 6, 3, 12, 6, 0), 1.4759, 103.808053, 0),
        # "Lara":    (dt(2025,  7, 31,  9, 10, 0), 1.3253,  103.808053, 0),
    }

    for name, (birthday, lat, lon, gender) in subjects.items():
        logger.info("=" * 60)
        logger.info("Subject: %s  (%s)", name, birthday.strftime("%Y-%m-%d %H:%M"))

        tst_birthday = get_true_solar_time(birthday, lat, lon)
        lunar_birthday = tst_birthday.getLunar()

        bazi = lunar_birthday.getEightChar()
        pillars = get_bazi_pillars(bazi)
        void = get_void_xun_kong(bazi)
        ten_gods = get_ten_gods(bazi)

        for k in ["年柱", "月柱", "日柱", "时柱"]:
            pillars[k]["藏干十神"] = ten_gods[k]["藏干十神"]
            pillars[k]["空亡"] = void.get(k, "无")

        interactions = get_natal_interactions(pillars, void)

        result = FiveElementsAnalyzer(pillars, interactions).analyze()
        logger.info(json.dumps(result, ensure_ascii=False, indent=2))
