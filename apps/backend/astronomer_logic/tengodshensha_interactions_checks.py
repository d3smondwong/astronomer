"""
Natal Chart Interaction Checks

This module holds inter-pillar interaction calculations that will be expanded
into a full interactions analysis layer. These methods are designed to be mixed
into ShenShaCalculator (or a future InteractionsCalculator) and rely on the
shared state (self.gans, self.zhis, self.me, self.branch_order, self._add_shen)
established in that class.

Interactions housed here:
- 互禄 (Mutual Lu)        — two pillars exchanging lu branches
- 虚邀禄 (Virtual Lu)     — lu branch absent but flanked by adjacent branches
- 虚邀贵 (Virtual Noble)  — noble branch absent but flanked by adjacent branches
阳刃伏藏 - used in classical Bazi literature to describe two different situations involving the Yang Blade.
"""

from __future__ import annotations

from apps.backend.astronomer_logic.natal_shen_sha import year_day_heavenly_stem_shens


class NatalInteractionsMixin:
    """
    Mixin providing inter-pillar interaction checks.
    Expects the host class to supply:
        self.gans, self.zhis, self.me, self.branch_order, self._add_shen()
    """

    def _calc_mutual_lu(self) -> None:
        """
        互禄 (Mutual Lu / Reciprocal Salary).
        Triggers when two pillars exchange lu branches:
        - Pillar A's master has lu at Pillar B's branch
        - Pillar B's master has lu at Pillar A's branch

        Tracks both adjacent (紧贴) and distant (遥) pairings.
        """
        lu_map = year_day_heavenly_stem_shens["禄神"]

        for i in range(4):
            for j in range(i + 1, 4):
                if (
                    lu_map.get(self.gans[i]) == self.zhis[j]
                    and lu_map.get(self.gans[j]) == self.zhis[i]
                ):
                    self._add_shen(i, "互禄", source="组合")
                    self._add_shen(j, "互禄", source="组合")

    def _calc_virtual_lu(self) -> None:
        """
        虚邀禄 (Virtual Lu / Aspiring Lu).
        Triggers when the Day Master's lu branch is NOT physically in the chart,
        but is flanked by adjacent branches.

        Distinguishes 拱禄 (Day-Hour position) from 夹禄 (others).
        """
        lu_map = year_day_heavenly_stem_shens["禄神"]
        my_lu = lu_map.get(self.me)

        if not my_lu or my_lu in self.zhis:
            return

        idx = self.branch_order.index(my_lu)
        prev_n = self.branch_order[(idx - 1) % 12]
        next_n = self.branch_order[(idx + 1) % 12]

        if prev_n in self.zhis and next_n in self.zhis:
            prev_indices = [i for i, zh in enumerate(self.zhis) if zh == prev_n]
            next_indices = [i for i, zh in enumerate(self.zhis) if zh == next_n]

            for p1 in prev_indices:
                for p2 in next_indices:
                    is_adj = abs(p1 - p2) == 1
                    is_gong = p1 >= 2 and p2 >= 2  # Day-Hour position
                    label = "拱禄" if is_gong else "夹禄"
                    prefix = "正" if is_adj else "遥"

                    p_min, p_max = min(p1, p2), max(p1, p2)
                    self._add_shen(p_min, f"{prefix}{label}", source="日干")
                    self._add_shen(p_max, f"{prefix}{label}", source="日干")

    def _calc_virtual_noble(self) -> None:
        """
        虚邀贵 (Virtual Noble / Aspiring Noble).
        Similar to 虚邀禄 but for 天乙贵人 (Heavenly Noble).
        Checks both 昼天乙 and 夜天乙.
        """
        noble_branches = list(
            set(
                [
                    year_day_heavenly_stem_shens["昼天乙贵人"].get(self.me),
                    year_day_heavenly_stem_shens["夜天乙贵人"].get(self.me),
                ]
            )
        )

        for nb in noble_branches:
            if not nb or nb in self.zhis:
                continue

            idx = self.branch_order.index(nb)
            p_nb = self.branch_order[(idx - 1) % 12]
            n_nb = self.branch_order[(idx + 1) % 12]

            if p_nb in self.zhis and n_nb in self.zhis:
                p_indices = [i for i, zh in enumerate(self.zhis) if zh == p_nb]
                n_indices = [i for i, zh in enumerate(self.zhis) if zh == n_nb]

                for p1 in p_indices:
                    for p2 in n_indices:
                        is_adj = abs(p1 - p2) == 1
                        is_gong = p1 >= 2 and p2 >= 2
                        label = "拱贵" if is_gong else "夹贵"
                        prefix = "正" if is_adj else "遥"

                        p_min, p_max = min(p1, p2), max(p1, p2)
                        self._add_shen(p_min, f"{prefix}{label}", source="日干")
                        self._add_shen(p_max, f"{prefix}{label}", source="日干")

'''
Meaning 1: 伏吟 (Fú Yín) – Duplication / Repetition of the Blade
This is the most literal interpretation of “伏藏” (hidden / repeated / lying dormant).

What it means: When the Earthly Branch of the Yang Blade appears more than once in the Four Pillars. In classical texts like Yuan Hai Zi Ping, this is called “Yang Blade Fu Yin” (阳刃伏吟).

How it happens: For example, a person with Day Stem 甲 (Jia) – whose blade branch is 卯 (Rabbit) – has 卯 in both the Year Pillar and the Month Pillar. The same blade branch repeats.

Why it matters: 伏吟 (Fu Yin) means “lying on the same spot” – it indicates duplication, stagnation, or intensification of that star’s energy. Since the Yang Blade is already fierce, having it “repeat” makes its negative effects twice as strong – more prone to financial loss, marital conflict, accidents, and legal trouble.

Classical reference:
“阳刃最忌伏吟” – “The Yang Blade most fears Fu Yin (repetition).”

Meaning 2: 伏制 (Fú Zhì) – Subduing / Controlling the Blade
This interpretation is about technique rather than a structure. The word “伏” here means “to subdue” (like 降伏), and “藏” means “to hide/contain”.

What it means: Using Official (正官) or Kill (七杀) stars to control the fierce energy of the Yang Blade. When the blade is successfully “subdued” (伏制), its violent energy is transformed into authority and leadership.

How it happens: For a 甲 day master with blade in 卯, a strong 庚 (metal) Seven Kill in the chart can “tame” the blade. The blade is still present, but it is “hidden” or “controlled” – hence 伏藏 (subdued and contained).

Why it matters: This is the basis of the famous “Blade Controlled by Kill” pattern (羊刃驾杀) – a noble formation for military officers, surgeons, executives, and entrepreneurs.
Classical reference:
“刃宜伏制，官煞皆宜” – “The blade should be subdued; both Official and Kill are suitable.”
'''