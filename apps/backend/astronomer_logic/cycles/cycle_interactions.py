"""
岁运作用 Cycle-vs-Natal Interaction Engine — a 1×4 scan.

One transiting (cycle) pillar — 大运 or 流年 — is scanned against the four
natal pillars. This engine runs SEPARATELY from natal_interactions.py: the
natal pipeline is hard-wired to exactly 4 pillars (range(4) loops,
distance = j - i positional adjacency, 日柱-anchored lock priority), and a
transiting pillar has no positional slot. What IS shared are the definitions:
every branch/stem relation map, the strength vocabulary, the declarative
PRIORITY_RULE_TABLE and the default-strength tables are imported from
natal_interactions so what counts as a 冲/合/刑 — and what suppresses what —
is defined in exactly one place.

Distance: every cycle-natal pairing uses the synthetic constant 距离 "紧贴" —
the 岁运 pillar acts directly on all four natal pillars; distance is never a
strength-decay factor here. Any natal rule gated on adjacency (e.g. 天干合 →
stem lock requires 距离==1) applies unconditionally. Strength differentiation
comes from tier order, the resolution passes, the cycle stem's 5-branch
rooting, and the natal 日柱-anchored void — plus 日柱特殊/涉及月柱 salience
flags (hits on 日柱/月令 carry more interpretive weight).

Cycle-unique whole-pillar types (top tiers, mirroring the legacy engine):
  反吟 — cycle stem clashes natal stem AND cycle branch clashes natal branch
         of the SAME pillar (whole-pillar 天克地冲).
  伏吟 — cycle 干支 exactly equal a natal pillar's 干支.
Classical basis: 「反吟伏吟，泪吟吟」 — a 岁运 pillar that wholly duplicates or
wholly opposes a natal pillar dominates it for the period; lesser interactions
on that pillar are read within that context (pre-pass caps them).
Branch-only repetition (branch matches, stem doesn't) is NOT whole-pillar and
is reported as 伏吟(支) at the natal branch-伏吟 tier.

Skipped vs legacy (documented parity gap): 共拱/拱会 virtual arches only —
they require two pillars "framing" a virtual branch via positional adjacency,
which does not exist for a transiting pillar. 残会 and 干支透合 ARE detected
(残会 needs no adjacency — both branches are physically present; 干支透合 is
the classical 引动/应期 mechanism: 「岁运之干与命局藏干合，谓之引动。合出何神，
即应何事」).
"""

from lunar_python.util import LunarUtil

from apps.backend.astronomer_logic.bazi_pillars import (
    compute_pillar_rooting,
    compute_single_stem_rooting,
)
from apps.backend.astronomer_logic.cycles.cycle_pillars import NatalContext
from apps.backend.astronomer_logic.day_master_strength import get_stem_element
from apps.backend.astronomer_logic.natal_interactions import (
    DEFAULT_STRENGTH,
    DIRECTION_TO_ELEMENT,
    INTERACTION_TIER_ORDER,
    PRIORITY_RULE_TABLE,
    SAN_HUI_DIRECTION,
    STRENGTH_ORDER,
    STRENGTH_REMARKS,
    _PUNISHMENT_STRENGTH,
    _STEM_COMBINE_ELEMENT,
    _STRENGTH_BY_RANK,
    _VAULT_BRANCHES,
    _XK_REMARKS,
    break_map,
    cardinal_branches,
    clash_map,
    directional_he,
    harm_map,
    hidden_stem_he,
    is_valid_peer_combination,
    is_valid_punishment,
    six_he_element_map,
    six_he_map,
    stem_clashes,
    stem_combines,
    stem_controls,
    triple_he,
)

_NATAL_PILLAR_KEYS = ["年柱", "月柱", "日柱", "时柱"]
_HIDE_TIERS = ("本气", "中气", "余气")

# Tier = resolution/sort priority. Whole-pillar 反吟/伏吟 are cycle-unique and
# occupy the top tiers (legacy CYCLE_TIER_ORDER did the same); everything else
# keeps its natal INTERACTION_TIER_ORDER position. 伏吟(支) sits at the natal
# branch-伏吟 tier.
CYCLE_TIER_ORDER = {
    "反吟": -2,
    "伏吟": -1,
    "伏吟(支)": INTERACTION_TIER_ORDER["伏吟"],
    **INTERACTION_TIER_ORDER,
}

