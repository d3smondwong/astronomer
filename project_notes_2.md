This architecture plan consolidates our discussions into a high-performance, scalable blueprint for your Bazi application. It leverages the "Heavy Brain, Multiple Bodies" philosophy to ensure your complex Python logic serves all platforms efficiently.

---

# 🌌 Astronomer Bazi: Full Architecture & Strategy

## 1. System Overview

A cross-platform ecosystem where a Centralized Python Brain (FastAPI) handles astronomical calculations and LLM orchestration, serving a Unified Frontend (React Web/Native) and Persistent Memory (Firestore).

---

## 2. Monorepo Structure (Turborepo)

We use a monorepo to maintain a single "Contract" between your calculations and your UI.

### Directory Layout

```
astronomer-monorepo/
├── /apps
│   ├── backend/                # Firebase Functions (Python + FastAPI)
│   ├── web/                    # Next.js (The "Orchestrator")
│   │   ├── app/                # App Router (SSR/ISR logic)
│   │   └── components/         # React + Victory (Interactive UI)
│   ├── mobile/                 # React Native + Victory-Native
│   └── playground/             # Streamlit (Your existing test scripts)
├── /packages
│   ├── bazi-engine/            # CORE: Pillars, Solar Terms, 10 Gods
│   ├── llm-core/               # ORCHESTRATOR: Prompts, Formatters, Providers
│   └── shared-schema/          # TYPES: Pydantic models & TS Interfaces
├── firebase.json               # Multi-codebase configuration
└── turbo.json                  # Task orchestration & caching
```

---

## 3. Data Pipeline & Hydration Strategy

To optimize performance and cost, we use a **Lazy-Hydration pattern** for the Bazi JSON.

### Stage 1: Basic (Instant)
- **Runs:** bazi_pillars.py + element_scores.py
- **Output:** Core 4 Pillars and basic traits
- **Storage:** Saved to Firestore as status: `"basic"`

### Stage 2: Full (On-Demand)
- **Trigger:** User requests "Full Report" or clicks "Chat with Master"
- **Action:** Fetch Stage 1 data from Firestore → Pass into liu_nian.py & liu_yue.py
- **Output:** Appends 10-year, annual, and monthly cycles
- **Storage:** Update Firestore to status: `"full"`

---

## 4. Execution Flow

### Data Flow Progression

| Step | Action | Platform |
|------|--------|----------|
| 1 | User navigates to /dashboard/desmond | Next.js Server |
| 2 | Next.js calls FastAPI: GET /bazi/desmond | Server-to-Server |
| 3 | FastAPI runs the Bazi engine & returns JSON | FastAPI (Python) |
| 4 | Next.js injects JSON into the React components | Next.js Server |
| 5 | User receives a fully rendered HTML page | Client Browser |

### Why This Architecture is Better

Server-to-server communication (Next.js to FastAPI) within the Google Cloud network is significantly faster than a user's mobile browser trying to call an API.

### The Live Execution Flow (The "Invisible" Backend)

When a user asks for a chart or chats with the Bazi Master, the data flows through Google's internal network to keep things fast and private.

**Component Chain:**
1. **React/Mobile UI:** Captures birth data (Date, Time, Longitude)
2. **Firebase Cloud Functions (Python + FastAPI):**
   - **The Engine:** Calculates the 4 Pillars, 10 Gods, and Luck Cycles
   - **The Bridge:** Communicates with the Gemini API for interpretations
3. **Gemini AI (Multi-turn):** Receives the Bazi JSON as hidden context and provides the persona-driven reading
4. **Firestore (Database):**
   - Stores the Extensive JSON so you only calculate it once (saving compute)
   - Stores the Chat History to maintain the conversation flow across devices

---

## 5. Technical Stack & Architecture

### Backend
- **Framework:** FastAPI + Firebase Functions
- **Version:** Python 3.12+
- **Cold Start Optimization:** Load heavy look-up tables (Solar Terms) as Global Variables to persist across warm instances
- **Validation:** Pydantic for strict models to validate the "Extensive JSON" before it leaves the backend

### Database (Firestore)
- **Collection Structure:** `users/{uid}/charts/{chartId}`
- **Caching Strategy:** Check Firestore before running any calculation
- **Logic Hash:** If your Python code version changes, invalidate the cache and re-calculate

