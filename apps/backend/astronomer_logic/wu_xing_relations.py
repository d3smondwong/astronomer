"""
五行生克 — the primitive element relations, and the ten-god categorisation built on them.

The single source of truth for 生 (generates) and 克 (controls). These two maps sit under
almost every other module: 日主强弱 weighs 生/克 to score the day master, 格局 uses them to
name a 化神's feeder and destroyer, and 用神 / 五行动态 use them to say which life-domain
each element governs.

They were previously copy-pasted into day_master_strength, ge_ju and cycle_wu_xing (with
element_ten_god_class duplicated verbatim alongside). That is a live correctness hazard,
not just untidiness: 生克 is the most foundational mapping in the engine, and a fix applied
to one copy would leave the others silently divergent — precisely the class of cross-layer
disagreement that produced the 癸午 inversion bug. Import from here; do not re-declare.
"""

ELEMENTS: list[str] = ["木", "火", "土", "金", "水"]

# 生 — X generates Y (木生火, 火生土, …)
GENERATES: dict[str, str] = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

# 克 — X controls Y (木克土, 火克金, …)
CONTROLS: dict[str, str] = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}


def element_ten_god_class(element: str, dm_element: str) -> str:
    """The ten-god CATEGORY an element represents for the day master (life-domain).

    Polarity-free (element-level), so 比劫 / 印星 / 食伤 / 财星 / 官杀 — e.g. for a 戊(土)
    day master, 水 is 财星 and 木 is 官杀. Fixed per chart; it is what lets each element's
    state be read as a domain ("your 财 is 旺 and rising").

    Note this is deliberately NOT the same as a pillar's 十神, which keeps 正/偏 polarity
    (正财 vs 偏财). Where a real ten god is available, prefer it — this is for the
    element-level view, where polarity does not exist.
    """
    if element == dm_element:
        return "比劫"
    if GENERATES.get(element) == dm_element:
        return "印星"
    if GENERATES.get(dm_element) == element:
        return "食伤"
    if CONTROLS.get(element) == dm_element:
        return "官杀"
    return "财星"
