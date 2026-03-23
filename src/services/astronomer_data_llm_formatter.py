"""
Astronomer Data LLM Formatter

Converts raw astronomer data into LLM-friendly formats.
Organizes complex astrological data into semantic groups for better LLM understanding.
"""


class AstroDataLLMFormatter:
    """Formats aggregated astronomer data for LLM consumption"""

    def __init__(self, raw_data: dict):
        """
        Initialize formatter with raw data from AstroDataAggregator.collect_data()

        Args:
            raw_data (dict): Output from AstroDataAggregator.collect_data()
        """
        self.raw_data = raw_data

    def _extract_basic_info(self) -> dict:
        """
        Extract and organize basic birth information for LLM consumption.

        Extracts:
        - 调整阳历生日 (Adjusted Solar Birthday)
        - 农历生日 (Lunar Birthday)
        - 天命大盘 (Destiny Wheel / Full Lunar Designation)
        - 性别 (Gender)
        - 时令 (Seasonal Context & Timing)

        Returns:
            dict: Organized basic information
        """
        basic_info = self.raw_data.get("basic_info", {})

        return {
            "阳历生日": basic_info.get("调整阳历生日"),
            "农历生日": basic_info.get("农历生日"),
            "天命大盘": basic_info.get("天命大盘"),
            "性别": basic_info.get("性别"),
            "时令": basic_info.get("时令"),
        }

    def _extract_birth_environment(self) -> dict:
        """
        Extract and reorganize birth environment data for LLM consumption.

        Reorganizes raw birth-environment data into 4 strategic groups:
        1. 地理与神性开运 (Geographic & Spiritual Fortune)
        2. 行动策略与禁忌 (Action Strategy & Taboos)
        3. 时令能量状态 (Seasonal Energy State)
        4. 历法与节气进程 (Calendar & Solar Terms Progress)

        Returns:
            dict: Reorganized birth environment data
        """
        # Unwrap the outer "出生环境" key from birth_environment data
        birth_env_outer = self.raw_data.get("birth_environment", {})
        birth_env = birth_env_outer.get("出生环境", {})

        # GROUP 1: STRATEGIC ASSETS (Where/What brings luck)
        directions = birth_env.get("方位与地理运气", {})
        deities = birth_env.get("天神与护佑", {})
        constellation = birth_env.get("星宿与神性背景", {})
        time_directions = birth_env.get("出生时刻方位", {})

        # GROUP 2: ACTIONABLE RULES (Daily Guidance & Warnings)
        auspicious_actions = birth_env.get("宜忌与行动指导", {})
        taboos_clashes = birth_env.get("禁忌与冲煞", {})
        tai_sui_positions = birth_env.get("太岁位置", {})

        # GROUP 3: ENERGY CYCLES (The "Vibe" of the moment)
        seasonal = birth_env.get("季节与节日", {})
        seasonal_cycles = birth_env.get("季节能量周期", {})
        phenology = birth_env.get("物候与天文", {})
        nine_star = birth_env.get("九星能量与风水", {})

        # GROUP 4: CHRONOLOGICAL METADATA (Technical timing)
        qi_markers = birth_env.get("气令与节气", {})
        jie_markers = birth_env.get("节令与中气", {})
        spiritual_calendars = birth_env.get("灵性历源", {})

        return {
            "地理与神性开运": {
                "方位运气": directions,
                "时刻方位": time_directions,
                "神性护佑": {
                    "星宿": constellation,
                    "天神": deities,
                },
            },
            "行动策略与禁忌": {
                "宜忌指引": auspicious_actions,
                "冲煞风险": taboos_clashes,
                "太岁方位": tai_sui_positions,
            },
            "时令能量状态": {
                "季节背景": seasonal,
                "能量周期": seasonal_cycles,
                "物候天文": phenology,
                "九星能量": nine_star,
            },
            "历法与节气进程": {
                "气令进度": qi_markers,
                "节令进度": jie_markers,
                "多维历法": spiritual_calendars,
            },
        }

    def _extract_three_palaces(self) -> dict:
        """
        Extract 三垣 (The Three Palaces) data for LLM consumption.
        Returns:
            dict: 三垣 data if present, else empty dict
        """
        san_yuan_outer = self.raw_data.get("san_yuan", {})
        return san_yuan_outer.get("三垣", {})

    def _extract_tai_xi(self) -> dict:
        """
        Extract 胎息 (Tai Xi) data for LLM consumption.
        Returns:
            dict: 胎息 data if present, else empty dict
        """
        tai_xi_outer = self.raw_data.get("tai_xi", {})
        return tai_xi_outer.get("胎息", {})

    def _extract_core_destiny_chart(self) -> dict:
        """
        Extract and organize the four pillars (四柱) with Five Elements, Nayin, 旬空, and 神煞.

        Combines bazi, wu_xing, na_yin, xun_kong, and shen_sha data into a cohesive pillar structure:
        - 天干 (Heavenly Stem)
        - 地支 (Earthly Branch)
        - 五行 (Five Elements: stem + branch)
        - 藏干 (Hidden Stems in the branch)
        - 纳音 (Nayin - Harmonic Resonance Element)
        - 旬空 (Void Cycle info)
        - 神煞 (Shen Sha - Spiritual Killers)

        Returns:
            dict: Four pillars organized with complete elemental and textual data, plus 旬空 and 神煞
        """
        # bazi data
        bazi_outer = self.raw_data.get("bazi", {})
        bazi = bazi_outer.get("八字", {})

        # wu_xing data
        wu_xing_data = self.raw_data.get("wu_xing", {})
        wu_xing_force = wu_xing_data.get("五行力量", {})
        wu_xing_basic_info = wu_xing_force.get("基本信息", {})
        wu_xing_pillars_data = wu_xing_force.get("四柱", {})

        # na_yin data
        na_yin_outer = self.raw_data.get("na_yin", {})
        na_yin_data = na_yin_outer.get("纳音", {})

        # xun_kong data
        xun_kong_outer = self.raw_data.get("xun_kong", {})
        xun_kong_data = xun_kong_outer.get("旬空", {})

        # shen_sha data
        shen_sha_outer = self.raw_data.get("shen_sha", {})
        shen_sha_inner = shen_sha_outer.get("神煞", {})
        shen_sha_data = shen_sha_inner.get("柱位神煞", {})

        # shi_shen data
        shi_shen_outer = self.raw_data.get("shi_shen", {})
        shi_shen_inner = shi_shen_outer.get("十神", {})

        # zuo yong data
        interactions_outer = self.raw_data.get("interactions", {})
        interactions_inner = interactions_outer.get("作用", {})
        zuo_yong_pillar_data = interactions_inner.get("柱位动态", {})
        zuo_yong_relationship_data = interactions_inner.get("关系总览", {})
        rooting_data = interactions_inner.get("根基", {})

        # di_shi data
        di_shi_outer = self.raw_data.get("di_shi", {})
        di_shi_data = di_shi_outer.get("地势", {})

        # Pillar mappings: (Chinese pillar name, Wu_xing key, Na_yin key)
        pillars = {}

        for pillar_name in ["年柱", "月柱", "日柱", "时柱"]:
            # Extract from bazi
            bazi_pillar = bazi.get(pillar_name, {})
            stem = bazi_pillar.get("天干")
            branch = bazi_pillar.get("地支")

            # Extract from wu_xing
            wu_xing_pillar = wu_xing_pillars_data.get(pillar_name, {})
            seasonal_state = wu_xing_pillar.get("季节状态")
            sheng_wang = wu_xing_pillar.get("十二长生")
            tong_gen = wu_xing_pillar.get("通根")
            gan_zhi_wu_xing = wu_xing_pillar.get("干支五行")
            hidden_stems = wu_xing_pillar.get("藏干", [])

            # Extract from na_yin
            nayin = na_yin_data.get(pillar_name, {})

            # Extract from xun_kong
            xun_kong = xun_kong_data.get(pillar_name, {})

            # Extract from shen_sha
            shen_sha_pillar = shen_sha_data.get(pillar_name, {})
            shen_sha_list = shen_sha_pillar.get("神煞", {})

            # Extract from interactions
            zuo_yong = zuo_yong_pillar_data.get(pillar_name, {})

            # Extract from shi_shen
            shi_shen_pillar = shi_shen_inner.get(pillar_name, {})

            # Extract from di_shi
            di_shi_pillar = di_shi_data.get(pillar_name, {})

            pillars[pillar_name] = {
                "天干": stem,
                "地支": branch,
                "藏干": hidden_stems,
                "根基": rooting_data,
                "季节状态": seasonal_state,
                "干支五行": gan_zhi_wu_xing,
                "季节状态": seasonal_state,
                "十二长生": sheng_wang,
                "通根": tong_gen,
                "十神": shi_shen_pillar,
                "地势": di_shi_pillar,
                "纳音": nayin,
                "旬空": xun_kong,
                "神煞": shen_sha_list,
                "作用": zuo_yong,
            }

        return {
            "干支关系总览": zuo_yong_relationship_data,
            "基本信息": wu_xing_basic_info,
            "四柱实体": pillars,
        }

    def _extract_wu_xing(self) -> dict:
        """
        Extract Five Elements Force (五行力量) analysis.

        Retrieves the comprehensive Five Elements strength weightage. Remaining data are extracted under the core destiny chart for better contextualization.

        Returns:
            dict: Five Elements force analysis
        """
        wu_xing_data = self.raw_data.get("wu_xing", {})

        wu_xing_force = wu_xing_data.get("五行力量", {})
        _EXCLUDE = {"基本信息", "四柱"}
        wu_xing_distribution = {k: v for k, v in wu_xing_force.items() if k not in _EXCLUDE}

        wu_xing_scoring_explanation = wu_xing_data.get("五行相位动力", {})

        return {"五行力量": wu_xing_distribution, "五行相位动力": wu_xing_scoring_explanation}

    def _extract_bone_weight(self) -> dict:
        """
        Extract 袁天罡称骨歌 (Yuan Tian Gang Bone Weight) analysis.

        Returns:
            dict: Bone weight analysis and prophetic poem
        """
        bone_weight_outer = self.raw_data.get("bone_weight", {})
        return bone_weight_outer.get("袁天罡称骨歌", {})

    def _extract_shen_sha(self) -> dict:
        """
        Extract 系统神煞 (Systemic Shen Sha) analysis markers.

        Retrieves general Shen Sha indicators that apply to the chart's overall
        relationships rather than specific pillars.

        Returns:
            dict: Relational Shen Sha data
        """
        shen_sha_outer = self.raw_data.get("shen_sha", {})
        shen_sha_inner = shen_sha_outer.get("神煞", {})
        shen_sha_inner2 = shen_sha_inner.get("系统神煞", {})

        return shen_sha_inner2

    def _extract_interactions(self) -> dict:
        """
        Extract 作用 (Interactions) between Heavenly Stems and Earthly Branches.

        This includes:
        - 判定优先级 (Interaction priority hierarchy)

        the following are extracted under the core destiny chart for better contextualization:
        - 关系总览 (Overview of relationships)
        - 柱位动态 (Dynamics per pillar)

        Returns:
            dict: Interaction data and priority definitions
        """
        interactions_outer = self.raw_data.get("interactions", {})
        interactions_inner = interactions_outer.get("作用", {})

        return interactions_inner.get("判定优先级")

    def _extract_day_master(self) -> dict:
        """
        Extract 日主 (Day Master) analysis for LLM consumption.

        Returns:
            dict: Day master with 得令/得地/得势/强弱, or empty dict if unavailable
        """
        day_master_outer = self.raw_data.get("day_master", {})
        return day_master_outer.get("日主", {})

    def _extract_da_yun(self) -> dict:
        """
        Extract 大运 (Da Yun - Big Luck Cycles) data for LLM consumption.

        Returns:
            dict: 大运 metadata and 10-year cycle array, or empty dict if unavailable
        """
        da_yun_outer = self.raw_data.get("da_yun", {})
        return da_yun_outer.get("大运", {})

    def _extract_xiao_yun(self) -> dict:
        """
        Extract 小运 (Xiao Yun - Small Luck Cycles) data for LLM consumption.

        Returns:
            dict: 小运 metadata and annual pre-luck cycle array, or empty dict if unavailable
        """
        xiao_yun_outer = self.raw_data.get("xiao_yun", {})
        return xiao_yun_outer.get("小运", {})

    def _extract_liu_nian_ye(self) -> dict:
        """
        Extract 流年流月 (Liu Nian & Liu Yue) combined data for LLM consumption.

        Returns the full output of get_liu_nian_ye() as stored by the aggregator.
        Each 流年周期 entry embeds its own 流月周期 for years within the 4-year month window.

        Returns:
            dict: Combined 流年 + embedded 流月 structure, or empty dict if unavailable
        """
        return self.raw_data.get("liu_nian_ye", {})

    def _organise_yun_cheng(self) -> dict:
        """
        Organise 运程 (Yun Cheng - Luck Journey) by combining 大运 and 小运 data
        into a single chronological narrative for LLM consumption.

        Structure:
        - 起运信息: When the main luck cycles begin (from 大运 起运 metadata)
        - 小运阶段: Pre-luck annual cycles from birth until 起运 (from 小运)
        - 大运阶段: The main 10-year luck cycles (from 大运周期)

        Returns:
            dict: Combined and organised luck journey data
        """
        da_yun = self._extract_da_yun()
        xiao_yun = self._extract_xiao_yun()

        return {
            "起运信息": xiao_yun.get("起运前", {}),
            "小运阶段": xiao_yun.get("小运周期", {}),
            "大运阶段": da_yun.get("大运周期", {})[1:],  # Skip the first 大运 cycle which is a placeholder. Fill it with 小运 data instead for the pre-luck phase.
        }

    def format_for_llm(self) -> dict:
        """
        Format complete data for LLM consumption.

        Returns:
            dict: Organized data with semantic groups
        """

        formatted_data = {
            "基本信息": self._extract_basic_info(),
            "出生环境": self._extract_birth_environment(),
            "核心命盘": self._extract_core_destiny_chart(),
            "系统神煞": self._extract_shen_sha(),
            "袁天罡称骨歌": self._extract_bone_weight(),
            "先天命数": {
                "三垣": self._extract_three_palaces(),
                "胎息": self._extract_tai_xi(),
            },
            "日主": self._extract_day_master(),
            "五行力量": self._extract_wu_xing().get("五行力量", {}),
            "运程": self._organise_yun_cheng(),
            # "流年流月": self._extract_liu_nian_ye(),
            "分析逻辑参考": {
                "干支作用优先级": self._extract_interactions(),
                "五行相位动力": self._extract_wu_xing().get("五行相位动力", {}),
            },
        }

        return formatted_data


