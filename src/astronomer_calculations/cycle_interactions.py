# ══════════════════════════════════════════════════════════════════════════════
# CYCLE INTERACTIONS — Shared Engine for External Pillar Analysis
#
# Covers: 大运 / 小运 / 流年 / 流月 (and any future cycle type)
# One external pillar (stem + branch) enters a 4-pillar natal chart.
# All cycle types use the same logic; only cycle_label differs.
#
# SECTION 1 — Imports & Cycle-Specific Constants
# SECTION 2 — CycleRegistry & Actors
# SECTION 3 — Utilities
# SECTION 4 — Detection Helpers
# SECTION 5 — Priority Filter  (apply_cycle_master_priority)
# SECTION 6 — Output Assembly
# SECTION 7 — Orchestrator     (_detect_cycle_interactions)
# ══════════════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Imports & Cycle-Specific Constants
# ══════════════════════════════════════════════════════════════════════════════

from lunar_python.util import LunarUtil

from src.astronomer_calculations.interactions_gan_zhi_zuo_yong import (
    # Branch maps
    six_he_map,
    six_he_element_map,
    clash_map,
    harm_map,
    break_map,
    hidden_stem_he,
    cardinal_branches,
    directional_he,
    SAN_HUI_DIRECTION,
    triple_he,
    POSITIONAL_ARCH_MAP,
    # Stem maps
    stem_combines,
    stem_clashes,
    stem_controls,
    stem_elements,
    # Punishment
    is_valid_punishment,
    # Peer combination
    is_valid_peer_combination,
    # Helpers & shared tables
    get_status,
    STRENGTH_ORDER,
    _get_shi_shen_for_stem_pair,
    _STEM_COMBINE_ELEMENT,
)

# ── Pillar name constants (shared with natal; redefined here for locality) ───
_PILLAR_NAMES = ["年柱", "月柱", "日柱", "时柱"]
_PILLAR_IDX_MAP = {"年柱": 0, "月柱": 1, "日柱": 2, "时柱": 3}

# ── Tier order for final sort ─────────────────────────────────────────────────
# 反吟/伏吟 are cycle-unique and occupy the top two tiers.
CYCLE_TIER_ORDER: dict[str, int] = {
    "反吟": 0,
    "伏吟": 1,
    "三会": 2,
    "三合": 3,
    "共拱": 4,
    "拱会": 5,
    "残会": 6,
    "半合": 7,
    "六冲": 8,
    "开库": 8,
    "六合": 9,
    "比和": 10,
    "天干合": 11,
    "天干克": 12,
    "天干冲": 13,
    "无恩之刑": 14,
    "恃势之刑": 14,
    "无礼之刑": 14,
    "自刑": 15,
    "六害": 16,
    "六破": 17,
    "干支透合": 18,
    "暗合": 18,
}

# ── Declarative priority rule table ──────────────────────────────────────────
# (lock_type, itype) → 强度
# Only downgrades — never upgrades via this table.
# STRUCTURAL covers both 三会 and 三合 as branch lock types.
#
# Design notes:
#   STRUCTURAL + 六冲 → 中等衰减 (not 消融吸收): the clash lives within the
#     structural field as tension (冲中有合之势), partially absorbed but real.
#   PRIMARY_六合 + 六冲 → 消融吸收: bilateral bond fully neutralises clash
#     (贪合忘冲). Stricter than STRUCTURAL because 六合 is a direct two-body lock.
#   PRIMARY_六冲 + 六害/刑 → 显著影响: 冲 and 害/刑 are classically co-active;
#     the clash does not suppress them — it amplifies the destabilisation.
#   STEM_天干冲 entry omitted: if 天干冲 is the stem lock, no stronger stem
#     interaction exists, so there is nothing to suppress.

CYCLE_PRIORITY_RULE_TABLE: dict[tuple, str] = {
    # ── STRUCTURAL branch lock (三会 or 三合) ──
    ("STRUCTURAL", "六合"): "大幅衰减",
    ("STRUCTURAL", "六冲"): "中等衰减",
    ("STRUCTURAL", "开库"): "中等衰减",
    ("STRUCTURAL", "半合"): "大幅衰减",
    ("STRUCTURAL", "拱会"): "大幅衰减",
    ("STRUCTURAL", "残会"): "大幅衰减",
    ("STRUCTURAL", "共拱"): "大幅衰减",
    ("STRUCTURAL", "六害"): "大幅衰减",
    ("STRUCTURAL", "六破"): "大幅衰减",
    ("STRUCTURAL", "无恩之刑"): "大幅衰减",
    ("STRUCTURAL", "恃势之刑"): "大幅衰减",
    ("STRUCTURAL", "无礼之刑"): "大幅衰减",
    ("STRUCTURAL", "自刑"): "大幅衰减",
    # ── PRIMARY_六合 branch lock (贪合忘冲) ──
    ("PRIMARY_六合", "六合"): "显著影响",  # same-partner 六合 appears twice in natal
    ("PRIMARY_六合", "六冲"): "消融吸收",
    ("PRIMARY_六合", "开库"): "消融吸收",
    ("PRIMARY_六合", "半合"): "显著影响",
    ("PRIMARY_六合", "拱会"): "显著影响",
    ("PRIMARY_六合", "残会"): "显著影响",
    ("PRIMARY_六合", "共拱"): "显著影响",
    ("PRIMARY_六合", "六害"): "大幅衰减",
    ("PRIMARY_六合", "六破"): "大幅衰减",
    ("PRIMARY_六合", "无恩之刑"): "大幅衰减",
    ("PRIMARY_六合", "恃势之刑"): "大幅衰减",
    ("PRIMARY_六合", "无礼之刑"): "大幅衰减",
    ("PRIMARY_六合", "自刑"): "大幅衰减",
    # ── PRIMARY_六冲 branch lock ──
    ("PRIMARY_六冲", "六冲"): "显著影响",  # same-target 六冲 appears twice in natal
    ("PRIMARY_六冲", "开库"): "显著影响",  # same-target tomb appears twice in natal
    ("PRIMARY_六冲", "六合"): "大幅衰减",
    ("PRIMARY_六冲", "半合"): "大幅衰减",
    ("PRIMARY_六冲", "拱会"): "大幅衰减",
    ("PRIMARY_六冲", "残会"): "大幅衰减",
    ("PRIMARY_六冲", "共拱"): "大幅衰减",
    ("PRIMARY_六冲", "六害"): "显著影响",  # 冲害协同
    ("PRIMARY_六冲", "六破"): "显著影响",  # 冲破协同
    ("PRIMARY_六冲", "无恩之刑"): "显著影响",  # 刑冲并见
    ("PRIMARY_六冲", "恃势之刑"): "显著影响",  # 刑冲并见
    ("PRIMARY_六冲", "无礼之刑"): "显著影响",  # 刑冲并见
    ("PRIMARY_六冲", "自刑"): "显著影响",  # 刑冲并见
    # ── Stem locks ──
    ("STEM_天干合", "天干克"): "消融吸收",
    ("STEM_天干合", "天干冲"): "消融吸收",
    ("STEM_天干克", "天干冲"): "大幅衰减",
    # STEM_天干冲 needs no entry — it is only the lock when no 天干合/克 exists,
    # so there is no other stem interaction present to suppress.
    # ── Branch/Stem locks → 干支透合 ──
    # 干支透合 is a covert stem-to-hidden-stem combination; always secondary.
    # STRUCTURAL: natal branch bound in structural field, hidden stems consumed by transformation.
    # PRIMARY_六合: natal branch occupied (贪合), hidden stems unavailable.
    # PRIMARY_六冲: natal branch clashed, hidden stems scattered (冲则气散).
    # STEM_天干合: cycle stem already directly locked; second covert combination absorbed (贪合忘合).
    # STEM_天干克 omitted: 克 operates stem-to-stem; branch hidden stem is a different layer.
    ("STRUCTURAL",   "干支透合"): "大幅衰减",
    ("PRIMARY_六合", "干支透合"): "大幅衰减",
    ("PRIMARY_六冲", "干支透合"): "大幅衰减",
    ("STEM_天干合",  "干支透合"): "消融吸收",
}

