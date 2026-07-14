'use client';

import { useState } from 'react';
import Image from 'next/image';
import { useRouter, usePathname } from 'next/navigation';
import {
  EmailAuthProvider,
  linkWithCredential,
  signInWithEmailAndPassword,
} from 'firebase/auth';
import { auth } from '@/lib/firebaseClient';
import { useAuth } from '@/lib/authContext';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';
import { reportClientError } from '@/lib/errorReporter';
import { toast } from 'sonner';

/**
 * Move the guest's profiles to the just-signed-in account. Migration failures are usually
 * transient (a network blip or a momentary server error), so retry a few times with
 * exponential backoff before giving up. Deterministic client errors (4xx) won't change on
 * retry, so we stop immediately on those. Returns true once the migration succeeds.
 */
async function migrateGuestProfiles(anonIdToken: string): Promise<boolean> {
  const backoffMs = [1000, 3000]; // waits before the 2nd and 3rd attempts → 3 attempts total
  for (let attempt = 0; attempt <= backoffMs.length; attempt++) {
    try {
      // Re-read the destination token each attempt so it can't go stale across the backoff.
      const newIdToken = await auth.currentUser?.getIdToken();
      if (newIdToken) {
        const res = await fetch('/api/profiles/migrate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${newIdToken}` },
          body: JSON.stringify({ anonIdToken }),
        });
        if (res.ok) return true;
        // 4xx (bad token / bad request) is deterministic — retrying won't help.
        if (res.status < 500 && res.status !== 408 && res.status !== 429) return false;
      }
    } catch {
      /* network error → transient, fall through to retry */
    }
    if (attempt < backoffMs.length) {
      await new Promise((resolve) => setTimeout(resolve, backoffMs[attempt]));
    }
  }
  return false;
}

function friendlyError(code: string): string {
  switch (code) {
    case 'auth/email-already-in-use':
      return 'This email is already registered. Please check your password.';
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
  const { isAuthModalOpen, closeAuthModal, setSpotlightCreateForm, refreshSession, modalReason } = useAuth();
  const { language } = useLanguage();
  const tr = translations.auth;
  const router = useRouter();
  const pathname = usePathname();

  // Contextual heading/subtitle for why the modal was opened.
  const copy = {
    login:        { title: tr.loginTitle,        subtitle: tr.loginSubtitle },
    addChart:     { title: tr.addChartTitle,     subtitle: tr.addChartSubtitle },
    pendingChart: { title: tr.pendingChartTitle, subtitle: tr.pendingChartSubtitle },
    insights:     { title: tr.insightsTitle,     subtitle: tr.insightsSubtitle },
  }[modalReason];

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!isAuthModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    const current = auth.currentUser;
    try {
      if (current?.isAnonymous) {
        // Guest creating an account → link the credential so the UID (and all guest
        // profiles) carry over. No "claim" step needed.
        const credential = EmailAuthProvider.credential(email, password);
        try {
          await linkWithCredential(current, credential);
        } catch (linkErr: any) {
          if (['auth/email-already-in-use', 'auth/credential-already-in-use'].includes(linkErr.code)) {
            // Email belongs to an existing account → sign into it, then migrate this guest's
            // profiles over. Capture the anon token first to prove control of the anon UID.
            const anonIdToken = await current.getIdToken();
            await signInWithEmailAndPassword(auth, email, password); // throws on wrong password
            // Move the guest's charts to this account, retrying transient failures behind the
            // scenes. Only surface an error if every attempt fails. Sign-in still succeeds.
            const migrated = await migrateGuestProfiles(anonIdToken);
            if (!migrated) {
              reportClientError({
                context: 'profile_migrate',
                uid: auth.currentUser?.uid,
                message: 'Profile migration failed after retries',
              });
              toast.error(tr.migrateFailed[language]);
            }
          } else {
            throw linkErr;
          }
        }
      } else {
        // No anonymous session (unexpected) → plain sign-in.
        await signInWithEmailAndPassword(auth, email, password);
      }
    } catch (err: any) {
      setError(friendlyError(err.code));
      setSubmitting(false);
      return;
    }

    // Re-mint the session cookie with the now-permanent identity before any navigation. If it
    // can't be established even after retries, keep the modal open with an error instead of
    // routing into a page the SSR would bounce; the user can hit Continue to retry.
    if (!(await refreshSession())) {
      setError(tr.sessionError[language]);
      setSubmitting(false);
      return;
    }

    // If this sign-in was triggered by a chart held pending on the landing form, that form's
    // auto-submit will create the chart and navigate. Stand down so we don't fire a competing
    // redirect (which could land them on the wrong profile or drop the pending chart).
    if (modalReason === 'pendingChart') {
      handleClose();
      return;
    }

    // Auth succeeded — route based on whether the user already has any charts.
    try {
      const idToken = await auth.currentUser?.getIdToken();
      if (idToken) {
        const res = await fetch('/api/profiles', {
          headers: { Authorization: `Bearer ${idToken}` },
        });
        if (res.ok) {
          const profiles = await res.json();
          handleClose();
          if (profiles.length === 0) {
            // Brand-new user with no charts → spotlight the landing-page form so they
            // know the next step. Redirect home first if they signed up elsewhere.
            setSpotlightCreateForm(true);
            if (pathname !== '/') router.push('/');
            return;
          }
          // Existing user landing from home → jump straight to their latest chart.
          if (pathname === '/') router.push(`/profile/${profiles[0].profileId}`);
          return;
        }
      }
    } catch {
      // Non-fatal — fall through to close
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
            {copy.title[language]}
          </span>
        </div>

        {/* Form body */}
        <form onSubmit={handleSubmit} style={{ padding: '12px 28px 28px' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '12px' }}>
            <Image src="/straight_huat_life_logo_svg.svg" alt="Huat Life" width={288} height={72} style={{ height: '72px', width: 'auto' }} />
          </div>

          <p style={{
            textAlign: 'center', fontSize: '14px', color: '#666',
            marginBottom: '20px', fontFamily: 'Noto Serif, serif', lineHeight: 1.4,
          }}>
            {copy.subtitle[language]}
          </p>

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
        </form>
      </div>
    </div>
  );
}
