/**
 * insightsCache collection — LLM-generated insights for a single profile.
 *
 * Keyed by `profileId`, NOT the 八字 chart key. The chart is deterministic and shared across
 * profiles with identical birth inputs (chartCache, keyed by chartKey), but insights are
 * intentionally per-profile: two profiles with the same inputs each get their own (subtly
 * different) interpretation rather than sharing one. The doc id here therefore mirrors the
 * profile doc id 1:1, and is deleted alongside the profile.
 *
 * Caching is always on: insights are read from the database and only regenerated on a miss.
 * To force a fresh regeneration during dev (the "re-generate" button), pass `force` in the
 * /api/insights request — that skips the cache read but still writes the new result back.
 */

import { getDb } from '@/lib/firebaseAdmin';
import type { InsightsResponse, StructuredSection } from '@/lib/fastApiClient';

const COLLECTION = 'insightsCache';

export interface InsightsCacheDoc extends InsightsResponse {
  createdAt: string;
}

export async function getCachedInsights(profileId: string): Promise<InsightsResponse | null> {
  const snap = await getDb().collection(COLLECTION).doc(profileId).get();
  if (!snap.exists) return null;
  const { createdAt, ...insights } = snap.data() as InsightsCacheDoc;
  return insights;
}

export async function setCachedInsights(profileId: string, insights: InsightsResponse): Promise<void> {
  const doc: InsightsCacheDoc = { ...insights, createdAt: new Date().toISOString() };
  await getDb().collection(COLLECTION).doc(profileId).set(doc);
}

/**
 * Merge a single section into the cached doc. Uses Firestore's merge so that
 * concurrent per-section writes (progressive loading fires all sections in
 * parallel) each set a distinct `sections.<key>` without clobbering siblings.
 */
export async function setCachedInsightsSection(
  profileId: string,
  section: string,
  value: string | StructuredSection,
): Promise<void> {
  await getDb()
    .collection(COLLECTION)
    .doc(profileId)
    .set(
      { sections: { [section]: value }, createdAt: new Date().toISOString() },
      { merge: true },
    );
}

/** Remove a profile's insights doc. Called when the profile itself is deleted. */
export async function deleteCachedInsights(profileId: string): Promise<void> {
  await getDb().collection(COLLECTION).doc(profileId).delete();
}
