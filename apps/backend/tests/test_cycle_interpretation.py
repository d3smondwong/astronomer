"""Cycle classical-rule engine (cycles/interpretation_cycle_chart.py) and the 卷一 cycle rules."""

import importlib
import json
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


def _pillar(gz: str, day_stem: str) -> dict:
    """A natal pillar in the 四柱实体 shape, ten gods relative to day_stem (raw — no relabel)."""
    stem, branch = gz[0], gz[1]
    hidden = {
        tier: {"天干": h, "十神": LunarUtil.SHI_SHEN.get(day_stem + h, "无"), "五行": LunarUtil.WU_XING_GAN[h]}
        for tier, h in zip(("本气", "中气", "余气"), LunarUtil.ZHI_HIDE_GAN.get(branch, []))
    }
    return {
        "天干": {"天干": stem, "五行": LunarUtil.WU_XING_GAN[stem], "十神": LunarUtil.SHI_SHEN.get(day_stem + stem, "日主")},
        "地支": {"地支": branch, "五行": LunarUtil.WU_XING_ZHI[branch]},
        "藏干": hidden,
        "纳音": LunarUtil.NAYIN[gz],
    }


def _ctx(year: str, month: str = "甲子", day: str = "甲子", hour: str = "甲子",
         gender: int = 1, dm_strength: str = "中和"):
    """A NatalContext stand-in carrying only what build_cycle_chart_context reads."""
    d = day[0]
    si_zhu = {"年柱": _pillar(year, d), "月柱": _pillar(month, d), "日柱": _pillar(day, d), "时柱": _pillar(hour, d)}
    si_zhu["日柱"]["天干"]["十神"] = "日主"
    return SimpleNamespace(
        natal_si_zhu=si_zhu,
        rule_si_zhu=si_zhu,
        day_stem=d,
        effective_day_stem=d,
        dm_strength=dm_strength,
        gender=gender,
        natal_five_elements={},
        lunar_birthday=None,
    )


def _fired(ctx, cycle_gz: str, label: str = "大运", companion=None, shen_sha=None, interactions=None) -> set[str]:
    out = engine.get_cycle_interpretations(
        ctx, cycle_gz[0], cycle_gz[1], label, companion, shen_sha=shen_sha, interactions=interactions
    )
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
        # Brute force over natal charts × every 运: catches typo'd 干支/branches/ten gods that
        # would make a rule dead. Rules reading the 运柱's 神煞 / interactions need those facts
        # supplied, so they are exercised by targeted tests (TestVolume2a) instead.
        months = [ALL_JIA_ZI[i] for i in range(12)]  # one per branch
        days = ["甲子", "丙寅", "戊辰", "庚午", "壬申", "乙丑", "丁卯", "己巳", "辛未", "癸酉"]
        day_hours = [
            ("甲子", "甲子"), ("戊辰", "丙寅"), ("壬子", "庚子"), ("丙寅", "丁卯"),
            ("甲申", "甲申"), ("庚寅", "甲子"), ("癸丑", "甲子"),
        ] + [(d, h) for d in days for h in ("丙午", "庚申", "壬子")]
        needs_facts = {"神煞", "交互"}
        pending = {
            r["逻辑名称"]: r for r in _all_cycle_rules()
            if not {leaf["判定目标"]["类型"] for leaf in _leaves(r["判定逻辑"])} & needs_facts
        }
        for r in list(pending.values()):
            first = r["判定逻辑"][0]
            year_led = first.get("位置", {}).get("柱") == "年柱" and first["判定目标"]["类型"] == "特定组合"
            years = first["判定目标"]["值"] if year_led else ["甲子", "丙午"]
            for year, month, (day, hour), strength, cycle in itertools.product(
                years, months, day_hours, ("中和", "弱"), ALL_JIA_ZI
            ):
                ctx = engine.build_cycle_chart_context(
                    _ctx(year, month, day, hour, dm_strength=strength), cycle[0], cycle[1]
                )
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

    def test_xian_yun_rules_cover_da_yun_and_xiao_yun_not_liu_nian(self):
        # 限 names a 运 period (大限, 童限, 大小运限) — never the 太岁.
        ctx = _ctx("丙辰")
        assert "运_丙辰_吉_限运逢癸亥_显荣" in _fired(ctx, "癸亥", "大运")
        assert "运_丙辰_吉_限运逢癸亥_显荣" in _fired(ctx, "癸亥", "小运")
        assert "运_丙辰_吉_限运逢癸亥_显荣" not in _fired(ctx, "癸亥", "流年")

    def test_xian_rules_are_tagged_da_yun_and_xiao_yun(self):
        for r in _all_cycle_rules():
            if "流年" in r["适用周期"]:
                pytest.fail(f"{r['逻辑名称']}: 卷一 has no 太岁 rule, so no rule may list 流年")
            if "依据" in r or "限" in r["断语"]:
                assert r["适用周期"] == ["大运", "小运"], r["逻辑名称"]

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

    @pytest.mark.parametrize("label", ["大运", "小运"])
    def test_evidence_names_the_period_not_yun_zhu(self, label):
        out = engine.get_cycle_interpretations(_ctx("壬寅"), "戊", "戌", label)
        match = next(m for m in out["纳音格局"] if m["逻辑名称"] == "运_壬寅癸卯_吉_平地木")
        evidence = match["证据"]
        assert label in json.dumps(evidence, ensure_ascii=False)
        assert "运柱" not in json.dumps([m["证据"] for ms in out.values() for m in ms], ensure_ascii=False)

    def test_period_naming_keeps_the_companion_and_natal_labels(self):
        evidence = [{"宫位": "运柱", "组合": "戊戌"}, {"宫位": "大运"}, {"柱": "年柱", "匹配柱": ["运柱", "时柱"]}]
        assert engine._name_the_period(evidence, "流年") == [
            {"宫位": "流年", "组合": "戊戌"}, {"宫位": "大运"}, {"柱": "年柱", "匹配柱": ["流年", "时柱"]},
        ]

    def test_nothing_fired_is_an_empty_dict(self):
        # A 小运 run reaches only 卷一's 「限」 rules; none covers a 甲子 year.
        assert engine.get_cycle_interpretations(_ctx("甲子"), "甲", "子", "小运") == {}

    def test_only_groups_with_matches_appear(self):
        out = engine.get_cycle_interpretations(_ctx("甲子"), "甲", "子", "大运")
        assert all(matches for matches in out.values())

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


