/**
 * profiles collection — user profile metadata.
 *
 * Each profile references its (shared) chart via `chartKey` (the 八字-based key from
 * NatalChartResponse.chart_key), stored in chartCache. Its insights are per-profile and live
 * in insightsCache keyed by the profile id. Backed by Firestore via the Admin SDK (local: the
 * Firestore emulator). All functions are async.
 */

import { getDb } from '@/lib/firebaseAdmin';
import { deleteCachedInsights } from '@/lib/insightsCacheDb';

const COLLECTION = 'profiles';

export interface ProfileRecord {
  profileId: string;
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
  // profileId is derived from the doc id so it's correct regardless of what's stored in the
  // document body (older docs predate the profileId field). The doc id is the source of truth.
  return snap.docs.map(d => ({ ...(d.data() as ProfileRecord), profileId: d.id }));
}

export async function findProfile(profileId: string): Promise<ProfileRecord | undefined> {
  const snap = await getDb().collection(COLLECTION).doc(profileId).get();
  return snap.exists ? { ...(snap.data() as ProfileRecord), profileId: snap.id } : undefined;
}

export async function createProfile(profile: ProfileRecord): Promise<void> {
  await getDb().collection(COLLECTION).doc(profile.profileId).set(profile);
}

export async function deleteProfile(profileId: string): Promise<void> {
  // Insights are 1:1 with the profile, so remove them too. The chart (chartCache) is shared
  // across profiles with identical inputs and is intentionally left in place.
  await Promise.all([
    getDb().collection(COLLECTION).doc(profileId).delete(),
    deleteCachedInsights(profileId),
  ]);
}

/**
 * Reassign every profile owned by `fromUid` to `toUid`. Used when a guest (anonymous) signs
 * into an existing account that can't be linked — their guest charts move to that account.
 * Returns the number of profiles moved.
 */
export async function reassignProfiles(fromUid: string, toUid: string): Promise<number> {
  const snap = await getDb().collection(COLLECTION).where('userId', '==', fromUid).get();
  if (snap.empty) return 0;
  const batch = getDb().batch();
  snap.docs.forEach((d) => batch.update(d.ref, { userId: toUid }));
  await batch.commit();
  return snap.size;
}
