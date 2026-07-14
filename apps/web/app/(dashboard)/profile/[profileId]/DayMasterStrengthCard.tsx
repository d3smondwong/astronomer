'use client';

import { useEffect, useState } from 'react';
import { Card } from 'antd';
import { translations } from '@/lib/translations';
import {
  GaugeContainer,
  GaugeReferenceArc,
  useGaugeState,
} from '@mui/x-charts/Gauge';
import {
  Nature,
  LocalFireDepartment,
  Terrain,
  StopCircleOutlined,
  Waves,
} from '@mui/icons-material';

interface DayMasterStrengthCardProps {
  chartData: any;
  language: 'en' | 'ch';
}

const MOBILE_BREAKPOINT = 720;
const TABLET_BREAKPOINT = 1024;

const ELEMENT_ICONS: Record<string, React.ComponentType<any>> = {
  '木': Nature,
  '火': LocalFireDepartment,
  '土': Terrain,
  '金': StopCircleOutlined,
  '水': Waves,
};

const VERDICT_TIERS = [
  { threshold: 3.2, key: '极旺', color: '#146432', label: { en: 'Very Strong', ch: '极旺' } },
  { threshold: 2.4, key: '旺',   color: '#2e8b57', label: { en: 'Strong', ch: '旺' } },
  { threshold: 1.6, key: '中和', color: '#9b8200', label: { en: 'Balanced', ch: '中和' } },
  { threshold: 0.8, key: '弱',   color: '#c46000', label: { en: 'Weak', ch: '弱' } },
  { threshold: 0.0, key: '极弱', color: '#b42424', label: { en: 'Very Weak', ch: '极弱' } },
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
    <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '8px', opacity: dimmed ? 0.5 : 1 }}>
      {Icon && <Icon sx={{ fontSize: '24px', color: 'rgba(115,92,0,0.6)' }} />}
      <div style={{ fontSize: '18px', fontFamily: '"Noto Sans SC", sans-serif', color: 'rgba(115,92,0,0.7)', fontWeight: 600 }}>
        {elem}
      </div>
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
  if (ratio < 0.2) return '#b42424';      // very weak
  if (ratio < 0.4) return '#c46000';      // weak
  if (ratio < 0.6) return '#9b8200';      // balanced
  if (ratio < 0.8) return '#2e8b57';      // strong
  return '#146432';                       // very strong
}

