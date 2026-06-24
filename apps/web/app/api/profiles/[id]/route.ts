/**
 * Individual profile endpoints
 *
 * GET /api/profiles/[id] — fetch a single profile
 * DELETE /api/profiles/[id] — delete a profile
 */

import { NextRequest, NextResponse } from 'next/server';
import { findProfile, deleteProfile } from '@/lib/profilesDb';
import { verifyIdToken, getDb } from '@/lib/firebaseAdmin';

export async function GET(
  _: NextRequest,
  { params }: { params: Promise<{ id: string }> }
): Promise<NextResponse> {
  const { id } = await params;
  const profile = await findProfile(id);
  if (!profile) {
    return NextResponse.json(
      { error: 'Profile not found' },
      { status: 404 }
    );
  }
  return NextResponse.json(profile);
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
): Promise<NextResponse> {
  try {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader?.startsWith('Bearer ')) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    const uid = await verifyIdToken(authHeader.slice(7));
    if (!uid) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { id } = await params;
    const { userId } = await request.json();

    if (userId !== uid) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    await getDb().collection('profiles').doc(id).update({ userId });
    return NextResponse.json({ ok: true });
  } catch (error) {
    console.error('Error claiming profile:', error);
    return NextResponse.json({ error: 'Failed to update profile' }, { status: 500 });
  }
}

export async function DELETE(
  _: NextRequest,
  { params }: { params: Promise<{ id: string }> }
): Promise<NextResponse> {
  try {
    const { id } = await params;
    await deleteProfile(id);
    return NextResponse.json({ ok: true });
  } catch (error) {
    console.error('Error deleting profile:', error);
    return NextResponse.json(
      { error: 'Failed to delete profile' },
      { status: 500 }
    );
  }
}
