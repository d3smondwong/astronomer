"""七杀 / 偏官 label matching in the natal classical rules.

The natal pipeline relabels a tamed 七杀 as 偏官 (`ten_gods.apply_qi_sha_transformation`), so a
rule's label decides whether it sees a tamed 煞. The label follows what the rule's own text
describes — see `.claude/rules/bazi-natal.md`:
  the 煞 as a star → 七杀 + 偏官; an uncontrolled 煞 → 七杀 only; a controlled 煞 → 偏官;
  官-purity absence lists keep 七杀 only (去煞留官); 日贵 lists both (no 去留 exception).
"""
import copy
import importlib
from datetime import datetime

import pytest

from apps.backend.astronomer_logic import interaction_natal_chart as inc
from apps.backend.orchestrator.astronomer_data_orchestrator import (
    calculate_natal_chart,
    get_lunar_birthday,
)

PILLARS = ("年柱", "月柱", "日柱", "时柱")
GOD_KEYS = ("值", "十神", "目标十神", "主神", "配神", "克方", "被克方", "生方", "被生方")


def _all_rules() -> dict[str, dict]:
    rules: dict[str, dict] = {}
    for n in range(1, 8):
        module = importlib.import_module(f"apps.backend.data.san_ming_tong_hui_v{n}")
        for value in vars(module).values():
            if isinstance(value, list) and value and isinstance(value[0], dict) and "逻辑名称" in value[0]:
                for rule in value:
                    rules[rule["逻辑名称"]] = rule
    return rules


RULES = _all_rules()


def _leaves(conditions: list[dict]):
    for cond in conditions:
        if "判定逻辑" in cond:
            yield from _leaves(cond["判定逻辑"])
        else:
            yield cond


def _sha_labels(rule: dict) -> set[str]:
    """Which of 七杀 / 偏官 the rule's conditions name anywhere."""
    leaves = list(_leaves(rule["判定逻辑"]))
    if rule.get("前提条件"):
        leaves.append(rule["前提条件"])
    named: set[str] = set()
    for leaf in leaves:
        target = leaf.get("判定目标", {})
        for key in GOD_KEYS:
            value = target.get(key)
            named.update([value] if isinstance(value, str) else (value if isinstance(value, list) else []))
    return named & {"七杀", "偏官"}


def _chart(birth: datetime, gender: int) -> tuple[dict, inc.ChartContext]:
    natal, _ = calculate_natal_chart(birth, 1.35, 103.8, gender, True)
    lunar = get_lunar_birthday(birth, 1.35, 103.8, True)
    return natal, inc.build_chart_context({**natal, "_lunar_birthday": lunar})


def _gods(natal: dict) -> set[str]:
    out: set[str] = set()
    for p in PILLARS:
        pillar = natal["四柱实体"][p]
        out.add(pillar["天干"]["十神"])
        out.update(t["十神"] for t in pillar["藏干"].values())
    return out


def _fires(name: str, ctx: inc.ChartContext) -> bool:
    return inc.evaluate_rule(RULES[name], ctx)[0]


