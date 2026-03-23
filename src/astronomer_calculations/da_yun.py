"""
Da Yun (大运 - Big Luck Cycles) Calculation Module

This module calculates the Big Luck Cycles (Da Yun) for a given lunar birthday and gender.
Each Da Yun cycle lasts 10 years and represents a major phase of life's fortune.

Comprehensive BaZi Destiny Analysis Components:

1. 起运 (Luck Cycle Start):
   - Gender-dependent timing based on birth solar term position
   - 顺推 (forward progression) or 逆推 (backward progression) logic

2. 大运周期 (10-Year Big Luck Cycles):
   - 10 consecutive cycles covering major life phases
   - Year ranges and age calculations included for each cycle

3. 干支 (Heavenly Stem & Earthly Branch):
   - Complete Gan-Zhi representation for each cycle
   - 旬 (Sexagenary Cycle) and 旬空 (Void Day) information

4. 五行 (Five Elements with Polarity):
   - Stem Five Element (干:木/火/土/金/水) and polarity (阳/阴)
   - Branch Five Element (支:木/火/土/金/水) and polarity (阳/阴)
   - Derived from lunar-python library data

5. 纳音 (Nayin - Harmonic Resonance Element):
   - Descriptive nayin names for each stem-branch combination
   - Examples: "海中金" (Gold in the Sea), "炉中火" (Fire in the Furnace)
   - Classical BaZi concept from lunar-python library's LunarUtil.NAYIN mapping

6. 十神 (Ten Gods - Relational Categories):
   - Primary theme: Based on Day Stem vs. Cycle Stem relationship
   - Hidden themes: Ten Gods for all three hidden stems in branch (本气/中气/余气)
   - 10 relationship categories mapping: 正财/偏财/正官/七杀/正印/偏印/食神/伤官/比肩/劫财

7. 地势 (Life Stage - Long Life Palace):
   - 12-stage positional strength from 长生十二宫 system
   - Maps each stem-branch pair to its corresponding life stage
   - Values: 长生→沐浴→冠带→临官→帝旺→衰→病→死→墓→绝→胎→养

8. 作用 (Interactions - Comprehensive 1×4 Scan):
   Da Yun pillar scanned against all 4 natal pillars with Tier-Based Priority (16 types):

   TIER 0-1 (Framework - Extreme):
   - 反吟: Stem clash + Branch clash (same natal pillar) → complete instability
   - 伏吟: Stem match + Branch match (same natal pillar) → stagnation

   TIER 2-3 (Framework - Structural):
   - 三会: Directional combination (3 branches, one per pillar)
   - 三合: Triple harmony (3 branches, specific elements)
   - 六冲: Clash (6 combinations) + 开库 sub-type (Earth tomb release)
   - 六合: Six Harmony (6 combinations with transformation)

   TIER 4-7 (Dynamics - Partial Combinations):
   - 共拱: Co-arching (two partial combos converging on missing branch)
   - 比和: Peer combinations (adjacent same-element branches)
   - 拱会: Two non-cardinal branches virtually pulling toward missing cardinal
   - 残会/半合: Cardinal + one flank, or partial element triple

   TIER 8-14 (Details - Stem & Parasitic):
   - 天干合(日主): Day Master stem harmony (highest stem priority)
   - 天干克(日主): Day Master stem clash (Day Master threat)
   - 天干合: Heavenly stem harmony
   - 天干克: Heavenly stem control
   - 天干冲: Heavenly stem opposition (same polarity, mutual clash)
   - 三刑 (Triple Punishments): [寅巳申], [丑戌未], Zi-Mao uncivilized, self-punishment
   - 六害: Six Harms (parasitic draining)
   - 六破: Six Destructions (undermining)

   TIER 15-19 (Covert):
   - 暗合: Hidden stem harmony (隐秘, constructive but weakest)

   Distance Semantics (紧贴 field):
   - Adjacent (月柱/日柱): Full-force interactions (正冲/正合/etc.)
   - Distant (年柱/时柱): Attenuated interactions (遥冲/遥合/etc.)
   - Applies to: 六冲, 六合, 六害, 六破, 天干克, 天干冲, 比和, all punishments

   Post-Calculation Modulation (apply_da_yun_master_priority):
   - Hierarchical strength scoring: 强势主流 → 显著影响 → 中等衰减 → 大幅衰减 → 消融吸收
   - Tier 0 (反吟/伏吟) absorbs or reduces lower-tier interactions
   - Tier 1 (三会/三合) suppresses interactions on same pillars
   - Tier 2 (六冲) shatters harmonies and amplifies conflicts
   - Tier 3 (六合) stabilizes and suppresses negative interactions
   - Stem interaction priority: 天干合 > 天干克

Key Functions:

    get_da_yun(lunar_birthday, gender):
        Calculates complete Big Luck Cycles analysis.
        Args:
            lunar_birthday (Lunar): Lunar calendar object
            gender (int): 0 for Female, 1 for Male
        Returns:
            dict: 10 × Big Luck Cycles with interactions, strengths, and interpretations

    _detect_da_yun_interactions(da_yun_stem, da_yun_branch, birth_chart):
        1×4 scan detecting all interaction types between Da Yun pillar and 4 natal pillars.
        Uses set-based validators for accuracy.
        Returns raw interactions (pre-modulation).

    apply_da_yun_master_priority(all_interactions, zhis):
        Post-calculation filtering and strength modulation.
        Applies hierarchical priority rules to assign 强度 scores.
        Sorts by DA_YUN_TIER_ORDER for consistent output.

Output Format:
    All dictionary keys and values use Chinese characters for consistency.
    Integrates lunar-python library data for accuracy and reliability.
    Each Da Yun cycle includes complete interaction details with:
    - 组合: interaction partners
    - 組合明細: detailed mapping
    - 状态: normalized status (正/遥)
    - 强度: strength level post-modulation
    - 备注: contextual interpretation
    - 紧贴: adjacency flag for distance semantics
"""

