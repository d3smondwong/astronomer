'use client';

import { useState, useEffect } from 'react';
import { Card } from 'antd';
import { ELEMENT_ICONS, ELEMENT_EN } from '@/lib/elements';
import { strengthScale } from '@/lib/theme';
import { BaziChartData, ElementState, FiveElements } from '@/types/baziChart';

const MOBILE_BREAKPOINT = 720;

interface FiveElementsCardProps {
  chartData: BaziChartData;
  language: 'en' | 'ch';
}

const ELEMENTS = ['木', '火', '土', '金', '水'] as const;

const STATE_ORDER: ElementState[] = ['死', '囚', '休', '相', '旺'];

// Seasonal-state colors reuse the shared 5-tier strength scale.
const STATE_COLORS: Record<ElementState, string> = {
  '旺': strengthScale.veryStrong,
  '相': strengthScale.strong,
  '休': strengthScale.balanced,
  '囚': strengthScale.weak,
  '死': strengthScale.veryWeak,
};

const STATE_EN: Record<ElementState, string> = {
  '旺': 'Flourishing',
  '相': 'Supported',
  '休': 'Resting',
  '囚': 'Restrained',
  '死': 'Dormant',
};

export default function FiveElementsCard({ chartData, language }: FiveElementsCardProps) {
  const wuXing = chartData['五行'] as FiveElements | undefined;

  const [isMobile, setIsMobile] = useState(
    typeof window !== 'undefined' && window.innerWidth < MOBILE_BREAKPOINT
  );
  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, []);

  if (!wuXing) return null;

  return (
    <Card
      styles={{
        body: { padding: isMobile ? '20px 20px 16px' : '20px 20px 16px' },
      }}
      style={{
        background: '#faf8f2',
        border: '1px solid rgba(115,92,0,0.15)',
        borderRadius: 12,
      }}
    >
      {/* Header */}
      <div
        style={{
          fontFamily: '"Noto Serif", serif',
          fontSize: 13,
          fontWeight: 600,
          color: 'rgba(115,92,0,0.6)',
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
          marginBottom: 20,
        }}
      >
        {language === 'en' ? 'Five Elements' : '五行旺衰'}
      </div>

      {/* Five columns */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(5, 1fr)',
          gap: 0,
        }}
      >
        {ELEMENTS.map((element, colIdx) => {
          const verdict = wuXing[element];
          const state = verdict?.状态 ?? '死';
          const stateIdx = STATE_ORDER.indexOf(state);
          const color = STATE_COLORS[state];
          const Icon = ELEMENT_ICONS[element];

          const tierBar = (
            <div style={{ display: 'flex', flexDirection: 'column-reverse', gap: 3 }}>
              {STATE_ORDER.map((_, segIdx) => (
                <div
                  key={segIdx}
                  style={{
                    width: 36,
                    height: 12,
                    borderRadius: 3,
                    background: segIdx <= stateIdx ? color : 'rgba(115,92,0,0.1)',
                    transition: 'background 0.2s ease',
                  }}
                />
              ))}
            </div>
          );

          const iconAndChar = (
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <Icon style={{ fontSize: 22, color }} />
              <span
                style={{
                  fontFamily: '"Ma Shan Zheng", serif',
                  fontSize: isMobile ? 18 : 28,
                  fontWeight: 700,
                  color: '#4d4635',
                  lineHeight: 1,
                }}
              >
                {element}
              </span>
            </div>
          );

          const englishName = (
            <span
              style={{
                fontFamily: '"Noto Serif", serif',
                fontSize: 12,
                color: 'rgba(115,92,0,0.55)',
                letterSpacing: '0.03em',
              }}
            >
              {ELEMENT_EN[element]}
            </span>
          );

          return (
            <div
              key={element}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 8,
                padding: '0 12px',
                borderLeft: colIdx > 0 ? '1px solid rgba(115,92,0,0.1)' : 'none',
              }}
            >
              {isMobile ? (
                /* Mobile: icon+char+english stacked above tier bar */
                <>
                  {iconAndChar}
                  {englishName}
                  {tierBar}
                </>
              ) : (
                /* Desktop: icon+char+english on the left, tier bar on the right */
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                    {iconAndChar}
                    {englishName}
                  </div>
                  {tierBar}
                </div>
              )}

              {/* State badge */}
              <div style={{ display: 'inline-flex', flexDirection: isMobile ? 'column' : 'row', alignItems: 'center', gap: isMobile ? 2 : 6, paddingTop: 4 }}>
                <span
                  style={{
                    fontFamily: '"Ma Shan Zheng", serif',
                    fontSize: 20,
                    fontWeight: 700,
                    color,
                  }}
                >
                  {state}
                </span>
                {language === 'en' && (
                  <span
                    style={{
                      fontFamily: '"Noto Serif", serif',
                      fontSize: 12,
                      color: 'rgba(115,92,0,0.6)',
                    }}
                  >
                    {STATE_EN[state]}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