### AI: Gemini 2.5/3.0 Orchestration
- **Invisible Context:** The LLM receives the Full JSON via the backend. The user never sees the raw data
- **Context Caching:** Use Explicit Gemini Caching for the "Full JSON"
- **Why:** In a 10-turn chat, you only pay for the massive Bazi JSON once. Subsequent messages only send the user's text

### Frontend: Victory Charts
- **Web:** victory (SVG-based)
- **Mobile:** victory-native (React Native SVG)
- **Design:** Map Bazi elements to static hex codes (Wood: Green, Fire: Red, etc.) in a shared theme file

### Build & Task Orchestration

**Turborepo (by Vercel):** Extremely fast and very easy to set up for JavaScript/TypeScript projects. It uses "Remote Caching," meaning if you haven't changed your Bazi engine code, it won't re-build it unnecessarily.

---

## 6. Three-Layer Caching Strategy

### Layer 1: The "Permanent" Cache (Firestore)

Treat Firestore as your primary cache for calculated results. As we discussed with the "Hydration" pattern, once you calculate a user's pillars or luck cycles, you should never calculate them again.

**Strategy:** Cache-Aside (Lazy Loading)

**Logic:**
1. Check Firestore for charts/{uid}
2. If it exists and contains the required scope (Basic vs. Full), return it
3. If it doesn't exist, run your Python engine, save the result, and then return it

**Benefit:** Reduces Cloud Function execution time and keeps your "Heavy Brain" from repeating work.

### Layer 2: The "In-Memory" Cache (Global Variables)

Because Cloud Functions are containers, they often stay "warm" between requests. You can cache expensive, static data (like solar term look-up tables or coordinate data) in Global Variables outside your main function handler.

```python
# global_cache.py (Inside your backend app)
# This is initialized once when the container starts, not every request.
SOLAR_LOOKUP_TABLE = load_solar_data_from_json()

def bazi_handler(request):
    # Uses the pre-loaded table instantly
    result = calculate_with(SOLAR_LOOKUP_TABLE)
```

**Strategy:** Global Object Persistence

**Benefit:** Drastically reduces "Cold Start" lag and file I/O overhead for every calculation.

### Layer 3: The "LLM Context" Cache (Gemini Context Caching)

This is the most advanced part of your strategy. Since your "Full Report" JSON is extensive, sending it to Gemini in every turn of a chat can get expensive.

**The Tech:** Use Gemini Context Caching (Explicit Caching)

**How it works:** You send the user's Full Bazi JSON to Gemini once and tell the API to "cache" this context for a specific TTL (e.g., 30 minutes).

**Benefit:** Subsequent chat turns only send the new message. You don't pay to re-send the huge Bazi JSON over and over. This reduces both Latency and Token Cost.

---

## 7. Strategic Engineering Best Practices

### A. Separation of API Concerns

**Next.js API Routes:** Use these for "Frontend" logic, like handling form submissions or simple session checks.

**FastAPI:** Keep this strictly for Domain Logic (Bazi calculations, Interpretive Insights, and LLM formatting). Do not put UI-specific logic here.

### B. Shared Type Safety

Since you are using Pydantic in Python, you can use a tool like json-schema-to-typescript to ensure your Next.js frontend always knows exactly what your Bazi JSON looks like. This prevents "Undefined" errors in your Victory charts.

### C. Authentication Flow

You will now use Firebase Admin Auth in both places:

- **Next.js Server:** Checks the user's cookie/token to see if they can access the dashboard (SSR)
- **FastAPI:** Checks the Bearer token to authorize the heavy Bazi calculations

---

## 8. Development Phases

### Phase 1: The Engine (Weeks 1-2)
- Move existing .py files into packages/bazi-engine
- Write Unit Tests for the 4 Pillars calculation to ensure zero "Logic Drift"
- Standardize the output into a single BaziBaseModel (Pydantic)

### Phase 2: The API Bridge (Weeks 3-4)
- Set up FastAPI in apps/backend
- Implement the Hydration Logic: `GET /chart` (check cache) and `POST /chart/hydrate` (run heavy luck cycles)
- Deploy to Firebase Functions (Region: asia-southeast1)

