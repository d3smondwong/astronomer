---
paths:
  - "apps/web/**"
---

# Frontend rules (Next.js, `apps/web`)

## Boundaries
- **Zero BaZi calculation in the browser.** No `lunar-javascript` or other calendar/BaZi math; the
  frontend only displays backend JSON.
- **Server Components by default.** `'use client'` only for interactive forms and context providers.
- **Server/client module boundary:** `lib/fastApiClient.ts` reads `FASTAPI_BEARER_TOKEN` at module
  scope, so it — and every Admin-SDK module (`firebaseAdmin`, `session`, `profilesDb`,
  `chartCacheDb`, `insightsCacheDb`) — carries `import 'server-only'`. The FastAPI request and
  response *types* live in `types/api.ts`, which both sides may import; `fastApiClient` re-exports
  them for server-side callers. A client component that needs a response shape imports
  `@/types/api`, never `@/lib/fastApiClient`.
- **Ownership is checked server-side** (`profile.userId === uid`) in every profile route.
- `components/` holds only what crosses route groups; route-specific UI is colocated with its route.
- Strict types matching the backend payloads; keep Chinese keys (see `api-contract.md`).

## Styling (theming single source of truth)
- **Colors and fonts are defined in exactly two places, kept in sync:** `styles/theme.css` (CSS land — Tailwind `@theme` brand tokens + semantic `:root` vars) and `lib/theme.ts` (JS land — `palette`, `goldAlpha()`, `fonts`, `strengthScale`, `antdTheme`). Never write a brand hex literal (`#735c00`, `#4d4635`, `#d4af37`, `rgba(115,92,0,…)`, …) in a component.
- **Components style with Tailwind utilities on those tokens** (`bg-parchment`, `text-gold-deep/60`, `border-gold-deep/15`, `font-serif`, `font-zh`, `font-zh-sans`). Repeated composites (sidebar rows, CTAs, badges) are named classes in `styles/components.css` under `@layer components`; responsive layout math lives in `styles/dashboard.css`.
- **Inline `style={{}}` is allowed only for** (a) genuinely dynamic values (score-driven heights, percent positions, data-driven category colors) and (b) antd/MUI component props, fed from `lib/theme.ts` — antd/MUI inject unlayered CSS-in-JS that beats layered utilities, and antd seed tokens must be literal values. Never mutate styles in `onMouseEnter`/`onMouseLeave` — use `:hover` rules or `data-active` attributes.
- **Cascade layers:** antd's `reset.css` is imported in `globals.css` into `layer(base)` — do not re-import it unlayered in `layout.tsx` (unlayered CSS silently overrides every utility, e.g. `button { color: inherit }`, `a { color: blue }`). Rules that must beat antd's own component CSS sit *below* the `@layer` block in `components.css` (see `.sidebar-shell`, `.profile-delete-btn`).
- **Fonts load via `next/font` in `app/layout.tsx`** (Noto Serif, Ma Shan Zheng, Noto Sans SC) and resolve through `--font-noto-serif` / `--font-ma-shan-zheng` / `--font-noto-sans-sc`; never add Google Fonts `@import` or inline `fontFamily`.
- **Five-element presentation constants** (`ELEMENT_ICONS`, `ELEMENT_EN`, `ELEMENT_COLOR`) come from `lib/elements.ts` — never redefine them per component.
- **User feedback: no toasts.** Success is communicated by the UI change itself (navigation, list update); errors render inline at the point of action (antd `<Alert>`, per-section error state with Retry) and always go through `reportClientError`.
- Dark mode is deliberately dormant: the `.dark` block in `theme.css` stays, `next-themes` is not installed. Semantic tokens (`--background`, `--primary`, …) already point at brand values so wiring a toggle later only needs a designed `.dark` palette + provider.

## Error boundaries
- `app/error.tsx` covers everything outside `(dashboard)`; `(dashboard)/error.tsx` renders inside the
  shell so the sidebar survives; both share `components/ErrorState.tsx`.
- `app/global-error.tsx` REPLACES the root layout, so it re-declares `<html>`/`<body>`,
  `globals.css` and the three `next/font` instances.
- `app/not-found.tsx` does a server-side `redirect('/')` and renders nothing.
