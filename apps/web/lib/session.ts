/**
 * Firebase session cookies — server-side identity for SSR + route gating.
 *
 * The client signs in (anonymously or with a credential) and POSTs its ID token to
 * /api/auth/session, which mints a Firebase session cookie here. Server components and
 * route handlers then read that cookie to learn *who is asking* — something a Bearer
 * header (client-only) can't give them during SSR.
 *
 * Security model: the cookie is a Google-signed JWT (unforgeable), httpOnly (XSS can't read
 * it), Secure in production, SameSite=Lax. It authorizes idempotent SSR reads only —
 * mutations still use Bearer tokens, so there is no CSRF surface on state changes.
 */

import 'server-only';
import { cache } from 'react';
import { cookies } from 'next/headers';
import { getAdminAuth, type VerifiedUser } from '@/lib/firebaseAdmin';

// Must be exactly "__session" to survive Firebase App Hosting / CDN caching, which strips
// all other cookies.
export const SESSION_COOKIE = '__session';

// Firebase session cookies last up to 14 days; mirror that as the cookie Max-Age.
export const SESSION_EXPIRES_IN_MS = 14 * 24 * 60 * 60 * 1000;
const SESSION_MAX_AGE_SECONDS = SESSION_EXPIRES_IN_MS / 1000;

export function sessionCookieOptions(maxAgeSeconds: number = SESSION_MAX_AGE_SECONDS) {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax' as const,
    path: '/',
    maxAge: maxAgeSeconds,
  };
}

/** Mint a session cookie value from a freshly-issued ID token. Throws if the token is invalid. */
export async function createSessionCookie(idToken: string): Promise<string> {
  return getAdminAuth().createSessionCookie(idToken, { expiresIn: SESSION_EXPIRES_IN_MS });
}

/**
 * Resolve the current caller from the session cookie, or null if absent/invalid/revoked.
 *
 * checkRevoked is ON. Sign-out calls revokeRefreshTokens (see app/api/auth/session/route.ts),
 * and this flag is what gives that teeth: without it a leaked cookie stayed valid for its full
 * 14 days with no way to kill it, because signing out only cleared the cookie in the browser
 * that clicked the button. Also catches disabled accounts.
 *
 * WHY cache(): the flag turns verification from a local JWT check (~0ms, cached public keys)
 * into a network round-trip to Firebase Auth. A single /profile/<id> render calls this THREE
 * times — root layout, dashboard layout, page — and those calls cannot be collapsed by
 * restructuring, because an App Router layout receives `children` as an opaque ReactNode and
 * so cannot pass data down to a page. React's cache() memoizes per request, turning 3 lookups
 * into 1. Do not unwrap it as redundant: without it this change triples the Auth traffic of
 * every page render. Note cache() keys on arguments, so keep this function argument-free and
 * keep reading the cookie inside it.
 *
 * Requests with no cookie return before any network call, so logged-out visitors to the
 * public landing page cost nothing.
 */
export const getSessionUser = cache(async (): Promise<VerifiedUser | null> => {
  const cookie = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!cookie) return null;
  try {
    const decoded = await getAdminAuth().verifySessionCookie(cookie, true);
    return { uid: decoded.uid, isAnonymous: decoded.firebase?.sign_in_provider === 'anonymous' };
  } catch {
    // A revoked cookie throws auth/session-cookie-revoked and lands here, so it is treated
    // exactly like "no session" — which callers already handle (the profile page redirects
    // to /?login=1). No separate error path is needed.
    return null;
  }
});
