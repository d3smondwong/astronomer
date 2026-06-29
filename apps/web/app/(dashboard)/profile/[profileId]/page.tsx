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

  let chartData: any = null;
  let insights: InsightsResponse | null = null;
  try {
    // Read the chart from cache; recompute and backfill on a miss (or a keyless legacy profile).
    const cached = chartKey ? await getCachedChart(chartKey) : null;
    if (cached) {
      chartData = cached.data;
    } else {
      const chart = await fetchNatalChart(profileRecord.birthData);
      chartData = chart.data;
      if (!chartKey) chartKey = chart.chart_key; // legacy profile had no stored key
      await setCachedChart(chartKey, chartData);
    }

    // Insights are cached per-profile (not by chartKey), so two profiles with identical
    // birth inputs each get their own interpretation. A miss here means the client will
    // generate them progressively on mount.
    insights = await getCachedInsights(profileId);
  } catch (error) {
    console.error('Error loading chart/insights:', error);
  }

  return <ProfilePageClient profileRecord={profileRecord} chartData={chartData} insights={insights} chartKey={chartKey} />;
}
