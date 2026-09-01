'use client';

import { Card } from 'antd';
import { ELEMENT_ICONS, ELEMENT_EN } from '@/lib/elements';
import { goldAlpha, palette, strengthScale } from '@/lib/theme';
import { useIsMobile } from '@/lib/useBreakpoint';
import { BaziChartData, ElementState, FiveElements } from '@/types/baziChart';

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

  // Shared tier (768px). This card used to keep its own 720px resize listener seeded
  // from window.innerWidth, which disagreed with the server HTML on first paint.
  const isMobile = useIsMobile();

  if (!wuXing) return null;

  return (
    <Card
      styles={{ body: { padding: '20px 20px 16px' } }}
      style={{
        background: palette.parchment,
        border: `1px solid ${goldAlpha(0.15)}`,
        borderRadius: 12,
      }}
    >
      {/* Header */}
      <div className="text-[13px] font-semibold text-gold-deep/60 tracking-wider uppercase mb-5">
        {language === 'en' ? 'Five Elements' : '五行旺衰'}
      </div>

      {/* Five columns */}
      <div className="grid grid-cols-5 gap-0">
        {ELEMENTS.map((element, colIdx) => {
          const verdict = wuXing[element];
          const state = verdict?.状态 ?? '死';
          const stateIdx = STATE_ORDER.indexOf(state);
          const color = STATE_COLORS[state];
          const Icon = ELEMENT_ICONS[element];

          const tierBar = (
            <div className="flex flex-col-reverse gap-[3px]">
              {STATE_ORDER.map((_, segIdx) => (
                <div
                  key={segIdx}
                  className="w-9 h-3 rounded-[3px] transition-colors duration-200"
                  style={{ background: segIdx <= stateIdx ? color : goldAlpha(0.1) }}
                />
              ))}
            </div>
          );

          const iconAndChar = (
            <div className="flex items-center gap-1">
              <Icon style={{ fontSize: 22, color }} />
              <span
                className={`font-zh font-bold text-bronze-muted leading-none ${isMobile ? 'text-lg' : 'text-[28px]'}`}
              >
                {element}
              </span>
            </div>
          );

          const englishName = (
            <span className="text-xs text-gold-deep/55 tracking-[0.03em]">
              {ELEMENT_EN[element]}
            </span>
          );

          return (
            <div
              key={element}
              className={`flex flex-col items-center gap-2 px-3 ${colIdx > 0 ? 'border-l border-gold-deep/10' : ''}`}
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
                <div className="flex items-center gap-2.5">
                  <div className="flex flex-col items-center gap-1">
                    {iconAndChar}
                    {englishName}
                  </div>
                  {tierBar}
                </div>
              )}

              {/* State badge — color is state-driven */}
              <div className={`inline-flex items-center pt-1 ${isMobile ? 'flex-col gap-0.5' : 'flex-row gap-1.5'}`}>
                <span className="font-zh text-xl font-bold" style={{ color }}>
                  {state}
                </span>
                {language === 'en' && (
                  <span className="text-xs text-gold-deep/60">
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
