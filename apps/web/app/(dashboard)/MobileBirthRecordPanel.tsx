'use client';

/**
 * MobileBirthRecordPanel — frame 5b. Drops beneath the chip strip when the selected
 * chip is tapped; the strip itself does not move and nothing above it reflows.
 *
 * This replaces the midnight-navy header card on phones (that card is hidden below md),
 * which is why the TST explanation is rendered as static helper text here rather than as
 * the desktop header's Tooltip — `cursor-help` has no touch equivalent, so on a phone the
 * explanation was simply unreachable.
 *
 * `Edit profile` is deliberately absent: there is no update path in the codebase (only
 * deleteProfileAction; create is POST /api/chart), so the row would be a dead control.
 *
 * Delete lives here as an always-visible row. In the sidebar it is `opacity-0
 * group-hover:opacity-60` — invisible but tappable on touch, which is worse than hidden.
 */

import { Popconfirm } from 'antd';
import { Trash2 } from 'lucide-react';
import dayjs from 'dayjs';
import localizedFormat from 'dayjs/plugin/localizedFormat';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';
import { toDisplayProfile } from '@/lib/profileDisplay';
import { type ProfileRecord } from '@/types/profile';

dayjs.extend(localizedFormat);

interface MobileBirthRecordPanelProps {
  profile: ProfileRecord;
  onDelete: () => void;
  /** Shows an inline failure notice; the row stays in the list. */
  deleteFailed: boolean;
}

export default function MobileBirthRecordPanel({
  profile,
  onDelete,
  deleteFailed,
}: MobileBirthRecordPanelProps) {
  const { language } = useLanguage();
  const tr = translations.sidebar;
  const trProfile = translations.profile;
  const display = toDisplayProfile(profile);

  return (
    <div className="mobile-panel" id="mobile-birth-record">
      <dl className="mobile-panel-fields">
        <dt className="mobile-panel-label">{tr.labelBorn[language]}</dt>
        <dd className="mobile-panel-value">{dayjs(display.birthDate).format('LL')}</dd>

        <dt className="mobile-panel-label">{tr.labelTime[language]}</dt>
        <dd className="mobile-panel-value">
          {display.birthTime}
          {display.usedSolarTime && <span className="mobile-tst-badge">{trProfile.tst[language]}</span>}
        </dd>

        <dt className="mobile-panel-label">{tr.labelPlace[language]}</dt>
        <dd className="mobile-panel-value">{display.birthLocation}</dd>

        <dt className="mobile-panel-label">{tr.labelGender[language]}</dt>
        <dd className="mobile-panel-value">
          {display.gender === 'male' ? tr.labelMale[language] : tr.labelFemale[language]}
        </dd>
      </dl>

      {/* Static, not a tooltip: this panel exists because touch cannot hover. */}
      {display.usedSolarTime && (
        <p className="mobile-panel-note">{trProfile.tstExplain[language]}</p>
      )}

      <div className="mobile-panel-actions">
        <Popconfirm
          title={tr.deleteProfile[language]}
          description={`${tr.deleteProfile[language]} "${display.name}"?`}
          onConfirm={onDelete}
          okText={tr.deleteOk[language]}
          cancelText={tr.deleteCancel[language]}
          okButtonProps={{ danger: true }}
        >
          <button type="button" className="mobile-panel-delete">
            <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
            {tr.deleteOk[language]}
          </button>
        </Popconfirm>
      </div>

      {deleteFailed && (
        <p className="mobile-panel-error">{trProfile.deleteError[language]}</p>
      )}
    </div>
  );
}
