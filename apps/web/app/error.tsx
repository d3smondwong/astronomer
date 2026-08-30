'use client';

/**
 * Root error boundary — covers everything OUTSIDE the (dashboard) group, which today
 * means the (marketing) group: the landing page, and pricing/about as they land.
 *
 * Not redundant with (dashboard)/error.tsx: route groups are real segments for
 * boundary purposes, so a throw in (marketing)/page.tsx or LandingPageClient is
 * invisible to the dashboard boundary. Without this file such a throw would escalate
 * all the way to global-error.tsx, and a recoverable client bug on the front door
 * would blow away the root layout, providers and chrome.
 *
 * It stays HERE rather than moving into (marketing)/ so it also remains the catch-all
 * for anything at the root — a boundary inside the group would cover only the group.
 * Route groups don't block inheritance, so (marketing) is covered either way.
 */

import { useEffect, useTransition } from 'react';
import { useRouter } from 'next/navigation';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';
import { reportClientError } from '@/lib/errorReporter';
import ErrorState from '@/components/ErrorState';

export default function RootError({
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

  useEffect(() => {
    reportClientError({
      context: 'error_boundary',
      boundary: 'root',
      message: error.message,
      digest: error.digest,
    });
  }, [error]);

  // See the ordering note in (dashboard)/error.tsx — refresh() then reset().
  const retry = () => {
    startTransition(() => {
      router.refresh();
      reset();
    });
  };

  return (
    <ErrorState
      title={tr.pageTitle[language]}
      body={tr.pageBody[language]}
      actionLabel={tr.retry[language]}
      onAction={retry}
      digest={error.digest}
      refIdLabel={tr.refId[language]}
      isPending={isPending}
    />
  );
}
