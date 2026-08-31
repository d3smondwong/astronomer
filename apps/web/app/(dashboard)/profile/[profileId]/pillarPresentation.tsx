/**
 * pillarPresentation — presentation constants and chips shared by the collapsed
 * PillarCard (天干 + 地支 only) and the expanded PillarDetailPanel (藏干, 旬空,
 * 十二长生, 纳音, 神煞).
 *
 * These are component-scoped display tables — Chinese→English glosses, semantic
 * tones per rooting depth / void category, and the repeated Tailwind class
 * strings. Brand colours still come from styles/theme.css tokens; the literals
 * here are semantic accents (green = deep root, red = void) that are not part of
 * the brand palette.
 */
import { ELEMENT_ICONS, ELEMENT_COLOR } from '@/lib/elements';

export type PillarKey = '年柱' | '月柱' | '日柱' | '时柱';

export const PILLAR_ORDER: PillarKey[] = ['年柱', '月柱', '日柱', '时柱'];

export const STEM_ELEMENT: Record<string, string> = {
  甲: '木', 乙: '木', 丙: '火', 丁: '火',
  戊: '土', 己: '土', 庚: '金', 辛: '金',
  壬: '水', 癸: '水',
};

export const BRANCH_ELEMENT: Record<string, string> = {
  子: '水', 丑: '土', 寅: '木', 卯: '木',
  辰: '土', 巳: '火', 午: '火', 未: '土',
  申: '金', 酉: '金', 戌: '土', 亥: '水',
};

// English labels for Heavenly Stems and Earthly Branches (used in English mode only)
export const GAN_LABELS: Record<string, string> = {
  甲: 'Yang Wood', 乙: 'Yin Wood', 丙: 'Yang Fire', 丁: 'Yin Fire',
  戊: 'Yang Earth', 己: 'Yin Earth', 庚: 'Yang Metal', 辛: 'Yin Metal',
  壬: 'Yang Water', 癸: 'Yin Water',
};

// Chinese polarity + element labels for Heavenly Stems
export const GAN_LABELS_CH: Record<string, string> = {
  甲: '阳木', 乙: '阴木', 丙: '阳火', 丁: '阴火',
  戊: '阳土', 己: '阴土', 庚: '阳金', 辛: '阴金',
  壬: '阳水', 癸: '阴水',
};

export const ZHI_LABELS: Record<string, string> = {
  子: 'Water Rat', 丑: 'Earth Ox', 寅: 'Wood Tiger', 卯: 'Wood Rabbit',
  辰: 'Earth Dragon', 巳: 'Fire Snake', 午: 'Fire Horse', 未: 'Earth Goat',
  申: 'Metal Monkey', 酉: 'Metal Rooster', 戌: 'Earth Dog', 亥: 'Water Pig',
};

// Chinese element + zodiac labels for Earthly Branches
export const ZHI_LABELS_CH: Record<string, string> = {
  子: '水鼠', 丑: '土牛', 寅: '木虎', 卯: '木兔',
  辰: '土龙', 巳: '火蛇', 午: '火马', 未: '土羊',
  申: '金猴', 酉: '金鸡', 戌: '土狗', 亥: '水猪',
};

export const SHI_SHEN_LABELS: Record<string, string> = {
  '比肩': 'Companion', '劫财': 'Wealth Robber', '食神': 'Food God',
  '伤官': 'Hurting Officer', '偏财': 'Indirect Wealth', '正财': 'Direct Wealth',
  '七杀': 'Seven Killings', '偏官': 'Indirect Officer', '正官': 'Direct Officer', '偏印': 'Indirect Resource',
  '正印': 'Direct Resource', '我': 'Self',
};

