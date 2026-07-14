'use client';

import React, { useEffect, useState } from 'react';
import { Card } from 'antd';
import { ELEMENT_ICONS } from '@/lib/elements';
import { translations } from '@/lib/translations';

interface PillarInteractionsCardProps {
  chartData: any;
  language: 'en' | 'ch';
}

const PILLAR_ORDER = ['年柱', '月柱', '日柱', '时柱'] as const;
const PILLAR_INDEX: Record<string, number> = { '年柱': 0, '月柱': 1, '日柱': 2, '时柱': 3 };
const HIDDEN_STRENGTHS = new Set<string>();

// Ten Gods translation mapping
const SHI_SHEN_LABELS: Record<string, string> = {
  '比肩': 'Companion', '劫财': 'Wealth Robber', '食神': 'Food God',
  '伤官': 'Hurting Officer', '偏财': 'Indirect Wealth', '正财': 'Direct Wealth',
  '七杀': 'Seven Killings', '偏官': 'Indirect Officer', '正官': 'Direct Officer', '偏印': 'Indirect Resource',
  '正印': 'Direct Resource', '我': 'Self',
};

type Category = 'he' | 'chong' | 'ke' | 'xing' | 'hai' | 'po' | 'yin' | 'xu' | 'other';

const CATEGORY_MAP: Record<string, Category> = {
  '六合': 'he', '三合': 'he', '半合': 'he', '天干合': 'he',
  '三会': 'he', '残会': 'he',
  '比和': 'he', '暗合': 'he', '干支透合': 'he',
  '六冲': 'chong', '天干冲': 'chong', '天克地冲': 'chong',
  '天干克': 'ke',
  '无恩之刑': 'xing', '恃势之刑': 'xing', '无礼之刑': 'xing', '自刑': 'xing',
  '六害': 'hai',
  '六破': 'po',
  '伏吟': 'yin',
  '拱合': 'xu', '拱会': 'xu',
};

const CATEGORY_STYLES: Record<Category, { bg: string; border: string; accent: string; text: string; label: { en: string; ch: string } }> = {
  he:    { bg: 'rgba(34, 120, 60, 0.07)',   border: 'rgba(34, 120, 60, 0.28)',   accent: '#1e7a3a', text: '#1a5c28', label: { en: 'Harmony', ch: '合' } },
  chong: { bg: 'rgba(185, 38, 38, 0.07)',   border: 'rgba(185, 38, 38, 0.28)',   accent: '#b42424', text: '#8b1e1e', label: { en: 'Clash',   ch: '冲' } },
  ke:    { bg: 'rgba(195, 100, 0, 0.07)',   border: 'rgba(195, 100, 0, 0.28)',   accent: '#c46000', text: '#8b4600', label: { en: 'Control', ch: '克' } },
  xing:  { bg: 'rgba(175, 95, 0, 0.07)',    border: 'rgba(175, 95, 0, 0.28)',    accent: '#af5f00', text: '#7a4000', label: { en: 'Punishment', ch: '刑' } },
  hai:   { bg: 'rgba(185, 38, 38, 0.07)',   border: 'rgba(185, 38, 38, 0.28)',   accent: '#b42424', text: '#8b1e1e', label: { en: 'Harm',    ch: '害' } },
  po:    { bg: 'rgba(195, 100, 0, 0.07)',   border: 'rgba(195, 100, 0, 0.28)',   accent: '#c46000', text: '#8b4600', label: { en: 'Break',   ch: '破' } },
  yin:   { bg: 'rgba(90, 60, 120, 0.06)',   border: 'rgba(90, 60, 120, 0.22)',   accent: '#5a3c78', text: '#3d2856', label: { en: 'Duplicate', ch: '吟' } },
  xu:    { bg: 'rgba(80, 80, 120, 0.06)',   border: 'rgba(80, 80, 120, 0.22)',   accent: '#505090', text: '#383870', label: { en: 'Virtual', ch: '拱' } },
  other: { bg: 'rgba(115, 92, 0, 0.06)',   border: 'rgba(115, 92, 0, 0.2)',     accent: '#735c00', text: '#4d4635', label: { en: 'Other',   ch: '其他' } },
};