# Cycle-unique priority cells absent from the natal table (merged over it).
# On a 伏吟 pillar, 比和/干支透合 are trivially redundant — the cycle pillar IS
# the natal pillar — so they are absorbed rather than merely capped.
CYCLE_PRIORITY_EXTRAS = {
    ("PREPASS_伏吟", "比和"): "消融吸收",
    ("PREPASS_伏吟", "干支透合"): "消融吸收",
}

_CYCLE_PRIORITY_TABLE = {**PRIORITY_RULE_TABLE, **CYCLE_PRIORITY_EXTRAS}

_CYCLE_EXTRA_REMARKS = {
    ("PREPASS_伏吟", "比和"): "伏吟局中，比和冗余，消融吸收",
    ("PREPASS_伏吟", "干支透合"): "伏吟局中，藏干重复，透合无义，消融吸收",
}

# Void-pass type groups (natal-anchored 日柱旬空 only — see pass 6)
_VOID_HE_TYPES = frozenset({"六合", "三合", "三会", "半合", "残会"})
_VOID_CHONG_TYPES = frozenset({"六冲", "反吟"})
_VOID_XING_TYPES = frozenset({"无恩之刑", "恃势之刑", "无礼之刑", "自刑"})
_VOID_HAI_PO_TYPES = frozenset({"六害", "六破"})
_VOID_MISC_TYPES = frozenset({"暗合", "干支透合", "比和", "伏吟(支)"})

# 反吟 is the cycle-unique name for whole-pillar 天克地冲 — the natal priority
# and remark tables know that configuration by its natal name. Without this
# alias, (lock, "反吟") matches no table row and a 反吟 would sail through
# locks that correctly dampen its sibling 伏吟.
_TABLE_TYPE_ALIAS = {"反吟": "天克地冲"}


def _table_type(itype: str) -> str:
    return _TABLE_TYPE_ALIAS.get(itype, itype)


def _rank(strength: str) -> int:
    return STRENGTH_ORDER.get(strength, 2)


def _cap(item: dict, ceiling: str, remark: str) -> None:
    """Downgrade-only: cap an item's 强度 at `ceiling`, appending the remark."""
    if _rank(item["强度"]) < _rank(ceiling):
        item["强度"] = ceiling
        _append_remark(item, remark)


def _downgrade_one_tier(item: dict, remark: str) -> None:
    new_rank = min(_rank(item["强度"]) + 1, max(_STRENGTH_BY_RANK))
    item["强度"] = _STRENGTH_BY_RANK[new_rank]
    _append_remark(item, remark)


def _append_remark(item: dict, remark: str) -> None:
    if not remark:
        return
    existing = item.get("备注")
    item["备注"] = f"{existing}；{remark}" if existing else remark


def _apply_table(item: dict, lock_type: str) -> None:
    """Apply the declarative (lock_type, 类型) → 强度 cell, if one exists.
    Looks up by the aliased table type (反吟 → 天克地冲)."""
    itype = _table_type(item["类型"])
    verdict = _CYCLE_PRIORITY_TABLE.get((lock_type, itype))
    if verdict is None:
        return
    remark = STRENGTH_REMARKS.get(
        (lock_type, itype),
        _CYCLE_EXTRA_REMARKS.get((lock_type, itype), ""),
    )
    if _rank(item["强度"]) < _rank(verdict):
        item["强度"] = verdict
        _append_remark(item, remark)


