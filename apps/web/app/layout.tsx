import 'antd/dist/reset.css';
import type { Metadata } from "next";
import "@/styles/globals.css";
import { ConfigProvider } from 'antd';
import { Noto_Serif, Ma_Shan_Zheng, Noto_Sans_SC } from 'next/font/google';
import { antdTheme } from '@/lib/theme';
import { LanguageProvider } from '@/lib/languageContext';
import { ClientRoot } from '@/components/ClientRoot';

/**
 * Self-hosted fonts via next/font — no render-blocking Google Fonts CSS.
 * The CSS variables are consumed by theme.css (--font-serif, --font-zh,
 * --font-zh-sans) so Tailwind utilities and the antd theme pick them up.
 */
const notoSerif = Noto_Serif({
  subsets: ['latin'],
  weight: ['400', '700'],
  style: ['normal', 'italic'],
  variable: '--font-noto-serif',
  display: 'swap',
});

const maShanZheng = Ma_Shan_Zheng({
  weight: '400',
  subsets: ['latin'],
  variable: '--font-ma-shan-zheng',
  display: 'swap',
  preload: false, // CJK font — served subset-split on demand
});

const notoSansSC = Noto_Sans_SC({
  weight: ['400', '500', '700'],
  subsets: ['latin'],
  variable: '--font-noto-sans-sc',
  display: 'swap',
  preload: false, // CJK font — served subset-split on demand
});

export const metadata: Metadata = {
  title: "Celestial Dawn",
  description: "An ethereal Bazi reading application rooted in ancient wisdom and driven by AI.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${notoSerif.variable} ${maShanZheng.variable} ${notoSansSC.variable}`}>
      <body className="antialiased" suppressHydrationWarning>
        <ConfigProvider theme={antdTheme}>
          <LanguageProvider>
            <ClientRoot>
              {children}
            </ClientRoot>
          </LanguageProvider>
        </ConfigProvider>
      </body>
    </html>
  );
}
