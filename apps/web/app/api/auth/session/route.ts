/**
 * Session cookie endpoints.
 *
 * POST   /api/auth/session  — body { idToken } → mint and set the __session cookie.
 * DELETE /api/auth/session  — clear the cookie (sign-out).
 *
 * The client calls POST after every sign-in (anonymous, link, or password) so the server
 * always has a verifiable identity for SSR. Mutations still authenticate via Bearer tokens.
 */

import { NextRequest, NextResponse } from 'next/server';
import { createSessionCookie, SESSION_COOKIE, sessionCookieOptions } from '@/lib/session';

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

export async function DELETE(): Promise<NextResponse> {
  const res = NextResponse.json({ ok: true });
  // Expire the cookie immediately.
  res.cookies.set(SESSION_COOKIE, '', sessionCookieOptions(0));
  return res;
}