# ── Remark templates ──────────────────────────────────────────────────────────
# Key: (lock_type, itype) → remark string template (use .format(cycle=...) to fill)
# Causal explanations only — generic noise belongs in the LLM layer.
CYCLE_REMARKS: dict[tuple, str] = {
    # Branch lock → other branch interactions
    ("STRUCTURAL", "六合"): "{cycle}支{cb}参与三会/三合结构，与{nb_pillar}{nb}之合力被宏观场压制",
    ("STRUCTURAL", "六冲"): "{cycle}支参与结构场，冲力与方位场形成内部张力，被部分吸收",
    ("STRUCTURAL", "开库"): "{cycle}支参与结构场，开库冲力被部分吸收",
    ("STRUCTURAL", "六害"): "被三会/三合方位场压制，害力衰减",
    ("STRUCTURAL", "六破"): "被三会/三合方位场压制，破力衰减",
    ("STRUCTURAL", "无恩之刑"): "被三会/三合方位场压制，刑力衰减",
    ("STRUCTURAL", "恃势之刑"): "被三会/三合方位场压制，刑力衰减",
    ("STRUCTURAL", "无礼之刑"): "被三会/三合方位场压制，刑力衰减",
    ("STRUCTURAL", "自刑"): "被三会/三合方位场压制，刑力衰减",
    (
        "PRIMARY_六合",
        "六合",
    ): "{cycle}支{cb}已六合{pillar}{lock_nb}，同一合伴再现于他柱，辅助共鸣，合力降级",
    ("PRIMARY_六合", "六冲"): "贪合忘冲：{cycle}支{cb}已六合{pillar}{lock_nb}，冲力被合化消融",
    (
        "PRIMARY_六合",
        "开库",
    ): "贪合忘冲：{cycle}支{cb}已六合{pillar}{lock_nb}，开库钥匙被锁，库门封闭",
    ("PRIMARY_六合", "六害"): "{cycle}支{cb}已六合{pillar}{lock_nb}，害力被合力压制",
    ("PRIMARY_六合", "六破"): "{cycle}支{cb}已六合{pillar}{lock_nb}，破力被合力压制",
    ("PRIMARY_六合", "无恩之刑"): "{cycle}支{cb}已六合{pillar}{lock_nb}，刑力被合力压制",
    ("PRIMARY_六合", "恃势之刑"): "{cycle}支{cb}已六合{pillar}{lock_nb}，刑力被合力压制",
    ("PRIMARY_六合", "无礼之刑"): "{cycle}支{cb}已六合{pillar}{lock_nb}，刑力被合力压制",
    ("PRIMARY_六合", "自刑"): "{cycle}支{cb}已六合{pillar}{lock_nb}，刑力被合力压制",
    (
        "PRIMARY_六冲",
        "六冲",
    ): "{cycle}支{cb}已锁定{pillar}{lock_nb}为主冲目标，同一冲伴再现于他柱，次级冲力",
    (
        "PRIMARY_六冲",
        "开库",
    ): "{cycle}支{cb}已锁定{pillar}{lock_nb}为主冲目标，同一库支再现于他柱，次级开库",
    (
        "PRIMARY_六冲",
        "六合",
    ): "冲位已占：{cycle}支{cb}已以{pillar}{lock_nb}为冲击目标，此合力大幅减弱",
    ("PRIMARY_六冲", "六害"): "刑冲并见：冲位不稳，害力乘势协同",
    ("PRIMARY_六冲", "六破"): "刑冲并见：冲位不稳，破力乘势协同",
    ("PRIMARY_六冲", "无恩之刑"): "刑冲并见：冲位已破，无恩之刑乘虚而入",
    ("PRIMARY_六冲", "恃势之刑"): "刑冲并见：冲位已破，恃势之刑乘虚而入",
    ("PRIMARY_六冲", "无礼之刑"): "刑冲并见：冲位已破，无礼之刑乘虚而入",
    ("PRIMARY_六冲", "自刑"): "刑冲并见：冲位已破，自刑内耗加剧",
    # Branch/Stem locks → 干支透合
    ("STRUCTURAL",   "干支透合"): "结构场锁定地支，藏干不得透出，干支透合受压",
    ("PRIMARY_六合", "干支透合"): "{pillar}{lock_nb}已被六合占位，藏干潜合力被合力压制",
    ("PRIMARY_六冲", "干支透合"): "{pillar}{lock_nb}支被六冲气散，藏干无力应合",
    ("STEM_天干合",  "干支透合"): "{cycle}干{cs}已与{pillar}{lock_ns}天干直合，贪合之下，藏干透合消融",
    # Stem lock → other stem interactions
    ("STEM_天干合", "天干克"): "天干合化锁定，克力被合化消融",
    ("STEM_天干合", "天干冲"): "天干合化锁定，冲力被合化消融",
    ("STEM_天干克", "天干冲"): "天干克在位，冲势被制化消融",
}

# ── 开库 strength by 钥匙受困 state ──────────────────────────────────────────
# Top-level 强度 of the 开库 interaction itself.
KAIKU_STRENGTH: dict[str, str] = {
    "free": "强势主流",
    "partially_trapped": "显著影响",
    "fully_trapped": "消融吸收",
}

# ── 库藏释放 strength by (钥匙受困 state, 层次) ──────────────────────────────
KAIKU_RELEASE_STRENGTH: dict[tuple, str] = {
    ("free", "主气"): "强势主流",
    ("free", "中气"): "显著影响",
    ("free", "余气"): "中等衰减",
    ("partially_trapped", "主气"): "显著影响",
    ("partially_trapped", "中气"): "中等衰减",
    ("partially_trapped", "余气"): "大幅衰减",
    ("fully_trapped", "主气"): "消融吸收",
    ("fully_trapped", "中气"): "消融吸收",
    ("fully_trapped", "余气"): "消融吸收",
}

# ── 库藏释放 性质 label by (钥匙受困 state, 层次) ────────────────────────────
KAIKU_RELEASE_NATURE: dict[tuple, str] = {
    ("free", "主气"): "稳定涌现",
    ("free", "中气"): "条件涌现",
    ("free", "余气"): "残余涌现",
    ("partially_trapped", "主气"): "受压涌现",
    ("partially_trapped", "中气"): "微弱渗出",
    ("partially_trapped", "余气"): "封而不死",
    ("fully_trapped", "主气"): "受阻封印",
    ("fully_trapped", "中气"): "受阻封印",
    ("fully_trapped", "余气"): "受阻封印",
}

# ── Tomb hidden stem hierarchy (static; do not derive from library) ───────────
# Each tomb branch: [(hidden_stem, 层次), ...]  ordered 主气 → 中气 → 余气
TOMB_HIDDEN_STEMS: dict[str, list[tuple[str, str]]] = {
    "辰": [("戊", "主气"), ("乙", "中气"), ("癸", "余气")],
    "戌": [("戊", "主气"), ("辛", "中气"), ("丁", "余气")],
    "丑": [("己", "主气"), ("癸", "中气"), ("辛", "余气")],
    "未": [("己", "主气"), ("丁", "中气"), ("乙", "余气")],
}
_TOMB_BRANCHES = frozenset(TOMB_HIDDEN_STEMS.keys())

# Hidden stems for non-tomb branches — used by _check_branch_rooting.
# Module-level constant to avoid re-creating the dict on every call.
_NON_TOMB_HIDDEN: dict[str, list[str]] = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

# ── Turbulence strength downgrade map ────────────────────────────────────────
# Applied post-pass to interactions touching a turbulent (反吟/伏吟) natal pillar.
# Floor at 大幅衰减 — classical sources do not nullify bonds via turbulence alone.
_TURBULENCE_DOWNGRADE: dict[str, str] = {
    "强势主流": "显著影响",
    "显著影响": "中等衰减",
    "中等衰减": "大幅衰减",
    "大幅衰减": "大幅衰减",  # floor
    # 消融吸收 → unchanged (already nullified)
}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — CycleRegistry & Actors
# ══════════════════════════════════════════════════════════════════════════════


class CycleStemActor:
    """
    The single stem of the external cycle pillar.

    lock_type values:
        None           — no stem interaction present
        "STEM_天干合"  — bonded (highest priority)
        "STEM_天干克"  — controlling
        "STEM_天干冲"  — clashing (lowest stem priority)
    """

    __slots__ = ("lock_type", "lock_item_id", "item_ids")

    def __init__(self):
        self.lock_type: str | None = None
        self.lock_item_id: int | None = None
        self.item_ids: list[int] = []


class CycleBranchActor:
    """
    The single branch of the external cycle pillar.

    lock_type values:
        None           — no branch interaction present
        "STRUCTURAL"   — locked by 三会 or 三合 (highest priority)
        "PRIMARY_六合" — locked by 六合
        "PRIMARY_六冲" — locked by 六冲 or 开库 (lowest branch priority)
    """

    __slots__ = ("lock_type", "lock_item_id", "item_ids")

    def __init__(self):
        self.lock_type: str | None = None
        self.lock_item_id: int | None = None
        self.item_ids: list[int] = []


class CycleRegistry:
    """
    Registry for all cycle-natal interactions.

    State machine per item:
        ACTIVE   — default; eligible for pass logic
        LOCKED   — claimed as primary lock for an actor
        ABSORBED — neutralised (消融吸收); excluded from further processing

    Internal bookkeeping keys (_iid, _synthetic) are stripped at output boundary.
    """

    def __init__(self):
        self._items: list[dict] = []
        self._state: dict[int, str] = {}  # _iid → "ACTIVE"|"LOCKED"|"ABSORBED"
        self._index: dict[int, dict] = {}  # _iid → item  (O(1) lookup)
        self._iid_counter: int = 0
        self.stem_actor: CycleStemActor = CycleStemActor()
        self.branch_actor: CycleBranchActor = CycleBranchActor()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _next_iid(self) -> int:
        self._iid_counter += 1
        return self._iid_counter

    def _wire(self, item: dict) -> None:
        """Connect item to the appropriate actor(s) based on interaction type."""
        iid = item["_iid"]
        itype = item.get("类型", "")
        if itype in {"天干合", "天干克", "天干冲"}:
            self.stem_actor.item_ids.append(iid)
        else:
            self.branch_actor.item_ids.append(iid)

    # ── Registration ─────────────────────────────────────────────────────────

    def register(self, item: dict) -> None:
        """Stamp item with _iid, set state ACTIVE, wire to actor."""
        item["_iid"] = self._next_iid()
        self._items.append(item)
        self._state[item["_iid"]] = "ACTIVE"
        self._index[item["_iid"]] = item
        self._wire(item)

    def inject(self, item: dict) -> None:
        """Add synthetic entry (e.g. partially-trapped 开库 sub-entries)."""
        item["_synthetic"] = True
        item["_iid"] = self._next_iid()
        self._items.append(item)
        self._state[item["_iid"]] = "ACTIVE"
        self._index[item["_iid"]] = item
        self._wire(item)

    # ── State transitions ─────────────────────────────────────────────────────

    def lock(self, iid: int) -> None:
        self._state[iid] = "LOCKED"

    def absorb(self, iid: int) -> None:
        self._state[iid] = "ABSORBED"

    # ── State queries ─────────────────────────────────────────────────────────

    def is_active(self, iid: int) -> bool:
        return self._state.get(iid) == "ACTIVE"

    def is_locked(self, iid: int) -> bool:
        return self._state.get(iid) == "LOCKED"

    def is_absorbed(self, iid: int) -> bool:
        return self._state.get(iid) == "ABSORBED"

    # ── Item access ───────────────────────────────────────────────────────────

    def item_by_id(self, iid: int) -> dict | None:
        return self._index.get(iid)

    def all_items(self) -> list[dict]:
        return list(self._items)

    def active_items(self) -> list[dict]:
        return [it for it in self._items if self.is_active(it["_iid"])]

    def get_by_type(
        self, types: list[str], actor: str = "branch", active_only: bool = True
    ) -> list[dict]:
        """Return items of given type(s) wired to the named actor."""
        a = self.stem_actor if actor == "stem" else self.branch_actor
        result = []
        for iid in a.item_ids:
            item = self.item_by_id(iid)
            if item is None:
                continue
            if active_only and not self.is_active(iid):
                continue
            if item.get("类型") in types:
                result.append(item)
        return result


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Utilities
# ══════════════════════════════════════════════════════════════════════════════