export const SHEN_SHA_LABELS: Record<string, string> = {
  // Year branch stars
  '龙德': 'Dragon Virtue', '红鸾': 'Red Luan', '天喜': 'Heavenly Joy',
  '桃花': 'Peach Blossom', '墙内桃花': 'Inner Peach Blossom', '墙外桃花': 'Outer Peach Blossom',
  '孤辰': 'Lonely Star', '寡宿': "Widow Star",
  '病符': 'Illness Star', '吊客': 'Mourning Guest', '天空': 'Sky Void',
  '丧门': 'Messenger of Death', '白虎': 'White Tiger', '卷舌': 'Curled Tongue',
  '披麻': 'Mourning Attire', '披头': 'Disheveled Head',
  '吟呻': 'Groaning Malefic', '破碎': 'Shattering Malefic', '白衣': 'White Garment Malefic',
  '元辰': 'Star of Separation and Discord', '六厄': 'Six Adversities',
  '飞廉': 'Flying Scythe',
  // Month branch stars
  '天德贵人': 'Heavenly Virtue Noble', '月德贵人': 'Monthly Virtue Noble', '天医': 'Heavenly Doctor',
  '月空': 'Monthly Void', '血刃': 'Blood Blade', '天赦': 'Heavenly Pardon',
  '月厌': 'Monthly Abomination', '月煞': 'Monthly Malefic',
  '天转': 'Heavenly Turn', '地转': 'Earthly Turn', '季节性退神': 'Seasonal Retreating Spirit',
  '天德合': 'Heavenly Virtue Combination', '月德合': 'Monthly Virtue Combination',
  '天月德合': 'Heavenly & Monthly Virtue Combination',
  // Day/year branch stars
  '将星': 'Commanding Star', '华盖': 'Canopy Star', '驿马': 'Travel Horse',
  '劫煞': 'Robbery Sha', '亡神': 'Perishing God', '灾煞': 'Calamity Sha',
  '沐浴桃花': 'Peach Blossom Bath',
  // Day/year stem stars
  '昼天乙贵人': 'Day Heavenly Noble', '夜天乙贵人': 'Night Heavenly Noble',
  '文昌贵人': 'Literary Star Noble', '学堂': 'Academy Star', '太极贵人': 'Tai Ji Noble',
  '禄神': 'Prosperity Star', '金舆': 'Golden Carriage', '国印': 'National Seal',
  '文昌贵': 'Literary Star Honour', '文誉贵': 'Literary Prestige Noble',
  '文星贵': 'Literary Luminary', '天印贵': 'Heavenly Seal Noble',
  '福星': 'Fortune Star', '真词馆': 'True Literary Academy', '正词馆': 'Standard Literary Academy',
  '红艳': 'Red Charm', '天厨贵人': 'Heavenly Kitchen Noble', '飞刃': 'Flying Blade',
  '天官贵人': 'Heavenly Officer Noble', '羊刃': 'Sheep Blade', '流霞': 'Blood Disaster Star',
  '勾煞': 'Hook Disaster', '绞煞': 'Twist Disaster',
  // Derived & special
  '天上三奇': "Heaven's Three Wonders", '地下三奇': "Earth's Three Wonders",
  '人间三奇': "Human's Three Wonders",
  '寅命自禄': 'Yin Self-Lu', '卯命自禄': 'Mao Self-Lu',
  '申命自禄': 'Shen Self-Lu', '酉命自禄': 'You Self-Lu',
  // Pillar formations
  '阴阳差错': 'Yin-Yang Discord', '十恶大败': 'Ten Great Failures',
  '魁罡': 'Chief Star',
  '进神': 'Advancing Spirit', '六秀': 'Six Elegance', '八专': 'Eight Specialty',
  '九丑': 'Nine Ugly', '孤鸾': 'Lone Phoenix', '退气神煞': 'Retreating Qi Sha',
  '四废': 'Four Wastes', '金神': 'Golden Deity', '十灵': 'Ten Spirits',
  '天罗': 'Heavenly Net', '地网': 'Earthly Net', '童子煞': 'Child Star',
  '隔角煞': 'Separated Corner Star',
  '自缢煞': 'Self-Strangulation Star', '破煞': 'Breakage Star',
  '挂剑煞': 'Hanging Sword Star', '天火煞': 'Celestial Fire Star',
  '天屠煞': 'Heavenly Slaughter Star', '剑锋煞': 'Sword Blade Star',
  // Relational stars (can appear on pillars)
  '德秀贵人': 'Virtue & Elegance Noble', '暗禄': 'Hidden Lu',
};

export type RootingTrKey = 'rootingDeep' | 'rootingModerate' | 'rootingLight' | 'rootingNone';

