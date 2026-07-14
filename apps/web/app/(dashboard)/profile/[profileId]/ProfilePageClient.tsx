'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Forest from '@mui/icons-material/Forest';
import LocalFireDepartment from '@mui/icons-material/LocalFireDepartment';
import Terrain from '@mui/icons-material/Terrain';
import StopCircleOutlined from '@mui/icons-material/StopCircleOutlined';
import Waves from '@mui/icons-material/Waves';
import { type LifeStageInfo, type NaYinInfo, type VoidInfo, type VoidStatus, type VoidCondition } from '@/types/baziLibraryTypes';
import { type ProfileRecord } from '@/lib/profilesDb';
import { type InsightsResponse, type StructuredSection } from '@/lib/fastApiClient';
import { Alert, Card, Tabs, Button, Popconfirm, Tooltip, Collapse } from 'antd';
import dayjs from 'dayjs';
import localizedFormat from 'dayjs/plugin/localizedFormat';
import { Calendar, Clock, MapPin, User, Trash2 } from 'lucide-react';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';
import { useAuth } from '@/lib/authContext';
import { reportClientError } from '@/lib/errorReporter';
import FiveElementsCard from './FiveElementsCard';
import PillarInteractionsCard from './PillarInteractionsCard';
import DayMasterStrengthCard from './DayMasterStrengthCard';
import FavorableElementsCard from './FavorableElementsCard';
import InsightsLoading from './InsightsLoading';

dayjs.extend(localizedFormat);

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

const ELEMENT_ICON: Record<string, React.ComponentType<Record<string, unknown>>> = {
  '木': Forest, '火': LocalFireDepartment, '土': Terrain, '金': StopCircleOutlined, '水': Waves,
};

