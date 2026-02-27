"""
Wu Xing (五行) - Five Elements Calculation Module

This module extracts and analyzes the Five Elements (Wu Xing) composition from a BaZi chart,
as well as the Hidden Stems (藏干) contained within each Earthly Branch.

Professional Scoring System:
This implementation uses a weighted scoring system (targeting 10.0 total points) based on
professional Bazi (Zi Ping) methodology:

1. Heavenly Stems: 1.0 point each (4 stems = 4.0 total)
2. Regular Branches: [Main (本气): 0.7, Secondary (中气): 0.2, Tertiary (余气): 0.1] per branch
3. Month Branch: [Main (本气): 2.0, Secondary (中气): 0.6, Tertiary (余气): 0.4] (acts as "Commander")

Total Scale: ~10.0 points
This preserves the relative weight of each element for LLM interpretation.

Key Functions:
    get_wu_xing(lunar_birthday): Extracts Wu Xing composition, Hidden Stems, and professional scores.

    Returns:
        dict: Structured JSON with Five Elements data organized by pillar:
        {
            "年柱": {
                "五行": {"天干五行": "...", "地支五行": "..."},
                "藏干": [...]
            },
            "月柱": {...},
            "日柱": {...},
            "时柱": {...},
            "五行力量": {
                "木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0  # Raw weighted scores
            }
        }

The Five Elements:
- 木 (Wood): Growth, expansion, flexibility
- 火 (Fire): Passion, activity, transformation
- 土 (Earth): Stability, nurture, balance
- 金 (Metal): Strength, discipline, precision
- 水 (Water): Flow, wisdom, flexibility

This data is LLM-ready and professional practitioners can immediately recognize the scoring logic.
"""

from lunar_python import Lunar
from datetime import datetime
from collections import Counter
from src.astronomer_calculations.solar_lunar_time import get_true_solar_time


def get_wu_xing(lunar_birthday: Lunar) -> dict:
    """
    Extract Five Elements (Wu Xing) from lunar birthday and return as JSON format (Chinese keys).

    Args:
        lunar_birthday (Lunar): Lunar calendar object

    Returns:
        dict: Five Elements composition by pillar with 天干五行 (Stem Element) and 地支五行 (Branch Element)
    """
    # Get the EightChar object
    bazi = lunar_birthday.getEightChar()

    # Extract Five Elements (Wu Xing) for each pillar
    # Each pillar's Wu Xing is a string like "木土" (stem element + branch element)
    year_wu_xing = bazi.getYearWuXing()
    month_wu_xing = bazi.getMonthWuXing()
    day_wu_xing = bazi.getDayWuXing()
    hour_wu_xing = bazi.getTimeWuXing()

    # Extract Hidden Stems (Hidden Gan) for each pillar
    year_hide_gan = bazi.getYearHideGan()
    month_hide_gan = bazi.getMonthHideGan()
    day_hide_gan = bazi.getDayHideGan()
    hour_hide_gan = bazi.getTimeHideGan()

    # Extract actual stems and branches for each pillar
    year_pillar_str = bazi.getYear()  # e.g., "甲子"
    month_pillar_str = bazi.getMonth()  # e.g., "丙寅"
    day_pillar_str = bazi.getDay()  # e.g., "戊辰"
    hour_pillar_str = bazi.getTime()  # e.g., "庚申"

    # Parse stems and branches
    year_stem = year_pillar_str[0] if year_pillar_str else None
    year_branch = year_pillar_str[1] if len(year_pillar_str) > 1 else None
    month_stem = month_pillar_str[0] if month_pillar_str else None
    month_branch = month_pillar_str[1] if len(month_pillar_str) > 1 else None
    day_stem = day_pillar_str[0] if day_pillar_str else None
    day_branch = day_pillar_str[1] if len(day_pillar_str) > 1 else None
    hour_stem = hour_pillar_str[0] if hour_pillar_str else None
    hour_branch = hour_pillar_str[1] if len(hour_pillar_str) > 1 else None

    # Calculate Wu Xing strength using professional weighted scoring
    wu_xing_strength = calculate_wu_xing_strength_professional(
        year_wu_xing=year_wu_xing,
        month_wu_xing=month_wu_xing,
        day_wu_xing=day_wu_xing,
        hour_wu_xing=hour_wu_xing,
        year_hide_gan=year_hide_gan,
        month_hide_gan=month_hide_gan,
        day_hide_gan=day_hide_gan,
        hour_hide_gan=hour_hide_gan,
        year_stem=year_stem,
        month_stem=month_stem,
        day_stem=day_stem,
        hour_stem=hour_stem,
        year_branch=year_branch,
        month_branch=month_branch,
        day_branch=day_branch,
        hour_branch=hour_branch,
    )

    return {
        "年柱": {
            "五行": parse_wu_xing(year_wu_xing),
            "藏干": year_hide_gan,
        },
        "月柱": {
            "五行": parse_wu_xing(month_wu_xing),
            "藏干": month_hide_gan,
        },
        "日柱": {
            "五行": parse_wu_xing(day_wu_xing),
            "藏干": day_hide_gan,
        },
        "时柱": {
            "五行": parse_wu_xing(hour_wu_xing),
            "藏干": hour_hide_gan,
        },
        "五行力量": wu_xing_strength,
    }


