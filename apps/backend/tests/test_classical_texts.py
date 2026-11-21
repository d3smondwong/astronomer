"""Coverage of the 释六十甲子 nature table (卷一) behind 古籍文献.三命通会_纳音性质."""

from lunar_python.util import LunarUtil

from apps.backend.astronomer_logic.classical_texts import (
    _JIAZI_NATURE,
    _extract_san_ming_tong_hui_pillar_nature,
)
from apps.backend.data.san_ming_tong_hui_v1 import volume_1_60_jia_zi_nature_pillar

ALL_JIA_ZI = [LunarUtil.JIA_ZI[i] for i in range(60)]


class TestJiaZiNatureTable:
    def test_covers_all_sixty_jia_zi(self):
        # A missing key silently yields 纳音性质: None for any pillar with that 干支.
        missing = [gz for gz in ALL_JIA_ZI if gz not in _JIAZI_NATURE]
        assert missing == []

    def test_no_duplicate_or_stray_keys(self):
        keys = [k for entry in volume_1_60_jia_zi_nature_pillar for k in entry]
        assert len(keys) == 60
        assert sorted(keys) == sorted(ALL_JIA_ZI)

    def test_follows_sixty_jia_zi_order(self):
        keys = [k for entry in volume_1_60_jia_zi_nature_pillar for k in entry]
        assert keys == ALL_JIA_ZI

    def test_each_entry_opens_with_its_own_gan_zhi(self):
        # Guards against a copy-paste putting one 干支's text under another's key.
        wrong = [gz for gz, text in _JIAZI_NATURE.items() if not text.startswith(gz)]
        assert wrong == []

    def test_restored_pillar_resolves(self):
        pillars = {
            "年柱": {"天干": "丙", "地支": "午"},
            "月柱": {"天干": "辛", "地支": "丑"},
            "日柱": {"天干": "壬", "地支": "寅"},
            "时柱": {"天干": "戊", "地支": "申"},
        }
        result = _extract_san_ming_tong_hui_pillar_nature(pillars)
        assert all(block["纳音性质"] for block in result.values())
