'use client';

/**
 * Last-resort boundary: the ONLY thing that catches a throw from the root layout.
 *
 * global-error.tsx REPLACES app/layout.tsx rather than rendering inside it, so
 * everything the root layout sets up has to be reproduced here:
 *   - its own <html>/<body>
 *   - @/styles/globals.css re-imported (this is what pulls in theme.css and therefore
 *     every --color-* / --font-* token)
 *   - the three next/font instances, with their .variable classes on <html> — omit
 *     them and the page silently renders in Times New Roman
 *
 * Three things are deliberately NOT reproduced:
 *   - ClientRoot / AuthProvider — auth or Firestore is plausibly what threw, and
 *     AuthProvider calls router.refresh(), which can loop on a persistent failure.
 *   - ConfigProvider — so antd components are unusable here. Hence the plain <button>
 *     and no <ErrorState>; the duplicated markup below is intentional, not an oversight.
 *   - LanguageProvider — so useLanguage() would silently degrade to 'en'. Rather than
 *     hand a Chinese user English on the scariest screen in the app, both languages are
 *     hardcoded and stacked.
 */

import '@/styles/globals.css';
import { useEffect } from 'react';
import { Noto_Serif, Ma_Shan_Zheng, Noto_Sans_SC } from 'next/font/google';
import { reportClientError } from '@/lib/errorReporter';

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
  preload: false,
});

const notoSansSC = Noto_Sans_SC({
  weight: ['400', '500', '700'],
  subsets: ['latin'],
  variable: '--font-noto-sans-sc',
  display: 'swap',
  preload: false,
});

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Safe even here: the reporter never throws and /api/clientError is unauthenticated.
    reportClientError({
      context: 'error_boundary',
      boundary: 'global',
      message: error.message,
      digest: error.digest,
    });
  }, [error]);

  return (
    <html
      lang="en"
      className={`${notoSerif.variable} ${maShanZheng.variable} ${notoSansSC.variable}`}
    >
      <body className="antialiased" suppressHydrationWarning>
        <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-parchment px-6 text-center">
          <h1 className="font-serif text-2xl m-0 text-gold-deep">Unable to load this page</h1>
          <p className="font-zh text-lg m-0 text-gold-deep">无法加载页面</p>

          {/* The only copy that names refresh as well as the button: a root-layout
              failure is the one case where the in-page retry may itself be broken. */}
          <p className="font-serif text-sm m-0 mt-2 text-bronze-muted">
            Please select Try again below, or refresh the page.
          </p>
          <p className="font-zh text-sm m-0 text-bronze-muted">
            请点击下方「重试」，或刷新页面。
          </p>

          <button type="button" className="indigo-cta mt-3" onClick={() => reset()}>
            Try again ・ 重试
          </button>

          {error.digest && (
            <p className="font-serif text-xs m-0 mt-2 text-bronze-muted/60">
              Reference ・ 错误编号: {error.digest}
            </p>
          )}
        </div>
      </body>
    </html>
  );
}
