'use client';

/**
 * PillarCard — one of the four pillar columns on the profile page
 * (heavenly stem, earthly branch, hidden stems, voids, life stages,
 * na yin, shen sha). Extracted from ProfilePageClient.tsx.
 */
import { ELEMENT_ICONS, ELEMENT_EN, ELEMENT_COLOR } from '@/lib/elements';
import { type LifeStageInfo, type NaYinInfo, type VoidInfo, type VoidStatus } from '@/types/baziLibraryTypes';
import { translations } from '@/lib/translations';

const STEM_ELEMENT: Record<string, string> = {
  甲: '木', 乙: '木', 丙: '火', 丁: '火',
  戊: '土', 己: '土', 庚: '金', 辛: '金',
  壬: '水', 癸: '水',
};

const BRANCH_ELEMENT: Record<string, string> = {
  子: '水', 丑: '土', 寅: '木', 卯: '木',
  辰: '土', 巳: '火', 午: '火', 未: '土',
  申: '金', 酉: '金', 戌: '土', 亥: '水',
};

// English labels for Heavenly Stems and Earthly Branches (used in English mode only)
const GAN_LABELS: Record<string, string> = {
  甲: 'Yang Wood', 乙: 'Yin Wood', 丙: 'Yang Fire', 丁: 'Yin Fire',
  戊: 'Yang Earth', 己: 'Yin Earth', 庚: 'Yang Metal', 辛: 'Yin Metal',
  壬: 'Yang Water', 癸: 'Yin Water',
};

// Chinese polarity + element labels for Heavenly Stems
const GAN_LABELS_CH: Record<string, string> = {
  甲: '阳木', 乙: '阴木', 丙: '阳火', 丁: '阴火',
  戊: '阳土', 己: '阴土', 庚: '阳金', 辛: '阴金',
  壬: '阳水', 癸: '阴水',
};

const ZHI_LABELS: Record<string, string> = {
  子: 'Water Rat', 丑: 'Earth Ox', 寅: 'Wood Tiger', 卯: 'Wood Rabbit',
  辰: 'Earth Dragon', 巳: 'Fire Snake', 午: 'Fire Horse', 未: 'Earth Goat',
  申: 'Metal Monkey', 酉: 'Metal Rooster', 戌: 'Earth Dog', 亥: 'Water Pig',
};

// Chinese element + zodiac labels for Earthly Branches
const ZHI_LABELS_CH: Record<string, string> = {
  子: '水鼠', 丑: '土牛', 寅: '木虎', 卯: '木兔',
  辰: '土龙', 巳: '火蛇', 午: '火马', 未: '土羊',
  申: '金猴', 酉: '金鸡', 戌: '土狗', 亥: '水猪',
};

const SHI_SHEN_LABELS: Record<string, string> = {
  '比肩': 'Companion', '劫财': 'Wealth Robber', '食神': 'Food God',
  '伤官': 'Hurting Officer', '偏财': 'Indirect Wealth', '正财': 'Direct Wealth',
  '七杀': 'Seven Killings', '偏官': 'Indirect Officer', '正官': 'Direct Officer', '偏印': 'Indirect Resource',
  '正印': 'Direct Resource', '我': 'Self',
};