export default function DayMasterStrengthCard({ chartData, language }: DayMasterStrengthCardProps) {
  const tr = translations.profile;
  const dayMaster = chartData?.["日主"];

  const [isMobile, setIsMobile] = useState(
    typeof window !== 'undefined' && window.innerWidth < MOBILE_BREAKPOINT
  );
  const [isTablet, setIsTablet] = useState(
    typeof window !== 'undefined' && window.innerWidth < TABLET_BREAKPOINT
  );
  useEffect(() => {
    const handler = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
      setIsTablet(window.innerWidth < TABLET_BREAKPOINT);
    };
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, []);

  if (!dayMaster) return null;

  const { 天干, 五行, 得令, 得地, 得势, 强弱, 强弱分数 } = dayMaster;

  const jielingScore = 得令?.分数 ?? 0;
  const jieqiScore = 得地?.分数 ?? 0;
  const shiliScore = 得势?.分数 ?? 0;


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
          margin: '0 0 20px 0',
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
        }}>
          {tr.dayMasterStrength[language]}
        </h3>

        {/* Main Section: Day Master Info (left) + Gauge + Bars (right) */}
        <div style={{
          display: isMobile ? 'flex' : 'grid',
          gridTemplateColumns: isTablet && !isMobile ? '1fr' : 'auto 1fr 2fr',
          gap: '24px',
          marginBottom: '24px',
          alignItems: 'stretch',
          ...(isMobile && { flexDirection: 'column' }),
        }}>
          {/* Left: Day Master Info Vertical Stack */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '16px',
            minWidth: '180px',
          }}>
            {/* Stem Character */}
            <div style={{
              fontFamily: '"Ma Shan Zheng", serif',
              fontSize: '40px',
              color: '#4d4635',
              lineHeight: 1,
              fontWeight: 700,
              textAlign: 'center',
            }}>
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
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                  <ElementRow elem={现五行!} />
                  <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ opacity: 0.45, fontSize: '20px', color: '#4d4635' }}>↑</span>
                    <span style={{
                      position: 'absolute',
                      left: '50%',
                      marginLeft: '8px',
                      fontSize: '12px',
                      fontFamily: '"Noto Sans SC", sans-serif',
                      color: 'rgba(30, 90, 170, 0.85)',
                      background: 'rgba(30, 90, 170, 0.08)',
                      border: '1px dashed rgba(30, 90, 170, 0.5)',
                      borderRadius: '20px',
                      padding: '1px 7px',
                      whiteSpace: 'nowrap',
                      lineHeight: 1.6,
                    }}>
                      天干合·化气格
                    </span>
                  </div>
                  <ElementRow elem={原五行} dimmed />
                </div>
              );
            })()}

          </div>

          {/* Center: Gauge */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ position: 'relative', width: '300px', height: '190px' }}>
              <GaugeContainer
                width={300}
                height={190}
                startAngle={-110}
                endAngle={110}
                value={scoreToGaugeValue(强弱分数)}
              >
                <GaugeReferenceArc style={{ stroke: 'rgba(115,92,0,0.08)' }} />
                <GaugeColorBands />
                <GaugePointer color={getTierForScore(强弱分数).color} />
              </GaugeContainer>

              {/* End labels */}
              <div style={{ position: 'absolute', bottom: '-25px', left: '8px', fontSize: '14px', fontFamily: '"Noto Serif", serif', color: 'rgba(115,92,0,0.55)', fontWeight: 500 }}>
                {language === 'ch' ? '极弱' : 'Very Weak'}
              </div>
              <div style={{ position: 'absolute', bottom: '-25px', right: '8px', fontSize: '14px', fontFamily: '"Noto Serif", serif', color: 'rgba(115,92,0,0.55)', fontWeight: 500 }}>
                {language === 'ch' ? '极旺' : 'Very Strong'}
              </div>
            </div>

            {/* Verdict text below gauge */}
            <div style={{
              fontFamily: language === 'ch' ? '"Ma Shan Zheng", serif' : '"Noto Serif", serif',
              fontSize: '28px',
              color: getTierForScore(强弱分数).color,
              fontWeight: 700,
              lineHeight: 1,
              marginTop: '12px',
            }}>
              {language === 'ch' ? 强弱 : getTierForScore(强弱分数).label.en}
            </div>
          </div>

          {/* Right: 3 Vertical Bar Gauges */}
          <div style={{
            display: 'flex',
            gap: '12px',
            justifyContent: 'space-around',
            alignItems: 'flex-end',
          }}>
            {/* 得令 Bar */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', flex: 1 }}>
              <div style={{
                position: 'relative',
                width: '28px',
                height: '80px',
                borderRadius: '6px',
                background: 'rgba(115,92,0,0.1)',
                overflow: 'hidden',
              }}>
                <div style={{
                  position: 'absolute',
                  bottom: 0,
                  width: '100%',
                  height: `${(jielingScore / 4) * 100}%`,
                  background: getBarFillColor(jielingScore, 4),
                  borderRadius: '6px',
                  transition: 'height 0.3s ease, background 0.3s ease',
                }} />
              </div>
              <div style={{ fontSize: '14px', fontFamily: '"Noto Serif", serif', color: 'rgba(115,92,0,0.6)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                {tr.dmSeasonalAuth[language]}
              </div>
              <div style={{ fontSize: '14px', fontFamily: '"Noto Serif", serif', color: 'rgba(115,92,0,0.7)', fontWeight: 600 }}>
                {jielingScore} / 4
              </div>
            </div>

            {/* 得地 Bar */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', flex: 1 }}>
              <div style={{
                position: 'relative',
                width: '28px',
                height: '80px',
                borderRadius: '6px',
                background: 'rgba(115,92,0,0.1)',
                overflow: 'hidden',
              }}>
                <div style={{
                  position: 'absolute',
                  bottom: 0,
                  width: '100%',
                  height: `${(jieqiScore / 4) * 100}%`,
                  background: getBarFillColor(jieqiScore, 4),
                  borderRadius: '6px',
                  transition: 'height 0.3s ease, background 0.3s ease',
                }} />
              </div>
              <div style={{ fontSize: '14px', fontFamily: '"Noto Serif", serif', color: 'rgba(115,92,0,0.6)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                {tr.dmRooting[language]}
              </div>
              <div style={{ fontSize: '14px', fontFamily: '"Noto Serif", serif', color: 'rgba(115,92,0,0.7)', fontWeight: 600 }}>
                {jieqiScore} / 4
              </div>
            </div>

            {/* 得势 Bar */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', flex: 1 }}>
              <div style={{
                position: 'relative',
                width: '28px',
                height: '80px',
                borderRadius: '6px',
                background: 'rgba(115,92,0,0.1)',
                overflow: 'hidden',
              }}>
                <div style={{
                  position: 'absolute',
                  bottom: 0,
                  width: '100%',
                  height: `${(shiliScore / 4) * 100}%`,
                  background: getBarFillColor(shiliScore, 4),
                  borderRadius: '6px',
                  transition: 'height 0.3s ease, background 0.3s ease',
                }} />
              </div>
              <div style={{ fontSize: '14px', fontFamily: '"Noto Serif", serif', color: 'rgba(115,92,0,0.6)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                {tr.dmSupport[language]}
              </div>
              <div style={{ fontSize: '14px', fontFamily: '"Noto Serif", serif', color: 'rgba(115,92,0,0.7)', fontWeight: 600 }}>
                {shiliScore} / 4
              </div>
            </div>
          </div>
        </div>

      </Card>
    </div>
  );
}
