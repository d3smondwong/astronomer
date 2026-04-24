# Project Context & AI Instructions
## Project: Huat Life (BaZi AI Platform)

This file serves as the canonical context for AI assistants working on the Astronomer project. It outlines the tech stack, architectural boundaries, and coding standards.

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

We use the `lunar-python` library, but it does not cover all of our advanced calculation needs. **Do not hallucinate capabilities for `lunar-python`.** Follow these strict boundaries:

### 🟢 Use `lunar-python` For:
* **Stem/Branch → Element Mappings:** Use `LunarUtil.WU_XING_GAN` and `LunarUtil.WU_XING_ZHI`.
* **Hidden Stems (藏干):** Use `eight_char.getYearHideGan()`, etc.
* **Xun / XunKong (旬 / 旬空):** Use `LunarUtil.getXun()` and `LunarUtil.getXunKong()`.
* **Nayin (纳音):** Use `LunarUtil.NAYIN` or `eight_char.getYearNaYin()`.
* **Basic ShiShen (十神) Lookups:** Use `LunarUtil.SHI_SHEN` table.

### 🔴 KEEP CUSTOM (Do NOT delegate to `lunar-python`):
* **Di Shi / 12 Life Stages (地势):** Keep our custom implementation in `cycle_di_shi.py` (it is more flexible than the library's default).
* **Seasonal Strength States (旺/相/囚/休/死):** `lunar-python` has **zero** support for this. Maintain our custom implementation utilizing month branches and custom state multipliers.
* **Wu Xing Dynamics & Qi Weighting:** All scoring, climate needs, and interaction weighing must remain custom-built in our engine.
* **Complex Ten God Synthesis:** Any derivation of Ten Gods stemming from complex branch interactions must be handled by our custom logic.

---

## 📡 API Schema & Response Contract

When building endpoints in FastAPI (`apps/backend/routers/chart.py`), adhere to the following clean contract boundary between English metadata and Chinese calculation payloads:

```python
class NatalChartResponse(BaseModel):
    lunar_date: str        # English metadata
    gender: str            # English metadata
    zodiac: str            # English metadata
    data: dict             # ALL Chinese-keyed BaZi calculation output goes here!
                           # Example: data["四柱实体"]["年柱"]["天干"]
```

Rule: Frontend components directly read from response.data.* (using Chinese keys mapped in TypeScript interfaces at apps/web/types/baziChart.ts). Do not build complex TypeScript transformers to turn Chinese keys into English camelCase on the frontend.

## 📂 Project Structure
Maintain strict boundary separation between frontend and backend in the monorepo:

- apps/backend/ — FastAPI application.
    - main.py — App entry point.
    - routers/ — API endpoints (e.g., chart.py).
    - models/ — Pydantic schemas.
    - astronomer_logic/ — All production calculation logic goes here. (Ignore standard src/ folders from preliminary tests).

- apps/web/ — Next.js application.
    - app/api/chart/route.ts — Route handler interfacing with FastAPI.
    - lib/fastApiClient.ts — Server-only fetch wrappers.

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

## Context Navigation:
When you need to understand the codebase, docs, or any files in this project:
1. ALWAYS query the knowledge graph first: `/graphify query "your question"`
2. Only read raw files if I explicitly say "read the file" or "look at the raw file"
3. Use `graphify-out/wiki/index.md` as your navigation entrypoint for browsing structure.