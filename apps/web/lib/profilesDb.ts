/**
 * Local profile database — stores profiles in apps/web/profiles directory
 * Each profile gets its own file: .{profile_name}_{date_of_birth}.json
 * Mirrors Firestore design for easy Phase 2 migration
 */

import fs from 'fs';
import path from 'path';

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
}

const PROFILES_DIR = path.join(process.cwd(), 'profiles');

function ensureProfilesDir(): void {
  if (!fs.existsSync(PROFILES_DIR)) {
    fs.mkdirSync(PROFILES_DIR, { recursive: true });
  }
}

function getProfileFileName(profile: ProfileRecord): string {
  const { year, month, day } = profile.birthData;
  const dob = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  return `.${profile.name}_${dob}.json`;
}

function getProfileFilePath(profile: ProfileRecord): string {
  return path.join(PROFILES_DIR, getProfileFileName(profile));
}

export function readProfiles(): ProfileRecord[] {
  ensureProfilesDir();

  try {
    const files = fs.readdirSync(PROFILES_DIR);
    const profiles: ProfileRecord[] = [];

    for (const file of files) {
      if (file.endsWith('.json')) {
        const filePath = path.join(PROFILES_DIR, file);
        try {
          const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
          profiles.push(data);
        } catch (e) {
          console.error(`Error reading profile file ${file}:`, e);
        }
      }
    }

    return profiles;
  } catch (e) {
    console.error('Error reading profiles directory:', e);
    return [];
  }
}

export function findProfile(id: string): ProfileRecord | undefined {
  return readProfiles().find(p => p.id === id);
}

export function createProfile(profile: ProfileRecord): void {
  ensureProfilesDir();
  try {
    const filePath = getProfileFilePath(profile);
    fs.writeFileSync(filePath, JSON.stringify(profile, null, 2));
  } catch (e) {
    console.error('Error creating profile:', e);
  }
}

export function deleteProfile(id: string): void {
  const profile = findProfile(id);
  if (!profile) return;

  try {
    const filePath = getProfileFilePath(profile);
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }
  } catch (e) {
    console.error('Error deleting profile:', e);
  }
}
