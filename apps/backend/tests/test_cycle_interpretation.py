"""Cycle classical-rule engine (cycles/interpretation_cycle_chart.py) and the 卷一 cycle rules."""

import importlib
import itertools
import re
from datetime import datetime
from types import SimpleNamespace

import pytest
from lunar_python.util import LunarUtil

from apps.backend.astronomer_logic import interaction_natal_chart as natal_engine
from apps.backend.astronomer_logic.cycles import interpretation_cycle_chart as engine
from apps.backend.astronomer_logic.interaction_natal_chart import evaluate_rule
from apps.backend.orchestrator.cycles_orchestrator import calculate_cycles

ALL_JIA_ZI = [LunarUtil.JIA_ZI[i] for i in range(60)]
CYCLE_POSITIONS = {engine.CYCLE_PILLAR, engine.COMPANION_PILLAR}
DATA_MODULES = [f"apps.backend.data.san_ming_tong_hui_v{n}" for n in range(1, 8)]

# Natal rules that already name a cycle position but predate the cycle engine. They never
# fire (no 运柱/大运 in a natal chart) and move to their chapter's cycle list when that
# chapter is encoded. The set may only shrink — a NEW natal rule with a cycle position
# would be a rule that silently never fires.
PENDING_MIGRATION = {
    "官星重犯",  # v5 — carries a "位置柱 " placeholder
    "岁带正马_寅卯月_运逢伤劫",  # v6
    "弃命从财_行运逢根",  # v6
    "正财_财旺身弱_运逢比劫",  # v6
}


# ── helpers ──────────────────────────────────────────────────────────────────


def _pillar(gz: str) -> dict:
    return {"天干": {"天干": gz[0]}, "地支": {"地支": gz[1]}, "纳音": LunarUtil.NAYIN[gz]}


def _ctx(year: str, month: str = "甲子", day: str = "甲子", hour: str = "甲子", gender: int = 1):
    """A NatalContext stand-in carrying only what build_cycle_chart_context reads."""
    return SimpleNamespace(
        natal_si_zhu={"年柱": _pillar(year), "月柱": _pillar(month), "日柱": _pillar(day), "时柱": _pillar(hour)},
        gender=gender,
        natal_five_elements={},
        lunar_birthday=None,
    )


def _fired(ctx, cycle_gz: str, label: str = "大运", companion=None) -> set[str]:
    out = engine.get_cycle_interpretations(ctx, cycle_gz[0], cycle_gz[1], label, companion)
    return {m["逻辑名称"] for matches in out.values() for m in matches}


def _all_cycle_rules() -> list[dict]:
    return [r for _, rules in engine.CYCLE_ANALYZERS for r in rules]


def _leaves(conds):
    for c in conds:
        if "判定逻辑" in c:
            yield from _leaves(c["判定逻辑"])
        else:
            yield c


def _positions(leaf) -> list[str]:
    zhu = leaf.get("位置", {}).get("柱")
    if zhu is None:
        return []
    return [zhu] if isinstance(zhu, str) else list(zhu)


# ── rule-data structure ──────────────────────────────────────────────────────


