'use client';

import { useEffect, useState } from 'react';

// Five elements in the generative (生) cycle, with the chart's element colors.
const ELEMENTS = [
  { glyph: '木', color: '#2d6a2d' },
  { glyph: '火', color: '#b42424' },
  { glyph: '土', color: '#8a6200' },
  { glyph: '金', color: '#8a7a3a' },
  { glyph: '水', color: '#1e5a9a' },
];

// Themed status lines, cycled while the LLM composes the report.
const PHRASES: { en: string; ch: string }[] = [
  { en: 'Casting the four pillars…', ch: '排定四柱…' },
  { en: 'Weighing your five elements…', ch: '权衡五行…' },
  { en: 'Tracing the hidden stems…', ch: '探寻藏干…' },
  { en: 'Reading the auspicious stars…', ch: '解读神煞…' },
  { en: 'Measuring the day master’s strength…', ch: '衡量日主强弱…' },
  { en: 'Following the cycle of life stages…', ch: '推算十二长生…' },
  { en: 'Mapping the ten gods…', ch: '梳理十神…' },
  { en: 'Sensing the seasonal energy…', ch: '体察节气之气…' },
  { en: 'Watching the clashes and harmonies…', ch: '观察刑冲合害…' },
  { en: 'Listening to the ancestral palace…', ch: '聆听祖业之宫…' },
  { en: 'Searching the marriage palace…', ch: '寻访夫妻宫…' },
  { en: 'Unlocking the wealth vaults…', ch: '开启财库…' },
  { en: 'Consulting the classical texts…', ch: '查阅古籍文献…' },
  { en: 'Aligning heaven, earth and self…', ch: '调和天地人…' },
  { en: 'Composing your story…', ch: '编织命书…' },
];

export default function InsightsLoading({
  language,
  compact = false,
}: {
  language: 'en' | 'ch';
  compact?: boolean;
}) {
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setIdx((i) => (i + 1) % PHRASES.length), 2200);
    return () => clearInterval(id);
  }, []);

  const glyphSize = compact ? '18px' : '30px';
  const phraseSize = compact ? '13px' : '15px';

  return (
    <div
      className={
        compact
          ? 'flex items-center gap-3 py-2'
          : 'flex flex-col items-center gap-5 py-8'
      }
    >
      <style>{`
        @keyframes baziPulse {
          0%, 100% { transform: scale(1); opacity: .3; text-shadow: none; }
          50%      { transform: scale(1.28); opacity: 1; text-shadow: 0 0 14px currentColor; }
        }
        @keyframes baziFade {
          from { opacity: 0; transform: translateY(4px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      <div className={compact ? 'flex items-end gap-2' : 'flex items-end gap-4'} aria-hidden>
        {ELEMENTS.map((el, i) => (
          <span
            key={el.glyph}
            className="font-serif"
            style={{
              color: el.color,
              fontSize: glyphSize,
              fontWeight: 600,
              display: 'inline-block',
              animation: 'baziPulse 2s ease-in-out infinite',
              animationDelay: `${i * 0.4}s`,
            }}
          >
            {el.glyph}
          </span>
        ))}
      </div>

      <p
        key={idx}
        className={compact ? 'font-serif text-bronze-muted/80' : 'font-serif text-center text-bronze-muted'}
        style={{ fontSize: phraseSize, fontWeight: 600, animation: 'baziFade .6s ease-out' }}
        aria-live="polite"
      >
        {PHRASES[idx][language]}
      </p>
    </div>
  );
}
