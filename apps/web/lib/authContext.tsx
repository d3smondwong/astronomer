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

/**
 * Re-mint the session cookie at most once an hour per identity.
 *
 * Only freshness depends on this value, never correctness — an identity change always mints
 * regardless of it. It exists because the cookie lasts 14 days (lib/session.ts) and re-minting
 * on activity is the only thing that keeps it alive: skip forever and an active user's cookie
 * expires around day 15, after which getSessionUser() returns null and the profile page
 * redirects them off their own chart. One hour matches Firebase's token-refresh cadence and
 * leaves that 14-day ceiling a wide margin.
 */
const MINT_TTL_MS = 60 * 60 * 1000;

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

export function AuthProvider({
  children,
  /**
   * Identity the SERVER tree was actually rendered for, as `uid:isAnonymous` (null when
   * the request carried no session cookie). Supplied by app/layout.tsx from the cookie,
   * and refreshed automatically whenever the server tree re-renders.
   */
  serverIdentity,
}: {
  children: ReactNode;
  serverIdentity: string | null;
}) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [modalConfig, setModalConfig] = useState<ModalConfig>({});
  const [spotlightCreateForm, setSpotlightCreateForm] = useState(false);

  // Mirror the prop into a ref so the long-lived onIdTokenChanged callback below (registered
  // once, with [] deps) reads the CURRENT value instead of the one captured at mount.
  //
  // This is not the latch that caused the 404 refresh loop. That one accumulated state
  // ("have I refreshed yet?") and so was destroyed by a remount, re-arming the loop. This
  // ref only ever mirrors a prop — it is re-derived from server state on every render, so a
  // remount reinitialises it to the correct value rather than a blank one.
  const serverIdentityRef = useRef(serverIdentity);
  serverIdentityRef.current = serverIdentity;

  /**
   * Last successful mint, so a repeat sync for the same identity can skip the round-trip.
   *
   * This IS memory, which the comment above warns against — but the failure modes are
   * opposite. Losing the old "already refreshed" latch caused an infinite refresh loop
   * (fail-dangerous). Losing this one causes a single redundant mint, which is exactly what
   * this code did before the ref existed (fail-safe). A remount therefore degrades to the
   * previous behaviour, never to a loop.
   */
  const lastMintRef = useRef<{ identity: string; at: number } | null>(null);

  /** In-flight sync, so concurrent callers for the same identity share one round-trip. */
  const inFlightRef = useRef<{ identity: string; promise: Promise<boolean> } | null>(null);

  /**
   * Mint/refresh the session cookie, then re-render the server tree if the server and the
   * client currently disagree about who the user is.
   *
   * Server Components read identity from the cookie, but the cookie is established
   * asynchronously *after* first paint — so a server-rendered tree (the dashboard sidebar)
   * would otherwise render for "no session" and never update. router.refresh() re-runs it
   * once the cookie lands.
   *
   * WHY A COMPARISON RATHER THAN A "already synced" FLAG: a flag is memory, and memory dies
   * with the component. When the tree remounted (as it does on a 404 route) the flag reset,
   * the sync looked un-done, and this refreshed forever — an endless
   * 404 → POST /api/auth/session → 404 loop. Comparing server identity against client
   * identity is a convergence condition, not memory: once a refresh lands, the server holds
   * the cookie, the two agree, and the condition is false no matter how many times this
   * component is torn down and rebuilt.
   *
   * Keyed on `uid:isAnonymous`, not uid alone: linkWithCredential (the common guest→account
   * upgrade) preserves the uid while flipping isAnonymous, and that transition changes what
   * the server should render. Without the key, the hourly silent token refresh would re-render
   * the whole tree every hour for nothing.
   */
  const syncSession = (u: User): Promise<boolean> => {
    const identity = `${u.uid}:${u.isAnonymous}`;

    // Share an in-flight sync for the SAME identity rather than starting a second.
    // linkWithCredential wakes the onIdTokenChanged listener at the same moment AuthModal
    // awaits refreshSession(); both want the identical cookie, milliseconds apart — too
    // close for the freshness check below to have recorded anything yet.
    const inFlight = inFlightRef.current;
    if (inFlight && inFlight.identity === identity) return inFlight.promise;

    const promise = (async () => {
      // Skip the mint when we already minted THIS identity recently.
      //
      // Keyed on identity, never on time alone: both refreshSession() callers run
      // immediately after an identity change, and a time-only check would return true while
      // the cookie still held the outgoing uid — the profile page's ownership gate would
      // then redirect the owner off their own chart. Their contract is "the cookie matches
      // the current client identity", which an identity-keyed skip satisfies.
      //
      // This is what removes the wasted mint during a guest→account upgrade: Firebase fires
      // onIdTokenChanged twice, and the first fire still reports isAnonymous=true — an
      // identity that already has a valid cookie and is superseded ~13ms later. That mint
      // also RACED the permanent one (retry backoff could land it last, stamping a stale
      // "still a guest" cookie), so dropping it removes the race rather than ordering it.
      const last = lastMintRef.current;
      const isFresh = last !== null && last.identity === identity && Date.now() - last.at < MINT_TTL_MS;

      if (!isFresh) {
        const ok = await establishSessionCookie(u);
        if (!ok) return false;
        lastMintRef.current = { identity, at: Date.now() };
      }

      // Runs on BOTH paths, including the skip: a fresh cookie the server has not yet
      // rendered for still needs the tree re-rendered, or the sidebar never updates.
      if (serverIdentityRef.current !== identity) {
        // Optimistically record what the refresh is about to make true. Without this a second
        // token event arriving before the server re-render completes would fire a duplicate
        // refresh; the next server render overwrites it with the authoritative value anyway.
        serverIdentityRef.current = identity;
        router.refresh();
      }
      return true;
    })();

    inFlightRef.current = { identity, promise };
    void promise.finally(() => {
      // Only clear if still ours — a newer identity may already have replaced the entry.
      if (inFlightRef.current?.promise === promise) inFlightRef.current = null;
    });

    return promise;
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
