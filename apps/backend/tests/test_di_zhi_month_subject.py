"""计数_五行 / 计数_地支 honour 位置 (default 全局 = the four natal pillars)."""
from apps.backend.astronomer_logic.cycles import interpretation_cycle_chart as engine
from apps.backend.astronomer_logic.interaction_natal_chart import evaluate_rule
from apps.backend.tests.test_cycle_interpretation import _ctx


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
