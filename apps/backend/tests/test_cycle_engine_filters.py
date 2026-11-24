"""Engine conditions the 卷二 论太岁 rules rely on: 交互.主动方 and a pillar-scoped 计数_神煞."""
from types import SimpleNamespace

from lunar_python.util import LunarUtil

from apps.backend.astronomer_logic.cycles import interpretation_cycle_chart as engine
from apps.backend.astronomer_logic.interaction_natal_chart import evaluate_rule


def _pillar(gz: str, day_stem: str) -> dict:
    stem, branch = gz[0], gz[1]
    return {
        "天干": {"天干": stem, "五行": LunarUtil.WU_XING_GAN[stem], "十神": LunarUtil.SHI_SHEN.get(day_stem + stem, "日主")},
        "地支": {"地支": branch, "五行": LunarUtil.WU_XING_ZHI[branch]},
        "藏干": {},
        "纳音": LunarUtil.NAYIN[gz],
    }


def _ctx() -> SimpleNamespace:
    si_zhu = {p: _pillar("甲子", "甲") for p in ("年柱", "月柱", "日柱", "时柱")}
    return SimpleNamespace(
        natal_si_zhu=si_zhu, rule_si_zhu=si_zhu, day_stem="甲", effective_day_stem="甲",
        dm_strength="中和", gender=1, natal_five_elements={}, lunar_birthday=None,
    )


def _rule(*conds: dict) -> dict:
    return {"逻辑名称": "t", "判定模式": "AND", "判定逻辑": list(conds)}


def _ke(actor: str) -> list[dict]:
    """A 流年 stem 克 between the 流年 and its 大运, as cycle_interactions emits it."""
    return [{"类型": "天干克", "形态": "岁运克", "组合明细": {"流年": "甲", "大运": "庚"},
             "主动方": actor, "强度": "强势主流"}]


class TestActorFilter:
    YUN_KE_SUI = {"位置": {"柱": "大运"}, "判定目标": {"类型": "交互", "值": ["天干克"], "主动方": "大运"}}
    SUI_KE_YUN = {"位置": {"柱": "大运"}, "判定目标": {"类型": "交互", "值": ["天干克"], "主动方": "运柱"}}

    def _ctx_with(self, actor: str):
        return engine.build_cycle_chart_context(
            _ctx(), "甲", "子", companion=("庚", "申"), interactions=_ke(actor), cycle_label="流年"
        )

    def test_matches_only_the_named_actor(self):
        ctx = self._ctx_with("大运")
        ok, ev = evaluate_rule(_rule(self.YUN_KE_SUI), ctx)
        assert ok and ev["主动方"] == "大运"
        assert not evaluate_rule(_rule(self.SUI_KE_YUN), ctx)[0]

    def test_the_period_actor_is_renamed_to_yun_zhu(self):
        ctx = self._ctx_with("流年")
        assert ctx.interactions[0]["主动方"] == "运柱"
        assert evaluate_rule(_rule(self.SUI_KE_YUN), ctx)[0]
        assert not evaluate_rule(_rule(self.YUN_KE_SUI), ctx)[0]

    def test_items_without_an_actor_never_match_it(self):
        clash = [{"类型": "六冲", "组合明细": {"流年": "子", "大运": "午"}, "强度": "强势主流"}]
        ctx = engine.build_cycle_chart_context(_ctx(), "甲", "子", ("庚", "午"), interactions=clash, cycle_label="流年")
        cond = {"位置": {"柱": "大运"}, "判定目标": {"类型": "交互", "值": ["六冲"], "主动方": "大运"}}
        assert not evaluate_rule(_rule(cond), ctx)[0]
        del cond["判定目标"]["主动方"]
        assert evaluate_rule(_rule(cond), ctx)[0]


class TestShenShaCountScope:
    STARS = [{"名称": "白虎", "来源": "年支"}, {"名称": "吊客", "来源": "年支"}]

    @staticmethod
    def _count(pillar: str, threshold: int) -> dict:
        return {"位置": {"柱": pillar}, "判定目标": {"类型": "计数_神煞", "神煞": ["白虎", "吊客", "丧门"],
                                                  "阈值": threshold, "比较": ">="}}

    def test_counts_the_transiting_pillars_stars(self):
        ctx = engine.build_cycle_chart_context(_ctx(), "甲", "子", shen_sha=self.STARS, cycle_label="流年")
        assert evaluate_rule(_rule(self._count("运柱", 2)), ctx)[0]
        assert not evaluate_rule(_rule(self._count("运柱", 3)), ctx)[0]

    def test_global_scope_still_means_the_natal_pillars(self):
        ctx = engine.build_cycle_chart_context(_ctx(), "甲", "子", shen_sha=self.STARS, cycle_label="流年")
        assert not evaluate_rule(_rule(self._count("全局", 1)), ctx)[0]
