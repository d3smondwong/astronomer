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
  usedSolarTime?: boolean;
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
 * Optionally converts birth date/time to True Solar Time, calculates the four pillars,
 * determines element balance, lucky elements, and personality traits.
 */
export async function calculateBazi(
  profile: Omit<BaziProfile, 'id' | 'baziChart'>,
  useSolarTimeCorrection: boolean = false
): Promise<BaziChart> {
  // Combine birth date and time into a single datetime
  const [hours, minutes] = profile.birthTime.split(':').map(Number);
  const birthDateTime = new Date(profile.birthDate);
  birthDateTime.setHours(hours, minutes, 0, 0);

  // Get the lunar date - either via TST conversion or directly from standard time
  let bazi: any;

  if (useSolarTimeCorrection) {
    // Convert to True Solar Time using lunar library
    const result = await getTrueSolarTime(
      birthDateTime,
      profile.latitude,
      profile.longitude
    );
    bazi = result.lunarDate.getEightChar();
  } else {
    // Use standard clock time directly
    const Solar = (await import('lunar-javascript/index.js')).Solar;
    const lunarDate = Solar.fromYmdHms(
      birthDateTime.getFullYear(),
      birthDateTime.getMonth() + 1,
      birthDateTime.getDate(),
      birthDateTime.getHours(),
      birthDateTime.getMinutes(),
      0
    );
    bazi = lunarDate.getLunar().getEightChar();
  }
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