# Parse each Wu Xing string into stem and branch elements
def parse_wu_xing(wu_xing_str: str) -> dict:
    """Split Wu Xing string (e.g., '木土') into stem and branch elements"""
    if len(wu_xing_str) >= 2:
        return {"天干五行": wu_xing_str[0], "地支五行": wu_xing_str[1]}
    return {"天干五行": "", "地支五行": ""}


from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class Element(Enum):
    WOOD = "木"
    FIRE = "火"
    EARTH = "土"
    METAL = "金"
    WATER = "水"


class Stem(Enum):
    JIA = "甲"  # Yang Wood
    YI = "乙"  # Yin Wood
    BING = "丙"  # Yang Fire
    DING = "丁"  # Yin Fire
    WU = "戊"  # Yang Earth
    JI = "己"  # Yin Earth
    GENG = "庚"  # Yang Metal
    XIN = "辛"  # Yin Metal
    REN = "壬"  # Yang Water
    GUI = "癸"  # Yin Water


class Branch(Enum):
    ZI = "子"  # Rat - Water
    CHOU = "丑"  # Ox - Earth
    YIN = "寅"  # Tiger - Wood
    MAO = "卯"  # Rabbit - Wood
    CHEN = "辰"  # Dragon - Earth
    SI = "巳"  # Snake - Fire
    WU = "午"  # Horse - Fire
    WEI = "未"  # Goat - Earth
    SHEN = "申"  # Monkey - Metal
    YOU = "酉"  # Rooster - Metal
    XU = "戌"  # Dog - Earth
    HAI = "亥"  # Pig - Water


@dataclass
class HiddenStem:
    stem: Stem
    depth: float  # Primary: 0.7, Secondary: 0.25, Residual: 0.05


@dataclass
class BranchInfo:
    branch: Branch
    primary_stem: Stem
    secondary_stem: Optional[Stem] = None
    residual_stem: Optional[Stem] = None
    # Depth percentages
    primary_depth: float = 0.7
    secondary_depth: float = 0.25
    residual_depth: float = 0.05


@dataclass
class Pillar:
    stem: Optional[Stem]
    branch: Optional[Branch]
    stem_element: Optional[Element]
    branch_element: Optional[Element]
    hidden_stems: List[HiddenStem]
    position: str  # year, month, day, hour
    position_weight: float  # month: 0.5, day: 0.25, year/hour: 0.125


@dataclass
class SeasonalFactors:
    season: str  # spring, summer, autumn, winter
    wood_state: str  # 旺,相,休,囚,死
    fire_state: str
    earth_state: str
    metal_state: str
    water_state: str

    # Multipliers based on state - REFINED FOR IMPERIAL METHOD
    @staticmethod
    def get_multiplier(state: str) -> float:
        multipliers = {
            "旺": 1.0,  # Prosperous - full power
            "相": 0.8,  # Prime - 80% power
            "休": 0.6,  # Resting - 60% power
            "囚": 0.4,  # Imprisoned - 40% power
            "死": 0.2,  # Dead - 20% power
        }
        return multipliers.get(state, 0.4)


# Branch database with hidden stems and depths
BRANCH_DATABASE = {
    Branch.ZI: BranchInfo(Branch.ZI, Stem.GUI, None, None, 1.0, 0, 0),
    Branch.CHOU: BranchInfo(Branch.CHOU, Stem.JI, Stem.GUI, Stem.XIN, 0.6, 0.3, 0.1),
    Branch.YIN: BranchInfo(Branch.YIN, Stem.JIA, Stem.BING, Stem.WU, 0.7, 0.2, 0.1),
    Branch.MAO: BranchInfo(Branch.MAO, Stem.YI, None, None, 1.0, 0, 0),
    Branch.CHEN: BranchInfo(Branch.CHEN, Stem.WU, Stem.YI, Stem.GUI, 0.6, 0.3, 0.1),
    Branch.SI: BranchInfo(Branch.SI, Stem.BING, Stem.WU, Stem.GENG, 0.7, 0.2, 0.1),
    Branch.WU: BranchInfo(Branch.WU, Stem.DING, Stem.JI, None, 0.7, 0.3, 0),
    Branch.WEI: BranchInfo(Branch.WEI, Stem.JI, Stem.DING, Stem.YI, 0.6, 0.3, 0.1),
    Branch.SHEN: BranchInfo(Branch.SHEN, Stem.GENG, Stem.REN, Stem.WU, 0.7, 0.2, 0.1),
    Branch.YOU: BranchInfo(Branch.YOU, Stem.XIN, None, None, 1.0, 0, 0),
    Branch.XU: BranchInfo(Branch.XU, Stem.WU, Stem.XIN, Stem.DING, 0.6, 0.3, 0.1),
    Branch.HAI: BranchInfo(Branch.HAI, Stem.REN, Stem.JIA, None, 0.7, 0.3, 0),
}

# Element mapping for stems
STEM_ELEMENT_MAP = {
    Stem.JIA: Element.WOOD,
    Stem.YI: Element.WOOD,
    Stem.BING: Element.FIRE,
    Stem.DING: Element.FIRE,
    Stem.WU: Element.EARTH,
    Stem.JI: Element.EARTH,
    Stem.GENG: Element.METAL,
    Stem.XIN: Element.METAL,
    Stem.REN: Element.WATER,
    Stem.GUI: Element.WATER,
}

