'use client';

import { useState, useEffect } from 'react';
import { Card } from 'antd';
import { ELEMENT_ICONS, ELEMENT_EN, ELEMENT_COLOR } from '@/lib/elements';
import { goldAlpha, palette, strengthScale } from '@/lib/theme';
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
      className={`inline-flex items-center gap-1.5 rounded-[20px] ${isMobile ? 'px-2.5 py-1.5' : 'px-3.5 py-2'}`}
      style={{ background: `${accent}14`, border: `1px solid ${accent}55` }}
    >
      {Icon && <Icon style={{ fontSize: 18, color: ELEMENT_COLOR[element] }} />}
      <span className={`font-zh font-bold text-bronze-muted leading-none ${isMobile ? 'text-lg' : 'text-[22px]'}`}>
        {element}
      </span>
      {language === 'en' && (
        <span className="text-xs text-gold-deep/60 tracking-[0.03em]">
          {ELEMENT_EN[element]}
        </span>
      )}
    </div>
  );
}

function GroupLabel({ text, accent }: { text: string; accent: string }) {
  return (
    <div
      className="text-xs font-semibold tracking-[0.06em] uppercase mb-2"
      style={{ color: accent }}
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
    <div className="mt-4">
      <Card
        style={{ border: `1px solid ${goldAlpha(0.15)}`, borderRadius: 12, background: palette.parchment }}
        styles={{ body: { padding: '20px 20px 16px' } }}
      >
        {/* Title */}
        <h3 className="text-[13px] font-semibold text-gold-deep/60 m-0 mb-1 tracking-[0.08em] uppercase">
          {tr.luckyElements[language]}
        </h3>
        <div className="text-xs text-gold-deep/45 mb-4">
          {tr.luckyElemDesc[language]}
        </div>

        {/* Special-structure banner (非正格 only) — the structure, not day-master support, decides 喜忌 */}
        {!isZhengGe && (
          <div
            className={`flex px-3.5 py-2.5 mb-4 rounded-lg bg-info-blue/6 border border-dashed border-info-blue/40 ${
              isMobile ? 'flex-col items-start gap-1.5' : 'flex-row items-center gap-3'
            }`}
          >
            <div className="flex items-center gap-2 shrink-0">
              <span className="font-zh text-xl font-bold text-info-blue/90 leading-none">
                {yongShen.格局详情?.名称 ?? yongShen.格局}
              </span>
              {yongShen.格局详情?.真假 && (
                <span className="text-[11px] font-zh-sans text-info-blue/85 bg-info-blue/10 border border-info-blue/35 rounded-[20px] px-2 py-px whitespace-nowrap">
                  {yongShen.格局详情.真假}
                </span>
              )}
            </div>
            {structKey && (
              <div className="text-[13px] text-info-blue/85 leading-normal">
                {tr[structKey][language]}
              </div>
            )}
          </div>
        )}

        {/* Favorable / Unfavorable chip groups */}
        <div className={`grid mb-4 ${isMobile ? 'grid-cols-1 gap-4' : 'grid-cols-2 gap-6'}`}>
          {favorable.length > 0 && (
            <div>
              <GroupLabel
                text={`${tr.favorableLabel[language]}${language === 'en' ? ' · 喜用' : ''}`}
                accent={FAVORABLE_COLOR}
              />
              <div className="flex flex-wrap gap-2">
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
              <div className="flex flex-wrap gap-2">
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
          <div className={`text-[13px] text-gold-deep/65 leading-relaxed ${climateElements.length > 0 ? 'mb-4' : 'mb-1'}`}>
            {tr[reasonKey][language]}
          </div>
        )}

        {/* Climate needs (调候适用 only) */}
        {climateElements.length > 0 && (
          <div className="pt-3 border-t border-gold-deep/10">
            <GroupLabel
              text={`${tr.climateLabel[language]}${language === 'en' ? ' · 调候' : ''}`}
              accent={CLIMATE_COLOR}
            />
            <div className="flex flex-wrap gap-2">
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
