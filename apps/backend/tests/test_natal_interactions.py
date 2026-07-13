"""
Regression tests for natal_interactions partial-frame detection.

Focus: the duplicate-branch adjacency bug in 半合/拱合 (_detect_san_he) and
残会/拱会 (_detect_san_hui). A partial gates on pillar adjacency; when a branch
value is duplicated, keying off the FIRST occurrence of each value could miss a
genuinely adjacent partial (or misjudge its distance). The fix scans all
occurrences and uses the closest cross pair.

Run:  python -m pytest apps/backend/tests/test_natal_interactions.py -q
"""

from apps.backend.astronomer_logic.natal_interactions import (
    _detect_san_he,
    _detect_san_hui,
    InteractionRegistry,
)


def san_he(zhis: list) -> list[tuple]:
    reg = InteractionRegistry()
    _detect_san_he(zhis, reg)
    return [
        (it["类型"], it["组合明细"], it["距离"], it.get("缺失支"))
        for it in reg.all_items()
    ]


def san_hui(zhis: list) -> list[tuple]:
    reg = InteractionRegistry()
    _detect_san_hui(zhis, reg)
    return [
        (it["类型"], it["组合明细"], it["距离"], it.get("缺失支"))
        for it in reg.all_items()
    ]


class TestBanHeDuplicateAdjacency:
    def test_duplicate_partner_no_longer_masks_adjacent_ban_he(self):
        # 子(年) 卯(月) 申(日) 子(时). Group 申子辰: 申(日,2)+子(时,3) are adjacent
        # → a valid 半合. The duplicate 子 at 年柱 must NOT hijack the pick.
        items = san_he(["子", "卯", "申", "子"])
        ban_he = [it for it in items if it[0] == "半合"]
        assert len(ban_he) == 1
        _, detail, distance, missing = ban_he[0]
        assert detail == {"日柱": "申", "时柱": "子"}
        assert distance == 1
        assert missing == "辰"

    def test_control_non_adjacent_single_occurrence(self):
        # Only 子 at 年柱: 申(日,2) and 子(年,0) are distance 2 → correctly NO 半合.
        items = san_he(["子", "卯", "申", "巳"])
        assert not [it for it in items if it[0] == "半合"]

    def test_control_single_adjacent_occurrence(self):
        # Only 子 at 时柱: 申(日)+子(时) adjacent → 半合 (behaviour unchanged).
        items = san_he(["巳", "卯", "申", "子"])
        ban_he = [it for it in items if it[0] == "半合"]
        assert len(ban_he) == 1
        assert ban_he[0][1] == {"日柱": "申", "时柱": "子"}


class TestCanHuiDuplicateAdjacency:
    def test_duplicate_cardinal_recovers_closer_can_hui(self):
        # 子(年) 子(月) 卯(日) 丑(时). Group 亥子丑 (残会 needs cardinal 子, excludes
        # only distance==3). First-occurrence picks 子(年,0)+丑(时,3) = distance 3
        # → excluded. But 子(月,1)+丑(时,3) = distance 2 → the 残会 should register.
        items = san_hui(["子", "子", "卯", "丑"])
        can_hui = [it for it in items if it[0] == "残会"]
        assert len(can_hui) == 1
        _, detail, distance, missing = can_hui[0]
        assert detail == {"月柱": "子", "时柱": "丑"}
        assert distance == 2
        assert missing == "亥"


class TestNoDuplicateUnchanged:
    def test_first_occurrence_pick_is_stable_without_duplicates(self):
        # No duplicate branches → closest-pair == first-occurrence pick, so the
        # partial's pillars/distance are exactly what they always were.
        # 丑(年) 亥(月) 辰(日) 申(时): 亥丑 form a 拱会 (北, cardinal 子 absent),
        # adjacent 年柱-月柱.
        items = san_hui(["丑", "亥", "辰", "申"])
        gong_hui = [it for it in items if it[0] == "拱会"]
        assert len(gong_hui) == 1
        _, detail, distance, missing = gong_hui[0]
        assert detail == {"年柱": "丑", "月柱": "亥"}
        assert distance == 1
        assert missing == "子"
