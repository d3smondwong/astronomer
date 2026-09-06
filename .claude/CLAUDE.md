# Project Context & AI Instructions
## Project: Huat Life (BaZi AI Platform)

This file serves as the canonical context for AI assistants working on the Astronomer project. It outlines the tech stack, architectural boundaries, and coding standards.

## graphify
Context Navigation: When you need to understand the codebase, docs, or any files in this project.

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)

## Project Environment
```
conda activate astronomer
```

## 🏗️ Core Architecture & Tech Stack

The project is a secure, hybrid server-side rendering model to protect IP and ensure user data privacy.

* **Frontend:** Next.js (React) hosted on **Firebase App Hosting**.
* **Backend:** FastAPI (Python) hosted on **Google Cloud Run**.
* **Database & Auth:** Firebase Auth + Firestore.
* **Communication:** Next.js Server Components / Route Handlers communicate server-to-server with the FastAPI backend.

### Data Flow (Target State)
1. User submits data → Next.js Route Handler.
2. Next.js checks Firestore cache (`/chartCache/{key}`).
3. On cache miss: Next.js calls FastAPI (`/v1/chart/full`).
4. FastAPI uses `lunar-python` + custom modules to calculate the chart.
5. Next.js receives JSON, saves it to Firestore, and renders the HTML.
6. **Rule:** Zero BaZi calculation math runs in the browser.

---

## 🧠 BaZi Logic Boundaries (Critical)

Use the `lunar-python` library if a mapping or function is available.

**七杀 → 偏官 transformation:** `apply_qi_sha_transformation()` in `apps/backend/astronomer_logic/ten_gods.py` relabels individual 七杀 occurrences to the distinct stored ten-god string `"偏官"` when a classical taming condition is met (食神制杀, 印化杀, etc.). Different 七杀 in the same chart can end up tamed or not independently. Any rule condition (`san_ming_tong_hui_v*.py`) that counts or matches on `["正官", "七杀"]` must also include `"偏官"`, or it will silently undercount charts with tamed killings.

**Cycle-pillar ten gods are RAW:** 大运/流年 pillar ten gods (`apps/backend/astronomer_logic/cycles/cycle_pillars.py`) are pure `LunarUtil.SHI_SHEN` lookups — the natal 七杀→偏官 / 食神→伤官 relabeling is adjacency-based and adjacency is undefined for a transiting pillar. Rules matching cycle-pillar gods use `["正官", "七杀"]` WITHOUT `"偏官"`; natal-side matching still requires `"偏官"`. When taming gods are revealed in the natal chart, the cycle pillar carries a `制化` annotation instead of a relabel.

**格局 decides where 喜忌 come from — 强弱 does NOT:** `astronomer_logic/ge_ju.py` classifies every chart as 正格 / 从财格 / 从杀格 / 从儿格 / 从势格 / 专旺格 / 化气格 *before* `yong_shen.py` computes 喜忌. For 正格 → 调候 + 扶抑. For everything else the **structure** dictates 喜忌 and **调候 is not applied**: a surrendered day master follows its dominant force, so 印比 — which 扶抑 would call 喜 for a weak DM — are in fact **忌** (they 破格). Same 强弱, inverted verdict. Never infer 从格 from 强弱: **极弱 does NOT imply 从格** (a weak-but-rooted chart wants support).

Detection gate (all must hold): 得令 = 0, 得地 = 无根, 得势 = 0, **and 印星 力量 ≈ 0**. That last condition is load-bearing — 得地 sees only the DM's own (clash-aware) 比劫 root and 得势 only 印比 in the *stems*, so 印星 buried in the **branches** is invisible to all three. Without it the detector fires on ~9% of charts instead of ~5%, inverting ordinary charts. Do NOT add 比劫 力量 to that gate: it double-counts roots 得地 has already ruled dead by 冲/空亡. 真从 = no 印 at all; 假从 = a trace survives (keeps the 从格 *direction*, flagged fragile — the residue is exactly what a 印比 运 revives to 破格). Calibration is pinned by `TestGeJu::test_cong_ge_rate_is_classically_rare`; 正格 must stay ≈95%.

