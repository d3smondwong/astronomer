/**
 * chartCache collection — the deterministic natal chart, computed once per
 * unique birth input and reused. Keyed by chartCacheKey(birthData).
 */

import { getDb } from '@/lib/firebaseAdmin';

const COLLECTION = 'chartCache';

export interface ChartCacheDoc {
  data: Record<string, any>; // Chinese-keyed orchestrator output
  createdAt: string;
}

export async function getCachedChart(key: string): Promise<ChartCacheDoc | null> {
  const snap = await getDb().collection(COLLECTION).doc(key).get();
  return snap.exists ? (snap.data() as ChartCacheDoc) : null;
}

export async function setCachedChart(key: string, data: Record<string, any>): Promise<void> {
  const doc: ChartCacheDoc = { data, createdAt: new Date().toISOString() };
  await getDb().collection(COLLECTION).doc(key).set(doc);
}
