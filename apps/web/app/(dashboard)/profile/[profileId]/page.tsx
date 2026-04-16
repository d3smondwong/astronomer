'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import type { BaziProfile } from '@/lib/baziOrchestrator';
import { getProfile, getProfiles, deleteProfile } from '@/lib/baziStorage';
import { type LifeStageInfo } from '@/lib/twelveLifeStages';
import { type NaYinInfo } from '@/lib/naYin';
import { type VoidInfo, type VoidStatus, computeVoidStatus } from '@/lib/void';
import { Card, Tag, Tabs, Button, Popconfirm, Tooltip } from 'antd';
import { format } from 'date-fns';
import { Calendar, Clock, MapPin, User, Trash2 } from 'lucide-react';
import { VictoryPie, VictoryChart, VictoryBar, VictoryTheme, VictoryAxis } from 'victory';
import { toast } from 'sonner';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';

export default function ProfilePage() {
  const params = useParams<{ profileId: string }>();
  const router = useRouter();
  const [profile, setProfile] = useState<BaziProfile | null>(null);
  const [isClient, setIsClient] = useState(false);
  const { language } = useLanguage();
  const tr = translations.profile;

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (isClient && params?.profileId) {
      const loadedProfile = getProfile(params.profileId as string);
      setProfile(loadedProfile || null);
    }
  }, [params?.profileId, isClient]);

  const handleDeleteProfile = () => {
    if (params?.profileId) {
      deleteProfile(params.profileId as string);
      toast.success('Profile deleted successfully');

      // Get all remaining profiles
      const allProfiles = getProfiles();

      // If there are other profiles, navigate to the first one
      if (allProfiles.length > 0) {
        router.push(`/profile/${allProfiles[0].id}`);
      } else {
        // If no profiles left, go to home
        router.push('/');
      }
    }
  };

  if (!isClient || !profile) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500">{isClient ? tr.profileNotFound[language] : tr.loadingProfile[language]}</p>
      </div>
    );
  }

  const { baziChart } = profile;
  if (!baziChart) return null;

  const elementData = Object.entries(baziChart.elements).map(([element, value]) => {
    const key = element.charAt(0).toUpperCase() + element.slice(1);
    const displayName = language === 'en'
      ? key
      : (translations.element[key as keyof typeof translations.element]?.ch ?? key);
    return { x: key, y: value, label: `${displayName}: ${value}` };
  });

  const elementColors = {
    Wood: '#22c55e',
    Fire: '#ef4444',
    Earth: '#f59e0b',
    Metal: '#94a3b8',
    Water: '#3b82f6',
  };

  const pieData = elementData.map(item => ({
    ...item,
    fill: elementColors[item.x as keyof typeof elementColors],
  }));

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
    '七杀': 'Seven Killings', '正官': 'Direct Officer', '偏印': 'Indirect Resource',
    '正印': 'Direct Resource', '我': 'Self',
  };

  const PillarCard = ({
    pillarLabel,
    pillar,
    isDayMaster = false,
    lifeStages,
    naYin,
    xunKong,
    voidStatus,
    maxVoidCount,
  }: {
    pillarLabel: string;
    pillar: any;
    isDayMaster?: boolean;
    lifeStages?: { xingYun: LifeStageInfo | null; ziZuo: LifeStageInfo | null } | null;
    naYin?: NaYinInfo | null;
    xunKong?: VoidInfo | null;
    voidStatus: VoidStatus;
    maxVoidCount: number;
  }) => {
    const heavenlyChar = pillar.heavenlyStem;
    const earthlyChar = pillar.earthlyBranch;
    const heavenlyName = GAN_LABELS[heavenlyChar] || heavenlyChar;
    const earthlyName = ZHI_LABELS[earthlyChar] || earthlyChar;
    const isAnyVoid = voidStatus.primaryVoid === true || voidStatus.reverseVoid === true;
    const activeVoidCount = [voidStatus.primaryVoid === true, voidStatus.reverseVoid === true].filter(Boolean).length;

    const hiddenStemPairs = [
      { stem: pillar.primaryQi, tenGod: pillar.primaryQiTenGod },
      { stem: pillar.middleQi, tenGod: pillar.middleQiTenGod },
      { stem: pillar.residualQi, tenGod: pillar.residualQiTenGod },
    ].filter((pair) => pair.stem != null) as { stem: string; tenGod: string | null }[];

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
              fontSize: '56px',
              fontWeight: '700',
              color: isDayMaster ? '#735c00' : '#4d4635',
              margin: '12px 0 12px 0',
              lineHeight: 1,
              fontFamily: 'Ma Shan Zheng, serif',
            }}
          >
            {heavenlyChar}
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
            {language === 'en' ? heavenlyName : (GAN_LABELS_CH[heavenlyChar] ?? heavenlyChar)}
          </p>
          {pillar.heavenlyStemTenGod && (() => {
            const displayChar = pillar.heavenlyStemTenGod === '日主' ? '我' : pillar.heavenlyStemTenGod;
            const displayLabel = pillar.heavenlyStemTenGod === '日主' ? 'Self' : (SHI_SHEN_LABELS[pillar.heavenlyStemTenGod] ?? pillar.heavenlyStemTenGod);
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
              fontSize: '56px',
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
            {voidStatus.reverseVoid === true && (
              <span style={{ fontSize: '11px', color: '#8C2F2F', fontFamily: 'Noto Serif, serif', fontStyle: 'italic',
                             borderLeft: '3px solid #8C2F2F', background: 'rgba(140, 47, 47, 0.08)', padding: '2px 10px' }}>
                {tr.reverseVoid[language]}
              </span>
            )}
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
        <div style={{ width: '100%' }}>
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
                    height: '56px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '56px',
                    fontWeight: '700',
                    color: '#4d4635',
                    opacity: 1.0,
                    lineHeight: 1,
                    fontFamily: 'Ma Shan Zheng, serif',
                    marginBottom: '12px',
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
                    height: '56px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '20px',
                    fontWeight: '700',
                    color: '#4d4635',
                    opacity: 0.45,
                    marginBottom: '12px',
                  }}
                >
                  —
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

          <div style={{ display: 'flex', gap: '12px' }}>
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
                      fontSize: '56px',
                      fontWeight: '700',
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
                      fontSize: '56px',
                      fontWeight: '700',
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
                  fontSize: '56px',
                  fontWeight: '700',
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
      </div>
    );
  };

  return (
    <div className="h-full overflow-auto" style={{ overflowX: 'hidden' }}>
      <div className="max-w-7xl mx-auto p-6 space-y-6" style={{ overflowX: 'hidden' }}>
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
                      <Tooltip title="True Solar Time conversion is utilised for this chart">
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
            <Tooltip title={tr.deleteBtn[language]}>
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
                  style={{
                    color: '#D4DFE6',
                    borderColor: 'transparent'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = '#E8F4F8';
                    e.currentTarget.style.backgroundColor = 'rgba(232, 244, 248, 0.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = '#D4DFE6';
                    e.currentTarget.style.backgroundColor = 'transparent';
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
                    const dayVoid  = baziChart.xunKong?.day  ?? null;
                    const yearVoid = baziChart.xunKong?.year ?? null;
                    const yearVS  = computeVoidStatus({ pillarType: 'year',  branch: baziChart.yearPillar.earthlyBranch,  dayVoidPair: dayVoid,  yearVoidPair: null });
                    const monthVS = computeVoidStatus({ pillarType: 'month', branch: baziChart.monthPillar.earthlyBranch, dayVoidPair: dayVoid,  yearVoidPair: null });
                    const dayVS   = computeVoidStatus({ pillarType: 'day',   branch: baziChart.dayPillar.earthlyBranch,   dayVoidPair: null,     yearVoidPair: yearVoid });
                    const hourVS  = computeVoidStatus({ pillarType: 'hour',  branch: baziChart.hourPillar.earthlyBranch,  dayVoidPair: dayVoid,  yearVoidPair: null });
                    const countVoids = (vs: VoidStatus) => [vs.primaryVoid === true, vs.reverseVoid === true].filter(Boolean).length;
                    const maxVoidCount = Math.max(countVoids(yearVS), countVoids(monthVS), countVoids(dayVS), countVoids(hourVS));
                    return (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4" style={{ position: 'relative', paddingTop: '20px', minWidth: 0 }}>
                        <PillarCard pillarLabel={tr.yearPillar[language]}  pillar={baziChart.yearPillar}  isDayMaster={false} lifeStages={baziChart.lifeStages?.year}  naYin={baziChart.naYin?.year}  xunKong={baziChart.xunKong?.year}  voidStatus={yearVS}  maxVoidCount={maxVoidCount} />
                        <PillarCard pillarLabel={tr.monthPillar[language]} pillar={baziChart.monthPillar} isDayMaster={false} lifeStages={baziChart.lifeStages?.month} naYin={baziChart.naYin?.month} xunKong={baziChart.xunKong?.month} voidStatus={monthVS} maxVoidCount={maxVoidCount} />
                        <PillarCard pillarLabel={tr.dayPillar[language]}   pillar={baziChart.dayPillar}   isDayMaster={true}  lifeStages={baziChart.lifeStages?.day}   naYin={baziChart.naYin?.day}   xunKong={baziChart.xunKong?.day}   voidStatus={dayVS}   maxVoidCount={maxVoidCount} />
                        <PillarCard pillarLabel={tr.hourPillar[language]}  pillar={baziChart.hourPillar}  isDayMaster={false} lifeStages={baziChart.lifeStages?.hour}  naYin={baziChart.naYin?.hour}  xunKong={baziChart.xunKong?.hour}  voidStatus={hourVS}  maxVoidCount={maxVoidCount} />
                      </div>
                    );
                  })()}
                </div>
              ),
            },
            {
              key: 'elements',
              label: tr.tabElements[language],
              children: (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
                      <h3 className="text-lg font-semibold mb-2 font-serif text-gold-deep">{tr.elementDistrib[language]}</h3>
                      <p className="text-sm text-bronze-muted/70 mb-4">{tr.fiveElementBal[language]}</p>
                      <svg viewBox="0 0 400 400" className="w-full max-w-md mx-auto">
                        <VictoryPie
                          standalone={false}
                          width={400}
                          height={400}
                          data={pieData}
                          colorScale={pieData.map(d => d.fill)}
                          labels={({ datum }) => {
                            const name = language === 'en' ? datum.x : (translations.element[datum.x as keyof typeof translations.element]?.ch ?? datum.x);
                            return `${name}\n${datum.y}`;
                          }}
                          style={{
                            labels: { fontSize: 16, fill: 'white' },
                          }}
                          innerRadius={80}
                        />
                      </svg>
                    </Card>

                    <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
                      <h3 className="text-lg font-semibold mb-2 font-serif text-gold-deep">{tr.elementStrength[language]}</h3>
                      <p className="text-sm text-bronze-muted/70 mb-4">{tr.comparativeView[language]}</p>
                      <svg viewBox="0 0 450 300" className="w-full">
                        <VictoryChart
                          standalone={false}
                          width={450}
                          height={300}
                          domainPadding={30}
                          theme={VictoryTheme.material}
                        >
                          <VictoryAxis
                            tickFormat={(tick) => language === 'en' ? tick : (translations.element[tick as keyof typeof translations.element]?.ch ?? tick)}
                          />
                          <VictoryAxis dependentAxis />
                          <VictoryBar
                            data={elementData}
                            style={{
                              data: {
                                fill: ({ datum }) => elementColors[datum.x as keyof typeof elementColors],
                              },
                            }}
                          />
                        </VictoryChart>
                      </svg>
                    </Card>
                  </div>

                  <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
                    <h3 className="text-lg font-semibold mb-2 font-serif text-gold-deep">{tr.luckyElements[language]}</h3>
                    <p className="text-sm text-bronze-muted/70 mb-4">{tr.luckyElemDesc[language]}</p>
                    <div className="flex gap-2 flex-wrap">
                      {baziChart.luckyElements.map((element) => (
                        <Tag
                          key={element}
                          color={elementColors[element as keyof typeof elementColors]}
                          style={{ color: 'white', fontSize: '14px', padding: '4px 12px' }}
                        >
                          {language === 'en' ? element : (translations.element[element as keyof typeof translations.element]?.ch ?? element)}
                        </Tag>
                      ))}
                    </div>
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
                    <h3 className="text-lg font-semibold mb-2 font-serif text-gold-deep">{tr.personalityProfile[language]}</h3>
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm text-bronze-muted/70 mb-2">{tr.yourArchetype[language]} <strong className="text-gold-deep">{baziChart.personalityTraits.archetype}</strong></p>
                        <p className="text-sm text-bronze-muted/70 mb-2">{tr.elementLabel[language]} <strong className="text-gold-deep">
                          {language === 'en' ? baziChart.personalityTraits.element : (translations.element[baziChart.personalityTraits.element as keyof typeof translations.element]?.ch ?? baziChart.personalityTraits.element)}
                        </strong></p>
                      </div>
                      <div>
                        <p className="text-sm text-bronze-muted/70 mb-2">{tr.keyTraits[language]}</p>
                        <div className="flex gap-2 flex-wrap">
                          {baziChart.personalityTraits.traits.map((trait) => (
                            <Tag key={trait} style={{ color: '#735c00', backgroundColor: 'rgba(115, 92, 0, 0.1)' }}>
                              {trait}
                            </Tag>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-sm text-bronze-muted/70 mb-2">{tr.strengths[language]}</p>
                        <ul className="list-disc list-inside text-sm text-bronze-muted">
                          {baziChart.personalityTraits.strengths.map((strength) => (
                            <li key={strength}>{strength}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <p className="text-sm text-bronze-muted/70 mb-2">{tr.areasToNote[language]}</p>
                        <ul className="list-disc list-inside text-sm text-bronze-muted">
                          {baziChart.personalityTraits.challenges.map((challenge) => (
                            <li key={challenge}>{challenge}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <p className="text-sm text-bronze-muted/70 mb-2">{tr.luckyColors[language]} <strong>{baziChart.personalityTraits.luckyColors.join(', ')}</strong></p>
                        <p className="text-sm text-bronze-muted/70">{tr.luckyNumbers[language]} <strong>{baziChart.personalityTraits.luckyNumbers.join(', ')}</strong></p>
                      </div>
                    </div>
                  </Card>

                  <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
                    <h3 className="text-lg font-semibold mb-2 font-serif text-gold-deep">{tr.yourSummary[language]}</h3>
                    <p className="text-base leading-relaxed text-bronze-muted mb-4">{baziChart.personalitySummary}</p>
                  </Card>

                  <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
                    <h3 className="text-lg font-semibold mb-2 font-serif text-gold-deep">{tr.lifeAspects[language]}</h3>
                    <p className="text-sm text-bronze-muted/70 mb-4">{tr.lifeAspectsDesc[language]}</p>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="p-4 border border-gold-deep/10 rounded-lg">
                        <h4 className="font-medium mb-2 text-gold-deep">{tr.careerWealth[language]}</h4>
                        <p className="text-sm text-bronze-muted/80">
                          {tr.careerWealthDesc[language].replace('{element}', language === 'en' ? baziChart.personalityTraits.element : (translations.element[baziChart.personalityTraits.element as keyof typeof translations.element]?.ch ?? baziChart.personalityTraits.element))}
                        </p>
                      </div>
                      <div className="p-4 border border-gold-deep/10 rounded-lg">
                        <h4 className="font-medium mb-2 text-gold-deep">{tr.relationships[language]}</h4>
                        <p className="text-sm text-bronze-muted/80">{tr.relationshipsDesc[language]}</p>
                      </div>
                      <div className="p-4 border border-gold-deep/10 rounded-lg">
                        <h4 className="font-medium mb-2 text-gold-deep">{tr.healthWellness[language]}</h4>
                        <p className="text-sm text-bronze-muted/80">{tr.healthWellnessDesc[language]}</p>
                      </div>
                      <div className="p-4 border border-gold-deep/10 rounded-lg">
                        <h4 className="font-medium mb-2 text-gold-deep">{tr.personalGrowth[language]}</h4>
                        <p className="text-sm text-bronze-muted/80">{tr.personalGrowthDesc[language]}</p>
                      </div>
                    </div>
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
