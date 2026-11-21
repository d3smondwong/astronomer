---
paths:
  - "apps/backend/astronomer_logic/**"
  - "apps/backend/data/**"
  - "apps/backend/orchestrator/astronomer_data_orchestrator.py"
  - "apps/backend/tests/**"
---

# Natal BaZi logic rules

These rules encode classical-methodology decisions the user has confirmed. Several look like bugs
but are deliberate — read the reasoning before "fixing" anything here. When a formula is
uncertain, ask the user rather than guess.

Use the `lunar-python` library if a mapping or function is available.

**七杀 → 偏官 transformation:** `apply_qi_sha_transformation()` in `apps/backend/astronomer_logic/ten_gods.py` relabels individual 七杀 occurrences to the distinct stored ten-god string `"偏官"` when a classical taming condition is met (食神制杀, 印化杀, etc.). Different 七杀 in the same chart can end up tamed or not independently. Any rule condition (`san_ming_tong_hui_v*.py`) that counts or matches on `["正官", "七杀"]` must also include `"偏官"`, or it will silently undercount charts with tamed killings.

**格局 decides where 喜忌 come from — 强弱 does NOT:** `astronomer_logic/ge_ju.py` classifies every chart as 正格 / 从财格 / 从杀格 / 从儿格 / 从势格 / 专旺格 / 化气格 *before* `yong_shen.py` computes 喜忌. For 正格 → 调候 + 扶抑. For everything else the **structure** dictates 喜忌 and **调候 is not applied**: a surrendered day master follows its dominant force, so 印比 — which 扶抑 would call 喜 for a weak DM — are in fact **忌** (they 破格). Same 强弱, inverted verdict. Never infer 从格 from 强弱: **极弱 does NOT imply 从格** (a weak-but-rooted chart wants support).

Detection gate (all must hold): 得令 = 0, 得地 = 无根, 得势 = 0, **and 印星 力量 ≈ 0**. That last condition is load-bearing — 得地 sees only the DM's own (clash-aware) 比劫 root and 得势 only 印比 in the *stems*, so 印星 buried in the **branches** is invisible to all three. Without it the detector fires on ~9% of charts instead of ~5%, inverting ordinary charts. Do NOT add 比劫 力量 to that gate: it double-counts roots 得地 has already ruled dead by 冲/空亡. 真从 = no 印 at all; 假从 = a trace survives (keeps the 从格 *direction*, flagged fragile — the residue is exactly what a 印比 运 revives to 破格). Calibration is pinned by `TestGeJu::test_cong_ge_rate_is_classically_rare`; 正格 must stay ≈95%.

**仇神/闲神 are a SPLIT of the 平 bucket — 角色 and 综合 are different axes.** `yong_shen.py` assigns every element both a favourability verdict `综合` (喜/忌/平) and a 五神 role `角色` (喜用神/忌神/仇神/闲神). **仇神 = 生忌神者** — an element that is neither wanted nor feared in itself but *feeds* one the chart fears (火生土 when 土 is 忌). Because 喜用/忌 are **sets** (调候 ∪ 扶抑, or structure-derived), an element that generates a 忌 element may already be the 用神 (土生金 on a weak 戊 that fears 金) — so **喜/忌 always win the label** and 仇神 is assigned in a second pass over the `平` leftovers only. The `克喜用神者` formulation is deliberately NOT encoded: under 扶抑, whatever attacks the 用神 is already tagged 忌.

**The `五神` block is a VIEW over those sets, never a re-derivation.** `_select_yong_shen` names one primary `用神` (化气格 → 化神; 从/专旺 → 主导 force's element; 正格 弱/旺 → the 扶抑 winner, preferring the element 调候 also concurs on; 正格 中和 → 调候喜[0]) and splits `喜用` into `用神` ∪ `喜神` — 喜神 is *the rest of the same 喜用 set*, its supporters, and `忌神/仇神/闲神` equal `忌/仇/闲` verbatim. The classical 生克 chain (`喜神 = 生用神`, `忌神 = 克用神`, `仇神 = 生忌神`) is deliberately NOT used to compute these: that chain re-anchors favourability on the **用神**, but 扶抑 anchors on the **日主** — a weak DM has three distinct 忌 categories (官杀克身/财耗身/食伤泄身), and a single-node 生克 chain would demote a real 忌 (食伤 leaking the DM) to 仇/闲. `五神` is human/LLM-facing; `综合`/`角色` stay the authoritative axes `cycle_wu_xing`/评级 read.

**用神 is a singleton SELECTION, never a fifth `角色` value.** The per-element `角色` keeps four values (`喜用神/忌神/仇神/闲神`); the primary 用神 is named once in `五神.用神` and its per-element `角色` stays `喜用神`. Overloading `角色` with a `用神` value would (a) lose the "exactly one" invariant a categorical enum cannot express, and (b) break every `role == "喜用神"` site — the primary would fall through to the 闲神 arm and read 「平和应对」, the same 仇神-as-闲神 bug class the module already guards. Instead `_element_reading` takes an `is_primary` boolean (derived at read time from `五神.用神`, single source of truth) and gives the primary a headline verdict (`用神得地，运势之枢，为大吉`) distinct from a 喜神 supporter's — presentation richness without touching the role axis or `YongShenRole`.

Consequences that look like bugs but are not: on a **弱/旺 正格 chart `仇` and `闲` are BOTH empty** — 扶抑 tags all five elements 喜 or 忌 and nothing is left idle. 仇神 only fires on **中和 charts** (~24%, where 扶抑 is silent and only 调候 speaks) and on **非正格** charts. And **仇神 never moves `运势.评级`**: 评级 reads `综合`, and a 仇神 is still `平` → 平运. `角色` is a *reading*, `综合` is the *verdict* — orthogonal axes, same discipline as 警示 vs 评级 in the 岁运 layer. `cycle_wu_xing.py` must READ `角色` from the 用神 block, never re-derive a role from `综合` — doing so is what made a 仇神 report 「闲神随运流转，平和应对」 (harmless) while it was strengthening the chart's 忌神.

**假化 never gets 化气格 用神:** `ten_gods.py` applies the DM element change for `形态 == "化气格"` ONLY. If 用神 treated 假化 as transformed, the 十神 layer would label every god against the ORIGINAL day master while 用神 reasoned about the 化神 — the two layers would disagree about what the day master *is*. 假化 falls through to normal detection and carries an advisory.

**Natal interactions are 4-pillar only.** `natal_interactions.py` is hard-wired to exactly 4 pillars and must not be extended; cycle scans live in `cycles/cycle_interactions.py` (see `bazi-cycles.md`).

## Style
- Type hints on all function signatures and Pydantic models.
- Prefer dictionary lookups and tuples over heavy conditional branches when mapping BaZi interactions.
- f-strings for string formatting.
- Domain logic stays in `astronomer_logic/`; `routers/` only handles HTTP.