class TestCycleRuleData:
    def test_required_fields(self):
        for r in _all_cycle_rules():
            assert r["逻辑名称"] and r["断语"] and r["判定逻辑"], r.get("逻辑名称")
            assert r["来源"].startswith("卷"), r["逻辑名称"]
            periods = r["适用周期"]
            assert periods and set(periods) <= engine.CYCLE_PERIODS, r["逻辑名称"]

    def test_names_unique_and_distinct_from_natal(self):
        names = [r["逻辑名称"] for r in _all_cycle_rules()]
        assert len(names) == len(set(names))
        natal_names = {
            r["逻辑名称"]
            for mod in DATA_MODULES
            for name, v in vars(importlib.import_module(mod)).items()
            if name.endswith("_predictions") and not name.endswith("_cycle_predictions")
            and isinstance(v, list) and v and isinstance(v[0], dict) and "逻辑名称" in v[0]
            for r in v
        }
        assert not set(names) & natal_names

    def test_every_rule_names_a_cycle_position(self):
        # A cycle rule that never touches 运柱/大运 is a natal rule in the wrong list.
        for r in _all_cycle_rules():
            used = {p for leaf in _leaves(r["判定逻辑"]) for p in _positions(leaf)}
            assert used & CYCLE_POSITIONS, r["逻辑名称"]

    def test_condition_types_are_supported(self):
        for r in _all_cycle_rules():
            for leaf in _leaves(r["判定逻辑"]):
                kind = leaf["判定目标"]["类型"]
                allowed = (
                    engine.CYCLE_POSITION_TYPES
                    if set(_positions(leaf)) & CYCLE_POSITIONS
                    else engine.NATAL_POSITION_TYPES
                )
                assert kind in allowed, f"{r['逻辑名称']}: {kind} on {_positions(leaf)}"

    def test_condition_values_are_valid(self):
        branches = set(LunarUtil.ZHI[1:])
        for r in _all_cycle_rules():
            for leaf in _leaves(r["判定逻辑"]):
                kind, vals = leaf["判定目标"]["类型"], leaf["判定目标"].get("值", [])
                if kind == "特定组合":
                    assert set(vals) <= set(ALL_JIA_ZI), r["逻辑名称"]
                elif kind == "地支值":
                    assert set(vals) <= branches, r["逻辑名称"]

    def test_severe_verdicts_are_tagged_not_softened(self):
        # Policy: 夭 verdicts stay verbatim and carry the conditional tag.
        for r in _all_cycle_rules():
            if "夭" in r["断语"]:
                assert r.get("标注") == "条件触发·非定论", r["逻辑名称"]

    def test_every_cycle_list_is_wired(self):
        wired = {id(rules) for _, rules in engine.CYCLE_ANALYZERS}
        for mod in DATA_MODULES:
            for name, v in vars(importlib.import_module(mod)).items():
                if name.endswith("_cycle_predictions"):
                    assert id(v) in wired, f"{mod}.{name} is not in CYCLE_ANALYZERS"

    def test_natal_lists_hold_no_new_cycle_rules(self):
        src = open(natal_engine.__file__, encoding="utf-8-sig").read()
        natal_lists = set(re.findall(r"\b(volume_\w+)\b", src))
        offenders = set()
        for mod in DATA_MODULES:
            for name, v in vars(importlib.import_module(mod)).items():
                if name not in natal_lists or not isinstance(v, list):
                    continue
                for r in v:
                    if not isinstance(r, dict) or "判定逻辑" not in r:
                        continue
                    used = {p.strip() for leaf in _leaves(r["判定逻辑"]) for p in _positions(leaf)}
                    if used & (CYCLE_POSITIONS | {"位置柱"}):
                        offenders.add(r["逻辑名称"])
        assert offenders <= PENDING_MIGRATION, offenders - PENDING_MIGRATION

    def test_every_rule_can_fire(self):
        # Brute force: catches typo'd 干支/branches that would make a rule dead.
        months = [ALL_JIA_ZI[i] for i in range(12)]  # one per branch
        day_hours = [
            ("甲子", "甲子"), ("戊辰", "丙寅"), ("壬子", "庚子"), ("丙寅", "丁卯"),
            ("甲申", "甲申"), ("庚寅", "甲子"), ("癸丑", "甲子"),
        ]
        pending = {r["逻辑名称"]: r for r in _all_cycle_rules()}
        for r in list(pending.values()):
            years = r["判定逻辑"][0]["判定目标"]["值"]
            label = r["适用周期"][0]
            for year, month, (day, hour), cycle in itertools.product(years, months, day_hours, ALL_JIA_ZI):
                ctx = engine.build_cycle_chart_context(_ctx(year, month, day, hour), cycle[0], cycle[1])
                if evaluate_rule(r, ctx)[0]:
                    pending.pop(r["逻辑名称"])
                    break
        assert not pending, sorted(pending)


# ── engine behaviour ─────────────────────────────────────────────────────────


