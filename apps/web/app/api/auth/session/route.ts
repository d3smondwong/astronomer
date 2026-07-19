/**
 * Session cookie endpoints.
 *
 * POST   /api/auth/session  — body { idToken } → mint and set the __session cookie.
 * DELETE /api/auth/session  — revoke the user's refresh tokens, then clear the cookie.
 *
 * The client calls POST after every sign-in (anonymous, link, or password) so the server
 * always has a verifiable identity for SSR. Mutations still authenticate via Bearer tokens.
 */

import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { createSessionCookie, SESSION_COOKIE, sessionCookieOptions } from '@/lib/session';
import { getAdminAuth } from '@/lib/firebaseAdmin';

export async function POST(request: NextRequest): Promise<NextResponse> {
  let idToken: string | undefined;
  try {
    ({ idToken } = await request.json());
  } catch {
    return NextResponse.json({ error: 'Invalid body' }, { status: 400 });
  }
  if (!idToken) {
    return NextResponse.json({ error: 'idToken required' }, { status: 400 });
  }

  try {
    // createSessionCookie verifies the ID token; an invalid/expired token throws.
    const cookieValue = await createSessionCookie(idToken);
    const res = NextResponse.json({ ok: true });
    res.cookies.set(SESSION_COOKIE, cookieValue, sessionCookieOptions());
    return res;
  } catch (error) {
    console.error('Failed to create session cookie:', error);
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
}

/**
 * Sign out: revoke the user's refresh tokens, then expire the cookie.
 *
 * The revocation is what makes sign-out mean something beyond this browser. It sets
 * tokensValidAfterTime on the user, which getSessionUser's verifySessionCookie(cookie, true)
 * then rejects — so every session cookie issued to that user, on any device, dies at once.
 * Without it a leaked cookie stayed valid for its full 14 days and nothing could kill it.
 *
 * Consequence worth knowing: revocation is per-USER, not per-device — Firebase offers no
 * per-device option — so signing out on a phone also ends the session on a laptop.
 *
 * No auth check is needed: the cookie IS the credential, so a caller can only ever revoke
 * the identity it already holds.
 */
export async function DELETE(): Promise<NextResponse> {
  const res = NextResponse.json({ ok: true });
  const cookie = (await cookies()).get(SESSION_COOKIE)?.value;

  if (cookie) {
    try {
      // checkRevoked deliberately FALSE — the opposite of getSessionUser. All we need is the
      // uid, and the weaker check is the one most likely to still yield it. It is still a
      // full signature verification: decoding without verifying would let any caller name
      // any uid and revoke a stranger's sessions.
      //
      // Measured caveat: the Auth emulator rejects an already-revoked cookie even with this
      // set to false, so on a second sign-out we land in the catch below rather than
      // re-revoking. Harmless — the tokens are already revoked and the cookie still clears.
      const { uid } = await getAdminAuth().verifySessionCookie(cookie, false);
      await getAdminAuth().revokeRefreshTokens(uid);
    } catch (error) {
      // Expired cookies land here too: verifySessionCookie rejects on expiry whatever
      // checkRevoked says, and there is no safe way to recover a uid from one. An expired
      // cookie is already worthless, so skipping revocation costs nothing.
      console.warn('Sign-out: token revocation skipped or failed', error);
    }
  }

  // ALWAYS clear, whatever happened above. A user who clicks Sign out must end up signed out
  // locally even if Firebase Auth is entirely down.
  res.cookies.set(SESSION_COOKIE, '', sessionCookieOptions(0));
  return res;
}
