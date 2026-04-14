/**
 * Element Balance Calculation Module
 *
 * Calculates the five element distribution (Wood, Fire, Earth, Metal, Water)
 * from the four pillars and determines lucky/deficient elements.
 */

import { Pillar } from './baziPillars';

export interface ElementBalance {
  wood: number;
  fire: number;
  earth: number;
  metal: number;
  water: number;
}

/**
 * Map element names to lowercase keys for the ElementBalance object
 */
const elementKeyMap: Record<string, keyof ElementBalance> = {
  'Wood': 'wood',
  'Fire': 'fire',
  'Earth': 'earth',
  'Metal': 'metal',
  'Water': 'water',
};

/**
 * Extract element from a stem (e.g., '甲' -> 'Wood')
 * and branch (e.g., '寅' -> 'Wood')
 */
function getStemElement(stem: string): string {
  // Extract just the character if stem includes romanization (e.g., "甲 (Jia)" -> "甲")
  const stemChar = stem.split(' ')[0];

  const stemElementMap: Record<string, string> = {
    '甲': 'Wood', '乙': 'Wood',
    '丙': 'Fire', '丁': 'Fire',
    '戊': 'Earth', '己': 'Earth',
    '庚': 'Metal', '辛': 'Metal',
    '壬': 'Water', '癸': 'Water',
  };
  return stemElementMap[stemChar] || 'Unknown';
}

function getBranchElement(branch: string): string {
  // Extract just the character if branch includes romanization (e.g., "寅 (Yin)" -> "寅")
  const branchChar = branch.split(' ')[0];

  const branchElementMap: Record<string, string> = {
    '子': 'Water', '丑': 'Earth', '寅': 'Wood', '卯': 'Wood',
    '辰': 'Earth', '巳': 'Fire', '午': 'Fire', '未': 'Earth',
    '申': 'Metal', '酉': 'Metal', '戌': 'Earth', '亥': 'Water',
  };
  return branchElementMap[branchChar] || 'Unknown';
}

/**
 * Calculate element balance from the four pillars
 *
 * Each pillar has a heavenly stem and earthly branch
 * Both contribute to the element count
 */
export function calculateElementBalance(
  yearPillar: Pillar,
  monthPillar: Pillar,
  dayPillar: Pillar,
  hourPillar: Pillar
): ElementBalance {
  const balance: ElementBalance = {
    wood: 0,
    fire: 0,
    earth: 0,
    metal: 0,
    water: 0,
  };

  // Array of all pillars and their components
  const pillars = [yearPillar, monthPillar, dayPillar, hourPillar];

  pillars.forEach((pillar) => {
    // Count stem element
    const stemElement = getStemElement(pillar.heavenlyStem);
    const stemKey = elementKeyMap[stemElement];
    if (stemKey) balance[stemKey]++;

    // Count branch element
    const branchElement = getBranchElement(pillar.earthlyBranch);
    const branchKey = elementKeyMap[branchElement];
    if (branchKey) balance[branchKey]++;
  });

  return balance;
}

/**
 * Determine lucky elements (the two weakest elements)
 * These are elements that need strengthening for balance
 */
export function determineLuckyElements(elements: ElementBalance): string[] {
  const elementArray = Object.entries(elements).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }));

  // Sort by value (lowest first)
  elementArray.sort((a, b) => a.value - b.value);

  // Return the two weakest elements as lucky elements
  return elementArray.slice(0, 2).map((e) => e.name);
}

/**
 * Determine which elements are strong/weak in the chart
 */
export function analyzeElementStrength(elements: ElementBalance): Record<string, 'Strong' | 'Weak'> {
  const average = (elements.wood + elements.fire + elements.earth + elements.metal + elements.water) / 5;

  return {
    Wood: elements.wood >= average ? 'Strong' : 'Weak',
    Fire: elements.fire >= average ? 'Strong' : 'Weak',
    Earth: elements.earth >= average ? 'Strong' : 'Weak',
    Metal: elements.metal >= average ? 'Strong' : 'Weak',
    Water: elements.water >= average ? 'Strong' : 'Weak',
  };
}
