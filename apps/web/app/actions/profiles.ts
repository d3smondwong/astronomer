'use server';

/**
 * Profile Server Actions.
 *
 * Why actions rather than route handlers: these mutations must invalidate server-rendered
 * data (the dashboard sidebar's profile list, and app/page.tsx's redirect decision). An action
 * can call revalidatePath and let the framework own the cache; a client fetch would leave us
 * hand-patching local state, which is what these replace.
 *
 * AUTH IS BEARER, NOT COOKIE — deliberately. The session cookie can lag the client's real
 * identity: right after an anonymous→permanent upgrade the cookie may still carry the old
 * anonymous uid while the client holds a fresh permanent-uid token (see the ordering comment in
 * components/BaziProfileForm.tsx). Reading cookies() here would attribute mutations to the wrong
 * user. Taking the ID token as an explicit argument means an action sees exactly what the route
 * handler it replaced saw. This is also stronger than cookie auth against CSRF — Next verifies
 * Origin/Host on action POSTs, and the credential is an argument rather than ambient, so a
 * cross-site caller cannot obtain it.
 *
 * CONTRACT: actions never throw across the boundary. Next masks server error messages in
 * production, so a thrown error reaches the client as an opaque digest and the inline <Alert>
 * has nothing to show. Every path returns a discriminated union; the real stack stays in
 * Cloud Logging via console.error. Keep arguments to ids and primitives.
 */

import { revalidatePath } from 'next/cache';
import { findProfile, deleteProfile, readProfiles } from '@/lib/profilesDb';
import { verifyToken } from '@/lib/firebaseAdmin';

export type ActionErrorCode =
  | 'unauthorized'
  | 'forbidden'
  | 'not_found'
  | 'server_error';

export type DeleteProfileResult =
  /** `remaining` is the caller's profile count after the delete — 0 means they have none left. */
  | { ok: true; remaining: number }
  | { ok: false; code: ActionErrorCode };

/**
 * Delete a profile the caller owns, along with its cached insights.
 *
 * `idToken` is a Firebase ID token from the browser (`user.getIdToken()`), verified here.
 */
export async function deleteProfileAction(
  idToken: string,
  profileId: string
): Promise<DeleteProfileResult> {
  try {
    const caller = await verifyToken(idToken);
    if (!caller) return { ok: false, code: 'unauthorized' };

    const profile = await findProfile(profileId);
    if (!profile) return { ok: false, code: 'not_found' };
    if (caller.uid !== profile.userId) return { ok: false, code: 'forbidden' };

    // Also clears the per-profile insights cache; chartCache is shared by 八字 key and
    // is intentionally left alone (see lib/profilesDb.ts).
    await deleteProfile(profileId);

    // 'layout' rooted at '/' is the only form that reaches the dashboard sidebar, which lives
    // in a shared layout — a page-level revalidation would leave the deleted row on screen.
    // It also covers app/page.tsx (whose redirect() reads the now-changed list, and which the
    // client navigates to immediately after) and the deleted profile's own route (so a
    // Back-button hit re-runs the SSR ownership check instead of rendering from cache).
    revalidatePath('/', 'layout');

    // Read *after* the delete so callers can tell "that was your last chart" without holding a
    // profile list of their own — the client-side list is exactly what this work removes.
    const remaining = (await readProfiles(caller.uid)).length;
    return { ok: true, remaining };
  } catch (error) {
    console.error(`Error deleting profile ${profileId}:`, error);
    return { ok: false, code: 'server_error' };
  }
}
