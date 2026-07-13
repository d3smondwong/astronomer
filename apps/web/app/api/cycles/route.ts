/**
 * Next.js Route Handler: POST /api/cycles
 *
 * Fetches 大运/流年 cycle analysis for an existing profile. The birth data is
 * read from the profile record (never from the client) so ownership stays
 * enforced and the payload can't be spoofed. 流年 are lazy: pass daYunIndex
 * to expand one decade.
 *
 * Caching: cycle timing depends on the exact birth instant, which chartKey
 * deliberately excludes — cycle data must never be cached under chartKey.
 * The response is deterministic per (profile birth data, daYunIndex); a
 * Firestore cache per profileId + daYunIndex is a possible follow-up, but
 * this handler recomputes for now (the calculation is cheap and LLM-free).
 */

import { NextRequest, NextResponse } from 'next/server';
import { fetchCycles, type RequestContext } from '@/lib/fastApiClient';
import { findProfile } from '@/lib/profilesDb';
import { verifyIdToken } from '@/lib/firebaseAdmin';

interface CyclesRequestBody {
  profileId: string;
  /** 大运 index (0-9); when set, that decade's 流年 are included. */
  daYunIndex?: number;
  requestId?: string;
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const authHeader = request.headers.get('Authorization');
    const uid = authHeader?.startsWith('Bearer ')
      ? await verifyIdToken(authHeader.slice(7))
      : null;
    if (!uid) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body: CyclesRequestBody = await request.json();
    if (typeof body.profileId !== 'string' || !body.profileId) {
      return NextResponse.json({ error: 'Invalid input: profileId is required' }, { status: 400 });
    }
    if (
      body.daYunIndex !== undefined &&
      (!Number.isInteger(body.daYunIndex) || body.daYunIndex < 0 || body.daYunIndex > 9)
    ) {
      return NextResponse.json(
        { error: 'Invalid input: daYunIndex must be an integer 0-9' },
        { status: 400 }
      );
    }

    const profile = await findProfile(body.profileId);
    if (!profile) {
      return NextResponse.json({ error: 'Profile not found' }, { status: 404 });
    }
    if (uid !== profile.userId) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const requestId: string = body.requestId || crypto.randomUUID();
    const ctx: RequestContext = {
      requestId,
      uid,
      profileId: body.profileId,
      chartKey: profile.chartKey,
    };

    const cycles = await fetchCycles(
      {
        ...profile.birthData,
        ...(body.daYunIndex !== undefined ? { da_yun_index: body.daYunIndex } : {}),
      },
      ctx
    );

    return NextResponse.json(cycles, {
      status: 200,
      headers: {
        'Cache-Control': 'no-store, private',
      },
    });
  } catch (error) {
    console.error('Error in /api/cycles:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ error: errorMessage }, { status: 500 });
  }
}
