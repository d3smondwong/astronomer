/**
 * Personality Generation Module
 *
 * Generates basic personality traits based on the day master's heavenly stem element.
 * The day master (day pillar's heavenly stem) is the strongest indicator of personality type.
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
 * Get element from heavenly stem
 */
function getStemElement(stem: string): string {
  // Extract just the character if stem includes romanization (e.g., "甲 (Jia)" -> "甲")
  const stemChar = stem.split(' ')[0];

  const stemElementMap: Record<string, string> = {
    '甲': 'Wood',
    '乙': 'Wood',
    '丙': 'Fire',
    '丁': 'Fire',
    '戊': 'Earth',
    '己': 'Earth',
    '庚': 'Metal',
    '辛': 'Metal',
    '壬': 'Water',
    '癸': 'Water',
  };
  return stemElementMap[stemChar] || 'Unknown';
}

/**
 * Generate personality traits based on day master element
 */
export function generatePersonalityTraits(dayMasterStem: string): PersonalityTraits {
  const element = getStemElement(dayMasterStem);

  const personalityMap: Record<string, Omit<PersonalityTraits, 'dayMasterStem'>> = {
    Wood: {
      element: 'Wood',
      archetype: 'The Pioneer',
      traits: ['Creative', 'Ambitious', 'Adaptable', 'Growth-oriented'],
      strengths: ['Innovation', 'Leadership', 'Resilience', 'Initiative'],
      challenges: ['Impatience', 'Stubbornness', 'Over-ambition'],
      luckyColors: ['Green', 'Blue'],
      luckyNumbers: [3, 8],
    },
    Fire: {
      element: 'Fire',
      archetype: 'The Illuminator',
      traits: ['Passionate', 'Expressive', 'Enthusiastic', 'Charismatic'],
      strengths: ['Inspiration', 'Confidence', 'Vitality', 'Intuition'],
      challenges: ['Impulsiveness', 'Volatility', 'Scattered energy'],
      luckyColors: ['Red', 'Purple'],
      luckyNumbers: [2, 7],
    },
    Earth: {
      element: 'Earth',
      archetype: 'The Stabilizer',
      traits: ['Reliable', 'Grounded', 'Practical', 'Nurturing'],
      strengths: ['Dependability', 'Loyalty', 'Stability', 'Compassion'],
      challenges: ['Rigidity', 'Overthinking', 'Resistance to change'],
      luckyColors: ['Yellow', 'Brown'],
      luckyNumbers: [5, 10],
    },
    Metal: {
      element: 'Metal',
      archetype: 'The Precision Master',
      traits: ['Disciplined', 'Precise', 'Sharp-minded', 'Principled'],
      strengths: ['Focus', 'Determination', 'Clarity', 'Justice'],
      challenges: ['Rigidity', 'Melancholy', 'Over-criticism'],
      luckyColors: ['White', 'Silver'],
      luckyNumbers: [4, 9],
    },
    Water: {
      element: 'Water',
      archetype: 'The Reflective Sage',
      traits: ['Intuitive', 'Adaptive', 'Thoughtful', 'Philosophical'],
      strengths: ['Wisdom', 'Flexibility', 'Perception', 'Communication'],
      challenges: ['Indecision', 'Passivity', 'Emotional depth'],
      luckyColors: ['Black', 'Blue'],
      luckyNumbers: [1, 6],
    },
  };

  const personalityData = personalityMap[element] || personalityMap['Water'];

  return {
    dayMasterStem,
    ...personalityData,
  };
}

/**
 * Generate a brief personality summary
 */
export function generatePersonalitySummary(traits: PersonalityTraits): string {
  return `As a ${traits.archetype} (${traits.element}), you are ${traits.traits.join(', ').toLowerCase()}.
Your natural strengths include ${traits.strengths.join(', ').toLowerCase()}.
To achieve balance, be mindful of tendencies toward ${traits.challenges.join(', ').toLowerCase()}.
Lucky colors: ${traits.luckyColors.join(', ')}. Lucky numbers: ${traits.luckyNumbers.join(', ')}.`;
}
