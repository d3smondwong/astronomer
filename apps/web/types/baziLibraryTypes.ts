/**
 * Consolidated BaZi Library Types
 *
 * Consolidates all type definitions from the lib folder modules that have been
 * migrated to the backend. This file serves as the single source for component
 * prop typing and type-only imports.
 */

/**
 * True Solar Time Result
 */
export interface TrueSolarTimeResult {
  originalDateTime: Date;
  trueSolarDateTime: Date;
  lunarDate: any;
}

/**
 * Ten God Values for a Pillar
 */
export interface TenGodValues {
  heavenlyStemTenGod: string;       // e.g. '比肩', '日主' for Day Master
  primaryQiTenGod: string | null;   // Ten god for Primary Qi hidden stem
  middleQiTenGod: string | null;    // Ten god for Middle Qi hidden stem
  residualQiTenGod: string | null;  // Ten god for Residual Qi hidden stem
}

/**
 * Personality Traits based on Day Master
 */
export interface PersonalityTraits {
  dayMasterStem: string;
  element: string;
  archetype: string;
  traits: string[];
  strengths: string[];
  challenges: string[];
  luckyColors: string[];
  luckyNumbers: number[];
}

/**
 * Element Balance - Five Elements Distribution
 */
export interface ElementBalance {
  wood: number;
  fire: number;
  earth: number;
  metal: number;
  water: number;
}

/**
 * Na Yin (纳音) - Sound Classification of the 60 Jiazi Pillars
 */
export interface NaYinInfo {
  chinese: string;
  english: string;
  element: 'Metal' | 'Wood' | 'Water' | 'Fire' | 'Earth';
}

/**
 * Void (空亡) Information
 */
export interface VoidInfo {
  chinese: string;    // e.g. "戌亥"
  english: string;    // e.g. "Dog & Pig"
}

/**
 * Void Status - Primary and Mutual Void indicators
 */
export interface VoidStatus {
  /** 空亡 — branch falls in the Day pillar's void pair. null for the Day pillar itself. */
  primaryVoid: boolean | null;
  /** 互换空亡 — count of active mutual voids (年日, 月日, 日时). 0–3. */
  mutualVoid: number;
}

/**
 * Life Stage Information (12长生 stages)
 */
export interface LifeStageInfo {
  chinese: string;
  english: string;
}

/**
 * Full Pillar - Pillar combined with Ten God Values
 */
export type FullPillar = {
  heavenlyStem: string;
  earthlyBranch: string;
  hiddenStems: string[];
  heavenlyStemTenGod: string;
  primaryQiTenGod: string | null;
  middleQiTenGod: string | null;
  residualQiTenGod: string | null;
};

/**
 * BaZi Profile - User's stored BaZi information
 */
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

/**
 * BaZi Chart - Complete BaZi calculation results
 */
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
    year: NaYinInfo | null;
    month: NaYinInfo | null;
    day: NaYinInfo | null;
    hour: NaYinInfo | null;
  };
  void: {
    year: VoidStatus;
    month: VoidStatus;
    day: VoidStatus;
    hour: VoidStatus;
  };
}