# --- EXECUTION ---
if __name__ == "__main__":
    import json
    from src.services.astronomer_data_aggregator import AstroDataAggregator
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
    from lunar_python import Solar
    from datetime import datetime

    # python -m src.services.astronomer_data_llm_formatter

    # Example: Collect data for Lara
    # solar_birthday = Solar.fromYmdHms(2025, 7, 31, 9, 10, 0)
    # tst_birthday, inputs_report = get_true_solar_time(
    #     datetime(2025, 7, 31, 9, 10, 0), 1.3253, 103.808053
    # )

    # Desmond's birthday example - Female test
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)
    tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)

    # Corinne's birthday example
    # solar_birthday= Solar.fromYmdHms(1987, 6, 3, 12, 6, 0)  # Create solar date June 3, 1987 at 12:06 PM
    # tst_birthday, inputs_report = get_true_solar_time(datetime(1987, 6, 3, 12, 6, 0), 1.4759, 103.808053)
    # lunar_birthday = tst_birthday.getLunar()

    lunar_birthday = tst_birthday.getLunar()

    # Collect raw data
    aggregator = AstroDataAggregator()
    raw_data = aggregator.collect_data(
        lunar_birthday,
        birth_datetime=datetime(1985, 11, 25, 17, 7, 0),
        latitude=1.3253,
        longitude=103.808053,
        gender=1,
    )

    # Format for LLM
    formatter = AstroDataLLMFormatter(raw_data)
    llm_friendly_data = formatter.format_for_llm()

    print("=== LLM-Friendly Format ===")
    print(json.dumps(llm_friendly_data, ensure_ascii=False, indent=2))
