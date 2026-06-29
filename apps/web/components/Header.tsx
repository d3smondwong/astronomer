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
    <header className="fixed top-0 w-full z-50 shadow-sm" style={{ backgroundColor: '#fbf9f4' }}>
      <nav className="flex justify-between items-center px-8 py-2 max-w-7xl mx-auto w-full">
        <div className="flex items-center">
          <Image
            src="/logo.png"
            alt="Celestial Dawn"
            width={220}
            height={55}
            loading="eager"
            style={{ width: 'auto', height: '56px' }}
          />
        </div>
        <div className="flex items-center gap-4">
          {/* Language toggle */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              backgroundColor: '#3d3a5c',
              borderRadius: '9999px',
              padding: '3px',
              gap: '0',
              cursor: 'pointer',
            }}
          >
            {(['en', 'ch'] as const).map((lang) => (
              <button
                key={lang}
                onClick={() => setLanguage(lang)}
                style={{
                  fontSize: '13px',
                  fontFamily: 'Noto Serif, serif',
                  fontWeight: 600,
                  letterSpacing: '0.05em',
                  padding: '4px 16px',
                  borderRadius: '9999px',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  backgroundColor: language === lang ? '#3d3a5c' : 'white',
                  color: language === lang ? 'white' : '#3d3a5c',
                  boxShadow: language === lang ? 'none' : '0 1px 3px rgba(0,0,0,0.1)',
                }}
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
                <span style={{ fontSize: '13px', color: '#3d3a5c', fontFamily: 'Noto Serif, serif' }}>
                  {user.email?.split('@')[0]}
                </span>
                <button
                  onClick={signOut}
                  style={{
                    border: '1px solid #3d3a5c',
                    borderRadius: '8px',
                    backgroundColor: 'transparent',
                    color: '#3d3a5c',
                    fontFamily: 'Noto Serif, serif',
                    fontSize: '13px',
                    fontWeight: 600,
                    padding: '6px 14px',
                    cursor: 'pointer',
                  }}
                >
                  {tr.signOut[language]}
                </button>
              </div>
            ) : (
              <button
                onClick={() => openAuthModal()}
                style={{
                  border: '1px solid #3d3a5c',
                  borderRadius: '8px',
                  backgroundColor: 'transparent',
                  color: '#3d3a5c',
                  fontFamily: 'Noto Serif, serif',
                  fontSize: '13px',
                  fontWeight: 600,
                  padding: '6px 14px',
                  cursor: 'pointer',
                }}
              >
                {tr.loginSignUp[language]}
              </button>
            )
          )}
        </div>
      </nav>
    </header>
  );
}
