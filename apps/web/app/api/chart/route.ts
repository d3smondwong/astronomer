/**
 * Next.js Route Handler: POST /api/chart
 *
 * Accepts birth data from the client, calls FastAPI /v1/chart/full,
 * and returns the chart JSON with appropriate cache headers.
 *
 * In Phase 2, this will verify Firebase ID tokens and cache results in Firestore.
 */

import { NextRequest, NextResponse } from 'next/server';
import { fetchFullChart, BirthInputPayload, ChartResponse } from '@/lib/fastApiClient';
import { createProfile, type ProfileRecord } from '@/lib/profilesDb';

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
  // For Phase 2: user metadata
  profileName?: string;
  birthLocation?: string;
}

interface ChartResponseBody {
  profileId: string;
  baziChart: ChartResponse;
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
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

    // Call FastAPI backend
    const baziChart = await fetchFullChart(birthInput);

    // Generate profile ID (in Phase 2, this will be a Firestore doc ID)
    const profileId = `profile_${Date.now()}`;

    // Store profile metadata in local JSON database
    // In Phase 2, this will be replaced by Firestore
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
    };

    // Write profile to local database
    createProfile(profileRecord);

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
