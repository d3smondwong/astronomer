'use client';

/**
 * MobileAccountPanel — sign in / sign out plus the EN/中文 toggle, opened from the
 * avatar button at the right edge of the chip strip.
 *
 * This exists because both controls were unreachable on a phone: dashboard.css hid
 * `.sidebar-login-btn` below 1024px and the language toggle sat in the sidebar footer
 * that a phone never sees. It shares the drop-down area with the birth-record panel —
 * at most one panel is open at a time.
 */

import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';

interface MobileAccountPanelProps {
  /** Display name for the signed-in user, or null for a guest. */
  accountName: string | null;
  onAuthAction: () => void;
}

export default function MobileAccountPanel({ accountName, onAuthAction }: MobileAccountPanelProps) {
  const { language, setLanguage } = useLanguage();
  const tr = translations.sidebar;

  return (
    <div className="mobile-panel" id="mobile-account-panel">
      <div className="mobile-panel-account-row">
        <span className="mobile-panel-account-name">{accountName ?? tr.guest[language]}</span>
        <button type="button" className="indigo-outline-btn" onClick={onAuthAction}>
          {accountName
            ? translations.header.signOut[language]
            : translations.header.loginSignUp[language]}
        </button>
      </div>

      {/* The toggle's own EN / 中文 labels are the label — a heading above it would
          only repeat them in whichever language is currently losing. */}
      <div className="mobile-panel-account-row">
        <div className="lang-toggle">
          {(['en', 'ch'] as const).map((lang) => (
            <button
              key={lang}
              className="lang-toggle-btn"
              data-active={language === lang}
              onClick={() => setLanguage(lang)}
            >
              {lang === 'en' ? 'EN' : '中文'}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
