"""
Tests for the 大运/流年 cycles pipeline.

Reference subject: Desmond, 1985-11-25 17:07, (1.3253, 103.808053), male,
TST on. Natal pillars (verified against /natal): 乙丑 丁亥 戊辰 庚申,
day master 戊, chart_key bBdLeEgIM. 乙丑 is a yin year + male → 逆推
(reverse direction), which exercises the non-default 起运 path.

Oracle facts below were hand-verified against the classical rules:
- 逆排 from month pillar 丁亥: 丙戌 乙酉 甲申 癸未 壬午 辛巳 庚辰 己卯 戊寅.
- 太岁 relations vs natal 年支 丑: 丑值, 未冲+刑, 辰破, 午害, 戌刑.

Run:  conda activate astronomer
      python -m pytest apps/backend/tests -q
"""

import json
from datetime import datetime, timedelta

import pytest
from lunar_python.util import LunarUtil

from apps.backend.astronomer_logic.cycles.cycle_interactions import (
    get_cycle_interactions,
)
from apps.backend.astronomer_logic.cycles.cycle_pillars import NatalContext
from apps.backend.astronomer_logic.cycles.cycle_shen_sha import get_cycle_shen_sha
from apps.backend.astronomer_logic.day_master_strength import get_seasonal_factors
from apps.backend.astronomer_logic.natal_five_elements import ELEMENTS, STATE_ORDER
from apps.backend.astronomer_logic.yong_shen import get_yong_shen
from apps.backend.orchestrator.astronomer_data_orchestrator import calculate_natal_chart
from apps.backend.orchestrator.cycles_orchestrator import calculate_cycles

DESMOND = dict(
    birth_datetime=datetime(1985, 11, 25, 17, 7, 0),
    latitude=1.3253,
    longitude=103.808053,
    gender=1,
    use_solar_time_correction=True,
)

# 逆排 from month pillar 丁亥 (index 1..9; index 0 is the pre-运 stub)
DESMOND_DA_YUN_GAN_ZHI = ["丙戌", "乙酉", "甲申", "癸未", "壬午", "辛巳", "庚辰", "己卯", "戊寅"]


@pytest.fixture(scope="module")
def desmond_cycles():
    cycles, chart_key = calculate_cycles(**DESMOND, da_yun_index=4)
    return cycles, chart_key


def make_ctx(
    gans: tuple,
    zhis: tuple,
    gender: int = 1,
    day_void: str = "",
    dm_strength: str = "中和",
    revealed_gods: frozenset = frozenset(),
) -> NatalContext:
    """Hand-built NatalContext for interaction unit tests."""
    hides = tuple(tuple(LunarUtil.ZHI_HIDE_GAN.get(z, [])) for z in zhis)
    return NatalContext(
        gans=gans,
        zhis=zhis,
        hides=hides,
        day_stem=gans[2],
        effective_day_stem=gans[2],
        gender=gender,
        natal_void={"年柱": "", "月柱": "", "日柱": day_void, "时柱": ""},
        na_yin={},
        dm_strength=dm_strength,
        dm_rooting="有根",
        seasonal=get_seasonal_factors(zhis[1]),
        revealed_gods=revealed_gods,
        # Only consumed by get_cycle_wu_xing; interaction unit tests don't need them.
        natal_si_zhu={},
        natal_interactions={},
        lunar_birthday=None,
        natal_five_elements={},
        yong_shen=make_yong_shen(
            gans[2], LunarUtil.WU_XING_GAN[gans[2]], zhis[1], dm_strength
        ),
    )


def make_yong_shen(
    day_stem: str,
    dm_element: str,
    month_branch: str,
    dm_strength: str = "中和",
    *,
    ling: float = 2.0,
    di: float = 2.0,
    shi: float = 2.0,
    root: str = "中根",
    five_elements: dict | None = None,
    interactions: dict | None = None,
) -> dict:
    """get_yong_shen over a synthesised day-master / 五行 / interactions context.

    Defaults describe a rooted, in-season day master → 格局 resolves to 正格, which is what
    the 调候/扶抑 tests want. Pass ling=di=shi=0 (root="无根") to synthesise a 从格 candidate,
    and `five_elements` with 力量 to steer which force it follows.
    """
    dm_data = {
        "日主": {
            "强弱": dm_strength,
            "得令": {"状态": "旺" if ling >= 4 else "休", "分数": ling},
            "得地": {"通根": root, "分数": di},
            "得势": {"得势层级": "中", "分数": shi},
        }
    }
    fe = five_elements or {el: {"力量": 1.0, "状态": "休"} for el in ELEMENTS}
    ix = interactions if interactions is not None else {"作用": {"柱位动态": []}}
    return get_yong_shen(day_stem, dm_element, month_branch, dm_data, fe, ix)


def find(interactions: dict, itype: str) -> list[dict]:
    return [it for it in interactions["柱位动态"] if it["类型"] == itype]


# ── 起运 & 大运 enumeration ─────────────────────────────────────────────────


class TestQiYunAndDaYun:
    def test_reverse_direction_for_yin_year_male(self, desmond_cycles):
        cycles, _ = desmond_cycles
        assert cycles["起运"]["顺逆"] == "逆推"
        assert cycles["起运"]["起运阳历"].startswith("1991-11-04")

    def test_da_yun_sequence_and_ranges(self, desmond_cycles):
        cycles, _ = desmond_cycles
        da_yun = cycles["大运"]
        assert len(da_yun) == 10
        assert [d["干支"] for d in da_yun[1:]] == DESMOND_DA_YUN_GAN_ZHI
        assert da_yun[1]["开始年份"] == 1991
        assert da_yun[1]["周期"] == "7-16岁"
        # decades are contiguous
        for prev, cur in zip(da_yun[1:], da_yun[2:]):
            assert cur["开始年份"] == prev["结束年份"] + 1

    def test_pre_yun_stub(self, desmond_cycles):
        cycles, _ = desmond_cycles
        stub = cycles["大运"][0]
        assert stub["阶段"] == "未行大运"
        assert stub["干支"] == ""
        assert "运柱" not in stub

    def test_chart_key_matches_natal(self, desmond_cycles):
        _, cycles_key = desmond_cycles
        _, natal_key = calculate_natal_chart(**DESMOND)
        assert cycles_key == natal_key == "bBdLeEgIM"


# ── 流年 lazy expansion ─────────────────────────────────────────────────────


class TestLiuNian:
    def test_only_requested_decade_expanded(self, desmond_cycles):
        cycles, _ = desmond_cycles
        for d in cycles["大运"]:
            expected = 10 if d["序号"] == 4 else 0
            assert len(d["流年"]) == expected

    def test_liu_nian_years_and_age(self, desmond_cycles):
        cycles, _ = desmond_cycles
        liu_nian = cycles["大运"][4]["流年"]
        assert [ln["年份"] for ln in liu_nian] == list(range(2021, 2031))
        first = liu_nian[0]
        assert first["干支"] == "辛丑"
        assert first["虚岁"] == 37
        assert first["生肖"] == "牛"
        assert first["流月"] == []  # reserved seam

    def test_tai_sui_relations(self, desmond_cycles):
        cycles, _ = desmond_cycles
        by_year = {ln["年份"]: ln["太岁"]["关系"] for ln in cycles["大运"][4]["流年"]}
        assert by_year[2021] == "值太岁"      # 丑 == natal 年支 丑
        assert by_year[2024] == "破太岁"      # 辰丑破
        assert by_year[2026] == "害太岁"      # 午丑害
        assert "冲太岁" in by_year[2027]      # 丑未冲
        assert "刑太岁" in by_year[2027]      # 丑未刑
        assert by_year[2022] == "无"


# ── 运柱 per-pillar block ───────────────────────────────────────────────────


class TestCyclePillar:
    def test_bing_xu_pillar(self, desmond_cycles):
        cycles, _ = desmond_cycles
        pillar = cycles["大运"][1]["运柱"]  # 丙戌 vs day master 戊
        assert pillar["天干"]["十神"] == "偏印"
        assert pillar["纳音"] == "屋上土"
        assert pillar["十二长生"] == {"日干": "墓", "自坐": "墓"}
        # 丙火 roots only in 戌's 余气 丁 — via the cycle's own branch
        assert pillar["天干"]["根基强度"] == "浅根"
        assert "大运支戌" in pillar["天干"]["通根于"]
        # 戌 sits in the natal 日柱 void pair 戌亥 → 填实, not weakness
        assert "填实" in pillar["空亡"]["落入命局空亡"]

    def test_raw_qi_sha_with_zhi_hua_annotation(self, desmond_cycles):
        cycles, _ = desmond_cycles
        pillar = cycles["大运"][3]["运柱"]  # 甲申: 甲 vs 戊 → 七杀 (RAW, never 偏官)
        assert pillar["天干"]["十神"] == "七杀"
        # natal 时干庚 = revealed 食神 → 食神制杀 annotation
        assert "食神" in pillar["制化"]

    def test_five_branch_rooting_includes_own_branch(self, desmond_cycles):
        cycles, _ = desmond_cycles
        # 流年 2021 辛丑: 辛 roots in natal 丑/申 AND its own 丑 (labeled 流年支)
        ln = cycles["大运"][4]["流年"][0]
        assert ln["运柱"]["天干"]["根基强度"] == "深根"
        assert "流年支丑" in ln["运柱"]["天干"]["通根于"]


# ── 五行动态 combined 4+1 reclassification ──────────────────────────────────

_VALID_STATES = set(STATE_ORDER)
_VALID_DELTAS = {"大升", "升", "持平", "降", "大降"}
# element → ten-god category for a 戊(土) day master (Desmond); fixed per chart.
_DESMOND_TEN_GODS = {"土": "比劫", "金": "食伤", "水": "财星", "木": "官杀", "火": "印星"}