const STRENGTH_LABEL: Record<string, { en: string; ch: string; opacity: number }> = {
  '强势主流': { en: 'Dominant',       ch: '强势主流', opacity: 1.0  },
  '显著影响': { en: 'Strong',         ch: '显著影响', opacity: 0.8  },
  '中等衰减': { en: 'Moderate',       ch: '中等衰减', opacity: 0.65 },
  '大幅衰减': { en: 'Weak',           ch: '大幅衰减', opacity: 0.5  },
  '消融吸收': { en: 'Fully Absorbed', ch: '消融吸收', opacity: 0.4  },
};

const VAULT_LABEL_EN: Record<string, string> = {
  '金库': 'Metal Vault', '水库': 'Water Vault',
  '木库': 'Wood Vault',  '火库': 'Fire Vault',
};
const SEASONAL_STATE_EN: Record<string, string> = {
  '旺': 'Dominant', '相': 'Prosperous', '休': 'Resting', '囚': 'Imprisoned', '死': 'Dead',
};
const ELEMENT_ACCENT: Record<string, string> = {
  '木': '#2e7d32', '火': '#c62828', '土': '#8d6e28', '金': '#546e7a', '水': '#1565c0',
};
const VAULT_OPEN_STYLE   = { bg: 'rgba(184,134,11,0.06)', border: 'rgba(184,134,11,0.22)', accent: '#b8860b', text: '#7a5800' };
const VAULT_SEALED_STYLE = { bg: 'rgba(115,105,90,0.06)', border: 'rgba(115,105,90,0.2)',  accent: '#8b8070', text: '#5c5445' };



function getPillarChar(ix: any, pillarIndex: number): string {
  const detail = ix.组合明细 ?? {};
  const pillarName = PILLAR_ORDER[pillarIndex];
  if (!pillarName) return '';
  return (detail[pillarName] as string) ?? '';
}

const MOBILE_BREAKPOINT = 640;

