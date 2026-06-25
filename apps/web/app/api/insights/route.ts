import { NextRequest, NextResponse } from 'next/server';
import { verifyIdToken } from '@/lib/firebaseAdmin';
import {
  getCachedInsights,
  setCachedInsights,
  setCachedInsightsSection,
} from '@/lib/insightsCacheDb';
import { getCachedChart } from '@/lib/chartCacheDb';
import { fetchInsights, type RequestContext } from '@/lib/fastApiClient';

export async function POST(request: NextRequest): Promise<NextResponse> {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader?.startsWith('Bearer ')) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const uid = await verifyIdToken(authHeader.slice(7));
  if (!uid) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await request.json();
  const { chartKey, section, force, profileId } = body;
  // Correlation id: reuse the client-supplied one (so a whole report generation shares
  // an id across its 6 section calls), else mint one. Flows to FastAPI via X-Request-Id.
  const requestId: string = body.requestId || crypto.randomUUID();
  if (!chartKey) {
    return NextResponse.json({ error: 'chartKey required' }, { status: 400 });
  }

  // Trace context forwarded to FastAPI so its logs carry the same anchors.
  const ctx: RequestContext = { requestId, chartKey, uid, profileId };

  // ── Single-section path (progressive/parallel loading) ──────────────────────
  // Returns { sections: { [section]: text } }. Reads/writes only that section so
  // the 6 parallel requests don't clobber each other (Firestore merge).
  if (section) {
    if (!force) {
      const cached = await getCachedInsights(chartKey);
      const existing = cached?.sections?.[section];
      if (existing) return NextResponse.json({ sections: { [section]: existing } });
    }
    const chart = await getCachedChart(chartKey);
    if (!chart) {
      return NextResponse.json({ error: 'Chart not found for this key' }, { status: 404 });
    }
    try {
      const result = await fetchInsights(chart.data, section, ctx);
      const text = result.sections?.[section] ?? '';
      await setCachedInsightsSection(chartKey, section, text);
      return NextResponse.json({ sections: { [section]: text } });
    } catch (err) {
      console.error(
        JSON.stringify({
          event: 'insights_section_error',
          requestId,
          uid,
          chartKey,
          section,
          message: err instanceof Error ? err.message : String(err),
        }),
      );
      return NextResponse.json({ error: 'Failed to generate insights' }, { status: 502 });
    }
  }

  // ── Full-report path ────────────────────────────────────────────────────────
  // Fast path: already cached. `force` (dev regenerate) skips the cache read so prompt/data
  // edits take effect. A doc without populated `sections` is a stale (pre-multi-section) shape
  // — treat it as a miss so it regenerates and overwrites.
  if (!force) {
    const cached = await getCachedInsights(chartKey);
    if (cached?.sections && Object.keys(cached.sections).length) {
      return NextResponse.json(cached);
    }
  }

  const chart = await getCachedChart(chartKey);
  if (!chart) {
    return NextResponse.json({ error: 'Chart not found for this key' }, { status: 404 });
  }

  try {
    const insights = await fetchInsights(chart.data, undefined, ctx);
    await setCachedInsights(chartKey, insights);
    return NextResponse.json(insights);
  } catch (err) {
    console.error(
      JSON.stringify({
        event: 'insights_report_error',
        requestId,
        uid,
        chartKey,
        message: err instanceof Error ? err.message : String(err),
      }),
    );
    return NextResponse.json({ error: 'Failed to generate insights' }, { status: 502 });
  }
}