# Element mapping for branches (base element)
BRANCH_ELEMENT_MAP = {
    Branch.ZI: Element.WATER,
    Branch.HAI: Element.WATER,
    Branch.YIN: Element.WOOD,
    Branch.MAO: Element.WOOD,
    Branch.SI: Element.FIRE,
    Branch.WU: Element.FIRE,
    Branch.SHEN: Element.METAL,
    Branch.YOU: Element.METAL,
    Branch.CHEN: Element.EARTH,
    Branch.XU: Element.EARTH,
    Branch.CHOU: Element.EARTH,
    Branch.WEI: Element.EARTH,
}

# Map string to Stem enum
STRING_TO_STEM = {
    "甲": Stem.JIA,
    "乙": Stem.YI,
    "丙": Stem.BING,
    "丁": Stem.DING,
    "戊": Stem.WU,
    "己": Stem.JI,
    "庚": Stem.GENG,
    "辛": Stem.XIN,
    "壬": Stem.REN,
    "癸": Stem.GUI,
}

# Map string to Branch enum
STRING_TO_BRANCH = {
    "子": Branch.ZI,
    "丑": Branch.CHOU,
    "寅": Branch.YIN,
    "卯": Branch.MAO,
    "辰": Branch.CHEN,
    "巳": Branch.SI,
    "午": Branch.WU,
    "未": Branch.WEI,
    "申": Branch.SHEN,
    "酉": Branch.YOU,
    "戌": Branch.XU,
    "亥": Branch.HAI,
}

# Map element string to Element enum
STRING_TO_ELEMENT = {
    "木": Element.WOOD,
    "火": Element.FIRE,
    "土": Element.EARTH,
    "金": Element.METAL,
    "水": Element.WATER,
}


# Seasonal state determination
def get_seasonal_factors(month_branch: Branch) -> SeasonalFactors:
    """Determine seasonal states based on month branch"""

    # Spring months: Yin, Mao, Chen
    if month_branch in [Branch.YIN, Branch.MAO, Branch.CHEN]:
        return SeasonalFactors(
            season="spring",
            wood_state="旺",
            fire_state="相",
            earth_state="死",
            metal_state="囚",
            water_state="休",
        )
    # Summer months: Si, Wu, Wei
    elif month_branch in [Branch.SI, Branch.WU, Branch.WEI]:
        return SeasonalFactors(
            season="summer",
            wood_state="休",
            fire_state="旺",
            earth_state="相",
            metal_state="死",
            water_state="囚",
        )
    # Autumn months: Shen, You, Xu
    elif month_branch in [Branch.SHEN, Branch.YOU, Branch.XU]:
        return SeasonalFactors(
            season="autumn",
            wood_state="死",
            fire_state="囚",
            earth_state="休",
            metal_state="旺",
            water_state="相",
        )
    # Winter months: Hai, Zi, Chou
    else:  # Hai, Zi, Chou
        return SeasonalFactors(
            season="winter",
            wood_state="相",
            fire_state="死",
            earth_state="囚",
            metal_state="休",
            water_state="旺",
        )


def get_depth_for_stem(branch: Branch, stem_value: str) -> float:
    """
    Get the correct depth percentage for a hidden stem based on its position in the branch
    """
    info = BRANCH_DATABASE[branch]

    if info.primary_stem and info.primary_stem.value == stem_value:
        return info.primary_depth
    elif info.secondary_stem and info.secondary_stem.value == stem_value:
        return info.secondary_depth
    elif info.residual_stem and info.residual_stem.value == stem_value:
        return info.residual_depth

    return 0.33  # fallback