def _cycle_pillar_index(combo: str) -> int | None:
    """
    Extract the natal pillar index from a cycle combo string like "大运-月柱".
    Skips the first token (the cycle label) and looks up only the second.
    Returns None if no valid natal pillar name is found.
    """
    parts = [p.strip() for p in combo.split("-")]
    for part in parts[1:]:  # skip cycle label at index 0
        if part in _PILLAR_IDX_MAP:
            return _PILLAR_IDX_MAP[part]
    return None


def _natal_indices_from_combo(combo: str) -> tuple[int, ...]:
    """
    Return all natal pillar indices from a combo string (skipping the cycle label).
    E.g. "大运-月柱-日柱" → (1, 2).  Always returns a tuple.
    """
    parts = [p.strip() for p in combo.split("-")]
    result = []
    for part in parts[1:]:
        if part in _PILLAR_IDX_MAP:
            result.append(_PILLAR_IDX_MAP[part])
    return tuple(sorted(set(result)))


def _pillar_name(idx: int | None) -> str:
    """Human-readable pillar name for 备注 strings."""
    if idx is None or idx >= len(_PILLAR_NAMES):
        return "未知柱"
    return _PILLAR_NAMES[idx]


def _is_ri_zhu(item: dict) -> bool:
    """True if this interaction touches the Day Pillar (index 2)."""
    return item.get("日柱特殊", False) or _cycle_pillar_index(item.get("组合", "")) == 2


def _apply_rule(
    item: dict,
    lock_type: str,
    cycle_label: str,
    lock_pillar_idx: int | None = None,
    lock_nb: str = "",
    lock_ns: str = "",
) -> None:
    """
    Apply a single CYCLE_PRIORITY_RULE_TABLE entry to item.
    Only downgrades (never upgrades). First causal remark wins.
    """
    itype = item.get("类型", "")
    new_strength = CYCLE_PRIORITY_RULE_TABLE.get((lock_type, itype))
    if new_strength is None:
        return
    current = item.get("强度")
    if current is not None:
        if STRENGTH_ORDER.get(new_strength, 99) <= STRENGTH_ORDER.get(current, 99):
            return  # would be an upgrade — skip
    item["强度"] = new_strength
    if "备注" not in item:
        template = CYCLE_REMARKS.get((lock_type, itype), "")
        if template:
            detail = item.get("组合明细", {})
            cb = detail.get(f"{cycle_label}支", "")
            cs = detail.get(f"{cycle_label}干", "")
            # natal partner of the suppressed item (not the lock item)
            _excl = {f"{cycle_label}支", f"{cycle_label}干"}
            nb_pillar = next((k for k in detail if k not in _excl), "")
            nb = detail.get(nb_pillar, "")
            item["备注"] = template.format(
                cycle=cycle_label,
                pillar=_pillar_name(lock_pillar_idx),
                cb=cb,
                cs=cs,
                lock_nb=lock_nb,
                lock_ns=lock_ns,
                nb_pillar=nb_pillar,
                nb=nb,
            )


def _check_branch_rooting(cycle_stem: str, cycle_branch: str) -> dict:
    """
    Check whether the cycle stem is rooted (通根) in the cycle branch.
    A stem is rooted when its element appears among the branch's hidden stems.
    """
    stem_elem = stem_elements.get(cycle_stem, "")
    hidden = [s for s, _ in TOMB_HIDDEN_STEMS.get(cycle_branch, [])]
    if not hidden:
        hidden = _NON_TOMB_HIDDEN.get(cycle_branch, [])
    hidden_elems = {stem_elements.get(s, "") for s in hidden}
    if stem_elem in hidden_elems:
        return {
            "strength": "有根",
            "interpretation": f"{cycle_stem}通根于{cycle_branch}，干力稳固",
        }
    return {
        "strength": "无根",
        "interpretation": f"{cycle_stem}在{cycle_branch}无根，干力虚浮",
    }


def _build_natal_protection(natal_zhis: list) -> set[int]:
    """
    Pre-compute which natal pillar indices are protected by a full natal
    三会 or 三合. Any incoming clash against a protected pillar is weakened.
    Returns set of protected natal pillar indices.

    Guard: require 3 DISTINCT branch values in the group, not just 3 pillars.
    A natal chart with duplicate branches (e.g. 午午寅) does not form a full
    三合 fire triad (寅午戌) even if 3 pillars are in the group.
    """
    protected: set[int] = set()
    for element, group in triple_he.items():
        distinct_in_group = {z for z in natal_zhis if z in group}
        if len(distinct_in_group) == len(group):  # all 3 distinct members present
            involved = [i for i, z in enumerate(natal_zhis) if z in group]
            protected.update(involved)
    for direction, group in directional_he.items():
        distinct_in_group = {z for z in natal_zhis if z in group}
        if len(distinct_in_group) == len(group):  # all 3 distinct members present
            involved = [i for i, z in enumerate(natal_zhis) if z in group]
            protected.update(involved)
    return protected


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Detection Helpers
# ══════════════════════════════════════════════════════════════════════════════


def _detect_cycle_structural(
    cycle_branch: str,
    natal_zhis: list[str],
    registry: CycleRegistry,
    cycle_label: str,
) -> None:
    """
    Detect structural group interactions: full 三会 / 三合 and partials
    (拱会 / 残会 from 三会, 半合 from 三合).

    A full structure (3 members present) is registered first.  If only 2
    members are present, the partial form is registered instead.

    Note on 半合 guard: the cycle branch may be the same as a natal branch
    (伏吟 case).  A branch cannot form 半合 with itself, so we skip when
    cycle_branch == natal_zhis[i].
    """

    # ── 三会 (directional group) ──────────────────────────────────────────────
    for element, group in directional_he.items():
        if cycle_branch not in group:
            continue
        direction = SAN_HUI_DIRECTION.get(frozenset(group), element)
        natal_matches = [(i, natal_zhis[i]) for i in range(4) if natal_zhis[i] in group]
        # Full 三会: cycle branch + 2 natal branches cover all 3 members
        needed = [b for b in group if b != cycle_branch]
        natal_in_group = {zhi for _, zhi in natal_matches}
        if all(b in natal_in_group for b in needed):
            participating = [i for i, z in natal_matches if z in needed]
            combo_pillars = (
                cycle_label
                + "-"
                + "-".join(_PILLAR_NAMES[k] for k in sorted(participating))
            )
            combo_detail = {_PILLAR_NAMES[k]: natal_zhis[k] for k in participating}
            combo_detail[f"{cycle_label}支"] = cycle_branch
            registry.register(
                {
                    "类型": "三会",
                    "元素": element,
                    "方位": direction,
                    "组合": combo_pillars,
                    "组合明细": combo_detail,
                    "涉及月柱": 1 in participating,
                    "状态": get_status("三会", {"key": "full"}),
                }
            )
        elif len(natal_in_group) == 1:
            # Partial 三会: cycle branch + exactly 1 distinct natal branch in group.
            # Find the first pillar that holds the matching branch.
            matching_branch = next(iter(natal_in_group))
            natal_idx = next(i for i, z in natal_matches if z == matching_branch)
            natal_branch = matching_branch
            cardinal = cardinal_branches.get(element)
            cardinal_present = (cycle_branch == cardinal) or (natal_branch == cardinal)
            itype_partial = "残会" if cardinal_present else "拱会"
            missing_branch = next(
                (b for b in group if b != cycle_branch and b != natal_branch), None
            )
            combo_pillars = f"{cycle_label}-{_PILLAR_NAMES[natal_idx]}"
            combo_detail = {
                _PILLAR_NAMES[natal_idx]: natal_branch,
                f"{cycle_label}支": cycle_branch,
            }
            entry = {
                "类型": itype_partial,
                "元素": element,
                "方位": direction,
                "组合": combo_pillars,
                "组合明细": combo_detail,
                "涉及月柱": natal_idx == 1,
                "待会": missing_branch or "无",
                "状态": get_status(
                    "三会", {"key": "residual" if cardinal_present else "arch"}
                ),
            }
            if not cardinal_present:
                entry["犹出"] = missing_branch or "无"
            registry.register(entry)

    # ── 三合 (triad group) ────────────────────────────────────────────────────
    for element, group in triple_he.items():
        if cycle_branch not in group:
            continue
        natal_matches = [(i, natal_zhis[i]) for i in range(4) if natal_zhis[i] in group]
        needed = [b for b in group if b != cycle_branch]
        natal_in_group = {zhi for _, zhi in natal_matches}

        if all(b in natal_in_group for b in needed):
            # Full 三合
            participating = [i for i, z in natal_matches if z in needed]
            combo_pillars = (
                cycle_label
                + "-"
                + "-".join(_PILLAR_NAMES[k] for k in sorted(participating))
            )
            combo_detail = {_PILLAR_NAMES[k]: natal_zhis[k] for k in participating}
            combo_detail[f"{cycle_label}支"] = cycle_branch
            registry.register(
                {
                    "类型": "三合",
                    "元素": element,
                    "组合": combo_pillars,
                    "组合明细": combo_detail,
                    "涉及月柱": 1 in participating,
                    "状态": get_status("三合", {"key": "full"}),
                    "邀出": "已全",
                }
            )
        else:
            # 半合: cycle branch + exactly 1 natal branch, different from cycle branch
            for natal_idx, natal_branch in natal_matches:
                if natal_branch == cycle_branch:
                    continue  # same branch — not a valid 半合
                all_branches = natal_zhis + [cycle_branch]
                cardinal = cardinal_branches.get(element)
                # State logic:
                # - 'strong':  cardinal is present anywhere in all branches
                # - 'arching': neither participant is cardinal (cardinal absent → arching toward it)
                # - The 'weak' case (else) is unreachable: if either participant IS the cardinal,
                #   then cardinal IS in all_branches → 'strong' fires first. Kept as fallback only.
                if cardinal in all_branches:
                    state, yao = "strong", "无"
                elif cycle_branch != cardinal and natal_branch != cardinal:
                    state, yao = "arching", cardinal
                else:
                    state, yao = (
                        "arching",
                        cardinal,
                    )  # fallback: unreachable in practice
                combo_pillars = f"{cycle_label}-{_PILLAR_NAMES[natal_idx]}"
                combo_detail = {
                    _PILLAR_NAMES[natal_idx]: natal_branch,
                    f"{cycle_label}支": cycle_branch,
                }
                registry.register(
                    {
                        "类型": "半合",
                        "元素": element,
                        "组合": combo_pillars,
                        "组合明细": combo_detail,
                        "涉及月柱": natal_idx == 1,
                        "状态": get_status(
                            "半合", {"element": element, "state": state}
                        ),
                        "邀出": yao,
                        "日柱特殊": natal_idx == 2,
                    }
                )