class TestVolume2a:
    """卷二 phase 2a: 论大运 and the 论地支 / 十干 大运 clauses (all 适用周期 ["大运"])."""

    def test_yuan_you_guan_xing_guan_yun(self):
        # 甲 day: 辛 = 正官. Natal year 辛酉 + 大运 癸酉 (酉 本气 辛) → 原有官，行官运发官.
        assert "论大运_原有官_行官运发官" in _fired(_ctx("辛酉"), "癸酉")
        assert "论大运_原有官_行官运发官" not in _fired(_ctx("甲子"), "癸酉")

    def test_sha_wants_control_only_while_untamed(self):
        # 甲 day: 庚 = 七杀, 丙 = 食神, 戊 = 偏财. 「煞欲运制」 is about an UNCONTROLLED 煞; a natal
        # 七杀 already relabelled 偏官 is controlled, so more 制 is 制伏太过 (phase 2b), not 吉.
        # 运 癸巳: 巳 本气 丙 = 食神.
        ctx = _ctx("庚午")
        assert "论大运_煞欲运制" in _fired(ctx, "癸巳")
        ctx.rule_si_zhu["年柱"]["天干"]["十神"] = "偏官"
        assert "论大运_煞欲运制" not in _fired(ctx, "癸巳")

    def test_sha_dislikes_help_whether_tamed_or_not(self):
        # 「煞不欲运助」 (财生煞) is a risk for the 煞 as a star — tamed or not.
        ctx = _ctx("庚午")
        assert "论大运_煞不欲运助" in _fired(ctx, "戊辰")
        ctx.rule_si_zhu["年柱"]["天干"]["十神"] = "偏官"
        assert "论大运_煞不欲运助" in _fired(ctx, "戊辰")

    def test_branch_ben_qi_decides_and_the_stem_adds_no_verdict(self):
        # 大运重地支. 戊 day, natal 丁 正印. 运 壬午: stem 壬 偏财, 午 本气 丁 正印 — the 印 side
        # fires; the stem's 财 does not add the opposite 「印不欲运衰」.
        fired = _fired(_ctx("丁卯", day="戊辰"), "壬午")
        assert "论大运_印欲运旺" in fired
        assert "论大运_印不欲运衰" not in fired
        # A stem-only match no longer fires: 运 丙寅 for a 庚 七杀 chart has 食神 only in its stem.
        assert "论大运_煞欲运制" not in _fired(_ctx("庚午"), "丙寅")

    def test_yun_pillar_carries_raw_ten_gods(self):
        # The 运柱 still exposes its stem's god (the modifier) alongside the branch's.
        pillar = engine.build_cycle_chart_context(_ctx("庚午"), "丙", "寅").pillars["运柱"]
        assert pillar["天干"]["十神"] == "食神"
        assert pillar["藏干"]["本气"]["十神"] == "比肩"

    def test_shi_er_chang_sheng_death_stage_is_tagged(self):
        # 甲 is 绝 at 申.
        out = engine.get_cycle_interpretations(_ctx("甲子"), "庚", "申", "大运")
        match = next(m for m in out["论大运"] if m["逻辑名称"] == "论大运_运临死绝")
        assert match["标注"] == "条件触发·非定论"
        assert "骨肉死丧" in match["结论"]

    def test_hua_gai_and_tian_yi_need_the_stars(self):
        ctx = _ctx("甲子")
        assert "论大运_运逢华盖" not in _fired(ctx, "甲辰")
        assert "论大运_运逢华盖" in _fired(ctx, "甲辰", shen_sha=[{"名称": "华盖", "来源": "年支"}])
        assert "论大运_运逢贵人" in _fired(ctx, "甲辰", shen_sha=[{"名称": "夜天乙贵人", "来源": "日干"}])

    def test_liu_he_reads_the_cycle_interactions(self):
        six_he = [{"类型": "六合", "组合明细": {"大运": "丑", "日柱": "子"}, "强度": "显著影响"}]
        out = engine.get_cycle_interpretations(_ctx("甲子"), "乙", "丑", "大运", interactions=six_he)
        match = next(m for m in out["论大运"] if m["逻辑名称"] == "论大运_运逢六合")
        assert "运柱" not in json.dumps(match["证据"], ensure_ascii=False)
        weak = [{**six_he[0], "强度": "轻微"}]  # below the natal material-strength floor
        assert "论大运_运逢六合" not in _fired(_ctx("甲子"), "乙丑", interactions=weak)

    def test_weak_day_master_wants_seal_or_peer(self):
        assert "论大运_身弱_运引旺乡" in _fired(_ctx("甲子", dm_strength="弱"), "壬子")
        assert "论大运_身弱_运引旺乡" not in _fired(_ctx("甲子", dm_strength="中和"), "壬子")

    def test_di_zhi_subject_is_the_month_branch(self):
        assert "论地支_午月_运行东南_身强" in _fired(_ctx("甲子", month="庚午"), "甲寅")
        assert "论地支_午月_运入西北_休囚" in _fired(_ctx("甲子", month="庚午"), "庚申")
        assert "论地支_午月_运行东南_身强" not in _fired(_ctx("甲子", day="庚午"), "甲寅")

    def test_jia_day_dislikes_the_west(self):
        assert "十干_甲日_运不喜西方" in _fired(_ctx("甲子"), "壬申")
        assert "十干_甲日_运不喜西方" not in _fired(_ctx("甲子", day="乙丑"), "壬申")

    def test_volume_2a_rules_are_da_yun_only(self):
        for name, rules in engine.CYCLE_ANALYZERS:
            if name in ("论大运", "论干支"):
                assert all(r["适用周期"] == ["大运"] for r in rules)
        assert not {n for n in _fired(_ctx("辛酉"), "辛未", "流年") if n.startswith(("论大运", "论地支", "十干"))}

    def test_real_chart_decades_get_volume_2a_readings(self):
        data, _ = calculate_cycles(datetime(1985, 11, 25, 17, 7), 1.35, 103.8, 1, True)
        decades = data["大运"][1:]
        assert any("论大运" in d["古籍解读"] for d in decades)
        evidence = [m["证据"] for d in decades for ms in d["古籍解读"].values() for m in ms]
        assert "运柱" not in json.dumps(evidence, ensure_ascii=False)  # prose may name the 运柱 block


