import { findProfile } from '@/lib/profilesDb';
import { fetchNatalChart, type InsightsResponse } from '@/lib/fastApiClient';
import { getCachedChart, setCachedChart } from '@/lib/chartCacheDb';
import { getCachedInsights } from '@/lib/insightsCacheDb';
import ProfilePageClient from './ProfilePageClient';

export default async function ProfilePage({ params }: { params: Promise<{ profileId: string }> }) {
  const { profileId } = await params;

  const profileRecord = await findProfile(profileId);
  if (!profileRecord) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500">Profile not found</p>
      </div>
    );
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

    if (chartKey) insights = await getCachedInsights(chartKey);
  } catch (error) {
    console.error('Error loading chart/insights:', error);
  }

  return <ProfilePageClient profileRecord={profileRecord} chartData={chartData} insights={insights} chartKey={chartKey} />;
}
