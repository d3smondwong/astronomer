/**
 * Profile API endpoints
 *
 * GET /api/profiles — list the authenticated user's profiles.
 *
 * Profiles are created via POST /api/chart (which computes the chart key and stamps the
 * owner's userId); there is intentionally no unauthenticated create endpoint here.
 */

import { NextRequest, NextResponse } from 'next/server';
import { readProfiles } from '@/lib/profilesDb';
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
