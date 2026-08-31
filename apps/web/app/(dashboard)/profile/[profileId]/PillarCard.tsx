'use client';

/**
 * PillarCard — one of the four pillar columns on the profile page.
 *
 * Shows only 天干 + 地支. Everything else (藏干, 旬空, 十二长生, 纳音, 神煞) lives in
 * PillarDetailPanel, which opens beneath the pillar row when a card is clicked.
 *
 * The root element is a <button>: the card has no interactive children, so keyboard
 * activation, focus handling and aria-expanded come for free. Hover / focus / open
 * styling lives in styles/components.css as .pillar-card rules — never as inline
 * style mutation.
 *
 * Two invisible placeholders are deliberate: the maxVoidCount chip loop and the
 * anyHeavenlyStemBadge slot keep the four cards row-aligned when only some pillars
 * carry a void condition or a 化气格 badge.
 */
import { ChevronDown } from 'lucide-react';
import { ELEMENT_ICONS, ELEMENT_EN, ELEMENT_COLOR } from '@/lib/elements';
import { type VoidStatus } from '@/types/baziLibraryTypes';
import { translations } from '@/lib/translations';
import {
  STEM_ELEMENT, BRANCH_ELEMENT, GAN_LABELS, GAN_LABELS_CH, ZHI_LABELS, ZHI_LABELS_CH,
  ROOTING_STYLES, VOID_CATEGORY_COLORS,
  SECTION_LABEL_CLS, GLYPH_LG_CLS, CAPTION_CLS,
  PillarDivider, TenGodCard,
} from './pillarPresentation';