class _Engine:
    """Single-use detection + resolution pipeline for one cycle pillar."""

    def __init__(
        self,
        cycle_stem: str,
        cycle_branch: str,
        ctx: NatalContext,
        cycle_label: str,
        cycle_stem_rooting: str | None,
    ):
        self.s = cycle_stem
        self.b = cycle_branch
        self.ctx = ctx
        self.label = cycle_label
        self.items: list[dict] = []
        # 反吟/伏吟-dominated natal pillar indices (pass 1)
        self.turbulent: dict[int, str] = {}
        # Natal per-pillar stem rooting — natal-only branches, matching /natal output.
        self.natal_rooting = compute_pillar_rooting(
            list(ctx.gans), list(ctx.zhis), [list(h) for h in ctx.hides]
        )
        # Cycle stem rooting is 5-branch (4 natal + own branch, 自坐通根).
        if cycle_stem_rooting is None:
            cycle_hide = list(LunarUtil.ZHI_HIDE_GAN.get(cycle_branch, []))
            cycle_stem_rooting = compute_single_stem_rooting(
                get_stem_element(cycle_stem),
                list(ctx.zhis) + [cycle_branch],
                [list(h) for h in ctx.hides] + [cycle_hide],
                _NATAL_PILLAR_KEYS + [f"{cycle_label}柱"],
            )["根基强度"]
        self.cycle_rooting = cycle_stem_rooting

    # ── registration helpers ─────────────────────────────────────────────

    def _register(self, itype: str, layer: str, natal_idx: set[int], **fields) -> dict:
        item = {"类型": itype, "_layer": layer, "_natal": natal_idx, **fields}
        if 2 in natal_idx:
            item["日柱特殊"] = True
        if 1 in natal_idx:
            item["涉及月柱"] = True
        self.items.append(item)
        return item

    def _detail(self, natal_idx: int, cycle_val: str, natal_val: str) -> dict:
        return {self.label: cycle_val, _NATAL_PILLAR_KEYS[natal_idx]: natal_val}

    def _root_detail(self, natal_idx: int) -> dict:
        return {
            self.label: self.cycle_rooting,
            _NATAL_PILLAR_KEYS[natal_idx]: self.natal_rooting[
                _NATAL_PILLAR_KEYS[natal_idx]
            ]["根基强度"],
        }

    # ── detection ────────────────────────────────────────────────────────

    def detect(self) -> None:
        self._detect_whole_pillar()
        self._detect_frames()
        self._detect_branch_pairs()
        self._detect_partials()
        self._detect_punishments()
        self._detect_stem_pairs()
        self._detect_tou_he()

    def _detect_whole_pillar(self) -> None:
        """反吟 / 伏吟 — whole-pillar (stem AND branch) vs each natal pillar."""
        for i, (g, z) in enumerate(zip(self.ctx.gans, self.ctx.zhis)):
            pillar_detail = {
                self.label: f"{self.s}{self.b}",
                _NATAL_PILLAR_KEYS[i]: f"{g}{z}",
            }
            if self.s == g and self.b == z:
                self._register(
                    "伏吟", "pillar", {i},
                    形态="岁运伏吟",
                    组合明细=pillar_detail,
                    备注=(
                        f"伏吟：干支皆同，{_NATAL_PILLAR_KEYS[i]}被{self.label}"
                        f"（{self.s}{self.b}）完全占据，停滞呻吟"
                    ),
                )
            elif stem_clashes.get(self.s) == g and clash_map.get(self.b) == z:
                self._register(
                    "反吟", "pillar", {i},
                    形态="天克地冲",
                    组合明细=pillar_detail,
                    根基=self._root_detail(i),
                    备注=(
                        f"反吟：干支皆反，{_NATAL_PILLAR_KEYS[i]}被{self.label}"
                        f"（{self.s}{self.b}）全面冲克，极度动荡"
                    ),
                )

    def _detect_frames(self) -> None:
        """三会 / 三合 — the cycle branch + 2 natal branches complete a frame.

        Enumeration is over distinct-branch SETS: for each frame containing the
        cycle branch, completion means the other two members appear among the
        natal branches. Frames are registered ONCE (keyed by the frame itself,
        never the detecting pair); contributors are re-swept as EVERY natal
        pillar whose branch belongs to the frame, so duplicated natal members
        are all listed in 组合明细 and all locked by pass 2.
        """
        natal_set = set(self.ctx.zhis)
        specs = [("三会", directional_he), ("三合", triple_he)]
        for itype, groups in specs:
            for element, group in groups.items():
                if self.b not in group:
                    continue
                needed = group - {self.b}
                if not needed <= natal_set:
                    continue
                contributors = {
                    i for i, z in enumerate(self.ctx.zhis) if z in group
                }
                detail = {self.label: self.b}
                for i in sorted(contributors):
                    detail[_NATAL_PILLAR_KEYS[i]] = self.ctx.zhis[i]
                fields: dict = {"组合明细": detail}
                if itype == "三会":
                    direction = SAN_HUI_DIRECTION.get(frozenset(group))
                    fields["元素"] = (
                        DIRECTION_TO_ELEMENT[direction]
                        if direction is not None
                        else element
                    )
                    fields["方位"] = direction
                else:
                    fields["元素"] = element
                # Frame already complete natally → the cycle member reinforces
                # an existing bureau rather than forming a new one.
                if group <= natal_set:
                    fields["子类型"] = "增力"
                    fields["备注"] = (
                        f"命局{itype}本已成局，{self.label}支{self.b}再临，同气增力"
                    )
                else:
                    fields["子类型"] = "引动成局"
                    fields["备注"] = (
                        f"{self.label}支{self.b}补足缺口，{itype}成局引动"
                    )
                self._register(itype, "branch", contributors, **fields)

    def _frame_complete(self, groups: dict) -> set[frozenset]:
        natal_set = set(self.ctx.zhis)
        return {
            frozenset(group)
            for group in groups.values()
            if self.b in group and (group - {self.b}) <= natal_set
        }

    def _detect_branch_pairs(self) -> None:
        """六冲/六合/比和/六害/六破/暗合/伏吟(支) — cycle branch vs each natal
        branch. (半合/残会 are handled by _detect_partials, which needs a
        per-group view rather than a per-pillar one.)"""
        for i, z in enumerate(self.ctx.zhis):
            g = self.ctx.gans[i]
            detail = self._detail(i, self.b, z)

            # 伏吟(支): branch-only repetition (whole-pillar 伏吟 caught earlier).
            if self.b == z:
                if self.s != g:
                    self._register(
                        "伏吟(支)", "branch", {i},
                        形态="岁运支伏",
                        组合明细=detail,
                        备注=f"{self.label}支与{_NATAL_PILLAR_KEYS[i]}支重逢，该支之事重现",
                    )
            else:
                peer = is_valid_peer_combination(self.b, z)
                if peer:
                    self._register(
                        "比和", "branch", {i}, 组合明细=detail, 元素=peer["element"]
                    )

            # 六冲 (skip when the same pillar is a whole-pillar 反吟)
            if clash_map.get(self.b) == z and stem_clashes.get(self.s) != g:
                fields: dict = {
                    "形态": "岁运冲",
                    "组合明细": detail,
                    "根基": self._root_detail(i),
                }
                vault = _VAULT_BRANCHES.get(z)
                if vault:
                    released = vault["releases"]
                    fields["子类型"] = "开库"
                    fields["开库详情"] = {
                        "库": vault["label"],
                        "柱": _NATAL_PILLAR_KEYS[i],
                        "透出藏干": released,
                        "十神": LunarUtil.SHI_SHEN.get(
                            self.ctx.effective_day_stem + released, "无"
                        ),
                    }
                    fields["备注"] = (
                        f"{self.label}支{self.b}冲开{_NATAL_PILLAR_KEYS[i]}"
                        f"{vault['label']}（{z}），{released}气透出应事"
                    )
                self._register("六冲", "branch", {i}, **fields)

            # 六合 — 形态 graded 合化/合绊 by the combined element's seasonal state
            if six_he_map.get(self.b) == z:
                pk = (self.b, z) if self.b <= z else (z, self.b)
                elem = six_he_element_map.get(pk, {}).get("primary", "无")
                hua = self.ctx.seasonal.states.get(elem) in {"旺", "相"}
                self._register(
                    "六合", "branch", {i},
                    形态="合化" if hua else "合绊",
                    组合明细=detail,
                    元素=elem,
                    备注=(
                        f"合化{elem}，得令而化" if hua else f"合而不化（{elem}失令），互相牵绊"
                    ),
                )

            if harm_map.get(self.b) == z:
                self._register("六害", "branch", {i}, 形态="岁运害", 组合明细=detail)
            if break_map.get(self.b) == z:
                self._register("六破", "branch", {i}, 形态="岁运破", 组合明细=detail)
            if z in hidden_stem_he.get(self.b, set()):
                self._register("暗合", "branch", {i}, 组合明细=detail)

    def _detect_partials(self) -> None:
        """半合 / 残会 — the cycle branch + ONE natal partner form 2 of a frame
        that includes the cardinal (帝旺).

        One item per group: because the frame is incomplete, at most one of the
        group's two non-cycle members can be present (both present, together
        with the cycle branch, would complete the frame — handled by
        _detect_frames). So there is never more than one partial per group, and
        no pair-picking is needed.

        Contributors are re-swept as EVERY natal pillar carrying a present
        member value — identical to _detect_frames — so a duplicated partner
        (e.g. 子 at 年柱 AND 日柱) is fully listed in 组合明细 and its salience
        flags (日柱特殊/涉及月柱) are set, rather than collapsing to the first
        pillar encountered.
        """
        natal_set = set(self.ctx.zhis)
        specs = [
            ("半合", triple_he, self._frame_complete(triple_he), False),
            ("残会", directional_he, self._frame_complete(directional_he), True),
        ]
        for itype, groups, completed, is_hui in specs:
            for element, group in groups.items():
                if self.b not in group or frozenset(group) in completed:
                    continue
                # Incomplete frame ⇒ 0 or 1 non-cycle member present (2 ⇒ complete).
                present_partners = (group - {self.b}) & natal_set
                if len(present_partners) != 1:
                    continue
                partner = next(iter(present_partners))
                cardinal = cardinal_branches.get(element)
                if cardinal not in (self.b, partner):
                    continue  # 半合/残会 require the cardinal (帝旺) in the pair
                # Missing frame member isn't present, so `z in group` selects
                # exactly the pillars carrying the cycle branch or the partner.
                contributors = {
                    i for i, z in enumerate(self.ctx.zhis) if z in group
                }
                detail = {self.label: self.b}
                for i in sorted(contributors):
                    detail[_NATAL_PILLAR_KEYS[i]] = self.ctx.zhis[i]
                missing = next(b for b in group if b not in (self.b, partner))
                fields: dict = {"组合明细": detail, "缺失支": missing}
                if is_hui:
                    direction = SAN_HUI_DIRECTION.get(frozenset(group))
                    fields["元素"] = DIRECTION_TO_ELEMENT.get(direction, element) if direction is not None else element
                    fields["方位"] = direction
                else:
                    fields["元素"] = element
                self._register(itype, "branch", contributors, **fields)

    def _detect_punishments(self) -> None:
        """三刑/自刑 — full-trio upgrade sees natal branches + the cycle branch."""
        all_branches = list(self.ctx.zhis) + [self.b]
        for i, z in enumerate(self.ctx.zhis):
            result = is_valid_punishment(self.b, z, natal_branches=all_branches)
            if not result:
                continue
            xing_type = result["type"]
            if xing_type in ("无恩之刑", "恃势之刑"):
                xing_form = "三刑全" if result["branch_count"] == 3 else "半刑 - 紧邻之刑"
            else:
                xing_form = "正刑"
            self._register(
                xing_type, "branch", {i},
                形态=xing_form,
                组合明细=self._detail(i, self.b, z),
            )

    def _detect_stem_pairs(self) -> None:
        """天干合 / 天干冲 / 天干克 — cycle stem vs each natal stem.

        岁运天干合 never forms a 化气格 — a transiting combination cannot
        restructure the natal chart; classically it binds (合绊) or competes
        (争合) and 引动s the bound god. Day-master involvement is flagged.
        """
        partner = stem_combines.get(self.s)
        partner_count = sum(1 for g in self.ctx.gans if g == partner)

        for i, g in enumerate(self.ctx.gans):
            detail = self._detail(i, self.s, g)
            root = self._root_detail(i)

            if partner == g:
                he_form = "争合" if partner_count >= 2 else "合绊"
                if he_form == "争合":
                    effect = f"命局两{g}争合，合力分散"
                else:
                    effect = "合绊引动，所合之神应事"
                remark = f"{self.label}干{self.s}与{_NATAL_PILLAR_KEYS[i]}干{g}相合，{effect}"
                if i == 2:
                    remark += "；日主贪合岁运，主意志外倾"
                self._register(
                    "天干合", "stem", {i},
                    形态=he_form,
                    组合明细=detail,
                    根基=root,
                    元素=_STEM_COMBINE_ELEMENT.get(self.s, ""),
                    主动方="相互",
                    备注=remark,
                )

            # 天干冲 (skip when branch also clashes — that pillar is 反吟)
            if stem_clashes.get(self.s) == g and clash_map.get(self.b) != self.ctx.zhis[i]:
                self._register(
                    "天干冲", "stem", {i},
                    形态="岁运冲",
                    组合明细=detail,
                    根基=root,
                    主动方="相互",
                )

            if (self.s, g) in stem_controls or (g, self.s) in stem_controls:
                controller = self.label if (self.s, g) in stem_controls else _NATAL_PILLAR_KEYS[i]
                self._register(
                    "天干克", "stem", {i},
                    形态="岁运克",
                    组合明细=detail,
                    根基=root,
                    主动方=controller,
                )

    def _detect_tou_he(self) -> None:
        """干支透合 — the classical 引动 mechanism, both directions:
        (a) cycle stem → hidden stem inside a natal branch;
        (b) natal visible stem → hidden stem inside the cycle branch.
        天干合 is 1-to-1: first hidden-stem match per branch only (natal rule).
        """
        # (a) cycle stem reaches into natal branches
        target = stem_combines.get(self.s)
        for i, z in enumerate(self.ctx.zhis):
            for h_idx, h_stem in enumerate(LunarUtil.ZHI_HIDE_GAN.get(z, [])):
                if h_stem == target:
                    tier = _HIDE_TIERS[h_idx]
                    god = LunarUtil.SHI_SHEN.get(
                        self.ctx.effective_day_stem + h_stem, "无"
                    )
                    self._register(
                        "干支透合", "stem", {i},
                        形态="岁运引动",
                        组合明细={self.label: self.s, _NATAL_PILLAR_KEYS[i]: z},
                        藏干详情={
                            "藏干": h_stem,
                            "藏干层": tier,
                            "藏干十神": god,
                            "合化五行": _STEM_COMBINE_ELEMENT.get(self.s, "无"),
                        },
                        引动藏干=f"{_NATAL_PILLAR_KEYS[i]}藏干{h_stem}（{god}）被{self.label}干{self.s}合动",
                        备注=f"合出{god}，即应{god}之事（应期引动）",
                    )
                    break

        # (b) natal stems reach into the cycle branch
        cycle_hides = list(LunarUtil.ZHI_HIDE_GAN.get(self.b, []))
        for i, g in enumerate(self.ctx.gans):
            target_n = stem_combines.get(g)
            for h_idx, h_stem in enumerate(cycle_hides):
                if h_stem == target_n:
                    tier = _HIDE_TIERS[h_idx]
                    god = LunarUtil.SHI_SHEN.get(
                        self.ctx.effective_day_stem + h_stem, "无"
                    )
                    self._register(
                        "干支透合", "stem", {i},
                        形态="命局引动",
                        组合明细={_NATAL_PILLAR_KEYS[i]: g, self.label: self.b},
                        藏干详情={
                            "藏干": h_stem,
                            "藏干层": tier,
                            "藏干十神": god,
                            "合化五行": _STEM_COMBINE_ELEMENT.get(g, "无"),
                        },
                        引动藏干=f"{self.label}支藏干{h_stem}（{god}）被{_NATAL_PILLAR_KEYS[i]}干{g}合动",
                        备注=f"命局之干贪合{self.label}藏干，{god}之事被引出",
                    )
                    break

    # ── resolution ───────────────────────────────────────────────────────

    def resolve(self) -> None:
        self._pass0_defaults()
        self._pass1_turbulence()
        self._pass2_structural()
        self._pass3_primary_branch()
        self._pass4_stem_lock()
        self._pass5_rootless()
        self._pass6_void()

    def _pass0_defaults(self) -> None:
        """Initial 强度 from the natal tables at distance 1 (紧贴 — constant)."""
        for item in self.items:
            itype = item["类型"]
            if itype in ("反吟", "伏吟"):
                item["强度"] = "强势主流"  # unconditional (pre-pass dominance)
            elif itype == "伏吟(支)":
                item["强度"] = DEFAULT_STRENGTH.get(("伏吟", 1), "显著影响")
            elif itype in _VOID_XING_TYPES:
                item["强度"] = _PUNISHMENT_STRENGTH.get(
                    (itype, item.get("形态", ""), 1), "显著影响"
                )
            elif itype == "天干合":
                key = "合绊" if item.get("形态") in ("合绊", "争合") else item.get("形态")
                item["强度"] = DEFAULT_STRENGTH.get(("天干合", key), "中等衰减")
            elif itype == "六合" and item.get("形态") == "合绊":
                item["强度"] = "显著影响"  # binding without transformation: one step down
            else:
                item["强度"] = DEFAULT_STRENGTH.get((itype, 1), "显著影响")

    def _pass1_turbulence(self) -> None:
        """反吟/伏吟 pre-pass — the only lock spanning BOTH stem and branch
        layers of the dominated natal pillar."""
        for item in self.items:
            if item["类型"] in ("反吟", "伏吟"):
                for i in item["_natal"]:
                    self.turbulent[i] = item["类型"]

        if not self.turbulent:
            return

        for item in self.items:
            if item["类型"] in ("反吟", "伏吟"):
                continue
            hit = [i for i in item["_natal"] if i in self.turbulent]
            if not hit:
                continue
            lock = f"PREPASS_{self.turbulent[hit[0]]}"
            cell = _CYCLE_PRIORITY_TABLE.get((lock, _table_type(item["类型"])))
            if cell is not None:
                _apply_table(item, lock)
            else:
                cause = self.turbulent[hit[0]]
                _cap(item, "中等衰减", f"{cause}主导该柱，余力皆抑")

    def _pass2_structural(self) -> None:
        """Completed 三会/三合 lock EVERY participating branch (cycle + all
        contributing natal pillars). Branch-layer items touching any locked
        pillar — and not part of the same structure — take the table downgrade.
        三会 > 三合 when both complete."""
        frames = [it for it in self.items if it["类型"] in ("三会", "三合")]
        if not frames:
            return

        san_hui = [f for f in frames if f["类型"] == "三会"]
        if san_hui:
            for f in frames:
                if f["类型"] == "三合":
                    _apply_table(f, "STRUCTURAL_三会")

        # The strongest surviving frame claims the lock (the cycle branch is a
        # member of every frame here, so one lock governs the branch layer).
        lock_frame = min(
            frames, key=lambda f: (0 if f["类型"] == "三会" else 1, _rank(f["强度"]))
        )
        lock = f"STRUCTURAL_{lock_frame['类型']}"

        for item in self.items:
            if item is lock_frame or item["类型"] in ("三会", "三合"):
                continue
            if item["_layer"] not in ("branch", "pillar"):
                continue  # stem layer is governed by pass 4, not branch structures
            # The completed frame always contains the cycle branch (detection
            # requires it), and every branch-layer item has that locked branch
            # as one endpoint — so the suppression legitimately reaches natal
            # pillars OUTSIDE the frame (贪会忘冲: a branch drawn into a bureau
            # forgets its clashes elsewhere). Whole-pillar items ride on the
            # locked branch too: a 伏吟's duplicate branch is itself a frame
            # member, and a 反吟's 地冲 half is delivered by the locked cycle
            # branch (its natal pillar can never be IN the frame — no trio
            # contains a 六冲 pair). The imported natal table rows decide the
            # verdict per type; types without a cell are untouched.
            _apply_table(item, lock)

    def _pass3_primary_branch(self) -> None:
        """贪合忘冲 / 刑冲并见 on the cycle branch. Lock grading by 形态:
        a 合化 六合 claims the lock (classical 贪合忘冲); a mere 合绊 does not —
        the 六冲 claims it and the 六合 takes the table value."""
        if any(it["类型"] in ("三会", "三合") for it in self.items):
            return  # structural lock already governs the branch layer

        he_items = [it for it in self.items if it["类型"] == "六合"]
        chong_items = [it for it in self.items if it["类型"] == "六冲"]
        if not he_items and not chong_items:
            return

        hua_he = [it for it in he_items if it.get("形态") == "合化"]
        if he_items and chong_items:
            lock_item = hua_he[0] if hua_he else chong_items[0]
        elif he_items:
            lock_item = hua_he[0] if hua_he else he_items[0]
        else:
            lock_item = chong_items[0]
        lock = f"PRIMARY_{lock_item['类型']}"

        for item in self.items:
            if item is lock_item or item["类型"] == lock_item["类型"]:
                continue
            if item["_layer"] != "branch":
                continue
            _apply_table(item, lock)

    def _pass4_stem_lock(self) -> None:
        """STEM_天干合: a combining stem is tied up — its 克/冲/透合 are absorbed.
        Adjacency is unconditional for cycles (紧贴). Affects the stem layer only."""
        he_items = [it for it in self.items if it["类型"] == "天干合"]
        if not he_items:
            return
        # The cycle stem is one actor in every stem item; its natal partners
        # are the other locked actors.
        locked_natal = set().union(*(it["_natal"] for it in he_items))
        for item in self.items:
            if item["_layer"] != "stem" or item["类型"] == "天干合":
                continue
            # cycle stem locked → all its 克/冲 absorbed; natal partner locked →
            # that pillar's 透合 into the cycle branch absorbed too.
            if item["类型"] in ("天干克", "天干冲"):
                _apply_table(item, "STEM_天干合")
            elif item["类型"] == "干支透合" and (
                item.get("形态") == "岁运引动" or item["_natal"] & locked_natal
            ):
                _apply_table(item, "STEM_天干合")

    def _pass5_rootless(self) -> None:
        """Mirrors natal Pass S: a rootless stem's interactions float."""
        if self.cycle_rooting != "无根":
            return
        for item in self.items:
            if item["_layer"] != "stem" or item["类型"] == "干支透合":
                continue
            natal_side_rootless = all(
                self.natal_rooting[_NATAL_PILLAR_KEYS[i]]["根基强度"] == "无根"
                for i in item["_natal"]
            )
            if natal_side_rootless:
                _cap(item, "中等衰减", "双方无根，气浮于表，作用大减")
            else:
                _cap(item, "显著影响", f"{self.label}干无根，浮而不实")

    def _pass6_void(self) -> None:
        """Natal-anchored void only: membership in the natal 日柱 旬空 pair.
        The cycle pillar's own 旬空 never drives downgrades (data only), and a
        cycle branch matching the natal void emits 填实 (in cycle_pillars), not
        a downgrade here."""
        day_void = self.ctx.natal_void.get("日柱", "")
        if not day_void:
            return
        for item in self.items:
            if item["_layer"] == "stem" or item["类型"] == "伏吟":
                continue
            void_pillars = [
                _NATAL_PILLAR_KEYS[i]
                for i in sorted(item["_natal"])
                if self.ctx.zhis[i] in day_void and i != 2  # 日支 defines the 旬, never void to itself
            ]
            if not void_pillars:
                continue
            joined = "、".join(void_pillars)
            itype = item["类型"]
            if itype in _VOID_CHONG_TYPES:
                _append_remark(item, _XK_REMARKS["冲开旬空"] + "，冲空填实")
                item["旬空涉及"] = void_pillars
            elif itype in _VOID_HE_TYPES:
                _downgrade_one_tier(item, _XK_REMARKS["合_single"].format(pillars=joined))
                item["旬空涉及"] = void_pillars
            elif itype in _VOID_XING_TYPES:
                _downgrade_one_tier(item, _XK_REMARKS["刑_single"].format(pillars=joined))
                item["旬空涉及"] = void_pillars
            elif itype in _VOID_HAI_PO_TYPES:
                _downgrade_one_tier(item, _XK_REMARKS["害破_single"].format(pillars=joined))
                item["旬空涉及"] = void_pillars
            elif itype in _VOID_MISC_TYPES:
                _downgrade_one_tier(item, _XK_REMARKS["misc_single"].format(pillars=joined))
                item["旬空涉及"] = void_pillars

    # ── output ───────────────────────────────────────────────────────────

    def output(self) -> dict:
        self.items.sort(
            key=lambda it: (CYCLE_TIER_ORDER.get(it["类型"], 99), _rank(it["强度"]))
        )
        overview = []
        dynamics = []
        for item in self.items:
            joined = "".join(f"{k}{v}" for k, v in item["组合明细"].items())
            overview.append(f"{item['类型']}({joined})")
            out = {k: v for k, v in item.items() if not k.startswith("_")}
            out["距离"] = "紧贴"  # constant by design — see module docstring
            dynamics.append(out)
        return {"关系总览": overview, "柱位动态": dynamics}


def get_cycle_interactions(
    cycle_stem: str,
    cycle_branch: str,
    ctx: NatalContext,
    cycle_label: str = "大运",
    cycle_xun_kong: str | None = None,
    cycle_stem_rooting: str | None = None,
) -> dict:
    """
    Scan one cycle pillar against the four natal pillars.

    Args:
        cycle_stem/cycle_branch: the transiting pillar.
        ctx:                     NatalContext from build_natal_context().
        cycle_label:             "大运" | "流年" — keys the cycle side of 组合明细.
        cycle_xun_kong:          the cycle pillar's own void pair (currently
                                 informational; reserved for the 流年-vs-大运 layer).
        cycle_stem_rooting:      5-branch 根基强度 from build_cycle_pillar; computed
                                 internally when None.

    Returns:
        {"关系总览": [str, ...], "柱位动态": [interaction dicts]} — same item
        schema as the natal 作用 output, with the cycle side keyed by cycle_label
        and a constant "距离": "紧贴".
    """
    engine = _Engine(cycle_stem, cycle_branch, ctx, cycle_label, cycle_stem_rooting)
    engine.detect()
    engine.resolve()
    return engine.output()