class TestNatalRelabelParity:
    """rule_si_zhu repeats the natal pipeline's 七杀→偏官 / 食神→伤官 passes in a second place
    (cycles_orchestrator._build_context). If either copy changes, the cycle rules would read
    natal ten gods differently from /natal — this pins them together. The charts are chosen so
    both relabels actually occur (four with a 偏官, three with a 食神→伤官)."""

    CHARTS = [
        (datetime(1965, 3, 7, 23, 27), 0), (datetime(1973, 8, 8, 13, 55), 1),
        (datetime(1989, 12, 2, 8, 9), 0), (datetime(1988, 8, 20, 11, 48), 0),
        (datetime(1956, 3, 20, 20, 24), 0), (datetime(1984, 1, 28, 12, 5), 1),
        (datetime(2005, 5, 12, 17, 12), 1),
    ]

    @staticmethod
    def _gods(si_zhu: dict) -> dict:
        return {
            p: (si_zhu[p]["天干"]["十神"], tuple(t["十神"] for t in si_zhu[p]["藏干"].values()))
            for p in ("年柱", "月柱", "日柱", "时柱")
        }

    def test_rule_view_matches_natal_and_raw_view_stays_raw(self):
        from apps.backend.orchestrator.astronomer_data_orchestrator import (
            calculate_natal_chart,
            get_lunar_birthday,
        )
        from apps.backend.orchestrator.cycles_orchestrator import _build_context

        relabelled = 0
        for birth, gender in self.CHARTS:
            natal, _ = calculate_natal_chart(birth, 1.35, 103.8, gender, True)
            lunar = get_lunar_birthday(birth, 1.35, 103.8, True)
            ctx = _build_context(lunar.getEightChar(), gender, lunar)
            assert self._gods(ctx.rule_si_zhu) == self._gods(natal["四柱实体"]), birth
            raw = self._gods(ctx.natal_si_zhu)
            assert "偏官" not in json.dumps(raw, ensure_ascii=False), birth
            relabelled += raw != self._gods(ctx.rule_si_zhu)
        assert relabelled == len(self.CHARTS)  # every fixture exercises a relabel