def _detect_cycle_pairwise(
    cycle_stem: str,
    cycle_branch: str,
    natal_gans: list[str],
    natal_zhis: list[str],
    registry: CycleRegistry,
    cycle_label: str,
    day_stem: str,
) -> None:
    """
    1×4 scan: cycle pillar vs each natal pillar.
    Registers all interactions found; suppression handled by priority filter.

    Interaction types detected per pillar:
        反吟, 伏吟, 六合, 六冲, 开库, 六害, 六破, 三刑, 暗合, 干支透合, 比和,
        天干合, 天干克, 天干冲
    """
    for i in range(4):
        target_gan = natal_gans[i]
        target_zhi = natal_zhis[i]
        pillar = _PILLAR_NAMES[i]
        combo = f"{cycle_label}-{pillar}"
        is_ri_zhu = i == 2
        combo_detail_branch = {f"{cycle_label}支": cycle_branch, pillar: target_zhi}
        combo_detail_stem = {f"{cycle_label}干": cycle_stem, pillar: target_gan}

        # ── 反吟 — stem AND branch both clash the same natal pillar ──────────
        stem_clashes_target = stem_clashes.get(cycle_stem) == target_gan
        if clash_map.get(cycle_branch) == target_zhi and stem_clashes_target:
            registry.register(
                {
                    "类型": "反吟",
                    "组合": combo,
                    "组合明细": {
                        f"{cycle_label}干": cycle_stem,
                        f"{cycle_label}支": cycle_branch,
                        pillar: f"{target_gan}{target_zhi}",
                    },
                    "状态": "干支皆反",
                    "涉及月柱": i == 1,
                    "日柱特殊": is_ri_zhu,
                }
            )

        # ── 伏吟 — cycle pillar exactly matches natal pillar ─────────────────
        if cycle_stem == target_gan and cycle_branch == target_zhi:
            registry.register(
                {
                    "类型": "伏吟",
                    "组合": combo,
                    "组合明细": {
                        f"{cycle_label}干": cycle_stem,
                        f"{cycle_label}支": cycle_branch,
                        pillar: f"{target_gan}{target_zhi}",
                    },
                    "状态": "干支皆同",
                    "涉及月柱": i == 1,
                    "日柱特殊": is_ri_zhu,
                }
            )

        # ── 六合 ─────────────────────────────────────────────────────────────
        if six_he_map.get(cycle_branch) == target_zhi:
            branches = sorted([cycle_branch, target_zhi])
            pk = (branches[0], branches[1])
            elem = six_he_element_map.get(pk, {}).get("primary", "")
            registry.register(
                {
                    "类型": "六合",
                    "组合": combo,
                    "组合明细": combo_detail_branch,
                    "元素": elem,

                    "涉及月柱": i == 1,
                    "日柱特殊": is_ri_zhu,
                    "状态": get_status(
                        "六合", {"key": "adjacent"}
                    ),
                }
            )

        # ── 六冲 / 开库 ───────────────────────────────────────────────────────
        if clash_map.get(cycle_branch) == target_zhi:
            if target_zhi in _TOMB_BRANCHES:
                # 开库: cycle branch is the key, natal branch is the tomb
                hidden_data = TOMB_HIDDEN_STEMS[target_zhi]
                rooting_info = _check_branch_rooting(cycle_stem, cycle_branch)
                ku_cang = [
                    {
                        "天干": stem,
                        "十神": _get_shi_shen_for_stem_pair(day_stem, stem),
                        "层次": ceng,
                        "释放性质": "pending",  # resolved in Pass 1 post-patch
                        "受阻": "pending",
                    }
                    for stem, ceng in hidden_data
                ]
                registry.register(
                    {
                        "类型": "开库",
                        "组合": combo,
                        "组合明细": combo_detail_branch,

                        "涉及月柱": i == 1,
                    "日柱特殊": is_ri_zhu,
                        "月令开库": (i == 1),
                        "库体": {
                            "库支": target_zhi,
                            "钥匙": cycle_branch,
                            "钥匙受困": "pending",  # sentinel — resolved after Pass 1
                        },
                        "库藏释放": ku_cang,
                        "根基强度": rooting_info["strength"],
                        "根基说明": rooting_info["interpretation"],
                    }
                )
            else:
                registry.register(
                    {
                        "类型": "六冲",
                        "组合": combo,
                        "组合明细": combo_detail_branch,

                        "涉及月柱": i == 1,
                    "日柱特殊": is_ri_zhu,
                        "状态": get_status(
                            "六冲", {"key": "adjacent"}
                        ),
                    }
                )

        # ── 六害 ─────────────────────────────────────────────────────────────
        if harm_map.get(cycle_branch) == target_zhi:
            registry.register(
                {
                    "类型": "六害",
                    "组合": combo,
                    "组合明细": combo_detail_branch,

                    "涉及月柱": i == 1,
                    "日柱特殊": is_ri_zhu,
                    "状态": get_status(
                        "六害", {"key": "adjacent"}
                    ),
                }
            )

        # ── 六破 ─────────────────────────────────────────────────────────────
        if break_map.get(cycle_branch) == target_zhi:
            registry.register(
                {
                    "类型": "六破",
                    "组合": combo,
                    "组合明细": combo_detail_branch,

                    "涉及月柱": i == 1,
                    "日柱特殊": is_ri_zhu,
                    "状态": get_status(
                        "六破", {"key": "adjacent"}
                    ),
                }
            )

        # ── 三刑 ──────────────────────────────────────────────────────────────
        # Guard: skip only exact 伏吟 (same stem AND branch) — already caught above.
        # Same-branch pairs with different stems are valid 自刑 candidates and
        # must be passed through to is_valid_punishment.
        is_fuyin = cycle_stem == target_gan and cycle_branch == target_zhi
        if not is_fuyin:
            punishment = is_valid_punishment(
                cycle_branch, target_zhi, natal_branches=natal_zhis
            )
            if punishment:
                pt = punishment["type"]
                code_map = {
                    "无恩之刑": "ungrateful",
                    "恃势之刑": "bullying",
                    "无礼之刑": "uncivilized",
                    "自刑": "self",
                }
                registry.register(
                    {
                        "类型": pt,
                        "组合": combo,
                        "组合明细": combo_detail_branch,

                        "涉及月柱": i == 1,
                    "日柱特殊": is_ri_zhu,
                        "状态": get_status(
                            "三刑",
                            {
                                "punishment_type": code_map.get(pt, "unknown"),
                                "is_full": punishment["is_full"],
                                "is_adjacent": True,
                            },
                        ),
                    }
                )

        # ── 暗合 ─────────────────────────────────────────────────────────────
        if target_zhi in hidden_stem_he.get(cycle_branch, set()):
            registry.register(
                {
                    "类型": "暗合",
                    "组合": combo,
                    "组合明细": combo_detail_branch,
                    "涉及月柱": i == 1,
                    "日柱特殊": is_ri_zhu,
                    "状态": get_status("暗合"),
                }
            )

        # ── 干支透合 — cycle stem combines with hidden stem in natal branch ──
        # Distinct from 暗合 (branch↔branch): this is cycle heavenly stem
        # covertly combining with a hidden stem (藏干) inside a natal branch.
        # e.g. cycle stem 甲 + natal 丑 (hides 己) → 甲己合 triggered covertly.
        _hidden_stems = LunarUtil.ZHI_HIDE_GAN.get(target_zhi, [])
        _hidden_labels = ["本气", "中气", "余气"]
        for _hi, _hs in enumerate(_hidden_stems):
            if stem_combines.get(cycle_stem) == _hs:
                registry.register(
                    {
                        "类型": "干支透合",
                        "组合": combo,
                        "组合明细": {
                            f"{cycle_label}干": cycle_stem,
                            f"{pillar}支": target_zhi,
                            "藏干": _hs,
                            "藏干层": _hidden_labels[_hi] if _hi < 3 else "余气",
                            "藏干十神": _get_shi_shen_for_stem_pair(day_stem, _hs),
                            "合化五行": _STEM_COMBINE_ELEMENT.get(cycle_stem, ""),
                        },
                        "涉及月柱": i == 1,
                    "日柱特殊": is_ri_zhu,
                        "状态": get_status("干支透合"),
                    }
                )
                break  # 天干合 is 1-to-1; one match per natal branch

        # ── 比和 ─────────────────────────────────────────────────────────────
        peer = is_valid_peer_combination(cycle_branch, target_zhi)
        if peer:
            registry.register(
                {
                    "类型": "比和",
                    "组合": combo,
                    "组合明细": combo_detail_branch,
                    "元素": peer["element"],

                    "涉及月柱": i == 1,
                    "日柱特殊": is_ri_zhu,
                    "状态": get_status(
                        "比和", {"key": "adjacent"}
                    ),
                }
            )

        # ── 天干合 ───────────────────────────────────────────────────────────
        if stem_combines.get(cycle_stem) == target_gan:
            rooting = _check_branch_rooting(cycle_stem, cycle_branch)
            registry.register(
                {
                    "类型": "天干合",
                    "组合": combo,
                    "组合明细": combo_detail_stem,
                    "涉及月柱": i == 1,
                    "日柱特殊": is_ri_zhu,
                    "状态": get_status("天干合"),
                    "根基强度": rooting["strength"],
                    "根基说明": rooting["interpretation"],
                }
            )

        # ── 天干冲 — mutual opposition (甲庚 乙辛 丙壬 丁癸) ─────────────────
        if stem_clashes.get(cycle_stem) == target_gan:
            rooting = _check_branch_rooting(cycle_stem, cycle_branch)
            registry.register(
                {
                    "类型": "天干冲",
                    "组合": combo,
                    "组合明细": combo_detail_stem,
                    "涉及月柱": i == 1,
                    "日柱特殊": is_ri_zhu,
                    "状态": get_status(
                        "天干冲", {"key": "adjacent"}
                    ),

                    "根基强度": rooting["strength"],
                    "根基说明": rooting["interpretation"],
                }
            )

        # ── 天干克 — directional five-element control (甲克戊/己 etc) ────────
        # 顺克: cycle stem controls natal stem (cycle exerts pressure outward)
        # 逆克: natal stem controls cycle stem (natal resists/suppresses cycle)
        _ke_cycle_to_natal = (cycle_stem, target_gan) in stem_controls
        _ke_natal_to_cycle = (target_gan, cycle_stem) in stem_controls
        if _ke_cycle_to_natal or _ke_natal_to_cycle:
            rooting = _check_branch_rooting(cycle_stem, cycle_branch)
            registry.register(
                {
                    "类型": "天干克",
                    "组合": combo,
                    "组合明细": combo_detail_stem,
                    "克向": "顺克" if _ke_cycle_to_natal else "逆克",
                    "涉及月柱": i == 1,
                    "日柱特殊": is_ri_zhu,
                    "状态": get_status(
                        "天干克", {"key": "adjacent"}
                    ),

                    "根基强度": rooting["strength"],
                    "根基说明": rooting["interpretation"],
                }
            )


