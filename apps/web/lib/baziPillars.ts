/**
 * BaZi Pillars Extraction Module
 *
 * Extracts the Four Pillars (Year, Month, Day, Hour) from a lunar calendar date.
 * Concerns itself only with heavenly stems, earthly branches, and hidden stems.
 * Ten Gods are a separate concern handled by tenGods.ts and assembled in the orchestrator.
 */

export interface Pillar {
  heavenlyStem: string;
  earthlyBranch: string;
  primaryQi: string | null;   // Primary Qi hidden stem
  middleQi: string | null;    // Middle Qi hidden stem
  residualQi: string | null;  // Residual Qi hidden stem
}

/**
 * Helper to safely extract 1-3 hidden stems from a variable-length array
 */
function parseHiddenStems(hideGan: string[]): [string | null, string | null, string | null] {
  return [
    hideGan[0] || null,
    hideGan[1] || null,
    hideGan[2] || null,
  ];
}

/**
 * Extract the Four Pillars from a bazi (EightChar) object
 */
export function extractPillars(bazi: any): {
  yearPillar: Pillar;
  monthPillar: Pillar;
  dayPillar: Pillar;
  hourPillar: Pillar;
} {

  const createPillar = (
    heavenlyStem: string,
    earthlyBranch: string,
    hideGan: string[],
  ): Pillar => {
    const [primaryQi, middleQi, residualQi] = parseHiddenStems(hideGan);
    return { heavenlyStem, earthlyBranch, primaryQi, middleQi, residualQi };
  };

  return {
    yearPillar:  createPillar(bazi.getYearGan(),  bazi.getYearZhi(),  bazi.getYearHideGan()),
    monthPillar: createPillar(bazi.getMonthGan(), bazi.getMonthZhi(), bazi.getMonthHideGan()),
    dayPillar:   createPillar(bazi.getDayGan(),   bazi.getDayZhi(),   bazi.getDayHideGan()),
    hourPillar:  createPillar(bazi.getTimeGan(),  bazi.getTimeZhi(),  bazi.getTimeHideGan()),
  };
}
