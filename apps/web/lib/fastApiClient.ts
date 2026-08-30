/**
 * FastAPI client for server-side use only.
 *
 * Handles communication with the FastAPI backend running at FASTAPI_URL.
 * Used by Next.js Server Components and Route Handlers.
 *
 * `server-only` is not decoration: FASTAPI_BEARER_TOKEN is read at module scope below, so
 * importing this from a client component would be a credential leak. The guard turns that
 * into a build error instead of a silent one. The wire-contract types moved to types/api.ts
 * for exactly this reason — client components need the shapes, never the transport — and are
 * re-exported here so server-side callers keep their existing import.
 */

import 'server-only';

import { FastApiError } from './errors';
import type {
  BirthInputPayload,
  ChartResponse,
  CyclesInputPayload,
  CyclesApiResponse,
  InsightsResponse,
} from '@/types/api';

const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://localhost:8000';
const FASTAPI_BEARER_TOKEN = process.env.FASTAPI_BEARER_TOKEN ?? '';

/**
 * Timeouts. Before these existed a wedged backend hung the request for the platform
 * default, which on an SSR path meant a hung page render.
 */

/** Deterministic BaZi math — 10s already exceeds patience during SSR. Below ~5s risks
 *  false positives against a cold Cloud Run instance. */
const CHART_TIMEOUT_MS = 10_000;

/** One non-streamed LLM section. Generous because a false timeout costs a regeneration. */
const INSIGHTS_TIMEOUT_MS = 60_000;

/**
 * Streaming budget — deliberately much larger, and NOT a connect timeout.
 *
 * AbortSignal.timeout() covers the entire exchange including body consumption (the
 * Fetch API has no headers-only timeout), so this bounds TOTAL generation time. A
 * stream still happily emitting deltas at T+185s would be killed. Do not "align" this
 * with INSIGHTS_TIMEOUT_MS — that would cut off long but healthy generations.
 */
const STREAM_TIMEOUT_MS = 180_000;

/**
 * The one place a FastAPI call is made.
 *
 * Returns the raw Response rather than parsed JSON so fetchInsightsStream can reuse it
 * and add only its own `!res.body` guard. Every failure leaves here as a FastApiError;
 * route handlers pass those to toClientError() and never to the client directly.
 */
async function postJson(
  endpoint: string,
  body: unknown,
  ctx: RequestContext | undefined,
  timeoutMs: number,
): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(`${FASTAPI_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(FASTAPI_BEARER_TOKEN ? { Authorization: `Bearer ${FASTAPI_BEARER_TOKEN}` } : {}),
        ...contextHeaders(ctx),
      },
      body: JSON.stringify(body),
      cache: 'no-store',
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (err) {
    // Timeout or network failure — no response was ever received.
    throw FastApiError.fromThrown(endpoint, err);
  }

  if (!res.ok) throw await FastApiError.fromResponse(endpoint, res);
  return res;
}

/**
 * Per-request log/trace context, forwarded to FastAPI as X-* headers so its logs
 * carry the same correlation ids (see apps/utils/logging.py). All fields optional —
 * a guest has no `uid`; `chartKey` is the cross-path natal↔insights join key.
 */
export interface RequestContext {
  requestId?: string;
  chartKey?: string;
  uid?: string;
  profileId?: string;
}

function contextHeaders(ctx?: RequestContext): Record<string, string> {
  if (!ctx) return {};
  return {
    ...(ctx.requestId ? { 'X-Request-Id': ctx.requestId } : {}),
    ...(ctx.chartKey ? { 'X-Chart-Key': ctx.chartKey } : {}),
    ...(ctx.uid ? { 'X-User-Id': ctx.uid } : {}),
    ...(ctx.profileId ? { 'X-Profile-Id': ctx.profileId } : {}),
  };
}

/**
 * The wire contract itself lives in types/api.ts so client components can read the shapes
 * without importing this module. Re-exported for server-side callers; new client code should
 * import from '@/types/api' directly.
 */
export type {
  BirthInputPayload,
  ChartResponse,
  CyclesInputPayload,
  CyclesApiResponse,
  InsightPoint,
  StructuredSection,
  InsightsResponse,
} from '@/types/api';

/**
 * Fetch natal chart (basic 4 pillars).
 */
export async function fetchNatalChart(
  input: BirthInputPayload,
  ctx?: RequestContext,
): Promise<ChartResponse> {
  const res = await postJson('/v1/chart/natal', input, ctx, CHART_TIMEOUT_MS);
  return res.json();
}

/**
 * Fetch 大运/流年 cycles for a birth input.
 *
 * All 10 大运 come back fully analysed; 流年 are lazy — pass da_yun_index to
 * populate one decade's 流年 list. Deterministic per (birth, gender, index),
 * so callers may cache per profileId + daYunIndex (never per chartKey).
 */
export async function fetchCycles(
  input: CyclesInputPayload,
  ctx?: RequestContext,
): Promise<CyclesApiResponse> {
  const res = await postJson('/v1/chart/cycles', input, ctx, CHART_TIMEOUT_MS);
  return res.json();
}

/**
 * Generate insights from an already-computed natal chart.
 *
 * Pass the `data` object returned by fetchNatalChart. Kept separate from chart
 * calculation so the slow LLM step never blocks chart rendering. When `section`
 * is provided, only that one section is generated (for progressive loading) and
 * the response's `sections` map contains just that key.
 */
export async function fetchInsights(
  chartData: Record<string, any>,
  section?: string,
  ctx?: RequestContext,
): Promise<InsightsResponse> {
  const res = await postJson(
    '/v1/chart/insights',
    { data: chartData, ...(section ? { section } : {}) },
    ctx,
    INSIGHTS_TIMEOUT_MS,
  );
  return res.json();
}

/**
 * Stream a single insight section from an already-computed natal chart.
 *
 * Returns the raw streaming Response (Server-Sent Events) — the caller reads
 * `res.body` and parses `data:` lines. Each event is
 * `{ section, delta: { <group>: [items] } }`, terminated by `data: [DONE]`.
 * Used by the /api/insights route handler to proxy progressive group-deltas to
 * the browser while the section generates.
 */
export async function fetchInsightsStream(
  chartData: Record<string, any>,
  section: string,
  ctx?: RequestContext,
): Promise<Response> {
  const endpoint = '/v1/chart/insights/stream';
  const res = await postJson(endpoint, { data: chartData, section }, ctx, STREAM_TIMEOUT_MS);

  // postJson already rejected every non-ok status; a 200 with no body is the one
  // failure it cannot see, and it's fatal here since the caller reads res.body.
  if (!res.body) {
    throw new FastApiError('upstream_error', endpoint, res.status, 'stream response had no body');
  }

  return res;
}

/**
 * Fetch full chart (natal + five elements).
 */
export async function fetchFullChart(input: BirthInputPayload): Promise<ChartResponse> {
  const res = await postJson('/v1/chart/full', input, undefined, CHART_TIMEOUT_MS);
  return res.json();
}