class TestCycleEngine:
    def test_cycle_pillar_supplies_the_partner(self):
        ctx = _ctx("壬寅")
        assert "运_壬寅癸卯_吉_平地木" in _fired(ctx, "戊戌")
        assert "运_壬寅癸卯_吉_平地木" not in _fired(ctx, "甲子")

    def test_natal_partner_alone_does_not_fire_cycle_rule(self):
        # 戊戌 in the natal month must NOT satisfy the 运柱 condition: 全局 ≠ 运柱.
        assert "运_壬寅癸卯_吉_平地木" not in _fired(_ctx("壬寅", month="戊戌"), "甲子")

    def test_global_scope_excludes_transiting_pillars(self):
        ctx = engine.build_cycle_chart_context(_ctx("甲子"), "戊", "戌", companion=("己", "亥"))
        probe = {
            "逻辑名称": "probe", "判定模式": "AND",
            "判定逻辑": [{"位置": {"柱": "全局"}, "判定目标": {"类型": "特定组合", "值": ["戊戌", "己亥"]}}],
        }
        assert evaluate_rule(probe, ctx)[0] is False

    def test_companion_is_addressable_on_liu_nian(self):
        ctx = engine.build_cycle_chart_context(_ctx("甲子"), "甲", "午", companion=("己", "亥"))
        probe = {
            "逻辑名称": "probe", "判定模式": "AND",
            "判定逻辑": [{"位置": {"柱": "大运"}, "判定目标": {"类型": "特定组合", "值": ["己亥"]}}],
        }
        assert evaluate_rule(probe, ctx)[0] is True

    def test_period_filter(self):
        # 运规东南 is a 运-only text → 大运, not 流年.
        ctx = _ctx("己巳")
        assert "运_己巳_运规东南_方成材用" in _fired(ctx, "甲辰", "大运")
        assert "运_己巳_运规东南_方成材用" not in _fired(ctx, "甲辰", "流年")

    def test_xian_yun_rules_apply_to_both_periods(self):
        ctx = _ctx("丙辰")
        assert "运_丙辰_吉_限运逢癸亥_显荣" in _fired(ctx, "癸亥", "大运")
        assert "运_丙辰_吉_限运逢癸亥_显荣" in _fired(ctx, "癸亥", "流年")

    def test_born_season_gate(self):
        assert "运_己未_春夏_运入沈潜之乡" in _fired(_ctx("己未", month="庚午"), "丙子")
        assert "运_己未_春夏_运入沈潜之乡" not in _fired(_ctx("己未", month="辛酉"), "丙子")

    def test_severe_rule_carries_tag_in_output(self):
        # 甲戌 山头火 + 丙寅 炉中火 = two 火纳音; 运 戊辰 大林木.
        out = engine.get_cycle_interpretations(_ctx("甲戌", month="丙寅"), "戊", "辰", "大运")
        match = next(m for m in out["纳音格局"] if m["逻辑名称"] == "运_甲戌乙亥_凶_火多限数逢木")
        assert match["标注"] == "条件触发·非定论"
        assert "或夭" in match["结论"]

    def test_output_shape(self):
        out = engine.get_cycle_interpretations(_ctx("壬寅"), "戊", "戌", "大运")
        match = out["纳音格局"][0]
        assert {"逻辑名称", "来源", "结论", "证据", "依据"} <= match.keys()
        assert match["依据"].endswith("限运同论。")

    def test_nothing_fired_is_an_empty_dict(self):
        assert engine.get_cycle_interpretations(_ctx("甲子"), "甲", "子", "大运") == {}

    def test_rejects_unknown_period(self):
        with pytest.raises(ValueError):
            engine.get_cycle_interpretations(_ctx("甲子"), "甲", "子", "流月")


