"""卷二·论地支 reads each branch as the MONTH: 「今当以月提为主」.

Natal rules (volume_2_di_zhi_prediction) and the 2a cycle rules (volume_2_gan_zhi_cycle_predictions)
encode the same passages; both gate on 月支, count 「日时…多/重」 the same way, and share one 编码说明.
"""
import pytest

from apps.backend.astronomer_logic.cycles import interpretation_cycle_chart as engine
from apps.backend.astronomer_logic.interaction_natal_chart import evaluate_rule
from apps.backend.data.san_ming_tong_hui_v2 import (
    volume_2_di_zhi_prediction as NATAL,
    volume_2_gan_zhi_cycle_predictions as CYCLE,
)
from apps.backend.tests.test_cycle_interpretation import _ctx, _fired, _leaves

NATAL_BY_NAME = {r["逻辑名称"]: r for r in NATAL}
SHARED_PREFIX = "主体取月支：「今当以月提为主」"


def _natal_fires(name: str, year: str, month: str, day: str, hour: str) -> bool:
    ctx = engine.build_cycle_chart_context(_ctx(year, month, day, hour), "甲", "子")
    return evaluate_rule(NATAL_BY_NAME[name], ctx)[0]


class TestCountScope:
    """计数_五行 / 计数_地支 honour 位置 (default 全局 = the four natal pillars)."""

    @staticmethod
    def _rule(cond: dict) -> dict:
        return {"逻辑名称": "t", "判定模式": "AND", "判定逻辑": [cond]}

    def _ctx(self):
        # 年 丙午 (火 火), 月 甲子, 日 甲子, 时 丁卯 (火 木)
        return engine.build_cycle_chart_context(_ctx("丙午", "甲子", "甲子", "丁卯"), "甲", "子")

    def test_wu_xing_count_scopes_pillars_and_layer(self):
        ctx = self._ctx()
        fire = lambda pos, n: self._rule({"位置": pos, "判定目标": {"类型": "计数_五行", "五行": ["火"], "阈值": n, "比较": ">="}})
        assert evaluate_rule(fire({"柱": "全局"}, 3), ctx)[0]
        assert not evaluate_rule(fire({"柱": ["日柱", "时柱"]}, 2), ctx)[0]  # only 丁 in 日+时
        assert evaluate_rule(fire({"柱": ["日柱", "时柱"]}, 1), ctx)[0]
        assert not evaluate_rule(fire({"柱": "全局", "部分": "天干"}, 3), ctx)[0]  # 丙 丁 = 2 stems

    def test_di_zhi_count_scopes_pillars(self):
        ctx = self._ctx()
        zi = lambda pos: self._rule({"位置": pos, "判定目标": {"类型": "计数_地支", "值": ["子"], "阈值": 2, "比较": ">="}})
        assert evaluate_rule(zi({"柱": "全局"}), ctx)[0]
        assert not evaluate_rule(zi({"柱": ["年柱", "时柱"]}), ctx)[0]


class TestMonthSubject:
    def test_every_natal_rule_gates_on_the_month(self):
        assert {r["前提条件"]["位置"]["柱"] for r in NATAL} == {"月柱"}

    def test_no_branch_partner_sits_on_the_month(self):
        for r in NATAL:
            for leaf in _leaves(r["判定逻辑"]):
                if leaf["判定目标"]["类型"] == "地支值":
                    assert leaf["位置"]["柱"] != "月柱", r["逻辑名称"]

    def test_every_cycle_di_zhi_rule_gates_on_the_month(self):
        for r in CYCLE:
            if r["逻辑名称"].startswith("论地支_"):
                assert r["判定逻辑"][0]["位置"]["柱"] == "月柱", r["逻辑名称"]

    def test_natal_and_cycle_share_one_encoding_note(self):
        cycle_notes = {r["编码说明"].split("。")[0] for r in CYCLE if r["逻辑名称"].startswith("论地支_")}
        natal_notes = {r["编码说明"].split("。")[0] for r in NATAL if "编码说明" in r}
        assert len(cycle_notes) == 1 and cycle_notes == natal_notes
        assert next(iter(cycle_notes)).startswith(SHARED_PREFIX)