class TestCycleWuXing:
    def _iter_wu_xing(self, cycles):
        """Every populated cycle pillar's 五行动态 (大运 index 1..9 + expanded 流年)."""
        for d in cycles["大运"]:
            if "五行动态" not in d:
                continue  # index-0 pre-运 stub
            yield d["五行动态"]
            for ln in d.get("流年", []):
                yield ln["五行动态"]

    def test_contract_shape(self, desmond_cycles):
        """五行动态 has exactly the new keys — 季节状态/五行构成 were dropped."""
        cycles, _ = desmond_cycles
        wx = cycles["大运"][1]["五行动态"]
        assert set(wx.keys()) == {"五行", "对日主", "引动"}
        assert "季节状态" not in wx and "五行构成" not in wx

    def test_five_elements_verdict_well_formed(self, desmond_cycles):
        cycles, _ = desmond_cycles
        for wx in self._iter_wu_xing(cycles):
            assert set(wx["五行"].keys()) == set(ELEMENTS)
            for verdict in wx["五行"].values():
                assert verdict["状态"] in _VALID_STATES
                assert verdict["本命"] in _VALID_STATES
                assert verdict["变化"] in _VALID_DELTAS
                # NOTE: 变化 is measured on the pre-cap 力量, NOT the capped 状态 — so it
                # may read 升 while 状态 == 本命 (the cap-fix). And 本命 is always the birth
                # anchor while 变化's baseline is the decade for 流年, so 状态/本命/变化 are
                # deliberately NOT tied together. Only field validity is asserted here.

    def test_natal_baseline_matches_natal_endpoint(self, desmond_cycles):
        """本命 in every cycle pillar equals the natal /natal 五行 verdict (shared classifier)."""
        cycles, _ = desmond_cycles
        natal = calculate_natal_chart(**DESMOND)[0]["五行"]
        natal_states = {el: natal[el]["状态"] for el in ELEMENTS}
        for wx in self._iter_wu_xing(cycles):
            for el in ELEMENTS:
                assert wx["五行"][el]["本命"] == natal_states[el]

    def test_triggers_carry_state_and_never_lower_their_element(self, desmond_cycles):
        """Each 引动 tags the triggered element's period 状态; forming a 三合/三会/合化 for
        an element must not push its 力量 DOWN (变化 != 降)."""
        cycles, _ = desmond_cycles
        boosting = {"三合", "三会", "六合合化"}
        for wx in self._iter_wu_xing(cycles):
            for trig in wx["引动"]:
                assert "状态" in trig
                elem = trig["元素"]
                if elem in wx["五行"]:
                    assert trig["状态"] == wx["五行"][elem]["状态"]
                    if trig["类型"] in boosting:
                        assert wx["五行"][elem]["变化"] not in ("降", "大降")

    def test_cycle_moves_something(self, desmond_cycles):
        """The transiting pillars must shift at least one element off its natal baseline —
        otherwise the reclassification is a no-op and the delta is meaningless."""
        cycles, _ = desmond_cycles
        assert any(
            verdict["变化"] != "持平"
            for wx in self._iter_wu_xing(cycles)
            for verdict in wx["五行"].values()
        )

    def test_element_rises_in_its_own_decade(self, desmond_cycles):
        """The cap-fix: each element strengthens in a decade dominated by it, even though
        the seasonal cap pins the displayed 状态. 变化 is read on the pre-cap 力量, so 金 in
        the 乙酉 (metal) decade shows 状态=相 (capped, == 本命) yet a rise. Before the fix
        these were all 持平 (the cap hid every off-season gain)."""
        cycles, _ = desmond_cycles
        dy = {d["干支"]: d["五行动态"]["五行"] for d in cycles["大运"] if "五行动态" in d}
        # 金 in 酉运: capped at 相 (== 本命) but 力量 rose → a rise (headline cap-fix case).
        assert dy["乙酉"]["金"]["状态"] == "相" and dy["乙酉"]["金"]["本命"] == "相"
        assert dy["乙酉"]["金"]["变化"] in ("升", "大升")
        assert dy["戊寅"]["木"]["变化"] in ("升", "大升")   # 寅 wood decade lifts 木
        assert dy["壬午"]["火"]["变化"] in ("升", "大升")   # 午 fire decade lifts 火
        assert dy["庚辰"]["土"]["变化"] in ("升", "大升")   # 辰 earth decade lifts 土
        # Magnitude grading is meaningful: a 帝旺 wood decade is a decisive swing.
        assert dy["戊寅"]["木"]["变化"] == "大升"

    def test_ten_god_and_decade_base_fields(self, desmond_cycles):
        """十神 tags each element's life-domain for the DM (fixed per chart); 运基 (the
        decade level) is present on 流年 only, absent on 大运."""
        cycles, _ = desmond_cycles
        da_yun = cycles["大运"][2]["五行动态"]["五行"]
        for el, tg in _DESMOND_TEN_GODS.items():
            assert da_yun[el]["十神"] == tg
        assert all("运基" not in da_yun[el] for el in ELEMENTS)  # 大运 has no decade above it
        liu = cycles["大运"][4]["流年"][0]["五行动态"]["五行"]
        assert all(liu[el]["运基"] in _VALID_STATES for el in ELEMENTS)
        assert all(liu[el]["十神"] == _DESMOND_TEN_GODS[el] for el in ELEMENTS)

    def test_yong_shen_summary_and_element_tags(self, desmond_cycles):
        """The cycles response carries a chart-fixed 用神 anchor, and every cycle element
        is tagged with 喜忌 + 解读 consistent with it.

        Desmond is 弱: 戊 is 囚 in the 亥 water month, and his only 本气 roots are 丑 and 辰 —
        湿土, frozen solid in winter. They are present on the chart and inert in practice
        (墓库根，如物之入库，虽存而无力), which is exactly why 戊亥's 调候 is 甲丙: 丙 to thaw
        the ground, 甲 to break it open. 身弱 caused BY 寒湿.
        """
        cycles, _ = desmond_cycles
        ys = cycles["用神"]
        assert ys["强弱"] == "弱"
        assert ys["调候用神"] == ["甲", "丙"]            # 戊亥 climate gods
        assert ys["调候忌神"] == ["辛"]                  # …and what it must avoid
        assert "火" in ys["喜用"] and "土" in ys["喜用"]  # weak DM favours 印/比
        assert "水" in ys["忌"]                          # 财 burdens a weak DM
        assert "金" in ys["忌"]                          # 辛 — and the 调候忌 agrees
        for wx in self._iter_wu_xing(cycles):
            for el, v in wx["五行"].items():
                assert v["喜忌"] in ("喜", "忌", "平")
                assert v["解读"]                          # non-empty reading
                assert v["喜忌"] == ys["五行"][el]["综合"]  # cycle tag == chart verdict
        huo = cycles["大运"][1]["五行动态"]["五行"]["火"]
        assert huo["喜忌"] == "喜" and huo["十神"] == "印星"   # 丙 — a 调候用神
        jin = cycles["大运"][1]["五行动态"]["五行"]["金"]
        assert jin["喜忌"] == "忌" and jin["十神"] == "食伤"   # 辛 — the 调候忌
        shui = cycles["大运"][1]["五行动态"]["五行"]["水"]
        assert shui["喜忌"] == "忌" and shui["十神"] == "财星"

    def test_liu_nian_read_within_its_decade(self):
        """岁运并临 (Move 2): a 流年's 五行 is reclassified natal+大运+流年, so a year in the
        壬午 (fire) decade reads 火 warmer than birth (死). 本命 stays the birth anchor."""
        cycles, _ = calculate_cycles(**DESMOND, da_yun_index=5)  # 大运[5] = 壬午
        liu_nian = cycles["大运"][5]["流年"]
        assert liu_nian, "expected 流年 expanded for the 壬午 decade"
        # 本命 is always the birth state (火 死), regardless of the decade.
        assert all(ln["五行动态"]["五行"]["火"]["本命"] == "死" for ln in liu_nian)
        # But the displayed 状态 is decade-warmed: some year reads 火 above 死.
        assert any(
            STATE_ORDER.index(ln["五行动态"]["五行"]["火"]["状态"]) > STATE_ORDER.index("死")
            for ln in liu_nian
        )


# ── 用神 (调候 + 扶抑) ───────────────────────────────────────────────────────


class TestYongShen:
    def test_weak_earth_winter(self):
        """Desmond: 戊 in 亥 (winter), 弱. 调候用神 甲丙; 火(印)+土(比) 喜, 金水 忌."""
        ys = make_yong_shen("戊", "土", "亥", "弱")
        assert ys["调候用神"] == ["甲", "丙"]
        assert ys["调候喜五行"] == ["木", "火"]
        assert ys["五行"]["火"]["综合"] == "喜"   # 印 + 调候, both agree
        assert ys["五行"]["火"]["备注"] == "调候扶抑两宜"
        assert ys["五行"]["土"]["综合"] == "喜"   # 比劫 supports a weak DM
        assert ys["五行"]["水"]["综合"] == "忌"   # 财 exhausts a weak DM
        assert ys["五行"]["金"]["综合"] == "忌"   # 食伤 drains a weak DM

    def test_climate_over_fu_yi_conflict_is_flagged(self):
        """木(官杀) burdens a weak 戊 by 扶抑, but is a 调候用神 (甲疏土) → 综合 喜 with a
        权衡 note. The tension is surfaced, not silently dropped."""
        ys = make_yong_shen("戊", "土", "亥", "弱")
        mu = ys["五行"]["木"]
        assert mu["扶抑"] == "忌" and mu["调候"] is True
        assert mu["综合"] == "喜"
        assert "权衡" in mu["备注"]

    def test_strong_dm_flips_fu_yi(self):
        """扶抑 inverts for a strong DM: 印/比 become 忌, 财/官/食 become 喜."""
        ys = make_yong_shen("甲", "木", "寅", "旺")
        assert ys["五行"]["水"]["扶抑"] == "忌"   # 印 for strong 木
        assert ys["五行"]["木"]["扶抑"] == "忌"   # 比劫 for strong 木
        assert ys["五行"]["土"]["扶抑"] == "喜"   # 财 for strong 木
        assert ys["五行"]["金"]["扶抑"] == "喜"   # 官杀 for strong 木

    def test_zhong_he_is_neutral(self):
        """中和 → no 扶抑 preference; only 调候用神 elements come out 喜."""
        ys = make_yong_shen("戊", "土", "亥", "中和")
        assert ys["五行"]["土"]["扶抑"] == "平"
        assert ys["五行"]["水"]["综合"] == "平"   # not a 调候用神, 扶抑 neutral
        assert ys["五行"]["火"]["综合"] == "喜"   # 调候用神 still 喜