from lunar_python import Lunar
from lunar_python.util import LunarUtil
from lunar_python.EightChar import EightChar
from src.astronomer_calculations.cycle_na_yin import get_nayin
from src.astronomer_calculations.cycle_interactions import get_cycle_interactions
from src.astronomer_calculations.day_master import get_day_master
from src.astronomer_calculations.cycle_di_shi import get_di_shi
from src.astronomer_calculations.cycle_wu_xing import CycleWuXingDynamics
from src.astronomer_calculations.cycle_shen_sha import get_cycle_shen_sha
from src.astronomer_calculations.void_xun_kong import get_xun_kong

# Pillar names for reference
pillar_names = ["年柱", "月柱", "日柱", "时柱"]

def get_da_yun(lunar_birthday: Lunar, gender: int) -> dict:
    """
    Calculate Big Luck Cycles (Da Yun) from lunar birthday and gender.

    Args:
        lunar_birthday (Lunar): Lunar calendar object
        gender (int): 0 for Female, 1 for Male

    Returns:
        dict: Structured JSON with Da Yun cycles and timing information
    """
    # Get the EightChar (八字) object
    bazi = lunar_birthday.getEightChar()

    # Compute natal xun kong internally
    natal_xk = get_xun_kong(lunar_birthday).get("旬空", {})

    # Day master 通根 tier — used to contextualise 开库 墓库境况
    tong_gen = get_day_master(lunar_birthday).get("日主", {}).get("得地", {}).get("通根", "中根")

    # Extract natal chart pillars for interaction detection
    natal_chart = {
        "year": {
            "stem": bazi.getYearGan(),
            "branch": bazi.getYearZhi(),
        },
        "month": {
            "stem": bazi.getMonthGan(),
            "branch": bazi.getMonthZhi(),
        },
        "day": {
            "stem": bazi.getDayGan(),
            "branch": bazi.getDayZhi(),
        },
        "hour": {
            "stem": bazi.getTimeGan(),
            "branch": bazi.getTimeZhi(),
        },
    }

    # Calculate 起运 (start of luck cycle) based on gender
    yun = bazi.getYun(gender)

    # Get the solar date when 起运 begins
    qi_yun_date = yun.getStartSolar()

    # Get all 大运 (Big Luck Cycles) - default 10 cycles
    da_yun_list = yun.getDaYun()

    # Process each 大运 into structured format
    da_yun_data = []
    for i, da_yun in enumerate(da_yun_list):
        gan_zhi = da_yun.getGanZhi()

        # Extract Gan (stem) and Zhi (branch) for Ten Gods analysis
        # Gan-Zhi format is like "戊子", "己丑", etc.
        da_yun_stem = gan_zhi[0] if len(gan_zhi) > 0 else ""
        da_yun_branch = gan_zhi[1] if len(gan_zhi) > 1 else ""

        # Calculate for this 大运
        if i > 0:  # Skip first cycle (no Gan-Zhi)
            cycle_xk_str = da_yun.getXunKong()
            # Detect interactions (作用) with natal chart using sophisticated 1x4 scan
            interactions_result = get_cycle_interactions(
                da_yun_stem, da_yun_branch, natal_chart,
                cycle_xk_str=cycle_xk_str,
                natal_xk=natal_xk,
                tong_gen=tong_gen,
            )
            interactions = interactions_result.get("作用", [])

            # Five Elements dynamics: enriched cycle pillar info + combined natal+cycle 五行力量
            cycle_wu_xing_info = CycleWuXingDynamics().calculate_cycle_interaction(
                da_yun, lunar_birthday,
                priority_list=interactions_result.get("_raw_priority_list", []),
                cycle_type="大运",
                xun_kong_data=natal_xk,
                cycle_xk_str=cycle_xk_str,
            )
            cycle_pillar_info = cycle_wu_xing_info.pop("大运柱", {})
            cycle_wu_xing_result = cycle_wu_xing_info.get("五行力量分析", "无数据")

            # Extract Shen Sha (神煞) for this cycle
            cycle_shen_sha = get_cycle_shen_sha(da_yun_stem, da_yun_branch, natal_chart, gender)
        else:
            interactions = "未行大运"
            cycle_pillar_info = "未行大运"
            cycle_wu_xing_result = "未行大运"
            cycle_shen_sha = "未行大运"

        # Assemble Da Yun data for this cycle
        da_yun_info = {
            # "序号": (
            #     "未行大运" if i == 0 else i
            # ),  # Index/sequence number (0 = before start)
            "开始年份": da_yun.getStartYear(),  # Start calendar year
            "结束年份": da_yun.getEndYear(),  # End calendar year
            "开始年龄": da_yun.getStartAge(),  # Start age (from birth)
            "结束年龄": da_yun.getEndAge(),  # End age (from birth)
            "周期": f"{da_yun.getStartAge()}-{da_yun.getEndAge()}岁",  # Age range display
            "运柱": cycle_pillar_info,  # Enriched cycle pillar: 五行, 十神, 通根, 藏干, 季节状态, 十二长生
            "五行力量": cycle_wu_xing_result,  # Combined natal+cycle 五行力量分析
            "神煞": cycle_shen_sha if i > 0 else "未行大运",  # Shen Sha stars for this cycle
            "作用": interactions,  # Branch and Stem interactions with birth chart
        }
        da_yun_data.append(da_yun_info)

    # Compile the complete da_yun structure
    return {
        "大运": {
            "起运": {
                "性别": "男" if gender == 1 else "女",
                "出生阳历": lunar_birthday.getSolar().toYmdHms(),
                "出生农历": f"{lunar_birthday.getYear()}-{lunar_birthday.getMonth():02d}-{lunar_birthday.getDay():02d} {lunar_birthday.getHour():02d}:{lunar_birthday.getMinute():02d}:{lunar_birthday.getSecond():02d}",
                "起运阳历": qi_yun_date.toYmdHms(),
                "起运计岁": f"{yun.getStartYear()}年{yun.getStartMonth()}月{yun.getStartDay()}天{yun.getStartHour()}小时",
                "顺逆": "顺推" if yun.isForward() else "逆推",
            },
            "大运周期": da_yun_data,
        }
    }


# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    import json
    from datetime import datetime
    from lunar_python import Solar
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
    from src.astronomer_calculations.bazi_pillars import get_bazi_pillars
    from src.utils.logging import configure_logging, get_logger

    # Configure logging system (creates logs in logs/YYYY-MM-DD/HH-MM-SS/app.log)
    configure_logging()
    logger = get_logger(__name__)

    # python -m src.astronomer_calculations.da_yun

    # Desmond's birthday example - Female test
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)
    tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)

    # Corinne's birthday example
    # solar_birthday = Solar.fromYmdHms(
    #     1987, 6, 3, 12, 6, 0
    # )  # Create solar date June 3, 1987 at 12:06 PM
    # tst_birthday, inputs_report = get_true_solar_time(
    #     datetime(1987, 6, 3, 12, 6, 0), 1.4759, 103.808053
    # )
    lunar_birthday = tst_birthday.getLunar()

    bazi_json = get_bazi_pillars(tst_birthday.getLunar())
    logger.info(f"八字: {bazi_json}")

    # logger.info("=== Female (Gender=0) ===")
    # result = get_da_yun(lunar_birthday, gender=0)
    # logger.info(json.dumps(result, ensure_ascii=False, indent=2))

    logger.info("=== Male (Gender=1) ===")
    result = get_da_yun(lunar_birthday, gender=1)
    logger.info(json.dumps(result, ensure_ascii=False, indent=2))
