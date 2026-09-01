'use client';

/**
 * useBreakpoint — the single viewport-tier source of truth for client components.
 *
 * Replaces five hand-rolled `resize` listeners that sat at four different numbers
 * (640 / 720 / 1024 / 1024). Two things are deliberate here:
 *
 * 1. `useSyncExternalStore`, not `useState` + `useEffect`. The old card hooks seeded
 *    state with `typeof window !== 'undefined' && window.innerWidth < N`, which returns
 *    the *real* width on the client's first render and so disagrees with the server HTML
 *    — a hydration mismatch. Reading through a store keeps the server render and the
 *    hydrating client render in agreement (both `false`), then re-reads immediately
 *    after hydration. No isMounted flag, no setState in an effect.
 *
 * 2. `matchMedia` change events, not `resize`. `resize` fires on every pixel of a drag
 *    and on mobile keyboard/URL-bar shifts; a media query fires only when the answer
 *    actually flips.
 *
 * Because the server snapshot is always `false`, prefer a CSS media query / Tailwind
 * `md:` prefix whenever the change is purely presentational — CSS is correct on the
 * first paint, this hook is only correct after hydration. Use it where CSS cannot
 * reach: inline numeric props, and layout switches that change the rendered tree.
 */

import { useSyncExternalStore } from 'react';

/** Phone tier. Matches Tailwind's `md`, so `md:` prefixes and this hook agree. */
export const MOBILE_BREAKPOINT = 768;
/** Sidebar collapses to an icon rail below this. Matches Tailwind's `lg`. */
export const TABLET_BREAKPOINT = 1024;

interface QueryBinding {
  subscribe: (onStoreChange: () => void) => () => void;
  getSnapshot: () => boolean;
}

// One binding per query string, cached so useSyncExternalStore sees a stable
// subscribe identity across renders and does not tear down its subscription.
const bindings = new Map<string, QueryBinding>();

function getBinding(query: string): QueryBinding {
  const cached = bindings.get(query);
  if (cached) return cached;

  // The MediaQueryList is created on first *call*, not here: getBinding runs during
  // render, and render also happens on the server where matchMedia does not exist.
  let mql: MediaQueryList | null = null;
  const list = () => (mql ??= window.matchMedia(query));

  const binding: QueryBinding = {
    subscribe: (onStoreChange) => {
      const m = list();
      m.addEventListener('change', onStoreChange);
      return () => m.removeEventListener('change', onStoreChange);
    },
    getSnapshot: () => list().matches,
  };
  bindings.set(query, binding);
  return binding;
}

// Hoisted so the identity is stable; React only calls this, but there is no reason
// to allocate a closure per render.
const serverSnapshot = () => false;

/**
 * Subscribe to a media query. Returns `false` on the server and for the first
 * client render, then the real value.
 */
export function useMediaQuery(query: string): boolean {
  const { subscribe, getSnapshot } = getBinding(query);
  return useSyncExternalStore(subscribe, getSnapshot, serverSnapshot);
}

/** True below 768px. */
export function useIsMobile(): boolean {
  return useMediaQuery(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
}

/** True below 1024px — the tier at which the desktop sidebar becomes an icon rail. */
export function useIsBelowTablet(): boolean {
  return useMediaQuery(`(max-width: ${TABLET_BREAKPOINT - 1}px)`);
}
