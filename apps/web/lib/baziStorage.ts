import type { BaziProfile } from './baziOrchestrator';

/**
 * Migrate stored BaziChart data to the current field naming.
 * Handles renames that would otherwise silently break loaded profiles.
 */
function migrateBaziChart(chart: any): any {
  const migratePillar = (pillar: any) => {
    if (!pillar) return pillar;
    // mainQi → primaryQi (renamed for consistency with UI labels)
    if ('mainQi' in pillar && !('primaryQi' in pillar)) {
      const { mainQi, mainQiTenGod, ...rest } = pillar;
      return { ...rest, primaryQi: mainQi, primaryQiTenGod: mainQiTenGod ?? null };
    }
    return pillar;
  };

  // Migrate flat lifeStages (LifeStageInfo | null) to nested { xingYun, ziZuo } shape
  const migrateLifeStages = (ls: any) => {
    if (!ls) return ls;
    const migrate = (entry: any) => {
      if (entry && ('xingYun' in entry || 'ziZuo' in entry)) return entry;
      return { xingYun: entry ?? null, ziZuo: null };
    };
    return { year: migrate(ls.year), month: migrate(ls.month), day: migrate(ls.day), hour: migrate(ls.hour) };
  };

  return {
    ...chart,
    yearPillar:  migratePillar(chart.yearPillar),
    monthPillar: migratePillar(chart.monthPillar),
    dayPillar:   migratePillar(chart.dayPillar),
    hourPillar:  migratePillar(chart.hourPillar),
    lifeStages:  migrateLifeStages(chart.lifeStages),
  };
}

export function saveProfile(profile: BaziProfile): void {
  const profiles = getProfiles();
  const existingIndex = profiles.findIndex(p => p.id === profile.id);

  if (existingIndex >= 0) {
    profiles[existingIndex] = profile;
  } else {
    profiles.push(profile);
  }

  localStorage.setItem('baziProfiles', JSON.stringify(profiles));
}

export function getProfiles(): BaziProfile[] {
  const stored = localStorage.getItem('baziProfiles');
  if (!stored) return [];

  try {
    const profiles = JSON.parse(stored);
    return profiles.map((p: any) => ({
      ...p,
      birthDate: new Date(p.birthDate),
      baziChart: p.baziChart ? migrateBaziChart(p.baziChart) : undefined,
    }));
  } catch {
    return [];
  }
}

export function getProfile(id: string): BaziProfile | undefined {
  const profiles = getProfiles();
  return profiles.find(p => p.id === id);
}

export function deleteProfile(id: string): void {
  const profiles = getProfiles();
  const filtered = profiles.filter(p => p.id !== id);
  localStorage.setItem('baziProfiles', JSON.stringify(filtered));
}
