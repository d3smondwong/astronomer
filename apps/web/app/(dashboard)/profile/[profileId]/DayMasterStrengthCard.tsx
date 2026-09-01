'use client';

import { Card } from 'antd';
import { translations } from '@/lib/translations';
import { useIsMobile, useIsBelowTablet } from '@/lib/useBreakpoint';
import {
  GaugeContainer,
  GaugeReferenceArc,
  useGaugeState,
} from '@mui/x-charts/Gauge';
import { ELEMENT_ICONS } from '@/lib/elements';
import { goldAlpha, palette, strengthScale } from '@/lib/theme';

interface DayMasterStrengthCardProps {
  chartData: any;
  language: 'en' | 'ch';
}


const VERDICT_TIERS = [
  { threshold: 3.2, key: '极旺', color: strengthScale.veryStrong, label: { en: 'Very Strong', ch: '极旺' } },
  { threshold: 2.4, key: '旺',   color: strengthScale.strong,     label: { en: 'Strong', ch: '旺' } },
  { threshold: 1.6, key: '中和', color: strengthScale.balanced,   label: { en: 'Balanced', ch: '中和' } },
  { threshold: 0.8, key: '弱',   color: strengthScale.weak,       label: { en: 'Weak', ch: '弱' } },
  { threshold: 0.0, key: '极弱', color: strengthScale.veryWeak,   label: { en: 'Very Weak', ch: '极弱' } },
];

const GAUGE_BAND_ORDER = [...VERDICT_TIERS].reverse();

// Maps a 0–4 score to the 0–100 value MUI Gauge expects
function scoreToGaugeValue(score: number): number {
  return Math.min((score / 4) * 100, 100);
}

// Draws the 5 tier colour bands using gauge context coords so they align with the needle.
function GaugeColorBands() {
  const { startAngle, endAngle, outerRadius, innerRadius, cx, cy } = useGaugeState();
  const totalSweep = endAngle - startAngle;
  const strokeWidth = outerRadius - innerRadius;

  // Band widths proportional to verdict ranges (0-4 score scale)
  const bandRanges = [
    { tier: GAUGE_BAND_ORDER[0], widthRatio: 0.8 / 4 },  // 极弱: 0-0.8
    { tier: GAUGE_BAND_ORDER[1], widthRatio: 0.8 / 4 },  // 弱: 0.8-1.6
    { tier: GAUGE_BAND_ORDER[2], widthRatio: 0.8 / 4 },  // 中和: 1.6-2.4
    { tier: GAUGE_BAND_ORDER[3], widthRatio: 0.8 / 4 },  // 旺: 2.4-3.2
    { tier: GAUGE_BAND_ORDER[4], widthRatio: 0.8 / 4 },  // 极旺: 3.2-4.0
  ];

  let currentAngle = startAngle;

  return (
    <>
      {bandRanges.map((band) => {
        const a0 = currentAngle;
        const a1 = a0 + totalSweep * band.widthRatio;
        const r = (outerRadius + innerRadius) / 2;
        const x1 = cx + r * Math.sin(a0);
        const y1 = cy - r * Math.cos(a0);
        const x2 = cx + r * Math.sin(a1);
        const y2 = cy - r * Math.cos(a1);
        const isLastBand = band.tier.key === GAUGE_BAND_ORDER[4].key;
        const isFirstBand = band.tier.key === GAUGE_BAND_ORDER[0].key;

        const path = (
          <path
            key={band.tier.key}
            d={`M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`}
            fill="none"
            stroke={band.tier.color}
            strokeWidth={strokeWidth}
            strokeLinecap={isFirstBand || isLastBand ? 'round' : 'butt'}
          />
        );
        currentAngle = a1;
        return path;
      })}
    </>
  );
}

function GaugePointer({ color }: { color: string }) {
  const { valueAngle, outerRadius, cx, cy } = useGaugeState();
  if (valueAngle === null) return null;
  const target = {
    x: cx + (outerRadius - 10) * Math.sin(valueAngle),
    y: cy - (outerRadius - 10) * Math.cos(valueAngle),
  };
  return (
    <g>
      <circle cx={cx} cy={cy} r={5} fill={color} />
      <path
        d={`M ${cx} ${cy} L ${target.x} ${target.y}`}
        stroke={color}
        strokeWidth={3}
        strokeLinecap="round"
      />
    </g>
  );
}

function ElementRow({ elem, dimmed }: { elem: string; dimmed?: boolean }) {
  const Icon = ELEMENT_ICONS[elem];
  return (
    <div className={`flex flex-row items-center gap-2 ${dimmed ? 'opacity-50' : ''}`}>
      {Icon && <Icon style={{ fontSize: 24, color: goldAlpha(0.6) }} />}
      <div className="text-lg font-zh-sans font-semibold text-gold-deep/70">
        {elem}
      </div>
    </div>
  );
}

// One vertical bar gauge (得令 / 得地 / 得势) — height/fill are score-driven.
function ScoreBar({ score, label }: { score: number; label: string }) {
  return (
    <div className="flex flex-col items-center gap-1.5 flex-1">
      <div className="relative w-7 h-20 rounded-md bg-gold-deep/10 overflow-hidden">
        <div
          className="absolute bottom-0 w-full rounded-md transition-[height,background] duration-300"
          style={{ height: `${(score / 4) * 100}%`, background: getBarFillColor(score, 4) }}
        />
      </div>
      <div className="text-sm text-gold-deep/60 tracking-wide uppercase">{label}</div>
      <div className="text-sm text-gold-deep/70 font-semibold">{score} / 4</div>
    </div>
  );
}

