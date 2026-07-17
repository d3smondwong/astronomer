import { redirect } from 'next/navigation';
import { getSessionUser } from '@/lib/session';
import { readProfiles } from '@/lib/profilesDb';
import LandingPageClient from './LandingPageClient';

/**
 * The landing page is the logged-out front door: a returning permanent user with charts has
 * no business reading the marketing copy, so send them straight to their latest chart.
 *
 * This decision belongs here rather than in a client effect. The client knows `user` from
 * context but not the profile list, so it would have to render the whole page, fetch
 * /api/profiles, and only then navigate — a visible flash of the very page we mean to skip.
 * The session cookie gives the server the same answer before a single byte is rendered.
 *
 * Guests stay: every first-time visitor is signed in anonymously (see authContext), so
 * redirecting them would mean nobody ever sees the landing page. The hero, the create form
 * and its sign-up prompts are exactly what an anonymous visitor is here for.
 */
export default async function Home() {
  const session = await getSessionUser();

  let latestProfileId: string | null = null;
  if (session && !session.isAnonymous) {
    try {
      // Ordered createdAt desc, so [0] is the newest — same convention AuthModal uses.
      const profiles = await readProfiles(session.uid);
      latestProfileId = profiles[0]?.profileId ?? null;
    } catch (error) {
      // A Firestore hiccup must not 500 the front door. Degrade to the landing page: the
      // user still has the Header and the form, and the next load retries.
      console.error('Landing redirect: failed to read profiles', error);
    }
  }

  // Outside the try — redirect() signals by throwing, and a catch would swallow it.
  if (latestProfileId) redirect(`/profile/${latestProfileId}`);

  return <LandingPageClient />;
}