# (natal rule, cycle rule, chart year/month/day/hour with the passage's branch as the month, a 运 that fires the cycle rule)
PAIRS = [
    ("辰支日时水木重_运向西北辰土难存", "论地支_辰月_日时水木_运向西北", ("甲申", "丙辰", "壬子", "甲寅"), "庚申"),
    ("巳支六阳之极_忌行东南烈焰之势", "论地支_巳月_运行东南_烧天烈焰", ("甲子", "己巳", "甲子", "甲子"), "甲寅"),
    ("未支柱中无火_怕行金水", "论地支_未月_柱中无火_怕金水运", ("庚申", "辛未", "壬子", "庚子"), "庚子"),
    ("未支日时多寒_偏爱丙丁", "论地支_未月_日时多寒_爱丙丁之乡", ("庚申", "辛未", "壬子", "庚子"), "丙午"),
    ("酉支日时火多_忌行东", "论地支_酉月_日时火多_愁东运", ("甲子", "己酉", "丙午", "丁巳"), "甲寅"),
    ("酉支日时水旺_忌行南", "论地支_酉月_日时水旺_怕南行", ("甲寅", "己酉", "壬子", "癸亥"), "丙午"),
    ("酉支柱见水土_有用运行西北", "论地支_酉月_柱见水泥_运行西北", ("甲子", "癸酉", "甲寅", "丙寅"), "庚申"),
]


class TestNatalAndCycleAgree:
    @pytest.mark.parametrize("natal,cycle,chart,yun", PAIRS)
    def test_same_chart_fires_both_versions(self, natal, cycle, chart, yun):
        assert _natal_fires(natal, *chart)
        assert cycle in _fired(_ctx(*chart), yun)

    @pytest.mark.parametrize("natal,cycle,chart,yun", PAIRS)
    def test_the_branch_as_day_branch_fires_neither(self, natal, cycle, chart, yun):
        year, month, day, hour = chart
        moved = (year, "甲子", month, hour)  # the passage's month pillar moved to the day, 月支 now 子
        assert not _natal_fires(natal, *moved)
        assert cycle not in _fired(_ctx(*moved), yun)


class TestTextConditions:
    def test_si_zhu_duo_huo_needs_two(self):
        assert not _natal_fires("寅支四柱多火_木不南奔", "甲子", "甲寅", "甲子", "丙子")  # one 火
        assert _natal_fires("寅支四柱多火_木不南奔", "甲子", "甲寅", "甲子", "丙午")

    def test_ri_shi_zhong_needs_two_within_day_and_hour(self):
        assert not _natal_fires("辰支日时水木重_运向西北辰土难存", "甲子", "丙辰", "丙午", "丙午")  # 0 in 日时
        assert not _natal_fires("辰支日时水木重_运向西北辰土难存", "甲子", "丙辰", "丙午", "甲午")  # 1
        assert _natal_fires("辰支日时水木重_运向西北辰土难存", "甲子", "丙辰", "壬午", "甲午")

    def test_tu_zhong_dui_mai_counts_earth_branches(self):
        assert not _natal_fires("申支土重堆埋_金有凶", "甲辰", "庚申", "甲子", "甲子")
        assert _natal_fires("申支土重堆埋_金有凶", "甲辰", "庚申", "甲子", "甲戌")
        assert not _natal_fires("申支土重堆埋_金有凶", "戊子", "庚申", "戊子", "戊子")  # 土 stems don't bury

    def test_wu_huo_is_checked(self):
        assert _natal_fires("申支木多无火_金终能胜", "甲寅", "庚申", "甲子", "甲子")
        assert not _natal_fires("申支木多无火_金终能胜", "甲寅", "庚申", "甲子", "丙子")

    def test_wei_split_reads_two_clauses(self):
        assert _natal_fires("未支柱中无火_怕行金水", "甲子", "辛未", "甲寅", "甲寅")
        assert not _natal_fires("未支日时多寒_偏爱丙丁", "甲子", "辛未", "甲寅", "甲寅")  # 日时 木, not cold
        assert _natal_fires("未支日时多寒_偏爱丙丁", "甲子", "辛未", "甲子", "甲子")  # 日时 子子 水
        assert not _natal_fires("未支柱中无火_怕行金水", "丙子", "辛未", "甲子", "甲子")  # 丙 is 火

    def test_hai_reads_any_earth_or_metal(self):
        assert _natal_fires("亥支见土_土至此不暖", "戊子", "乙亥", "甲子", "甲子")
        assert not _natal_fires("亥支见土_土至此不暖", "甲子", "乙亥", "甲子", "甲子")
        assert _natal_fires("亥支见金_金至此生寒", "甲申", "乙亥", "甲子", "甲子")


class TestBeforeAfter:
    """Documents the shift for real-looking charts: the subject moved from 日支 to 月支."""

    def test_zi_day_wu_month_now_reads_the_wu_month(self):
        chart = ("甲申", "庚午", "甲子", "甲子")
        # Before: 日支 子 was the subject → 子支见午 fired. After: 月支 午 is the subject.
        assert not _natal_fires("子支见午_水火相战", *chart)
        assert _natal_fires("午支见申子_水火战克", *chart)

    def test_chou_month_no_longer_needs_a_chou_day(self):
        # Before: required 日支 丑 AND 月支 丑. 「人命生于丑月」 asks only the month.
        assert _natal_fires("丑支生于丑月日时多水木_宜行巽离", "甲子", "丁丑", "甲午", "壬子")