# ── 1×4 interaction engine (hand-built fixtures) ────────────────────────────


class TestCycleInteractions:
    def test_liu_chong(self):
        ctx = make_ctx(("甲", "丙", "戊", "庚"), ("子", "寅", "巳", "申"))
        result = get_cycle_interactions("癸", "亥", ctx)
        chong = find(result, "六冲")
        assert len(chong) == 1
        assert chong[0]["组合明细"] == {"大运": "亥", "日柱": "巳"}
        assert chong[0]["距离"] == "紧贴"

    def test_liu_he_hua_vs_ban(self):
        # month 寅 (spring): 卯戌合火 → 火 is 相 in spring → 合化
        ctx = make_ctx(("甲", "丙", "戊", "庚"), ("子", "寅", "戌", "申"))
        he = find(get_cycle_interactions("乙", "卯", ctx), "六合")
        assert he and he[0]["形态"] == "合化"
        # month 申 (autumn): 火 is 囚 → 合绊
        ctx2 = make_ctx(("甲", "丙", "戊", "庚"), ("子", "申", "戌", "申"))
        he2 = find(get_cycle_interactions("乙", "卯", ctx2), "六合")
        assert he2 and he2[0]["形态"] == "合绊"

    def test_san_he_frame_completion_and_dedup(self):
        # natal has 申(year) 申(hour) 子(day); cycle 辰 completes 申子辰 — ONE frame,
        # 组合明细 listing every contributing pillar including the duplicate 申.
        ctx = make_ctx(("甲", "丙", "戊", "庚"), ("申", "寅", "子", "申"))
        frames = find(get_cycle_interactions("壬", "辰", ctx), "三合")
        assert len(frames) == 1
        assert frames[0]["元素"] == "水"
        assert frames[0]["子类型"] == "引动成局"
        assert set(frames[0]["组合明细"]) == {"大运", "年柱", "日柱", "时柱"}

    def test_san_he_reinforcement_when_natal_complete(self):
        # 申子辰 fully natal; cycle 子 duplicates a member → 增力, not formation
        ctx = make_ctx(("甲", "丙", "戊", "庚"), ("申", "子", "辰", "酉"))
        frames = find(get_cycle_interactions("壬", "子", ctx), "三合")
        assert len(frames) == 1
        assert frames[0]["子类型"] == "增力"

    def test_ban_he_lists_all_duplicate_partners(self):
        # natal 子 at 年柱(0) AND 日柱(2); cycle 申 → 申子 半合 (cardinal 子).
        # One item, but 组合明细 must list BOTH 子 pillars and _natal must set
        # 日柱特殊 — not collapse to the first-encountered 年柱.
        ctx = make_ctx(("甲", "丙", "戊", "庚"), ("子", "卯", "子", "巳"))
        ban_he = find(get_cycle_interactions("庚", "申", ctx), "半合")
        assert len(ban_he) == 1
        item = ban_he[0]
        assert item["组合明细"] == {"大运": "申", "年柱": "子", "日柱": "子"}
        assert item["日柱特殊"] is True
        assert item["缺失支"] == "辰"

    def test_can_hui_requires_cardinal(self):
        # cycle 卯 (East cardinal) + natal 辰, no 寅ANY → 残会 East
        ctx = make_ctx(("甲", "丙", "戊", "庚"), ("子", "午", "辰", "申"))
        can_hui = find(get_cycle_interactions("乙", "卯", ctx), "残会")
        assert can_hui and can_hui[0]["方位"] == "东" and can_hui[0]["缺失支"] == "寅"
        # non-cardinal pair (辰 + 寅 without 卯) would be a virtual arch — skipped
        ctx2 = make_ctx(("甲", "丙", "戊", "庚"), ("子", "午", "寅", "申"))
        assert not find(get_cycle_interactions("丙", "辰", ctx2), "残会")

    def test_gan_zhi_tou_he_both_directions(self):
        # (a) cycle stem 甲 reaches hidden 己 inside natal 丑 (本气) → 引动
        ctx = make_ctx(("庚", "丙", "戊", "己"), ("丑", "午", "子", "戌"))
        tou_he = find(get_cycle_interactions("甲", "寅", ctx), "干支透合")
        outbound = [t for t in tou_he if t.get("形态") == "岁运引动"]
        assert outbound and outbound[0]["藏干详情"]["藏干"] == "己"
        assert outbound[0]["藏干详情"]["藏干十神"] == "劫财"  # 己 vs DM 戊
        # (b) natal hour stem 己 reaches hidden 甲 inside cycle branch 寅 (本气)
        inbound = [t for t in tou_he if t.get("形态") == "命局引动"]
        assert any(t["藏干详情"]["藏干"] == "甲" for t in inbound)

    def test_san_xing_full_trio_upgrade(self):
        # natal 寅+巳 present; cycle 申 completes 寅巳申 无恩之刑 → 三刑全
        ctx = make_ctx(("甲", "丙", "戊", "庚"), ("寅", "巳", "子", "酉"))
        xing = find(get_cycle_interactions("庚", "申", ctx), "无恩之刑")
        assert xing and all(x["形态"] == "三刑全" for x in xing)

    def test_fan_yin_dominance(self):
        # cycle 庚申 vs natal 甲寅 pillar: 天克地冲 whole-pillar 反吟.
        # The 反吟 pillar's other interactions are capped; 六冲 on that pillar
        # is NOT separately registered (subsumed by 反吟).
        ctx = make_ctx(("甲", "丙", "戊", "壬"), ("寅", "午", "子", "戌"))
        result = get_cycle_interactions("庚", "申", ctx)
        fan_yin = find(result, "反吟")
        assert len(fan_yin) == 1 and fan_yin[0]["强度"] == "强势主流"
        assert not any(
            "年柱" in it["组合明细"] for it in find(result, "六冲")
        )
        # 暗合? none here — instead check a capped co-resident interaction if present
        for it in result["柱位动态"]:
            if it["类型"] in ("反吟", "伏吟"):
                continue
            if "年柱" in it["组合明细"]:
                assert it["强度"] in ("中等衰减", "大幅衰减", "消融吸收")

    def test_fan_yin_dampened_by_completed_frame(self):
        # cycle 庚辰 completes 申子辰 with natal 申(月)+子(日) AND forms a 反吟 vs
        # natal 年柱 甲戌 (庚克甲 + 辰冲戌). The cycle branch is locked into the
        # water bureau, so the 反吟 takes the natal table row
        # (STRUCTURAL_三合, 天克地冲) via the 反吟→天克地冲 alias → 中等衰减.
        ctx = make_ctx(("甲", "丙", "戊", "庚"), ("戌", "申", "子", "巳"))
        result = get_cycle_interactions("庚", "辰", ctx)
        assert find(result, "三合")
        fan_yin = find(result, "反吟")
        assert len(fan_yin) == 1
        assert fan_yin[0]["强度"] == "中等衰减"
        assert "三合" in fan_yin[0]["备注"]

    def test_fu_yin_whole_pillar(self):
        # (natal deliberately holds no completable frame with 寅 — a completed
        # 三合/三会 would dampen the 伏吟 via the natal priority table)
        ctx = make_ctx(("甲", "丙", "戊", "壬"), ("寅", "申", "子", "辰"))
        result = get_cycle_interactions("甲", "寅", ctx)
        fu_yin = find(result, "伏吟")
        assert len(fu_yin) == 1 and fu_yin[0]["强度"] == "强势主流"
        # branch-only repetition stays 伏吟(支)
        result2 = get_cycle_interactions("丙", "寅", ctx)
        assert find(result2, "伏吟(支)") and not find(result2, "伏吟")

    def test_tan_he_wang_chong(self):
        # cycle 卯: 六合 with natal 戌 (合化 in spring month 寅) + 六冲 with natal 酉
        # → 合化 claims the lock, 冲 absorbed (贪合忘冲)
        ctx = make_ctx(("甲", "丙", "戊", "庚"), ("戌", "寅", "酉", "申"))
        result = get_cycle_interactions("乙", "卯", ctx)
        chong = find(result, "六冲")
        assert chong and chong[0]["强度"] == "消融吸收"
        assert "贪合忘冲" in chong[0]["备注"]

    def test_stem_lock_absorbs_clash(self):
        # cycle 癸: 合 natal 戊 (day) → its 克/冲 vs 丁 absorbed
        ctx = make_ctx(("丁", "丙", "戊", "庚"), ("丑", "午", "子", "申"))
        result = get_cycle_interactions("癸", "亥", ctx)
        assert find(result, "天干合")
        for it in find(result, "天干冲") + find(result, "天干克"):
            assert it["强度"] == "消融吸收"

    def test_rootless_stem_capped(self):
        # cycle 丙 with no 火 root anywhere (no 巳午寅戌未 hidden 丙/丁), and no
        # 辛 in the natal stems (丙辛合 would stem-lock the 克 first)
        ctx = make_ctx(("庚", "甲", "戊", "庚"), ("子", "丑", "子", "申"))
        result = get_cycle_interactions("丙", "子", ctx, cycle_stem_rooting="无根")
        ke = find(result, "天干克")
        assert ke
        for it in ke:
            assert it["强度"] in ("显著影响", "中等衰减", "大幅衰减")
            assert "无根" in it.get("备注", "")

    def test_void_downgrade_and_chong_kong_exception(self):
        # natal 日柱 void pair 戌亥; natal 月支 戌 is void.
        # cycle 卯 六合 natal 戌 → one-tier downgrade + remark;
        # cycle 辰 六冲 natal 戌 → 冲空填实 remark, NO downgrade.
        ctx = make_ctx(("甲", "丙", "戊", "庚"), ("子", "戌", "寅", "申"), day_void="戌亥")
        he = find(get_cycle_interactions("乙", "卯", ctx), "六合")
        assert he and he[0]["旬空涉及"] == ["月柱"]
        assert "旬空" in he[0]["备注"]
        # different natal for the 冲 — the first would let cycle 辰 complete 申子辰
        ctx2 = make_ctx(("甲", "丙", "戊", "庚"), ("午", "戌", "寅", "巳"), day_void="戌亥")
        chong = find(get_cycle_interactions("丙", "辰", ctx2), "六冲")
        assert chong and chong[0]["强度"] == "强势主流"
        assert "冲空填实" in chong[0]["备注"]


