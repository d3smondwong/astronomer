'use client';

import { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { createUserWithEmailAndPassword, signInWithEmailAndPassword } from 'firebase/auth';
import { auth } from '@/lib/firebaseClient';
import { useAuth } from '@/lib/authContext';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';

function friendlyError(code: string): string {
  switch (code) {
    case 'auth/email-already-in-use':
      // Reached when sign-in failed and create failed because email exists — means wrong password
      return 'Incorrect password for this account. Please try again.';
    case 'auth/weak-password':
      return 'Password must be at least 6 characters.';
    case 'auth/invalid-email':
      return 'Please enter a valid email address.';
    case 'auth/invalid-credential':
    case 'auth/wrong-password':
      return 'Incorrect email or password.';
    case 'auth/too-many-requests':
      return 'Too many attempts. Please try again later.';
    default:
      return 'Something went wrong. Please try again.';
  }
}

export default function AuthModal() {
  const { isAuthModalOpen, closeAuthModal, modalShowSkip, modalOnSkip } = useAuth();
  const { language } = useLanguage();
  const tr = translations.auth;
  const router = useRouter();
  const pathname = usePathname();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!isAuthModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      // Try sign-in first
      await signInWithEmailAndPassword(auth, email, password);
    } catch (signInErr: any) {
      // On invalid credential / user not found → try creating the account
      if (['auth/user-not-found', 'auth/invalid-credential', 'auth/wrong-password'].includes(signInErr.code)) {
        try {
          await createUserWithEmailAndPassword(auth, email, password);
        } catch (signUpErr: any) {
          setError(friendlyError(signUpErr.code));
          setSubmitting(false);
          return;
        }
      } else {
        setError(friendlyError(signInErr.code));
        setSubmitting(false);
        return;
      }
    }

    // Auth succeeded — redirect to latest profile when on the home page
    if (pathname === '/') {
      try {
        const idToken = await auth.currentUser?.getIdToken();
        if (idToken) {
          const res = await fetch('/api/profiles', {
            headers: { Authorization: `Bearer ${idToken}` },
          });
          if (res.ok) {
            const profiles = await res.json();
            if (profiles.length > 0) {
              handleClose();
              router.push(`/profile/${profiles[0].id}`);
              return;
            }
          }
        }
      } catch {
        // Non-fatal — fall through to close
      }
    }

    handleClose();
  };

  const handleClose = () => {
    closeAuthModal();
    setEmail('');
    setPassword('');
    setError('');
    setSubmitting(false);
  };

  const handleSkip = () => {
    handleClose();
    modalOnSkip?.();
  };

  return (
    <div
      style={{
        position: 'fixed', inset: 0,
        backgroundColor: 'rgba(0,0,0,0.5)',
        zIndex: 9999, display: 'flex',
        alignItems: 'center', justifyContent: 'center',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) handleClose(); }}
    >
      <div style={{
        backgroundColor: '#fff', borderRadius: '12px',
        width: '480px', maxWidth: 'calc(100vw - 48px)',
        boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
        fontFamily: 'Noto Serif, serif',
      }}>
        {/* Header bar */}
        <div style={{
          display: 'flex', alignItems: 'center',
          padding: '16px 24px', borderBottom: '1px solid #e8e8e8',
        }}>
          <button
            onClick={handleClose}
            aria-label="Close"
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              padding: '4px', borderRadius: '50%',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M2 2L14 14M14 2L2 14" stroke="#222" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
          <span style={{
            flex: 1, textAlign: 'center', fontWeight: 600,
            fontSize: '24px', color: '#222', marginRight: '24px',
          }}>
            {tr.loginTitle[language]}
          </span>
        </div>

        {/* Form body */}
        <form onSubmit={handleSubmit} style={{ padding: '12px 28px 28px' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '12px' }}>
            <img src="/straight_huat_life_logo_svg.svg" alt="Huat Life" style={{ height: '72px', width: 'auto' }} />
          </div>

          <div style={{ marginBottom: '12px' }}>
            <input
              type="email"
              placeholder={tr.emailPlaceholder[language]}
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              autoComplete="email"
              style={{
                width: '100%', padding: '14px 12px',
                border: '1px solid #b0b0b0', borderRadius: '8px',
                fontSize: '15px', fontFamily: 'Noto Serif, serif',
                outline: 'none', boxSizing: 'border-box',
              }}
            />
          </div>

          <div style={{ marginBottom: error ? '8px' : '20px' }}>
            <input
              type="password"
              placeholder={tr.passwordPlaceholder[language]}
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              minLength={6}
              autoComplete="current-password"
              style={{
                width: '100%', padding: '14px 12px',
                border: '1px solid #b0b0b0', borderRadius: '8px',
                fontSize: '15px', fontFamily: 'Noto Serif, serif',
                outline: 'none', boxSizing: 'border-box',
              }}
            />
          </div>

          {error && (
            <p style={{ color: '#c0392b', fontSize: '13px', marginBottom: '16px' }}>{error}</p>
          )}

          <button
            type="submit"
            disabled={submitting}
            style={{
              width: '100%', padding: '14px',
              backgroundColor: submitting ? '#7f7a9e' : '#3d3a5c',
              color: '#fff', border: 'none', borderRadius: '8px',
              fontSize: '15px', fontWeight: 600,
              fontFamily: 'Noto Serif, serif',
              cursor: submitting ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.2s',
            }}
          >
            {submitting ? tr.loading[language] : tr.continueBtn[language]}
          </button>

          {modalShowSkip && (
            <p style={{ textAlign: 'center', marginTop: '16px' }}>
              <button
                type="button"
                onClick={handleSkip}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  fontSize: '13px', color: '#888',
                  fontFamily: 'Noto Serif, serif',
                  textDecoration: 'underline',
                }}
              >
                {tr.skipForNow[language]}
              </button>
            </p>
          )}
        </form>
      </div>
    </div>
  );
}
