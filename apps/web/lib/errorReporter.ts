/**
 * Client-side error reporter.
 *
 * Fire-and-forget: POSTs a structured error to /api/clientError, which writes it to
 * stdout → Cloud Logging, correlatable by chartKey/uid/requestId alongside the backend
 * logs. Never throws and never blocks the calling flow — a failed report must not break
 * the UI.
 *
 * This is the single migration seam: to move to Sentry later, swap the body of
 * `reportClientError` for `Sentry.captureException(...)` (mapping these fields to
 * tags/context). No call site changes.
 */

export interface ClientErrorReport {
  /** Which flow failed — keep in sync with the backend's event taxonomy. */
  context:
    | 'chart_generation'
    | 'insights_section'
    | 'auth_token'
    | 'profile_migrate'
    | 'profile_delete'
    /** An error.tsx boundary caught a throw. Covers Server Component throws too. */
    | 'error_boundary';
  /** Human-readable error message (err.message or response text). */
  message: string;
  /** Correlation/anchor fields — present when the flow has them (a guest has no uid). */
  requestId?: string;
  chartKey?: string;
  uid?: string;
  profileId?: string;
  section?: string;
  /** HTTP status, when the failure was a non-ok response. */
  status?: number;
  /**
   * Next's `error.digest` — the ONLY join key back to the server log.
   *
   * In production Next replaces `error.message` with a generic string and logs the
   * real stack server-side keyed solely by this digest. Without it a boundary report
   * reads "An error occurred in the Server Components render" and joins to nothing.
   */
  digest?: string;
  /** Which boundary caught it — gives blast radius at a glance. */
  boundary?: 'global' | 'root' | 'dashboard';
}

export function reportClientError(report: ClientErrorReport): void {
  try {
    const body = JSON.stringify({
      ...report,
      url: typeof location !== 'undefined' ? location.href : undefined,
      ts: Date.now(),
    });
    // keepalive lets the request survive page unload / tab close / navigation —
    // exactly the "user closes the tab mid-failure" case.
    void fetch('/api/clientError', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      keepalive: true,
    }).catch(() => {
      /* swallow — the reporter must never surface its own failure */
    });
  } catch {
    /* serialization or environment error — never propagate to the caller */
  }
}