const ELEMENT_COLOR: Record<string, string> = {
  '木': '#2d6a2d', '火': '#b42424', '土': '#8a6200', '金': '#666666', '水': '#1e5a9a',
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
}) => {
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
          {(() => {
            const stemTransform: { 合化五行: string; 原五行: string; label: string } | undefined =
              tianGanHua ? { 合化五行: tianGanHua.元素, 原五行: tianGanHua.原五行, label: tianGanHua.label } : undefined;
            const origLabel = language === 'en' ? heavenlyName : (GAN_LABELS_CH[heavenlyChar] ?? heavenlyChar);

            if (!stemTransform) {
              const el = STEM_ELEMENT[heavenlyChar];
              const Icon = el ? ELEMENT_ICON[el] : null;
              const color = el ? ELEMENT_COLOR[el] : '#4d4635';
              return (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                  {Icon && <Icon style={{ fontSize: 13, color }} />}
                  <p style={{ fontSize: '13px', color: '#4d4635', opacity: 0.75, margin: 0, fontStyle: 'italic' }}>
                    {origLabel}
                  </p>
                </div>
              );
            }

            const OldElement = stemTransform.原五行;
            const OldIcon = OldElement ? ELEMENT_ICON[OldElement] : null;
            const oldColor = OldElement ? ELEMENT_COLOR[OldElement] : '#4d4635';
            const NewElement = stemTransform.合化五行;
            const NewIcon = NewElement ? ELEMENT_ICON[NewElement] : null;
            const newColor = NewElement ? ELEMENT_COLOR[NewElement] : '#4d4635';
            const combinedLabel = language === 'en'
              ? `${origLabel.split(' ')[0]} ${ELEMENT_EN[NewElement] ?? NewElement}`
              : `${origLabel[0]}${NewElement}`;

            return (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', fontSize: '13px', color: '#4d4635', fontStyle: 'italic' }}>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', opacity: 0.55 }}>
                  {OldIcon && <OldIcon style={{ fontSize: 13, color: oldColor }} />}
                  <span>{origLabel}</span>
                </span>
                <span style={{ margin: '0 2px', opacity: 0.45 }}>→</span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                  {NewIcon && <NewIcon style={{ fontSize: 13, color: newColor }} />}
                  <span>{combinedLabel}</span>
                </span>
              </div>
            );
          })()}
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
        {pillar.天干?.十神 && (() => {
          const displayChar  = pillar.天干.十神 === '日主' ? '我' : pillar.天干.十神;
          const displayLabel = pillar.天干.十神 === '日主' ? 'Self' : (SHI_SHEN_LABELS[pillar.天干.十神] ?? pillar.天干.十神);
          const oldTenGod    = pillar.化气格变化?.原天干十神;
          const hasTransformation = oldTenGod != null && oldTenGod !== '' && oldTenGod !== pillar.天干.十神;

          const TenGodCard = ({ value, dimmed }: { value: string; dimmed?: boolean }) => {
            const char  = value === '日主' ? '我' : value;
            const label = value === '日主' ? 'Self' : (SHI_SHEN_LABELS[value] ?? value);
            return (
              <div style={{
                display: 'inline-flex', flexDirection: 'column', alignItems: 'center',
                border: '1px solid rgba(115, 92, 0, 0.25)', borderRadius: '8px',
                padding: '4px 10px', background: 'rgba(115, 92, 0, 0.06)',
                opacity: dimmed ? 0.55 : 1,
              }}>
                <span style={{ fontSize: '13px', color: 'rgba(115, 92, 0, 0.75)', fontFamily: 'Ma Shan Zheng, serif' }}>
                  {char}
                </span>
                {language === 'en' && (
                  <span style={{ fontSize: '10px', color: 'rgba(115, 92, 0, 0.6)', fontFamily: 'Noto Serif, serif', marginTop: '2px' }}>
                    {label}
                  </span>
                )}
              </div>
            );
          };

          if (hasTransformation) {
            return (
              <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '6px', marginTop: '8px', flexWrap: 'wrap', justifyContent: 'center' }}>
                <TenGodCard value={oldTenGod!} dimmed />
                <span style={{ opacity: 0.45, fontSize: '13px', color: '#4d4635' }}>→</span>
                <TenGodCard value={pillar.天干.十神} />
              </div>
            );
          }

          return (
            <div style={{
              display: 'inline-flex', flexDirection: 'column', alignItems: 'center',
              border: '1px solid rgba(115, 92, 0, 0.25)', borderRadius: '8px',
              padding: '4px 10px', background: 'rgba(115, 92, 0, 0.06)', marginTop: '8px',
            }}>
              <span style={{ fontSize: '13px', color: 'rgba(115, 92, 0, 0.75)', fontFamily: 'Ma Shan Zheng, serif' }}>
                {displayChar}
              </span>
              {language === 'en' && (
                <span style={{ fontSize: '10px', color: 'rgba(115, 92, 0, 0.6)', fontFamily: 'Noto Serif, serif', marginTop: '2px' }}>
                  {displayLabel}
                </span>
              )}
            </div>
          );
        })()}
        {pillar.天干?.根基强度 && (() => {
          const rootingMap: Record<string, { trKey: keyof typeof tr; color: string; bg: string }> = {
            '深根': { trKey: 'rootingDeep',     color: '#2d6a2d', bg: 'rgba(45, 106, 45, 0.08)'  },
            '中根': { trKey: 'rootingModerate', color: '#3d5a80', bg: 'rgba(61, 90, 128, 0.08)'  },
            '浅根': { trKey: 'rootingLight',    color: '#8a5200', bg: 'rgba(138, 82, 0, 0.08)'   },
            '无根': { trKey: 'rootingNone',     color: '#7a4040', bg: 'rgba(122, 64, 64, 0.08)'  },
          };
          const cfg = rootingMap[pillar.天干.根基强度];
          if (!cfg) return null;
          return (
            <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: '12px' }}>
              <span style={{ display: 'block', width: '60%', fontSize: '11px', color: cfg.color, fontFamily: 'Noto Serif, serif',
                             fontStyle: 'italic', textAlign: 'center', borderLeft: `3px solid ${cfg.color}`,
                             background: cfg.bg, padding: '2px 10px' }}>
                {language === 'en' ? tr[cfg.trKey][language] : pillar.天干.根基强度}
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
        {(() => {
          const branchElement = BRANCH_ELEMENT[earthlyChar];
          const ElemIcon = branchElement ? ELEMENT_ICON[branchElement] : null;
          const elemColor = branchElement ? ELEMENT_COLOR[branchElement] : '#4d4635';
          return (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
              {ElemIcon && <ElemIcon style={{ fontSize: 13, color: elemColor }} />}
              <p style={{ fontSize: '13px', color: '#4d4635', opacity: 0.75, margin: 0, fontStyle: 'italic' }}>
                {language === 'en' ? earthlyName : (ZHI_LABELS_CH[earthlyChar] ?? earthlyChar)}
              </p>
            </div>
          );
        })()}
        <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: '8px', gap: '8px' }}>
          {Array.from({ length: maxVoidCount }).map((_, i) => {
            const c = voidStatus.conditions[i];
            if (!c) return <span key={i} style={{ display: 'block', width: '66.67%', fontSize: '11px', padding: '2px 10px', visibility: 'hidden' }}>–</span>;
            const color = c.category === 'primary' ? '#8C2F2F' : c.category === 'oneway' ? '#b77306' : '#4A2080';
            const rgb   = c.category === 'primary' ? '140,47,47' : c.category === 'oneway' ? '122,79,0' : '74,32,128';
            return (
              <span key={i} style={{ display: 'block', width: '60%', fontSize: '11px', color, fontFamily: 'Noto Serif, serif',
                                     fontStyle: 'italic', textAlign: 'center', borderLeft: `3px solid ${color}`,
                                     background: `rgba(${rgb}, 0.08)`, padding: '2px 10px' }}>
                {language === 'en' ? c.label.en : c.label.ch}
              </span>
            );
          })}
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
            {hiddenStemPairs.map(({ stem, tenGod, oldTenGod }, idx: number) => {
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
                  {(() => {
                    const stemElement = STEM_ELEMENT[stem];
                    const ElemIcon = stemElement ? ELEMENT_ICON[stemElement] : null;
                    const elemColor = stemElement ? ELEMENT_COLOR[stemElement] : 'rgba(77, 70, 53, 0.6)';
                    return (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>
                        {ElemIcon && <ElemIcon style={{ fontSize: 11, color: elemColor }} />}
                        <p style={{ fontSize: '11px', color: 'rgba(77, 70, 53, 0.6)', margin: 0, lineHeight: 1.2 }}>
                          {language === 'en' ? (GAN_LABELS[stem] || stem) : (GAN_LABELS_CH[stem] || stem)}
                        </p>
                      </div>
                    );
                  })()}
                </div>
                {tenGod && (() => {
                  const hasHiddenTransformation = oldTenGod != null && oldTenGod !== '' && oldTenGod !== tenGod;
                  const HiddenTenGodCard = ({ value, dimmed }: { value: string; dimmed?: boolean }) => (
                    <div style={{
                      display: 'inline-flex', flexDirection: 'column', alignItems: 'center',
                      border: '1px solid rgba(115, 92, 0, 0.2)', borderRadius: '6px',
                      padding: '3px 8px', background: 'rgba(115, 92, 0, 0.05)',
                      opacity: dimmed ? 0.55 : 1,
                    }}>
                      <span style={{ fontSize: '13px', color: 'rgba(115, 92, 0, 0.7)', fontFamily: 'Ma Shan Zheng, serif', marginBottom: '4px' }}>
                        {value}
                      </span>
                      {language === 'en' && (
                        <span style={{ fontSize: '9px', color: 'rgba(115, 92, 0, 0.55)', fontFamily: 'Noto Serif, serif', marginTop: '1px' }}>
                          {SHI_SHEN_LABELS[value] ?? value}
                        </span>
                      )}
                    </div>
                  );
                  if (hasHiddenTransformation) {
                    return (
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', marginTop: '8px' }}>
                        <HiddenTenGodCard value={oldTenGod!} dimmed />
                        <span style={{ opacity: 0.45, fontSize: '13px', color: '#4d4635' }}>↓</span>
                        <HiddenTenGodCard value={tenGod} />
                      </div>
                    );
                  }
                  return <div style={{ marginTop: '8px' }}><HiddenTenGodCard value={tenGod} /></div>;
                })()}
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

// Ordered insight sections (matches the backend SECTION_REGISTRY) -> title translation key.
const INSIGHT_SECTIONS: { key: string; title: keyof typeof translations.profile }[] = [
  { key: 'personality', title: 'secPersonality' },
  { key: 'family', title: 'secFamily' },
  { key: 'romance', title: 'secRomance' },
  { key: 'career', title: 'secCareer' },
  { key: 'wealth', title: 'secWealth' },
];

// Narratives are plain paragraphs separated by blank lines — render each as a <p>.
const renderProse = (text: string) =>
  text
    .split(/\n{2,}/)
    .map((p) => p.trim())
    .filter(Boolean)
    .map((p, i) => (
      <p key={i} className="mb-3 text-bronze-muted/80 leading-relaxed">
        {p}
      </p>
    ));

type LabelKeyMap = Record<string, keyof typeof translations.profile>;

// Per-section group-key -> heading translation key. A section listed here renders
// as a structured object (labelled groups); everything else renders as prose.
const STRUCTURED_LABEL_KEYS: Record<string, LabelKeyMap> = {
  personality: {
    core: 'personalityCore',
    mind: 'personalityMind',
    drives: 'personalityDrives',
    strengths: 'personalityStrengths',
    weakness: 'personalityWeakness',
  },
  family: {
    roots: 'familyRoots',
    parents: 'familyParents',
    siblings: 'familySiblings',
  },
  romance: {
    partner: 'romancePartner',
    spouse: 'romanceSpouse',
    journey: 'romanceJourney',
    children: 'romanceChildren',
  },
  career: {
    path_to_success: 'careerPathToSuccess',
    highlights: 'careerHighlights',
    challenges: 'careerChallenges',
    advice: 'careerAdvice',
  },
  wealth: {
    sources: 'wealthSources',
    capacity: 'wealthCapacity',
    risks: 'wealthRisks',
    timing: 'wealthTiming',
    strategy: 'wealthStrategy',
  },
};

// Structured sections render as labelled groups of bulleted point/explanation items.
const renderStructured = (
  value: StructuredSection,
  labelKeys: LabelKeyMap,
  language: keyof typeof translations.profile.careerAdvice,
) =>
  Object.entries(value)
    .filter(([, items]) => Array.isArray(items) && items.length > 0)
    .map(([groupKey, items]) => {
      const labelKey = labelKeys[groupKey];
      return (
      <div key={groupKey} className="mb-5 last:mb-0">
        <h4 className="font-serif text-gold-deep mb-2" style={{ fontWeight: 600 }}>
          {labelKey ? translations.profile[labelKey][language] : groupKey}
        </h4>
        <ul className="list-disc pl-5 space-y-2">
          {items.map((it, i) => (
            <li key={i} className="text-bronze-muted/80 leading-relaxed">
              <span style={{ fontWeight: 600 }}>{it.point}</span>
              {it.explanation ? <> — {it.explanation}</> : null}
            </li>
          ))}
        </ul>
      </div>
      );
    });

// A section is "ready" when prose has text, or a structured object has ≥1 item.
const sectionHasContent = (value: string | StructuredSection | undefined): boolean => {
  if (typeof value === 'string') return value.trim().length > 0;
  if (value && typeof value === 'object') {
    return Object.values(value).some((items) => Array.isArray(items) && items.length > 0);
  }
  return false;
};

interface ProfilePageClientProps {
  profileRecord: ProfileRecord;
  chartData: any;
  insights?: InsightsResponse | null;
  chartKey: string;
}

export default function ProfilePageClient({ profileRecord, chartData, insights, chartKey }: ProfilePageClientProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  // Delete failure shown inline next to the delete control (success just navigates away).
  const [deleteError, setDeleteError] = useState(false);
  const [insightsData, setInsightsData] = useState<InsightsResponse | null>(insights ?? null);
  // Section keys whose LLM call is currently in flight (progressive loading).
  const [loadingSections, setLoadingSections] = useState<string[]>([]);
  // Section keys whose fetch failed — surfaced as an inline alert with Retry in the
  // Insights tab (sections that did succeed keep rendering normally).
  const [failedSections, setFailedSections] = useState<string[]>([]);
  const { language } = useLanguage();
  const tr = translations.profile;
  const trAuth = translations.auth;
  const { user, openAuthModal } = useAuth();
  const router = useRouter();
  // Ensures the auto insights generation fires at most once per mount.
  const insightsRequestedRef = useRef(false);

  const generating = loadingSections.length > 0;

  // Fetch one section and merge its prose into state; always clears its loading flag.
  // `requestId` correlates all 6 section calls of one generation across browser → Next → FastAPI.
  const fetchSection = async (idToken: string, key: string, force: boolean, requestId: string) => {
    setFailedSections((prev) => prev.filter((k) => k !== key));
    try {
      const res = await fetch('/api/insights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${idToken}` },
        body: JSON.stringify({ chartKey, section: key, force, requestId, profileId: profileRecord.profileId }),
      });
      if (res.ok) {
        const contentType = res.headers.get('content-type') ?? '';
        if (contentType.includes('text/event-stream') && res.body) {
          // Streaming path: merge each group-delta into the section as it arrives,
          // so the section's groups fill in progressively (renderStructured already
          // shows whichever groups have items).
          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';
          for (;;) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const events = buffer.split('\n\n');
            buffer = events.pop() ?? '';
            for (const evt of events) {
              const line = evt.split('\n').find((l) => l.startsWith('data:'));
              if (!line) continue;
              const payload = line.slice(5).trim();
              if (payload === '[DONE]') continue;
              let parsed: { delta?: Record<string, unknown>; error?: string };
              try { parsed = JSON.parse(payload); } catch { continue; }
              if (parsed.error) throw new Error(parsed.error);
              const delta = parsed.delta;
              if (!delta) continue;
              if (delta.__prose__ !== undefined) {
                const text = delta.__prose__ as string;
                setInsightsData((prev) => ({ sections: { ...(prev?.sections ?? {}), [key]: text } }));
              } else {
                setInsightsData((prev) => {
                  const existing = (prev?.sections?.[key] ?? {}) as StructuredSection;
                  return { sections: { ...(prev?.sections ?? {}), [key]: { ...existing, ...(delta as StructuredSection) } } };
                });
              }
            }
          }
        } else {
          // Cache hit: a single JSON response with the full section value.
          const data: InsightsResponse = await res.json();
          const value = data.sections?.[key] ?? '';
          setInsightsData((prev) => ({ sections: { ...(prev?.sections ?? {}), [key]: value } }));
        }
      } else {
        const detail = await res.text().catch(() => '');
        console.error(`Insights section '${key}' failed [req:${requestId}]:`, res.status, detail);
        reportClientError({
          context: 'insights_section', requestId, chartKey, profileId: profileRecord.profileId,
          uid: user?.uid, section: key, status: res.status, message: detail || `HTTP ${res.status}`,
        });
        setFailedSections((prev) => (prev.includes(key) ? prev : [...prev, key]));
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error(`Insights section '${key}' failed [req:${requestId}]:`, err);
      reportClientError({
        context: 'insights_section', requestId, chartKey, profileId: profileRecord.profileId,
        uid: user?.uid, section: key, message,
      });
      setFailedSections((prev) => (prev.includes(key) ? prev : [...prev, key]));
    } finally {
      setLoadingSections((prev) => prev.filter((k) => k !== key));
    }
  };

  // Progressive load: Core Personality first (renders immediately), then the
  // remaining sections in parallel. `force` (dev) bypasses the cache.
  const generateInsights = async (force = false): Promise<void> => {
    if (!user || user.isAnonymous) return; // insights require a permanent account
    const requestId = crypto.randomUUID();
    const keys = INSIGHT_SECTIONS.map((s) => s.key);
    setLoadingSections(keys);
    let idToken: string;
    try {
      idToken = await user.getIdToken();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error(`Failed to get auth token [req:${requestId}]:`, err);
      reportClientError({
        context: 'auth_token', requestId, profileId: profileRecord.profileId, uid: user?.uid, message,
      });
      setFailedSections(keys);
      setLoadingSections([]);
      return;
    }
    await fetchSection(idToken, keys[0], force, requestId); // personality first
    await Promise.all(keys.slice(1).map((k) => fetchSection(idToken, k, force, requestId)));
  };

  // Re-fetch only the failed sections (fresh token + requestId).
  const retryFailedSections = async (): Promise<void> => {
    if (!user || user.isAnonymous || failedSections.length === 0) return;
    const keys = [...failedSections];
    const requestId = crypto.randomUUID();
    setLoadingSections(keys);
    let idToken: string;
    try {
      idToken = await user.getIdToken();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error(`Failed to get auth token [req:${requestId}]:`, err);
      reportClientError({
        context: 'auth_token', requestId, profileId: profileRecord.profileId, uid: user?.uid, message,
      });
      setLoadingSections([]);
      return;
    }
    await Promise.all(keys.map((k) => fetchSection(idToken, k, false, requestId)));
  };

  // Auto-generate insights once we have a permanent (non-anonymous) owner and none are cached.
  // Covers a logged-in user landing on a freshly-created chart, and a guest who upgrades to an
  // account while viewing their chart. Ownership is already enforced server-side (SSR), and the
  // profile is owned at creation, so there is no "claim" step. Anonymous guests are gated.
  useEffect(() => {
    if (!user || user.isAnonymous) return;
    if (insightsData?.sections || insightsRequestedRef.current) return;
    insightsRequestedRef.current = true;
    void generateInsights();
  }, [user?.uid, user?.isAnonymous]); // eslint-disable-line react-hooks/exhaustive-deps

  // Reconstruct profile object for rendering
  const profile = {
    id: profileRecord.profileId,
    name: profileRecord.name,
    birthDate: new Date(profileRecord.birthData.year, profileRecord.birthData.month - 1, profileRecord.birthData.day),
    birthTime: `${String(profileRecord.birthData.hour).padStart(2, '0')}:${String(profileRecord.birthData.minute).padStart(2, '0')}`,
    birthLocation: profileRecord.birthLocation,
    gender: profileRecord.birthData.gender === 1 ? 'male' : 'female',
    usedSolarTime: profileRecord.birthData.use_solar_time_correction,
  };

  const handleDeleteProfile = async () => {
    setIsDeleting(true);
    setDeleteError(false);
    try {
      const idToken = user ? await user.getIdToken() : null;
      const res = await fetch(`/api/profiles/${profileRecord.profileId}`, {
        method: 'DELETE',
        headers: idToken ? { Authorization: `Bearer ${idToken}` } : undefined,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      // Success needs no announcement — navigating away from the deleted profile is the feedback.
      router.push('/');
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.error('Error deleting profile:', error);
      reportClientError({ context: 'profile_delete', profileId: profileRecord.profileId, uid: user?.uid, message });
      setDeleteError(true);
      setIsDeleting(false);
    }
  };


  const tianGanHuaMap: Record<string, { 元素: string; 原五行: string; label: string }> = {};
  const siZhuMeta = (chartData?.["四柱实体"] ?? {}) as Record<string, any>;
  for (const pillarName of ['年柱', '月柱', '日柱', '时柱']) {
    const pillar = siZhuMeta[pillarName];
    if (!pillar) continue;
    if (pillar.化气格信息?.现五行) {
      tianGanHuaMap[pillarName] = { 元素: pillar.化气格信息.现五行, 原五行: pillar.化气格信息.原五行, label: `天干合·${pillar.化气格信息.类型}` };
    }
  }

  const anyHeavenlyStemBadge = Object.keys(tianGanHuaMap).length > 0;


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
                    {dayjs(profile.birthDate).format('LL')}
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
            {deleteError && (
              <p className="text-xs m-0 mt-1 text-right" style={{ color: '#f1aeb5' }}>
                {tr.deleteError[language]}
              </p>
            )}
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

                    // Void condition metadata and supersession rules
                    const VOID_CONDITION_META: Record<string, { category: 'primary' | 'oneway' | 'mutual'; ch: string; en: string }> = {
                      被日柱空:    { category: 'primary', ch: '空亡',    en: 'Primary Void'           },
                      被年柱空:    { category: 'oneway',  ch: '被年空',  en: 'Void by Year'           },
                      被月柱空:    { category: 'oneway',  ch: '被月空',  en: 'Void by Month'          },
                      被时柱空:    { category: 'oneway',  ch: '被时空',  en: 'Void by Hour'           },
                      年日互换空亡: { category: 'mutual',  ch: '年日互换', en: 'Mutual Void Year↔Day'  },
                      月日互换空亡: { category: 'mutual',  ch: '月日互换', en: 'Mutual Void Month↔Day' },
                      日时互换空亡: { category: 'mutual',  ch: '日时互换', en: 'Mutual Void Day↔Hour'  },
                    };
                    const SUPERSEDED_BY: Record<string, string[]> = {
                      被日柱空: ['年日互换空亡', '月日互换空亡', '日时互换空亡'],
                      被年柱空: ['年日互换空亡'],
                      被月柱空: ['月日互换空亡'],
                      被时柱空: ['日时互换空亡'],
                    };

                    const buildVoidStatus = (pillarData: any): VoidStatus => {
                      const v = pillarData?.空亡 ?? {};
                      const activeKeys = new Set<string>();
                      for (const key of Object.keys(VOID_CONDITION_META)) {
                        const val = v[key];
                        const isActive = key === '被日柱空' ? val !== '无' : !!val;
                        if (isActive) activeKeys.add(key);
                      }
                      const conditions: VoidCondition[] = [...activeKeys]
                        .filter(key => !(SUPERSEDED_BY[key] ?? []).some(s => activeKeys.has(s)))
                        .map(key => {
                          const meta = VOID_CONDITION_META[key];
                          return { category: meta.category, label: { ch: meta.ch, en: meta.en } };
                        });
                      return { conditions };
                    };

                    const yearVS  = buildVoidStatus(siZhu.年柱);
                    const monthVS = buildVoidStatus(siZhu.月柱);
                    const dayVS   = buildVoidStatus(siZhu.日柱);
                    const hourVS  = buildVoidStatus(siZhu.时柱);
                    const maxVoidCount = Math.max(yearVS.conditions.length, monthVS.conditions.length, dayVS.conditions.length, hourVS.conditions.length);

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
                      // lifeStageData is { 日干: "养", 自坐: "衰" }
                      return {
                        xingYun: { chinese: lifeStageData.日干, english: '' },
                        ziZuo: { chinese: lifeStageData.自坐, english: '' }
                      };
                    };
                    const buildNaYin = (naYinValue: any) => naYinValue ? { chinese: naYinValue, english: '', element: extractElementFromNaYin(naYinValue) } : null;
                    const buildXunKong = (voidValue: any) => voidValue && voidValue !== '无' ? { chinese: voidValue, english: '' } : null;

                    const pillarShenSha = chartData?.神煞 ?? {};

                    return (
                      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4" style={{ position: 'relative', paddingTop: '20px', minWidth: 0 }}>
                        <PillarCard pillarLabel={tr.yearPillar[language]} language={language} anyHeavenlyStemBadge={anyHeavenlyStemBadge}  pillar={siZhu.年柱}  isDayMaster={false} lifeStages={buildLifeStage(siZhu.年柱?.十二长生)}  naYin={buildNaYin(siZhu.年柱?.纳音)}  xunKong={buildXunKong(siZhu.年柱?.空亡?.本柱旬空)}  voidStatus={yearVS}  maxVoidCount={maxVoidCount} shenSha={pillarShenSha.年柱} tianGanHua={tianGanHuaMap['年柱']} />
                        <PillarCard pillarLabel={tr.monthPillar[language]} language={language} anyHeavenlyStemBadge={anyHeavenlyStemBadge} pillar={siZhu.月柱} isDayMaster={false} lifeStages={buildLifeStage(siZhu.月柱?.十二长生)} naYin={buildNaYin(siZhu.月柱?.纳音)} xunKong={buildXunKong(siZhu.月柱?.空亡?.本柱旬空)} voidStatus={monthVS} maxVoidCount={maxVoidCount} shenSha={pillarShenSha.月柱} tianGanHua={tianGanHuaMap['月柱']} />
                        <PillarCard pillarLabel={tr.dayPillar[language]} language={language} anyHeavenlyStemBadge={anyHeavenlyStemBadge}   pillar={siZhu.日柱}   isDayMaster={true}  lifeStages={buildLifeStage(siZhu.日柱?.十二长生)}   naYin={buildNaYin(siZhu.日柱?.纳音)}   xunKong={buildXunKong(siZhu.日柱?.空亡?.本柱旬空)}   voidStatus={dayVS}   maxVoidCount={maxVoidCount} shenSha={pillarShenSha.日柱} tianGanHua={tianGanHuaMap['日柱']} />
                        <PillarCard pillarLabel={tr.hourPillar[language]} language={language} anyHeavenlyStemBadge={anyHeavenlyStemBadge}  pillar={siZhu.时柱}  isDayMaster={false} lifeStages={buildLifeStage(siZhu.时柱?.十二长生)}  naYin={buildNaYin(siZhu.时柱?.纳音)}  xunKong={buildXunKong(siZhu.时柱?.空亡?.本柱旬空)}  voidStatus={hourVS}  maxVoidCount={maxVoidCount} shenSha={pillarShenSha.时柱} tianGanHua={tianGanHuaMap['时柱']} />
                      </div>
                    );
                  })()}
                  <FiveElementsCard chartData={chartData} language={language} />
                  <PillarInteractionsCard chartData={chartData} language={language} />
                  <DayMasterStrengthCard chartData={chartData} language={language} />
                  <FavorableElementsCard chartData={chartData} language={language} />
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
                  {/* Sections that failed to generate — inline alert with retry; sections
                      that did succeed keep rendering below. */}
                  {failedSections.length > 0 && !generating && (
                    <Alert
                      type="error"
                      showIcon
                      message={tr.errorInsights[language]}
                      action={
                        <Button size="small" danger onClick={() => void retryFailedSections()}>
                          {tr.retryInsights[language]}
                        </Button>
                      }
                    />
                  )}
                  {process.env.NODE_ENV !== 'production' && user && !user.isAnonymous && (
                    /* Dev-only: force-regenerate (bypass cache) to iterate on prompt/data edits */
                    <div className="flex justify-end">
                      <button
                        onClick={() => generateInsights(true)}
                        disabled={generating}
                        style={{
                          padding: '4px 12px',
                          border: '1px dashed rgba(115,92,0,0.4)',
                          borderRadius: '6px',
                          fontSize: '12px',
                          color: '#735c00',
                          background: 'transparent',
                          cursor: generating ? 'default' : 'pointer',
                          opacity: generating ? 0.5 : 1,
                        }}
                      >
                        ↻ Regenerate (dev)
                      </button>
                    </div>
                  )}
                  {(!user || user.isAnonymous) ? (
                    /* Guest gate card — anonymous users must create an account to unlock insights */
                    <Card style={{ borderColor: 'rgba(115, 92, 0, 0.15)', background: 'rgba(251,249,244,0.8)' }}>
                      <div className="flex flex-col items-center gap-4 py-4">
                        {/* Blurred placeholder rows */}
                        <div style={{ width: '100%', filter: 'blur(4px)', pointerEvents: 'none', opacity: 0.4 }}>
                          {[80, 60, 90, 70, 55].map((w, i) => (
                            <div key={i} style={{
                              height: '12px', borderRadius: '6px', marginBottom: '10px',
                              background: 'linear-gradient(90deg, rgba(115,92,0,0.25), rgba(115,92,0,0.1))',
                              width: `${w}%`,
                            }} />
                          ))}
                        </div>
                        <div style={{ width: '40px', height: '1px', background: 'rgba(115,92,0,0.2)' }} />
                        <p className="font-serif text-center text-bronze-muted" style={{ fontSize: '15px', fontWeight: 600 }}>
                          {trAuth.unlockInsights[language]}
                        </p>
                        <button
                          onClick={() => openAuthModal({ reason: 'insights' })}
                          style={{
                            padding: '10px 24px',
                            backgroundColor: '#3d3a5c', color: '#fff',
                            border: 'none', borderRadius: '8px',
                            fontSize: '13px', fontWeight: 600,
                            fontFamily: 'Noto Serif, serif', cursor: 'pointer',
                          }}
                        >
                          {trAuth.createFreeAccount[language]}
                        </button>
                      </div>
                    </Card>
                  ) : generating && !sectionHasContent(insightsData?.sections?.personality) ? (
                    /* Personality not ready yet — themed full loader */
                    <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
                      <InsightsLoading language={language} />
                    </Card>
                  ) : (insightsData?.sections && Object.values(insightsData.sections).some(sectionHasContent)) || generating ? (
                    (() => {
                      const sections = insightsData?.sections ?? {};
                      // Show a panel for each section that is ready OR still loading.
                      const panels = INSIGHT_SECTIONS.filter(
                        (s) => sectionHasContent(sections[s.key]) || loadingSections.includes(s.key),
                      );
                      const firstKey = panels[0]?.key;
                      return (
                        <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
                          <Collapse
                            accordion
                            defaultActiveKey={firstKey ? [firstKey] : []}
                            items={panels.map((s) => ({
                              key: s.key,
                              label: (
                                <span className="font-serif text-gold-deep" style={{ fontWeight: 600 }}>
                                  {tr[s.title][language]}
                                </span>
                              ),
                              children: sectionHasContent(sections[s.key]) ? (
                                <div>
                                  {typeof sections[s.key] === 'string'
                                    ? renderProse(sections[s.key] as string)
                                    : renderStructured(
                                        sections[s.key] as StructuredSection,
                                        STRUCTURED_LABEL_KEYS[s.key] ?? {},
                                        language,
                                      )}
                                </div>
                              ) : (
                                <InsightsLoading language={language} compact />
                              ),
                            }))}
                          />
                        </Card>
                      );
                    })()
                  ) : (
                    /* Logged in but no insights yet — manual trigger */
                    <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
                      <div className="flex flex-col items-center gap-3 py-2">
                        <button
                          onClick={() => generateInsights()}
                          style={{
                            padding: '10px 24px',
                            backgroundColor: '#3d3a5c', color: '#fff',
                            border: 'none', borderRadius: '8px',
                            fontSize: '13px', fontWeight: 600,
                            fontFamily: 'Noto Serif, serif', cursor: 'pointer',
                          }}
                        >
                          {trAuth.generateInsights[language]}
                        </button>
                      </div>
                    </Card>
                  )}
                </div>
              ),
            },
          ]}
        />
      </div>
    </div>
  );
}
