import type { Metadata } from "next";
import "@/styles/globals.css"; // includes antd reset (layered) — see globals.css header
import { ConfigProvider } from 'antd';
import { Noto_Serif, Ma_Shan_Zheng, Noto_Sans_SC } from 'next/font/google';
import { antdTheme } from '@/lib/theme';
import { LanguageProvider } from '@/lib/languageContext';
import { ClientRoot } from '@/components/ClientRoot';
import { getSessionUser } from '@/lib/session';

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
  /**
   * Referenced from /public rather than moved to the app/icon.svg file convention: the same
   * asset is the collapsed-sidebar logo in DashboardShell, and one copy beats two that can
   * drift. This also settles the favicon.ico 404 the browser console logged on every page.
   */
  icons: { icon: '/short_huat_life_logo.svg' },
};

/**
 * Async because it reads the session cookie: AuthProvider needs to know which identity the
 * SERVER actually rendered for, so it can tell whether a router.refresh() is still needed.
 * That comparison replaces an "already synced" flag which a remount could reset, causing an
 * endless refresh loop (see lib/authContext.tsx). Reading cookies here makes every route
 * dynamic — no loss, they already were.
 */
export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const session = await getSessionUser();
  const serverIdentity = session ? `${session.uid}:${session.isAnonymous}` : null;

  return (
    <html lang="en" className={`${notoSerif.variable} ${maShanZheng.variable} ${notoSansSC.variable}`}>
      <body className="antialiased" suppressHydrationWarning>
        <ConfigProvider theme={antdTheme}>
          <LanguageProvider>
            <ClientRoot serverIdentity={serverIdentity}>
              {children}
            </ClientRoot>
          </LanguageProvider>
        </ConfigProvider>
      </body>
    </html>
  );
}
