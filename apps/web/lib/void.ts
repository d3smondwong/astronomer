/**
 * Xun Kong / Void (空亡) Module
 *
 * Each of the 60 Jiazi pillars belongs to one of six 旬 (Xun) cycles.
 * Each cycle leaves two Earthly Branches unused — those are the 空亡 (void) branches.
 * A pillar whose branch falls on its void pair has suspended or weakened luck.
 *
 * The lunar-javascript library computes the void branches per pillar via:
 *   bazi.getYearXunKong()  — uses exact Li Chun moment
 *   bazi.getMonthXunKong() — uses exact solar term moment
 *   bazi.getDayXunKong()   — uses exact day boundary (late-Zi = next day)
 *   bazi.getTimeXunKong()  — standard hour method
 *
 * All return a two-character string of the void branch pair (e.g. "戌亥").
 * This module enriches those strings with English branch names.
 */

export interface VoidInfo {
  chinese: string;    // e.g. "戌亥"
  english: string;    // e.g. "Dog & Pig"
}

// All 6 possible void branch pairs across the 6 Xun cycles
const VOID_ENGLISH: Record<string, string> = {
  '戌亥': 'Dog & Pig',
  '申酉': 'Monkey & Rooster',
  '午未': 'Horse & Goat',
  '辰巳': 'Dragon & Snake',
  '寅卯': 'Tiger & Rabbit',
  '子丑': 'Rat & Ox',
};

/**
 * Enrich a raw void-branch string (from lunar-javascript) with its English name.
 *
 * @param chinese  The two-character void pair returned by bazi.getYearXunKong() etc. (e.g. '戌亥')
 * @returns VoidInfo or null if the value is unrecognised.
 */
export function getVoidInfo(chinese: string): VoidInfo | null {
  const english = VOID_ENGLISH[chinese];
  if (!english) return null;
  return { chinese, english };
}