def _detect_cycle_gong_gong(
    cycle_branch: str,
    natal_zhis: list[str],
    registry: CycleRegistry,
    cycle_label: str,
) -> None:
    """
    Detect positional 共拱: cycle branch + one natal branch sandwich a missing
    branch between them on the 12-branch cycle (A–C–B consecutive, C absent).

    Guard: the arched-toward branch must not be the cycle branch itself, and
    must not already be present in the natal chart or as the cycle branch.

    Structural 共拱 (multi-partial convergence) is intentionally omitted here
    because in a 1×4 scan the cycle branch can only pair with one natal branch
    at a time per positional arch — multi-partial convergence requires three or
    more branches, which is handled by the structural detection above.
    """
    all_present = set(natal_zhis) | {cycle_branch}

    for missing_branch, (a, b) in POSITIONAL_ARCH_MAP.items():
        if missing_branch in all_present:
            continue  # branch is not missing
        if missing_branch == cycle_branch:
            continue  # cannot arch toward oneself

        # Check if cycle_branch and a natal branch form the flanking pair.
        # Iterate all matching natal indices — a branch may appear in multiple pillars.
        for pair in [(a, b), (b, a)]:
            lo, hi = pair
            if cycle_branch == lo:
                for natal_idx, natal_zhi in enumerate(natal_zhis):
                    if natal_zhi == hi:
                        combo = f"{cycle_label}-{_PILLAR_NAMES[natal_idx]}"
                        clashed = bool(
                            clash_map.get(cycle_branch) in all_present
                            or clash_map.get(natal_zhi) in all_present
                        )
                        registry.register(
                            {
                                "类型": "共拱",
                                "框架": f"岁运拱{missing_branch}",
                                "组合": combo,
                                "组合明细": {
                                    _PILLAR_NAMES[natal_idx]: hi,
                                    cycle_label: lo,
                                },
                                "拱向": missing_branch,
                                "涉及月柱": natal_idx == 1,
                                "混杂": clashed,
                                "日柱特殊": natal_idx == 2,
                            }
                        )
            elif cycle_branch == hi:
                for natal_idx, natal_zhi in enumerate(natal_zhis):
                    if natal_zhi == lo:
                        combo = f"{cycle_label}-{_PILLAR_NAMES[natal_idx]}"
                        clashed = bool(
                            clash_map.get(cycle_branch) in all_present
                            or clash_map.get(natal_zhi) in all_present
                        )
                        registry.register(
                            {
                                "类型": "共拱",
                                "框架": f"岁运拱{missing_branch}",
                                "组合": combo,
                                "组合明细": {
                                    _PILLAR_NAMES[natal_idx]: lo,
                                    cycle_label: hi,
                                },
                                "拱向": missing_branch,
                                "涉及月柱": natal_idx == 1,
                                "混杂": clashed,
                                "日柱特殊": natal_idx == 2,
                            }
                        )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Priority Filter
# ══════════════════════════════════════════════════════════════════════════════

_STEM_TYPES = {"天干合", "天干克", "天干冲"}
_BRANCH_TYPES = {
    "反吟",
    "伏吟",
    "三会",
    "三合",
    "六冲",
    "开库",
    "六合",
    "拱会",
    "残会",
    "半合",
    "共拱",
    "六害",
    "六破",
    "无恩之刑",
    "恃势之刑",
    "无礼之刑",
    "自刑",
    "暗合",
    "干支透合",
    "比和",
}
_STRUCTURAL_TYPES = {"三会", "三合"}
_TOMB_CLASH_TYPES = {"六冲", "开库"}


def _pre_pass(
    registry: CycleRegistry,
    cycle_label: str,
) -> set[int]:
    """
    Pre-Pass: 反吟 / 伏吟 — mark turbulent natal pillars.

    反吟 and 伏吟 are assigned 强势主流 unconditionally.
    Returns the set of turbulent natal pillar indices (for post-pass modifier).

    NOTE: turbulence does NOT absorb other interactions here — it is applied
    as a one-level downgrade AFTER all passes complete (see _turbulence_pass).
    This preserves methodological accuracy: a turbulent pillar's bonds still
    exist; they merely operate in a destabilised environment.
    """
    turbulent: set[int] = set()
    fuyin_pillars: set[int] = set()  # natal pillar indices that have 伏吟

    for item in registry.all_items():
        itype = item.get("类型")
        if itype in ("反吟", "伏吟"):
            item["强度"] = "强势主流"
            detail = item.get("组合明细", {})
            cs = detail.get(f"{cycle_label}干", "")
            cb = detail.get(f"{cycle_label}支", "")
            if itype == "反吟":
                item.setdefault(
                    "备注", f"反吟：干支皆反，该柱位被{cycle_label}（{cs}{cb}）完全主导，极度动荡"
                )
            else:
                item.setdefault(
                    "备注", f"伏吟：干支皆同，该柱位被{cycle_label}（{cs}{cb}）完全占据，停滞呻吟"
                )
            idx = _cycle_pillar_index(item.get("组合", ""))
            if idx is not None:
                turbulent.add(idx)
                if itype == "伏吟":
                    fuyin_pillars.add(idx)

    # Absorb 比和 on 伏吟 pillars: when the cycle branch exactly matches a natal
    # branch (伏吟), the same-element resonance (比和) is trivially true and
    # conveys no independent information beyond 伏吟 itself.
    for item in registry.all_items():
        if item.get("类型") != "比和":
            continue
        idx = _cycle_pillar_index(item.get("组合", ""))
        if idx in fuyin_pillars:
            item["强度"] = "消融吸收"
            item.setdefault("备注", "比和被伏吟吸收：同柱同支，比和信息已含于伏吟之内")
            registry.absorb(item["_iid"])

    return turbulent


