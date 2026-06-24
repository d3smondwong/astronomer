/**
 * Deterministic cache key for a birth input.
 *
 * Identical births produce the same key, so the chart and its insights are
 * computed once and reused across profiles. Used as the document id for both
 * the chartCache and insightsCache collections.
 */

import { createHash } from 'crypto';
import type { BirthInputPayload } from '@/lib/fastApiClient';

export function chartCacheKey(birth: BirthInputPayload): string {
  const normalized = [
    birth.year,
    birth.month,
    birth.day,
    birth.hour,
    birth.minute,
    birth.gender,
    birth.latitude,
    birth.longitude,
    birth.use_solar_time_correction ?? true,
  ].join('|');
  return createHash('sha1').update(normalized).digest('hex');
}
