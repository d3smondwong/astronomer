---
paths:
  - "apps/backend/astronomer_logic/cycles/**"
  - "apps/backend/orchestrator/cycles_orchestrator.py"
  - "apps/backend/data/climate_data.py"
  - "apps/backend/data_models/cycles.py"
  - "apps/backend/tests/test_cycles.py"
  - "apps/web/types/cyclesChart.ts"
  - "apps/web/app/api/cycles/**"
---

# 大运 / 流年 / 岁运 rules

Natal-side rules (格局, 用神, 五神, 七杀→偏官) are in `bazi-natal.md`; the response shape is in
`api-contract.md`.

**Cycle-pillar ten gods are RAW:** 大运/流年 pillar ten gods (`apps/backend/astronomer_logic/cycles/cycle_pillars.py`) are pure `LunarUtil.SHI_SHEN` lookups — the natal 七杀→偏官 / 食神→伤官 relabeling is adjacency-based and adjacency is undefined for a transiting pillar. Rules matching cycle-pillar gods use `["正官", "七杀"]` WITHOUT `"偏官"`; natal-side matching still requires `"偏官"`. When taming gods are revealed in the natal chart, the cycle pillar carries a `制化` annotation instead of a relabel.

**Cycle interaction engine is separate but shares definitions:** `cycles/cycle_interactions.py` runs a 1×N scan (one transiting pillar vs its opponents) — `natal_interactions.py` is hard-wired to exactly 4 pillars and must not be extended. All relation maps, `PRIORITY_RULE_TABLE`, and strength tables are imported from `natal_interactions.py`; never redefine what counts as a 冲/合/刑. Every pairing uses the constant `距离: "紧贴"` (no distance decay).

**岁运 — a 大运 is scanned 1×4, a 流年 1×5:** a decade exists independently of any year inside it, so the 大运 meets only the 4 natal pillars. A 流年 meets the natal pillars **plus its enclosing 大运** (`CompanionPillar`, opponent index 4) — classically the year meets its decade FIRST, and only what survives reaches the 命局. 岁运 items are those whose `组合明细` carries a `"大运"` key. Opponent index 4 is NOT a natal pillar: the `日柱特殊`/`涉及月柱` salience flags, the 日主贪合 remark, and the 日柱-anchored void pass all stay gated on indices 0-3 (`_NATAL_COUNT`) — a transiting branch has no slot in the natal 旬 to be absent from. The 1×5 scan is what makes cross-frames visible (大运申 + 流年子 + 日柱辰 → 三合水局); no 1×1 side-scan could see them, which is why there is no second engine.

**The companion reaches every cycle layer — but 神煞 anchors are the hard boundary.** A 流年's `CompanionPillar` (defined in `cycles/cycle_pillars.py`) feeds four layers: the 1×5 interaction scan, the 制化 annotation, 岁运互空, and the set-completion 神煞. Two of these were *wrong answers* before, not merely missing ones:
- **制化** (`_zhi_hua_annotation`) read only natal revealed stems, so a 流年 七杀 arriving while the **大运 carries 食神** reported 「命局无明显制化，岁运七杀直临」 — an unrestrained killing. 食神制杀 works from the 大运 stem too (it is revealed and present for ten years). A tamed 七杀 is an authority asset; an unrestrained one is danger — the verdict inverts.
- **天火煞** (`cycle_shen_sha.py`) is voided by water, but the evaluator could not see the 大运, so a 流年 completing 寅午戌 inside a **癸亥** decade fired anyway. A false positive.