function getTierForScore(score: number): typeof VERDICT_TIERS[number] {
  for (const tier of VERDICT_TIERS) {
    if (score >= tier.threshold) return tier;
  }
  return VERDICT_TIERS[VERDICT_TIERS.length - 1];
}


function getBarFillColor(score: number, max: number): string {
  const ratio = Math.min(score / max, 1);
  if (ratio < 0.2) return strengthScale.veryWeak;
  if (ratio < 0.4) return strengthScale.weak;
  if (ratio < 0.6) return strengthScale.balanced;
  if (ratio < 0.8) return strengthScale.strong;
  return strengthScale.veryStrong;
}

export default function DayMasterStrengthCard({ chartData, language }: DayMasterStrengthCardProps) {
  const tr = translations.profile;
  const dayMaster = chartData?.["日主"];

  // Shared tiers (768 / 1024), replacing this card's own 720/1024 resize listener.
  const isMobile = useIsMobile();
  const isTablet = useIsBelowTablet();

  if (!dayMaster) return null;

  const { 天干, 五行, 得令, 得地, 得势, 强弱, 强弱分数 } = dayMaster;

  const jielingScore = 得令?.分数 ?? 0;
  const jieqiScore = 得地?.分数 ?? 0;
  const shiliScore = 得势?.分数 ?? 0;

  return (
    <div className="mt-4">
      <Card
        style={{ border: `1px solid ${goldAlpha(0.15)}`, borderRadius: '12px', background: palette.parchment }}
        styles={{ body: { padding: '20px 20px 16px' } }}
      >
        {/* Title */}
        <h3 className="text-[13px] font-semibold text-gold-deep/60 m-0 mb-5 tracking-[0.08em] uppercase">
          {tr.dayMasterStrength[language]}
        </h3>

        {/* Main Section: Day Master Info (left) + Gauge + Bars (right).
            Layout switches are JS-breakpoint-driven — they stay inline. */}
        <div
          className="gap-6 mb-6 items-stretch"
          style={{
            display: isMobile ? 'flex' : 'grid',
            gridTemplateColumns: isTablet && !isMobile ? '1fr' : 'auto 1fr 2fr',
            ...(isMobile && { flexDirection: 'column' as const }),
          }}
        >
          {/* Left: Day Master Info Vertical Stack */}
          <div className="flex flex-col items-center justify-center gap-4 min-w-[180px]">
            {/* Stem Character */}
            <div className="font-zh text-[40px] text-bronze-muted leading-none font-bold text-center">
              {天干}
            </div>

            {/* Element with Icon (and optional 化气格 transformation) */}
            {(() => {
              const 化气格信息 = chartData?.["四柱实体"]?.["日柱"]?.["化气格信息"];
              const 原五行 = 化气格信息?.["原五行"];
              const 现五行 = 化气格信息?.["现五行"];
              const hasTransform = 原五行 != null && 现五行 != null;

              if (!hasTransform) return <ElementRow elem={五行} />;

              return (
                <div className="flex flex-col items-center gap-1">
                  <ElementRow elem={现五行!} />
                  <div className="relative flex items-center justify-center">
                    <span className="opacity-45 text-xl text-bronze-muted">↑</span>
                    <span className="absolute left-1/2 ml-2 text-xs font-zh-sans text-info-blue/85 bg-info-blue/8 border border-dashed border-info-blue/50 rounded-[20px] px-[7px] py-px whitespace-nowrap leading-[1.6]">
                      天干合·化气格
                    </span>
                  </div>
                  <ElementRow elem={原五行} dimmed />
                </div>
              );
            })()}

          </div>

          {/* Center: Gauge */}
          <div className="flex flex-col items-center justify-center">
            <div className="relative w-[300px] h-[190px]">
              <GaugeContainer
                width={300}
                height={190}
                startAngle={-110}
                endAngle={110}
                value={scoreToGaugeValue(强弱分数)}
              >
                <GaugeReferenceArc style={{ stroke: goldAlpha(0.08) }} />
                <GaugeColorBands />
                <GaugePointer color={getTierForScore(强弱分数).color} />
              </GaugeContainer>

              {/* End labels */}
              <div className="absolute bottom-[-25px] left-2 text-sm text-gold-deep/55 font-medium">
                {language === 'ch' ? '极弱' : 'Very Weak'}
              </div>
              <div className="absolute bottom-[-25px] right-2 text-sm text-gold-deep/55 font-medium">
                {language === 'ch' ? '极旺' : 'Very Strong'}
              </div>
            </div>

            {/* Verdict text below gauge — color is tier-driven. English labels ("Very Strong")
                are far wider than the 2-char Chinese, so they run smaller to clear the gauge's
                end labels. */}
            <div
              className={`font-bold leading-none mt-4 ${language === 'ch' ? 'font-zh text-[28px]' : 'font-serif text-[19px]'}`}
              style={{ color: getTierForScore(强弱分数).color }}
            >
              {language === 'ch' ? 强弱 : getTierForScore(强弱分数).label.en}
            </div>
          </div>

          {/* Right: 3 Vertical Bar Gauges */}
          <div className="flex gap-3 justify-around items-end">
            <ScoreBar score={jielingScore} label={tr.dmSeasonalAuth[language]} />
            <ScoreBar score={jieqiScore} label={tr.dmRooting[language]} />
            <ScoreBar score={shiliScore} label={tr.dmSupport[language]} />
          </div>
        </div>

      </Card>
    </div>
  );
}
