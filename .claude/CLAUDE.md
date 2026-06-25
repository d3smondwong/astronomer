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

## 📂 Project Structure
Maintain strict boundary separation between frontend and backend in the monorepo:

```
apps/
├── backend/ — FastAPI application
│   ├── main.py — App entry point
│   ├── routers/
│   │   └── chart.py — Chart calculation endpoint
│   ├── data_models/
│   │   └── birth_input.py — Input validation schemas
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
│   │   └── (other calculation modules)
│   ├── orchestrator/
│   │   └── astronomer_data_orchestrator.py — Orchestrates calculation pipeline
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