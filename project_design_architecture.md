# Project Architecture Plan: Astronomer / Celestial Dawn
## Migrating BaZi Calculations from Client-Side TypeScript → Server-Side Python

---

## Context

The app currently runs ALL BaZi calculations inside the user's browser using `lunar-javascript` (TypeScript). This is a privacy concern — birth data and chart logic are exposed client-side. The goal is to adopt a hybrid rendering strategy identical to cantian.ai: Next.js fetches chart JSON from a Python FastAPI backend at render time, injects it into React components server-side, and the browser only ever receives the final HTML. Birth data never touches the browser's calculation stack.

Additionally, all profiles currently live in `localStorage` — no auth, no cross-device sync. The target is Firebase Auth + Firestore persistence hosted on Google Cloud (Firebase App Hosting for Next.js, Cloud Run for FastAPI).

---

## Current State Summary

| Concern | Current | Target |
|---|---|---|
| BaZi math | Browser (lunar-javascript, TypeScript) | Cloud Run (lunar-python, Python) |
| Profile storage | localStorage | Firestore `/users/{uid}/profiles/{id}` |
| Auth | None | Firebase Auth (Google Sign-In) |
| Frontend hosting | Local dev | Firebase App Hosting |
| Backend hosting | Local scripts / Streamlit | Cloud Run (FastAPI) |

---

## Architecture Overview

```
Browser (React/Next.js client)
    ↕ (page load = fully-rendered HTML)
Firebase App Hosting → Next.js Server
    ↕ (server-to-server, Bearer token)
Cloud Run → FastAPI (Python)
    ↕
lunar-python + apps/backend/astronomer_logic/* modules

Firestore ← Next.js Server (Admin SDK) ← Chart cache + user profiles
Firebase Auth ← Client SDK (ID token sent to Next.js API routes)
```

---

## Phase 1 — Full Local Dev: FastAPI Backend + Next.js Frontend (Concurrent)

**Goal:** Build the complete feature set locally first. FastAPI runs on `localhost:8000`; Next.js runs on `localhost:3000`. The frontend calls the Python backend for ALL BaZi logic. Firebase and Cloud Run come later.

This phase ships the full feature surface in a working local environment before any cloud deployment.

### 1A — FastAPI Core Setup

**New files in `apps/backend/`:**
```
apps/backend/
  main.py                      ← FastAPI app, CORS for localhost:3000
  models/
    birth_input.py             ← BirthInput + NatalChartResponse (Pydantic)
  routers/
    chart.py                   ← all /v1/chart/* endpoints
  requirements.txt             ← fastapi, uvicorn[standard], pydantic
  Dockerfile                   ← for Cloud Run later
```

**Run locally:**
```bash
uvicorn apps.backend.main:app --reload --port 8000
```

### 1B — API Endpoints

All endpoints live in `apps/backend/routers/chart.py`:

```
POST /v1/chart/natal   ← 4 pillars, 10 gods, 12 life stages, na yin, void, 3 palaces, true solar time
POST /v1/chart/full    ← natal + wu xing (lazy augment: runs natal then adds 5 elements)
GET  /health           ← Cloud Run health check (later)
```

**Pydantic models (`apps/backend/models/birth_input.py`):**
```python
class BirthInput(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    gender: int            # 1 = male, 0 = female
    latitude: float
    longitude: float
    use_solar_time_correction: bool = True

class NatalChartResponse(BaseModel):
    lunar_date: str        # English metadata at the top level
    gender: str
    zodiac: str
    data: dict             # ALL Chinese-keyed calculation output lives here
                           # e.g. data["四柱实体"]["年柱"]["天干"]
                           #      data["胎命身"]
                           #      data["五行"] (added by /v1/chart/full)

class FullChartResponse(NatalChartResponse):
    is_full: bool = True
```

**Why `data` as a wrapper key:** The Python orchestrator already returns a nested Chinese-keyed dict. Wrapping it under `data` creates a clean English/Chinese boundary — English fields are metadata (who, when, what type), `data` is the raw calculation payload. This keeps the response contract clean and readable.

**Key Python modules to wire up** (all live in `apps/backend/`):
- `apps/backend/orchestrator/astronomer_data_orchestrator.py` → `calculate_natal_chart()`
- `apps/backend/astronomer_logic/` — all Phase 1 modules (already exists)
- New module to build: `apps/backend/astronomer_logic/wu_xing.py` — five elements calculation

**No dependency on `src/`** — those are preliminary test modules and will not be used. All production logic is built fresh in `apps/backend/astronomer_logic/`.

