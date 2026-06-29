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
 * Resolve the current caller from the session cookie, or null if absent/invalid.
 *
 * checkRevoked is intentionally OFF: it would add a per-request Auth lookup to detect revoked
 * sessions / disabled accounts, but sign-out here only clears the cookie (no revokeRefreshTokens),
 * so there is nothing to detect. If a true "sign out everywhere" / account-disable flow is added,
 * revoke on sign-out and flip this to verifySessionCookie(cookie, true).
 */
export async function getSessionUser(): Promise<VerifiedUser | null> {
  const cookie = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!cookie) return null;
  try {
    const decoded = await getAdminAuth().verifySessionCookie(cookie);
    return { uid: decoded.uid, isAnonymous: decoded.firebase?.sign_in_provider === 'anonymous' };
  } catch {
    return null;
  }
}