# ── 神煞 & determinism ──────────────────────────────────────────────────────


class TestShenShaAndDeterminism:
    def test_cycle_shen_sha_classical_anchors(self, desmond_cycles):
        cycles, _ = desmond_cycles
        # 神煞 is a flat list of {名称, 来源, 解读}; anchor each star to the natal
        # pillar it is derived from.
        shen_sha = cycles["大运"][2]["神煞"]  # 乙酉
        pairs = {(e["名称"], e["来源"]) for e in shen_sha}
        assert ("将星", "年支") in pairs      # 年支丑 → 酉
        assert ("桃花", "日支") in pairs      # 日支辰 (申子辰) → 酉
        assert ("天德贵人", "月支") in pairs   # 月支亥 → 乙 (cycle stem)

    def test_deterministic_output(self):
        a, _ = calculate_cycles(**DESMOND, da_yun_index=1)
        b, _ = calculate_cycles(**DESMOND, da_yun_index=1)
        assert json.dumps(a, ensure_ascii=False, sort_keys=True) == json.dumps(
            b, ensure_ascii=False, sort_keys=True
        )


# ── guest-pillar 神煞 (Phase 0 divergence fixes + Phase 1/2 new stars) ────────


def _ss_names(entries: list) -> set:
    return {e["名称"] for e in entries}


def _ss_find(entries: list, name: str) -> dict | None:
    return next((e for e in entries if e["名称"] == name), None)


class TestGuestPillarShenSha:
    # ── Phase 1 — single-anchor stars ────────────────────────────────────────
    def test_yin_shen_year_anchor(self):
        # 年支 子 → 暗金的煞 target 巳 = 吟呻; guest branch 巳
        ss = get_cycle_shen_sha("甲", "巳", make_ctx(("甲", "丙", "戊", "庚"), ("子", "卯", "辰", "申")))
        e = _ss_find(ss, "吟呻")
        assert e is not None and e["来源"] == "年支"

    def test_jian_feng_sha(self):
        # 甲子年 → 旬首 子 → 剑锋 (辰, 戌); guest branch 辰
        ss = get_cycle_shen_sha("丙", "辰", make_ctx(("甲", "丙", "戊", "庚"), ("子", "卯", "午", "申")))
        assert "剑锋煞" in _ss_names(ss)

    def test_zhen_ci_guan_day_stem(self):
        # 日干 甲 → 真词馆 target 庚寅; guest 干支 庚寅
        ss = get_cycle_shen_sha("庚", "寅", make_ctx(("乙", "丙", "甲", "庚"), ("子", "卯", "午", "申")))
        e = _ss_find(ss, "真词馆")
        assert e is not None and e["来源"] == "日干"

    # ── Phase 2 — set-based stars ────────────────────────────────────────────
    def test_san_qi_yin_dong_adjacency(self):
        # natal 年乙 月丙 (day/hour non-trio) + guest 丁 → 天上三奇 via [Y,M,G]
        ss = get_cycle_shen_sha("丁", "巳", make_ctx(("乙", "丙", "壬", "己"), ("子", "卯", "午", "申")))
        e = _ss_find(ss, "天上三奇")
        assert e is not None
        assert e["来源"] == "组合" and e["细节"] == "引动成局"
        assert e["组合明细"] == ["运柱", "年柱", "月柱"]

    def test_san_qi_zeng_li_when_natal_complete(self):
        # natal already 乙丙丁 in Y-M-D + guest 丁 → 增力
        ss = get_cycle_shen_sha("丁", "巳", make_ctx(("乙", "丙", "丁", "己"), ("子", "卯", "午", "申")))
        e = _ss_find(ss, "天上三奇")
        assert e is not None and e["细节"] == "增力"

    def test_san_qi_scattered_does_not_fire(self):
        # natal 年辛 日癸 (壬 would need to slot between, but 月 blocks) + guest 壬 → NO fire
        ss = get_cycle_shen_sha("壬", "午", make_ctx(("辛", "戊", "癸", "己"), ("子", "卯", "午", "申")))
        assert "人间三奇" not in _ss_names(ss)

    def test_zi_yi_sha_completion(self):
        # pair {戌, 巳}: natal 戌, guest 巳 → 自缢煞 引动成局
        ss = get_cycle_shen_sha("甲", "巳", make_ctx(("甲", "丙", "戊", "庚"), ("戌", "卯", "午", "申")))
        e = _ss_find(ss, "自缢煞")
        assert e is not None and e["来源"] == "四柱" and e["细节"] == "引动成局"
        assert "运柱" in e["组合明细"] and "年柱" in e["组合明细"]  # natal 戌 is the year pillar

    def test_tian_tu_sha_guest_as_hour(self):
        # natal day branch 亥, partner 丑; guest branch 丑 → 天屠煞 (guest as Hour)
        ss = get_cycle_shen_sha("甲", "丑", make_ctx(("甲", "丙", "戊", "庚"), ("子", "卯", "亥", "申")))
        e = _ss_find(ss, "天屠煞")
        assert e is not None and e["来源"] == "日支"
        assert e["组合明细"] == ["运柱", "日柱"]

    # ── Phase 0 — divergence-fix parity with natal ──────────────────────────
    def test_tian_luo_no_nayin_gate(self):
        # natal 戌 present (non-火命, na_yin empty), guest 亥 → 天罗 fires (branch-pair only)
        ss = get_cycle_shen_sha("甲", "亥", make_ctx(("甲", "丙", "戊", "庚"), ("戌", "卯", "午", "申")))
        e = _ss_find(ss, "天罗")
        assert e is not None and e["来源"] == "四柱"

    def test_gou_jiao_gender_swap(self):
        from apps.backend.astronomer_logic.natal_shen_sha import year_earthly_branches_shens
        qian = year_earthly_branches_shens["勾绞煞"]["子"]  # 前三辰 of year 子
        # 甲子 year = 阳年; guest branch == qian
        male = get_cycle_shen_sha("甲", qian, make_ctx(("甲", "丙", "戊", "庚"), ("子", "卯", "午", "申"), gender=1))
        female = get_cycle_shen_sha("甲", qian, make_ctx(("甲", "丙", "戊", "庚"), ("子", "卯", "午", "申"), gender=0))
        assert "勾煞" in _ss_names(male)   # 阳男 → 前三辰 = 勾煞
        assert "绞煞" in _ss_names(female)  # 阳女 → 前三辰 = 绞煞
        assert "勾绞煞" not in _ss_names(male)  # merged name never emitted

    def test_tong_zi_sha_spring_case(self):
        # 月支 卯 → 春; targets {寅, 子}; guest branch 寅 → 童子煞 (节气)
        ss = get_cycle_shen_sha("甲", "寅", make_ctx(("甲", "丙", "戊", "庚"), ("午", "卯", "巳", "申")))
        e = _ss_find(ss, "童子煞")
        assert e is not None and e["来源"] == "节气"

    def test_de_xiu_requires_conjunction(self):
        # 月支 寅: 德=丙丁, 秀=(戊,癸). Only 德 (guest 丙), no 秀 → must NOT fire.
        only_de = get_cycle_shen_sha("丙", "午", make_ctx(("甲", "甲", "乙", "庚"), ("子", "寅", "午", "申")))
        assert "德秀贵人" not in _ss_names(only_de)
        # 德 (guest 丙) + 秀 (natal 戊 & 癸) → fires
        both = get_cycle_shen_sha("丙", "午", make_ctx(("戊", "甲", "癸", "乙"), ("子", "寅", "午", "申")))
        assert "德秀贵人" in _ss_names(both)

    def test_ming_zi_lu_branch_specific_name(self):
        # guest 甲寅 → 寅命自禄 (source 自柱), not the merged "自禄"
        ss = get_cycle_shen_sha("甲", "寅", make_ctx(("乙", "丙", "戊", "庚"), ("子", "卯", "午", "申")))
        e = _ss_find(ss, "寅命自禄")
        assert e is not None and e["来源"] == "自柱"
        assert "自禄" not in _ss_names(ss)

    # ── Regression: every emitted (名称, 来源) resolves to an interpretation ──
    def test_all_emitted_stars_resolve_interpretation(self):
        from lunar_python import Solar

        from apps.backend.astronomer_logic.cycles.cycle_interpretation_shen_sha import (
            get_cycle_shen_sha_interpretations,
        )
        from apps.backend.orchestrator.cycles_orchestrator import _build_context

        gan, zhi = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
        jiazi = [gan[i % 10] + zhi[i % 12] for i in range(60)]
        for y in (1972, 1985, 1990, 2000):
            for g in (0, 1):
                bazi = Solar.fromYmdHms(y, 6, 15, 12, 0, 0).getLunar().getEightChar()
                ctx = _build_context(bazi, g)
                for gz in jiazi:
                    enriched = get_cycle_shen_sha_interpretations(
                        get_cycle_shen_sha(gz[0], gz[1], ctx), "流年"
                    )
                    for e in enriched:
                        assert e["解读"] != "无", f"{e['名称']}/{e['来源']} unresolved"


