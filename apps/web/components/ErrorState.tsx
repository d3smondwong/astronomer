'use client';

/**
 * Full-page error state, shared by every error.tsx boundary and by not-found.tsx.
 *
 * House style is an antd <Alert type="error" showIcon> whose `message` is a single
 * line, with no `description` (see ProfilePageClient's insights alert and
 * BaziProfileForm's form error — the app's only other two). A boundary needs a
 * headline as well, so the TITLE renders as a heading *above* the Alert rather than
 * as `description`: the Alert itself stays one line, exactly like the inline ones.
 *
 * Not usable from app/global-error.tsx — that file renders without ConfigProvider,
 * so antd components there would be unstyled. It inlines its own markup instead.
 */

import { Alert, Button } from 'antd';

interface ErrorStateProps {
  /** Names the artifact that failed, e.g. "Unable to load your chart". */
  title: string;
  /**
   * The recovery action. Must name the action button by its exact visible label, and
   * must NOT claim a position ("below") — antd renders that button inside the Alert on
   * the right, so any positional wording here would be wrong.
   */
  body: string;
  actionLabel: string;
  onAction: () => void;
  /** Next's error.digest — the only string a user can quote that maps to a server log. */
  digest?: string;
  /** Label for the digest line ("Reference" / "错误编号"). */
  refIdLabel?: string;
  /** Disables the action while a retry is in flight, so retries can't stack. */
  isPending?: boolean;
}

export default function ErrorState({
  title,
  body,
  actionLabel,
  onAction,
  digest,
  refIdLabel,
  isPending = false,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16 px-6 text-center">
      <h2 className="font-serif text-xl m-0 text-gold-deep">{title}</h2>

      <Alert
        type="error"
        showIcon
        className="font-serif text-left"
        // antd v6 renamed Alert's `message` prop to `title`; `message` still works but
        // logs a deprecation warning. The app's older Alerts (ProfilePageClient,
        // BaziProfileForm) still pass `message` and warn — worth a follow-up sweep.
        title={body}
        action={
          <Button size="small" danger loading={isPending} onClick={onAction}>
            {actionLabel}
          </Button>
        }
      />

      {/* Omitted entirely without a digest — a bare "Reference:" label helps nobody. */}
      {digest && (
        <p className="text-xs m-0 text-bronze-muted/60 font-serif">
          {refIdLabel}: {digest}
        </p>
      )}
    </div>
  );
}
