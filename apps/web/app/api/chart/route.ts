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
import {
  fetchNatalChart,
  fetchInsights,
  BirthInputPayload,
  ChartResponse,
} from '@/lib/fastApiClient';
import { createProfile, type ProfileRecord } from '@/lib/profilesDb';
import { chartCacheKey } from '@/lib/cacheKey';
import { verifyIdToken } from '@/lib/firebaseAdmin';
import { getCachedChart, setCachedChart } from '@/lib/chartCacheDb';
import { getCachedInsights, setCachedInsights } from '@/lib/insightsCacheDb';

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
}

interface ChartResponseBody {
  profileId: string;
  baziChart: ChartResponse;
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    // Extract userId from Bearer token (optional — profiles created without auth are anonymous).
    const authHeader = request.headers.get('Authorization');
    let userId: string | undefined;
    if (authHeader?.startsWith('Bearer ')) {
      userId = (await verifyIdToken(authHeader.slice(7))) ?? undefined;
    }

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

    // Deterministic key — identical births reuse the same cached chart/insights.
    const chartKey = chartCacheKey(birthInput);

    // chartCache: get-or-compute the deterministic natal chart.
    let baziChart: ChartResponse;
    const cachedChart = await getCachedChart(chartKey);
    if (cachedChart) {
      baziChart = { lunar_date: '', gender: '', zodiac: '', data: cachedChart.data };
    } else {
      baziChart = await fetchNatalChart(birthInput);
      await setCachedChart(chartKey, baziChart.data);
    }

    // insightsCache: only generate LLM insights for authenticated users.
    if (!body.skipInsights && userId && !(await getCachedInsights(chartKey))) {
      try {
        const insights = await fetchInsights(baziChart.data);
        await setCachedInsights(chartKey, insights);
      } catch (insightsError) {
        console.error('Error generating insights (non-fatal):', insightsError);
      }
    }

    // Generate profile ID (Firestore doc id)
    const profileId = `profile_${Date.now()}`;

    const profileRecord: ProfileRecord = {
      id: profileId,
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
      ...(userId && { userId }),
    };

    // Write profile document (references chart/insights by chartKey)
    await createProfile(profileRecord);

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
    console.error('Error in /api/chart:', error);

    // Return error response
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json(
      { error: errorMessage },
      { status: 500 }
    );
  }
}