# ============================================================================
# 运势 — the per-decade/per-year 喜运/平运/忌运 headline (from the 金不换 方位表)
# ============================================================================
class TestYunShi:
    """The 运势 verdict + the CLIMATE_DATA branch lists it trusts.

    The 方位表 (大运喜/大运忌) is hand-curated per 日干+月支 and is the ONLY source of a
    holistic per-period verdict; the 五行动态 breakdown is per-element and cannot give one.
    These tests lock the data's purity (a stem or a stray concept leaking into a branch
    list would silently mis-rate a decade) and the rule that consumes it.
    """

    BRANCHES = frozenset("子丑寅卯辰巳午未申酉戌亥")

    # ── Data invariants over all 120 CLIMATE_DATA entries ────────────────────
    def test_da_yun_lists_are_pure_branches(self):
        from apps.backend.data.climate_data import CLIMATE_DATA

        for key, entry in CLIMATE_DATA.items():
            for field in ("大运喜", "大运忌"):
                vals = entry.get(field)
                assert isinstance(vals, list), f"{key}.{field} is not a list"
                for v in vals:
                    assert v in self.BRANCHES, f"{key}.{field} has non-branch {v!r}"
                assert len(vals) == len(set(vals)), f"{key}.{field} has duplicates"

    def test_no_branch_is_both_favorable_and_unfavorable(self):
        """A branch in BOTH lists makes the verdict order-dependent — never allowed."""
        from apps.backend.data.climate_data import CLIMATE_DATA

        for key, entry in CLIMATE_DATA.items():
            both = set(entry.get("大运喜", [])) & set(entry.get("大运忌", []))
            assert not both, f"{key}: {sorted(both)} in both 大运喜 and 大运忌"

    # ── get_yong_shen passes the curated lists through ───────────────────────
    def test_yong_shen_exposes_da_yun_branches(self):
        # Desmond: 戊 day master, 亥 month → 南方火运 warms a cold winter 戊.
        ys = make_yong_shen("戊", "土", "亥", "弱")
        assert ys["大运喜"] == ["巳", "午", "未"]
        assert ys["大运忌"] == ["酉", "卯", "辰"]

    # ── The verdict rule ─────────────────────────────────────────────────────
    def test_rating_follows_the_curated_table(self):
        from apps.backend.astronomer_logic.cycles.cycle_wu_xing import get_cycle_yun_shi

        ys = make_yong_shen("戊", "土", "亥", "弱")
        assert get_cycle_yun_shi("午", ys)["评级"] == "喜运"   # ∈ 大运喜
        assert get_cycle_yun_shi("卯", ys)["评级"] == "忌运"   # ∈ 大运忌
        assert get_cycle_yun_shi("申", ys)["评级"] == "平运"   # in neither
        assert get_cycle_yun_shi("午", ys)["来源"] == "金不换"

    def test_uncurated_chart_falls_back_to_yong_shen_elements(self):
        """丁巳 has BOTH lists empty — the verdict must degrade to the branch's 本气 五行,
        not silently rate every decade 平运."""
        from apps.backend.astronomer_logic.cycles.cycle_wu_xing import get_cycle_yun_shi

        ys = make_yong_shen("丁", "火", "巳", "旺")
        assert ys["大运喜"] == [] and ys["大运忌"] == []
        # 丁巳 调候用神 = 甲(木)/庚(金); 日主旺 so 比劫(火) is the one 忌 element.
        assert get_cycle_yun_shi("子", ys)["评级"] == "喜运"   # 子 本气 水 = 官杀 → 喜
        assert get_cycle_yun_shi("午", ys)["评级"] == "忌运"   # 午 本气 火 = 比劫 → 忌
        assert get_cycle_yun_shi("子", ys)["来源"] == "用神五行"
        # 调候 leads 扶抑: 木 is 印星 (扶抑忌 for a 旺 DM) but a 调候用神, so it rates 喜运.
        # The fallback must inherit that resolution rather than re-deriving from 扶抑 alone.
        assert ys["五行"]["木"]["扶抑"] == "忌" and ys["五行"]["木"]["综合"] == "喜"
        assert get_cycle_yun_shi("卯", ys)["评级"] == "喜运"

    def test_cong_ge_conditional_clause_is_not_encoded_as_a_direction(self):
        """癸午's source 大运 clause ('喜从火财 忌申(无根夭)') is 从格-conditional, NOT a
        方位 judgment — it holds only if the 癸 is rootless enough to follow the fire.

        This table is keyed on 日干+月支 alone and the engine has no 从格 detection, so the
        condition is inexpressible here. Encoding it would rate the chart's own 用神 (庚金,
        which the 经典 calls 必须庚辛为生身之本) as 忌运 — exactly backwards. Both lists must
        stay empty so the per-chart 用神 fallback decides.
        """
        from apps.backend.astronomer_logic.cycles.cycle_wu_xing import get_cycle_yun_shi
        from apps.backend.data.climate_data import CLIMATE_DATA

        assert CLIMATE_DATA["癸午"]["大运喜"] == []
        assert CLIMATE_DATA["癸午"]["大运忌"] == []

        ys = make_yong_shen("癸", "水", "午", "弱")  # 五月癸水，至弱无根
        assert get_cycle_yun_shi("申", ys)["评级"] == "喜运"  # 庚金 印 — 生身之本
        assert get_cycle_yun_shi("午", ys)["评级"] == "忌运"  # 丁火 — 调候忌丁
        assert get_cycle_yun_shi("申", ys)["来源"] == "用神五行"

    # ── End-to-end through the orchestrator ──────────────────────────────────
    def test_desmond_fire_decades_are_xi_yun(self, desmond_cycles):
        """癸未/壬午/辛巳 (37-66) are Desmond's 南方火运 — the classically best decades."""
        cycles, _ = desmond_cycles
        by_gan_zhi = {d["干支"]: d for d in cycles["大运"] if d["序号"] != 0}
        for gz in ("癸未", "壬午", "辛巳"):
            assert by_gan_zhi[gz]["运势"]["评级"] == "喜运", gz
        for gz in ("乙酉", "庚辰", "己卯"):
            assert by_gan_zhi[gz]["运势"]["评级"] == "忌运", gz
        for gz in ("丙戌", "甲申", "戊寅"):
            assert by_gan_zhi[gz]["运势"]["评级"] == "平运", gz

    def test_every_analysed_pillar_carries_a_verdict(self, desmond_cycles):
        """Every 大运 (bar the pre-运 stub) and every 流年 gets a well-formed 运势."""
        cycles, _ = desmond_cycles
        ratings = {"喜运", "平运", "忌运"}
        seen = 0
        for d in cycles["大运"]:
            if d["序号"] == 0:
                assert "运势" not in d  # pre-运 stub has no pillar to rate
                continue
            assert d["运势"]["评级"] in ratings
            assert d["运势"]["依据"] and d["运势"]["来源"]
            seen += 1
            for ln in d["流年"]:
                assert ln["运势"]["评级"] in ratings
                seen += 1
        assert seen > 9  # 9 decades + the expanded decade's 流年


