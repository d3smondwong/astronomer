/**
 * profileDisplay — ProfileRecord (storage shape) → the shape the UI actually renders.
 *
 * `birthData` is stored as numeric parts (year/month/day/hour/minute, gender 1|0) because
 * that is what FastAPI's BirthInput takes. Every surface that shows a birth record needs
 * the same four derivations off it — a Date, a zero-padded HH:mm, a 'male'|'female'
 * string, and the TST flag — so they live here once rather than being re-derived per
 * component. Currently used by the profile page's header and the mobile birth-record panel.
 *
 * Pure and environment-free: safe to import from server or client components.
 */

import { type ProfileRecord } from '@/types/profile';

export interface DisplayProfile {
  id: string;
  name: string;
  birthDate: Date;
  /** Wall-clock birth time, zero-padded 'HH:mm'. */
  birthTime: string;
  birthLocation: string;
  gender: 'male' | 'female';
  /** Whether the chart was computed with the true-solar-time correction applied. */
  usedSolarTime: boolean;
}

export function toDisplayProfile(record: ProfileRecord): DisplayProfile {
  const { year, month, day, hour, minute, gender, use_solar_time_correction } = record.birthData;
  return {
    id: record.profileId,
    name: record.name,
    // month is 1-12 on the wire, 0-11 in Date.
    birthDate: new Date(year, month - 1, day),
    birthTime: `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`,
    birthLocation: record.birthLocation,
    gender: gender === 1 ? 'male' : 'female',
    usedSolarTime: use_solar_time_correction,
  };
}
