/**
 * Profile API endpoints
 *
 * GET /api/profiles — list all profiles
 * POST /api/profiles — create a new profile
 */

import { NextRequest, NextResponse } from 'next/server';
import { readProfiles, createProfile, type ProfileRecord } from '@/lib/profilesDb';
import { verifyIdToken } from '@/lib/firebaseAdmin';

export async function GET(request: NextRequest): Promise<NextResponse> {
  const authHeader = request.headers.get('Authorization');
  let userId: string | undefined;
  if (authHeader?.startsWith('Bearer ')) {
    userId = (await verifyIdToken(authHeader.slice(7))) ?? undefined;
  }
  const profiles = await readProfiles(userId);
  return NextResponse.json(profiles);
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json();
    const profile: ProfileRecord = {
      id: body.id,
      name: body.name,
      birthLocation: body.birthLocation || 'Unknown',
      birthData: body.birthData,
      createdAt: body.createdAt,
    };

    await createProfile(profile);

    return NextResponse.json(profile, { status: 201 });
  } catch (error) {
    console.error('Error creating profile:', error);
    return NextResponse.json(
      { error: 'Failed to create profile' },
      { status: 500 }
    );
  }
}
