/**
 * Next.js Route Handler: POST /api/chart
 *
 * Accepts birth data, computes (or reuses) the natal chart and its LLM insights,
 * caches both in Firestore (chartCache / insightsCache), and writes a profile
 * document that references them by chartKey.
 *
 * In Phase 2, this will additionally verify Firebase ID tokens.
 */

import { NextRequest, NextResponse } from 'next/server';
import { revalidatePath } from 'next/cache';
import {
  fetchNatalChart,
  BirthInputPayload,
  ChartResponse,
  type RequestContext,
} from '@/lib/fastApiClient';
import { createProfile, readProfiles, type ProfileRecord } from '@/lib/profilesDb';
import { verifyToken } from '@/lib/firebaseAdmin';
import { setCachedChart } from '@/lib/chartCacheDb';
import { toClientError } from '@/lib/errors';

interface ChartRequestBody {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  gender: number;
  latitude: number;
  longitude: number;
  use_solar_time_correction?: boolean;
  profileName?: string;
  birthLocation?: string;
  skipInsights?: boolean;
  requestId?: string;
}

interface ChartResponseBody {
  profileId: string;
  baziChart: ChartResponse;
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    // Every request carries a token now (anonymous guests included). Identify the caller and
    // own the profile at creation; anonymous tokens are guests.
    const authHeader = request.headers.get('Authorization');
    const caller = authHeader?.startsWith('Bearer ')
      ? await verifyToken(authHeader.slice(7))
      : null;
    if (!caller) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    const userId = caller.uid;

    // Parse request body
    const body: ChartRequestBody = await request.json();

    // Validate required fields
    if (
      typeof body.year !== 'number' ||
      typeof body.month !== 'number' ||
      typeof body.day !== 'number' ||
      typeof body.hour !== 'number' ||
      typeof body.minute !== 'number' ||
      typeof body.gender !== 'number' ||
      typeof body.latitude !== 'number' ||
      typeof body.longitude !== 'number'
    ) {
      return NextResponse.json(
        { error: 'Invalid input: missing or invalid birth data fields' },
        { status: 400 }
      );
    }

    // Guest limit: a guest (anonymous) gets one free chart; further charts require an account.
    // NOTE: this count-then-create is intentionally non-atomic. The client already disables the
    // submit button during a request (no single-tab double-submit), so the only way past this is
    // two tabs/devices firing concurrently — rare, and the worst case is a guest getting 2 free
    // charts. Not worth a Firestore transaction for that; revisit if it's ever abused.
    if (caller.isAnonymous && (await readProfiles(userId)).length >= 1) {
      return NextResponse.json(
        { error: 'Guest chart limit reached. Please create an account to add more.' },
        { status: 409 }
      );
    }

    // Build birth input for FastAPI
    const birthInput: BirthInputPayload = {
      year: body.year,
      month: body.month,
      day: body.day,
      hour: body.hour,
      minute: body.minute,
      gender: body.gender,
      latitude: body.latitude,
      longitude: body.longitude,
      use_solar_time_correction: body.use_solar_time_correction ?? true,
    };

    // Trace context forwarded to FastAPI (X-* headers) so its logs share these ids.
    // requestId originates in the browser (BaziProfileForm) and spans browser → Next →
    // FastAPI; profileId is minted up-front so the natal/insights compute logs carry it.
    const requestId: string = body.requestId || crypto.randomUUID();
    const profileId = `profile_${Date.now()}`;
    const natalCtx: RequestContext = { requestId, uid: userId, profileId };

    // The chart compute is cheap and is the only source of the 八字-based key (the frontend
    // can't derive it), so always call /natal. This natal call has no chartKey in its trace
    // ctx yet — it is the call that *produces* the key.
    const baziChart = await fetchNatalChart(birthInput, natalCtx);
    const chartKey = baziChart.chart_key;

    // Cache the deterministic chart so the profile read path renders without recomputing.
    await setCachedChart(chartKey, baziChart.data);

    // Insights are intentionally NOT generated here. The chart compute is fast; the insights
    // pass is slow and would block this response (and the redirect). Insights are also
    // per-profile (not shared by chartKey), so the profile page generates them progressively
    // via /api/insights once it knows the profileId. body.skipInsights is now unused.

    const profileRecord: ProfileRecord = {
      profileId,
      name: body.profileName || `Profile ${new Date().toLocaleDateString()}`,
      birthLocation: body.birthLocation || 'Unknown',
      birthData: {
        year: body.year,
        month: body.month,
        day: body.day,
        hour: body.hour,
        minute: body.minute,
        gender: body.gender,
        latitude: body.latitude,
        longitude: body.longitude,
        use_solar_time_correction: body.use_solar_time_correction ?? true,
      },
      createdAt: new Date().toISOString(),
      chartKey,
      userId, // always owned at creation (anonymous guest or permanent account)
    };

    // Write profile document (references chart/insights by chartKey)
    await createProfile(profileRecord);

    // The dashboard sidebar is server-rendered from this collection, and app/page.tsx's
    // redirect decision reads it too — both must see the new profile. 'layout' rooted at '/'
    // is what reaches a shared layout. Route handlers can revalidate just like Server Actions,
    // which is why chart creation didn't need converting to one.
    revalidatePath('/', 'layout');

    // Return response with cache headers
    return NextResponse.json(
      {
        profileId,
        baziChart,
      } as ChartResponseBody,
      {
        status: 200,
        headers: {
          'Cache-Control': 'no-store, private',
        },
      }
    );
  } catch (error) {
    // The log keeps everything — a FastApiError's message carries the raw upstream
    // body. The client gets only toClientError's fixed prose, which is why the two
    // lines below must never be collapsed into one.
    console.error('Error in /api/chart:', error);

    const { message, status, code } = toClientError(error);
    return NextResponse.json({ error: message, code }, { status });
  }
}
