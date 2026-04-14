'use client';

import Image from 'next/image';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';

export default function Header() {
  const { language, setLanguage } = useLanguage();
  const tr = translations.header;

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
          <button className="text-gold-deep font-serif tracking-tight hover:text-gold-light transition-colors duration-300 px-4 py-2">
            {tr.signIn[language]}
          </button>
        </div>
      </nav>
    </header>
  );
}
