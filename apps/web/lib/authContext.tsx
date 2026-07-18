'use client';

import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import {
  type User,
  onIdTokenChanged,
  signInAnonymously,
  signOut as firebaseSignOut,
} from 'firebase/auth';
import { auth } from './firebaseClient';

/**
 * POST the current user's fresh ID token to mint/refresh the server session cookie.
 * Returns true on success.
 *
 * Session-cookie failures are almost always transient (a network blip, a server cold start, a
 * momentary Auth backend hiccup), so retry a few times with exponential backoff before giving
 * up. The /api/auth/session route collapses every failure to a non-2xx, and the ID token is
 * freshly valid here, so we retry on any failure. A persistent false matters because a
 * missing/stale cookie makes the SSR ownership check bounce the owner off their own pages.
 */
async function establishSessionCookie(u: User): Promise<boolean> {
  const backoffMs = [1000, 3000]; // waits before the 2nd and 3rd attempts → 3 attempts total
  for (let attempt = 0; attempt <= backoffMs.length; attempt++) {
    try {
      const idToken = await u.getIdToken();
      const res = await fetch('/api/auth/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idToken }),
      });
      if (res.ok) return true;
      console.error('Failed to establish session cookie:', res.status);
    } catch (err) {
      console.error('Failed to establish session cookie:', err);
    }
    if (attempt < backoffMs.length) {
      await new Promise((resolve) => setTimeout(resolve, backoffMs[attempt]));
    }
  }
  return false;
}

/** Why the auth modal was opened — drives its contextual copy and post-auth behaviour. */
export type AuthReason = 'login' | 'addChart' | 'pendingChart' | 'insights';

/** Options carried by an openAuthModal() call, scoped to that modal session. */
interface ModalConfig {
  /**
   * Drives the modal's contextual heading/subtitle. 'pendingChart' additionally changes
   * behaviour: AuthModal stands down from its own post-auth routing so the landing form's
   * auto-submit creates the chart and navigates, instead of the two racing.
   */
  reason?: AuthReason;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  /** True when the current user is a guest (Firebase anonymous sign-in). */
  isAnonymous: boolean;
  isAuthModalOpen: boolean;
  /** Why the open modal was triggered — drives contextual copy + post-auth behaviour. */
  modalReason: AuthReason;
  openAuthModal: (config?: ModalConfig) => void;
  closeAuthModal: () => void;
  signOut: () => Promise<void>;
  /** Re-mint the server session cookie from the current user's latest token (after link/sign-in). Returns true on success. */
  refreshSession: () => Promise<boolean>;
  // When a brand-new user signs up with no charts yet, the landing page form is
  // "spotlit" (page darkened except the form) to point them at the next step.
  spotlightCreateForm: boolean;
  setSpotlightCreateForm: (v: boolean) => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  isAnonymous: false,
  isAuthModalOpen: false,
  modalReason: 'login',
  openAuthModal: () => {},
  closeAuthModal: () => {},
  signOut: async () => {},
  refreshSession: async () => false,
  spotlightCreateForm: false,
  setSpotlightCreateForm: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [modalConfig, setModalConfig] = useState<ModalConfig>({});
  const [spotlightCreateForm, setSpotlightCreateForm] = useState(false);
  // Identity the server tree was last re-rendered for, as `uid:isAnonymous`.
  const syncedIdentityRef = useRef<string | null>(null);

  /**
   * Mint/refresh the session cookie, then re-render the server tree if the identity it
   * represents actually changed.
   *
   * Server Components read identity from the cookie, but the cookie is established
   * asynchronously *after* first paint — so a server-rendered tree (the dashboard sidebar)
   * would otherwise render for "no session" and never update. router.refresh() re-runs it
   * once the cookie lands.
   *
   * Keyed on `uid:isAnonymous`, not uid alone: linkWithCredential (the common guest→account
   * upgrade) preserves the uid while flipping isAnonymous, and that transition changes what
   * the server should render. Without the key, the hourly silent token refresh would re-render
   * the whole tree every hour for nothing.
   */
  const syncSession = async (u: User): Promise<boolean> => {
    const ok = await establishSessionCookie(u);
    if (!ok) return false;
    const identity = `${u.uid}:${u.isAnonymous}`;
    if (syncedIdentityRef.current !== identity) {
      syncedIdentityRef.current = identity;
      router.refresh();
    }
    return true;
  };

  useEffect(() => {
    // onIdTokenChanged (not onAuthStateChanged) so that linking a credential onto the
    // anonymous user — which keeps the same UID but flips isAnonymous — is also observed.
    return onIdTokenChanged(auth, async (u) => {
      if (!u) {
        // No session (first visit or just signed out) → create an anonymous one so every
        // visitor owns their guest data. onAuthStateChanged fires again with the anon user.
        try {
          await signInAnonymously(auth);
        } catch (err) {
          console.error('Anonymous sign-in failed:', err);
          setUser(null);
          setLoading(false);
        }
        return;
      }
      setUser(u);
      setLoading(false);
      // Establish/refresh the server session cookie for SSR ownership checks + route gating.
      await syncSession(u);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refreshSession = async (): Promise<boolean> => {
    if (!auth.currentUser) return false;
    return syncSession(auth.currentUser);
  };

  const signOut = async () => {
    // Clear the server cookie, then the client session. onAuthStateChanged(null) will
    // re-establish an anonymous session + cookie afterwards.
    try {
      await fetch('/api/auth/session', { method: 'DELETE' });
    } catch (err) {
      console.error('Failed to clear session cookie:', err);
    }
    await firebaseSignOut(auth);
  };

  const openAuthModal = (config: ModalConfig = {}) => {
    setModalConfig(config);
    setIsAuthModalOpen(true);
  };
  const closeAuthModal = () => {
    setIsAuthModalOpen(false);
    setModalConfig({});
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAnonymous: user?.isAnonymous ?? false,
        isAuthModalOpen,
        modalReason: modalConfig.reason ?? 'login',
        openAuthModal,
        closeAuthModal,
        signOut,
        refreshSession,
        spotlightCreateForm,
        setSpotlightCreateForm,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  return useContext(AuthContext);
}
