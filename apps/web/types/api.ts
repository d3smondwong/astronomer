/**
 * FastAPI wire contract — request payloads and response shapes.
 *
 * These live here, apart from lib/fastApiClient.ts, because both sides of the boundary need
 * them: Server Components and Route Handlers that CALL FastAPI, and client components that
 * merely RENDER what came back (ProfilePageClient reads InsightsResponse / StructuredSection).
 *
 * fastApiClient is `server-only` and reads FASTAPI_BEARER_TOKEN at module scope, so a client
 * component must never import from it. Type-only imports are erased and would happen to work,
 * but that leaves the browser bundle one careless `import { fetchInsights }` away from pulling
 * in a module that reads a secret. Types belong on the shared side of that line; transport
 * does not.
 *
 * Chinese-keyed chart payloads stay `Record<string, any>` here — see types/baziChart.ts and
 * types/cyclesChart.ts for the structures the UI actually reads.
 */

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

export interface CyclesInputPayload extends BirthInputPayload {
  /** 大运 index (0-9); when set, that decade's 流年 list is populated. */
  da_yun_index?: number;
}

export interface CyclesApiResponse {
  /** 起运 + 大运 list — Chinese-keyed; see types/cyclesChart.ts CyclesData. */
  data: Record<string, any>;
  /**
   * Log-correlation key ONLY. Cycles depend on the exact birth instant, which
   * this 八字-based key excludes — never cache cycle data under it.
   */
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