### 1C — Next.js Frontend Wired to Local FastAPI

**New files in `apps/web/`:**
- `lib/fastApiClient.ts` — server-only fetch wrapper
- `app/api/chart/route.ts` — Next.js Route Handler: accepts birth data from form, calls FastAPI, returns chart JSON
- `types/baziChart.ts` — TypeScript interfaces matching Python schema (Chinese keys)

**`.env.local` additions:**
```
FASTAPI_URL=http://localhost:8000
FASTAPI_BEARER_TOKEN=          # empty in local dev
```

**`apps/web/lib/fastApiClient.ts`:**
```typescript
const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://localhost:8000';

export async function fetchNatalChart(input: BirthInputPayload): Promise<RawChartJSON> {
  const res = await fetch(`${FASTAPI_URL}/v1/chart/natal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`FastAPI ${res.status}`);
  return res.json();
}

export async function fetchFullChart(input: BirthInputPayload): Promise<FullChartJSON> {
  const res = await fetch(`${FASTAPI_URL}/v1/chart/full`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
    cache: 'no-store',
  });
  return res.json();
}
```

**Data schema:** No `chartTransformer.ts`. The Python response puts all calculated output under `response.data` (Chinese-keyed). Components read from `data.*` directly using `types/baziChart.ts` interfaces. This is the canonical schema going forward.

### 1D — BaziProfileForm: Submit to Server

**`apps/web/components/BaziProfileForm.tsx`** — `onFinish` changed from calling `calculateBazi()` to POSTing to `/api/chart`:

```typescript
// BEFORE: calculateBazi(values) → localStorage
// AFTER:
const res = await fetch('/api/chart', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(birthInput),
});
const { profileId, baziChart } = await res.json();
saveProfileMetadata(profileId, { name, birthDate, ... });  // metadata only, no chart
router.push(`/profile/${profileId}`);
```

### 1E — Profile Page as Server Component

**`apps/web/app/(dashboard)/profile/[profileId]/page.tsx`** — convert from client component (reads localStorage) to **Server Component** (fetches from FastAPI):

```typescript
// No 'use client'
export default async function ProfilePage({ params, searchParams }) {
  // Birth metadata from searchParams or a compact cookie
  const birthInput = buildBirthInputFromMetadata(profile);
  const fullChart = await fetchFullChart(birthInput);   // server-to-server, local dev
  return <ProfileView data={fullChart.data} />;
}
```

**Profile metadata seam (local dev):** Birth metadata stored as a signed `httpOnly` cookie when form submits, so the Server Component can read it via `cookies()`. In Phase 2 this is replaced by Firestore.

### 1F — Frontend Scope

**In Phase 1:**
- Profile page (`/profile/[profileId]`): convert to Server Component, fed by Python backend
- Birth data form (`BaziProfileForm.tsx`): submit to `/api/chart` instead of running `calculateBazi()`
- Components updated to read from `response.data.*` (Chinese keys) directly using `types/baziChart.ts`

**Not touched in Phase 1 (kept as-is):**
- Compatibility page — left unchanged
- AI Oracle Chat page — left unchanged

### 1G — Local Dev Verification

Cross-check for demo birth date (Desmond, 1985-11-25, 17:07, Singapore, Male):
1. `uvicorn main:app --reload` in `apps/backend/` starts without errors
2. `POST localhost:8000/v1/chart/natal` → 四柱实体 matches existing TypeScript output for demo birth date
3. `POST localhost:8000/v1/chart/full` → includes `wu_xing` (five elements scores)
4. `npm run dev` in `apps/web/` → form submission POSTs to `/api/chart`, no `lunar-javascript` calls in network tab
5. Profile page renders correctly with existing Four Pillars and Elements tabs
6. `Cache-Control: no-store, private` on all `/api/*` responses

---

## Phase 2 — Firebase Auth + Firestore Persistence

**Goal:** Add Google Sign-In. Move profiles from cookies/localStorage to Firestore. Cache chart results in Firestore.

### New Files
- `firebase.json`, `.firebaserc`, `firestore.rules`, `firestore.indexes.json`
- `apps/web/lib/firebase.ts` — client SDK init
- `apps/web/lib/firebaseAdmin.ts` — Admin SDK init (service account)
- `apps/web/components/AuthProvider.tsx` — `useAuth()` hook

### Firestore Data Model
```
/users/{uid}
  displayName, email, photoURL, createdAt, lastLoginAt

/users/{uid}/profiles/{profileId}
  name, birthDate, birthTime, birthLocation, gender,
  latitude, longitude, usedSolarTime,
  chartCacheKey (sha256 of inputs), createdAt

/chartCache/{cacheKey}
  cacheKey, computedAt, payload (NatalChartResponse JSON with data)

/llmCache/geminiContextId
  contextId, createdAt, expiresAt
```

**Cache key:** `sha256("{year}-{month}-{day}-{hour}-{minute}-{lat:.4f}-{lng:.4f}-{gender}-{tst}")`

### Cache-Aside in `/api/chart/route.ts`
1. Verify Firebase ID token
2. Check Firestore `/chartCache/{key}` — return immediately on hit
3. On miss: call FastAPI, store in Firestore, return to browser

### Verification
- Sign in → `/users/{uid}` created in Firestore
- Submit chart → `/chartCache/{key}` created; second submit is a Firestore hit (no FastAPI call)
- Profile page renders with no localStorage reads

---

## Phase 3 — Cloud Run + Firebase App Hosting Deployment

**Goal:** FastAPI on Cloud Run (asia-southeast1); Next.js on Firebase App Hosting.

### Files
- `apps/backend/Dockerfile` — finalised for Cloud Run
- `cloudbuild.yaml` — path-based triggers: `/backend` → Cloud Run, `/web` → App Hosting
- `apps/web/apphosting.yaml` — `FASTAPI_URL`, `FASTAPI_BEARER_TOKEN` (Secret Manager), `FIREBASE_ADMIN_SERVICE_ACCOUNT_JSON`

### Bearer Token (Phase 3 simple)
Static secret in Secret Manager. FastAPI middleware checks `Authorization: Bearer {token}`. Upgrade to OIDC later.

### Dockerfile
Only `apps/backend/` is needed — no `src/` copy required. All logic lives under `apps/backend/astronomer_logic/`. Simple single-directory copy.

### Verification
- Cloud Run health check passes; unauthenticated request returns 401
- Live App Hosting domain generates a chart via Cloud Run
- `Cache-Control: no-store, private` on all responses

---

## Files to Create / Modify

### Create (Phase 1)
| File | Purpose |
|---|---|
| `apps/backend/main.py` | FastAPI app entry point |
| `apps/backend/models/birth_input.py` | Pydantic models |
| `apps/backend/routers/chart.py` | /v1/chart/* endpoints |
| `apps/backend/astronomer_logic/wu_xing.py` | Five elements calculation |
| `apps/backend/Dockerfile` | Container for Cloud Run |
| `apps/web/lib/fastApiClient.ts` | Server-side fetch wrapper |
| `apps/web/types/baziChart.ts` | TypeScript interfaces (Chinese keys) |
| `apps/web/app/api/chart/route.ts` | Next.js Route Handler |

### Modify (Phase 1)
| File | Change |
|---|---|
| `apps/web/components/BaziProfileForm.tsx` | POST to `/api/chart` instead of `calculateBazi()` |
| `apps/web/app/(dashboard)/profile/[profileId]/page.tsx` | Convert to Server Component |

---

## Data Flow: Before vs After

**Before:**
```
Browser → BaziProfileForm → calculateBazi() [lunar-javascript, client-side]
        → localStorage write → router.push('/profile/id')
        → ProfilePage useEffect reads localStorage → renders
```

**After (Phase 1 local dev):**
```
Browser → BaziProfileForm → POST /api/chart [Next.js server]
                              → POST localhost:8000/v1/chart/full [FastAPI, Python]
                              → store profile metadata in cookie
        → router.push('/profile/id')
Next.js Server → ProfilePage (Server Component)
              → read birth metadata from cookie
              → POST localhost:8000/v1/chart/full [FastAPI]
              → pass response.data directly to components → render HTML
Browser receives fully-rendered HTML — zero BaZi math client-side
```

**After (Phase 3 production):**
```
Browser → POST /api/chart [Firebase App Hosting, Next.js server]
            → verifyIdToken (Firebase)
            → check /chartCache/{key} (Firestore Admin SDK)
            → if miss: POST Cloud Run /v1/chart/full [FastAPI, Python]
                         apps/backend/astronomer_logic/* (all logic here)
            → store result in Firestore
Next.js Server → ProfilePage → read from Firestore → render HTML
```

---

## Key Modules (All in `apps/backend/astronomer_logic/`)

### Already Exists
- `bazi_pillars.py`
- `ten_gods.py`
- `twelve_life_stages.py`
- `na_yin.py`
- `void_xun_kong.py`
- `tai_ming_shen.py`
- `true_solar_time.py`

### To Build
- `wu_xing.py` — Five elements: count stems/branches, compute strength scores, derive lucky/unlucky elements
