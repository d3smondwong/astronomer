/**
 * POST /api/profiles/migrate
 *
 * Transfers a guest's (anonymous) profiles to an existing account when the two can't be
 * linked (the email was already registered). Called right after the guest signs into that
 * account.
 *
 * Auth: requires BOTH proofs of control —
 *   - Authorization: Bearer <token of the destination account>  (the now signed-in user)
 *   - body { anonIdToken }  (the anonymous session being migrated FROM)
 * Both are verified server-side; the source must be an anonymous account.
 */

import { NextRequest, NextResponse } from 'next/server';
import { revalidatePath } from 'next/cache';
import { verifyToken } from '@/lib/firebaseAdmin';
import { reassignProfiles } from '@/lib/profilesDb';

export async function POST(request: NextRequest): Promise<NextResponse> {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader?.startsWith('Bearer ')) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const dest = await verifyToken(authHeader.slice(7));
  if (!dest) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  let anonIdToken: string | undefined;
  try {
    ({ anonIdToken } = await request.json());
  } catch {
    return NextResponse.json({ error: 'Invalid body' }, { status: 400 });
  }
  if (!anonIdToken) {
    return NextResponse.json({ error: 'anonIdToken required' }, { status: 400 });
  }

  const source = await verifyToken(anonIdToken);
  if (!source || !source.isAnonymous) {
    // Only an anonymous session may be migrated, and only by proving control of it.
    return NextResponse.json({ error: 'Invalid source session' }, { status: 403 });
  }

  if (source.uid === dest.uid) {
    return NextResponse.json({ migrated: 0 }); // nothing to do (already same account)
  }

  const migrated = await reassignProfiles(source.uid, dest.uid);

  // Ownership just changed, so the server-rendered sidebar (and app/(marketing)/page.tsx's redirect
  // decision) are both stale for the destination account. Easy to miss because this runs
  // *after* the upgrade: without it, a guest who signs into an existing account sees the
  // pre-migration list until a hard reload.
  if (migrated > 0) revalidatePath('/', 'layout');

  return NextResponse.json({ migrated });
}
