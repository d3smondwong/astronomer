'use client';

/**
 * MobileProfileStrip — the phone header. It IS the header: no logo row, no avatar
 * column, no separate name line.
 *
 * The selected chip does two jobs. Tapping a *different* chip switches profile;
 * tapping the *selected* chip (which carries a caret) opens the birth record beneath
 * the strip. One control, two jobs, and the strip never leaves the screen — so
 * switching is always one tap and the header costs the same ~44px either way.
 *
 * The trailing avatar button is the one deviation from the design frames. Sign in /
 * sign out is unreachable on a phone today (`.sidebar-login-btn` is display:none below
 * 1024px), and a 44px strip full of chips has nowhere to put it — so account controls
 * get their own panel behind this button, opening into the same drop-down area.
 *
 * Rendered by DashboardShell and hidden at md+ via CSS (.mobile-topbar); it holds no
 * profile state of its own — the list is the server-rendered prop, and which panel is
 * open lives in the shell so the profile page can hide its tab bar while one is.
 */

import Link from 'next/link';
import { ChevronDown, Plus, User } from 'lucide-react';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';
import { type ProfileRecord } from '@/types/profile';

export type MobilePanel = 'birth' | 'account' | null;

interface MobileProfileStripProps {
  profiles: ProfileRecord[];
  /** null on /compatibility and /ai_oracle_chat — no chip is selected there. */
  activeProfileId: string | null;
  openPanel: MobilePanel;
  onTogglePanel: (panel: Exclude<MobilePanel, null>) => void;
  onAddProfile: () => void;
  /** Signed-in email initial for the account button, or null for a guest. */
  accountInitial: string | null;
}

export default function MobileProfileStrip({
  profiles,
  activeProfileId,
  openPanel,
  onTogglePanel,
  onAddProfile,
  accountInitial,
}: MobileProfileStripProps) {
  const { language } = useLanguage();
  const tr = translations.sidebar;

  return (
    <div className="mobile-strip">
      <div className="mobile-strip-chips">
        {profiles.map((profile) => {
          const isSelected = profile.profileId === activeProfileId;

          // Selected chip: a button that toggles the birth record. Unselected: a link
          // that navigates. Same visual chip, two different elements, because the
          // semantics genuinely differ — one discloses, one moves.
          if (isSelected) {
            return (
              <button
                key={profile.profileId}
                type="button"
                className="profile-chip"
                data-selected="true"
                aria-expanded={openPanel === 'birth'}
                aria-controls="mobile-birth-record"
                onClick={() => onTogglePanel('birth')}
              >
                <span className="profile-chip-name">{profile.name}</span>
                <ChevronDown className="profile-chip-caret w-3.5 h-3.5 shrink-0" aria-hidden="true" />
                <span className="sr-only">
                  {openPanel === 'birth' ? tr.hideBirthRecord[language] : tr.showBirthRecord[language]}
                </span>
              </button>
            );
          }

          return (
            <Link
              key={profile.profileId}
              href={`/profile/${profile.profileId}`}
              className="profile-chip"
              data-selected="false"
            >
              <span className="profile-chip-name">{profile.name}</span>
            </Link>
          );
        })}

        <button
          type="button"
          className="profile-chip-add"
          onClick={onAddProfile}
          aria-label={tr.addProfile[language]}
        >
          <Plus className="w-4 h-4" aria-hidden="true" />
        </button>
      </div>

      <button
        type="button"
        className="mobile-strip-account"
        data-open={openPanel === 'account'}
        aria-expanded={openPanel === 'account'}
        aria-controls="mobile-account-panel"
        aria-label={tr.account[language]}
        onClick={() => onTogglePanel('account')}
      >
        {accountInitial ?? <User className="w-4 h-4" aria-hidden="true" />}
      </button>
    </div>
  );
}
