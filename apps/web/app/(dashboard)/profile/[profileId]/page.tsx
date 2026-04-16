import { findProfile } from '@/lib/profilesDb';
import { fetchNatalChart } from '@/lib/fastApiClient';
import ProfilePageClient from './ProfilePageClient';

export default async function ProfilePage({ params }: { params: Promise<{ profileId: string }> }) {
  const { profileId } = await params;

  const profileRecord = findProfile(profileId);
  if (!profileRecord) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500">Profile not found</p>
      </div>
    );
  }

  let chartData: any = null;
  try {
    const chart = await fetchNatalChart(profileRecord.birthData);
    chartData = chart.data;
  } catch (error) {
    console.error('Error fetching chart:', error);
  }

  return <ProfilePageClient profileRecord={profileRecord} chartData={chartData} />;
}
