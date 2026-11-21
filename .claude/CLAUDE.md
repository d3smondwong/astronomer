# Huat Life (Astronomer)

A BaZi (八字) charting platform. A Python backend computes the natal chart, 格局/用神 and
大运/流年 cycles; an LLM turns the chart into narrative insights; a Next.js frontend renders it.
All BaZi math runs server-side to protect the IP and the user's birth data.

## Commands
Activate the env first: `conda activate astronomer`. Run from the repo root unless noted.

- Full dev stack (backend :8000, Firebase emulators :4000, Next.js :3000): `start-dev.bat`
- Backend only: `python -m apps.backend.main`
- Backend tests: `python -m pytest apps/backend/tests`
- Frontend lint: `npm run lint` (in `apps/web`)
- Frontend against emulators: `npm run dev:emulated` (in `apps/web`)
- Refresh the code graph after editing code: `graphify update .`
- LLM provider: `active_provider` in `config/llm_config.yaml` (gemini | claude | huggingface | deepseek)

## Architecture
- **Backend** `apps/backend` — FastAPI (target: Cloud Run). `routers/chart.py` → `orchestrator/` →
  `astronomer_logic/` (calculation) + `data/` (classical reference tables) + `llm/` (insights).
- **Frontend** `apps/web` — Next.js App Router (target: Firebase App Hosting). Route handlers and
  Server Actions call FastAPI server-to-server via `lib/fastApiClient.ts`.
- **Data** — Firebase Auth + Firestore (`profiles`, `chartCache`, `insightsCache`), written only by
  the Next.js server through the Admin SDK.
- **Shared** — `apps/utils/logging.py` (per-request log context).
- **Reference only** — `src/astronomer_calculations/` is the legacy prototype; never import it.

Entry points: natal pipeline `orchestrator/astronomer_data_orchestrator.py`, cycles pipeline
`orchestrator/cycles_orchestrator.py`, profile page
`apps/web/app/(dashboard)/profile/[profileId]/`.

## Hard rules
- **IMPORTANT: zero BaZi calculation in the browser.** No `lunar-javascript` or calendar math in
  `apps/web`; the frontend only displays backend JSON.
- **Chinese keys end to end.** Map them to TypeScript interfaces; never rename them to camelCase.
- **Server-only modules stay server-only.** Anything reading secrets or the Admin SDK carries
  `import 'server-only'`; client code imports types from `@/types/api`.
- **Ownership is enforced server-side** (`profile.userId === uid`); cycles read birth data from the
  profile record, never from the client.
- **IMPORTANT: never cache cycle data under `chart_key`** — it excludes the birth instant that
  起运 depends on.
- **Contract changes travel together:** a response-shape change updates the backend, the matching
  `apps/web/types/*.ts`, and `.claude/rules/api-contract.md` in the same commit.
- **Use `lunar-python`** where it provides the mapping — except where a rule file says why it is
  wrong (e.g. `DaYun.getLiuNian()`, lunar-python ages).
- **BaZi formulas follow confirmed classical methodology.** If a formula or rule is uncertain, ask
  the user — do not guess.

## Rule files (`.claude/rules/`)
These load automatically when you work on matching paths. For a cross-cutting question that
touches their topic, read the file explicitly.
- `bazi-natal.md` — 七杀→偏官, 格局 vs 强弱, 从格 gate, 仇神/闲神, 五神, 用神, 假化, Python style
- `bazi-cycles.md` — 大运/流年/岁运: raw cycle ten gods, 1×4/1×5 scans, 神煞 anchors, 合 vs 冲,
  运势, 方位表, independent time axes, ages, TST frame, deferred items
- `api-contract.md` — endpoint request/response shapes, caching, headers, Firestore collections
- `frontend.md` — server/client boundary, styling and theming rules, error boundaries

## Workflow
- Tasks touching more than 3 files: propose a plan and wait for approval before coding.
- Backend change → check the frontend types, routes and components that consume it, and vice versa.
- Before calling work done, run the relevant check (pytest for backend, `npm run lint` for web) and
  report the result.
- Codebase/architecture questions: read `graphify-out/GRAPH_REPORT.md` first (god nodes,
  communities). For "how does X relate to Y", prefer `graphify query "<q>"`,
  `graphify path "<A>" "<B>"` or `graphify explain "<concept>"` over grep. If
  `graphify-out/wiki/index.md` exists, navigate it instead of raw files. The CLI is in the
  `astronomer` conda env; `graphify-out/` is git-ignored.

## Git practice
`main` is the line that ships: once deployment is wired, hosting builds from it. Whatever is on
`main` must run. Remote: `origin` = `https://github.com/d3smondwong/astronomer.git`.

**Flow — always:** branch off `main` → make clearly scoped commits → merge back into `main`
through a GitHub pull request. No change of any kind (code, docs, config) is committed to `main`
directly.

**Branches**
- Prefixes, used exactly:
  - `feature/<name>` — new functionality (e.g. `feature/cycles-timeline`)
  - `bugfix/<name>` — bug fixes (e.g. `bugfix/fastapi-bearer-auth`)
  - `refactor/<name>` — behaviour-preserving restructures
  - `docs/<name>` — documentation only (`README.md`, `.claude/`, root `*.md`)
  - `chore/<name>` — tooling, dependencies, config
- Name a branch for the goal, not its first commit (`feature/cycles-ui`, not
  `feature/cycles-tab-header`). If the work grows before the branch is pushed, rename it
  (`git branch -m old new`); once pushed with a PR, keep the name and let the PR title describe it.
- Start each branch from an up-to-date `main` (`git pull` first).

**Commits**
- **Explain before committing:** list the files, what changed in each and why, and the proposed
  message — then wait for the user's yes. Commit only what was explained; name anything left out.
- **Each commit is clearly defined by what it works on:** one logical change, revertable on its
  own, and its message names exactly that change. Never mix a BaZi-logic change with a
  frontend/chrome change, or a refactor with a behaviour change.
- Conventional Commits, as the history uses: `<type>(<scope>): <what changed>`, short and
  imperative. Types `feat`, `fix`, `refactor`, `chore`, `docs`, `test`; scopes `backend`, `cycles`,
  `web`, `llm`. E.g. `fix(backend): separate 大运/流年 into independent time axes`.
- A new module or folder updates the *Architecture* section or the relevant rule file in the same
  commit.

**Merging**
- Open the PR only after the user approves; the PR description summarises every commit on the
  branch. Merge into `main` only on the user's go-ahead, then delete the branch.

**Never**
- Force-push `main` or rewrite its history.
- Commit directly to `main` — every change goes through a branch.
- Commit, push, merge or deploy without asking the user first.
- Skip hooks (`--no-verify`).
- Commit secrets or machine-local state: `.env`, `.env.local`, `.claude/settings.local.json`,
  `apps/web/emulator-data/`, Firebase debug logs.

## Known gaps (as of 2026-11)
- **FastAPI does not verify the bearer token** that `fastApiClient.ts` sends. Fix before FastAPI is
  reachable from anywhere but localhost.
- Cycles UI: the profile page's Cycles tab is a "Coming Soon" placeholder; only
  `FavorableElementsCard` reads cycles `用神`.
- No deployment config yet (no Dockerfile / `apphosting.yaml`); everything runs locally.
- 流月/流日 not built (each 流年 carries an empty `流月: []` seam); no per-profile cycle cache yet.
- Deliberately not installed: `next-themes` (dark mode dormant), any toast library (no toasts),
  `lunar-javascript`. Check `package.json` / `requirements.txt` for versions.
