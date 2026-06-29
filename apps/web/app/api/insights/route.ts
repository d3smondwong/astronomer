import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/firebaseAdmin';
import {
  getCachedInsights,
  setCachedInsights,
  setCachedInsightsSection,
} from '@/lib/insightsCacheDb';
import { getCachedChart } from '@/lib/chartCacheDb';
import { fetchInsights, fetchInsightsStream, type RequestContext } from '@/lib/fastApiClient';
import type { StructuredSection } from '@/lib/fastApiClient';

export async function POST(request: NextRequest): Promise<Response> {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader?.startsWith('Bearer ')) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const caller = await verifyToken(authHeader.slice(7));
  if (!caller) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  // Insights are an account-only feature; anonymous guests get the chart only.
  if (caller.isAnonymous) {
    return NextResponse.json({ error: 'Account required for insights' }, { status: 403 });
  }
  const uid = caller.uid;

  const body = await request.json();
  const { chartKey, section, force, profileId } = body;
  // Correlation id: reuse the client-supplied one (so a whole report generation shares
  // an id across its 6 section calls), else mint one. Flows to FastAPI via X-Request-Id.
  const requestId: string = body.requestId || crypto.randomUUID();
  // chartKey identifies the (shared) chart to feed the LLM; profileId is the cache key for the
  // (per-profile) insights. Both are required: identical inputs share a chart but not insights.
  if (!chartKey) {
    return NextResponse.json({ error: 'chartKey required' }, { status: 400 });
  }
  if (!profileId) {
    return NextResponse.json({ error: 'profileId required' }, { status: 400 });
  }

  // Trace context forwarded to FastAPI so its logs carry the same anchors.
  const ctx: RequestContext = { requestId, chartKey, uid, profileId };

  // ── Single-section path (progressive/parallel loading) ──────────────────────
  // Returns { sections: { [section]: text } }. Reads/writes only that section so
  // the 6 parallel requests don't clobber each other (Firestore merge).
  if (section) {
    if (!force) {
      const cached = await getCachedInsights(profileId);
      const existing = cached?.sections?.[section];
      if (existing) return NextResponse.json({ sections: { [section]: existing } });
    }
    const chart = await getCachedChart(chartKey);
    if (!chart) {
      return NextResponse.json({ error: 'Chart not found for this key' }, { status: 404 });
    }
    try {
      // Proxy the SSE stream of group-deltas to the browser, forwarding bytes
      // unchanged while accumulating the merged section value to cache on [DONE].
      const upstream = await fetchInsightsStream(chart.data, section, ctx);
      const reader = upstream.body!.getReader();
      const decoder = new TextDecoder();

      // Accumulated final value: structured groups merge into `acc`; a prose section
      // (no categories — none today) instead sets `prose` and is cached as a string.
      let acc: StructuredSection = {};
      let prose: string | null = null;
      let sawDone = false;
      let sseBuffer = '';

      const stream = new ReadableStream<Uint8Array>({
        async pull(controller) {
          const { done, value } = await reader.read();
          if (done) {
            if (sawDone) {
              try {
                await setCachedInsightsSection(profileId, section, prose ?? acc);
              } catch (cacheErr) {
                console.error(
                  JSON.stringify({
                    event: 'insights_section_cache_error',
                    requestId, uid, chartKey, section,
                    message: cacheErr instanceof Error ? cacheErr.message : String(cacheErr),
                  }),
                );
              }
            }
            controller.close();
            return;
          }
          // Forward the raw SSE bytes straight to the browser.
          controller.enqueue(value);
          // Parse complete events for the accumulator (does not affect what's forwarded).
          sseBuffer += decoder.decode(value, { stream: true });
          const events = sseBuffer.split('\n\n');
          sseBuffer = events.pop() ?? '';
          for (const evt of events) {
            const line = evt.split('\n').find((l) => l.startsWith('data:'));
            if (!line) continue;
            const data = line.slice(5).trim();
            if (data === '[DONE]') { sawDone = true; continue; }
            try {
              const parsed = JSON.parse(data);
              const delta = parsed?.delta;
              if (!delta) continue;
              if (delta.__prose__ !== undefined) prose = delta.__prose__;
              else acc = { ...acc, ...delta };
            } catch {
              // Ignore partial/non-JSON lines; the browser still gets the raw bytes.
            }
          }
        },
        cancel() {
          reader.cancel().catch(() => {});
        },
      });

      return new Response(stream, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache, no-transform',
          Connection: 'keep-alive',
          'X-Accel-Buffering': 'no',
        },
      });
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
    const cached = await getCachedInsights(profileId);
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
    await setCachedInsights(profileId, insights);
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