class MingQiDynamicsCalculator:
    def __init__(self):

        # Position weights to sum to 0.90. Heavenly Stems will be 0.10. Together, they sum to 1.0 for a complete chart analysis.
        self.position_weights = {
            "year": 0.14,  # Year branch: 13%
            "month": 0.40,  # Month branch: 40%
            "day": 0.22,  # Day branch: 23%
            "hour": 0.14,  # Hour branch: 13%
        }

        # Heavenly Stem Weight (Ming Dynasty)
        # 4 stems × 0.025 = 0.1 (10% total)
        self.stem_weight = 0.025

        # Combination triplets
        self.water_triplet = [Branch.SHEN, Branch.ZI, Branch.CHEN]
        self.wood_triplet = [Branch.HAI, Branch.MAO, Branch.WEI]
        self.fire_triplet = [Branch.YIN, Branch.WU, Branch.XU]
        self.metal_triplet = [Branch.SI, Branch.YOU, Branch.CHOU]

        # IMPERIAL CORRECTION 3: Half-combinations are subtle, not dominant
        self.half_combinations = {
            # Water half combos - reduced from 0.5 to 0.15
            (Branch.SHEN, Branch.ZI): (Element.WATER, 0.15),
            (Branch.ZI, Branch.CHEN): (Element.WATER, 0.15),
            (Branch.SHEN, Branch.CHEN): (Element.WATER, 0.15),
            # Wood half combos
            (Branch.HAI, Branch.MAO): (Element.WOOD, 0.15),
            (Branch.MAO, Branch.WEI): (Element.WOOD, 0.15),
            (Branch.HAI, Branch.WEI): (Element.WOOD, 0.15),
            # Fire half combos
            (Branch.YIN, Branch.WU): (Element.FIRE, 0.15),
            (Branch.WU, Branch.XU): (Element.FIRE, 0.15),
            (Branch.YIN, Branch.XU): (Element.FIRE, 0.15),
            # Metal half combos
            (Branch.SI, Branch.YOU): (Element.METAL, 0.15),
            (Branch.YOU, Branch.CHOU): (Element.METAL, 0.15),
            (Branch.SI, Branch.CHOU): (Element.METAL, 0.15),
        }

        # Full triplet bonus (when all three present)
        self.full_triplet_bonus = 0.25  # Additional 25% when all three present

        # Clash pairs
        self.clash_pairs = [
            (Branch.ZI, Branch.WU),
            (Branch.CHOU, Branch.WEI),
            (Branch.YIN, Branch.SHEN),
            (Branch.MAO, Branch.YOU),
            (Branch.CHEN, Branch.XU),
            (Branch.SI, Branch.HAI),
        ]

        # IMPERIAL CORRECTION 4: Temperature values moderated
        self.branch_temperature = {
            Branch.ZI: -6,
            Branch.HAI: -5,
            Branch.CHOU: -3,  # Cold but not arctic
            Branch.YIN: 0,
            Branch.MAO: 0,
            Branch.CHEN: 0,  # Neutral
            Branch.SI: 6,
            Branch.WU: 8,
            Branch.WEI: 3,  # Warm but not scorching
            Branch.SHEN: -2,
            Branch.YOU: -2,
            Branch.XU: 0,  # Cool
        }

        # Moisture values - refined
        self.branch_moisture = {
            Branch.ZI: 15,
            Branch.HAI: 15,
            Branch.CHEN: 10,  # Wet
            Branch.CHOU: 8,
            Branch.WEI: 5,  # Damp
            Branch.YIN: 0,
            Branch.MAO: 0,
            Branch.SI: -3,  # Neutral
            Branch.WU: -8,
            Branch.XU: -5,
            Branch.SHEN: 3,  # Dry
            Branch.YOU: 0,
        }

        # Climate adjustment caps - elements never fully extinguished
        self.climate_min_mult = 0.6  # Minimum 60% power after climate
        self.climate_max_mult = 1.4  # Maximum 140% power after climate

    def calculate_seasonal_multiplier(
        self, element: Element, seasonal_factors: SeasonalFactors
    ) -> float:
        """Get the seasonal multiplier for an element"""
        state_map = {
            Element.WOOD: seasonal_factors.wood_state,
            Element.FIRE: seasonal_factors.fire_state,
            Element.EARTH: seasonal_factors.earth_state,
            Element.METAL: seasonal_factors.metal_state,
            Element.WATER: seasonal_factors.water_state,
        }
        return SeasonalFactors.get_multiplier(state_map[element])

    def calculate_temperature_moisture_adjustments(
        self, pillars: List[Pillar]
    ) -> Tuple[float, float]:
        """Calculate overall temperature and moisture of the chart"""
        total_temp = 0
        total_moisture = 0
        total_weight = 0

        for pillar in pillars:
            if pillar.branch and pillar.branch in self.branch_temperature:
                total_temp += (
                    self.branch_temperature[pillar.branch] * pillar.position_weight
                )
                total_moisture += (
                    self.branch_moisture[pillar.branch] * pillar.position_weight
                )
                total_weight += pillar.position_weight

        # Normalize by total weight
        if total_weight > 0:
            total_temp /= total_weight
            total_moisture /= total_weight

        return total_temp, total_moisture

    def check_combinations(self, pillars: List[Pillar]) -> Dict[Element, float]:
        """Check for half-combinations between branches"""
        combo_energy = {
            Element.WOOD: 0,
            Element.FIRE: 0,
            Element.EARTH: 0,
            Element.METAL: 0,
            Element.WATER: 0,
        }

        branches = [(p.branch, p.position_weight) for p in pillars if p.branch]
        branches_set = {b for b, _ in branches}

        # Check all pairs
        for i, (branch1, weight1) in enumerate(branches):
            for branch2, weight2 in branches[i + 1 :]:
                # Check if this pair forms a half combination
                for (b1, b2), (element, strength) in self.half_combinations.items():
                    if (branch1 == b1 and branch2 == b2) or (
                        branch1 == b2 and branch2 == b1
                    ):
                        # Calculate combination energy
                        combo_power = (weight1 + weight2) * strength
                        combo_energy[element] += combo_power

                        # Check for full triplet
                        if self._is_full_triplet(element, branches_set):
                            combo_energy[element] += self.full_triplet_bonus

        return combo_energy

    def _is_full_triplet(self, element: Element, branches_set: set) -> bool:
        """Check if we have all three branches of a triplet"""
        if element == Element.WATER:
            return all(b in branches_set for b in self.water_triplet)
        elif element == Element.WOOD:
            return all(b in branches_set for b in self.wood_triplet)
        elif element == Element.FIRE:
            return all(b in branches_set for b in self.fire_triplet)
        elif element == Element.METAL:
            return all(b in branches_set for b in self.metal_triplet)
        return False

    def check_clashes(self, pillars: List[Pillar]) -> Dict[Branch, float]:
        """Check for clashes between branches and return reduction factors"""
        clash_reduction = {}
        branches = [p for p in pillars if p.branch]

        for i, pillar1 in enumerate(branches):
            for pillar2 in branches[i + 1 :]:
                for b1, b2 in self.clash_pairs:
                    if (pillar1.branch == b1 and pillar2.branch == b2) or (
                        pillar1.branch == b2 and pillar2.branch == b1
                    ):
                        # IMPERIAL CORRECTION: Clashes reduce by 40%, not 50%
                        clash_reduction[pillar1.branch] = (
                            clash_reduction.get(pillar1.branch, 1.0) * 0.6
                        )
                        clash_reduction[pillar2.branch] = (
                            clash_reduction.get(pillar2.branch, 1.0) * 0.6
                        )

        return clash_reduction

    def calculate_root_depth_factor(
        self, stem: Stem, pillar: Pillar, all_pillars: List[Pillar]
    ) -> float:
        """Calculate how much root support a stem has"""
        root_factor = 1.0
        stem_element = STEM_ELEMENT_MAP[stem]

        # Check if stem has root in its own pillar
        if pillar.branch and BRANCH_ELEMENT_MAP[pillar.branch] == stem_element:
            root_factor *= 1.3  # Strong root in same pillar (reduced from 1.5)

        # Check other pillars for roots
        for other in all_pillars:
            if other.branch and other != pillar and other.stem:
                if BRANCH_ELEMENT_MAP[other.branch] == stem_element:
                    # IMPERIAL CORRECTION 5: Distance factors reduced
                    distance = abs(
                        self._get_pillar_distance(pillar.position, other.position)
                    )
                    if distance == 1:
                        root_factor *= (
                            1.15  # Adjacent pillar support (reduced from 1.3)
                        )
                    elif distance == 2:
                        root_factor *= 1.05  # Separated by one (reduced from 1.15)

        return root_factor

    def _get_pillar_distance(self, pos1: str, pos2: str) -> int:
        """Get distance between pillars (0=same, 1=adjacent, 2=separated by one)"""
        order = ["year", "month", "day", "hour"]
        if pos1 in order and pos2 in order:
            return abs(order.index(pos1) - order.index(pos2))
        return 3

    def calculate_penetration_effects(
        self, pillars: List[Pillar]
    ) -> Dict[Element, float]:
        """Calculate how hidden stems penetrate to visible stems

        IMPORTANT: For "Pure Pillars" (stem and branch same element), reduce penetration
        to avoid double-counting with root support.
        """
        penetration_bonus = {
            Element.WOOD: 0,
            Element.FIRE: 0,
            Element.EARTH: 0,
            Element.METAL: 0,
            Element.WATER: 0,
        }

        # Map visible stems by element
        visible_stems = {}
        for pillar in pillars:
            if pillar.stem:
                element = STEM_ELEMENT_MAP[pillar.stem]
                if element not in visible_stems:
                    visible_stems[element] = []
                visible_stems[element].append(pillar)

        # Check hidden stems for penetration
        for pillar in pillars:
            for hidden in pillar.hidden_stems:
                hidden_element = STEM_ELEMENT_MAP[hidden.stem]

                # If this hidden stem's element appears as a visible stem
                if hidden_element in visible_stems:
                    for visible_pillar in visible_stems[hidden_element]:
                        # Calculate distance
                        distance = self._get_pillar_distance(
                            pillar.position, visible_pillar.position
                        )

                        # Check if visible_pillar is a "Pure Pillar" (stem and branch same element)
                        is_pure_pillar = (
                            visible_pillar.stem_element
                            == visible_pillar.branch_element
                            == hidden_element
                        )

                        # IMPERIAL CORRECTION 6: Penetration bonuses greatly reduced
                        # For Pure Pillars, reduce further to avoid double-counting with root support
                        penetration_multiplier = 0.5 if is_pure_pillar else 1.0

                        if distance == 0:  # Same pillar
                            penetration_bonus[hidden_element] += (
                                0.08 * hidden.depth * penetration_multiplier
                            )  # Reduced from 0.3
                        elif distance == 1:  # Adjacent
                            penetration_bonus[hidden_element] += (
                                0.04 * hidden.depth * penetration_multiplier
                            )  # Reduced from 0.2
                        elif distance == 2:  # Separated by one
                            penetration_bonus[hidden_element] += (
                                0.02 * hidden.depth * penetration_multiplier
                            )  # Reduced from 0.1

        # Cap penetration bonuses
        for element in penetration_bonus:
            penetration_bonus[element] = min(
                penetration_bonus[element], 0.15
            )  # Max 15% total

        return penetration_bonus

    def calculate_earth_support(self, pillars: List[Pillar]) -> float:
        """IMPERIAL ADDITION: Earth elements support each other"""
        earth_count = 0

        for pillar in pillars:
            if pillar.stem_element == Element.EARTH:
                earth_count += 1.0  # Full stem counts as 1
            if pillar.branch_element == Element.EARTH:
                earth_count += 0.5  # Branch counts as 0.5

        # Earth supports itself - more Earth = stronger foundation
        if earth_count >= 2:
            return 0.05 * earth_count  # 5% per Earth element, capped
        return 0.0

    def get_climate_adjustments(
        self, element: Element, temp: float, moisture: float
    ) -> Tuple[float, float]:
        """
        IMPERIAL CORRECTION 7: Climate effects are moderate with caps
        """
        temp_mult = 1.0
        moisture_mult = 1.0

        if element == Element.FIRE:
            # Fire: warmth helps, moisture hurts (but never below 60%)
            temp_mult = 1.0 + (temp / 200)  # More moderate: 1.0 ± 0.05 per 10°
            moisture_mult = 1.0 - (moisture / 400)  # More moderate
        elif element == Element.WATER:
            # Water: cold helps, moisture helps
            temp_mult = 1.0 - (temp / 400)  # More moderate
            moisture_mult = 1.0 + (moisture / 300)  # More moderate
        elif element == Element.WOOD:
            # Wood: moisture helps slightly
            moisture_mult = 1.0 + (moisture / 500)  # Very subtle
        elif element == Element.EARTH:
            # Earth: moisture hurts slightly
            moisture_mult = 1.0 - (moisture / 500)  # Very subtle
        elif element == Element.METAL:
            # Metal: Cold weakens Metal, Moisture rusts/weakens Metal
            moisture_mult = 1.0 - (moisture / 500)
            temp_mult = 1.0 - (temp / 500)

        # Apply caps
        temp_mult = max(self.climate_min_mult, min(self.climate_max_mult, temp_mult))
        moisture_mult = max(
            self.climate_min_mult, min(self.climate_max_mult, moisture_mult)
        )

        return temp_mult, moisture_mult

    def calculate_wu_xing_strength_ming_dynasty(
        self, pillars: List[Pillar], month_branch: Branch
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate Wu Xing strength using proper Ming Dynasty Qi Dynamics method.

        Structure (no artificial layers):
        - Branch weights: 0.5 + 0.25 + 0.125 + 0.125 = 1.0
        - Hidden stems: Subsets of branch power via depth percentages (0.7, 0.25, 0.05)
        - Heavenly stems: 4 × 0.025 = 0.1
        - Total naturally ~1.1 (no forced normalization)

        Adjustments applied as multipliers to base power, not separate layers.
        """

        # Get all influencing factors
        seasonal = get_seasonal_factors(month_branch)
        temp, moisture = self.calculate_temperature_moisture_adjustments(pillars)
        combo_energy = self.check_combinations(pillars)
        clash_reduction = self.check_clashes(pillars)
        penetration = self.calculate_penetration_effects(pillars)
        earth_support = self.calculate_earth_support(pillars)

        print("Seasonal factors:", seasonal)
        print(
            "Fire state:",
            seasonal.fire_state,
            "Multiplier:",
            SeasonalFactors.get_multiplier(seasonal.fire_state),
        )
        print(
            "Water state:",
            seasonal.water_state,
            "Multiplier:",
            SeasonalFactors.get_multiplier(seasonal.water_state),
        )

        # Initialize power accumulators
        power = {
            Element.WOOD: 0,
            Element.FIRE: 0,
            Element.EARTH: 0,
            Element.METAL: 0,
            Element.WATER: 0,
        }

        # STEP 1: Branch power with hidden stems as subsets
        for pillar in pillars:
            if pillar.branch:
                # Base branch weight from position
                branch_reduction = clash_reduction.get(pillar.branch, 1.0)
                base_branch_weight = pillar.position_weight * branch_reduction

                # Hidden stems consume part of branch power via depth
                for hidden in pillar.hidden_stems:
                    element = STEM_ELEMENT_MAP[hidden.stem]
                    seasonal_mult = self.calculate_seasonal_multiplier(
                        element, seasonal
                    )
                    temp_mult, moisture_mult = self.get_climate_adjustments(
                        element, temp, moisture
                    )

                    # Hidden stem power = branch weight × depth × adjustments
                    hidden_power = (
                        base_branch_weight
                        * hidden.depth
                        * seasonal_mult
                        * temp_mult
                        * moisture_mult
                    )
                    power[element] += hidden_power

        print("\n=== DEBUG: After STEP 1 (Branches with hidden stems) ===")
        print(f"Power sum: {sum(power.values()):.3f}")
        for element, value in power.items():
            print(f"  {element.value}: {value:.3f}")

        # STEP 2: Heavenly stem power (independent layer)
        for pillar in pillars:
            if pillar.stem:
                element = STEM_ELEMENT_MAP[pillar.stem]
                seasonal_mult = self.calculate_seasonal_multiplier(element, seasonal)
                root_factor = self.calculate_root_depth_factor(
                    pillar.stem, pillar, pillars
                )
                temp_mult, moisture_mult = self.get_climate_adjustments(
                    element, temp, moisture
                )
                pen_bonus = penetration.get(element, 0)

                # Stem power = fixed weight × root support × seasonal × climate + penetration
                stem_power = (
                    self.stem_weight
                    * root_factor
                    * seasonal_mult
                    * temp_mult
                    * moisture_mult
                ) + pen_bonus

                power[element] += stem_power

        print("\n=== DEBUG: After STEP 2 (Heavenly stems) ===")
        print(f"Power sum: {sum(power.values()):.3f}")
        for element, value in power.items():
            print(f"  {element.value}: {value:.3f}")

        # STEP 3: Add subtle effects
        for element, energy in combo_energy.items():
            power[element] += energy
        power[Element.EARTH] += earth_support

        print("\n=== DEBUG: After STEP 3 (Combinations + Earth support) ===")
        print(f"Combo energy: {combo_energy}")
        print(f"Earth support: {earth_support}")
        print(f"Power sum: {sum(power.values()):.3f}")
        for element, value in power.items():
            print(f"  {element.value}: {value:.3f}")

        # STEP 4: Calculate percentages from total power
        total_power = sum(power.values())
        percentages = {}
        if total_power > 0:
            for element, value in power.items():
                percentages[element.value] = round((value / total_power) * 100, 2)

        # STEP 5: Seasonal states for interpretation
        seasonal_states = {
            Element.WOOD.value: seasonal.wood_state,
            Element.FIRE.value: seasonal.fire_state,
            Element.EARTH.value: seasonal.earth_state,
            Element.METAL.value: seasonal.metal_state,
            Element.WATER.value: seasonal.water_state,
        }

        # STEP 6: Format adjustment factors for output
        formatted_adjustments = {
            "温度": round(temp, 1),
            "湿度": round(moisture, 1),
            "组合能量": {
                k.value: round(v, 2) for k, v in combo_energy.items() if v > 0
            },
            "穿透加成": {k.value: round(v, 3) for k, v in penetration.items() if v > 0},
            "相冲减损": {b.value: round(v, 2) for b, v in clash_reduction.items()},
            "地球支持": round(earth_support, 3),
        }

        print("\n=== DEBUG: FINAL POWER ===")
        print(f"Total raw power: {sum(power.values()):.3f}")
        for element, value in power.items():
            print(f"  {element.value}: {value:.3f}")

        return {
            "原始力量": {k.value: round(v, 3) for k, v in power.items()},
            "百分比": percentages,
            "季节状态": seasonal_states,
            "调整因子": formatted_adjustments,
        }


def calculate_wu_xing_strength_professional(
    year_wu_xing: str,
    month_wu_xing: str,
    day_wu_xing: str,
    hour_wu_xing: str,
    year_hide_gan: List[str],
    month_hide_gan: List[str],
    day_hide_gan: List[str],
    hour_hide_gan: List[str],
    year_stem: Optional[str] = None,
    month_stem: Optional[str] = None,
    day_stem: Optional[str] = None,
    hour_stem: Optional[str] = None,
    year_branch: Optional[str] = None,
    month_branch: Optional[str] = None,
    day_branch: Optional[str] = None,
    hour_branch: Optional[str] = None,
) -> Dict[str, Dict[str, float]]:
    """
    Professional calculation of Wu Xing strength using Ming Dynasty Qi Dynamics method
    """

    calculator = MingQiDynamicsCalculator()

    # Create pillars with proper branch and stem identification
    pillars = []

    # Year pillar
    year_branch_enum = STRING_TO_BRANCH.get(year_branch) if year_branch else None
    year_stem_enum = STRING_TO_STEM.get(year_stem) if year_stem else None

    year_pillar = Pillar(
        stem=year_stem_enum,
        branch=year_branch_enum,
        stem_element=STRING_TO_ELEMENT.get(year_wu_xing[0]) if year_wu_xing else None,
        branch_element=(
            STRING_TO_ELEMENT.get(year_wu_xing[1])
            if year_wu_xing and len(year_wu_xing) > 1
            else None
        ),
        hidden_stems=[
            HiddenStem(
                stem=STRING_TO_STEM[hs],
                depth=(
                    get_depth_for_stem(year_branch_enum, hs)
                    if year_branch_enum
                    else 0.33
                ),
            )
            for hs in year_hide_gan
            if hs in STRING_TO_STEM
        ],
        position="year",
        position_weight=0.125,
    )
    pillars.append(year_pillar)

    # Month pillar
    month_branch_enum = STRING_TO_BRANCH.get(month_branch) if month_branch else None
    month_stem_enum = STRING_TO_STEM.get(month_stem) if month_stem else None

    month_pillar = Pillar(
        stem=month_stem_enum,
        branch=month_branch_enum,
        stem_element=STRING_TO_ELEMENT.get(month_wu_xing[0]) if month_wu_xing else None,
        branch_element=(
            STRING_TO_ELEMENT.get(month_wu_xing[1])
            if month_wu_xing and len(month_wu_xing) > 1
            else None
        ),
        hidden_stems=[
            HiddenStem(
                stem=STRING_TO_STEM[hs],
                depth=(
                    get_depth_for_stem(month_branch_enum, hs)
                    if month_branch_enum
                    else 0.33
                ),
            )
            for hs in month_hide_gan
            if hs in STRING_TO_STEM
        ],
        position="month",
        position_weight=0.50,
    )
    pillars.append(month_pillar)

    # Day pillar
    day_branch_enum = STRING_TO_BRANCH.get(day_branch) if day_branch else None
    day_stem_enum = STRING_TO_STEM.get(day_stem) if day_stem else None

    day_pillar = Pillar(
        stem=day_stem_enum,
        branch=day_branch_enum,
        stem_element=STRING_TO_ELEMENT.get(day_wu_xing[0]) if day_wu_xing else None,
        branch_element=(
            STRING_TO_ELEMENT.get(day_wu_xing[1])
            if day_wu_xing and len(day_wu_xing) > 1
            else None
        ),
        hidden_stems=[
            HiddenStem(
                stem=STRING_TO_STEM[hs],
                depth=(
                    get_depth_for_stem(day_branch_enum, hs) if day_branch_enum else 0.33
                ),
            )
            for hs in day_hide_gan
            if hs in STRING_TO_STEM
        ],
        position="day",
        position_weight=0.25,
    )
    pillars.append(day_pillar)

    # Hour pillar
    hour_branch_enum = STRING_TO_BRANCH.get(hour_branch) if hour_branch else None
    hour_stem_enum = STRING_TO_STEM.get(hour_stem) if hour_stem else None

    hour_pillar = Pillar(
        stem=hour_stem_enum,
        branch=hour_branch_enum,
        stem_element=STRING_TO_ELEMENT.get(hour_wu_xing[0]) if hour_wu_xing else None,
        branch_element=(
            STRING_TO_ELEMENT.get(hour_wu_xing[1])
            if hour_wu_xing and len(hour_wu_xing) > 1
            else None
        ),
        hidden_stems=[
            HiddenStem(
                stem=STRING_TO_STEM[hs],
                depth=(
                    get_depth_for_stem(hour_branch_enum, hs)
                    if hour_branch_enum
                    else 0.33
                ),
            )
            for hs in hour_hide_gan
            if hs in STRING_TO_STEM
        ],
        position="hour",
        position_weight=0.125,
    )
    pillars.append(hour_pillar)

    # Ensure we have a valid month branch for seasonal factors
    if not month_branch_enum:
        # Try to determine from hidden stems
        for branch, info in BRANCH_DATABASE.items():
            branch_stems = {info.primary_stem.value}
            if info.secondary_stem:
                branch_stems.add(info.secondary_stem.value)
            if info.residual_stem:
                branch_stems.add(info.residual_stem.value)

            if set(month_hide_gan) == branch_stems:
                month_branch_enum = branch
                break

        if not month_branch_enum:
            month_branch_enum = Branch.YIN  # Default fallback

    # Calculate strength
    result = calculator.calculate_wu_xing_strength_ming_dynasty(
        pillars, month_branch_enum
    )

    # Add minimal context for LLM understanding
    day_master_element = (
        day_pillar.stem_element.value if day_pillar.stem_element else "未知"
    )

    result["数值说明"] = {
        "原始力量": "各五行原始能量值，总和约为1.1，包括地支(1.0)和天干(0.1)的能量比例",
        "百分比": "各五行能量百分比，总和100%",
        "温度": "命盘寒暖度，负值为寒，正值为暖，单位°C",
        "湿度": "命盘燥湿度，负值为燥，正值为湿，单位%",
        "组合能量": "地支半合三会产生的额外能量",
        "穿透加成": "藏干透出天干产生的能量加成",
        "相冲减损": "地支相冲导致的能量减损",
        "地球支持": "土元素之间的相互支持",
        "季节状态": {
            "旺": "当令极旺",
            "相": "得生有力",
            "休": "退休无力",
            "囚": "被困受制",
            "死": "死绝无用",
        },
        "日主": day_master_element,
    }

    return result


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from src.astronomer_calculations.bazi_pillars import get_bazi_pillars
    from lunar_python import Solar

    # python -m src.astronomer_calculations.wu_xing

    # # Desmond's birthday example
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)  # Create solar date
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)  # Create datetime object
    tst_birthday, _ = get_true_solar_time(
        datetime_birthday, 1.3253, 103.808053
    )  # Get true solar time

    # # Corinne's birthday example
    # solar_birthday= Solar.fromYmdHms(1987, 6, 3, 12, 6, 0)  # Create solar date June 3, 1987 at 12:06 PM
    # tst_birthday, inputs_report = get_true_solar_time(datetime(1987, 6, 3, 12, 6, 0), 1.4759, 103.808053)  # Get true solar time for the birthday

    # # Lara's birthday example
    # solar_birthday = Solar.fromYmdHms(
    #     2025, 7, 31, 9, 10, 0
    # )  # Create solar date June 3, 1987 at 12:06 PM
    # tst_birthday, inputs_report = get_true_solar_time(
    #     datetime(2025, 7, 31, 9, 10, 0), 1.3253, 103.808053
    # )

    print("阳历生日: " + solar_birthday.toYmdHms())
    print("真太阳时生日: " + tst_birthday.toYmdHms())

    lunar_birthday = tst_birthday.getLunar()  # Convert to lunar calendar

    bazi = lunar_birthday.getEightChar()
    print(
        f"\nBaZi: {bazi.getYear()}, {bazi.getMonth()}, {bazi.getDay()}, {bazi.getTime()}"
    )

    # Get Wu Xing in LLM-ready JSON format
    result = get_wu_xing(lunar_birthday)

    print(f"\n--- JSON Output for LLM ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))
