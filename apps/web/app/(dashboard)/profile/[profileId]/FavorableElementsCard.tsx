'use client';

import { useState, useEffect } from 'react';
import { Card } from 'antd';
import { ELEMENT_ICONS, ELEMENT_EN, ELEMENT_COLOR } from '@/lib/elements';
import { palette, strengthScale } from '@/lib/theme';
import { BaziChartData } from '@/types/baziChart';
import { YongShen } from '@/types/cyclesChart';
import { translations } from '@/lib/translations';

const MOBILE_BREAKPOINT = 720;

interface FavorableElementsCardProps {
  chartData: BaziChartData;
  language: 'en' | 'ch';
}

const FAVORABLE_COLOR = strengthScale.strong;
const UNFAVORABLE_COLOR = strengthScale.veryWeak;
const CLIMATE_COLOR = palette.infoBlue;

// 强弱 → plain-language reason (正格 only; special structures use the banner instead).
const REASON_KEY: Record<string, 'reasonStrong' | 'reasonWeak' | 'reasonBalanced'> = {
  '极旺': 'reasonStrong',
  '旺': 'reasonStrong',
  '中和': 'reasonBalanced',
  '弱': 'reasonWeak',
  '极弱': 'reasonWeak',
};

// 格局 → banner explanation (非正格 only).
const STRUCT_KEY: Record<string, 'structCong' | 'structZhuanWang' | 'structHuaQi'> = {
  '从财格': 'structCong',
  '从杀格': 'structCong',
  '从儿格': 'structCong',
  '从势格': 'structCong',
  '专旺格': 'structZhuanWang',
  '化气格': 'structHuaQi',
};

function ElementChip({
  element,
  accent,
  language,
  isMobile,
}: {
  element: string;
  accent: string;
  language: 'en' | 'ch';
  isMobile: boolean;
}) {
  const Icon = ELEMENT_ICONS[element];
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: isMobile ? '6px 10px' : '8px 14px',
        borderRadius: 20,
        background: `${accent}14`,
        border: `1px solid ${accent}55`,
      }}
    >
      {Icon && <Icon style={{ fontSize: 18, color: ELEMENT_COLOR[element] }} />}
      <span
        style={{
          fontFamily: '"Ma Shan Zheng", serif',
          fontSize: isMobile ? 18 : 22,
          fontWeight: 700,
          color: '#4d4635',
          lineHeight: 1,
        }}
      >
        {element}
      </span>
      {language === 'en' && (
        <span
          style={{
            fontFamily: '"Noto Serif", serif',
            fontSize: 12,
            color: 'rgba(115,92,0,0.6)',
            letterSpacing: '0.03em',
          }}
        >
          {ELEMENT_EN[element]}
        </span>
      )}
    </div>
  );
}

function GroupLabel({ text, accent }: { text: string; accent: string }) {
  return (
    <div
      style={{
        fontFamily: '"Noto Serif", serif',
        fontSize: 12,
        fontWeight: 600,
        color: accent,
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
        marginBottom: 8,
      }}
    >
      {text}
    </div>
  );
}

