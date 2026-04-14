/**
 * Twelve Life Stages (长生十二宫 / Chang Sheng 12 Stages)
 *
 * The lunar-javascript library computes the life stage for each pillar via
 * bazi.getYearDiShi(), getMonthDiShi(), getDayDiShi(), getTimeDiShi().
 * This module enriches those raw Chinese strings with English translations,
 * and provides a manual 自坐 calculation using each pillar's own stem.
 */

export interface LifeStageInfo {
  chinese: string;
  english: string;
}

const LIFE_STAGE_INFO: Record<string, string> = {
  '长生': 'Birth',
  '沐浴': 'Bathing',
  '冠带': 'Crowning',
  '临官': 'Official',
  '帝旺': 'Peak',
  '衰':   'Decline',
  '病':   'Illness',
  '死':   'Death',
  '墓':   'Tomb',
  '绝':   'Void',
  '胎':   'Embryo',
  '养':   'Nourishment',
};

/**
 * Enrich a raw Chinese life stage string (from lunar-javascript) with its
 * English translation.
 *
 * @param chinese  The Chinese stage name returned by bazi.getYearDiShi() etc.
 * @returns LifeStageInfo or null if the value is unrecognised.
 */
export function getLifeStageInfo(chinese: string): LifeStageInfo | null {
  const english = LIFE_STAGE_INFO[chinese];
  if (!english) return null;
  return { chinese, english };
}

// ─── 自坐 (Self-Seated) Life Stage Calculation ───────────────────────────────
//
// The library's _getDiShi() is hardcoded to the Day Master stem. For 自坐 we
// replicate the same algorithm using each pillar's own Heavenly Stem instead.
// LunarUtil is exported but its tables use i18n placeholder keys ({tg.jia} etc.)
// rather than Chinese characters, so we encode the offsets directly here.

// The 12 stages in index order (mirrors LunarUtil.CHANG_SHENG)
const CHANG_SHENG_ORDER = [
  '长生','沐浴','冠带','临官','帝旺','衰','病','死','墓','绝','胎','养',
] as const;

// Starting offset per Heavenly Stem (mirrors LunarUtil.CHANG_SHENG_OFFSET)
// Yang stems progress clockwise (+zhiIndex), Yin stems counter-clockwise (-zhiIndex)
// Earth stems (戊/己) share the same offset as Fire stems (丙/丁) — standard BaZi rule
const CHANG_SHENG_OFFSET: Record<string, number> = {
  '甲': 1, '丙': 10, '戊': 10, '庚': 7, '壬': 4,
  '乙': 6, '丁':  9, '己':  9, '辛': 0, '癸': 3,
};

// Earthly Branch to 0-based index (子=0 … 亥=11)
const ZHI_INDEX: Record<string, number> = {
  '子': 0, '丑': 1, '寅': 2, '卯': 3, '辰': 4, '巳': 5,
  '午': 6, '未': 7, '申': 8, '酉': 9, '戌': 10, '亥': 11,
};

const YANG_STEMS = new Set(['甲', '丙', '戊', '庚', '壬']);

/**
 * Compute the 自坐 (self-seated) life stage for a pillar.
 * Uses the pillar's own Heavenly Stem as the reference against its own Earthly Branch,
 * replicating the library's _getDiShi() algorithm with a custom stem.
 *
 * @param stem    Heavenly Stem of the pillar (e.g. "甲")
 * @param branch  Earthly Branch of the pillar (e.g. "子")
 * @returns LifeStageInfo or null if stem/branch are unrecognised.
 */
export function getPillarLifeStageInfo(stem: string, branch: string): LifeStageInfo | null {
  const offset = CHANG_SHENG_OFFSET[stem];
  const zhiIndex = ZHI_INDEX[branch];
  if (offset === undefined || zhiIndex === undefined) return null;
  const isYang = YANG_STEMS.has(stem);
  const rawIndex = offset + (isYang ? zhiIndex : -zhiIndex);
  const index = ((rawIndex % 12) + 12) % 12;
  return getLifeStageInfo(CHANG_SHENG_ORDER[index]);
}
