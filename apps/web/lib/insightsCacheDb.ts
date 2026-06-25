/**
 * insightsCache collection — LLM-generated insights derived from a cached chart.
 * Keyed by the same chartCacheKey, since insights are a pure function of the chart.
 */

import { getDb } from '@/lib/firebaseAdmin';
import type { InsightsResponse } from '@/lib/fastApiClient';

const COLLECTION = 'insightsCache';

export interface InsightsCacheDoc extends InsightsResponse {
  createdAt: string;
}

export async function getCachedInsights(key: string): Promise<InsightsResponse | null> {
  const snap = await getDb().collection(COLLECTION).doc(key).get();
  if (!snap.exists) return null;
  const { createdAt, ...insights } = snap.data() as InsightsCacheDoc;
  return insights;
}

export async function setCachedInsights(key: string, insights: InsightsResponse): Promise<void> {
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
  await getDb()
    .collection(COLLECTION)
    .doc(key)
    .set(
      { sections: { [section]: text }, createdAt: new Date().toISOString() },
      { merge: true },
    );
}
