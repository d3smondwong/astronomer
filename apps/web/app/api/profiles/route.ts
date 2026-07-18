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
  // Fail closed on a missing/invalid token. Previously an unauthenticated call fell through to
  // readProfiles(undefined) → [] with a 200, which the client could not distinguish from
  // "this user genuinely has no profiles" — a silent empty state instead of an auth error.
  if (!authHeader?.startsWith('Bearer ')) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const userId = await verifyIdToken(authHeader.slice(7));
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const profiles = await readProfiles(userId);
  return NextResponse.json(profiles);
}