def _pass1_identity(
    registry: CycleRegistry,
    cycle_label: str,
) -> None:
    """
    Pass 1: Identity Pass — assign actor locks.

    Stem priority:  天干合 > 天干克 > 天干冲
    Branch priority: STRUCTURAL (三会/三合) > PRIMARY_六合 > PRIMARY_六冲/开库

    Two-phase design (mirrors natal _pass3_stems fix):
      Phase 1 — determine lock_type and winner for each actor; call registry.lock()
      Phase 2 — apply rule table (only after ALL locks are assigned)

    Post-Phase-1 patch: resolve 开库 钥匙受困 sentinel based on branch lock type.
    """
    # ── Phase 1a: Stem actor locking ─────────────────────────────────────────
    stem = registry.stem_actor
    he = registry.get_by_type(["天干合"], actor="stem")
    ke = registry.get_by_type(
        ["天干克"], actor="stem"
    )  # directional control (higher priority)
    chong = registry.get_by_type(
        ["天干冲"], actor="stem"
    )  # mutual opposition (lower priority)

    stem_winner: dict | None = None
    if he:
        stem_winner = he[0]
        stem.lock_type = "STEM_天干合"
    elif ke:
        # 天干克 outranks 天干冲; prefer Day Master interaction
        ri_zhu_ke = [it for it in ke if _is_ri_zhu(it)]
        stem_winner = ri_zhu_ke[0] if ri_zhu_ke else ke[0]
        stem.lock_type = "STEM_天干克"
    elif chong:
        ri_zhu_chong = [it for it in chong if _is_ri_zhu(it)]
        stem_winner = ri_zhu_chong[0] if ri_zhu_chong else chong[0]
        stem.lock_type = "STEM_天干冲"

    if stem_winner is not None:
        stem.lock_item_id = stem_winner["_iid"]
        registry.lock(stem_winner["_iid"])

    # ── Phase 1b: Branch actor locking ───────────────────────────────────────
    branch = registry.branch_actor

    structural = registry.get_by_type(list(_STRUCTURAL_TYPES), actor="branch")
    liu_he = registry.get_by_type(["六合"], actor="branch")
    liu_chong = registry.get_by_type(["六冲", "开库"], actor="branch")

    branch_winner: dict | None = None
    if structural:
        branch_winner = structural[0]
        branch.lock_type = "STRUCTURAL"
    elif liu_he:
        ri_zhu_he = [it for it in liu_he if _is_ri_zhu(it)]
        branch_winner = ri_zhu_he[0] if ri_zhu_he else liu_he[0]
        branch.lock_type = "PRIMARY_六合"
    elif liu_chong:
        ri_zhu_chong = [it for it in liu_chong if _is_ri_zhu(it)]
        branch_winner = ri_zhu_chong[0] if ri_zhu_chong else liu_chong[0]
        branch.lock_type = "PRIMARY_六冲"

    if branch_winner is not None:
        branch.lock_item_id = branch_winner["_iid"]
        registry.lock(branch_winner["_iid"])

    # ── Post-Phase-1 patch: resolve 开库 sentinels ───────────────────────────
    # Determine whether the cycle branch (the key) is trapped by another bond.
    # free            — branch lock is 六冲 (the 开库 itself) or no lock
    # partially_trapped — branch locked by STRUCTURAL (三会/三合 absorbs some energy)
    # fully_trapped   — branch locked by PRIMARY_六合 (bilateral lock; key immobilised)
    if branch.lock_type == "STRUCTURAL":
        trapped_state = "partially_trapped"
    elif branch.lock_type == "PRIMARY_六合":
        trapped_state = "fully_trapped"
    else:
        trapped_state = "free"  # PRIMARY_六冲 (the 开库 is the lock) or no lock

    for item in registry.all_items():
        if item.get("类型") != "开库":
            continue
        ku_ti = item.get("库体", {})
        if ku_ti.get("钥匙受困") != "pending":
            continue
        ku_ti["钥匙受困"] = trapped_state
        for entry in item.get("库藏释放", []):
            ceng = entry.get("层次", "余气")
            entry["释放性质"] = KAIKU_RELEASE_NATURE.get(
                (trapped_state, ceng), "受阻封印"
            )
            entry["受阻"] = trapped_state == "fully_trapped"


def _pass2_conflict(
    registry: CycleRegistry,
    cycle_label: str,
    natal_gans: list[str],
    natal_zhis: list[str],
) -> None:
    """
    Pass 2: Conflict Pass — table-driven downgrade of non-winner interactions.

    Two-phase stem processing (lock first, remark second, sorted by priority)
    prevents a weaker stem lock from writing a misleading remark on an item
    whose real suppressor is a stronger lock on the same actor.

    Branch processing is single-actor so ordering is not an issue there.
    """
    stem = registry.stem_actor
    branch = registry.branch_actor

    # ── Stem conflicts ────────────────────────────────────────────────────────
    if stem.lock_type is not None:
        lock_pillar_idx = _cycle_pillar_index(
            registry.item_by_id(stem.lock_item_id).get("组合", "")
            if stem.lock_item_id
            else ""
        )
        lock_ns = natal_gans[lock_pillar_idx] if lock_pillar_idx is not None else ""
        for item in registry.get_by_type(
            list(_STEM_TYPES), actor="stem", active_only=False
        ):
            if item["_iid"] == stem.lock_item_id:
                continue  # winner — handled in Pass 3
            _apply_rule(item, stem.lock_type, cycle_label, lock_pillar_idx, lock_ns=lock_ns)

    # ── Cross-actor: stem lock → 干支透合 ────────────────────────────────────
    # 干支透合 is wired to the branch actor but must also be suppressed when
    # the cycle stem is locked in a direct 天干合 (贪合忘合: stem occupied, covert
    # bond absorbed). Branch conflict loop below only applies branch.lock_type
    # rules, so this cross-actor suppression must be handled explicitly here.
    if stem.lock_type is not None:
        stem_lock_pillar_idx = _cycle_pillar_index(
            (registry.item_by_id(stem.lock_item_id) or {}).get("组合", "")
            if stem.lock_item_id
            else ""
        )
        stem_lock_ns = natal_gans[stem_lock_pillar_idx] if stem_lock_pillar_idx is not None else ""
        for item in registry.active_items():
            if item.get("类型") != "干支透合":
                continue
            _apply_rule(item, stem.lock_type, cycle_label, stem_lock_pillar_idx, lock_ns=stem_lock_ns)

    # ── Branch conflicts ──────────────────────────────────────────────────────
    if branch.lock_type is not None:
        lock_pillar_idx = _cycle_pillar_index(
            registry.item_by_id(branch.lock_item_id).get("组合", "")
            if branch.lock_item_id
            else ""
        )
        lock_nb = natal_zhis[lock_pillar_idx] if lock_pillar_idx is not None else ""
        for item in registry.active_items():
            itype = item.get("类型", "")
            if itype in _STEM_TYPES:
                continue  # stem interactions handled above
            if itype in ("反吟", "伏吟"):
                continue  # pre-pass items are frozen
            if item["_iid"] == branch.lock_item_id:
                continue  # winner — handled in Pass 3
            _apply_rule(item, branch.lock_type, cycle_label, lock_pillar_idx, lock_nb=lock_nb)


def _pass3_winners(
    registry: CycleRegistry,
    natal_zhis: list[str],
    natal_protected: set[int],
    cycle_label: str,
) -> None:
    """
    Pass 3: Assign 强势主流 to winners with contextual remarks.

    Special cases:
      - 六冲 winner: check natal 三会/三合 protection.
      - 开库 winner: strength from KAIKU_STRENGTH by 钥匙受困 state.
      - Cross-actor annotation: 合中有冲 / 冲中有合 added as 交织 field.
    """
    stem = registry.stem_actor
    branch = registry.branch_actor

    # ── Stem winner ───────────────────────────────────────────────────────────
    if stem.lock_item_id is not None:
        item = registry.item_by_id(stem.lock_item_id)
        if item is None:
            return
        itype = item.get("类型", "")
        is_ri = _is_ri_zhu(item)
        pillar_idx = _cycle_pillar_index(item.get("组合", ""))
        pillar = _pillar_name(pillar_idx)
        detail = item.get("组合明细", {})
        cs = detail.get(f"{cycle_label}干", "")
        ns = detail.get(pillar, "")

        if itype == "天干合":
            item["强度"] = "强势主流"
            item.setdefault(
                "备注",
                (
                    f"{cycle_label}干{cs}合绑日主，为干元首要合化，意义重大"
                    if is_ri
                    else f"{cycle_label}干{cs}合绑{pillar}{ns}，干元主要合化激活"
                ),
            )
        elif itype == "天干克":
            item["强度"] = "强势主流" if item.get("根基强度") == "有根" else "显著影响"
            ke_xiang = item.get("克向", "顺克")
            if is_ri:
                item.setdefault(
                    "备注",
                    (
                        f"{cycle_label}干{cs}顺克日主，外力克制日元，压力极大"
                        if ke_xiang == "顺克"
                        else f"日主逆克{cycle_label}干{cs}，命主元气抑制来运，被压而不从"
                    ),
                )
            else:
                item.setdefault(
                    "备注",
                    (
                        f"{cycle_label}干{cs}顺克{pillar}{ns}，克力向外施压"
                        if ke_xiang == "顺克"
                        else f"{pillar}{ns}逆克{cycle_label}干{cs}，来运受制，力道受阻"
                    ),
                )
        elif itype == "天干冲":
            item["强度"] = "强势主流"
            item.setdefault(
                "备注",
                (
                    f"{cycle_label}干{cs}冲撞日主，干元主要冲力激活，动荡剧烈"
                    if is_ri
                    else f"{cycle_label}干{cs}冲击{pillar}{ns}，干元主要冲力激活"
                ),
            )

    # ── Branch winner ─────────────────────────────────────────────────────────
    if branch.lock_item_id is not None:
        item = registry.item_by_id(branch.lock_item_id)
        if item is None:
            return
        itype = item.get("类型", "")
        is_ri = _is_ri_zhu(item)
        pillar_idx = _cycle_pillar_index(item.get("组合", ""))
        pillar = _pillar_name(pillar_idx)
        detail = item.get("组合明细", {})
        cb = detail.get(f"{cycle_label}支", "")
        nb = detail.get(pillar, "")

        if itype in _STRUCTURAL_TYPES:
            item["强度"] = "强势主流"
            item.setdefault(
                "备注", f"{itype}方位场成局，{cycle_label}支参与结构主导，全局牵引"
            )

        elif itype == "六合":
            item["强度"] = "强势主流"
            item.setdefault(
                "备注",
                (
                    f"{cycle_label}支{cb}六合日柱，支元首要合化，与日主紧密相系"
                    if is_ri
                    else f"{cycle_label}支{cb}六合{pillar}{nb}，支元主要合化激活"
                ),
            )

        elif itype in ("六冲", "开库"):
            if itype == "六冲":
                if pillar_idx is not None and pillar_idx in natal_protected:
                    item["强度"] = "大幅衰减"
                    item["备注"] = f"命盘三会/三合护{pillar}{nb}，{cycle_label}支{cb}冲力大幅衰减"
                else:
                    item["强度"] = "强势主流"
                    item.setdefault(
                        "备注", f"{cycle_label}支{cb}六冲{pillar}{nb}，冲力完整激活，结构破位"
                    )
            else:  # 开库
                trapped = item.get("库体", {}).get("钥匙受困", "free")
                item["强度"] = KAIKU_STRENGTH.get(trapped, "强势主流")
                if not item.get("备注"):
                    if trapped == "free":
                        item["备注"] = (
                            f"{cycle_label}支{cb}开{item.get('库体',{}).get('库支','')}库，"
                            f"钥匙自由，库藏主气涌现"
                        )
                    elif trapped == "partially_trapped":
                        item["备注"] = (
                            f"{cycle_label}支{cb}开{item.get('库体',{}).get('库支','')}库，"
                            f"钥匙受三会/三合牵制，库藏受压渗出"
                        )
                    else:
                        item["备注"] = f"{cycle_label}支{cb}开库钥匙已被六合锁定，库门封闭"

    # ── Cross-actor annotation: 合中有冲 / 冲中有合 ───────────────────────────
    # If stem is bonded (天干合) while branch clashes the same natal pillar,
    # or stem clashes while branch bonds, annotate both winners with 交织.
    if stem.lock_item_id and branch.lock_item_id:
        s_item = registry.item_by_id(stem.lock_item_id)
        b_item = registry.item_by_id(branch.lock_item_id)
        s_pillar = _cycle_pillar_index(s_item.get("组合", ""))
        b_pillar = _cycle_pillar_index(b_item.get("组合", ""))
        if s_pillar == b_pillar:  # same natal pillar affected by both actors
            s_type = s_item.get("类型", "")
            b_type = b_item.get("类型", "")
            if s_type == "天干合" and b_type in ("六冲", "开库"):
                note = "合中有冲：干合支冲同柱，合力不稳，冲力受制"
                s_item.setdefault("交织", note)
                b_item.setdefault("交织", note)
            elif s_type in ("天干克", "天干冲") and b_type == "六合":
                note = "冲中有合：支合干冲同柱，合力缓冲冲克之势"
                s_item.setdefault("交织", note)
                b_item.setdefault("交织", note)