# ============================================================================
# 格局 — chart structure (正格 / 从格 / 专旺格 / 化气格) and the 喜忌 inversion
# ============================================================================
class TestGeJu:
    """格局 decides whether 喜忌 come from 扶抑+调候 or from a surrendered structure.

    The stakes: for a 从格, 扶抑 says 印比 are 喜 (support the weak DM) when they are in
    fact 忌 (they 破格). Getting 格局 wrong inverts the entire reading of a chart, so these
    tests pin both the detection gate and the inversion.
    """

    # 从财 chart found in the real-chart sweep: 甲寅 丁卯 辛酉 丙申.
    # 辛 sits on its own 禄 (酉) — but 卯酉冲 AND 寅申冲 clash BOTH metal roots away, in a
    # 卯 (财) month surrounded by 甲寅木財 / 丙丁火官杀. The DM has nothing left → 弃命从财.
    CONG_CAI = dict(
        birth_datetime=datetime(1974, 3, 21, 15, 44, 0),
        latitude=1.3253, longitude=103.808053, gender=0,
        use_solar_time_correction=True,
    )

    @pytest.fixture(scope="class")
    def cong_cai_chart(self):
        chart, _ = calculate_natal_chart(**self.CONG_CAI)
        return chart

    def test_desmond_is_zheng_ge(self):
        """The reference subject is an ordinary rooted chart — must NOT be swept into 从格."""
        chart, _ = calculate_natal_chart(**DESMOND)
        assert chart["用神"]["格局"] == "正格"
        assert chart["用神"]["格局详情"]["真假"] is None

    def test_cong_cai_detected_and_inverted(self, cong_cai_chart):
        ys = cong_cai_chart["用神"]
        assert ys["格局"] == "从财格"
        assert ys["格局详情"]["真假"] == "真从"
        assert ys["格局详情"]["主导"] == "财星"
        # 辛(金) DM: 印星=土, 比劫=金 — both 忌 because they revive a surrendered DM.
        assert ys["五行"]["土"]["综合"] == "忌"   # 印星 破格
        assert ys["五行"]["金"]["综合"] == "忌"   # 比劫 破格
        # …and the followed force + its feeders are 喜.
        assert ys["五行"]["木"]["综合"] == "喜"   # 财星 (followed)
        assert ys["五行"]["火"]["综合"] == "喜"   # 官杀 (财生官)

    def test_inversion_is_recorded_against_fu_yi(self, cong_cai_chart):
        """扶抑 would say 印比 are 喜 for this 极弱 DM. The structure overrides it, and the
        override is surfaced in 备注 so a reader can audit why."""
        ys = cong_cai_chart["用神"]
        earth = ys["五行"]["土"]  # 印星
        assert earth["扶抑"] == "喜"      # what 扶抑 alone would have concluded
        assert earth["综合"] == "忌"      # what the structure concludes
        assert "破格" in earth["备注"]
        assert earth["调候"] is False     # 从格 does not take 调候

    def test_strength_is_not_structure(self):
        """极弱 does NOT imply 从格 — a weak DM with 印比 to lean on stays 正格.

        This is the gate that the three foundations alone get wrong: 得地/得势 cannot see
        印星 buried in the branches, so without the 全局无生扶 check this chart would be
        mis-swept into 从格 and have its 喜忌 inverted.
        """
        from apps.backend.astronomer_logic.ge_ju import detect_ge_ju

        dm_data = {
            "日主": {
                "强弱": "极弱",
                "得令": {"状态": "死", "分数": 0.0},
                "得地": {"通根": "无根", "分数": 0.0},
                "得势": {"得势层级": "无", "分数": 0.0},
            }
        }
        five = {el: {"力量": 0.0, "状态": "死"} for el in ELEMENTS}
        no_ix = {"作用": {"柱位动态": []}}

        # 甲(木) DM. 印星 = 水. Strong 水 in the branches → the DM can be revived → 正格.
        five["水"]["力量"] = 6.0
        five["金"]["力量"] = 3.0   # 官杀
        assert detect_ge_ju(dm_data, five, no_ix, "木")["格局"] == "正格"

        # Same foundations, but strip the 印 away → nothing can revive it → 从杀格.
        five["水"]["力量"] = 0.0
        assert detect_ge_ju(dm_data, five, no_ix, "木")["格局"] == "从杀格"

    def test_cong_ge_rate_is_classically_rare(self):
        """Calibration guard. 从格 is rare; a detector that fires broadly would invert
        ordinary charts. Sweeping real charts, non-正格 must stay in single digits.

        (The three-foundation gate alone fired on 20% of charts — this guard is what
        would have caught that.)
        """
        import random

        random.seed(3)
        start = datetime(1950, 1, 1)
        n = 400
        non_zheng = 0
        for _ in range(n):
            dt = start + timedelta(
                days=random.randint(0, 365 * 75), hours=random.randint(0, 23)
            )
            chart, _ = calculate_natal_chart(
                dt, 1.3253, 103.808053, gender=random.randint(0, 1)
            )
            if chart["用神"]["格局"] != "正格":
                non_zheng += 1
        rate = non_zheng / n
        assert 0.005 < rate < 0.10, f"非正格 rate {rate:.1%} — detector mis-calibrated"

    def test_cong_ge_bypasses_the_zheng_ge_authored_table(self, cong_cai_chart):
        """A 从格 must NOT be judged by the 金不换 方位表 — it is authored for 正格 charts,
        where the DM stands and must be balanced. This is the generalisation of the 癸午 bug."""
        from apps.backend.astronomer_logic.cycles.cycle_wu_xing import get_cycle_yun_shi

        ys = cong_cai_chart["用神"]
        v = get_cycle_yun_shi("寅", ys)      # 寅 本气 木 = 财星 = the followed force
        assert v["来源"] == "从格用神"        # not "金不换"
        assert v["评级"] == "喜运"
        v = get_cycle_yun_shi("酉", ys)      # 酉 本气 金 = 比劫 → 破格
        assert v["评级"] == "忌运"

    def test_pattern_mapping_covers_every_detectable_cong_ge(self):
        """Any 从/专旺 格局 the detector can emit must have a 喜忌 spec, or it would
        silently return empty 喜用/忌 and rate every cycle 平运."""
        from apps.backend.astronomer_logic.ge_ju import (
            _CONG_BY_DOMINANT,
            PATTERN_MAPPING,
        )

        for name in _CONG_BY_DOMINANT.values():
            assert name in PATTERN_MAPPING
        assert "从势格" in PATTERN_MAPPING and "专旺格" in PATTERN_MAPPING
        for name, spec in PATTERN_MAPPING.items():
            assert spec["喜用"] and spec["忌"], name
            assert not (set(spec["喜用"]) & set(spec["忌"])), f"{name}: 喜忌 overlap"


# ============================================================================
# 五行生克 primitives — single source of truth
# ============================================================================
class TestWuXingRelationsAreShared:
    """生/克 and element_ten_god_class must exist ONCE, in wu_xing_relations.

    They were previously copy-pasted across day_master_strength / ge_ju / cycle_wu_xing.
    生克 underpins 强弱, 格局 and 用神 alike, so a fix applied to one copy while the others
    drift is a cross-layer disagreement bug — the same shape as the 癸午 inversion. These
    tests fail the moment someone re-declares them locally.
    """

    def test_all_consumers_share_one_object(self):
        from apps.backend.astronomer_logic import (
            day_master_strength,
            ge_ju,
            wu_xing_relations,
            yong_shen,
        )
        from apps.backend.astronomer_logic.cycles import cycle_wu_xing

        assert wu_xing_relations.GENERATES is day_master_strength._GENERATES
        assert wu_xing_relations.GENERATES is ge_ju._GENERATES
        assert wu_xing_relations.CONTROLS is day_master_strength._CONTROLS
        assert wu_xing_relations.CONTROLS is ge_ju._CONTROLS
        for mod in (ge_ju, yong_shen, cycle_wu_xing):
            assert mod.element_ten_god_class is wu_xing_relations.element_ten_god_class

    def test_no_module_redeclares_the_primitives(self):
        """Guard the source text — an `is` check cannot catch a fresh local copy in a
        module this test doesn't import.

        Matches on CONTENT, not on name. Name-matching is what let _NA_YIN_SHENG and
        _WU_XING_SHENG/_WU_XING_KE hide in plain sight: they were the same two maps wearing
        different labels. Any dict literal mapping 木→火 (生) or 木→土 (克) is a re-declaration
        no matter what it is called.
        """
        import pathlib
        import re

        root = pathlib.Path("apps/backend/astronomer_logic")
        owner = root / "wu_xing_relations.py"
        # a 生 or 克 map, however named, opens with 木→火 or 木→土 (whitespace/newline tolerant)
        redeclared = re.compile(r'\{\s*"木"\s*:\s*"[火土]"')
        also_named = re.compile(r"^def _?element_ten_god_class", re.M)

        offenders = []
        for path in root.rglob("*.py"):
            if path == owner:
                continue
            src = path.read_text(encoding="utf-8")
            if redeclared.search(src) or also_named.search(src):
                offenders.append(path.as_posix())
        assert not offenders, (
            f"{offenders} re-declare 五行生克 — import GENERATES/CONTROLS from "
            f"wu_xing_relations instead"
        )

    def test_relations_are_a_consistent_cycle(self):
        """生 and 克 must each form a single 5-cycle over the elements."""
        from apps.backend.astronomer_logic.wu_xing_relations import (
            CONTROLS,
            ELEMENTS,
            GENERATES,
        )

        for m in (GENERATES, CONTROLS):
            assert set(m) == set(ELEMENTS)
            assert set(m.values()) == set(ELEMENTS)   # bijection → one cycle, no orphans
            assert all(m[e] != e for e in ELEMENTS)   # nothing generates/controls itself
        # 克 skips exactly one step of the 生 cycle: X 克 (the element X's child generates)
        for e in ELEMENTS:
            assert CONTROLS[e] == GENERATES[GENERATES[e]]


class TestYongShenKeysAreUnambiguous:
    """用神.喜用 (ELEMENTS) and 格局详情.喜用十神 (TEN-GOD CATEGORIES) are different types.

    They were briefly both called 喜用 — a trap: a consumer reaching for 格局详情.喜用 gets
    [] on the ~95% of charts that are 正格, and ten-god strings on the rest, while the real
    answer lives at 用神.喜用. The names now carry the type.
    """

    def test_element_and_ten_god_keys_do_not_collide(self):
        chart, _ = calculate_natal_chart(**TestGeJu.CONG_CAI)
        ys = chart["用神"]
        gj = ys["格局详情"]

        # the outer answer is ELEMENTS…
        assert set(ys["喜用"]) <= set(ELEMENTS)
        assert set(ys["忌"]) <= set(ELEMENTS)
        # …the structure detail is TEN-GOD CATEGORIES, under distinct keys.
        categories = {"比劫", "印星", "食伤", "财星", "官杀"}
        assert set(gj["喜用十神"]) <= categories and gj["喜用十神"]
        assert set(gj["忌十神"]) <= categories and gj["忌十神"]
        # the ambiguous names must be gone from the detail block entirely
        assert "喜用" not in gj and "忌" not in gj

    def test_yong_shen_is_self_contained_on_cycles(self):
        """/cycles carries NO 日主 block, so 用神.强弱 is the only carrier of the strength
        there — it is a projection, not a redundant copy, and must not be removed."""
        cycles, _ = calculate_cycles(**DESMOND)
        assert "日主" not in cycles
        assert cycles["用神"]["强弱"] in {"极旺", "旺", "中和", "弱", "极弱"}
        natal, _ = calculate_natal_chart(**DESMOND)
        # and it must agree with the natal 日主 block it was projected from
        assert cycles["用神"]["强弱"] == natal["日主"]["强弱"]


