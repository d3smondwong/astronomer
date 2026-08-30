'use client';

import Image from 'next/image';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';
import { useAuth } from '@/lib/authContext';

export default function Header() {
  const { language, setLanguage } = useLanguage();
  const tr = translations.header;
  const { user, loading, openAuthModal, signOut } = useAuth();

  return (
    <header className="fixed top-0 w-full z-50 shadow-sm bg-parchment">
      <nav className="flex justify-between items-center px-8 py-2 max-w-7xl mx-auto w-full">
        <div className="flex items-center">
          <Image
            src="/logo.png"
            alt="Celestial Dawn"
            width={220}
            height={55}
            loading="eager"
            className="w-auto h-14"
          />
        </div>
        <div className="flex items-center gap-4">
          {/* Language toggle — header variant is slightly larger than the sidebar one */}
          <div className="lang-toggle cursor-pointer">
            {(['en', 'ch'] as const).map((lang) => (
              <button
                key={lang}
                className="lang-toggle-btn text-[13px] px-4 py-1"
                data-active={language === lang}
                onClick={() => setLanguage(lang)}
              >
                {lang === 'en' ? 'EN' : '中文'}
              </button>
            ))}
          </div>

          {/* Auth area — hidden during initial auth state check. Anonymous (guest) users see
              the Login / Sign Up button; only permanent accounts see the account UI. */}
          {!loading && (
            user && !user.isAnonymous ? (
              <div className="flex items-center gap-3">
                <span className="text-[13px] text-ink-indigo">
                  {user.email?.split('@')[0]}
                </span>
                <button className="indigo-outline-btn" onClick={signOut}>
                  {tr.signOut[language]}
                </button>
              </div>
            ) : (
              <button className="indigo-outline-btn" onClick={() => openAuthModal()}>
                {tr.loginSignUp[language]}
              </button>
            )
          )}
        </div>
      </nav>
    </header>
  );
}
