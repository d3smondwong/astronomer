import { redirect } from 'next/navigation';
import { findProfile } from '@/lib/profilesDb';
import { fetchNatalChart, type InsightsResponse } from '@/lib/fastApiClient';
import { getCachedChart, setCachedChart } from '@/lib/chartCacheDb';
import { getCachedInsights } from '@/lib/insightsCacheDb';
import { getSessionUser } from '@/lib/session';
import ProfilePageClient from './ProfilePageClient';

export default async function ProfilePage({ params }: { params: Promise<{ profileId: string }> }) {
  const { profileId } = await params;

  // Authorization lives here in the Server Component (the data-access layer), not in a
  // proxy/middleware — that's the Next.js 16 recommendation. The session cookie (set
  // client-side after anonymous/permanent sign-in) is the server's only view of who is asking
  // during SSR. Missing profile, no session, and non-owner all redirect to the home page with
  // ?login=1 (which pops the auth modal for guests) — identically, so the response never
  // reveals whether a given profile id exists.
  const [profileRecord, session] = await Promise.all([findProfile(profileId), getSessionUser()]);
  if (!profileRecord || !session || session.uid !== profileRecord.userId) {
    redirect('/?login=1');
  }

  // The 八字 key lives on the profile (computed server-side at creation). The frontend
  // can't recompute it (no BaZi math in the browser), so a legacy profile missing the key
  // gets it from the backend, which now returns chart_key alongside the chart.
  let chartKey = profileRecord.chartKey ?? '';

  // FATAL. The chart IS the page — every card below reads from it. Previously a failure
  // here was swallowed and chartData stayed null, which ProfilePageClient optional-chains
  // away into a screen of empty cards with no explanation. It now re-throws to
  // app/(dashboard)/error.tsx, which keeps the sidebar and offers a retry.
  let chartData: any;
  try {
    // Read the chart from cache; recompute and backfill on a miss (or a keyless legacy profile).
    const cached = chartKey ? await getCachedChart(chartKey) : null;
    if (cached) {
      chartData = cached.data;
    } else {
      const chart = await fetchNatalChart(profileRecord.birthData, {
        uid: session.uid,
        profileId,
      });
      chartData = chart.data;
      if (!chartKey) chartKey = chart.chart_key; // legacy profile had no stored key

      // Non-fatal: we already have the chart in hand. A Firestore write hiccup costs a
      // recompute next visit; it must not blank a chart we computed successfully.
      try {
        await setCachedChart(chartKey, chartData);
      } catch (error) {
        console.error('Non-fatal: chart cache write failed', { profileId, chartKey, error });
      }
    }
  } catch (error) {
    // Log then re-throw: the log keeps the full FastApiError (including the raw upstream
    // body) with correlation ids attached, while the client sees only Next's digest.
    console.error('Fatal: chart load failed', { profileId, chartKey, error });
    throw error;
  }

  // NON-FATAL. Insights are cached per-profile (not by chartKey), so two profiles with
  // identical birth inputs each get their own interpretation. A cache miss and a cache
  // *error* look identical to the client — it generates them progressively on mount —
  // so this degrades rather than failing the page.
  let insights: InsightsResponse | null = null;
  try {
    insights = await getCachedInsights(profileId);
  } catch (error) {
    console.error('Non-fatal: insights cache read failed', { profileId, error });
  }

  return <ProfilePageClient profileRecord={profileRecord} chartData={chartData} insights={insights} chartKey={chartKey} />;
}
