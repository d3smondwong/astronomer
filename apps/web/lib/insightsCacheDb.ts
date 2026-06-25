/**
 * insightsCache collection — LLM-generated insights derived from a cached chart.
 * Keyed by the same 八字 chart key, since insights are a pure function of the chart.
 *
 * Toggle: set INSIGHTS_CACHE_ENABLED=false (e.g. in apps/web/.env.local) to disable the
 * cache entirely — reads always miss and writes are skipped, so every request regenerates
 * fresh insights. Useful while iterating on prompts. Defaults to enabled.
 */

import { getDb } from '@/lib/firebaseAdmin';
import type { InsightsResponse } from '@/lib/fastApiClient';

const COLLECTION = 'insightsCache';

// Cache is on unless explicitly disabled. Server-side only (no NEXT_PUBLIC needed).
const CACHE_ENABLED = process.env.INSIGHTS_CACHE_ENABLED !== 'false';

export interface InsightsCacheDoc extends InsightsResponse {
  createdAt: string;
}

export async function getCachedInsights(key: string): Promise<InsightsResponse | null> {
  if (!CACHE_ENABLED) return null; // disabled → always a miss, forcing regeneration
  const snap = await getDb().collection(COLLECTION).doc(key).get();
  if (!snap.exists) return null;
  const { createdAt, ...insights } = snap.data() as InsightsCacheDoc;
  return insights;
}

export async function setCachedInsights(key: string, insights: InsightsResponse): Promise<void> {
  if (!CACHE_ENABLED) return; // disabled → skip writes so testing leaves no stale entries
  const doc: InsightsCacheDoc = { ...insights, createdAt: new Date().toISOString() };
  await getDb().collection(COLLECTION).doc(key).set(doc);
}

/**
 * Merge a single section into the cached doc. Uses Firestore's merge so that
 * concurrent per-section writes (progressive loading fires all sections in
 * parallel) each set a distinct `sections.<key>` without clobbering siblings.
 */
export async function setCachedInsightsSection(
  key: string,
  section: string,
  text: string,
): Promise<void> {
  if (!CACHE_ENABLED) return; // disabled → skip writes so testing leaves no stale entries
  await getDb()
    .collection(COLLECTION)
    .doc(key)
    .set(
      { sections: { [section]: text }, createdAt: new Date().toISOString() },
      { merge: true },
    );
}