**仇神/闲神 are a SPLIT of the 平 bucket — 角色 and 综合 are different axes.** `yong_shen.py` assigns every element both a favourability verdict `综合` (喜/忌/平) and a 五神 role `角色` (喜用神/忌神/仇神/闲神). **仇神 = 生忌神者** — an element that is neither wanted nor feared in itself but *feeds* one the chart fears (火生土 when 土 is 忌). Because 喜用/忌 are **sets** (调候 ∪ 扶抑, or structure-derived), an element that generates a 忌 element may already be the 用神 (土生金 on a weak 戊 that fears 金) — so **喜/忌 always win the label** and 仇神 is assigned in a second pass over the `平` leftovers only. The `克喜用神者` formulation is deliberately NOT encoded: under 扶抑, whatever attacks the 用神 is already tagged 忌.

**The `五神` block is a VIEW over those sets, never a re-derivation.** `_select_yong_shen` names one primary `用神` (化气格 → 化神; 从/专旺 → 主导 force's element; 正格 弱/旺 → the 扶抑 winner, preferring the element 调候 also concurs on; 正格 中和 → 调候喜[0]) and splits `喜用` into `用神` ∪ `喜神` — 喜神 is *the rest of the same 喜用 set*, its supporters, and `忌神/仇神/闲神` equal `忌/仇/闲` verbatim. The classical 生克 chain (`喜神 = 生用神`, `忌神 = 克用神`, `仇神 = 生忌神`) is deliberately NOT used to compute these: that chain re-anchors favourability on the **用神**, but 扶抑 anchors on the **日主** — a weak DM has three distinct 忌 categories (官杀克身/财耗身/食伤泄身), and a single-node 生克 chain would demote a real 忌 (食伤 leaking the DM) to 仇/闲. `五神` is human/LLM-facing; `综合`/`角色` stay the authoritative axes `cycle_wu_xing`/评级 read.

**用神 is a singleton SELECTION, never a fifth `角色` value.** The per-element `角色` keeps four values (`喜用神/忌神/仇神/闲神`); the primary 用神 is named once in `五神.用神` and its per-element `角色` stays `喜用神`. Overloading `角色` with a `用神` value would (a) lose the "exactly one" invariant a categorical enum cannot express, and (b) break every `role == "喜用神"` site — the primary would fall through to the 闲神 arm and read 「平和应对」, the same 仇神-as-闲神 bug class the module already guards. Instead `_element_reading` takes an `is_primary` boolean (derived at read time from `五神.用神`, single source of truth) and gives the primary a headline verdict (`用神得地，运势之枢，为大吉`) distinct from a 喜神 supporter's — presentation richness without touching the role axis or `YongShenRole`.

Consequences that look like bugs but are not: on a **弱/旺 正格 chart `仇` and `闲` are BOTH empty** — 扶抑 tags all five elements 喜 or 忌 and nothing is left idle. 仇神 only fires on **中和 charts** (~24%, where 扶抑 is silent and only 调候 speaks) and on **非正格** charts. And **仇神 never moves `运势.评级`**: 评级 reads `综合`, and a 仇神 is still `平` → 平运. `角色` is a *reading*, `综合` is the *verdict* — orthogonal axes, same discipline as 警示 vs 评级 in the 岁运 layer. `cycle_wu_xing.py` must READ `角色` from the 用神 block, never re-derive a role from `综合` — doing so is what made a 仇神 report 「闲神随运流转，平和应对」 (harmless) while it was strengthening the chart's 忌神.

**假化 never gets 化气格 用神:** `ten_gods.py` applies the DM element change for `形态 == "化气格"` ONLY. If 用神 treated 假化 as transformed, the 十神 layer would label every god against the ORIGINAL day master while 用神 reasoned about the 化神 — the two layers would disagree about what the day master *is*. 假化 falls through to normal detection and carries an advisory.

**Cycle interaction engine is separate but shares definitions:** `cycles/cycle_interactions.py` runs a 1×N scan (one transiting pillar vs its opponents) — `natal_interactions.py` is hard-wired to exactly 4 pillars and must not be extended. All relation maps, `PRIORITY_RULE_TABLE`, and strength tables are imported from `natal_interactions.py`; never redefine what counts as a 冲/合/刑. Every pairing uses the constant `距离: "紧贴"` (no distance decay).

**岁运 — a 大运 is scanned 1×4, a 流年 1×5:** a decade exists independently of any year inside it, so the 大运 meets only the 4 natal pillars. A 流年 meets the natal pillars **plus its enclosing 大运** (`CompanionPillar`, opponent index 4) — classically the year meets its decade FIRST, and only what survives reaches the 命局. 岁运 items are those whose `组合明细` carries a `"大运"` key. Opponent index 4 is NOT a natal pillar: the `日柱特殊`/`涉及月柱` salience flags, the 日主贪合 remark, and the 日柱-anchored void pass all stay gated on indices 0-3 (`_NATAL_COUNT`) — a transiting branch has no slot in the natal 旬 to be absent from. The 1×5 scan is what makes cross-frames visible (大运申 + 流年子 + 日柱辰 → 三合水局); no 1×1 side-scan could see them, which is why there is no second engine.

**The companion reaches every cycle layer — but 神煞 anchors are the hard boundary.** A 流年's `CompanionPillar` (defined in `cycles/cycle_pillars.py`) feeds four layers: the 1×5 interaction scan, the 制化 annotation, 岁运互空, and the set-completion 神煞. Two of these were *wrong answers* before, not merely missing ones:
- **制化** (`_zhi_hua_annotation`) read only natal revealed stems, so a 流年 七杀 arriving while the **大运 carries 食神** reported 「命局无明显制化，岁运七杀直临」 — an unrestrained killing. 食神制杀 works from the 大运 stem too (it is revealed and present for ten years). A tamed 七杀 is an authority asset; an unrestrained one is danger — the verdict inverts.
- **天火煞** (`cycle_shen_sha.py`) is voided by water, but the evaluator could not see the 大运, so a 流年 completing 寅午戌 inside a **癸亥** decade fired anyway. A false positive.

**神煞 splits into ANCHOR stars and SET stars, and only SET stars see the 大运.** Anchor stars (年支/月支/日支/日干/年干/纳音 → 驿马, 桃花, 天乙贵人, 羊刃, 元辰 …) derive from **birth facts**; the 大运 is itself a guest and must NEVER become an anchor, or we invent 神煞 no classical text recognises. Set stars (天罗, 地网, 自缢煞, 破煞, 挂剑煞, 天火煞, 德秀贵人's 秀 pair) ask whether a group is *present together*, and 岁运命 are all present at once — so they draw on natal + 大运 + guest, exactly like the interaction engine's cross-frames. **三奇 is excluded despite being a combination star**: it needs three stems in *consecutive* pillars, and a 大运/流年 pair has no sequence position (same documented parity gap as 共拱/拱会).

**通根 and 空亡 stay narrow, deliberately.** A 流年 stem does NOT root into the 大运's branch (原局 + 自坐 only) — 通根 describes the chart a stem *stands on*, and rooting into a transient neighbour would make the same year's stem strength swing decade to decade. 岁运互空 is reported but **never downgrades**, preserving the standing rule that only the natal 日柱-anchored void has force.

**合 binds, 冲 agitates — the 岁运 rule that is easiest to get backwards.** `cycles/sui_yun.py` re-resolves the decade's `柱位动态` under the year's 岁运 locks, because the 大运's actions are computed ONCE per decade but a 大运 bound by the 流年 does not deliver its 冲 to the 命局 *that year* (贪合忘冲). **合/三合/伏吟/反吟 downgrade the decade's actions; 六冲 downgrades NOTHING** — 岁冲运 destabilises the decade (`大运态: 受冲`) but does not tie it down, and reading 冲 as suppression would silence exactly the years the classics call the loudest. Each lock behaves exactly as the same lock behaves inside the engine's own passes (`PRIMARY_六合` → branch layer, `STEM_天干合` → stem layer, `STRUCTURAL_三合/三会` → branch+pillar, 交战 → everything). Output is a **compact delta** (`大运制约`) — only items whose 强度 moved, each self-contained so no join back to the decade entry is needed — plus an always-present `大运态` verdict, so an empty delta reads as "the decade acts normally", never "not computed". The re-resolved dynamics (not the raw ones) feed the year's 五行动态, or the two layers would disagree about whether the 大运 acted. Severity surfaces as `运势.警示`, never as a change to `评级`: 评级 is elemental favourability, 警示 is intensity/delivery — orthogonal axes.

---

## 📡 API Schema & Response Contract

### Endpoint: POST `/v1/chart/natal`

**Request (BirthInput):**
```python
class BirthInput(BaseModel):
    year: int                           # Gregorian year
    month: int                          # 1-12
    day: int                            # 1-31
    hour: int                           # 0-23 (wall-clock time)
    minute: int                         # 0-59
    gender: int                         # 1 = male, 0 = female
    latitude: float                     # Birth location (decimal degrees)
    longitude: float                    # Birth location (decimal degrees)
    use_solar_time_correction: bool     # Default True — apply TST conversion
```

**Response (NatalChartResponse):**
```python
class NatalChartResponse(BaseModel):
    data: Dict[str, Any]  # Complete Chinese-keyed chart output (see below)
    chart_key: str        # 八字-based cache key (8 GanZhi letters + gender), e.g. "bBdLiGfJM"
```

**Response Structure** — all Chinese-keyed fields from orchestrator:
```json
{
  "农历生日": "农历日期 (时辰)",
  "性别": "男 | 女",
  "生肖": "鼠 | 牛 | ... 猪",
  "生时节气": "节气名称",
  "四柱实体": {
    "年柱": { "天干", "地支", "藏干", "藏干十神", "天干十神", "根基强度", "通根于", "十二长生", "空亡地支", "纳音" },
    "月柱": { ... },
    "日柱": { ... },
    "时柱": { ... }
  },
  "日坐十神纳音": { ... },
  "胎命身": { "胎": "...", "命": "...", "身": "..." },
  "六亲": { ... },
  "古籍文献": { ... },
  "相互作用": { ... },
  "神煞": { ... }
}
```

**Rule:** Frontend reads directly from the `data` object using Chinese keys. Map these to TypeScript interfaces at `apps/web/types/baziChart.ts` but preserve the Chinese structure—do not transform keys to camelCase. Chinese keys maintain domain accuracy and bridge backend-frontend seamlessly.

### Endpoint: POST `/v1/chart/cycles`

**Request (CyclesInput = BirthInput +):**
```python
class CyclesInput(BirthInput):
    da_yun_index: Optional[int]   # 0-9; when set, that decade's 流年 list is populated
```

**Response (CyclesResponse):** `{data: Dict[str, Any], chart_key: str}` where `data`:
```json
{
  "起运": { "顺逆": "顺推|逆推", "起运阳历": "...", "起运计岁": "...", "性别": "..." },
  "用神": { "强弱", "格局", "格局详情", "五神", "调候适用", "调候用神", "调候忌神", "调候喜五行", "调候忌五行",
           "喜用", "忌", "仇", "闲", "大运喜", "大运忌", "五行", "经典" },
  // 五神 = { 用神 (singular; "" iff 喜用 空), 喜神 (rest of 喜用), 忌神, 仇神, 闲神 } — additive
  //   presentation split of the sets; 综合/角色 stay authoritative. See yong_shen._select_yong_shen.
  // 五行[元素] = { 十神, 扶抑, 调候, 综合 (喜|忌|平), 角色 (喜用神|忌神|仇神|闲神), 备注 }
  "大运": [
    { "序号": 0, "阶段": "未行大运", "干支": "", "起始", "结束",
      "开始虚岁", "结束虚岁", "开始周岁", "结束周岁", "周期", "流年": [] },
    { "序号": 1, "干支": "丙戌", "起始": "1991-11-04 16:14:27", "结束": "2001-11-04 16:14:27",
      "开始虚岁": 7, "结束虚岁": 17, "开始周岁": 5, "结束周岁": 15, "周期": "7-17岁", ...,
      "运柱": { 天干/地支/藏干/十二长生/纳音/空亡/季节状态/制化 },
      "作用": { "关系总览": [...], "柱位动态": [...] },
      "神煞": [ { "名称", "来源", "解读" } ],
      "运势": { "评级": "喜运|平运|忌运", "依据": "...", "来源": "金不换|用神五行" },
      "五行动态": { "五行", "对日主", "引动" },
      // 五行[元素] = { 状态, 本命, 运基 (流年 only), 变化, 十神, 喜忌, 角色, 解读 }
      "流年": [ { "年份", "起始", "结束", "交运年", "虚岁", "周岁", "干支", "生肖",
                 "运柱", "作用", "神煞",
                 "运势": { ..., "警示": ["岁运并临（重）：…"] },
                 "五行动态",
                 "岁运": { "关系总览": [...], "特殊组合": [ {"名称","级别","说明"} ],
                          "大运态": "交战|入局|被合绊|受冲|常态", "大运态说明": "...",
                          "大运制约": [ {"类型","组合明细","原强度","本年强度","起因","说明"} ],
                          "警示": [...] },
                 "太岁", "流月": [] } ] }
  ]
}
```
`岁运` is present on every 流年 EXCEPT the pre-起运 stub's (未行大运 — no decade to relate to). `运势.警示` appears only when a 级别 "重" configuration fires.

**运势 (per-decade / per-year verdict):** the holistic 喜运/平运/忌运 headline the per-element `五行动态` breakdown cannot give (five elements each move their own way). Sourced from the hand-curated `大运喜`/`大运忌` branch table in `data/climate_data.py` (金不换), keyed `日干+月支` — 运支 ∈ 大运喜 → 喜运, ∈ 大运忌 → 忌运, else 平运. These branch lists are **curated, not derived**: mechanically expanding 喜用 五行 to branches would flag ~7 of 12 branches favorable and say nothing. For the handful of charts with no curated table, the verdict degrades to the branch's 本气 五行 read against the chart's 用神, and reports `来源: "用神五行"` so callers can tell the two apart. Invariant (locked by tests): every 大运喜/大运忌 list holds only pure branch chars, and no branch appears in both.

**The 方位表 is 正格-authored — 非正格 charts bypass it entirely.** It assumes the day master stands and must be balanced, so for a 从格/专旺格/化气格 its directions are not merely unhelpful but *backwards*. `get_cycle_yun_shi` therefore skips it whenever `格局 != 正格` and reads the structure-derived 用神 instead (`来源: "从格用神"`). This is the general form of a real bug: 癸午's source clause (`喜从火财 忌申(无根夭)`) is **从格-conditional, not a 方位 judgment**, and encoding its `忌申` rated 庚金 — the very element 癸午's 经典 calls 必须庚辛为生身之本 — as 忌运 for ordinary charts. Both `大运喜`/`大运忌` there are deliberately empty; do not "restore" them from the raw source string.

**流年 are lazy:** default request returns all 10 大运 fully analysed with empty `流年` lists (~62KB); pass `da_yun_index` to expand one decade (~157KB for its 11 流年, of which the 岁运 layer is ~14KB). Every 流年 carries an empty `流月` seam for the future monthly layer. TypeScript interfaces: `apps/web/types/cyclesChart.ts`.

**大运 and 流年 are TWO INDEPENDENT TIME AXES — never align one to the other.** A 大运 boundary is **individual**: the 起运 instant, then every 10 years on that anniversary (交运). A 流年 boundary is **universal**: 立春, the same instant for everyone alive. Nothing synchronises them, so a year straddling a 交运 is lived partly under each decade and **appears in BOTH decades' `流年` lists** with `交运年: true` — analysed once per decade against that decade's companion, which is the classical "read the 交运 year against both decades" for free. A decade therefore normally carries **11 流年, not 10**; only a 起运 landing exactly on 立春 gives a clean ten.

This is why `DaYun.getLiuNian()` is **not** used: it groups years by calendar year counted off the decade's start year (1991-2000 for a decade actually running Nov 1991 → Nov 2001), silently snapping the individual axis onto the universal one. `cycles_orchestrator._overlapping_liu_nian_years` enumerates them instead. For the same reason a 大运 has no `开始年份`/`结束年份` — a Nov→Nov decade has no honest year-pair label; `起始`/`结束` carry the boundaries and `周期` is the display string.

**Ages are ENDPOINT ages, and 虚岁 is 立春-anchored.** `开始虚岁`/`结束虚岁` are read at the period's own two boundaries, so a decade's `结束虚岁` equals the next decade's `开始虚岁` exactly as their instants coincide (7→17, 17→27 — not lunar-python's 7-16, a calendar-year artifact). `虚岁` counts 1 throughout the **立春-year** of birth and +1 at every 立春; lunar-python's `year - 出生年 + 1` (`DaYun.getStartAge`, inherited by `LiuNian.getAge`) agrees for anyone born after 立春 but is off by one **for life** for a January-born subject, whose birth 立春-year is the previous solar year. `周岁` is completed years lived, birthday-accurate — at 立春 2021 a subject born 1985-11-25 is **35** (虚岁 37), not the 36 that `年份 - 出生年` reports. Both ages are read at `max(period start, birth)`, so the birth year reports 虚 1 / 周 0 rather than a negative age.

**All instants share the chart's (TST-shifted) frame** — the birth instant, `起运阳历`, every 节气 lunar-python reports, and every `起始`/`结束`. Callers comparing against a wall-clock `now` must convert first; never mix frames.

**Caching rule (critical):** cycle timing (起运) depends on the exact birth instant, which `chart_key` deliberately excludes — **never cache cycle data under `chart_key`**. The response is deterministic per (birth fields, lat/lon, TST flag, gender, da_yun_index); cache at the Next.js layer per `profileId + daYunIndex` if needed. `chart_key` in the cycles response is for log correlation only. The `/api/cycles` route handler reads birth data from the profile record (owner-enforced), never from the client.

## 📂 Project Structure
Maintain strict boundary separation between frontend and backend in the monorepo:

```
apps/
├── backend/ — FastAPI application
│   ├── main.py — App entry point
│   ├── routers/
│   │   └── chart.py — Chart calculation endpoint
│   ├── data_models/
│   │   ├── birth_input.py — Input validation schemas
│   │   └── cycles.py — CyclesInput / CyclesResponse
│   ├── astronomer_logic/ — All production BaZi calculation modules
│   │   ├── bazi_pillars.py — Four pillars extraction
│   │   ├── wu_xing.py — Five elements calculations
│   │   ├── ten_gods.py — Ten gods mappings
│   │   ├── twelve_life_stages.py — Di Shi / Life stages
│   │   ├── day_master_strength.py — Seasonal strength states
│   │   ├── void_xun_kong.py — Void/XunKong logic
│   │   ├── natal_interactions.py — Pillar interactions & dynamics
│   │   ├── natal_shen_sha.py — Spiritual stars calculations
│   │   ├── na_yin.py — Nayin element mappings
│   │   ├── true_solar_time.py — TST calculations
│   │   ├── tai_ming_shen.py — Six Relatives stars
│   │   ├── cycles/ — 大运/流年 cycle modules (大运 = 1×4 scan; 流年 = 1×5, vs natal + 大运)
│   │   │   ├── cycle_pillars.py — NatalContext + per-pillar 运柱 enrichment
│   │   │   ├── cycle_interactions.py — Cycle-vs-chart interaction engine (CompanionPillar)
│   │   │   ├── sui_yun.py — 岁运: classical 流年-vs-大运 reading + 大运制约 (合绊) pass
│   │   │   ├── cycle_shen_sha.py — Single-pillar shen sha (imports natal tables)
│   │   │   └── cycle_wu_xing.py — Qualitative elemental dynamics + 引动
│   │   └── (other calculation modules)
│   ├── orchestrator/
│   │   ├── astronomer_data_orchestrator.py — Natal calculation pipeline
│   │   └── cycles_orchestrator.py — 大运/流年 pipeline (lazy 流年, 太岁)
│   ├── tests/
│   │   └── test_cycles.py — Cycles test suite (pytest)
│   └── data/ — Reference data files
│       ├── qiong_tong_bao_jian.py
│       ├── san_ming_tong_hui.py
│       └── sixty_days_classification.py
│
└── web/ — Next.js application (SSR + client components)
    ├── app/
    │   ├── layout.tsx — Root layout (fonts, ConfigProvider, LanguageProvider, ClientRoot)
    │   ├── error.tsx — Root error boundary (covers everything outside (dashboard))
    │   ├── global-error.tsx — Last resort; REPLACES the root layout, so it re-declares
    │   │                     <html>/<body>, globals.css and the three next/font instances
    │   ├── not-found.tsx — Server-side redirect('/'), renders nothing (see its docblock)
    │   ├── actions/profiles.ts — Server Actions (bearer auth, revalidatePath, never throw)
    │   ├── (marketing)/ — Public front door; group adds no URL segment
    │   │   ├── layout.tsx — Header + <main> + Footer chrome, shared by every page here
    │   │   ├── page.tsx — Landing "/" (Server Component: redirects returning users)
    │   │   ├── LandingPageClient.tsx — Hero, create form, feature cards
    │   │   ├── Header.tsx — Fixed top bar (logo, language toggle, auth)
    │   │   └── Footer.tsx
    │   ├── api/
    │   │   ├── chart/route.ts — Route handler calling FastAPI backend
    │   │   ├── cycles/route.ts — 大运/流年 (reads profile birthData, owner-only)
    │   │   ├── insights/route.ts — LLM insights (streamed + non-streamed)
    │   │   ├── auth/session/route.ts — Mints/revokes the session cookie
    │   │   ├── clientError/route.ts — Unauthenticated client error sink
    │   │   └── profiles/
    │   │       ├── route.ts — GET list (owner's profiles; no create endpoint by design)
    │   │       └── migrate/route.ts — POST guest→account transfer (two-token auth)
    │   └── (dashboard)/ — Protected dashboard routes
    │       ├── layout.tsx — Server Component; reads the sidebar's profile list
    │       ├── DashboardShell.tsx — Collapsible sidebar chrome (the dashboard's own
    │       │                        Header equivalent: logo, auth, language toggle)
    │       ├── error.tsx — Dashboard boundary; renders inside the shell, sidebar survives
    │       ├── profile/[profileId]/
    │       │   ├── page.tsx — Server Component: auth, owner check, chart load
    │       │   ├── loading.tsx — Streaming fallback
    │       │   ├── ProfilePageClient.tsx — Interactive elements
    │       │   └── PillarCard / FiveElementsCard / PillarInteractionsCard /
    │       │       DayMasterStrengthCard / FavorableElementsCard / InsightsLoading
    │       ├── compatibility/page.tsx — Compatibility analysis
    │       └── ai_oracle_chat/page.tsx — AI oracle feature
    ├── components/ — Only what crosses route groups; route-specific UI is colocated above
    │   ├── ClientRoot.tsx — AuthProvider + AuthModal wrapper (root layout)
    │   ├── AuthModal.tsx — Sign in / sign up / guest migration
    │   ├── ErrorState.tsx — Shared body of both error boundaries
    │   ├── BaziProfileForm.tsx — Used by landing, sidebar and Server Actions
    │   └── PlacesAutocompleteInput.tsx
    ├── lib/
    │   ├── (server-only) firebaseAdmin, session, profilesDb, chartCacheDb,
    │   │   insightsCacheDb, fastApiClient — each guarded by `import 'server-only'`
    │   ├── (client) authContext, languageContext, firebaseClient, errorReporter,
    │   │   theme, elements, translations, google-loader
    │   └── errors.ts — FastApiError + toClientError sanitization boundary
    ├── types/
    │   ├── api.ts — FastAPI wire contract; safe for client components (see below)
    │   ├── baziChart.ts / cyclesChart.ts — Chinese-keyed chart structures
    │   ├── baziLibraryTypes.ts / profile.ts
    ├── styles/ — theme.css (tokens), components.css, dashboard.css, globals.css
    └── public/ — Static assets (logos, icons, SVGs)

(Profile fixtures live at repo-root fixtures/profiles/, not inside apps/web.)
```

**Server/client module boundary:** `lib/fastApiClient.ts` reads `FASTAPI_BEARER_TOKEN` at module
scope, so it — and every Admin-SDK module — carries `import 'server-only'`. The FastAPI request
and response *types* therefore live in `types/api.ts`, which both sides may import;
`fastApiClient` re-exports them for existing server-side callers. A client component that needs a
response shape imports `@/types/api`, never `@/lib/fastApiClient`.

## 🛠️ Code Style & Guidelines

Python (Backend)
- Use Type Hints for all function signatures and Pydantic models.
- Prefer dictionary lookups and tuples over heavy conditional branches when mapping BaZi interactions.
- Use f-strings for string formatting.
- Keep domain logic cleanly separated from HTTP routing.

TypeScript (Frontend)
- Use Server Components by default. Keep 'use client' strictly restricted to interactive forms or context providers.
- No lunar-javascript imports allowed in frontend code.
- Use strict TypeScript types matching the backend's JSON payload schemas.

### 🎨 Styling rules (theming single source of truth)
- **Colors and fonts are defined in exactly two places, kept in sync:** `styles/theme.css` (CSS land — Tailwind `@theme` brand tokens + semantic `:root` vars) and `lib/theme.ts` (JS land — `palette`, `goldAlpha()`, `fonts`, `strengthScale`, `antdTheme`). Never write a brand hex literal (`#735c00`, `#4d4635`, `#d4af37`, `rgba(115,92,0,…)`, …) in a component.
- **Components style with Tailwind utilities on those tokens** (`bg-parchment`, `text-gold-deep/60`, `border-gold-deep/15`, `font-serif`, `font-zh`, `font-zh-sans`). Repeated composites (sidebar rows, CTAs, badges) are named classes in `styles/components.css` under `@layer components`; responsive layout math lives in `styles/dashboard.css`.
- **Inline `style={{}}` is allowed only for** (a) genuinely dynamic values (score-driven heights, percent positions, data-driven category colors) and (b) antd/MUI component props, fed from `lib/theme.ts` — antd/MUI inject unlayered CSS-in-JS that beats layered utilities, and antd seed tokens must be literal values. Never mutate styles in `onMouseEnter`/`onMouseLeave` — use `:hover` rules or `data-active` attributes.
- **Cascade layers:** antd's `reset.css` is imported in `globals.css` into `layer(base)` — do not re-import it unlayered in `layout.tsx` (unlayered CSS silently overrides every utility, e.g. `button { color: inherit }`, `a { color: blue }`). Rules that must beat antd's own component CSS sit *below* the `@layer` block in `components.css` (see `.sidebar-shell`, `.profile-delete-btn`).
- **Fonts load via `next/font` in `app/layout.tsx`** (Noto Serif, Ma Shan Zheng, Noto Sans SC) and resolve through `--font-noto-serif` / `--font-ma-shan-zheng` / `--font-noto-sans-sc`; never add Google Fonts `@import` or inline `fontFamily`.
- **Five-element presentation constants** (`ELEMENT_ICONS`, `ELEMENT_EN`, `ELEMENT_COLOR`) come from `lib/elements.ts` — never redefine them per component.
- **User feedback: no toasts.** Success is communicated by the UI change itself (navigation, list update); errors render inline at the point of action (antd `<Alert>`, per-section error state with Retry) and always go through `reportClientError`.
- Dark mode is deliberately dormant: the `.dark` block in `theme.css` stays, `next-themes` is not installed. Semantic tokens (`--background`, `--primary`, …) already point at brand values so wiring a toggle later only needs a designed `.dark` palette + provider.

## 📚 Dependencies & Libraries

### Backend (Python)
| Library | Version | Purpose |
|---------|---------|---------|
| **FastAPI** | 0.135.3 | Web framework for API endpoints |
| **Uvicorn** | 0.44.0 | ASGI server for FastAPI |
| **Pydantic** | 2.41.5 | Data validation and JSON schemas |
| **lunar-python** | 1.4.8 | Lunar calendar & BaZi pillar extraction |
| **timezonefinder** | 6.4.4 | Timezone lookup from coordinates |
| **bidict** | 0.23.1 | Bidirectional dictionary for mappings |
| **anthropic** | 0.86.0 | Claude API client for AI oracle feature |
| **openai** | 2.30.0 | OpenAI API client (future integration) |
| **google-genai** | 1.68.0 | Google GenAI client (experimental) |
| **huggingface_hub** | 1.7.2 | HuggingFace model access |
| **hydra-core** | 1.3.2 | Configuration management |
| **streamlit** | 1.54.0 | Prototyping & testing UI |
| **python-dotenv** | 1.2.2 | Environment variable management |
| **jinja2** | 3.1.6 | Template engine for rendering |
| **json-repair** | 0.58.7 | JSON repair utility |

### Frontend (Node.js)
| Library | Version | Purpose |
|---------|---------|---------|
| **Next.js** | 16.2.3 | React SSR framework |
| **React** | 19.2.5 | UI library |
| **TypeScript** | 5.8.2 | Type safety for JS/TSX |
| **Tailwind CSS** | 4.2.0 | Utility-first CSS framework |
| **Ant Design (antd)** | 6.3.5 | Component library for complex UI |
| **Material-UI (@mui)** | 9.0.0 | Material design components |
| **Emotion** | 11.14.0/1 | CSS-in-JS styling |
| **Lucide React** | 1.8.0 | Icon library |
| **Victory** | 37.3.0 | Charting & visualization library |
| **lunar-javascript** | 1.7.7 | (NOT used in production) — client-side reference only |
| **next-themes** | 0.4.6 | Dark mode theme management |
| **sonner** | 1.7.4 | Toast notifications |
| **date-fns** | 4.1.0 | Date utility functions |
| **dayjs** | 1.11.20 | Lightweight date library |
| **tz-lookup** | 6.1.25 | Timezone lookup (browser-side) |
| **@googlemaps/js-api-loader** | 2.0.2 | Google Maps API loader |
| **motion** | 12.38.0 | Animation library |
| **clsx** | 2.1.1 | Classname utility |
| **class-variance-authority** | 0.7.1 | Component variant management |

**Notes:**
- Backend is Python-only; all BaZi calculations happen server-side.
- Frontend imports `lunar-javascript` only for reference/testing—never in production.
- Google Maps, Ant Design, and MUI provide flexible component systems for dashboard UI.
- Victory is used for charting pillar interactions and compatibility analysis.