export default function PillarCard({
  pillarLabel,
  pillar,
  isDayMaster = false,
  voidStatus,
  maxVoidCount,
  tianGanHua,
  language,
  anyHeavenlyStemBadge,
  isExpanded,
  onToggle,
}: {
  pillarLabel: string;
  pillar: any;
  isDayMaster?: boolean;
  voidStatus: VoidStatus;
  maxVoidCount: number;
  tianGanHua?: { 元素: string; 原五行: string; label: string };
  language: 'en' | 'ch';
  anyHeavenlyStemBadge: boolean;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const tr = translations.profile;
  const heavenlyChar = pillar?.天干?.天干;
  const earthlyChar = pillar?.地支?.地支;
  const heavenlyName = GAN_LABELS[heavenlyChar] || heavenlyChar;
  const earthlyName = ZHI_LABELS[earthlyChar] || earthlyChar;

  return (
    <button
      type="button"
      onClick={onToggle}
      aria-expanded={isExpanded}
      aria-controls="pillar-detail-panel"
      data-expanded={isExpanded}
      className={`pillar-card relative w-full min-h-full rounded-xl px-5 pt-6 pb-9 flex flex-col items-center text-center cursor-pointer ${
        isDayMaster
          ? 'bg-gold-deep/4 border-2 border-gold-deep/30'
          : 'bg-parchment border border-gold-deep/15'
      }`}
    >
      {/* Day Master Badge */}
      {isDayMaster && (
        <div className="day-master-badge absolute -top-4 left-1/2 -translate-x-1/2 text-white rounded-[20px] px-3.5 py-1 text-[11px] font-semibold uppercase tracking-[0.1em]">
          {tr.dayMasterBadge[language]}
        </div>
      )}

      {/* Pillar Label */}
      <div className="mb-3">
        <p className="text-base font-semibold text-bronze-muted opacity-70 mt-1 mb-0 italic">
          {pillarLabel}
        </p>
      </div>

      {/* HEAVENLY STEM Section */}
      <div className="w-full">
        <label className={SECTION_LABEL_CLS}>{tr.heavenlyStem[language]}</label>
        <div className={`font-zh text-5xl font-semibold leading-none mt-1.5 mb-3 ${isDayMaster ? 'text-gold-deep' : 'text-bronze-muted'}`}>
          {heavenlyChar}
        </div>
        <div className="flex flex-col items-center justify-center gap-[5px]">
          {(() => {
            const stemTransform: { 合化五行: string; 原五行: string; label: string } | undefined =
              tianGanHua ? { 合化五行: tianGanHua.元素, 原五行: tianGanHua.原五行, label: tianGanHua.label } : undefined;
            const origLabel = language === 'en' ? heavenlyName : (GAN_LABELS_CH[heavenlyChar] ?? heavenlyChar);

            if (!stemTransform) {
              const el = STEM_ELEMENT[heavenlyChar];
              const Icon = el ? ELEMENT_ICONS[el] : null;
              const color = el ? ELEMENT_COLOR[el] : undefined;
              return (
                <div className="flex items-center justify-center gap-1">
                  {Icon && <Icon style={{ fontSize: 13, color }} />}
                  <p className={CAPTION_CLS}>{origLabel}</p>
                </div>
              );
            }

            const OldElement = stemTransform.原五行;
            const OldIcon = OldElement ? ELEMENT_ICONS[OldElement] : null;
            const oldColor = OldElement ? ELEMENT_COLOR[OldElement] : undefined;
            const NewElement = stemTransform.合化五行;
            const NewIcon = NewElement ? ELEMENT_ICONS[NewElement] : null;
            const newColor = NewElement ? ELEMENT_COLOR[NewElement] : undefined;
            const combinedLabel = language === 'en'
              ? `${origLabel.split(' ')[0]} ${ELEMENT_EN[NewElement] ?? NewElement}`
              : `${origLabel[0]}${NewElement}`;

            return (
              <div className="flex items-center justify-center gap-1 text-[13px] text-bronze-muted italic">
                <span className="inline-flex items-center gap-[3px] opacity-55">
                  {OldIcon && <OldIcon style={{ fontSize: 13, color: oldColor }} />}
                  <span>{origLabel}</span>
                </span>
                <span className="mx-0.5 opacity-45">→</span>
                <span className="inline-flex items-center gap-[3px]">
                  {NewIcon && <NewIcon style={{ fontSize: 13, color: newColor }} />}
                  <span>{combinedLabel}</span>
                </span>
              </div>
            );
          })()}
          {anyHeavenlyStemBadge && (
            <span
              className="inline-block text-xs font-zh-sans not-italic text-info-blue/85 bg-info-blue/8 border border-dashed border-info-blue/50 rounded-[20px] px-[7px] py-px whitespace-nowrap leading-[1.6]"
              style={{ visibility: tianGanHua ? 'visible' : 'hidden' }}
            >
              {tianGanHua?.label ?? ' '}
            </span>
          )}
        </div>
        {pillar?.天干?.十神 && (() => {
          const oldTenGod = pillar.化气格变化?.原天干十神;
          const hasTransformation = oldTenGod != null && oldTenGod !== '' && oldTenGod !== pillar.天干.十神;

          if (hasTransformation) {
            return (
              <div className="flex flex-row items-center gap-1.5 mt-2 flex-wrap justify-center">
                <TenGodCard value={oldTenGod!} language={language} dimmed />
                <span className="opacity-45 text-[13px] text-bronze-muted">→</span>
                <TenGodCard value={pillar.天干.十神} language={language} />
              </div>
            );
          }

          return (
            <div className="mt-2">
              <TenGodCard value={pillar.天干.十神} language={language} />
            </div>
          );
        })()}
        {pillar?.天干?.根基强度 && (() => {
          const cfg = ROOTING_STYLES[pillar.天干.根基强度];
          if (!cfg) return null;
          return (
            <div className="w-full flex flex-col items-center mt-3">
              <span
                className="block w-3/5 text-[11px] italic text-center px-2.5 py-0.5"
                style={{ color: cfg.color, borderLeft: `3px solid ${cfg.color}`, background: cfg.bg }}
              >
                {language === 'en' ? tr[cfg.trKey][language] : pillar.天干.根基强度}
              </span>
            </div>
          );
        })()}
      </div>

      <PillarDivider />

      {/* EARTHLY BRANCH Section */}
      <div className="w-full">
        <label className={SECTION_LABEL_CLS}>{tr.earthlyBranch[language]}</label>
        <div className={`${GLYPH_LG_CLS} font-bold opacity-80 my-3`}>
          {earthlyChar}
        </div>
        {(() => {
          const branchElement = BRANCH_ELEMENT[earthlyChar];
          const ElemIcon = branchElement ? ELEMENT_ICONS[branchElement] : null;
          const elemColor = branchElement ? ELEMENT_COLOR[branchElement] : undefined;
          return (
            <div className="flex items-center justify-center gap-1">
              {ElemIcon && <ElemIcon style={{ fontSize: 13, color: elemColor }} />}
              <p className={CAPTION_CLS}>
                {language === 'en' ? earthlyName : (ZHI_LABELS_CH[earthlyChar] ?? earthlyChar)}
              </p>
            </div>
          );
        })()}
        <div className="w-full flex flex-col items-center mt-2 gap-2">
          {Array.from({ length: maxVoidCount }).map((_, i) => {
            const c = voidStatus.conditions[i];
            if (!c) return <span key={i} className="block w-2/3 text-[11px] px-2.5 py-0.5 invisible">–</span>;
            const tone = VOID_CATEGORY_COLORS[c.category] ?? VOID_CATEGORY_COLORS.mutual;
            return (
              <span
                key={i}
                className="block w-3/5 text-[11px] italic text-center px-2.5 py-0.5"
                style={{ color: tone.color, borderLeft: `3px solid ${tone.color}`, background: tone.bg }}
              >
                {language === 'en' ? c.label.en : c.label.ch}
              </span>
            );
          })}
        </div>
      </div>

      {/* Expand affordance — mirrors the day-master ribbon on the opposite edge */}
      <span className="pillar-toggle-pill absolute -bottom-3.5 left-1/2 -translate-x-1/2 inline-flex items-center gap-1 rounded-[20px] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.1em] text-gold-deep/70">
        <span className="pillar-toggle-label">{tr.pillarDetails[language]}</span>
        <ChevronDown className="pillar-toggle-icon w-3.5 h-3.5 shrink-0" />
      </span>
    </button>
  );
}
