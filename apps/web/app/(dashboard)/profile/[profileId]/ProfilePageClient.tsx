'use client';

import { useState } from 'react';
import { type LifeStageInfo, type NaYinInfo, type VoidInfo, type VoidStatus } from '@/types/baziLibraryTypes';
import { type ProfileRecord } from '@/lib/profilesDb';
import { Card, Tabs, Button, Popconfirm, Tooltip } from 'antd';
import { format } from 'date-fns';
import { Calendar, Clock, MapPin, User, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';
import { deleteProfileAction } from './actions';
import PillarInteractionsCard from './PillarInteractionsCard';
import DayMasterStrengthCard from './DayMasterStrengthCard';

interface ProfilePageClientProps {
  profileRecord: ProfileRecord;
  chartData: any;
}

export default function ProfilePageClient({ profileRecord, chartData }: ProfilePageClientProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const { language } = useLanguage();
  const tr = translations.profile;

  // Reconstruct profile object for rendering
  const profile = {
    id: profileRecord.id,
    name: profileRecord.name,
    birthDate: new Date(profileRecord.birthData.year, profileRecord.birthData.month - 1, profileRecord.birthData.day),
    birthTime: `${String(profileRecord.birthData.hour).padStart(2, '0')}:${String(profileRecord.birthData.minute).padStart(2, '0')}`,
    birthLocation: profileRecord.birthLocation,
    gender: profileRecord.birthData.gender === 1 ? 'male' : 'female',
    usedSolarTime: profileRecord.birthData.use_solar_time_correction,
  };

  const handleDeleteProfile = async () => {
    setIsDeleting(true);
    try {
      await deleteProfileAction(profileRecord.id);
      toast.success('Profile deleted successfully');
    } catch (error) {
      console.error('Error deleting profile:', error);
      toast.error('Failed to delete profile');
      setIsDeleting(false);
    }
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

  const ELEMENT_EN: Record<string, string> = {
    '木': 'Wood', '火': 'Fire', '土': 'Earth', '金': 'Metal', '水': 'Water',
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
    '七杀': 'Seven Killings', '正官': 'Direct Officer', '偏印': 'Indirect Resource',
    '正印': 'Direct Resource', '我': 'Self',
  };

  const SHEN_SHA_LABELS: Record<string, string> = {
    // Year branch stars
    '龙德': 'Dragon Virtue', '红鸾': 'Red Luan', '天喜': 'Heavenly Joy',
    '桃花': 'Peach Blossom', '墙内桃花': 'Inner Peach Blossom', '墙外桃花': 'Outer Peach Blossom',
    '孤辰': 'Lonely Star', '寡宿': "Widow's Lodge",
    '大耗': 'Great Drain', '病符': 'Illness Star', '吊客': 'Mourning Guest',
    '丧门': 'Messenger of Death', '白虎': 'White Tiger', '卷舌': 'Curled Tongue',
    '披麻': 'Mourning Attire', '披头': 'Disheveled Head',
    '吟呻': 'Groaning Malefic', '破碎': 'Shattering Malefic', '白衣': 'White Garment Malefic',
    '元辰': 'Primary Star', '六厄': 'Six Adversities',
    // Month branch stars
    '天德贵人': 'Heavenly Virtue Noble', '月德贵人': 'Monthly Virtue Noble', '天医': 'Heavenly Doctor',
    '月空': 'Monthly Void', '血刃': 'Blood Blade', '天赦': 'Heavenly Pardon',
    '天转': 'Heavenly Turn', '地转': 'Earthly Turn', '季节性退神': 'Seasonal Retreating Spirit',
    '天德合': 'Heavenly Virtue Combination', '月德合': 'Monthly Virtue Combination',
    '天月德合': 'Heavenly & Monthly Virtue Combination',
    // Day/year branch stars
    '将星': 'Commanding Star', '华盖': 'Canopy Star', '驿马': 'Travel Horse',
    '劫煞': 'Robbery Sha', '亡神': 'Perishing God', '灾煞': 'Calamity Sha',
    '沐浴桃花': 'Peach Blossom Bath',
    // Day/year stem stars
    '昼天乙贵人': 'Day Heavenly Noble', '夜天乙贵人': 'Night Heavenly Noble',
    '文昌': 'Literary Star', '学堂': 'Academy Star', '太极贵人': 'Tai Ji Noble',
    '禄神': 'Prosperity Star', '金舆': 'Golden Carriage', '国印': 'National Seal',
    '福星': 'Fortune Star', '真词馆': 'True Literary Academy', '正词馆': 'Standard Literary Academy',
    '红艳': 'Red Charm', '天厨贵人': 'Heavenly Kitchen Noble', '飞刃': 'Flying Blade',
    '天官贵人': 'Heavenly Officer Noble', '羊刃': 'Sheep Blade', '流霞': 'Blood Disaster Star',
    '勾煞': 'Hook Disaster', '绞煞': 'Twist Disaster',
    // Derived & special
    '福禄双美': 'Double Fortune & Prosperity',
    '天上三奇': "Heaven's Three Wonders", '地下三奇': "Earth's Three Wonders",
    '人中三奇': "Human's Three Wonders",
    '寅命自禄': 'Yin Self-Lu', '卯命自禄': 'Mao Self-Lu',
    '申命自禄': 'Shen Self-Lu', '酉命自禄': 'You Self-Lu',
    '巳中藏丙': 'Si Hidden Bing', '亥中藏壬': 'Hai Hidden Ren',
    // Pillar formations
    '阴阳差错': 'Yin-Yang Discord', '十恶大败': 'Ten Great Failures',
    '魁罡': 'Kui Gang',
    '进神': 'Advancing Spirit', '六秀': 'Six Elegance', '八专': 'Eight Specialty',
    '九丑': 'Nine Ugly', '孤鸾': 'Lone Phoenix', '退气神煞': 'Retreating Qi Sha',
    '四废': 'Four Wastes', '金神': 'Golden Deity', '十灵': 'Ten Spirits',
    '天罗': 'Heavenly Net', '地网': 'Earthly Net', '童子煞': 'Child Sha',
    '隔角煞': 'Separated Corner Sha',
    // Relational stars (can appear on pillars)
    '禄元互换': 'Lu-Yuan Exchange', '进真禄': 'Advancing True Lu',
    '退真禄': 'Retreating True Lu', '德秀贵人': 'Virtue & Elegance Noble', '暗禄': 'Hidden Lu',
  };

  const tianGanHuaMap: Record<string, { 元素: string; label: string }> = {};
  const pillarDynamic = (chartData?.作用?.柱位动态 ?? []) as any[];
  for (const ix of pillarDynamic) {
    if (ix.类型 === '天干合' && (ix.形态 === '合化' || ix.形态 === '化气格') && ix.元素) {
      for (const pillarName of Object.keys(ix.组合明细 ?? {})) {
        tianGanHuaMap[pillarName] = { 元素: ix.元素, label: `天干合·${ix.形态}` };
      }
    }
  }

  const anyHeavenlyStemBadge = Object.keys(tianGanHuaMap).length > 0;

  const PillarCard = ({
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
    tianGanHua?: { 元素: string; label: string };
  }) => {
    const heavenlyChar = pillar.天干;
    const earthlyChar = pillar.地支;
    const heavenlyName = GAN_LABELS[heavenlyChar] || heavenlyChar;
    const earthlyName = ZHI_LABELS[earthlyChar] || earthlyChar;
    const activeVoidCount = (voidStatus.primaryVoid === true ? 1 : 0) + voidStatus.mutualVoid;

    const hiddenStemPairs = [
      { stem: pillar.藏干?.本气, tenGod: pillar.藏干十神?.本气十神 },
      { stem: pillar.藏干?.中气, tenGod: pillar.藏干十神?.中气十神 },
      { stem: pillar.藏干?.余气, tenGod: pillar.藏干十神?.余气十神 },
    ].filter((pair) => pair.stem != null && pair.stem !== '无') as { stem: string; tenGod: string | null }[];

    return (
      <div
        style={{
          position: 'relative',
          background: isDayMaster ? 'rgba(115, 92, 0, 0.04)' : '#faf8f2',
          border: isDayMaster ? '2px solid rgba(115, 92, 0, 0.3)' : '1px solid rgba(115, 92, 0, 0.15)',
          borderRadius: '12px',
          padding: '24px 20px',
          minHeight: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
        }}
      >
        {/* Day Master Badge */}
        {isDayMaster && (
          <div
            style={{
              position: 'absolute',
              top: '-16px',
              left: '50%',
              transform: 'translateX(-50%)',
              background: 'linear-gradient(135deg, #735c00, #a08000)',
              color: 'white',
              borderRadius: '20px',
              padding: '4px 14px',
              fontSize: '11px',
              fontWeight: '600',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              fontFamily: 'Noto Serif, serif',
            }}
          >
            {tr.dayMasterBadge[language]}
          </div>
        )}

        {/* Pillar Label */}
        <div style={{ marginBottom: '12px' }}>
          <p
            style={{
              fontSize: '16px',
              fontWeight: '600',
              color: '#4d4635',
              opacity: 0.7,
              margin: '4px 0 0 0',
              fontStyle: 'italic',
            }}
          >
            {pillarLabel}
          </p>
        </div>

        {/* HEAVENLY STEM Section */}
        <div style={{ width: '100%' }}>
          <label
            style={{
              fontSize: '14px',
              fontWeight: '600',
              color: 'rgba(115, 92, 0, 0.45)',
              textTransform: 'uppercase',
              letterSpacing: '0.12em',
              fontFamily: 'Noto Serif, serif',
              display: 'block',
              marginBottom: '8px',
            }}
          >
            {tr.heavenlyStem[language]}
          </label>
          <div
            style={{
              fontSize: '48px',
              fontWeight: '600',
              color: isDayMaster ? '#735c00' : '#4d4635',
              margin: '6px 0 12px 0',
              lineHeight: 1,
              fontFamily: 'Ma Shan Zheng, serif',
            }}
          >
            {heavenlyChar}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '5px' }}>
            <p
              style={{
                fontSize: '13px',
                color: '#4d4635',
                opacity: 0.75,
                margin: 0,
                fontStyle: 'italic',
              }}
            >
              {(() => {
                const stemTransform: { 合化五行: string; label: string } | undefined =
                  tianGanHua ? { 合化五行: tianGanHua.元素, label: tianGanHua.label } : undefined;
                const origLabel = language === 'en' ? heavenlyName : (GAN_LABELS_CH[heavenlyChar] ?? heavenlyChar);
                if (!stemTransform) return origLabel;
                let combinedLabel: string;
                if (language === 'en') {
                  const polarity = origLabel.split(' ')[0];
                  combinedLabel = `${polarity} ${ELEMENT_EN[stemTransform.合化五行] ?? stemTransform.合化五行}`;
                } else {
                  const polarity = origLabel[0];
                  combinedLabel = `${polarity}${stemTransform.合化五行}`;
                }
                return (
                  <>
                    <span style={{ opacity: 0.55 }}>{origLabel}</span>
                    <span style={{ margin: '0 4px', opacity: 0.45 }}>→</span>
                    <span>{combinedLabel}</span>
                  </>
                );
              })()}
            </p>
            {anyHeavenlyStemBadge && (
              <span style={{
                display: 'inline-block',
                fontSize: '12px',
                fontFamily: '"Noto Sans SC", sans-serif',
                fontStyle: 'normal',
                color: 'rgba(30, 90, 170, 0.85)',
                background: 'rgba(30, 90, 170, 0.08)',
                border: '1px dashed rgba(30, 90, 170, 0.5)',
                borderRadius: '20px',
                padding: '1px 7px',
                whiteSpace: 'nowrap',
                lineHeight: 1.6,
                visibility: tianGanHua ? 'visible' : 'hidden',
              }}>
                {tianGanHua?.label ?? ' '}
              </span>
            )}
          </div>
          {pillar.天干十神 && (() => {
            const displayChar = pillar.天干十神 === '日主' ? '我' : pillar.天干十神;
            const displayLabel = pillar.天干十神 === '日主' ? 'Self' : (SHI_SHEN_LABELS[pillar.天干十神] ?? pillar.天干十神);
            return (
              <div
                style={{
                  display: 'inline-flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  border: '1px solid rgba(115, 92, 0, 0.25)',
                  borderRadius: '8px',
                  padding: '4px 10px',
                  background: 'rgba(115, 92, 0, 0.06)',
                  marginTop: '8px',
                }}
              >
                <span
                  style={{
                    fontSize: '13px',
                    color: 'rgba(115, 92, 0, 0.75)',
                    fontFamily: 'Ma Shan Zheng, serif',
                  }}
                >
                  {displayChar}
                </span>
                {language === 'en' && (
                  <span
                    style={{
                      fontSize: '10px',
                      color: 'rgba(115, 92, 0, 0.6)',
                      fontFamily: 'Noto Serif, serif',
                      marginTop: '2px',
                    }}
                  >
                    {displayLabel}
                  </span>
                )}
              </div>
            );
          })()}
          {pillar.根基强度 && (() => {
            const rootingMap: Record<string, { trKey: keyof typeof tr; color: string; bg: string }> = {
              '深根': { trKey: 'rootingDeep',     color: '#2d6a2d', bg: 'rgba(45, 106, 45, 0.08)'  },
              '中根': { trKey: 'rootingModerate', color: '#3d5a80', bg: 'rgba(61, 90, 128, 0.08)'  },
              '浅根': { trKey: 'rootingLight',    color: '#8a5200', bg: 'rgba(138, 82, 0, 0.08)'   },
              '无根': { trKey: 'rootingNone',     color: '#7a4040', bg: 'rgba(122, 64, 64, 0.08)'  },
            };
            const cfg = rootingMap[pillar.根基强度];
            if (!cfg) return null;
            return (
              <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: '12px' }}>
                <span style={{ fontSize: '11px', color: cfg.color, fontFamily: 'Noto Serif, serif', fontStyle: 'italic',
                               borderLeft: `3px solid ${cfg.color}`, background: cfg.bg, padding: '2px 10px' }}>
                  {language === 'en' ? tr[cfg.trKey][language] : pillar.根基强度}
                </span>
              </div>
            );
          })()}
        </div>

        {/* Divider */}
        <div
          style={{
            width: '80%',
            height: '1px',
            background: 'rgba(115, 92, 0, 0.12)',
            margin: '16px 0',
          }}
        />

        {/* EARTHLY BRANCH Section */}
        <div style={{ width: '100%' }}>
          <label
            style={{
              fontSize: '14px',
              fontWeight: '600',
              color: 'rgba(115, 92, 0, 0.45)',
              textTransform: 'uppercase',
              letterSpacing: '0.12em',
              fontFamily: 'Noto Serif, serif',
              display: 'block',
              marginBottom: '8px',
            }}
          >
            {tr.earthlyBranch[language]}
          </label>
          <div
            style={{
              fontSize: '48px',
              fontWeight: '700',
              color: '#4d4635',
              opacity: 0.8,
              margin: '12px 0 12px 0',
              lineHeight: 1,
              fontFamily: 'Ma Shan Zheng, serif',
            }}
          >
            {earthlyChar}
          </div>
          <p
            style={{
              fontSize: '13px',
              color: '#4d4635',
              opacity: 0.75,
              margin: 0,
              fontStyle: 'italic',
            }}
          >
            {language === 'en' ? earthlyName : (ZHI_LABELS_CH[earthlyChar] ?? earthlyChar)}
          </p>
          <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: '8px', gap: '3px' }}>
            {voidStatus.primaryVoid === true && (
              <span style={{ fontSize: '11px', color: '#8C2F2F', fontFamily: 'Noto Serif, serif', fontStyle: 'italic',
                             borderLeft: '3px solid #8C2F2F', background: 'rgba(140, 47, 47, 0.08)', padding: '2px 10px' }}>
                {tr.primaryVoid[language]}
              </span>
            )}
            {Array.from({ length: voidStatus.mutualVoid }).map((_, i) => (
              <span key={i} style={{ fontSize: '11px', color: '#8C2F2F', fontFamily: 'Noto Serif, serif', fontStyle: 'italic',
                             borderLeft: '3px solid #8C2F2F', background: 'rgba(140, 47, 47, 0.08)', padding: '2px 10px' }}>
                {tr.mutualVoid[language]}
              </span>
            ))}
            {Array.from({ length: maxVoidCount - activeVoidCount }).map((_, i) => (
              <span key={i} style={{ fontSize: '11px', padding: '2px 10px', visibility: 'hidden' }}>–</span>
            ))}
          </div>
        </div>

        {/* Divider */}
        <div
          style={{
            width: '80%',
            height: '1px',
            background: 'rgba(115, 92, 0, 0.12)',
            margin: '16px 0',
          }}
        />

        {/* HIDDEN STEMS Section */}
        <div style={{ width: 'calc(100% + 40px)', marginLeft: '-20px', marginRight: '-20px' }}>
          <label
            style={{
              fontSize: '14px',
              fontWeight: isDayMaster ? '700' : '600',
              color: 'rgba(115, 92, 0, 0.45)',
              textTransform: 'uppercase',
              letterSpacing: '0.12em',
              fontFamily: 'Noto Serif, serif',
              display: 'block',
              marginBottom: '12px',
            }}
          >
            {tr.hiddenStems[language]}
          </label>
          {hiddenStemPairs.length > 0 ? (
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                gap: '16px',
                flexWrap: 'wrap',
              }}
            >
              {hiddenStemPairs.map(({ stem, tenGod }, idx: number) => {
                const QI_LABELS = [tr.primaryQi[language], tr.middleQi[language], tr.residualQi[language]];
                return (
                <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <span
                    style={{
                      fontSize: '10px',
                      fontWeight: '600',
                      color: 'rgba(115, 92, 0, 0.4)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.1em',
                      fontFamily: 'Noto Serif, serif',
                      marginBottom: '8px',
                    }}
                  >
                    {QI_LABELS[idx]}
                  </span>
                  <div
                    style={{
                      fontSize: '36px',
                      fontWeight: '600',
                      color: '#4d4635',
                      lineHeight: 1,
                      fontFamily: 'Ma Shan Zheng, serif',
                      marginBottom: '8px',
                    }}
                  >
                    {stem}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                    <p
                      style={{
                        fontSize: '11px',
                        color: 'rgba(77, 70, 53, 0.6)',
                        margin: 0,
                        lineHeight: 1.2,
                      }}
                    >
                      {language === 'en' ? (GAN_LABELS[stem] || stem) : (GAN_LABELS_CH[stem] || stem)}
                    </p>
                  </div>
                  {tenGod && (
                    <div
                      style={{
                        display: 'inline-flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        border: '1px solid rgba(115, 92, 0, 0.2)',
                        borderRadius: '6px',
                        padding: '3px 8px',
                        background: 'rgba(115, 92, 0, 0.05)',
                        marginTop: '8px',
                      }}
                    >
                      <span
                        style={{
                          fontSize: '13px',
                          color: 'rgba(115, 92, 0, 0.7)',
                          fontFamily: 'Ma Shan Zheng, serif',
                          marginBottom: '4px',
                        }}
                      >
                        {tenGod}
                      </span>
                      {language === 'en' && (
                        <span
                          style={{
                            fontSize: '9px',
                            color: 'rgba(115, 92, 0, 0.55)',
                            fontFamily: 'Noto Serif, serif',
                            marginTop: '1px',
                          }}
                        >
                          {SHI_SHEN_LABELS[tenGod] ?? tenGod}
                        </span>
                      )}
                    </div>
                  )}
                </div>
                );
              })}
            </div>
          ) : (
            <p style={{ fontSize: '12px', color: '#4d4635', opacity: 0.45, margin: 0 }}>
              {tr.noneLabel[language]}
            </p>
          )}
        </div>

        {/* Divider */}
        <div
          style={{
            width: '80%',
            height: '1px',
            background: 'rgba(115, 92, 0, 0.12)',
            margin: '16px 0',
          }}
        />

        {/* VOID BRANCH PAIRS Section */}
        <div style={{ width: '100%' }}>
          <label
            style={{
              fontSize: '14px',
              fontWeight: '600',
              color: 'rgba(115, 92, 0, 0.45)',
              textTransform: 'uppercase',
              letterSpacing: '0.12em',
              fontFamily: 'Noto Serif, serif',
              display: 'block',
              marginBottom: '8px',
            }}
          >
            {tr.voidBranchPairs[language]}
          </label>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', margin: 0 }}>
            {xunKong ? (
              <>
                <div
                  style={{
                    fontSize: '36px',
                    fontWeight: '600',
                    color: '#4d4635',
                    margin: '6px 0 12px 0',
                    lineHeight: 1,
                    fontFamily: 'Ma Shan Zheng, serif',
                  }}
                >
                  {xunKong.chinese}
                </div>
                <p
                  style={{
                    fontSize: '13px',
                    color: '#4d4635',
                    opacity: 0.75,
                    margin: 0,
                    fontStyle: 'italic',
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
                <div
                  style={{
                    height: '36px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '20px',
                    fontWeight: '600',
                    color: '#4d4635',
                    opacity: 0.45,
                    marginBottom: '12px',
                  }}
                >
                </div>
                <p style={{ fontSize: '13px', margin: 0, visibility: 'hidden', height: language === 'en' ? 'auto' : 0, overflow: 'hidden' }}>–</p>
              </>
            )}
          </div>
        </div>

        {/* Divider */}
        <div
          style={{
            width: '80%',
            height: '1px',
            background: 'rgba(115, 92, 0, 0.12)',
            margin: '16px 0',
          }}
        />

        {/* 12 LIFE STAGES Section */}
        <div style={{ width: '100%' }}>
          <label
            style={{
              fontSize: '14px',
              fontWeight: '600',
              color: 'rgba(115, 92, 0, 0.45)',
              textTransform: 'uppercase',
              letterSpacing: '0.12em',
              fontFamily: 'Noto Serif, serif',
              display: 'block',
              marginBottom: '8px',
            }}
          >
            {tr.twelveLifeStages[language]}
          </label>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Day Master reference */}
            <div style={{ flex: 1 }}>
              <span
                style={{
                  fontSize: '12px',
                  fontWeight: '600',
                  color: 'rgba(115, 92, 0, 0.35)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                  fontFamily: 'Noto Serif, serif',
                }}
              >
                {tr.dayMasterRef[language]}
              </span>
              {lifeStages?.xingYun ? (
                <>
                  <div
                    style={{
                      fontSize: '36px',
                      fontWeight: '600',
                      color: '#4d4635',
                      margin: '6px 0 12px 0',
                      lineHeight: 1,
                      fontFamily: 'Ma Shan Zheng, serif',
                    }}
                  >
                    {lifeStages.xingYun.chinese}
                  </div>
                  {language === 'en' && (
                    <p style={{ fontSize: '12px', color: '#4d4635', opacity: 0.75, margin: 0, fontStyle: 'italic' }}>
                      {lifeStages.xingYun.english}
                    </p>
                  )}
                </>
              ) : (
                <p style={{ fontSize: '20px', fontWeight: '700', color: '#4d4635', opacity: 0.45, margin: '6px 0 0 0' }}>—</p>
              )}
            </div>

            {/* Pillar's Heavenly Stem reference */}
            <div style={{ flex: 1 }}>
              <span
                style={{
                  fontSize: '12px',
                  fontWeight: '600',
                  color: 'rgba(115, 92, 0, 0.35)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                  fontFamily: 'Noto Serif, serif',
                }}
              >
                {tr.pillarStemRef[language]}
              </span>
              {lifeStages?.ziZuo ? (
                <>
                  <div
                    style={{
                      fontSize: '36px',
                      fontWeight: '600',
                      color: '#4d4635',
                      margin: '6px 0 12px 0',
                      lineHeight: 1,
                      fontFamily: 'Ma Shan Zheng, serif',
                    }}
                  >
                    {lifeStages.ziZuo.chinese}
                  </div>
                  {language === 'en' && (
                    <p style={{ fontSize: '12px', color: '#4d4635', opacity: 0.75, margin: 0, fontStyle: 'italic' }}>
                      {lifeStages.ziZuo.english}
                    </p>
                  )}
                </>
              ) : (
                <p style={{ fontSize: '20px', fontWeight: '700', color: '#4d4635', opacity: 0.45, margin: '6px 0 0 0' }}>—</p>
              )}
            </div>
          </div>
        </div>

        {/* Divider */}
        <div
          style={{
            width: '80%',
            height: '1px',
            background: 'rgba(115, 92, 0, 0.12)',
            margin: '16px 0',
          }}
        />

        {/* NAYIN Section */}
        <div style={{ width: '100%' }}>
          <label
            style={{
              fontSize: '14px',
              fontWeight: '600',
              color: 'rgba(115, 92, 0, 0.45)',
              textTransform: 'uppercase',
              letterSpacing: '0.12em',
              fontFamily: 'Noto Serif, serif',
              display: 'block',
              marginBottom: '8px',
            }}
          >
            {tr.naYin[language]}
          </label>
          {naYin ? (
            <>
              <div
                style={{
                  fontSize: '36px',
                  fontWeight: '600',
                  color: '#4d4635',
                  opacity: 1.0,
                  margin: '12px 0 12px 0',
                  lineHeight: 1,
                  fontFamily: 'Ma Shan Zheng, serif',
                }}
              >
                {naYin.chinese}
              </div>
              {language === 'en' && (
                <p
                  style={{
                    fontSize: '13px',
                    color: '#4d4635',
                    opacity: 0.75,
                    margin: 0,
                    fontStyle: 'italic',
                  }}
                >
                  {naYin.english}
                </p>
              )}
            </>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100px', width: '100%' }}>
              <p style={{ fontSize: '20px', fontWeight: '700', color: '#4d4635', opacity: 0.45, margin: 0 }}>
                —
              </p>
            </div>
          )}
        </div>

        {/* SHEN SHA Section */}
        {shenSha && shenSha.length > 0 && (
          <>
            <div
              style={{
                width: '80%',
                height: '1px',
                background: 'rgba(115, 92, 0, 0.12)',
                margin: '16px 0',
              }}
            />
            <div style={{ width: '100%' }}>
              <label
                style={{
                  fontSize: '14px',
                  fontWeight: '600',
                  color: 'rgba(115, 92, 0, 0.45)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.12em',
                  fontFamily: 'Noto Serif, serif',
                  display: 'block',
                  marginBottom: '10px',
                }}
              >
                {tr.shenSha[language]}
              </label>
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '6px',
                  justifyContent: 'center',
                }}
              >
                {shenSha
                  .filter((star, idx, arr) => arr.findIndex(s => s.名称 === star.名称) === idx)
                  .map((star, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      background: 'rgba(30, 90, 200, 0.07)',
                      border: '1px solid rgba(30, 90, 200, 0.28)',
                      borderRadius: '8px',
                      padding: '4px 10px',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    <span
                      style={{
                        fontSize: '24px',
                        fontWeight: '400',
                        fontFamily: 'Ma Shan Zheng, serif',
                        color: '#4d4635',
                        lineHeight: 1.4,
                      }}
                    >
                      {star.名称}
                    </span>
                    {language === 'en' && SHEN_SHA_LABELS[star.名称] && (
                      <span
                        style={{
                          fontSize: '13px',
                          fontFamily: 'Noto Serif, serif',
                          color: 'rgba(77, 70, 53, 0.55)',
                          lineHeight: 1.3,
                          marginTop: '4px',
                        }}
                      >
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
  };

  return (
    <div className="h-full overflow-auto" style={{ overflowX: 'hidden' }}>
      <div className="max-w-screen-2xl mx-auto px-4 py-6 space-y-6" style={{ overflowX: 'hidden' }}>
        {/* Profile Header */}
        <Card style={{
          borderColor: 'rgba(115, 92, 0, 0.1)',
          background: 'linear-gradient(180deg, #243447 0%, #1B263B 100%)',
          position: 'relative'
        }}>
          <div className="flex items-start justify-between">
            {/* Name + Info Grid */}
            <div className="flex-1 min-w-0">
              <h1 className="text-3xl font-semibold mb-3 font-serif" style={{ color: '#E8F4F8' }}>{profile.name}</h1>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {/* Date of Birth */}
                <div className="flex flex-col gap-0.5">
                  <span style={{
                    fontSize: 10,
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    color: '#A8BCC9',
                    fontWeight: 500
                  }}>
                    Date of Birth
                  </span>
                  <span className="flex items-center gap-1.5 text-sm" style={{ color: '#D4DFE6' }}>
                    <Calendar className="w-3.5 h-3.5 shrink-0" />
                    {format(profile.birthDate, 'PPP')}
                  </span>
                </div>

                {/* Birth Time */}
                <div className="flex flex-col gap-0.5">
                  <span style={{
                    fontSize: 10,
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    color: '#A8BCC9',
                    fontWeight: 500
                  }}>
                    Birth Time
                  </span>
                  <span className="flex items-center gap-1.5 text-sm" style={{ color: '#D4DFE6' }}>
                    <Clock className="w-3.5 h-3.5 shrink-0" />
                    {profile.birthTime}
                    {profile.usedSolarTime && (
                      <Tooltip
                        title="True Solar Time conversion is utilised for this chart"
                        color="#fbf9f4"
                        styles={{
                          root: {
                            color: '#4d4635',
                          },
                        }}
                      >
                        <span style={{
                          display: 'inline-block',
                          backgroundColor: '#A8BCC9',
                          color: '#1B263B',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '10px',
                          fontWeight: 600,
                          cursor: 'help',
                          marginLeft: '4px'
                        }}>
                          TST
                        </span>
                      </Tooltip>
                    )}
                  </span>
                </div>

                {/* Birth Location */}
                <div className="flex flex-col gap-0.5">
                  <span style={{
                    fontSize: 10,
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    color: '#A8BCC9',
                    fontWeight: 500
                  }}>
                    Birth Location
                  </span>
                  <span className="flex items-center gap-1.5 text-sm" style={{ color: '#D4DFE6' }}>
                    <MapPin className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">{profile.birthLocation}</span>
                  </span>
                </div>

                {/* Gender */}
                <div className="flex flex-col gap-0.5">
                  <span style={{
                    fontSize: 10,
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    color: '#A8BCC9',
                    fontWeight: 500
                  }}>
                    Gender
                  </span>
                  <span className="flex items-center gap-1.5 text-sm" style={{ color: '#D4DFE6' }}>
                    <User className="w-3.5 h-3.5 shrink-0" />
                    {profile.gender === 'male' ? tr.male[language] : tr.female[language]}
                  </span>
                </div>
              </div>
            </div>

          </div>

          {/* Delete Button - Top Right Corner */}
          <div style={{
            position: 'absolute',
            top: '16px',
            right: '16px'
          }}>
            <Tooltip
              title={tr.deleteBtn[language]}
              color="#DC3545"
              styles={{
                root: {
                  color: '#FFFFFF',
                },
              }}
            >
              <Popconfirm
                title={tr.deleteTitle[language]}
                description={`Are you sure you want to delete "${profile.name}"? This action cannot be undone.`}
                onConfirm={handleDeleteProfile}
                okText={tr.deleteOk[language]}
                cancelText={tr.deleteCancel[language]}
                okButtonProps={{ danger: true }}
              >
                <Button
                  danger
                  type="text"
                  size="small"
                  icon={<Trash2 className="w-4 h-4" />}
                  loading={isDeleting}
                  disabled={isDeleting}
                  style={{
                    color: '#D4DFE6',
                    borderColor: 'transparent',
                    opacity: isDeleting ? 0.6 : 1,
                  }}
                  onMouseEnter={(e) => {
                    if (!isDeleting) {
                      e.currentTarget.style.color = '#E8F4F8';
                      e.currentTarget.style.backgroundColor = 'rgba(232, 244, 248, 0.1)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isDeleting) {
                      e.currentTarget.style.color = '#D4DFE6';
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }
                  }}
                />
              </Popconfirm>
            </Tooltip>
          </div>
        </Card>

        {/* Tabs */}
        <Tabs
          items={[
            {
              key: 'pillars',
              label: tr.tabFourPillars[language],
              children: (
                <div className="space-y-4" style={{ overflowX: 'hidden' }}>
                  {(() => {
                    const siZhu = chartData?.四柱实体 || {};

                    // Void status computed from Python data (空亡, 年日互换空亡, 月日互换空亡, 日时互换空亡)
                    const buildVoidStatus = (pillarData: any) => ({
                      primaryVoid: pillarData?.空亡 !== '无' && pillarData?.空亡 !== undefined,
                      mutualVoid: [pillarData?.年日互换空亡, pillarData?.月日互换空亡, pillarData?.日时互换空亡]
                        .filter(v => v !== undefined && v !== '无').length,
                    });

                    const yearVS  = buildVoidStatus(siZhu.年柱);
                    const monthVS = buildVoidStatus(siZhu.月柱);
                    const dayVS   = buildVoidStatus(siZhu.日柱);
                    const hourVS  = buildVoidStatus(siZhu.时柱);
                    const countVoids = (vs: VoidStatus) => (vs.primaryVoid === true ? 1 : 0) + vs.mutualVoid;
                    const maxVoidCount = Math.max(countVoids(yearVS), countVoids(monthVS), countVoids(dayVS), countVoids(hourVS));

                    // Helper to extract element from naYin phrase (last character typically contains the element)
                    const extractElementFromNaYin = (naYinPhrase: string): 'Metal' | 'Wood' | 'Water' | 'Fire' | 'Earth' => {
                      const lastChar = naYinPhrase.charAt(naYinPhrase.length - 1);
                      const elementMap: Record<string, 'Metal' | 'Wood' | 'Water' | 'Fire' | 'Earth'> = {
                        '金': 'Metal', '木': 'Wood', '水': 'Water', '火': 'Fire', '土': 'Earth',
                      };
                      return elementMap[lastChar] ?? 'Metal';
                    };

                    // Helper to build lifeStage, naYin, xunKong objects from pillar data
                    const buildLifeStage = (lifeStageData: any) => {
                      if (!lifeStageData) return null;
                      // lifeStageData is { 星运: "养", 自坐: "衰" }
                      return {
                        xingYun: { chinese: lifeStageData.星运, english: '' },
                        ziZuo: { chinese: lifeStageData.自坐, english: '' }
                      };
                    };
                    const buildNaYin = (naYinValue: any) => naYinValue ? { chinese: naYinValue, english: '', element: extractElementFromNaYin(naYinValue) } : null;
                    const buildXunKong = (voidValue: any) => voidValue && voidValue !== '无' ? { chinese: voidValue, english: '' } : null;

                    const pillarShenSha = chartData?.神煞 ?? {};

                    return (
                      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4" style={{ position: 'relative', paddingTop: '20px', minWidth: 0 }}>
                        <PillarCard pillarLabel={tr.yearPillar[language]}  pillar={siZhu.年柱}  isDayMaster={false} lifeStages={buildLifeStage(siZhu.年柱?.十二长生)}  naYin={buildNaYin(siZhu.年柱?.纳音)}  xunKong={buildXunKong(siZhu.年柱?.空亡地支)}  voidStatus={yearVS}  maxVoidCount={maxVoidCount} shenSha={pillarShenSha.年柱} tianGanHua={tianGanHuaMap['年柱']} />
                        <PillarCard pillarLabel={tr.monthPillar[language]} pillar={siZhu.月柱} isDayMaster={false} lifeStages={buildLifeStage(siZhu.月柱?.十二长生)} naYin={buildNaYin(siZhu.月柱?.纳音)} xunKong={buildXunKong(siZhu.月柱?.空亡地支)} voidStatus={monthVS} maxVoidCount={maxVoidCount} shenSha={pillarShenSha.月柱} tianGanHua={tianGanHuaMap['月柱']} />
                        <PillarCard pillarLabel={tr.dayPillar[language]}   pillar={siZhu.日柱}   isDayMaster={true}  lifeStages={buildLifeStage(siZhu.日柱?.十二长生)}   naYin={buildNaYin(siZhu.日柱?.纳音)}   xunKong={buildXunKong(siZhu.日柱?.空亡地支)}   voidStatus={dayVS}   maxVoidCount={maxVoidCount} shenSha={pillarShenSha.日柱} tianGanHua={tianGanHuaMap['日柱']} />
                        <PillarCard pillarLabel={tr.hourPillar[language]}  pillar={siZhu.时柱}  isDayMaster={false} lifeStages={buildLifeStage(siZhu.时柱?.十二长生)}  naYin={buildNaYin(siZhu.时柱?.纳音)}  xunKong={buildXunKong(siZhu.时柱?.空亡地支)}  voidStatus={hourVS}  maxVoidCount={maxVoidCount} shenSha={pillarShenSha.时柱} tianGanHua={tianGanHuaMap['时柱']} />
                      </div>
                    );
                  })()}
                  <PillarInteractionsCard chartData={chartData} language={language} />
                  <DayMasterStrengthCard chartData={chartData} language={language} />
                </div>
              ),
            },
            {
              key: 'elements',
              label: tr.tabElements[language],
              children: (
                <div className="space-y-4">
                  <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
                    <p className="text-center text-bronze-muted/70">Coming Soon</p>
                  </Card>
                </div>
              ),
            },
            {
              key: 'insights',
              label: tr.tabInsights[language],
              children: (
                <div className="space-y-4">
                  <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
                    <p className="text-center text-bronze-muted/70">Coming Soon</p>
                  </Card>
                </div>
              ),
            },
          ]}
        />
      </div>
    </div>
  );
}