// Semantic tone per rooting depth — component-scoped data, not brand theme.
export const ROOTING_STYLES: Record<string, { trKey: RootingTrKey; color: string; bg: string }> = {
  '深根': { trKey: 'rootingDeep',     color: '#2d6a2d', bg: 'rgba(45, 106, 45, 0.08)'  },
  '中根': { trKey: 'rootingModerate', color: '#3d5a80', bg: 'rgba(61, 90, 128, 0.08)'  },
  '浅根': { trKey: 'rootingLight',    color: '#8a5200', bg: 'rgba(138, 82, 0, 0.08)'   },
  '无根': { trKey: 'rootingNone',     color: '#7a4040', bg: 'rgba(122, 64, 64, 0.08)'  },
};

// Semantic tone per void category — component-scoped data.
export const VOID_CATEGORY_COLORS: Record<string, { color: string; bg: string }> = {
  primary: { color: '#8C2F2F', bg: 'rgba(140, 47, 47, 0.08)' },
  oneway:  { color: '#b77306', bg: 'rgba(122, 79, 0, 0.08)'  },
  mutual:  { color: '#4A2080', bg: 'rgba(74, 32, 128, 0.08)' },
};

/* Shared class strings for the repeating patterns across card + panel */
export const SECTION_LABEL_CLS = 'block text-sm font-semibold text-gold-deep/45 uppercase tracking-[0.12em] mb-2';
/** Left label gutter in the detail panel's rows — same tone, left-aligned, no bottom margin. */
export const GUTTER_LABEL_CLS = 'text-[11px] font-semibold text-gold-deep/45 uppercase tracking-[0.12em] leading-snug text-left';
export const SUB_LABEL_CLS = 'text-xs font-semibold text-gold-deep/35 uppercase tracking-[0.1em]';
export const GLYPH_LG_CLS = 'font-zh text-5xl font-semibold text-bronze-muted leading-none';
export const GLYPH_MD_CLS = 'font-zh text-4xl font-semibold text-bronze-muted leading-none';
export const CAPTION_CLS = 'text-[13px] text-bronze-muted opacity-75 m-0 italic';

export function PillarDivider() {
  return <div className="w-4/5 h-px bg-gold-deep/12 my-4" />;
}

/** Ten-god chip under a heavenly stem (offset arrow pair when 化气格 relabelled it). */
export function TenGodCard({ value, language, dimmed }: { value: string; language: 'en' | 'ch'; dimmed?: boolean }) {
  const char = value === '日主' ? '我' : value;
  const label = value === '日主' ? 'Self' : (SHI_SHEN_LABELS[value] ?? value);
  return (
    <div className={`inline-flex flex-col items-center border border-gold-deep/25 rounded-lg px-2.5 py-1 bg-gold-deep/6 ${dimmed ? 'opacity-55' : ''}`}>
      <span className="font-zh text-[13px] text-gold-deep/75">{char}</span>
      {language === 'en' && (
        <span className="text-[10px] text-gold-deep/60 mt-0.5">{label}</span>
      )}
    </div>
  );
}

/** Smaller ten-god chip for hidden stems. */
export function HiddenTenGodCard({ value, language, dimmed }: { value: string; language: 'en' | 'ch'; dimmed?: boolean }) {
  return (
    <div className={`inline-flex flex-col items-center border border-gold-deep/20 rounded-md px-2 py-[3px] bg-gold-deep/5 ${dimmed ? 'opacity-55' : ''}`}>
      <span className="font-zh text-[13px] text-gold-deep/70 mb-1">{value}</span>
      {language === 'en' && (
        <span className="text-[9px] text-gold-deep/55 mt-px">{SHI_SHEN_LABELS[value] ?? value}</span>
      )}
    </div>
  );
}

/**
 * Element icon + label caption, e.g. "◇ Yin Metal" / "◇ 阴金".
 * `size` tunes the icon and text for the large (stem/branch) vs small (hidden stem) cases.
 */
export function ElementCaption({ element, label, size = 'md' }: { element?: string; label: string; size?: 'sm' | 'md' }) {
  const Icon = element ? ELEMENT_ICONS[element] : null;
  const color = element ? ELEMENT_COLOR[element] : undefined;
  const iconSize = size === 'sm' ? 11 : 13;
  return (
    <div className={`flex items-center gap-1 ${size === 'sm' ? '' : ''}`}>
      {Icon && <Icon style={{ fontSize: iconSize, color }} />}
      <p className={size === 'sm'
        ? 'text-[11px] text-bronze-muted/60 m-0 leading-tight'
        : CAPTION_CLS}>
        {label}
      </p>
    </div>
  );
}
