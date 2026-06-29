/**
 * Individual profile endpoints
 *
 * GET    /api/profiles/[profileId] — fetch a single profile (owner only)
 * DELETE /api/profiles/[profileId] — delete a profile (owner only)
 *
 * Every profile is owned at creation (anonymous guest or permanent account), so both verbs
 * require the caller to be the owner. Ownership transfer happens only via /api/profiles/migrate;
 * there is no client-facing claim endpoint.
 */

import { NextRequest, NextResponse } from 'next/server';
import { findProfile, deleteProfile } from '@/lib/profilesDb';
import { verifyIdToken } from '@/lib/firebaseAdmin';

/** Extract the caller's verified Firebase UID from the Bearer token, or null if absent/invalid. */
async function uidFromRequest(request: NextRequest): Promise<string | null> {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader?.startsWith('Bearer ')) return null;
  return verifyIdToken(authHeader.slice(7));
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ profileId: string }> }
): Promise<NextResponse> {
  const { profileId } = await params;
  const profile = await findProfile(profileId);
  if (!profile) {
    return NextResponse.json({ error: 'Profile not found' }, { status: 404 });
  }
  if ((await uidFromRequest(request)) !== profile.userId) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
  }
  return NextResponse.json(profile);
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ profileId: string }> }
): Promise<NextResponse> {
  try {
    const { profileId } = await params;
    const profile = await findProfile(profileId);
    if (!profile) {
      return NextResponse.json({ error: 'Profile not found' }, { status: 404 });
    }
    if ((await uidFromRequest(request)) !== profile.userId) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }
    await deleteProfile(profileId);
    return NextResponse.json({ ok: true });
  } catch (error) {
    console.error('Error deleting profile:', error);
    return NextResponse.json(
      { error: 'Failed to delete profile' },
      { status: 500 }
    );
  }
}