class TestPinnedLabels:
    """Each rule's label is a methodology decision (confirmed 2026-11-24); pin it."""

    UNTAMED_ONLY = [
        # 鬼 / 无制 / 攻身 — the uncontrolled 煞
        "勾绞_有鬼", "六甲日官煞混杂无制", "六甲日七杀无制为鬼", "官煞混杂", "弃命从煞", "煞重身轻",
        "杂气_七杀透出_需制伏",
        # 煞临子位 is followed by 「七煞有制亦多儿」
        "煞临子位",
        # 官 purity: 「有物去煞留官者，即以正官论」
        "正气官星格", "丙丁日子月忌七煞伤官", "甲乙日丑月忌煞伤岁同", "己日寅月忌七煞伤官", "戊日卯月忌煞伤官",
        "丙丁日辰月忌官伏无冲及煞伤", "辛日巳月忌坐七煞伤官", "癸日巳月忌七煞伤官", "壬日午月忌七煞伤官",
        "戊己日未月忌官伏无冲兼煞混伤官", "壬癸日未月忌七煞伤官", "乙日申月忌七煞伤官", "丙丁日申月忌伤七煞",
        "甲日酉月忌七煞伤官", "丁日亥月忌七煞伤官",
        # a 食神-tamed 煞 is 食神_制煞's subject, not a broken 食神格
        "食神_见官煞",
        # written 偏官 but requires no 食神 克 and no 合 — an untamed 煞
        "丁日子月偏官忌身弱无合露",
    ]
    BOTH = [
        "食神_制煞", "食神_制煞_逢枭", "日贵_昼生", "日贵_夜生", "日贵_财食印助", "日贵_重逢奇格",
        "财旺生官_戊己亥子月", "七煞遇长生_女命", "贪合忘煞", "建禄_时煞取贵", "印绶_逢七煞", "飞财_泄气凶",
        "火克金_生旺_象", "土克水",
    ]

    @pytest.mark.parametrize("name", UNTAMED_ONLY)
    def test_untamed_only(self, name: str):
        assert _sha_labels(RULES[name]) == {"七杀"}, name

    @pytest.mark.parametrize("name", BOTH)
    def test_both_labels(self, name: str):
        assert _sha_labels(RULES[name]) == {"七杀", "偏官"}, name


class TestTamedShaBehaviour:
    """Real charts whose only 煞 is tamed (偏官, no 七杀 label left)."""

    # 七杀 tamed by an adjacent 食神 (trigger 食神克七杀)
    SHI_SHEN_TAMED = [(datetime(1976, 12, 28, 2, 16), 0), (datetime(1985, 10, 21, 10, 37), 0)]
    # 日贵 day (癸卯/丁亥/癸巳/丁酉) whose chart carries a tamed 偏官
    RI_GUI_WITH_TAMED = [(datetime(1943, 2, 14, 12, 45), 0), (datetime(1963, 2, 13, 7, 21), 1)]

    @pytest.mark.parametrize("birth,gender", SHI_SHEN_TAMED)
    def test_shi_shen_zhi_sha_fires_on_the_control_it_describes(self, birth: datetime, gender: int):
        natal, ctx = _chart(birth, gender)
        triggers = {t for p in PILLARS for t in natal["四柱实体"][p].get("七杀化偏官", {}).values()}
        assert "食神克七杀" in triggers and "偏官" in _gods(natal) and "七杀" not in _gods(natal)
        assert _fires("食神_制煞", ctx)
        # The same 煞 must not also read as 「食神格破」: 食神_见官煞's 煞 branch (its 正官
        # alternative removed — a revealed 正官 breaks 食神格 on its own) stays silent.
        jian_sha = copy.deepcopy(RULES["食神_见官煞"])
        for cond in jian_sha["判定逻辑"]:
            if cond.get("判定模式") == "OR":
                cond["判定逻辑"] = [c for c in cond["判定逻辑"] if c["判定目标"].get("值") != ["正官"]]
        assert not inc.evaluate_rule(jian_sha, ctx)[0]

    @pytest.mark.parametrize("birth,gender", SHI_SHEN_TAMED)
    def test_gou_jiao_gui_is_the_untamed_sha(self, birth: datetime, gender: int):
        _, ctx = _chart(birth, gender)
        assert not _fires("勾绞_有鬼", ctx)
        assert _fires("勾绞_无鬼", ctx)

    @pytest.mark.parametrize("birth,gender", RI_GUI_WITH_TAMED)
    def test_tamed_sha_still_spoils_ri_gui(self, birth: datetime, gender: int):
        natal, ctx = _chart(birth, gender)
        assert "偏官" in _gods(natal) and "七杀" not in _gods(natal)
        assert not _fires("日贵_昼生", ctx)
