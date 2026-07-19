'use client';

/**
 * Route-level loading UI for the profile page — the one route with real server cost
 * (findProfile + getSessionUser, then a possible cache-miss fetchNatalChart).
 *
 * Without it, navigating between profiles leaves the PREVIOUS profile on screen until
 * the new RSC payload lands, which reads as a hang rather than as loading.
 *
 * Reuses InsightsLoading rather than inventing a second loading visual — the 五行 pulse
 * is already this app's loading language.
 *
 * Deliberately not placed at (dashboard)/loading.tsx: that would flash a skeleton on
 * every dashboard navigation, including instant ones like /compatibility.
 */

import { useLanguage } from '@/lib/languageContext';
import InsightsLoading from './InsightsLoading';

export default function ProfileLoading() {
  const { language } = useLanguage();

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <InsightsLoading language={language} />
    </div>
  );
}