export default function PillarInteractionsCard({ chartData, language }: PillarInteractionsCardProps) {
  const tr = translations.profile;
  const pillarDynamic = (chartData?.作用?.柱位动态 ?? []) as any[];

  const [isMobile, setIsMobile] = useState(
    typeof window !== 'undefined' && window.innerWidth < MOBILE_BREAKPOINT
  );
  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, []);

  const vaultItems = (chartData?.作用?.库位状态 ?? []) as any[];

  const entries = pillarDynamic
    .filter(item => !HIDDEN_STRENGTHS.has(item.强度))
    .map(item => {
      const pillars = Object.keys(item.组合明细 ?? {})
        .map((p: string) => PILLAR_INDEX[p])
        .filter((i): i is number => i !== undefined)
        .sort((a, b) => a - b);
      return { interaction: item, pillars };
    })
    .sort((a, b) => {
      const spanA = (a.pillars[a.pillars.length - 1] ?? 0) - (a.pillars[0] ?? 0);
      const spanB = (b.pillars[b.pillars.length - 1] ?? 0) - (b.pillars[0] ?? 0);
      if (a.pillars[0] !== b.pillars[0]) return (a.pillars[0] ?? 0) - (b.pillars[0] ?? 0);
      return spanA - spanB;
    });

  const pillarDisplayLabels: Record<string, string> = language === 'ch'
    ? { '年柱': '年柱', '月柱': '月柱', '日柱': '日柱', '时柱': '时柱' }
    : { '年柱': 'Year', '月柱': 'Month', '日柱': 'Day', '时柱': 'Hour' };

  const CATEGORY_ORDER: Category[] = ['he', 'chong', 'ke', 'xing', 'hai', 'po', 'yin', 'other', 'xu'];
  const presentCategories = [...new Set(entries.map(e => CATEGORY_MAP[e.interaction.类型] ?? 'other'))]
    .sort((a, b) => CATEGORY_ORDER.indexOf(a) - CATEGORY_ORDER.indexOf(b));

  const renderRow = ({ interaction: ix, pillars }: typeof entries[number], rowKey: string) => {
    const cat = CATEGORY_MAP[ix.类型] ?? 'other';
    const catStyle = CATEGORY_STYLES[cat];
    const leftPi = pillars[0]!;
    const rightPi = pillars[pillars.length - 1]!;
    const leftCenterPct = (leftPi + 0.5) * 25;
    const rightCenterPct = (rightPi + 0.5) * 25;
    const midPct = (leftCenterPct + rightCenterPct) / 2;

    // Compute gap midpoints between consecutive pillars
    const gapMidpoints = pillars.slice(0, -1).map((pi, idx) => {
      const l = (pi + 0.5) * 25;
      const r = (pillars[idx + 1]! + 0.5) * 25;
      return (l + r) / 2;
    });

    const rowOpacity = ix.强度 === '消融吸收' ? 0.6 : 1;

    return (
        <div key={rowKey} style={{ position: 'relative', height: '60px', width: '100%', cursor: 'default', opacity: rowOpacity }}>
          {pillars.map(pi => {
            const centerPct = (pi + 0.5) * 25;
            const char = getPillarChar(ix, pi);
            return (
              <div key={pi} style={{
                position: 'absolute', left: `${centerPct}%`, transform: 'translateX(-50%)',
                top: 0, height: '36px', display: 'flex', flexDirection: 'column', alignItems: 'center',
              }}>
                <span style={{ fontFamily: '"Ma Shan Zheng", cursive', fontSize: '16px', color: catStyle.text, lineHeight: 1.1, whiteSpace: 'nowrap' }}>
                  {char || ' '}
                </span>
                <div style={{ width: 0, height: 0, borderLeft: '3.5px solid transparent', borderRight: '3.5px solid transparent', borderTop: `4px solid ${catStyle.accent}`, margin: '2px 0', flexShrink: 0 }} />
                <div style={{ width: '1.5px', background: catStyle.accent, flex: 1, marginBottom: '-2px' }} />
              </div>
            );
          })}
          <div style={{ position: 'absolute', left: `${leftCenterPct}%`, width: `${rightCenterPct - leftCenterPct}%`, top: '36px', height: '2px', background: catStyle.accent }} />
          {/* Element display (above the line) */}
          {(() => {
            let elementChar = '';
            let tenGodChar = '';

            if (ix.类型 === '干支透合') {
              elementChar = ix.藏干详情?.['合化五行'] ?? '';
              tenGodChar = ix.藏干详情?.['藏干十神'] ?? '';
            } else {
              elementChar = ix.元素 ?? '';
            }

            if (!elementChar) return null;
            const pillOutsideRight = isMobile && (100 - rightCenterPct) >= leftCenterPct;
            return (
              <>
                {gapMidpoints.map((gapPct, gi) => (
                  <div key={gi} style={{ position: 'absolute', left: `${gapPct}%`, transform: 'translateX(-50%)', top: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    {React.createElement(ELEMENT_ICONS[elementChar], {
                      sx: { fontSize: '14px', color: catStyle.accent }
                    })}
                    <span style={{ fontFamily: '"Noto Sans SC", sans-serif', fontSize: '12px', fontWeight: 500, color: catStyle.text, whiteSpace: 'nowrap' }}>
                      {elementChar}
                    </span>
                    {tenGodChar && !isMobile && (
                      <div style={{
                        display: 'inline-flex', flexDirection: 'row', alignItems: 'center', gap: '4px',
                        border: '1px solid rgba(115, 92, 0, 0.25)', borderRadius: '6px', padding: '2px 6px',
                        background: 'rgba(115, 92, 0, 0.06)', marginLeft: '4px',
                      }}>
                        <span style={{ fontSize: '13px', color: 'rgba(115, 92, 0, 0.75)', fontFamily: '"Ma Shan Zheng", serif', lineHeight: 1, whiteSpace: 'nowrap' }}>
                          {tenGodChar}
                        </span>
                        {language === 'en' && (
                          <span style={{ fontSize: '10px', color: 'rgba(115, 92, 0, 0.6)', fontFamily: '"Noto Serif", serif', lineHeight: 1, whiteSpace: 'nowrap' }}>
                            {SHI_SHEN_LABELS[tenGodChar] || tenGodChar}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
                {tenGodChar && isMobile && (
                  <div style={{
                    position: 'absolute',
                    top: '10px',
                    ...(pillOutsideRight
                      ? { left: `calc(${rightCenterPct}% + 8px)` }
                      : { left: `calc(${leftCenterPct}% - 8px)`, transform: 'translateX(-100%)' }
                    ),
                    display: 'inline-flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '1px',
                    border: '1px solid rgba(115, 92, 0, 0.25)',
                    borderRadius: '6px',
                    padding: '2px 6px',
                    background: 'rgba(115, 92, 0, 0.06)',
                  }}>
                    <span style={{ fontSize: '13px', color: 'rgba(115, 92, 0, 0.75)', fontFamily: '"Ma Shan Zheng", serif', lineHeight: 1, whiteSpace: 'nowrap' }}>
                      {tenGodChar}
                    </span>
                    {language === 'en' && (
                      <span style={{ fontSize: '10px', color: 'rgba(115, 92, 0, 0.6)', fontFamily: '"Noto Serif", serif', lineHeight: 1, whiteSpace: 'nowrap' }}>
                        {SHI_SHEN_LABELS[tenGodChar] || tenGodChar}
                      </span>
                    )}
                  </div>
                )}
              </>
            );
          })()}
          <div style={{ position: 'absolute', left: `${midPct}%`, transform: 'translateX(-50%)', top: '46px', display: 'flex', alignItems: 'center', gap: '3px', whiteSpace: 'nowrap' }}>
            <span style={{ fontFamily: '"Noto Sans SC", sans-serif', fontSize: '12px', fontWeight: 500, color: catStyle.text }}>
              {ix.类型}
            </span>
            {ix.形态 && (
              <>
                <span style={{ fontSize: '12px', color: catStyle.accent, opacity: 0.75, margin: '0 1px' }}>·</span>
                <span style={{ fontFamily: '"Noto Sans SC", sans-serif', fontSize: '11px', fontStyle: 'italic', color: catStyle.accent, opacity: 0.75 }}>
                  {ix.形态}
                </span>
              </>
            )}
            <span style={{ fontFamily: 'Noto Serif, serif', fontSize: '10px', color: catStyle.accent, background: `${catStyle.accent}18`, border: `1px solid ${catStyle.accent}40`, borderRadius: '3px', padding: '1px 4px', marginLeft: '5px', opacity: ix.强度 !== '消融吸收' ? (STRENGTH_LABEL[ix.强度]?.opacity ?? 1) : 1 }}>
              {STRENGTH_LABEL[ix.强度]?.[language] ?? ix.强度}
            </span>
          </div>
        </div>
    );
  };

  const renderVaultCard = (item: any, key: string) => {
    const isOpen     = item.是否开库 as boolean;
    const vs         = isOpen ? VAULT_OPEN_STYLE : VAULT_SEALED_STYLE;
    const elemAccent = isOpen ? (ELEMENT_ACCENT[item.元素] ?? vs.accent) : vs.accent;
    const labelEn    = VAULT_LABEL_EN[item.标签] ?? item.标签;
    const colIndex   = PILLAR_INDEX[item.库柱] ?? 0;
    const ElemIcon   = ELEMENT_ICONS[item.元素];
    const mechanisms: string[] = item.开库机制 ?? [];

    return (
      <div key={key} style={{
        gridColumn: colIndex + 1,
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        gap: '4px', padding: '8px 6px 0 5px', borderRadius: '7px', textAlign: 'center',
        background: vs.bg,
        border: `1px solid ${vs.border}`,
        borderLeft: `1px solid ${vs.border}`,
        overflow: 'hidden',
      }}>
        {/* Element icon + vault label */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {ElemIcon && React.createElement(ElemIcon, { sx: { fontSize: '15px', color: elemAccent } })}
          <span style={{ fontFamily: language === 'en' ? '"Noto Sans SC", sans-serif' : '"Ma Shan Zheng", cursive', fontSize: language === 'en' ? '12px' : '14px', fontWeight: language === 'en' ? 500 : undefined, color: vs.text, lineHeight: 1.1 }}>
            {language === 'en' ? labelEn : item.标签}
          </span>
        </div>
        {/* Mechanisms */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '3px', flexWrap: 'wrap', justifyContent: 'center' }}>
          {mechanisms.length > 0 ? mechanisms.map((m, i) => (
            <span key={i} style={{ fontFamily: '"Noto Sans SC", sans-serif', fontSize: '11px', fontStyle: 'italic', color: vs.accent, opacity: 0.85 }}>
              {i > 0 && <span style={{ margin: '0 2px', opacity: 0.5 }}>·</span>}{m}
            </span>
          )) : (
            <span style={{ fontSize: '11px', color: vs.accent, opacity: 0.25 }}>—</span>
          )}
        </div>
        {/* Released stem + seasonal state */}
        <div style={{ fontFamily: '"Noto Sans SC", sans-serif', fontSize: '11px', color: vs.accent, opacity: 0.75 }}>
          {language === 'en'
            ? `${item.释放} · ${SEASONAL_STATE_EN[item.季节状态] ?? item.季节状态}`
            : `释放${item.释放} · 库气${item.季节状态}`}
        </div>
        {/* Ten God badge */}
        {item.释放十神 && (
          <div style={{
            display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: '4px',
            border: `1px solid ${vs.border}`, borderRadius: '6px', padding: '6px 6px',
            background: vs.bg,
          }}>
            <span style={{ fontSize: '13px', color: vs.text, fontFamily: '"Ma Shan Zheng", serif', lineHeight: 1, whiteSpace: 'nowrap' }}>
              {item.释放十神}
            </span>
            {language === 'en' && (
              <span style={{ fontSize: '10px', color: vs.accent, fontFamily: '"Noto Serif", serif', lineHeight: 1, whiteSpace: 'nowrap' }}>
                {SHI_SHEN_LABELS[item.释放十神] || item.释放十神}
              </span>
            )}
          </div>
        )}
        {/* Open / Sealed footer strip */}
        <div style={{
          alignSelf: 'stretch',
          marginLeft: '-5px', marginRight: '-6px', marginTop: '4px',
          padding: '4px 6px',
          background: isOpen ? '#1e7a3a18' : `${vs.accent}12`,
          borderTop: `1px solid ${isOpen ? '#1e7a3a40' : vs.border}`,
          textAlign: 'center',
        }}>
          <span style={{ fontFamily: 'Noto Serif, serif', fontSize: '10px', color: isOpen ? '#1e7a3a' : vs.accent }}>
            {isOpen ? (language === 'en' ? 'Open' : '开泄') : (language === 'en' ? 'Sealed' : '封藏')}
          </span>
        </div>
      </div>
    );
  };

  const DIVIDER_STRENGTHS = new Set(['中等衰减', '大幅衰减', '消融吸收']);
  const topEntries = entries.filter(e => !DIVIDER_STRENGTHS.has(e.interaction.强度));
  const moderateEntries = entries.filter(e => e.interaction.强度 === '中等衰减');
  const weakEntries = entries.filter(e => e.interaction.强度 === '大幅衰减');
  const absorbedEntries = entries.filter(e => e.interaction.强度 === '消融吸收');

  const renderDivider = (strengthKey: string) => (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '2px 0' }}>
      <div style={{ flex: 1, height: '1px', background: 'rgba(115,92,0,0.15)' }} />
      <span style={{ fontFamily: 'Noto Serif, serif', fontSize: '10px', color: 'rgba(115,92,0,0.4)', whiteSpace: 'nowrap' }}>
        {STRENGTH_LABEL[strengthKey]?.[language] ?? strengthKey}
      </span>
      <div style={{ flex: 1, height: '1px', background: 'rgba(115,92,0,0.15)' }} />
    </div>
  );

  return (
    <div style={{ marginTop: '16px' }}>
      <Card
        style={{ border: '1px solid rgba(115,92,0,0.15)', borderRadius: '12px', background: '#faf8f2' }}
        styles={{ body: { padding: '20px 20px 16px' } }}
      >
        {/* Title */}
        <h3 style={{
          fontFamily: 'Noto Serif, serif',
          fontSize: '13px',
          fontWeight: 600,
          color: 'rgba(115,92,0,0.6)',
          margin: '0 0 16px 0',
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
        }}>
          {tr.pillarInteractions[language]}
        </h3>

        {/* Pillar column headers */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: '10px' }}>
          {PILLAR_ORDER.map((pillarKey, pi) => {
            const pillarData = chartData?.四柱实体?.[pillarKey];
            const isLast = pi === 3;
            return (
              <div
                key={pillarKey}
                style={{
                  textAlign: 'center',
                  borderRight: isLast ? 'none' : '1px dashed rgba(115,92,0,0.12)',
                  padding: '0 4px 8px',
                }}
              >
                <div style={{
                  fontSize: '10px',
                  color: 'rgba(115,92,0,0.4)',
                  fontFamily: 'Noto Serif, serif',
                  letterSpacing: '0.06em',
                  marginBottom: '3px',
                  textTransform: 'uppercase',
                }}>
                  {pillarDisplayLabels[pillarKey]}
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '2px' }}>
                  <span style={{ fontFamily: '"Ma Shan Zheng", cursive', fontSize: '20px', color: '#4d4635', lineHeight: 1 }}>
                    {pillarData?.天干?.天干 ?? '—'}
                  </span>
                  <span style={{ fontFamily: '"Ma Shan Zheng", cursive', fontSize: '20px', color: '#4d4635', lineHeight: 1 }}>
                    {pillarData?.地支?.地支 ?? '—'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Interaction bars */}
        {entries.length === 0 && vaultItems.length === 0 ? (
          <p style={{ textAlign: 'center', color: 'rgba(115,92,0,0.35)', fontFamily: 'Noto Serif, serif', fontSize: '12px', margin: '8px 0' }}>
            {tr.noInteractions[language]}
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {topEntries.map((e, i) => renderRow(e, `top-${i}`))}
            {moderateEntries.length > 0 && (
              <>
                {renderDivider('中等衰减')}
                {moderateEntries.map((e, i) => renderRow(e, `moderate-${i}`))}
              </>
            )}
            {weakEntries.length > 0 && (
              <>
                {renderDivider('大幅衰减')}
                {weakEntries.map((e, i) => renderRow(e, `weak-${i}`))}
              </>
            )}
            {absorbedEntries.length > 0 && (
              <>
                {renderDivider('消融吸收')}
                {absorbedEntries.map((e, i) => renderRow(e, `absorbed-${i}`))}
              </>
            )}
            {vaultItems.length > 0 && (
              <>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '2px 0' }}>
                  <div style={{ flex: 1, height: '1px', background: 'rgba(115,92,0,0.15)' }} />
                  <span style={{ fontFamily: 'Noto Serif, serif', fontSize: '10px', color: 'rgba(115,92,0,0.4)', whiteSpace: 'nowrap' }}>
                    {language === 'en' ? 'Vault Dynamics' : '库藏动态'}
                  </span>
                  <div style={{ flex: 1, height: '1px', background: 'rgba(115,92,0,0.15)' }} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
                  {vaultItems.map((item, i) => renderVaultCard(item, `vault-${i}`))}
                </div>
              </>
            )}
          </div>
        )}

        {/* Legend */}
        {presentCategories.length > 0 && (
          <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid rgba(115,92,0,0.1)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
              <span style={{ fontSize: '13px', color: 'rgba(115,92,0,1)', fontFamily: 'Noto Serif, serif', flexShrink: 0 }}>
                {language === 'ch' ? '强度：' : 'Strength:'}
              </span>
              {Object.entries(STRENGTH_LABEL).map(([, s]) => (
                <span
                  key={s.en}
                  style={{
                    fontSize: '12px',
                    fontFamily: 'Noto Serif, serif',
                    color: 'rgba(115,92,0,0.8)',
                    background: 'rgba(115,92,0,0.08)',
                    border: '1px solid rgba(115,92,0,0.2)',
                    borderRadius: '3px',
                    padding: '1px 5px',
                    opacity: s.opacity,
                  }}
                >
                  {s[language]}
                </span>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
              {presentCategories.map(cat => {
                const s = CATEGORY_STYLES[cat];
                return (
                  <div key={cat} style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <div style={{ width: '12px', height: '3px', background: s.accent, borderRadius: '4px' }} />
                    <span style={{ fontSize: '13px', color: 'rgba(115,92,0,1)', fontFamily: 'Noto Serif, serif' }}>
                      {s.label[language]}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
