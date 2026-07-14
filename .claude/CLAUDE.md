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

**假化 never gets 化气格 用神:** `ten_gods.py` applies the DM element change for `形态 == "化气格"` ONLY. If 用神 treated 假化 as transformed, the 十神 layer would label every god against the ORIGINAL day master while 用神 reasoned about the 化神 — the two layers would disagree about what the day master *is*. 假化 falls through to normal detection and carries an advisory.

**Cycle interaction engine is separate but shares definitions:** `cycles/cycle_interactions.py` runs a 1×4 scan (one transiting pillar vs 4 natal pillars) — `natal_interactions.py` is hard-wired to exactly 4 pillars and must not be extended. All relation maps, `PRIORITY_RULE_TABLE`, and strength tables are imported from `natal_interactions.py`; never redefine what counts as a 冲/合/刑. Every cycle-natal pairing uses the constant `距离: "紧贴"` (no distance decay).

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
  "用神": { "强弱", "格局", "格局详情", "调候用神", "调候喜五行", "喜用", "忌", "大运喜", "大运忌", "五行", "经典" },
  "大运": [
    { "序号": 0, "阶段": "未行大运", "干支": "", "开始年份", "结束年份", "开始年龄", "结束年龄", "流年": [] },
    { "序号": 1, "干支": "丙戌", "周期": "7-16岁", ...,
      "运柱": { 天干/地支/藏干/十二长生/纳音/空亡/季节状态/制化 },
      "作用": { "关系总览": [...], "柱位动态": [...] },
      "神煞": [ { "名称", "来源", "解读" } ],
      "运势": { "评级": "喜运|平运|忌运", "依据": "...", "来源": "金不换|用神五行" },
      "五行动态": { "五行构成", "季节状态", "对日主", "引动" },
      "流年": [ { "年份", "虚岁", "周岁", "干支", "生肖", "运柱", "作用", "神煞", "运势", "五行动态", "太岁", "流月": [] } ] }
  ]
}
```

**运势 (per-decade / per-year verdict):** the holistic 喜运/平运/忌运 headline the per-element `五行动态` breakdown cannot give (five elements each move their own way). Sourced from the hand-curated `大运喜`/`大运忌` branch table in `data/climate_data.py` (金不换), keyed `日干+月支` — 运支 ∈ 大运喜 → 喜运, ∈ 大运忌 → 忌运, else 平运. These branch lists are **curated, not derived**: mechanically expanding 喜用 五行 to branches would flag ~7 of 12 branches favorable and say nothing. For the handful of charts with no curated table, the verdict degrades to the branch's 本气 五行 read against the chart's 用神, and reports `来源: "用神五行"` so callers can tell the two apart. Invariant (locked by tests): every 大运喜/大运忌 list holds only pure branch chars, and no branch appears in both.

**The 方位表 is 正格-authored — 非正格 charts bypass it entirely.** It assumes the day master stands and must be balanced, so for a 从格/专旺格/化气格 its directions are not merely unhelpful but *backwards*. `get_cycle_yun_shi` therefore skips it whenever `格局 != 正格` and reads the structure-derived 用神 instead (`来源: "从格用神"`). This is the general form of a real bug: 癸午's source clause (`喜从火财 忌申(无根夭)`) is **从格-conditional, not a 方位 judgment**, and encoding its `忌申` rated 庚金 — the very element 癸午's 经典 calls 必须庚辛为生身之本 — as 忌运 for ordinary charts. Both `大运喜`/`大运忌` there are deliberately empty; do not "restore" them from the raw source string.

**流年 are lazy:** default request returns all 10 大运 fully analysed with empty `流年` lists (~40KB); pass `da_yun_index` to expand one decade (~84KB). Every 流年 carries an empty `流月` seam for the future monthly layer. TypeScript interfaces: `apps/web/types/cyclesChart.ts`.

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
│   │   ├── cycles/ — 大运/流年 cycle modules (1×4 scan vs natal pillars)
│   │   │   ├── cycle_pillars.py — NatalContext + per-pillar 运柱 enrichment
│   │   │   ├── cycle_interactions.py — Cycle-vs-natal interaction engine
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
    │   ├── layout.tsx — Root layout
    │   ├── page.tsx — Landing page
    │   ├── api/
    │   │   ├── chart/route.ts — Route handler calling FastAPI backend
    │   │   ├── cycles/route.ts — 大运/流年 (reads profile birthData, owner-only)
    │   │   └── profiles/[id]/route.ts — Profile API endpoints
    │   └── (dashboard)/ — Protected dashboard routes
    │       ├── layout.tsx — Dashboard layout
    │       ├── profile/[profileId]/
    │       │   ├── page.tsx — Profile page (Server Component)
    │       │   ├── ProfilePageClient.tsx — Interactive elements
    │       │   └── PillarInteractionsCard.tsx — Interaction display
    │       ├── compatibility/page.tsx — Compatibility analysis
    │       └── ai_oracle_chat/page.tsx — AI oracle feature
    ├── components/
    │   ├── ui/ — Shadcn UI components (button, card, tabs, etc.)
    │   ├── Header.tsx
    │   └── Footer.tsx
    ├── lib/
    │   ├── languageContext.tsx — i18n context provider
    │   └── utils.ts — Utility functions
    ├── types/
    │   └── (TypeScript interfaces matching backend schemas)
    ├── styles/
    │   └── globals.css
    ├── public/ — Static assets (logos, icons, SVGs)
    └── profiles/ — User profile JSON data
```

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