export default function FavorableElementsCard({ chartData, language }: FavorableElementsCardProps) {
  const tr = translations.profile;
  const yongShen = chartData['用神'] as YongShen | undefined;

  const [isMobile, setIsMobile] = useState(
    typeof window !== 'undefined' && window.innerWidth < MOBILE_BREAKPOINT
  );
  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, []);

  // Old cached charts predate the 用神 field — omit the card silently (sibling convention).
  if (!yongShen) return null;

  const isZhengGe = yongShen.格局 === '正格';
  const favorable = yongShen.喜用 ?? [];
  const unfavorable = yongShen.忌 ?? [];
  // 调候 fields are context-only when 调候适用 is false (从/专旺/化气) — never shown as advice.
  const climateElements = yongShen.调候适用 ? (yongShen.调候喜五行 ?? []) : [];

  const structKey = STRUCT_KEY[yongShen.格局];
  const reasonKey = REASON_KEY[yongShen.强弱];

  return (
    <div style={{ marginTop: '16px' }}>
      <Card
        style={{ border: '1px solid rgba(115,92,0,0.15)', borderRadius: 12, background: '#faf8f2' }}
        styles={{ body: { padding: '20px 20px 16px' } }}
      >
        {/* Title */}
        <h3
          style={{
            fontFamily: '"Noto Serif", serif',
            fontSize: 13,
            fontWeight: 600,
            color: 'rgba(115,92,0,0.6)',
            margin: '0 0 4px 0',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
          }}
        >
          {tr.luckyElements[language]}
        </h3>
        <div
          style={{
            fontFamily: '"Noto Serif", serif',
            fontSize: 12,
            color: 'rgba(115,92,0,0.45)',
            marginBottom: 16,
          }}
        >
          {tr.luckyElemDesc[language]}
        </div>

        {/* Special-structure banner (非正格 only) — the structure, not day-master support, decides 喜忌 */}
        {!isZhengGe && (
          <div
            style={{
              display: 'flex',
              flexDirection: isMobile ? 'column' : 'row',
              alignItems: isMobile ? 'flex-start' : 'center',
              gap: isMobile ? 6 : 12,
              padding: '10px 14px',
              marginBottom: 16,
              borderRadius: 8,
              background: 'rgba(30, 90, 170, 0.06)',
              border: '1px dashed rgba(30, 90, 170, 0.4)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
              <span
                style={{
                  fontFamily: '"Ma Shan Zheng", serif',
                  fontSize: 20,
                  fontWeight: 700,
                  color: 'rgba(30, 90, 170, 0.9)',
                  lineHeight: 1,
                }}
              >
                {yongShen.格局详情?.名称 ?? yongShen.格局}
              </span>
              {yongShen.格局详情?.真假 && (
                <span
                  style={{
                    fontSize: 11,
                    fontFamily: '"Noto Sans SC", sans-serif',
                    color: 'rgba(30, 90, 170, 0.85)',
                    background: 'rgba(30, 90, 170, 0.1)',
                    border: '1px solid rgba(30, 90, 170, 0.35)',
                    borderRadius: 20,
                    padding: '1px 8px',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {yongShen.格局详情.真假}
                </span>
              )}
            </div>
            {structKey && (
              <div
                style={{
                  fontFamily: '"Noto Serif", serif',
                  fontSize: 13,
                  color: 'rgba(30, 90, 170, 0.85)',
                  lineHeight: 1.5,
                }}
              >
                {tr[structKey][language]}
              </div>
            )}
          </div>
        )}

        {/* Favorable / Unfavorable chip groups */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr',
            gap: isMobile ? 16 : 24,
            marginBottom: 16,
          }}
        >
          {favorable.length > 0 && (
            <div>
              <GroupLabel
                text={`${tr.favorableLabel[language]}${language === 'en' ? ' · 喜用' : ''}`}
                accent={FAVORABLE_COLOR}
              />
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {favorable.map((element) => (
                  <ElementChip
                    key={element}
                    element={element}
                    accent={FAVORABLE_COLOR}
                    language={language}
                    isMobile={isMobile}
                  />
                ))}
              </div>
            </div>
          )}
          {unfavorable.length > 0 && (
            <div>
              <GroupLabel
                text={`${tr.unfavorableLabel[language]}${language === 'en' ? ' · 忌' : ''}`}
                accent={UNFAVORABLE_COLOR}
              />
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {unfavorable.map((element) => (
                  <ElementChip
                    key={element}
                    element={element}
                    accent={UNFAVORABLE_COLOR}
                    language={language}
                    isMobile={isMobile}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Plain-language reason (正格 only — the banner explains special structures) */}
        {isZhengGe && reasonKey && (
          <div
            style={{
              fontFamily: '"Noto Serif", serif',
              fontSize: 13,
              color: 'rgba(115,92,0,0.65)',
              lineHeight: 1.6,
              marginBottom: climateElements.length > 0 ? 16 : 4,
            }}
          >
            {tr[reasonKey][language]}
          </div>
        )}

        {/* Climate needs (调候适用 only) */}
        {climateElements.length > 0 && (
          <div
            style={{
              paddingTop: 12,
              borderTop: '1px solid rgba(115,92,0,0.1)',
            }}
          >
            <GroupLabel
              text={`${tr.climateLabel[language]}${language === 'en' ? ' · 调候' : ''}`}
              accent={CLIMATE_COLOR}
            />
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {climateElements.map((element) => (
                <ElementChip
                  key={element}
                  element={element}
                  accent={CLIMATE_COLOR}
                  language={language}
                  isMobile={isMobile}
                />
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
