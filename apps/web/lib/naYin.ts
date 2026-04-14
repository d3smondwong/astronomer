/**
 * NaYin (纳音 / Na Yin) — Sound Classification of the 60 Jiazi Pillars
 *
 * Each of the 60 Heavenly Stem + Earthly Branch combinations maps to one of
 * 30 Nayin phrases. The lunar-javascript library returns the raw Chinese string
 * via bazi.getYearNaYin(), getMonthNaYin(), getDayNaYin(), getTimeNaYin().
 * This module enriches those strings with English translations and the
 * associated Five Element.
 */

export interface NaYinInfo {
  chinese: string;
  english: string;
  element: 'Metal' | 'Wood' | 'Water' | 'Fire' | 'Earth';
}

// Maps the last character of a Nayin string to its Five Element
const ELEMENT_CHAR: Record<string, NaYinInfo['element']> = {
  '金': 'Metal',
  '木': 'Wood',
  '水': 'Water',
  '火': 'Fire',
  '土': 'Earth',
};

// All 30 unique Nayin phrases with English translations
const NAYIN_ENGLISH: Record<string, string> = {
  '海中金': 'Gold in the Sea',
  '炉中火': 'Fire in the Furnace',
  '大林木': 'Great Forest Wood',
  '路旁土': 'Roadside Earth',
  '剑锋金': 'Sword Edge Gold',
  '山头火': 'Mountain Fire',
  '涧下水': 'Water in the Stream',
  '城头土': 'City Wall Earth',
  '白蜡金': 'White Wax Gold',
  '杨柳木': 'Willow Wood',
  '泉中水': 'Water from the Spring',
  '屋上土': 'Earth on the House',
  '霹雳火': 'Thunderbolt Fire',
  '松柏木': 'Pine and Cypress Wood',
  '长流水': 'Long Flowing Water',
  '沙中金': 'Gold in the Sand',
  '山下火': 'Fire Under the Mountain',
  '平地木': 'Flat Land Wood',
  '壁上土': 'Earth on the Wall',
  '金箔金': 'Gold Foil',
  '覆灯火': 'Lamp Cover Fire',
  '天河水': 'Heavenly River Water',
  '大驿土': 'Great Post Earth',
  '钗钏金': 'Gold Hairpin',
  '桑柘木': 'Mulberry Wood',
  '大溪水': 'Water of the Great Stream',
  '沙中土': 'Earth in the Sand',
  '天上火': 'Fire in the Sky',
  '石榴木': 'Pomegranate Wood',
  '大海水': 'Great Ocean Water',
};

/**
 * Enrich a raw Chinese Nayin string (from lunar-javascript) with its
 * English translation and Five Element.
 *
 * @param chinese  The Nayin string returned by bazi.getYearNaYin() etc. (e.g. '海中金')
 * @returns NaYinInfo or null if the value is unrecognised.
 */
export function getNaYinInfo(chinese: string): NaYinInfo | null {
  const english = NAYIN_ENGLISH[chinese];
  if (!english) return null;

  const lastChar = chinese.slice(-1);
  const element = ELEMENT_CHAR[lastChar];
  if (!element) return null;

  return { chinese, english, element };
}