const SHEN_SHA_LABELS: Record<string, string> = {
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

// Semantic tone per rooting depth — component-scoped data, not brand theme.
const ROOTING_STYLES: Record<string, { trKey: RootingTrKey; color: string; bg: string }> = {
  '深根': { trKey: 'rootingDeep',     color: '#2d6a2d', bg: 'rgba(45, 106, 45, 0.08)'  },
  '中根': { trKey: 'rootingModerate', color: '#3d5a80', bg: 'rgba(61, 90, 128, 0.08)'  },
  '浅根': { trKey: 'rootingLight',    color: '#8a5200', bg: 'rgba(138, 82, 0, 0.08)'   },
  '无根': { trKey: 'rootingNone',     color: '#7a4040', bg: 'rgba(122, 64, 64, 0.08)'  },
};
type RootingTrKey = 'rootingDeep' | 'rootingModerate' | 'rootingLight' | 'rootingNone';

// Semantic tone per void category — component-scoped data.
const VOID_CATEGORY_COLORS: Record<string, { color: string; bg: string }> = {
  primary: { color: '#8C2F2F', bg: 'rgba(140, 47, 47, 0.08)' },
  oneway:  { color: '#b77306', bg: 'rgba(122, 79, 0, 0.08)'  },
  mutual:  { color: '#4A2080', bg: 'rgba(74, 32, 128, 0.08)' },
};

/* Shared class strings for the repeating patterns in this card */
const SECTION_LABEL_CLS = 'block text-sm font-semibold text-gold-deep/45 uppercase tracking-[0.12em] mb-2';
const SUB_LABEL_CLS = 'text-xs font-semibold text-gold-deep/35 uppercase tracking-[0.1em]';
const GLYPH_LG_CLS = 'font-zh text-5xl font-semibold text-bronze-muted leading-none';
const GLYPH_MD_CLS = 'font-zh text-4xl font-semibold text-bronze-muted leading-none';
const CAPTION_CLS = 'text-[13px] text-bronze-muted opacity-75 m-0 italic';

function PillarDivider() {
  return <div className="w-4/5 h-px bg-gold-deep/12 my-4" />;
}

// Ten-god chip under the heavenly stem (offset arrow pair when 化气格 relabelled it).
function TenGodCard({ value, language, dimmed }: { value: string; language: 'en' | 'ch'; dimmed?: boolean }) {
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

// Smaller ten-god chip for hidden stems.
function HiddenTenGodCard({ value, language, dimmed }: { value: string; language: 'en' | 'ch'; dimmed?: boolean }) {
  return (
    <div className={`inline-flex flex-col items-center border border-gold-deep/20 rounded-md px-2 py-[3px] bg-gold-deep/5 ${dimmed ? 'opacity-55' : ''}`}>
      <span className="font-zh text-[13px] text-gold-deep/70 mb-1">{value}</span>
      {language === 'en' && (
        <span className="text-[9px] text-gold-deep/55 mt-px">{SHI_SHEN_LABELS[value] ?? value}</span>
      )}
    </div>
  );
}

export default function PillarCard({
  pillarLabel,
  pillar,
  isDayMaster = false,
  lifeStages,
  naYin,
  xunKong,
  voidStatus,
  maxVoidCount,
  shenSha,
  tianGanHua,
  language,
  anyHeavenlyStemBadge,
}: {
  pillarLabel: string;
  pillar: any;
  isDayMaster?: boolean;
  lifeStages?: { xingYun: LifeStageInfo | null; ziZuo: LifeStageInfo | null } | null;
  naYin?: NaYinInfo | null;
  xunKong?: VoidInfo | null;
  voidStatus: VoidStatus;
  maxVoidCount: number;
  shenSha?: { 名称: string; 来源: string; 解读?: string }[];
  tianGanHua?: { 元素: string; 原五行: string; label: string };
  language: 'en' | 'ch';
  anyHeavenlyStemBadge: boolean;
}) {
  const tr = translations.profile;
  const heavenlyChar = pillar.天干?.天干;
  const earthlyChar = pillar.地支?.地支;
  const heavenlyName = GAN_LABELS[heavenlyChar] || heavenlyChar;
  const earthlyName = ZHI_LABELS[earthlyChar] || earthlyChar;

  const 化气格变化 = pillar.化气格变化;
  const hiddenStemPairs = [
    { stem: pillar.藏干?.本气?.天干, tenGod: pillar.藏干?.本气?.十神, oldTenGod: 化气格变化?.原藏干十神?.本气 },
    { stem: pillar.藏干?.中气?.天干, tenGod: pillar.藏干?.中气?.十神, oldTenGod: 化气格变化?.原藏干十神?.中气 },
    { stem: pillar.藏干?.余气?.天干, tenGod: pillar.藏干?.余气?.十神, oldTenGod: 化气格变化?.原藏干十神?.余气 },
  ].filter((pair) => pair.stem != null && pair.stem !== '无') as { stem: string; tenGod: string | null; oldTenGod?: string }[];

  return (
    <div
      className={`relative rounded-xl px-5 py-6 min-h-full flex flex-col items-center text-center ${
        isDayMaster
          ? 'bg-gold-deep/4 border-2 border-gold-deep/30'
          : 'bg-parchment border border-gold-deep/15'
      }`}
    >
      {/* Day Master Badge */}
      {isDayMaster && (
        <div className="day-master-badge absolute -top-4 left-1/2 -translate-x-1/2 text-white rounded-[20px] px-3.5 py-1 text-[11px] font-semibold uppercase tracking-[0.1em]">
          {tr.dayMasterBadge[language]}
        </div>
      )}

      {/* Pillar Label */}
      <div className="mb-3">
        <p className="text-base font-semibold text-bronze-muted opacity-70 mt-1 mb-0 italic">
          {pillarLabel}
        </p>
      </div>

      {/* HEAVENLY STEM Section */}
      <div className="w-full">
        <label className={SECTION_LABEL_CLS}>{tr.heavenlyStem[language]}</label>
        <div className={`font-zh text-5xl font-semibold leading-none mt-1.5 mb-3 ${isDayMaster ? 'text-gold-deep' : 'text-bronze-muted'}`}>
          {heavenlyChar}
        </div>
        <div className="flex flex-col items-center justify-center gap-[5px]">
          {(() => {
            const stemTransform: { 合化五行: string; 原五行: string; label: string } | undefined =
              tianGanHua ? { 合化五行: tianGanHua.元素, 原五行: tianGanHua.原五行, label: tianGanHua.label } : undefined;
            const origLabel = language === 'en' ? heavenlyName : (GAN_LABELS_CH[heavenlyChar] ?? heavenlyChar);

            if (!stemTransform) {
              const el = STEM_ELEMENT[heavenlyChar];
              const Icon = el ? ELEMENT_ICONS[el] : null;
              const color = el ? ELEMENT_COLOR[el] : undefined;
              return (
                <div className="flex items-center justify-center gap-1">
                  {Icon && <Icon style={{ fontSize: 13, color }} />}
                  <p className={CAPTION_CLS}>{origLabel}</p>
                </div>
              );
            }

            const OldElement = stemTransform.原五行;
            const OldIcon = OldElement ? ELEMENT_ICONS[OldElement] : null;
            const oldColor = OldElement ? ELEMENT_COLOR[OldElement] : undefined;
            const NewElement = stemTransform.合化五行;
            const NewIcon = NewElement ? ELEMENT_ICONS[NewElement] : null;
            const newColor = NewElement ? ELEMENT_COLOR[NewElement] : undefined;
            const combinedLabel = language === 'en'
              ? `${origLabel.split(' ')[0]} ${ELEMENT_EN[NewElement] ?? NewElement}`
              : `${origLabel[0]}${NewElement}`;

            return (
              <div className="flex items-center justify-center gap-1 text-[13px] text-bronze-muted italic">
                <span className="inline-flex items-center gap-[3px] opacity-55">
                  {OldIcon && <OldIcon style={{ fontSize: 13, color: oldColor }} />}
                  <span>{origLabel}</span>
                </span>
                <span className="mx-0.5 opacity-45">→</span>
                <span className="inline-flex items-center gap-[3px]">
                  {NewIcon && <NewIcon style={{ fontSize: 13, color: newColor }} />}
                  <span>{combinedLabel}</span>
                </span>
              </div>
            );
          })()}
          {anyHeavenlyStemBadge && (
            <span
              className="inline-block text-xs font-zh-sans not-italic text-info-blue/85 bg-info-blue/8 border border-dashed border-info-blue/50 rounded-[20px] px-[7px] py-px whitespace-nowrap leading-[1.6]"
              style={{ visibility: tianGanHua ? 'visible' : 'hidden' }}
            >
              {tianGanHua?.label ?? ' '}
            </span>
          )}
        </div>
        {pillar.天干?.十神 && (() => {
          const oldTenGod = pillar.化气格变化?.原天干十神;
          const hasTransformation = oldTenGod != null && oldTenGod !== '' && oldTenGod !== pillar.天干.十神;

          if (hasTransformation) {
            return (
              <div className="flex flex-row items-center gap-1.5 mt-2 flex-wrap justify-center">
                <TenGodCard value={oldTenGod!} language={language} dimmed />
                <span className="opacity-45 text-[13px] text-bronze-muted">→</span>
                <TenGodCard value={pillar.天干.十神} language={language} />
              </div>
            );
          }

          return (
            <div className="mt-2">
              <TenGodCard value={pillar.天干.十神} language={language} />
            </div>
          );
        })()}
        {pillar.天干?.根基强度 && (() => {
          const cfg = ROOTING_STYLES[pillar.天干.根基强度];
          if (!cfg) return null;
          return (
            <div className="w-full flex flex-col items-center mt-3">
              <span
                className="block w-3/5 text-[11px] italic text-center px-2.5 py-0.5"
                style={{ color: cfg.color, borderLeft: `3px solid ${cfg.color}`, background: cfg.bg }}
              >
                {language === 'en' ? tr[cfg.trKey][language] : pillar.天干.根基强度}
              </span>
            </div>
          );
        })()}
      </div>

      <PillarDivider />

      {/* EARTHLY BRANCH Section */}
      <div className="w-full">
        <label className={SECTION_LABEL_CLS}>{tr.earthlyBranch[language]}</label>
        <div className={`${GLYPH_LG_CLS} font-bold opacity-80 my-3`}>
          {earthlyChar}
        </div>
        {(() => {
          const branchElement = BRANCH_ELEMENT[earthlyChar];
          const ElemIcon = branchElement ? ELEMENT_ICONS[branchElement] : null;
          const elemColor = branchElement ? ELEMENT_COLOR[branchElement] : undefined;
          return (
            <div className="flex items-center justify-center gap-1">
              {ElemIcon && <ElemIcon style={{ fontSize: 13, color: elemColor }} />}
              <p className={CAPTION_CLS}>
                {language === 'en' ? earthlyName : (ZHI_LABELS_CH[earthlyChar] ?? earthlyChar)}
              </p>
            </div>
          );
        })()}
        <div className="w-full flex flex-col items-center mt-2 gap-2">
          {Array.from({ length: maxVoidCount }).map((_, i) => {
            const c = voidStatus.conditions[i];
            if (!c) return <span key={i} className="block w-2/3 text-[11px] px-2.5 py-0.5 invisible">–</span>;
            const tone = VOID_CATEGORY_COLORS[c.category] ?? VOID_CATEGORY_COLORS.mutual;
            return (
              <span
                key={i}
                className="block w-3/5 text-[11px] italic text-center px-2.5 py-0.5"
                style={{ color: tone.color, borderLeft: `3px solid ${tone.color}`, background: tone.bg }}
              >
                {language === 'en' ? c.label.en : c.label.ch}
              </span>
            );
          })}
        </div>
      </div>

      <PillarDivider />

      {/* HIDDEN STEMS Section */}
      <div className="w-[calc(100%+40px)] -mx-5">
        <label className={`${SECTION_LABEL_CLS} mb-3 ${isDayMaster ? 'font-bold' : ''}`}>
          {tr.hiddenStems[language]}
        </label>
        {hiddenStemPairs.length > 0 ? (
          <div className="flex justify-center gap-4 flex-wrap">
            {hiddenStemPairs.map(({ stem, tenGod, oldTenGod }, idx: number) => {
              const QI_LABELS = [tr.primaryQi[language], tr.middleQi[language], tr.residualQi[language]];
              return (
              <div key={idx} className="flex flex-col items-center">
                <span className="text-[10px] font-semibold text-gold-deep/40 uppercase tracking-[0.1em] mb-2">
                  {QI_LABELS[idx]}
                </span>
                <div className={`${GLYPH_MD_CLS} mb-2`}>{stem}</div>
                <div className="flex flex-col items-center justify-center gap-1">
                  {(() => {
                    const stemElement = STEM_ELEMENT[stem];
                    const ElemIcon = stemElement ? ELEMENT_ICONS[stemElement] : null;
                    const elemColor = stemElement ? ELEMENT_COLOR[stemElement] : undefined;
                    return (
                      <div className="flex items-center justify-center gap-[3px]">
                        {ElemIcon && <ElemIcon style={{ fontSize: 11, color: elemColor }} />}
                        <p className="text-[11px] text-bronze-muted/60 m-0 leading-tight">
                          {language === 'en' ? (GAN_LABELS[stem] || stem) : (GAN_LABELS_CH[stem] || stem)}
                        </p>
                      </div>
                    );
                  })()}
                </div>
                {tenGod && (() => {
                  const hasHiddenTransformation = oldTenGod != null && oldTenGod !== '' && oldTenGod !== tenGod;
                  if (hasHiddenTransformation) {
                    return (
                      <div className="flex flex-col items-center gap-1 mt-2">
                        <HiddenTenGodCard value={oldTenGod!} language={language} dimmed />
                        <span className="opacity-45 text-[13px] text-bronze-muted">↓</span>
                        <HiddenTenGodCard value={tenGod} language={language} />
                      </div>
                    );
                  }
                  return (
                    <div className="mt-2">
                      <HiddenTenGodCard value={tenGod} language={language} />
                    </div>
                  );
                })()}
              </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-bronze-muted opacity-45 m-0">{tr.noneLabel[language]}</p>
        )}
      </div>

      <PillarDivider />

      {/* VOID BRANCH PAIRS Section */}
      <div className="w-full">
        <label className={SECTION_LABEL_CLS}>{tr.voidBranchPairs[language]}</label>
        <div className="flex flex-col items-center w-full m-0">
          {xunKong ? (
            <>
              <div className={`${GLYPH_MD_CLS} mt-1.5 mb-3`}>{xunKong.chinese}</div>
              <p
                className={CAPTION_CLS}
                style={{
                  visibility: language === 'en' ? 'visible' : 'hidden',
                  height: language === 'en' ? 'auto' : 0,
                  overflow: 'hidden',
                }}
              >
                {xunKong.english}
              </p>
            </>
          ) : (
            <>
              <div className="h-9 flex items-center justify-center text-xl font-semibold text-bronze-muted opacity-45 mb-3" />
              <p
                className="text-[13px] m-0 invisible overflow-hidden"
                style={{ height: language === 'en' ? 'auto' : 0 }}
              >
                –
              </p>
            </>
          )}
        </div>
      </div>

      <PillarDivider />

      {/* 12 LIFE STAGES Section */}
      <div className="w-full">
        <label className={SECTION_LABEL_CLS}>{tr.twelveLifeStages[language]}</label>

        <div className="flex flex-col gap-3">
          {/* Day Master reference */}
          <div className="flex-1">
            <span className={SUB_LABEL_CLS}>{tr.dayMasterRef[language]}</span>
            {lifeStages?.xingYun ? (
              <>
                <div className={`${GLYPH_MD_CLS} mt-1.5 mb-3`}>{lifeStages.xingYun.chinese}</div>
                {language === 'en' && (
                  <p className="text-xs text-bronze-muted opacity-75 m-0 italic">{lifeStages.xingYun.english}</p>
                )}
              </>
            ) : (
              <p className="text-xl font-bold text-bronze-muted opacity-45 mt-1.5 mb-0">—</p>
            )}
          </div>

          {/* Pillar's Heavenly Stem reference */}
          <div className="flex-1">
            <span className={SUB_LABEL_CLS}>{tr.pillarStemRef[language]}</span>
            {lifeStages?.ziZuo ? (
              <>
                <div className={`${GLYPH_MD_CLS} mt-1.5 mb-3`}>{lifeStages.ziZuo.chinese}</div>
                {language === 'en' && (
                  <p className="text-xs text-bronze-muted opacity-75 m-0 italic">{lifeStages.ziZuo.english}</p>
                )}
              </>
            ) : (
              <p className="text-xl font-bold text-bronze-muted opacity-45 mt-1.5 mb-0">—</p>
            )}
          </div>
        </div>
      </div>

      <PillarDivider />

      {/* NAYIN Section */}
      <div className="w-full">
        <label className={SECTION_LABEL_CLS}>{tr.naYin[language]}</label>
        {naYin ? (
          <>
            <div className={`${GLYPH_MD_CLS} my-3`}>{naYin.chinese}</div>
            {language === 'en' && <p className={CAPTION_CLS}>{naYin.english}</p>}
          </>
        ) : (
          <div className="flex items-center justify-center min-h-[100px] w-full">
            <p className="text-xl font-bold text-bronze-muted opacity-45 m-0">—</p>
          </div>
        )}
      </div>

      {/* SHEN SHA Section */}
      {shenSha && shenSha.length > 0 && (
        <>
          <PillarDivider />
          <div className="w-full">
            <label className={`${SECTION_LABEL_CLS} mb-2.5`}>{tr.shenSha[language]}</label>
            <div className="flex flex-wrap gap-1.5 justify-center">
              {shenSha
                .filter((star, idx, arr) => arr.findIndex(s => s.名称 === star.名称) === idx)
                .map((star, idx) => (
                <div
                  key={idx}
                  className="flex flex-col items-center bg-info-blue/7 border border-info-blue/28 rounded-lg px-2.5 py-1 whitespace-nowrap"
                >
                  <span className="font-zh text-2xl font-normal text-bronze-muted leading-[1.4]">
                    {star.名称}
                  </span>
                  {language === 'en' && SHEN_SHA_LABELS[star.名称] && (
                    <span className="text-[13px] text-bronze-muted/55 leading-snug mt-1">
                      {SHEN_SHA_LABELS[star.名称]}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
