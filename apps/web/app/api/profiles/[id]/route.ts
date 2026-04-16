/**
 * Individual profile endpoints
 *
 * GET /api/profiles/[id] — fetch a single profile
 * DELETE /api/profiles/[id] — delete a profile
 */

import { NextRequest, NextResponse } from 'next/server';
import { findProfile, deleteProfile } from '@/lib/profilesDb';

export async function GET(
  _: NextRequest,
  { params }: { params: Promise<{ id: string }> }
): Promise<NextResponse> {
  const { id } = await params;
  const profile = findProfile(id);
  if (!profile) {
    return NextResponse.json(
      { error: 'Profile not found' },
      { status: 404 }
    );
  }
  return NextResponse.json(profile);
}

export async function DELETE(
  _: NextRequest,
  { params }: { params: Promise<{ id: string }> }
): Promise<NextResponse> {
  try {
    const { id } = await params;
    deleteProfile(id);
    return NextResponse.json({ ok: true });
  } catch (error) {
    console.error('Error deleting profile:', error);
    return NextResponse.json(
      { error: 'Failed to delete profile' },
      { status: 500 }
    );
  }
}