### Phase 3: The Visualization (Weeks 5-6)
- Build the React dashboard
- Implement the Victory Radar Chart for element strengths
- Create the Timeline Chart for the 10-Year Luck Pillars

### Phase 4: The AI Persona (Weeks 7-8)
- Integrate llm-core with Gemini
- Implement Multi-turn Chat with context caching
- Refine the data_llm_formatter.py to strip unnecessary technical noise before sending to AI

---

## 9. Deployment & CI/CD (Google Cloud)

### Core Infrastructure

- **Cloud Build:** Automated triggers based on folder paths
- **Secret Manager:** Securely store Gemini API keys
- **Firebase Hosting:** Deploy the React web app to the global CDN
- **Firebase App Hosting:** Best place to host your Next.js app. It automatically handles the SSR environment for you
- **Cloud Run (or Firebase Functions):** Your FastAPI backend lives here
- **The Bridge:** Point your Next.js fetch() calls to the internal URL of your FastAPI service

### The Deployment Pipeline (CI/CD)

Using Google Cloud Build, your deployment is automated and optimized for a monorepo.

**Trigger Process:**
1. Push to GitHub → Cloud Build triggers
2. Path-Based Filters apply:
   - Changed /backend? → Cloud Build redeploys the Firebase Python Function
   - Changed /web? → Cloud Build refreshes Firebase Hosting
   - Changed /mobile? → Cloud Build runs tests and can even push a new build to Firebase App Distribution for testing

### Scaling Note

By using this monorepo and hydration strategy, you ensure that your "Astronomer" app remains fast and cost-effective whether you have 10 users or 10,000. Each user's heavy calculations are performed exactly once and cached forever.

---

## 10. Data Aggregator Implementation Pattern

### The "Hydration" Strategy

Instead of two aggregators, use a Firestore-first "Hydration" pattern. This is a standard engineering practice where you check if the "base" exists before doing more work.

### The Workflow

**Stage 1 (Basic):** User opens the app. The aggregator runs the "Basic" logic and saves the result to Firestore under charts/{uid}.

**Stage 2 (Full/Chat):** User clicks the Chat.
- The Backend pulls the existing document from Firestore
- It checks for a flag like is_full_analysis: true
- **If False:** It passes the existing basic data into the heavy modules (liu_nian, liu_yue). It appends the new data to the existing object and updates Firestore
- **If True:** It just pulls the data and hands it to Gemini

### Implementation in your Python Code

You can keep one class but use a method that "augments" the data. This keeps your code DRY (Don't Repeat Yourself).

```python
# services/astronomer_data_aggregator.py

class AstronomerAggregator:
    def get_basic_data(self, birth_input):
        # Runs pillars, elements, and basic insights
        return self._run_core_engine(birth_input)

    def hydrate_to_full(self, existing_basic_data):
        # Take the output of get_basic_data and add the heavy lifting
        # No re-running of pillars!
        annual = liu_nian.calculate(existing_basic_data)
        monthly = liu_yue.calculate(existing_basic_data)

        return {**existing_basic_data, "annual": annual, "monthly": monthly, "is_full": True}
```

### Why This is Better Than a Separate Aggregator

1. **Dependency Injection:** Your liu_nian.py likely needs the output of bazi_pillars.py to function. By "hydrating," you are simply passing the already-calculated pillars into the luck module

2. **Cost Efficiency:** You only pay for the "expensive" Python execution time once per user

3. **API Speed:** If a user returns to the chat a day later, your API sees is_full: True in Firestore and returns the data in milliseconds without running a single line of Bazi math

---

## 11. Engineering Decisions Summary

| Component | Decision | Why? |
|-----------|----------|------|
| Logic Wrapper | FastAPI + Pydantic | Type safety, auto-validation of big JSON, and async performance |
| Visuals | Victory (Cross-Platform) | Identical API for Web and Mobile; handles polar/radar charts for elements |
| Persistence | Firestore (Document-per-Chart) | High-speed reads, handles up to 1MB JSON, and easy to scale |
| Intelligence | Gemini (Server-side) | Keeps your Bazi data invisible to the client; cheaper token handling on the backend |
