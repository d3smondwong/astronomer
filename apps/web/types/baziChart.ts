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
    本气十神: string;
    中气十神: string;
    余气十神: string;
  };
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
  天干: string;
  天干十神: string;
  地支: string;
  藏干: string[];
  藏干十神: {
    本气十神: string;
    中气十神: string;
    余气十神: string;
  };
  十二长生: string;
  空亡地支: string;
  primary_void_status?: string;
  reverse_void_status?: string;
  纳音: string;
  合化信息?: {
    类型: string;
    合化元素: string;
    参与柱位: string[];
    原天干十神: string;
  };
  化气格信息?: {
    原五行: string;
    现五行: string;
  };
  化气格变化?: {
    原天干十神: string;
    原藏干十神: {
      本气十神: string;
      中气十神: string;
      余气十神: string;
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
