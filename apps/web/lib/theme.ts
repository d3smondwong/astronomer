/**
 * theme.ts — JS-side design tokens for the "Celestial Dawn" theme.
 *
 * ⚠ KEEP IN SYNC WITH styles/theme.css — the two files define the same palette.
 * CSS-land (Tailwind utilities, component classes) reads styles/theme.css;
 * JS-land (antd ConfigProvider, chart colors, SVG fills) reads this file.
 * antd seed tokens must be literal color values (it derives hover/active
 * shades from them), so they cannot reference CSS variables.
 *
 * To change a brand color site-wide: edit it here AND in styles/theme.css.
 */
import type { ThemeConfig } from 'antd';

/** Brand palette — mirrors the @theme block in styles/theme.css. */
export const palette = {
  parchment: '#fbf9f4',
  parchmentDark: '#f4f1e8',
  goldDeep: '#735c00',
  goldLight: '#d4af37',
  bronzeMuted: '#4d4635',
  surfaceContainer: '#f0eee9',
  surfaceLow: '#f5f3ee',
  surfaceLowest: '#ffffff',
  outlineVariant: 'rgba(127, 118, 99, 0.15)',
  outlineStrong: '#8b7f73',
  /** Deep indigo used for the language toggle and auth CTAs. */
  inkIndigo: '#3d3a5c',
  /** Midnight-navy profile header gradient + its light-on-dark text tones. */
  inkNavy: '#1b263b',
  inkNavyLight: '#243447',
  frost: '#e8f4f8',
  frostMuted: '#d4dfe6',
  frostLabel: '#a8bcc9',
  /** Destructive/error accent (delete buttons, inline error text). */
  danger: '#c0392b',
  /** Informational blue accent (climate 调候 chips, 化气格 badges). */
  infoBlue: '#1e5a9a',
} as const;

/** The dominant translucent-gold pattern: rgba over gold-deep. */
export const goldAlpha = (alpha: number): string => `rgba(115, 92, 0, ${alpha})`;

/**
 * Font stacks — resolve through the next/font variables set on <html>
 * in app/layout.tsx. Safe to use in inline styles and antd tokens.
 */
export const fonts = {
  serif: 'var(--font-noto-serif), serif',
  zh: 'var(--font-ma-shan-zheng), cursive',
  zhSans: 'var(--font-noto-sans-sc), sans-serif',
} as const;

/**
 * 5-tier strength scale (very weak → very strong) shared by the day-master
 * gauge bands, its pointer, and the 得令/得地/得势 bar fills.
 */
export const strengthScale = {
  veryWeak: '#b42424',
  weak: '#c46000',
  balanced: '#9b8200',
  strong: '#2e8b57',
  veryStrong: '#146432',
} as const;

/**
 * Global antd theme (ConfigProvider) built from the palette so antd
 * components follow the same source of truth as everything else.
 */
export const antdTheme: ThemeConfig = {
  token: {
    colorPrimary: palette.goldDeep,
    fontFamily: fonts.serif,
    borderRadius: 4,
    colorBgContainer: palette.surfaceLowest,
    colorText: palette.bronzeMuted,
    colorBorder: palette.outlineVariant,
  },
  components: {
    Button: {
      colorPrimary: palette.goldDeep,
      colorPrimaryHover: palette.goldLight,
      borderRadius: 4,
    },
    Input: {
      activeBorderColor: palette.goldDeep,
      hoverBorderColor: palette.goldLight,
    },
    Radio: {
      colorPrimary: palette.goldDeep,
      colorBorder: palette.outlineStrong,
    },
  },
};
