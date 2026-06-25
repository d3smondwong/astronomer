/**
 * profiles collection — user profile metadata.
 *
 * Each profile references its chart/insights via `chartKey` (the 八字-based key from
 * NatalChartResponse.chart_key); the chart and insights themselves live in the chartCache /
 * insightsCache collections. Backed by Firestore via the Admin SDK (local: the
 * Firestore emulator). All functions are async.
 */

import { getDb } from '@/lib/firebaseAdmin';

const COLLECTION = 'profiles';

export interface ProfileRecord {
  id: string;
  name: string;
  birthLocation: string;
  birthData: {
    year: number;
    month: number;
    day: number;
    hour: number;
    minute: number;
    gender: number;
    latitude: number;
    longitude: number;
    use_solar_time_correction: boolean;
  };
  createdAt: string;
  chartKey?: string;
  userId?: string;
}

export async function readProfiles(userId?: string): Promise<ProfileRecord[]> {
  if (!userId) return [];
  const snap = await getDb()
    .collection(COLLECTION)
    .where('userId', '==', userId)
    .orderBy('createdAt', 'desc')
    .get();
  return snap.docs.map(d => d.data() as ProfileRecord);
}

export async function findProfile(id: string): Promise<ProfileRecord | undefined> {
  const snap = await getDb().collection(COLLECTION).doc(id).get();
  return snap.exists ? (snap.data() as ProfileRecord) : undefined;
}

export async function createProfile(profile: ProfileRecord): Promise<void> {
  await getDb().collection(COLLECTION).doc(profile.id).set(profile);
}

export async function deleteProfile(id: string): Promise<void> {
  await getDb().collection(COLLECTION).doc(id).delete();
}
