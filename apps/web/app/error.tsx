'use client';

/**
 * Root error boundary — covers everything OUTSIDE the (dashboard) group, i.e. the
 * landing page.
 *
 * Not redundant with (dashboard)/error.tsx: route groups are real segments for
 * boundary purposes, so a throw in app/page.tsx or LandingPageClient is invisible to
 * the dashboard boundary. Without this file such a throw would escalate all the way to
 * global-error.tsx, and a recoverable client bug on the front door would blow away the
 * root layout, providers and chrome.
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
