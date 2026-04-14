/**
 * Ten Gods Module (十神 ShiShen)
 *
 * Handles parsing and management of the ten gods, which represent
 * the relationships between heavenly stems in BaZi analysis.
 */

/**
 * Interface for ten god values associated with a pillar
 */
export interface TenGodValues {
  heavenlyStemTenGod: string;       // e.g. '比肩', '日主' for Day Master
  primaryQiTenGod: string | null;   // Ten god for Primary Qi hidden stem
  middleQiTenGod: string | null;    // Ten god for Middle Qi hidden stem
  residualQiTenGod: string | null;  // Ten god for Residual Qi hidden stem
}

/**
 * Helper to safely extract 1-3 ten gods for hidden stems from a variable-length array
 */
export function parseHiddenStemTenGods(
  shiShenArray: string[]
): [string | null, string | null, string | null] {
  return [
    shiShenArray[0] || null,
    shiShenArray[1] || null,
    shiShenArray[2] || null,
  ];
}

/**
 * Create ten god values for a pillar
 */
export function createTenGodValues(
  shiShenGan: string,
  shiShenZhi: string[]
): TenGodValues {
  const [primaryQiTenGod, middleQiTenGod, residualQiTenGod] = parseHiddenStemTenGods(shiShenZhi);

  return {
    heavenlyStemTenGod: shiShenGan,
    primaryQiTenGod,
    middleQiTenGod,
    residualQiTenGod,
  };
}
