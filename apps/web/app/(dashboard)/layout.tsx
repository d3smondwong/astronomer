/**
 * Dashboard layout — Server Component.
 *
 * Owns exactly one thing: reading the signed-in user's profile list for the sidebar. All
 * interactivity lives in DashboardShell. Because the list is server-rendered, mutations
 * invalidate it via revalidatePath('/', 'layout') rather than patching client state — see
 * app/actions/profiles.ts.
 *
 * Identity comes from the session cookie, which is minted client-side after Firebase auth
 * settles. On a brand-new visitor's first paint there is no cookie yet, so this renders an
 * empty sidebar; AuthProvider calls router.refresh() once the cookie lands (lib/authContext.tsx).
 */

import { readProfiles } from '@/lib/profilesDb';
import { getSessionUser } from '@/lib/session';
import { type ProfileRecord } from '@/types/profile';
import DashboardShell from './DashboardShell';

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await getSessionUser();

  // A Firestore hiccup degrades to an empty sidebar rather than 500ing the whole dashboard —
  // the page inside still renders. Mirrors the same tradeoff in app/(marketing)/page.tsx.
  let profiles: ProfileRecord[] = [];
  try {
    profiles = await readProfiles(session?.uid);
  } catch (error) {
    console.error('Dashboard sidebar: failed to read profiles:', error);
  }

  return <DashboardShell profiles={profiles}>{children}</DashboardShell>;
}
