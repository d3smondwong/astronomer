'use client';

/**
 * Dashboard error boundary.
 *
 * Catches throws from every page under (dashboard) — most importantly the fatal chart
 * load in profile/[profileId]/page.tsx. Because error.tsx wraps its segment's page but
 * NOT the layout it renders inside, this renders within DashboardShell: the sidebar
 * and chrome survive, only the content area is replaced.
 *
 * useLanguage()/useAuth() are safe here for the same reason — the providers are above.
 */

import { useEffect, useTransition } from 'react';
import { useRouter } from 'next/navigation';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';
import { reportClientError } from '@/lib/errorReporter';
import ErrorState from '@/components/ErrorState';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const { language } = useLanguage();
  const tr = translations.error;
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  // Keyed on `error` so a repeat render doesn't re-report the same failure.
  useEffect(() => {
    reportClientError({
      context: 'error_boundary',
      boundary: 'dashboard',
      message: error.message,
      digest: error.digest,
    });
  }, [error]);

  /**
   * router.refresh() BEFORE reset() is load-bearing, not belt-and-braces.
   *
   * reset() only re-renders the boundary's children on the client; the RSC payload for
   * this segment is still the cached error, so the page would re-throw immediately and
   * the button would look broken. refresh() refetches the payload; reset() then clears
   * the boundary. Both inside startTransition so isPending can disable the button and
   * users can't stack retries against a still-down backend.
   */
  const retry = () => {
    startTransition(() => {
      router.refresh();
      reset();
    });
  };

  return (
    <ErrorState
      title={tr.chartTitle[language]}
      body={tr.chartBody[language]}
      // Chart-specific label, not the generic `retry` used by the root boundary.
      actionLabel={tr.regenerateChart[language]}
      onAction={retry}
      digest={error.digest}
      refIdLabel={tr.refId[language]}
      isPending={isPending}
    />
  );
}