**神煞 splits into ANCHOR stars and SET stars, and only SET stars see the 大运.** Anchor stars (年支/月支/日支/日干/年干/纳音 → 驿马, 桃花, 天乙贵人, 羊刃, 元辰 …) derive from **birth facts**; the 大运 is itself a guest and must NEVER become an anchor, or we invent 神煞 no classical text recognises. Set stars (天罗, 地网, 自缢煞, 破煞, 挂剑煞, 天火煞, 德秀贵人's 秀 pair) ask whether a group is *present together*, and 岁运命 are all present at once — so they draw on natal + 大运 + guest, exactly like the interaction engine's cross-frames. **三奇 is excluded despite being a combination star**: it needs three stems in *consecutive* pillars, and a 大运/流年 pair has no sequence position (same documented parity gap as 共拱/拱会).

**通根 and 空亡 stay narrow, deliberately.** A 流年 stem does NOT root into the 大运's branch (原局 + 自坐 only) — 通根 describes the chart a stem *stands on*, and rooting into a transient neighbour would make the same year's stem strength swing decade to decade. 岁运互空 is reported but **never downgrades**, preserving the standing rule that only the natal 日柱-anchored void has force.

**合 binds, 冲 agitates — the 岁运 rule that is easiest to get backwards.** `cycles/sui_yun.py` re-resolves the decade's `柱位动态` under the year's 岁运 locks, because the 大运's actions are computed ONCE per decade but a 大运 bound by the 流年 does not deliver its 冲 to the 命局 *that year* (贪合忘冲). **合/三合/伏吟/反吟 downgrade the decade's actions; 六冲 downgrades NOTHING** — 岁冲运 destabilises the decade (`大运态: 受冲`) but does not tie it down, and reading 冲 as suppression would silence exactly the years the classics call the loudest. Each lock behaves exactly as the same lock behaves inside the engine's own passes (`PRIMARY_六合` → branch layer, `STEM_天干合` → stem layer, `STRUCTURAL_三合/三会` → branch+pillar, 交战 → everything). Output is a **compact delta** (`大运制约`) — only items whose 强度 moved, each self-contained so no join back to the decade entry is needed — plus an always-present `大运态` verdict, so an empty delta reads as "the decade acts normally", never "not computed". The re-resolved dynamics (not the raw ones) feed the year's 五行动态, or the two layers would disagree about whether the 大运 acted. Severity surfaces as `运势.警示`, never as a change to `评级`: 评级 is elemental favourability, 警示 is intensity/delivery — orthogonal axes.

**运势 (per-decade / per-year verdict):** the holistic 喜运/平运/忌运 headline the per-element `五行动态` breakdown cannot give (five elements each move their own way). Sourced from the hand-curated `大运喜`/`大运忌` branch table in `data/climate_data.py` (金不换), keyed `日干+月支` — 运支 ∈ 大运喜 → 喜运, ∈ 大运忌 → 忌运, else 平运. These branch lists are **curated, not derived**: mechanically expanding 喜用 五行 to branches would flag ~7 of 12 branches favorable and say nothing. For the handful of charts with no curated table, the verdict degrades to the branch's 本气 五行 read against the chart's 用神, and reports `来源: "用神五行"` so callers can tell the two apart. Invariant (locked by tests): every 大运喜/大运忌 list holds only pure branch chars, and no branch appears in both.

**The 方位表 is 正格-authored — 非正格 charts bypass it entirely.** It assumes the day master stands and must be balanced, so for a 从格/专旺格/化气格 its directions are not merely unhelpful but *backwards*. `get_cycle_yun_shi` therefore skips it whenever `格局 != 正格` and reads the structure-derived 用神 instead (`来源: "从格用神"`). This is the general form of a real bug: 癸午's source clause (`喜从火财 忌申(无根夭)`) is **从格-conditional, not a 方位 judgment**, and encoding its `忌申` rated 庚金 — the very element 癸午's 经典 calls 必须庚辛为生身之本 — as 忌运 for ordinary charts. Both `大运喜`/`大运忌` there are deliberately empty; do not "restore" them from the raw source string.

**大运 and 流年 are TWO INDEPENDENT TIME AXES — never align one to the other.** A 大运 boundary is **individual**: the 起运 instant, then every 10 years on that anniversary (交运). A 流年 boundary is **universal**: 立春, the same instant for everyone alive. Nothing synchronises them, so a year straddling a 交运 is lived partly under each decade and **appears in BOTH decades' `流年` lists** with `交运年: true` — analysed once per decade against that decade's companion, which is the classical "read the 交运 year against both decades" for free. A decade therefore normally carries **11 流年, not 10**; only a 起运 landing exactly on 立春 gives a clean ten.

This is why `DaYun.getLiuNian()` is **not** used: it groups years by calendar year counted off the decade's start year (1991-2000 for a decade actually running Nov 1991 → Nov 2001), silently snapping the individual axis onto the universal one. `cycles_orchestrator._overlapping_liu_nian_years` enumerates them instead. For the same reason a 大运 has no `开始年份`/`结束年份` — a Nov→Nov decade has no honest year-pair label; `起始`/`结束` carry the boundaries and `周期` is the display string.

**Ages are ENDPOINT ages, and 虚岁 is 立春-anchored.** `开始虚岁`/`结束虚岁` are read at the period's own two boundaries, so a decade's `结束虚岁` equals the next decade's `开始虚岁` exactly as their instants coincide (7→17, 17→27 — not lunar-python's 7-16, a calendar-year artifact). `虚岁` counts 1 throughout the **立春-year** of birth and +1 at every 立春; lunar-python's `year - 出生年 + 1` (`DaYun.getStartAge`, inherited by `LiuNian.getAge`) agrees for anyone born after 立春 but is off by one **for life** for a January-born subject, whose birth 立春-year is the previous solar year. `周岁` is completed years lived, birthday-accurate — at 立春 2021 a subject born 1985-11-25 is **35** (虚岁 37), not the 36 that `年份 - 出生年` reports. Both ages are read at `max(period start, birth)`, so the birth year reports 虚 1 / 周 0 rather than a negative age.

**All instants share the chart's (TST-shifted) frame** — the birth instant, `起运阳历`, every 节气 lunar-python reports, and every `起始`/`结束`. Callers comparing against a wall-clock `now` must convert first; never mix frames.

## Deferred, by design
- **流月/流日:** every 流年 carries an empty `流月: []` seam. 流月 = one more orchestrator loop via
  `LiuNian.getLiuYue()`; 流日 has no lunar-python class — derive per date via
  `Lunar.getDayInGanZhiExact2()`.
- **Dropped on user decision:** 九星能量, 方位分析, 五黄煞 (feng-shui almanac, not chart analysis);
  共拱/拱会 virtual arches (need positional adjacency).
- **Cycle 神煞 解读:** natal interpretation texts are pillar-positional prose; the LLM layer
  interprets cycle stars instead.
- **Rule DSL:** `san_ming_tong_hui_v2.py` `requires_dynamic` rules could consume cycle data, but
  the `位置.柱` vocabulary has no 大运/流年 values yet.
