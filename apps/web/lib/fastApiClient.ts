/**
 * FastAPI client for server-side use only.
 *
 * Handles communication with the FastAPI backend running at FASTAPI_URL.
 * Used by Next.js Server Components and Route Handlers.
 */

const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://localhost:8000';
const FASTAPI_BEARER_TOKEN = process.env.FASTAPI_BEARER_TOKEN ?? '';

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

export interface BirthInputPayload {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  gender: number; // 1 = male, 0 = female
  latitude: number;
  longitude: number;
  use_solar_time_correction?: boolean;
}

export interface ChartResponse {
  lunar_date: string;
  gender: string;
  zodiac: string;
  data: Record<string, any>;
  is_full?: boolean;
  // 八字-based cache key (8 GanZhi letters + gender) returned by /v1/chart/natal.
  // Computed server-side from the pillars — the only trustworthy source for the key.
  chart_key: string;
}

// One item inside a structured section: a crisp claim plus its grounded explanation.
export interface InsightPoint {
  point: string;
  explanation: string;
}

// A structured section (currently: career) -> named groups, each a list of points.
// e.g. { path_to_success: [...], highlights: [...], challenges: [...], advice: [...] }
export type StructuredSection = Record<string, InsightPoint[]>;

export interface InsightsResponse {
  // section key (personality | family | romance | career | wealth | health)
  // -> either narrative prose (string) or a structured groups object (career).
  sections: Record<string, string | StructuredSection>;
}

/**
 * Fetch natal chart (basic 4 pillars).
 */
export async function fetchNatalChart(
  input: BirthInputPayload,
  ctx?: RequestContext,
): Promise<ChartResponse> {
  const res = await fetch(`${FASTAPI_URL}/v1/chart/natal`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(FASTAPI_BEARER_TOKEN ? { Authorization: `Bearer ${FASTAPI_BEARER_TOKEN}` } : {}),
      ...contextHeaders(ctx),
    },
    body: JSON.stringify(input),
    cache: 'no-store',
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`FastAPI /v1/chart/natal failed: ${res.status} ${error}`);
  }

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
  const res = await fetch(`${FASTAPI_URL}/v1/chart/insights`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(FASTAPI_BEARER_TOKEN ? { Authorization: `Bearer ${FASTAPI_BEARER_TOKEN}` } : {}),
      ...contextHeaders(ctx),
    },
    body: JSON.stringify({ data: chartData, ...(section ? { section } : {}) }),
    cache: 'no-store',
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`FastAPI /v1/chart/insights failed: ${res.status} ${error}`);
  }

  return res.json();
}

/**
 * Fetch full chart (natal + five elements).
 */
export async function fetchFullChart(input: BirthInputPayload): Promise<ChartResponse> {
  const res = await fetch(`${FASTAPI_URL}/v1/chart/full`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(FASTAPI_BEARER_TOKEN ? { Authorization: `Bearer ${FASTAPI_BEARER_TOKEN}` } : {}),
    },
    body: JSON.stringify(input),
    cache: 'no-store',
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`FastAPI /v1/chart/full failed: ${res.status} ${error}`);
  }

  return res.json();
}
