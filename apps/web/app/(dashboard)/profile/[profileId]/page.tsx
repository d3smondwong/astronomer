'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getProfile, getProfiles, deleteProfile, type BaziProfile } from '@/lib/baziOrchestrator';
import { type LifeStageInfo } from '@/lib/twelveLifeStages';
import { type NaYinInfo } from '@/lib/naYin';
import { type VoidInfo } from '@/lib/void';
import { Card, Tag, Tabs, Button, Popconfirm } from 'antd';
import { format } from 'date-fns';
import { Calendar, Clock, MapPin, User, Trash2 } from 'lucide-react';
import { VictoryPie, VictoryChart, VictoryBar, VictoryTheme, VictoryAxis } from 'victory';
import { toast } from 'sonner';

export default function ProfilePage() {
  const params = useParams<{ profileId: string }>();
  const router = useRouter();
  const [profile, setProfile] = useState<BaziProfile | null>(null);
  const [isClient, setIsClient] = useState(false);

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
        <p className="text-gray-500">{isClient ? 'Profile not found' : 'Loading profile...'}</p>
      </div>
    );
  }

  const { baziChart } = profile;
  if (!baziChart) return null;

  const elementData = Object.entries(baziChart.elements).map(([element, value]) => ({
    x: element.charAt(0).toUpperCase() + element.slice(1),
    y: value,
    label: `${element.charAt(0).toUpperCase() + element.slice(1)}: ${value}`,
  }));

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

  // Lookup tables for Heavenly Stems (GAN) and Earthly Branches (ZHI)
  const GAN_LABELS: Record<string, string> = {
    甲: 'Yang Wood', 乙: 'Yin Wood', 丙: 'Yang Fire', 丁: 'Yin Fire',
    戊: 'Yang Earth', 己: 'Yin Earth', 庚: 'Yang Metal', 辛: 'Yin Metal',
    壬: 'Yang Water', 癸: 'Yin Water',
  };

  const ZHI_LABELS: Record<string, string> = {
    子: 'Water Rat', 丑: 'Earth Ox', 寅: 'Wood Tiger', 卯: 'Wood Rabbit',
    辰: 'Earth Dragon', 巳: 'Fire Snake', 午: 'Fire Horse', 未: 'Earth Goat',
    申: 'Metal Monkey', 酉: 'Metal Rooster', 戌: 'Earth Dog', 亥: 'Water Pig',
  };

  const SHI_SHEN_LABELS: Record<string, string> = {
    '比肩': 'Companion',
    '劫财': 'Wealth Robber',
    '食神': 'Food God',
    '伤官': 'Hurting Officer',
    '偏财': 'Indirect Wealth',
    '正财': 'Direct Wealth',
    '七杀': 'Seven Killings',
    '正官': 'Direct Officer',
    '偏印': 'Indirect Resource',
    '正印': 'Direct Resource',
    '我': 'Self',
  };

  const PillarCard = ({
    relationshipLabel,
    pillarLabel,
    pillar,
    isDayMaster = false,
    lifeStages,
    naYin,
    xunKong,
    showVoidSection = true,
    voidCheckPair,
  }: {
    relationshipLabel: string;
    pillarLabel: string;
    pillar: any;
    isDayMaster?: boolean;
    lifeStages?: { xingYun: LifeStageInfo | null; ziZuo: LifeStageInfo | null } | null;
    naYin?: NaYinInfo | null;
    xunKong?: VoidInfo | null;
    showVoidSection?: boolean;
    voidCheckPair?: VoidInfo | null;  // Day Pillar's void pair, used to check this pillar's earthly branch
  }) => {
    const heavenlyChar = pillar.heavenlyStem;
    const earthlyChar = pillar.earthlyBranch;
    const heavenlyName = GAN_LABELS[heavenlyChar] || heavenlyChar;
    const earthlyName = ZHI_LABELS[earthlyChar] || earthlyChar;
    const isVoid = voidCheckPair != null && voidCheckPair.chinese.includes(earthlyChar);

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
            Day Master
          </div>
        )}

        {/* Relationship & Pillar Labels */}
        <div style={{ marginBottom: '12px' }}>
          <h3
            style={{
              fontSize: '10px',
              fontWeight: '600',
              color: 'rgba(115, 92, 0, 0.45)',
              margin: 0,
              textTransform: 'uppercase',
              letterSpacing: '0.15em',
              fontFamily: 'Noto Serif, serif',
            }}
          >
            {relationshipLabel}
          </h3>
          <p
            style={{
              fontSize: '13px',
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
              fontSize: '10px',
              fontWeight: '600',
              color: 'rgba(115, 92, 0, 0.45)',
              textTransform: 'uppercase',
              letterSpacing: '0.12em',
              fontFamily: 'Noto Serif, serif',
              display: 'block',
              marginBottom: '8px',
            }}
          >
            Heavenly Stem
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
            {heavenlyName}
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
              fontSize: '10px',
              fontWeight: '600',
              color: 'rgba(115, 92, 0, 0.45)',
              textTransform: 'uppercase',
              letterSpacing: '0.12em',
              fontFamily: 'Noto Serif, serif',
              display: 'block',
              marginBottom: '8px',
            }}
          >
            Earthly Branch
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
            {earthlyName}
          </p>
          <div style={{ width: '100%', display: 'flex', justifyContent: 'center', marginTop: '8px' }}>
            <div
              style={{
                borderLeft: `3px solid ${isVoid ? '#8C2F2F' : 'transparent'}`,
                background: isVoid ? 'rgba(140, 47, 47, 0.08)' : 'transparent',
                padding: '4px 12px',
                width: '60%',
                boxSizing: 'border-box',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <span style={{ fontSize: '11px', color: '#8C2F2F', fontFamily: 'Noto Serif, serif', fontStyle: 'italic', visibility: isVoid ? 'visible' : 'hidden' }}>
                Void
              </span>
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

        {/* HIDDEN STEMS Section */}
        <div style={{ width: '100%' }}>
          <label
            style={{
              fontSize: '10px',
              fontWeight: isDayMaster ? '700' : '600',
              color: 'rgba(115, 92, 0, 0.45)',
              textTransform: 'uppercase',
              letterSpacing: '0.12em',
              fontFamily: 'Noto Serif, serif',
              display: 'block',
              marginBottom: '12px',
            }}
          >
            Hidden Stems
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
                const QI_LABELS = ['Primary Qi', 'Middle Qi', 'Residual Qi'];
                return (
                <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <span
                    style={{
                      fontSize: '9px',
                      fontWeight: '600',
                      color: 'rgba(115, 92, 0, 0.4)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.1em',
                      fontFamily: 'Noto Serif, serif',
                      marginBottom: '6px',
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
                      marginBottom: '6px',
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
                    {GAN_LABELS[stem] || stem}
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
                        marginTop: '4px',
                      }}
                    >
                      <span
                        style={{
                          fontSize: '11px',
                          color: 'rgba(115, 92, 0, 0.7)',
                          fontFamily: 'Ma Shan Zheng, serif',
                        }}
                      >
                        {tenGod}
                      </span>
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
                    </div>
                  )}
                </div>
                );
              })}
            </div>
          ) : (
            <p style={{ fontSize: '12px', color: '#4d4635', opacity: 0.45, margin: 0 }}>
              None
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
              fontSize: '10px',
              fontWeight: '600',
              color: 'rgba(115, 92, 0, 0.45)',
              textTransform: 'uppercase',
              letterSpacing: '0.12em',
              fontFamily: 'Noto Serif, serif',
              display: 'block',
              marginBottom: '8px',
            }}
          >
            Void Branch Pairs
          </label>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', margin: '12px 0' }}>
            {xunKong && showVoidSection ? (
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
                <p style={{ fontSize: '13px', margin: 0, visibility: 'hidden' }}>–</p>
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
              fontSize: '10px',
              fontWeight: '600',
              color: 'rgba(115, 92, 0, 0.45)',
              textTransform: 'uppercase',
              letterSpacing: '0.12em',
              fontFamily: 'Noto Serif, serif',
              display: 'block',
              marginBottom: '8px',
            }}
          >
            12 Life Stages
          </label>

          <div style={{ display: 'flex', gap: '12px' }}>
            {/* Day Master reference */}
            <div style={{ flex: 1 }}>
              <span
                style={{
                  fontSize: '9px',
                  fontWeight: '600',
                  color: 'rgba(115, 92, 0, 0.35)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                  fontFamily: 'Noto Serif, serif',
                }}
              >
                Day Master
              </span>
              {lifeStages?.xingYun ? (
                <>
                  <div
                    style={{
                      fontSize: '56px',
                      fontWeight: '700',
                      color: '#4d4635',
                      margin: '6px 0 4px 0',
                      lineHeight: 1,
                      fontFamily: 'Ma Shan Zheng, serif',
                    }}
                  >
                    {lifeStages.xingYun.chinese}
                  </div>
                  <p style={{ fontSize: '12px', color: '#4d4635', opacity: 0.75, margin: 0, fontStyle: 'italic' }}>
                    {lifeStages.xingYun.english}
                  </p>
                </>
              ) : (
                <p style={{ fontSize: '20px', fontWeight: '700', color: '#4d4635', opacity: 0.45, margin: '6px 0 0 0' }}>—</p>
              )}
            </div>

            {/* Pillar's Heavenly Stem reference */}
            <div style={{ flex: 1 }}>
              <span
                style={{
                  fontSize: '9px',
                  fontWeight: '600',
                  color: 'rgba(115, 92, 0, 0.35)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                  fontFamily: 'Noto Serif, serif',
                }}
              >
                Pillar's Stem
              </span>
              {lifeStages?.ziZuo ? (
                <>
                  <div
                    style={{
                      fontSize: '56px',
                      fontWeight: '700',
                      color: '#4d4635',
                      margin: '6px 0 4px 0',
                      lineHeight: 1,
                      fontFamily: 'Ma Shan Zheng, serif',
                    }}
                  >
                    {lifeStages.ziZuo.chinese}
                  </div>
                  <p style={{ fontSize: '12px', color: '#4d4635', opacity: 0.75, margin: 0, fontStyle: 'italic' }}>
                    {lifeStages.ziZuo.english}
                  </p>
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
              fontSize: '10px',
              fontWeight: '600',
              color: 'rgba(115, 92, 0, 0.45)',
              textTransform: 'uppercase',
              letterSpacing: '0.12em',
              fontFamily: 'Noto Serif, serif',
              display: 'block',
              marginBottom: '8px',
            }}
          >
            NaYin
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
        <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-semibold mb-4 font-serif text-gold-deep">{profile.name}</h1>
              <div className="space-y-2">
                <div className="flex items-center gap-6 text-sm text-bronze-muted">
                  <span className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    {format(profile.birthDate, 'PPP')}
                  </span>
                  <span className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    {profile.birthTime}
                  </span>
                  <span className="flex items-center gap-2">
                    <MapPin className="w-4 h-4" />
                    {profile.birthLocation}
                  </span>
                  <span className="flex items-center gap-2">
                    <User className="w-4 h-4" />
                    {profile.gender.charAt(0).toUpperCase() + profile.gender.slice(1)}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {(profile.latitude != null && profile.longitude != null) && (
                <Tag color="blue">
                  {profile.latitude.toFixed(4)}° / {profile.longitude.toFixed(4)}°
                </Tag>
              )}
              <Popconfirm
                title="Delete Profile"
                description={`Are you sure you want to delete "${profile.name}"? This action cannot be undone.`}
                onConfirm={handleDeleteProfile}
                okText="Delete"
                cancelText="Cancel"
                okButtonProps={{ danger: true }}
              >
                <Button danger type="text" size="small" icon={<Trash2 className="w-4 h-4" />}>
                  Delete
                </Button>
              </Popconfirm>
            </div>
          </div>
        </Card>

        {/* Tabs */}
        <Tabs
          items={[
            {
              key: 'pillars',
              label: 'Four Pillars',
              children: (
                <div className="space-y-4" style={{ overflowX: 'hidden' }}>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4" style={{ position: 'relative', paddingTop: '20px', minWidth: 0 }}>
                    <PillarCard
                      relationshipLabel="ANCESTRY"
                      pillarLabel="Year Pillar"
                      pillar={baziChart.yearPillar}
                      isDayMaster={false}
                      lifeStages={baziChart.lifeStages?.year}
                      naYin={baziChart.naYin?.year}
                      xunKong={baziChart.xunKong?.year}
                      voidCheckPair={baziChart.xunKong?.day}
                    />
                    <PillarCard
                      relationshipLabel="PARENTS"
                      pillarLabel="Month Pillar"
                      pillar={baziChart.monthPillar}
                      isDayMaster={false}
                      lifeStages={baziChart.lifeStages?.month}
                      naYin={baziChart.naYin?.month}
                      xunKong={baziChart.xunKong?.month}
                      showVoidSection={false}
                      voidCheckPair={baziChart.xunKong?.day}
                    />
                    <PillarCard
                      relationshipLabel="SELF"
                      pillarLabel="Day Pillar"
                      pillar={baziChart.dayPillar}
                      isDayMaster={true}
                      lifeStages={baziChart.lifeStages?.day}
                      naYin={baziChart.naYin?.day}
                      xunKong={baziChart.xunKong?.day}
                    />
                    <PillarCard
                      relationshipLabel="CHILDREN"
                      pillarLabel="Hour Pillar"
                      pillar={baziChart.hourPillar}
                      isDayMaster={false}
                      lifeStages={baziChart.lifeStages?.hour}
                      naYin={baziChart.naYin?.hour}
                      xunKong={baziChart.xunKong?.hour}
                      showVoidSection={false}
                      voidCheckPair={baziChart.xunKong?.day}
                    />
                  </div>
                </div>
              ),
            },
            {
              key: 'elements',
              label: 'Elements',
              children: (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
                      <h3 className="text-lg font-semibold mb-2 font-serif text-gold-deep">Element Distribution</h3>
                      <p className="text-sm text-bronze-muted/70 mb-4">Your Five Element Balance</p>
                      <svg viewBox="0 0 400 400" className="w-full max-w-md mx-auto">
                        <VictoryPie
                          standalone={false}
                          width={400}
                          height={400}
                          data={pieData}
                          colorScale={pieData.map(d => d.fill)}
                          labels={({ datum }) => `${datum.x}\n${datum.y}`}
                          style={{
                            labels: { fontSize: 16, fill: 'white' },
                          }}
                          innerRadius={80}
                        />
                      </svg>
                    </Card>

                    <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
                      <h3 className="text-lg font-semibold mb-2 font-serif text-gold-deep">Element Strength</h3>
                      <p className="text-sm text-bronze-muted/70 mb-4">Comparative View</p>
                      <svg viewBox="0 0 450 300" className="w-full">
                        <VictoryChart
                          standalone={false}
                          width={450}
                          height={300}
                          domainPadding={30}
                          theme={VictoryTheme.material}
                        >
                          <VictoryAxis />
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
                    <h3 className="text-lg font-semibold mb-2 font-serif text-gold-deep">Lucky Elements</h3>
                    <p className="text-sm text-bronze-muted/70 mb-4">Elements that can bring balance to your chart</p>
                    <div className="flex gap-2 flex-wrap">
                      {baziChart.luckyElements.map((element) => (
                        <Tag
                          key={element}
                          color={elementColors[element as keyof typeof elementColors]}
                          style={{ color: 'white', fontSize: '14px', padding: '4px 12px' }}
                        >
                          {element}
                        </Tag>
                      ))}
                    </div>
                  </Card>
                </div>
              ),
            },
            {
              key: 'insights',
              label: 'Insights',
              children: (
                <div className="space-y-4">
                  <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
                    <h3 className="text-lg font-semibold mb-2 font-serif text-gold-deep">Personality Profile</h3>
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm text-bronze-muted/70 mb-2">Your Archetype: <strong className="text-gold-deep">{baziChart.personalityTraits.archetype}</strong></p>
                        <p className="text-sm text-bronze-muted/70 mb-2">Element: <strong className="text-gold-deep">{baziChart.personalityTraits.element}</strong></p>
                      </div>
                      <div>
                        <p className="text-sm text-bronze-muted/70 mb-2">Key Traits:</p>
                        <div className="flex gap-2 flex-wrap">
                          {baziChart.personalityTraits.traits.map((trait) => (
                            <Tag key={trait} style={{ color: '#735c00', backgroundColor: 'rgba(115, 92, 0, 0.1)' }}>
                              {trait}
                            </Tag>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-sm text-bronze-muted/70 mb-2">Strengths:</p>
                        <ul className="list-disc list-inside text-sm text-bronze-muted">
                          {baziChart.personalityTraits.strengths.map((strength) => (
                            <li key={strength}>{strength}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <p className="text-sm text-bronze-muted/70 mb-2">Areas to Note:</p>
                        <ul className="list-disc list-inside text-sm text-bronze-muted">
                          {baziChart.personalityTraits.challenges.map((challenge) => (
                            <li key={challenge}>{challenge}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <p className="text-sm text-bronze-muted/70 mb-2">Lucky Colors: <strong>{baziChart.personalityTraits.luckyColors.join(', ')}</strong></p>
                        <p className="text-sm text-bronze-muted/70">Lucky Numbers: <strong>{baziChart.personalityTraits.luckyNumbers.join(', ')}</strong></p>
                      </div>
                    </div>
                  </Card>

                  <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
                    <h3 className="text-lg font-semibold mb-2 font-serif text-gold-deep">Your Summary</h3>
                    <p className="text-base leading-relaxed text-bronze-muted mb-4">{baziChart.personalitySummary}</p>
                  </Card>

                  <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
                    <h3 className="text-lg font-semibold mb-2 font-serif text-gold-deep">Life Aspects</h3>
                    <p className="text-sm text-bronze-muted/70 mb-4">Key areas influenced by your Bazi chart</p>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="p-4 border border-gold-deep/10 rounded-lg">
                        <h4 className="font-medium mb-2 text-gold-deep">Career & Wealth</h4>
                        <p className="text-sm text-bronze-muted/80">
                          Your {baziChart.personalityTraits.element} element suggests focusing on careers that align with your natural strengths.
                          Lucky elements provide additional guidance for prosperity.
                        </p>
                      </div>
                      <div className="p-4 border border-gold-deep/10 rounded-lg">
                        <h4 className="font-medium mb-2 text-gold-deep">Relationships</h4>
                        <p className="text-sm text-bronze-muted/80">
                          The Day Pillar's earthly branch represents your spouse palace. Understanding this
                          helps in relationship compatibility and harmony.
                        </p>
                      </div>
                      <div className="p-4 border border-gold-deep/10 rounded-lg">
                        <h4 className="font-medium mb-2 text-gold-deep">Health & Wellness</h4>
                        <p className="text-sm text-bronze-muted/80">
                          Element imbalances can indicate areas of health to watch. Strengthening weak
                          elements through lifestyle choices promotes wellbeing.
                        </p>
                      </div>
                      <div className="p-4 border border-gold-deep/10 rounded-lg">
                        <h4 className="font-medium mb-2 text-gold-deep">Personal Growth</h4>
                        <p className="text-sm text-bronze-muted/80">
                          Your chart reveals natural talents and areas for development. Focus on cultivating
                          your lucky elements for optimal growth.
                        </p>
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