# ============================================================================
# 燥土 / 湿土 — root QUALITY for an earth day master
# ============================================================================
class TestWetEarthRooting:
    """辰戌丑未 are not equivalent roots for a 土 day master.

    未/戌 carry 丁火 — 燥土, warm and dry, sound footing.
    辰/丑 carry 癸水 — 湿土; in a winter month, 冻土, frozen solid.

    The weight table scored all four at a full 本气 0.6, so a 戊 standing on frozen mud in a
    water month got MAX 得地 — a foundation the classics say cannot hold him up
    (墓库根，如物之入库，虽存而无力). That is 身弱 caused BY 寒湿: the two are orthogonal axes,
    and this is where they meet. It is also self-confirming — 戊亥's 调候 is 甲丙 precisely
    because the ground must be thawed (丙) and broken open (甲) before it can bear weight.
    """

    def test_frozen_wet_earth_is_discounted(self):
        from apps.backend.astronomer_logic.day_master_strength import earth_root_factor

        # 戊 in a winter month, rooting in 辰/丑 → 冻土
        assert earth_root_factor("丑", "土", "亥") == 0.5
        assert earth_root_factor("辰", "土", "子") == 0.5
        # 湿土 outside winter — wet, but not frozen
        assert earth_root_factor("辰", "土", "午") == 0.7

    def test_dry_earth_is_untouched(self):
        """未/戌 are 燥土 — a sound root. The rule must not become a blanket earth penalty."""
        from apps.backend.astronomer_logic.day_master_strength import earth_root_factor

        for month in ("亥", "子", "丑", "午", "寅"):
            assert earth_root_factor("未", "土", month) == 1.0
            assert earth_root_factor("戌", "土", month) == 1.0

    def test_non_earth_day_masters_are_untouched(self):
        """Critical: for 木/火/金/水 the 墓库 root is ALREADY scored 0.1 (余气) in
        BRANCH_HIDDEN_STEM_ROOTING — "stored qi is weak" is baked into the table. Applying a
        discount here as well would double-penalise them."""
        from apps.backend.astronomer_logic.day_master_strength import (
            BRANCH_HIDDEN_STEM_ROOTING,
            earth_root_factor,
            get_stem_element,
        )

        for dm_elem in ("木", "火", "金", "水"):
            for branch in ("辰", "戌", "丑", "未"):
                assert earth_root_factor(branch, dm_elem, "亥") == 1.0

        # …and confirm the premise: a non-earth DM's root in its own 库 really is 余气-weight.
        for elem, ku in {"木": "未", "火": "戌", "金": "丑", "水": "辰"}.items():
            w = sum(w for s, w in BRANCH_HIDDEN_STEM_ROOTING[ku] if get_stem_element(s) == elem)
            assert w == 0.1, f"{elem} in {ku} should be 余气 weight, got {w}"

    def test_desmond_is_weak_from_frozen_roots(self):
        """The reference subject: 戊 in 亥月 whose only 本气 roots are 丑 and 辰."""
        chart, _ = calculate_natal_chart(**DESMOND)
        dm = chart["日主"]
        assert dm["五行"] == "土"
        assert dm["得地"]["通根"] == "中根"   # not 深根 — the frozen roots are discounted
        assert dm["强弱"] == "弱"
        # and the 用神 lands where the classics put it: 火土 to support, 甲丙 to thaw/break
        ys = chart["用神"]
        assert "火" in ys["喜用"] and "土" in ys["喜用"]
        assert ys["调候用神"] == ["甲", "丙"]


# ============================================================================
# 化气格 — the 合化 partner is ABSORBED, not merely relabelled
# ============================================================================
class TestHuaQiGePartnerAbsorbed:
    """天干五合 merges BOTH stems into the 化神. The partner is not "a 伤官 that transformed";
    it is no longer a 伤官 at all.

    The bug: the partner's 五行 was rewritten to the 化神 while its 十神 was still looked up
    from the RAW char — so a pillar read 戊 / 五行=火 / 十神=伤官, and 伤官 is the EARTH
    reading of 戊. compute_de_shi meanwhile reclassifies 合化 stems by the NEW element and was
    already counting it as 火/supporting. Three layers, two answers.
    """

    # 丁卯 乙巳 癸未 戊午 — 戊癸合化火. 癸 is 无根 (no water in 卯/巳/未/午), 化神 火 holds the
    # 月令 (巳) and roots in 巳/午, no 争合 → 真化火格.
    HUA_HUO = dict(
        birth_datetime=datetime(1987, 6, 3, 12, 6, 0),
        latitude=1.3253, longitude=103.808053, gender=0,
        use_solar_time_correction=True,
    )

    @pytest.fixture(scope="class")
    def chart(self):
        c, _ = calculate_natal_chart(**self.HUA_HUO)
        return c

    def test_hua_qi_ge_detected(self, chart):
        assert chart["日主"]["五行"] == "火"          # 癸 水 → 化神 火
        assert chart["用神"]["格局"] == "化气格"
        assert chart["用神"]["格局详情"]["名称"] == "化火格"
        assert chart["用神"]["格局详情"]["真假"] == "真化"

    def test_absorbed_partner_reads_as_the_hua_shen(self, chart):
        """戊(阳土) absorbed into 火 → read as 丙(阳火) → vs 丁 day master = 劫财."""
        shi = chart["四柱实体"]["时柱"]["天干"]
        assert shi["天干"] == "戊"      # the raw char is unchanged…
        assert shi["五行"] == "火"      # …but it now carries 化神 qi
        assert shi["十神"] == "劫财"    # …and the ten god says so too (was 伤官)

    def test_every_stem_ten_god_agrees_with_its_element(self, chart):
        """The invariant the bug violated: a stem's 十神 must imply the 五行 next to it."""
        from apps.backend.astronomer_logic.wu_xing_relations import element_ten_god_class

        cat = {
            "比肩": "比劫", "劫财": "比劫", "正印": "印星", "偏印": "印星",
            "食神": "食伤", "伤官": "食伤", "正财": "财星", "偏财": "财星",
            "正官": "官杀", "七杀": "官杀", "偏官": "官杀", "日主": "比劫",
        }
        dm_elem = chart["日主"]["五行"]
        for p in ("年柱", "月柱", "日柱", "时柱"):
            t = chart["四柱实体"][p]["天干"]
            implied = cat[t["十神"]]
            actual = element_ten_god_class(t["五行"], dm_elem)
            assert implied == actual, f"{p} {t['天干']}: 十神={t['十神']} but 五行={t['五行']}"

    def test_absorbed_partner_can_never_be_tamed_or_tipped(self, chart):
        """Why no extra guard is needed in apply_qi_sha / apply_shi_shen_transformation.

        An absorbed partner is BY CONSTRUCTION the day master's own element, hence 比肩/劫财.
        It can therefore never match 七杀 or 食神 in _ten_god_occurrences — the single funnel
        both transformations use — so neither can act on a god the 化 has already consumed.
        A separate guard would be dead code; this test pins the reason.
        """
        shi = chart["四柱实体"]["时柱"]
        assert shi.get("化气格信息") is not None          # it IS an absorbed partner
        assert shi["天干"]["十神"] in ("比肩", "劫财")     # …so it is 比劫, never 七杀/食神
        assert "七杀化偏官" not in shi                     # never tamed
        assert "食神化伤官" not in shi                     # never tipped

    def test_de_shi_agrees_with_the_label(self, chart):
        """得势 already counted the absorbed 戊 as 火/supporting. The label now matches it."""
        assert chart["日主"]["得势"]["得势层级"] == "强"
        assert chart["日主"]["强弱"] == "极旺"   # 化火格 in 巳月 with 巳午未 fire

    def test_tiao_hou_indexed_on_the_effective_day_master(self, chart):
        """调候 is a CLIMATE concept — it must be read for the day master the chart HAS.

        癸 became 丁 (火). A 丁火 in 巳月 experiences summer very differently from a 癸水 in
        巳月, and the 经典 prose handed to the LLM must describe the former. The lookup was
        keyed on the RAW 癸 (row 癸巳: 喜辛 — "四月癸水，喜辛金为用"), describing a water day
        master that no longer exists.
        """
        ys = chart["用神"]
        assert ys["调候用神"] == ["甲", "庚"]        # 丁巳 row, not 癸巳's ["辛"]
        assert "丁火" in ys["经典"]["原则"]           # prose describes a FIRE day master

    def test_tiao_hou_is_flagged_not_in_force(self, chart):
        """调候适用 = False for 化气格 — and the flag is load-bearing, not decorative.

        Any chart in 巳月 fears more fire, so 调候忌五行 legitimately contains 火 — while 格局
        makes 火 the 化神 and 喜用. Both statements are true in their own frame. Without the
        flag, a consumer reading only the 调候 block would enforce the exact opposite of the
        chart's actual verdict.
        """
        ys = chart["用神"]
        assert ys["调候适用"] is False
        assert "火" in ys["调候忌五行"]      # the climate row says avoid fire…
        assert "火" in ys["喜用"]            # …the structure says fire IS the day master
        # the verdict follows the structure, not the climate
        assert ys["五行"]["火"]["综合"] == "喜"

    def test_zheng_ge_charts_keep_tiao_hou_in_force(self):
        """The flag must not silently disable 调候 on ordinary charts."""
        chart, _ = calculate_natal_chart(**DESMOND)
        ys = chart["用神"]
        assert ys["格局"] == "正格"
        assert ys["调候适用"] is True
        assert ys["调候用神"] == ["甲", "丙"]        # raw == effective on a 正格 chart


