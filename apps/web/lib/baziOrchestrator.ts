// Utility functions for Bazi calculations

import { getTrueSolarTime } from './trueSolarTime';
import { Pillar, extractPillars } from './baziPillars';
import { TenGodValues, createTenGodValues } from './tenGods';
import {
  ElementBalance,
  calculateElementBalance,
  determineLuckyElements,
} from './elementBalance';
import {
  PersonalityTraits,
  generatePersonalityTraits,
  generatePersonalitySummary,
} from './personalityFromDayMaster';
import { LifeStageInfo, getLifeStageInfo, getPillarLifeStageInfo } from './twelveLifeStages';
import { NaYinInfo, getNaYinInfo } from './naYin';
import { VoidInfo, getVoidInfo } from './void';

export type FullPillar = Pillar & TenGodValues;

export interface BaziProfile {
  id: string;
  name: string;
  birthDate: Date;
  birthTime: string;
  birthLocation: string;
  gender: 'male' | 'female';
  latitude: number;
  longitude: number;
  baziChart?: BaziChart;
}

export interface BaziChart {
  yearPillar: FullPillar;
  monthPillar: FullPillar;
  dayPillar: FullPillar;
  hourPillar: FullPillar;
  elements: ElementBalance;
  luckyElements: string[];
  personalityTraits: PersonalityTraits;
  personalitySummary: string;
  lifeStages: {
    year:  { xingYun: LifeStageInfo | null; ziZuo: LifeStageInfo | null };
    month: { xingYun: LifeStageInfo | null; ziZuo: LifeStageInfo | null };
    day:   { xingYun: LifeStageInfo | null; ziZuo: LifeStageInfo | null };
    hour:  { xingYun: LifeStageInfo | null; ziZuo: LifeStageInfo | null };
  };
  naYin: {
    year:  NaYinInfo | null;
    month: NaYinInfo | null;
    day:   NaYinInfo | null;
    hour:  NaYinInfo | null;
  };
  xunKong: {
    year:  VoidInfo | null;
    month: VoidInfo | null;
    day:   VoidInfo | null;
    hour:  VoidInfo | null;
  };
}

/**
 * Combine a structural pillar with its ten god values
 */
function attachTenGods(pillar: Pillar, shiShenGan: string, shiShenZhi: string[]): FullPillar {
  return { ...pillar, ...createTenGodValues(shiShenGan, shiShenZhi) };
}

/**
 * Main Bazi calculation function
 *
 * Converts birth date/time to True Solar Time, calculates the four pillars,
 * determines element balance, lucky elements, and personality traits.
 */
export async function calculateBazi(
  profile: Omit<BaziProfile, 'id' | 'baziChart'>
): Promise<BaziChart> {
  // Combine birth date and time into a single datetime
  const [hours, minutes] = profile.birthTime.split(':').map(Number);
  const birthDateTime = new Date(profile.birthDate);
  birthDateTime.setHours(hours, minutes, 0, 0);

  // Convert to True Solar Time using lunar library
  const result = await getTrueSolarTime(
    birthDateTime,
    profile.latitude,
    profile.longitude
  );

  // Get bazi object from the TST-adjusted lunar date, then extract pillars
  const bazi = result.lunarDate.getEightChar();
  const pillars = extractPillars(bazi);

  // Extract 12 Life Stages — two sub-categories per pillar:
  // 星运 (xingYun): Day Master as reference, via lunar-javascript
  // 自坐 (ziZuo):   Own Heavenly Stem as reference, computed manually
  const lifeStages = {
    year:  { xingYun: getLifeStageInfo(bazi.getYearDiShi()),  ziZuo: getPillarLifeStageInfo(pillars.yearPillar.heavenlyStem,  pillars.yearPillar.earthlyBranch)  },
    month: { xingYun: getLifeStageInfo(bazi.getMonthDiShi()), ziZuo: getPillarLifeStageInfo(pillars.monthPillar.heavenlyStem, pillars.monthPillar.earthlyBranch) },
    day:   { xingYun: getLifeStageInfo(bazi.getDayDiShi()),   ziZuo: getPillarLifeStageInfo(pillars.dayPillar.heavenlyStem,   pillars.dayPillar.earthlyBranch)   },
    hour:  { xingYun: getLifeStageInfo(bazi.getTimeDiShi()),  ziZuo: getPillarLifeStageInfo(pillars.hourPillar.heavenlyStem,  pillars.hourPillar.earthlyBranch)  },
  };

  // Extract NaYin from lunar-javascript
  const naYin = {
    year:  getNaYinInfo(bazi.getYearNaYin()),
    month: getNaYinInfo(bazi.getMonthNaYin()),
    day:   getNaYinInfo(bazi.getDayNaYin()),
    hour:  getNaYinInfo(bazi.getTimeNaYin()),
  };

  // Extract Xun Kong / Void (空亡) from lunar-javascript
  const xunKong = {
    year:  getVoidInfo(bazi.getYearXunKong()),
    month: getVoidInfo(bazi.getMonthXunKong()),
    day:   getVoidInfo(bazi.getDayXunKong()),
    hour:  getVoidInfo(bazi.getTimeXunKong()),
  };

  const yearPillar  = attachTenGods(pillars.yearPillar,  bazi.getYearShiShenGan(),  bazi.getYearShiShenZhi());
  const monthPillar = attachTenGods(pillars.monthPillar, bazi.getMonthShiShenGan(), bazi.getMonthShiShenZhi());
  const dayPillar   = attachTenGods(pillars.dayPillar,   bazi.getDayShiShenGan(),   bazi.getDayShiShenZhi());
  const hourPillar  = attachTenGods(pillars.hourPillar,  bazi.getTimeShiShenGan(),  bazi.getTimeShiShenZhi());

  // Calculate element balance from all four pillars
  const elements = calculateElementBalance(
    yearPillar,
    monthPillar,
    dayPillar,
    hourPillar
  );

  // Determine lucky elements (the two weakest elements)
  const luckyElements = determineLuckyElements(elements);

  // Generate personality traits based on day master (day pillar's heavenly stem)
  const personalityTraits = generatePersonalityTraits(
    dayPillar.heavenlyStem
  );
  const personalitySummary = generatePersonalitySummary(personalityTraits);

  return {
    yearPillar,
    monthPillar,
    dayPillar,
    hourPillar,
    elements,
    luckyElements,
    personalityTraits,
    personalitySummary,
    lifeStages,
    naYin,
    xunKong,
  };
}


// Storage functions
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

export function getProfile(id: string): BaziProfile | undefined {
  const profiles = getProfiles();
  return profiles.find(p => p.id === id);
}

export function deleteProfile(id: string): void {
  const profiles = getProfiles();
  const filtered = profiles.filter(p => p.id !== id);
  localStorage.setItem('baziProfiles', JSON.stringify(filtered));
}
