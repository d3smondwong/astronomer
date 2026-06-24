/**
 * TypeScript interfaces for BaZi chart data.
 *
 * Mirrors the Python schema returned by FastAPI. All calculation output is
 * under the 'data' key with Chinese-keyed structures.
 */

/**
 * Ten Gods for a pillar stem.
 */
export interface TenGods {
  天干十神: string;
  藏干十神: {
    本气: string;
    中气: string;
    余气: string;
  };
}

/**
 * Heavenly stem with all derived attributes.
 */
export interface HeavenlyStem {
  天干: string;
  阴阳: string;
  五行: string;
  根基强度: string;
  通根于: string;
  十神: string;
}

/**
 * Earthly branch with all derived attributes.
 */
export interface EarthlyBranch {
  地支: string;
  阴阳: string;
  五行: string;
}

/**
 * A single hidden stem tier within a pillar.
 */
export interface HiddenStemTier {
  天干: string;
  阴阳: string;
  五行: string;
  十神: string;
}

/**
 * Life stage (12长生 stages).
 */
export interface LifeStage {
  xingYun: string; // e.g., "沐浴" (Bath)
  shiGan: string;  // strong/weak indicator
}

/**
 * Void status for a pillar.
 */
export interface VoidStatus {
  void_xun_kong: string;
  primary_void_status: string;
  reverse_void_status: string;
}

/**
 * A single pillar (year, month, day, hour).
 */
export interface Pillar {
  天干: HeavenlyStem;
  地支: EarthlyBranch;
  藏干: {
    本气: HiddenStemTier;
    中气?: HiddenStemTier;
    余气?: HiddenStemTier;
  };
  十二长生: string;
  空亡: {
    本柱旬空: string;
    被日柱空: string;
    被年柱空?: string;
    被月柱空?: string;
    被时柱空?: string;
    年日互换空亡?: string;
    月日互换空亡?: string;
    日时互换空亡?: string;
  };
  纳音: string;
  化气格信息?: {
    类型: string;
    原五行: string;
    现五行: string;
  };
  化气格变化?: {
    原天干十神: string;
    原藏干十神: {
      本气: string;
      中气?: string;
      余气?: string;
    };
  };
}

/**
 * Four pillars (四柱实体).
 */
export interface FourPillars {
  年柱: Pillar;
  月柱: Pillar;
  日柱: Pillar;
  时柱: Pillar;
}

/**
 * Three palaces (胎元, 命宫, 身宫).
 */
export interface ThreePalaces {
  胎元: {
    天干: string;
    地支: string;
  };
  命宫: {
    天干: string;
    地支: string;
  };
  身宫: {
    天干: string;
    地支: string;
  };
}

/**
 * Five elements (五行) qualitative classical state per element.
 * 状态 is one of 旺 / 相 / 休 / 囚 / 死.
 */
export type ElementState = '旺' | '相' | '休' | '囚' | '死';

export interface ElementVerdict {
  状态: ElementState;
}

export type FiveElements = Record<'木' | '火' | '土' | '金' | '水', ElementVerdict>;

/**
 * Chart data payload — all Chinese-keyed calculation output.
 */
export interface BaziChartData {
  四柱实体: FourPillars;
  胎元?: {
    天干: string;
    地支: string;
  };
  命宫?: {
    天干: string;
    地支: string;
  };
  身宫?: {
    天干: string;
    地支: string;
  };
  五行?: FiveElements;
  [key: string]: any; // Allow other keys for future expansion
}

export interface VaultState {
  库柱: string;
  库支: string;
  标签: string;
  元素: string;
  释放: string;
  释放十神: string;
  是否开库: boolean;
  开库机制: string[];
  透干: { 是否透干: boolean; 透干柱位: string | null };
  季节状态: string;
  开库条件?: { 冲开: string; 刑开: string[]; 透干: string };
  备注: string;
}

/**
 * Full chart response from FastAPI.
 */
export interface BaziChartResponse {
  lunar_date: string;
  gender: string;
  zodiac: string;
  data: BaziChartData;
  is_full?: boolean;
}
