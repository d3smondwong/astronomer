"""小运 — the personal annual pillar on the pre-起运 years (cycles_orchestrator)."""

from datetime import datetime

import pytest

from apps.backend.orchestrator.cycles_orchestrator import _xiao_yun_gan_zhi, calculate_cycles

SINGAPORE = (1.35, 103.8)


def _stub_years(birth: datetime, gender: int) -> tuple[dict, list[dict]]:
    data, _ = calculate_cycles(birth, *SINGAPORE, gender, True, da_yun_index=0)
    return data, data["大运"][0]["流年"]


class TestXiaoYunStep:
    def test_first_year_is_hour_pillar_plus_one(self):
        # 「甲子时生堕地，即行乙丑，二岁丙寅」
        assert _xiao_yun_gan_zhi("甲子", 1, True) == "乙丑"
        assert _xiao_yun_gan_zhi("甲子", 2, True) == "丙寅"

    def test_backward_and_wraparound(self):
        assert _xiao_yun_gan_zhi("甲子", 1, False) == "癸亥"
        assert _xiao_yun_gan_zhi("癸亥", 1, True) == "甲子"
        assert _xiao_yun_gan_zhi("甲子", 60, True) == "甲子"


class TestXiaoYunOnStubYears:
    def test_reference_chart_male_backward(self):
        # 1985-11-25 17:07 TST → 时柱 庚申; 乙丑 is a yin year, male → 逆推.
        data, years = _stub_years(datetime(1985, 11, 25, 17, 7), 1)
        assert data["起运"]["顺逆"] == "逆推"
        assert [(y["虚岁"], y["小运"]["干支"]) for y in years[:3]] == [(1, "己未"), (2, "戊午"), (3, "丁巳")]

    def test_reference_chart_female_forward(self):
        data, years = _stub_years(datetime(1985, 11, 25, 17, 7), 0)
        assert data["起运"]["顺逆"] == "顺推"
        assert [(y["虚岁"], y["小运"]["干支"]) for y in years[:2]] == [(1, "辛酉"), (2, "壬戌")]

    def test_steps_on_li_chun_xu_sui_not_calendar_year(self):
        # Born 1990-01-15, before 立春: the birth 立春-year is 1989, so 虚岁 1 is the partial
        # 1989 entry and calendar 1990 is already 虚岁 2. lunar-python would call 1990 age 1.
        _, years = _stub_years(datetime(1990, 1, 15, 10, 0), 1)
        by_year = {y["年份"]: (y["虚岁"], y["小运"]["干支"]) for y in years}
        assert by_year[1989][0] == 1
        assert by_year[1990][0] == 2
        assert by_year[1990][1] == _xiao_yun_gan_zhi(by_year[1989][1], 1, False)

    def test_one_step_per_year(self):
        _, years = _stub_years(datetime(1985, 11, 25, 17, 7), 1)
        for prev, cur in zip(years, years[1:]):
            assert cur["小运"]["干支"] == _xiao_yun_gan_zhi(prev["小运"]["干支"], 1, False)

    def test_block_shape(self):
        _, years = _stub_years(datetime(1985, 11, 25, 17, 7), 1)
        block = years[0]["小运"]
        assert set(block) == {"干支", "运柱", "作用", "运势", "古籍解读"}
        assert block["运势"]["评级"] in {"喜运", "平运", "忌运"}
        assert block["古籍解读"] == {}  # no 小运 rules until 卷二·论小运

    def test_meets_natal_chart_only(self):
        # 1×4: no 流年 / 大运 opponent ever appears in a 小运 interaction.
        _, years = _stub_years(datetime(1985, 11, 25, 17, 7), 1)
        for y in years:
            for item in y["小运"]["作用"]["柱位动态"]:
                assert "小运" in item["组合明细"]
                assert not {"流年", "大运"} & set(item["组合明细"])


class TestPillarLabels:
    """Prose names the pillar it describes: 小运 relations are not 岁运 relations."""

    def test_xiao_yun_forms_are_named_for_it(self):
        _, years = _stub_years(datetime(1985, 11, 25, 17, 7), 1)
        forms = {i.get("形态", "") for y in years for i in y["小运"]["作用"]["柱位动态"]}
        assert any(f.startswith("小运") for f in forms)
        assert not any(f.startswith("岁运") for f in forms)

    def test_yun_shi_reason_names_each_pillar(self):
        data, _ = calculate_cycles(datetime(1985, 11, 25, 17, 7), *SINGAPORE, 1, True, da_yun_index=2)
        decade = data["大运"][2]
        assert decade["运势"]["依据"].startswith("运支")  # 大运 wording unchanged
        assert decade["流年"][0]["运势"]["依据"].startswith("流年支")
        _, years = _stub_years(datetime(1985, 11, 25, 17, 7), 1)
        reason = years[0]["小运"]["运势"]["依据"]
        assert reason.startswith("小运支") and "大运" not in reason

    def test_liu_nian_forms_keep_sui_yun(self):
        data, _ = calculate_cycles(datetime(1985, 11, 25, 17, 7), *SINGAPORE, 1, True, da_yun_index=2)
        forms = {i.get("形态", "") for y in data["大运"][2]["流年"] for i in y["作用"]["柱位动态"]}
        assert any(f.startswith("岁运") for f in forms)
        assert not any(f.startswith("小运") for f in forms)


class TestXiaoYunScope:
    @pytest.mark.parametrize("da_yun_index", [1, 2])
    def test_absent_once_the_first_da_yun_starts(self, da_yun_index):
        data, _ = calculate_cycles(datetime(1985, 11, 25, 17, 7), *SINGAPORE, 1, True, da_yun_index=da_yun_index)
        assert all("小运" not in y for y in data["大运"][da_yun_index]["流年"])
