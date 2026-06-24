import { NextRequest, NextResponse } from 'next/server';
import { verifyIdToken } from '@/lib/firebaseAdmin';
import { getCachedInsights, setCachedInsights } from '@/lib/insightsCacheDb';
import { getCachedChart } from '@/lib/chartCacheDb';
import { fetchInsights } from '@/lib/fastApiClient';

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
  const { chartKey } = body;
  if (!chartKey) {
    return NextResponse.json({ error: 'chartKey required' }, { status: 400 });
  }

  // Fast path: already cached
  const cached = await getCachedInsights(chartKey);
  if (cached) return NextResponse.json(cached);

  // Cache miss: look up chart and generate
  const chart = await getCachedChart(chartKey);
  if (!chart) {
    return NextResponse.json({ error: 'Chart not found for this key' }, { status: 404 });
  }

  try {
    const insights = await fetchInsights(chart.data);
    await setCachedInsights(chartKey, insights);
    return NextResponse.json(insights);
  } catch (err) {
    console.error('Insights generation error:', err);
    return NextResponse.json({ error: 'Failed to generate insights' }, { status: 502 });
  }
}