def _pass4_group(
    registry: CycleRegistry,
    cycle_label: str,
) -> None:
    """
    Pass 4: Group / Environment Pass — residual group interactions.

    Covers items not handled by Passes 1–3:
      三会 / 三合 — secondary structural when cycle branch belongs to two groups
      半合 / 拱会 / 残会 / 共拱 — capped by branch lock
      比和                      — always 显著影响
      暗合                      — always 显著影响
      六害 / 六破 / 刑          — default 显著影响 when no branch lock

    Secondary structural (三会/三合) note:
      A cycle branch can belong to at most one 三会 direction AND one 三合 element
      simultaneously (e.g. 寅 in 木方 and 寅午戌). When both form full structures,
      Pass 1 locks whichever was registered first; the other remains ACTIVE here.
      Both are full, real structures — the secondary is also 强势主流.
      CYCLE_PRIORITY_RULE_TABLE intentionally has no entry for
      (STRUCTURAL, 三会/三合): full structures are co-active, never suppressed.
    """
    branch = registry.branch_actor
    lock = branch.lock_type

    for item in registry.active_items():
        if item.get("强度") is not None:
            continue  # already assigned by an earlier pass
        itype = item.get("类型", "")

        if itype in ("三会", "三合"):
            # Secondary structural: cycle branch participates in two full group structures.
            # Both are valid and mutually reinforcing — assign 强势主流 with context remark.
            item["强度"] = "强势主流"
            winner_item = (
                registry.item_by_id(branch.lock_item_id)
                if branch.lock_item_id
                else None
            )
            winner_type = winner_item.get("类型", "") if winner_item else ""
            item.setdefault(
                "备注",
                f"{cycle_label}支双重结构力：同时参与{winner_type}与{itype}，两局共力，势能叠加",
            )

        elif itype in ("半合", "拱会", "残会", "共拱"):
            if lock == "PRIMARY_六合":
                item["强度"] = "显著影响"
                item.setdefault("备注", f"{cycle_label}支已六合，此{itype}仅作背景共鸣")
            elif lock in ("STRUCTURAL", "PRIMARY_六冲"):
                item["强度"] = "大幅衰减"
                item.setdefault(
                    "备注", f"{cycle_label}支已被{lock}锁定，此{itype}势力被吸收"
                )
            else:
                # No branch lock — independent activation
                if itype == "共拱" and item.get("混杂"):
                    item["强度"] = "显著影响"
                    item.setdefault(
                        "备注", f"共拱：{cycle_label}支与命盘联拱缺位，参与支遭冲，框架混杂衰减"
                    )
                else:
                    item["强度"] = "强势主流"
                    if itype == "半合":
                        item.setdefault("备注", f"半合独立激活，{cycle_label}支部分合力")
                    elif itype == "拱会":
                        item.setdefault("备注", f"拱会：{cycle_label}支与命盘虚拱方位")
                    elif itype == "残会":
                        item.setdefault(
                            "备注", f"残会：{cycle_label}支与命盘残会，方位带头"
                        )
                    else:
                        item.setdefault("备注", f"共拱：{cycle_label}支与命盘联拱缺位")

        elif itype == "比和":
            item["强度"] = "显著影响"
            _pillar_idx = _cycle_pillar_index(item.get("组合", ""))
            _pillar = _pillar_name(_pillar_idx)
            _detail = item.get("组合明细", {})
            cb = _detail.get(f"{cycle_label}支", "")
            nb = _detail.get(_pillar, "")
            item.setdefault("备注", f"比和：{cycle_label}支{cb}与{_pillar}{nb}同气共鸣，背景助力")

        elif itype == "暗合":
            item["强度"] = "显著影响"
            _pillar_idx = _cycle_pillar_index(item.get("组合", ""))
            _pillar = _pillar_name(_pillar_idx)
            _detail = item.get("组合明细", {})
            cb = _detail.get(f"{cycle_label}支", "")
            nb = _detail.get(_pillar, "")
            item.setdefault("备注", f"{cycle_label}支{cb}与{_pillar}{nb}暗合，潜流影响")

        elif itype == "干支透合":
            item["强度"] = "显著影响"
            _pillar_idx = _cycle_pillar_index(item.get("组合", ""))
            _pillar = _pillar_name(_pillar_idx)
            _detail = item.get("组合明细", {})
            cs = _detail.get(f"{cycle_label}干", "")
            nb = _detail.get(f"{_pillar}支", "")
            hidden_stem = _detail.get("藏干", "")
            hidden_label = _detail.get("藏干层", "")
            item.setdefault(
                "备注",
                f"干支透合：{cycle_label}干{cs}与{_pillar}支{nb}内{hidden_label}藏干{hidden_stem}暗合，潜流感应",
            )

        elif itype in ("六害", "六破"):
            item["强度"] = "显著影响"
            _pillar_idx = _cycle_pillar_index(item.get("组合", ""))
            _pillar = _pillar_name(_pillar_idx)
            _detail = item.get("组合明细", {})
            cb = _detail.get(f"{cycle_label}支", "")
            nb = _detail.get(_pillar, "")
            item.setdefault("备注", f"{cycle_label}支{cb}{itype}{_pillar}{nb}，摩擦显现")

        elif itype in ("无恩之刑", "恃势之刑", "无礼之刑", "自刑"):
            item["强度"] = "强势主流"
            _pillar_idx = _cycle_pillar_index(item.get("组合", ""))
            _pillar = _pillar_name(_pillar_idx)
            _detail = item.get("组合明细", {})
            cb = _detail.get(f"{cycle_label}支", "")
            nb = _detail.get(_pillar, "")
            item.setdefault("备注", f"{cycle_label}支{cb}{itype}{_pillar}{nb}，刑力主导")

        else:
            # Fallback
            item.setdefault("强度", "显著影响")
            item.setdefault("备注", "独立激活")


def _turbulence_pass(
    registry: CycleRegistry,
    turbulent: set[int],
) -> None:
    """
    Post-pass turbulence modifier.

    Applied after all four passes. For each item touching a turbulent natal
    pillar, downgrade 强度 by one level. Floor: 大幅衰减.

    Rules:
      - 反吟 / 伏吟 items are exempt (they ARE the turbulence source)
      - Items already at 消融吸收 are exempt (already nullified)
      - Stacking is disabled: even if multiple turbulent pillars are touched,
        the downgrade applies exactly once
    """
    if not turbulent:
        return

    for item in registry.all_items():
        itype = item.get("类型", "")
        if itype in ("反吟", "伏吟"):
            continue
        current = item.get("强度")
        if current == "消融吸收" or current is None:
            continue
        # Check if any natal pillar this item touches is turbulent
        indices = _natal_indices_from_combo(item.get("组合", ""))
        if any(idx in turbulent for idx in indices):
            item["强度"] = _TURBULENCE_DOWNGRADE.get(current, current)
            item.setdefault("备注_动荡", "所涉柱位处于反吟/伏吟动荡状态，作用力降一级")


