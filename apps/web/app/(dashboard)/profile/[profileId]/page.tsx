import { findProfile } from '@/lib/profilesDb';
import { fetchNatalChart, type InsightsResponse } from '@/lib/fastApiClient';
import { chartCacheKey } from '@/lib/cacheKey';
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

  const chartKey = profileRecord.chartKey ?? chartCacheKey(profileRecord.birthData);

  let chartData: any = null;
  let insights: InsightsResponse | null = null;
  try {
    // Read the chart from cache; recompute and backfill on a miss (e.g. legacy profiles).
    const cached = await getCachedChart(chartKey);
    if (cached) {
      chartData = cached.data;
    } else {
      const chart = await fetchNatalChart(profileRecord.birthData);
      chartData = chart.data;
      await setCachedChart(chartKey, chartData);
    }

    insights = await getCachedInsights(chartKey);
  } catch (error) {
    console.error('Error loading chart/insights:', error);
  }

  return <ProfilePageClient profileRecord={profileRecord} chartData={chartData} insights={insights} chartKey={chartKey} />;
}