class TestVolume1Scope:
    """卷一 decisions: 金泊金「限运同论」covers the fire passage only; 山下火「俱依此断」the whole section."""

    def test_jin_bo_jin_is_fire_passage_only(self):
        names = {r["逻辑名称"] for r in _all_cycle_rules() if "壬寅癸卯" in r["逻辑名称"]}
        assert names == {
            "运_壬寅癸卯_吉_平地木",
            "运_壬寅癸卯_夭_有火",
            "运_壬寅癸卯_忌_太阳_二火同见",
            "运_壬寅癸卯_吉_山下山头_清水",
            "运_壬寅癸卯_忌_炉火",
        }

    def test_post_clause_judgements_stay_natal(self):
        # 昆山片玉 (壬寅 见 戊寅) comes after 「限运同论」 → no cycle reading.
        assert not {n for n in _fired(_ctx("壬寅"), "戊寅") if "昆山" in n}

    def test_fire_kills_thin_gold(self):
        fired = _fired(_ctx("壬寅"), "丙申")  # 山下火, no 清水 in the natal chart
        assert "运_壬寅癸卯_夭_有火" in fired
        assert "运_壬寅癸卯_吉_山下山头_清水" not in fired

    def test_clear_water_is_the_exception(self):
        fired = _fired(_ctx("壬寅", day="甲申"), "丙申")  # natal 井泉水
        assert "运_壬寅癸卯_吉_山下山头_清水" in fired
        assert "运_壬寅癸卯_夭_有火" not in fired

    def test_sun_alone_is_not_fire_death(self):
        # 「遇太阳为日间之显」— the sun alone neither kills nor clashes.
        fired = _fired(_ctx("壬寅"), "戊午")
        assert "运_壬寅癸卯_夭_有火" not in fired
        assert "运_壬寅癸卯_忌_太阳_二火同见" not in fired

    def test_sun_with_another_fire_clashes(self):
        fired = _fired(_ctx("壬寅", month="丙寅"), "戊午")  # natal 炉中火 + 运 太阳
        assert "运_壬寅癸卯_忌_太阳_二火同见" in fired
        assert "运_壬寅癸卯_夭_有火" not in fired

    def test_furnace_fire_is_both_fire_and_worst_fire(self):
        fired = _fired(_ctx("壬寅"), "丙寅")
        assert {"运_壬寅癸卯_忌_炉火", "运_壬寅癸卯_夭_有火"} <= fired

    def test_shan_is_the_texts_list(self):
        # 山下火 names 癸丑 and 乙丑 as 山; 壬子 is not 山.
        assert "运_丙申丁酉_轻凶_大海水_无山" in _fired(_ctx("丙申", day="壬子"), "壬戌")
        assert "运_丙申丁酉_贵格_大海水_有山" in _fired(_ctx("丙申", day="癸丑"), "壬戌")
        assert "运_丙申丁酉_贵格_大海水_有山" in _fired(_ctx("丙申", day="乙丑"), "壬戌")

    def test_wind_excess(self):
        ctx = _ctx("丙申", month="戊辰", day="庚寅")  # 松柏木 + 辰 already in the chart
        assert "运_丙申丁酉_夭_松柏平地_风多" in _fired(ctx, "丁巳")
        assert "运_丙申丁酉_夭_松柏平地_风多" not in _fired(_ctx("丙申", day="庚寅"), "丁巳")

    def test_jia_yin_and_yi_mao(self):
        assert "运_丙申丁酉_吉_甲寅水" in _fired(_ctx("丁酉"), "甲寅")
        assert "运_丙申丁酉_不佳_乙卯震风" in _fired(_ctx("丁酉"), "乙卯")

    def test_metal_without_wood_leaks_fire(self):
        assert "运_丙申丁酉_丁酉_忌_余金_无木窃气" in _fired(_ctx("丁酉", month="甲子"), "庚戌")
        assert "运_丙申丁酉_丁酉_忌_余金_无木窃气" not in _fired(_ctx("丁酉", month="甲子", day="庚寅"), "庚戌")

    def test_encoding_note_travels_with_the_cycle_variant(self):
        rule = next(r for r in _all_cycle_rules() if r["逻辑名称"] == "运_丙申丁酉_夭_霹雳火_无木无山")
        assert "无火" in rule["编码说明"]


class TestOrchestratorWiring:
    def test_every_cycle_entry_carries_gu_ji_jie_du(self):
        data, _ = calculate_cycles(datetime(1985, 11, 25, 17, 7), 1.35, 103.8, 1, True, da_yun_index=2)
        decades = data["大运"]
        assert "古籍解读" not in decades[0]  # pre-运 stub has no 运柱
        for d in decades[1:]:
            assert isinstance(d["古籍解读"], dict)
        for year in decades[2]["流年"]:
            assert isinstance(year["古籍解读"], dict)

    def test_real_chart_fires_cycle_rule(self):
        # 1962-06-15, female (逆推) → 年柱 壬寅 (金泊金), decades run 乙巳 … 己亥, 戊戌.
        # Exactly the 戊戌/己亥 decades must fire 平地木.
        data, _ = calculate_cycles(datetime(1962, 6, 15, 12, 0), 1.35, 103.8, 0, True)
        hits = [
            d["干支"]
            for d in data["大运"][1:]
            if "运_壬寅癸卯_吉_平地木" in {m["逻辑名称"] for ms in d["古籍解读"].values() for m in ms}
        ]
        expected = [d["干支"] for d in data["大运"][1:] if d["干支"] in ("戊戌", "己亥")]
        assert expected, "fixture chart must run a 戊戌/己亥 decade"
        assert hits == expected