def apply_cycle_master_priority(
    registry: CycleRegistry,
    natal_gans: list[str],
    natal_zhis: list[str],
    cycle_label: str,
) -> list[dict]:
    """
    Four-Pass Priority Filter orchestrator for external cycle pillars.

    PRE-PASS : 反吟 / 伏吟 — mark turbulent pillars, assign 强势主流
    PASS 1   : Identity — actor locking, 开库 sentinel resolution
    PASS 2   : Conflict — table-driven downgrade of non-winners
    PASS 3   : Winners  — assign 强势主流 with contextual remarks
    PASS 4   : Group    — residual group / environment interactions
    POST-PASS: Turbulence — one-level downgrade for turbulent pillar items

    Returns all items sorted by CYCLE_TIER_ORDER.
    """
    natal_protected = _build_natal_protection(natal_zhis)

    turbulent = _pre_pass(registry, cycle_label)
    _pass1_identity(registry, cycle_label)
    _pass2_conflict(registry, cycle_label, natal_gans, natal_zhis)
    _pass3_winners(registry, natal_zhis, natal_protected, cycle_label)
    _pass4_group(registry, cycle_label)
    _turbulence_pass(registry, turbulent)

    result = registry.all_items()
    result.sort(key=lambda x: CYCLE_TIER_ORDER.get(x.get("类型", ""), 99))
    return result


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Output Assembly
# ══════════════════════════════════════════════════════════════════════════════

_OUTPUT_STRIP_KEYS = {"_iid", "_synthetic"}

_CYCLE_TIER1 = {"三会", "三合", "六冲", "开库", "六合", "反吟", "伏吟"}
_CYCLE_TIER2 = {"共拱", "比和", "拱会", "残会", "半合", "天干合", "天干克", "天干冲"}
_CYCLE_TIER3 = {"无恩之刑", "恃势之刑", "无礼之刑", "自刑", "六害", "六破", "暗合", "干支透合"}


def _build_cycle_pillar_dynamics(items: list[dict]) -> dict:
    """
    Distribute interactions into per-natal-pillar tier buckets.
    Strips internal keys (_iid, _synthetic) in-place on first encounter.
    """
    dynamics = {
        i: {"第一梯队_纲领层": [], "第二梯队_气势层": [], "第三梯队_琐碎层": []}
        for i in range(4)
    }
    stripped: set[int] = set()
    added: set[tuple] = set()

    for item in items:
        itype = item.get("类型", "")
        indices = _natal_indices_from_combo(item.get("组合", ""))
        if not indices:
            continue

        if itype in _CYCLE_TIER1:
            tier = "第一梯队_纲领层"
        elif itype in _CYCLE_TIER2:
            tier = "第二梯队_气势层"
        else:
            tier = "第三梯队_琐碎层"

        item_id = item["_iid"]
        # Strip internal keys once per item
        if item_id not in stripped:
            for k in _OUTPUT_STRIP_KEYS:
                item.pop(k, None)
            stripped.add(item_id)

        for idx in indices:
            key = (idx, tier, item_id)
            if key not in added:
                dynamics[idx][tier].append(item)
                added.add(key)

    return {_PILLAR_NAMES[k]: dynamics[k] for k in range(4)}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Orchestrator
# ══════════════════════════════════════════════════════════════════════════════


def get_cycle_interactions(
    cycle_stem: str,
    cycle_branch: str,
    natal_chart: dict,
    cycle_label: str = "大运",
) -> dict:
    """
    Detect all interactions between one external cycle pillar and the natal chart.

    This is the single shared entry point for all cycle types:
        _detect_cycle_interactions("甲", "子", gans, zhis, "大运")
        _detect_cycle_interactions("丙", "午", gans, zhis, "流年")
        _detect_cycle_interactions("庚", "申", gans, zhis, "小运")
        _detect_cycle_interactions("壬", "戌", gans, zhis, "流月")

        Args:
                cycle_stem   : Heavenly stem of the external pillar
                cycle_branch : Earthly branch of the external pillar
                natal_chart  : dict with natal pillars, e.g.
                                             {
                                                 "year": {"stem":..., "branch":...},
                                                 "month": {"stem":..., "branch":...},
                                                 "day": {"stem":..., "branch":...},
                                                 "hour": {"stem":..., "branch":...},
                                             }
                cycle_label  : Display label for this cycle type (used in combo strings
                                             and 备注 templates). Default "大运".

    Returns:
        {
            "作用": {
                "关系总览": [...],         # active interactions summary
                "柱位动态": {...},          # per-pillar tier buckets
                "判定优先级": {...},        # tier classification reference
            }
        }
    """
    if not cycle_stem or not cycle_branch:
        return {"作用": {"关系总览": [], "柱位动态": {}, "判定优先级": {}}}

    # Build natal_gans and natal_zhis from natal_chart dict
    if not isinstance(natal_chart, dict):
        raise ValueError("natal_chart must be a dict with keys year/month/day/hour")
    try:
        natal_gans = [
            natal_chart["year"]["stem"],
            natal_chart["month"]["stem"],
            natal_chart["day"]["stem"],
            natal_chart["hour"]["stem"],
        ]
        natal_zhis = [
            natal_chart["year"]["branch"],
            natal_chart["month"]["branch"],
            natal_chart["day"]["branch"],
            natal_chart["hour"]["branch"],
        ]
    except KeyError as e:
        raise ValueError(f"Invalid natal_chart structure; missing key: {e}") from e

    day_stem = natal_gans[2]
    registry = CycleRegistry()

    # ── Detection ─────────────────────────────────────────────────────────────
    # Structural detection first (三会/三合/半合/拱会/残会) — these may influence
    # branch actor locking in Pass 1.
    _detect_cycle_structural(cycle_branch, natal_zhis, registry, cycle_label)

    # Pairwise 1×4 scan (all other interaction types)
    _detect_cycle_pairwise(
        cycle_stem,
        cycle_branch,
        natal_gans,
        natal_zhis,
        registry,
        cycle_label,
        day_stem,
    )

    # 共拱 detection — after structural, so structural registrations are visible
    _detect_cycle_gong_gong(cycle_branch, natal_zhis, registry, cycle_label)

    # ── Priority filter ───────────────────────────────────────────────────────
    filtered = apply_cycle_master_priority(registry, natal_gans, natal_zhis, cycle_label)

    # ── Output assembly ───────────────────────────────────────────────────────
    # _build_cycle_pillar_dynamics strips _iid/_synthetic in-place
    pillar_dynamics = _build_cycle_pillar_dynamics(filtered)

    # 关系总览: 强势主流 / 显著影响 items only
    summary: list[str] = []
    seen: set[str] = set()
    for item in filtered:
        if item.get("强度") not in ("强势主流", "显著影响"):
            continue
        detail_vals = "".join(item.get("组合明细", {}).values())
        label = item.get("状态") or f"{item.get('类型', '')}({detail_vals})"
        if label not in seen:
            summary.append(label)
            seen.add(label)

    return {
        "作用": {
            "关系总览": summary,
            "柱位动态": pillar_dynamics,
            "判定优先级": {
                "第一梯队_纲领层": [
                    "反吟",
                    "伏吟",
                    "三会",
                    "三合",
                    "六冲",
                    "开库",
                    "六合",
                ],
                "第二梯队_气势层": [
                    "共拱",
                    "拱会",
                    "残会",
                    "半合",
                    "比和",
                    "天干合",
                    "天干克",
                    "天干冲",
                ],
                "第三梯队_琐碎层": [
                    "无恩之刑",
                    "恃势之刑",
                    "无礼之刑",
                    "自刑",
                    "六害",
                    "六破",
                    "暗合",
                    "干支透合",
                ],
            },
        },
        "_raw_priority_list": filtered,
    }

# --- EXECUTION ---

if __name__ == "__main__":
    # python -m src.astronomer_calculations.cycle_interactions
    import json
    from lunar_python import Solar
    from datetime import datetime
    from src.utils.logging import configure_logging, get_logger
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time

    # python -m src.astronomer_calculations.cycle_interactions

    configure_logging()
    logger = get_logger(__name__)

    # --- Birthday examples (uncomment one) ---

    # Desmond
    # solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)
    # datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)
    # tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)

    # Corinne
    solar_birthday = Solar.fromYmdHms(1987, 6, 3, 12, 6, 0)
    tst_birthday, _ = get_true_solar_time(datetime(1987, 6, 3, 12, 6, 0), 1.4759, 103.808053)

    # Lara
    # solar_birthday = Solar.fromYmdHms(2025, 7, 31, 9, 10, 0)
    # tst_birthday, _ = get_true_solar_time(datetime(2025, 7, 31, 9, 10, 0), 1.3253, 103.808053)

    logger.info("阳历生日: " + solar_birthday.toYmdHms())
    logger.info("真太阳时生日: " + tst_birthday.toYmdHms())

    bazi = tst_birthday.getLunar().getEightChar()
    logger.info(
        f"\nBaZi: {bazi.getYear()}, {bazi.getMonth()}, {bazi.getDay()}, {bazi.getTime()}"
    )

    # --- Cycle pillar to test ---
    cycle_stem, cycle_branch = "戊", "子"
    cycle_label = "大运"

    natal_chart = {
        "year":  {"stem": bazi.getYearGan(),  "branch": bazi.getYearZhi()},
        "month": {"stem": bazi.getMonthGan(), "branch": bazi.getMonthZhi()},
        "day":   {"stem": bazi.getDayGan(),   "branch": bazi.getDayZhi()},
        "hour":  {"stem": bazi.getTimeGan(),  "branch": bazi.getTimeZhi()},
    }

    result = get_cycle_interactions(cycle_stem, cycle_branch, natal_chart, cycle_label)

    logger.info(f"\n--- JSON Output for LLM ({cycle_label} {cycle_stem}{cycle_branch}) ---")
    logger.info(json.dumps(result, ensure_ascii=False, indent=2))