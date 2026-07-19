/**
 * Unmatched URL → send the user straight home. No 404 page is shown.
 *
 * WHY A REDIRECT RATHER THAN A PAGE
 *
 * A rendered 404 had nothing useful to offer. Every route in this app is reached by
 * clicking (sidebar, cards, post-generation navigation), so a user who lands here has
 * no context to act on — the only sensible action was "Back to home", i.e. a button
 * whose sole job was to do what we can simply do for them.
 *
 * It was also actively broken. A rendered 404 sits inside the root layout, so
 * AuthProvider mounts, signs in anonymously, POSTs /api/auth/session and then calls
 * router.refresh() to re-render the server tree for the new identity. That refresh
 * REMOUNTS the tree on a 404 route, which resets AuthProvider's `syncedIdentityRef`
 * (a useRef — it cannot outlive its component). With the guard reset the identity
 * looks new again, so it refreshes again… producing an endless
 * 404 → POST /api/auth/session → 404 → … loop, hammering both Firebase Auth and the
 * server. Redirecting server-side means AuthProvider never mounts on this route, so
 * the loop cannot start.
 *
 * This is a Server Component on purpose: redirect() runs during the server render,
 * before any client component mounts. Do NOT reintroduce 'use client' + a
 * useEffect(router.replace) — that would mount AuthProvider first and race the loop.
 *
 * Trade-off accepted: the response is a redirect rather than a 404 status, which for a
 * public content site would be a "soft 404" and bad for SEO. This is a private,
 * auth-gated dashboard with nothing to index, so landing the user somewhere useful
 * beats returning a technically-correct status to a crawler.
 *
 * NOTE: the underlying AuthProvider remount-loop is only sidestepped here, not fixed.
 * It would resurface anywhere else the tree remounts while an identity sync is
 * pending; a durable fix would move that guard somewhere that survives a remount
 * (module scope or sessionStorage) rather than a useRef.
 */

import { redirect } from 'next/navigation';

export default function NotFound() {
  redirect('/');
}