# ============================================================================
# 化气格 破格 — 原日主五行复起, and why 位置 (stem vs branch) decides it
# ============================================================================
class TestHuaQiGePoGe:
    """A 化气格 shatters two ways: 克化神, and 日主复根 (the DM regains a root in the element
    it USED to be). The second was listed in 破格 but never reflected in 忌五行.

    Across the ten 化气格 cases the old code was right in only two (where 原五行 happened to
    equal 克化神者). In four it rated 原五行 平 — though its ONLY function there is to revive
    the day master and break the 化. In two more it rated 原五行 喜 — because there the
    original element is ALSO the 生化神者 (辛化水: 金生水; 壬化木: 水生木).

    That last pair is not a contradiction. It is a STEM/BRANCH question:
        金 as a floating 天干 (庚/辛) → feeds the 化神        → genuinely 喜
        金 in a BRANCH (申/酉/丑)     → roots 辛, it reverts  → 破格
    An element-level 忌五行 cannot hold both. 位置 can.
    """

    @staticmethod
    def _hua_chart(dm_stem, partner, hua_element):
        from apps.backend.astronomer_logic.ge_ju import detect_ge_ju

        ix = {"作用": {"柱位动态": [{
            "类型": "天干合", "形态": "化气格",
            "组合明细": {"日柱": dm_stem, "时柱": partner},
            "合化条件": {"合化元素": hua_element},
        }]}}
        dmd = {"日主": {"强弱": "旺",
                        "得令": {"状态": "旺", "分数": 4.0},
                        "得地": {"通根": "深根", "分数": 4.0},
                        "得势": {"得势层级": "强", "分数": 4.0}}}
        five = {e: {"力量": 1.0} for e in ELEMENTS}
        return detect_ge_ju(dmd, five, ix, hua_element)

    def test_original_element_that_only_revives_the_dm_is_ji(self):
        """The 4 cases where 原五行 neither feeds nor attacks the 化神 — it was rated 平."""
        for dm, partner, hua, orig in [
            ("乙", "庚", "金", "木"), ("丙", "辛", "水", "火"),
            ("丁", "壬", "木", "火"), ("戊", "癸", "火", "土"),
        ]:
            g = self._hua_chart(dm, partner, hua)
            assert g["原五行"] == orig
            assert orig in g["忌五行"], f"{dm}化{hua}: {orig} must be 忌 — it only revives the DM"

    def test_original_element_that_feeds_the_hua_shen_stays_xi_with_caveat(self):
        """辛化水 / 壬化木 — 原五行 IS the 生化神者. It stays 喜; only its ROOTS break the 化."""
        for dm, partner, hua, orig in [("辛", "丙", "水", "金"), ("壬", "丁", "木", "水")]:
            g = self._hua_chart(dm, partner, hua)
            assert g["原五行"] == orig
            assert orig in g["喜用五行"]        # it genuinely feeds the 化神
            assert orig not in g["忌五行"]      # …so it is NOT blanket-忌
            assert g["提示"] and "复根" in g["提示"]   # …but the root caveat is recorded

    def test_po_ge_carries_position(self):
        g = self._hua_chart("辛", "丙", "水")
        by_cond = {p["条件"]: p for p in g["破格"]}
        assert by_cond["克化神"]["位置"] == "天干或地支"
        assert by_cond["日主复根"]["位置"] == "地支"   # ROOTS only
        assert by_cond["日主复根"]["五行"] == "金"

    def test_cycle_branch_that_reroots_the_dm_is_ji_yun(self):
        """The payoff. 化气格 requires 日主无根 at birth, so 复根 can ONLY arrive via a 运.

        For 辛化水, 金 rates 喜 on elements (生化神) — so 酉/申/丑 would have been 喜运. But
        each of them roots the 辛, it reverts, and the whole structure shatters.
        """
        from apps.backend.astronomer_logic.cycles.cycle_wu_xing import get_cycle_yun_shi

        ix = {"作用": {"柱位动态": [{
            "类型": "天干合", "形态": "化气格",
            "组合明细": {"日柱": "辛", "时柱": "丙"},
            "合化条件": {"合化元素": "水"},
        }]}}
        ys = make_yong_shen("癸", "水", "子", "旺", ling=4, di=4, shi=4, root="深根",
                            interactions=ix)
        assert ys["格局"] == "化气格"

        # 本气/中气 roots of 金 → a real 复根 → 破格 override fires
        for branch in ("酉", "申", "巳", "戌"):
            v = get_cycle_yun_shi(branch, ys)
            assert v["评级"] == "忌运", branch
            assert v["来源"] == "化气破格", branch
            assert "复根" in v["依据"]

        # 丑 holds 辛 only as 余气 (0.1) — a 墓库 root, 虽存而无力. The override does NOT fire.
        # 丑 is still 忌运, but for the correct reason: its 本气 土 克s the 化神 水.
        v = get_cycle_yun_shi("丑", ys)
        assert v["评级"] == "忌运"
        assert v["来源"] == "从格用神"

        for branch in ("子", "亥"):                # the 化神 itself — untouched
            v = get_cycle_yun_shi(branch, ys)
            assert v["评级"] == "喜运", branch
            assert v["来源"] == "从格用神", branch

    def test_yu_qi_root_does_not_shatter_the_hua_shens_own_branch(self):
        """The bug the depth gate fixes: counting 余气 rated the 化神's OWN branches as 破格.

        戊化火 vs 巳 — 巳's 本气 IS 丙火, the 化神. The branch overwhelmingly FEEDS the
        structure, yet a 0.1 余气 戊 was shattering it. Eight verdicts were wrong this way.
        """
        from apps.backend.astronomer_logic.cycles.cycle_wu_xing import (
            _substantive_root,
            get_cycle_yun_shi,
        )

        assert _substantive_root("巳", "土") is None      # 戊 in 巳 is 余气 → not substantive
        assert _substantive_root("未", "木") is None      # 乙 in 未 is 余气 (木墓)
        assert _substantive_root("酉", "金") == ("辛", "本气")
        assert _substantive_root("巳", "金") == ("庚", "中气")

        ix = {"作用": {"柱位动态": [{
            "类型": "天干合", "形态": "化气格",
            "组合明细": {"日柱": "戊", "时柱": "癸"},
            "合化条件": {"合化元素": "火"},
        }]}}
        ys = make_yong_shen("丙", "火", "午", "旺", ling=4, di=4, shi=4, root="深根",
                            interactions=ix)
        assert ys["格局详情"]["原五行"] == "土"
        for branch in ("巳", "寅"):   # 化神 itself / 生化神 — must NOT be 破格
            v = get_cycle_yun_shi(branch, ys)
            assert v["评级"] == "喜运", branch
            assert v["来源"] != "化气破格", branch

    def test_non_hua_qi_charts_are_unaffected(self):
        """The override must fire ONLY for 化气格 — a 从格 has no 化神 to break."""
        from apps.backend.astronomer_logic.cycles.cycle_wu_xing import get_cycle_yun_shi

        chart, _ = calculate_natal_chart(**TestGeJu.CONG_CAI)   # 从财格
        for branch in ("酉", "申", "丑", "子"):
            assert get_cycle_yun_shi(branch, chart["用神"])["来源"] != "化气破格"

    def test_ji_stem_downgrades_the_verdict(self):
        """The 天干 half of 破格's 位置 — declared in the data, and previously never checked.

        运势 read only the branch, but a 运柱 has two characters. A 化火格 meeting 壬午 has its
        化神 openly attacked by the visible 壬水, even though 午 IS the 化神 — and that rated
        喜运. The stem now drags the verdict down one step.

        It can only DOWNGRADE, never lift: the branch owns the direction (运看地支为重) and a
        friendly stem merely helps — exactly what the 辛化水 caveat says
        ("金生化神，天干透之则助化").
        """
        from apps.backend.astronomer_logic.cycles.cycle_wu_xing import get_cycle_yun_shi

        ix = {"作用": {"柱位动态": [{
            "类型": "天干合", "形态": "化气格",
            "组合明细": {"日柱": "癸", "时柱": "戊"},
            "合化条件": {"合化元素": "火"},
        }]}}
        ys = make_yong_shen("丁", "火", "巳", "极旺", ling=4, di=4, shi=4, root="深根",
                            interactions=ix)
        assert ys["格局详情"]["忌五行"] == ["水"]

        # 忌 stem on a 喜 branch → downgraded a step, and the reason is recorded
        v = get_cycle_yun_shi("午", ys, "壬")          # 壬(水) 克化神, 午 IS the 化神
        assert v["评级"] == "平运"
        assert "透干破格" in v["依据"]
        assert get_cycle_yun_shi("午", ys)["评级"] == "喜运"   # branch alone would say 喜运

        # a friendly stem must NOT lift the verdict
        assert get_cycle_yun_shi("午", ys, "丙")["评级"] == "喜运"   # 丙 IS the 化神
        assert get_cycle_yun_shi("寅", ys, "甲")["评级"] == "喜运"   # 甲 生化神

    def test_zheng_ge_stays_branch_only(self):
        """正格 charts must ignore the stem. The 金不换 表 is a 方位 (direction) table, and
        directions ARE branches — reading stems into it would invent data it does not have."""
        from apps.backend.astronomer_logic.cycles.cycle_wu_xing import get_cycle_yun_shi

        chart, _ = calculate_natal_chart(**DESMOND)
        ys = chart["用神"]
        assert ys["格局"] == "正格"
        for stem in ("甲", "庚", "壬", "丙"):
            v = get_cycle_yun_shi("午", ys, stem)
            assert v["评级"] == get_cycle_yun_shi("午", ys)["评级"]
            assert v["来源"] == "金不换"
