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
 *
 * Mobile: all four cards stay on one row below 768px, which leaves each about 81px of
 * outer width. The card's own `px-5` was 40px of that, so the horizontal padding
 * collapses to `px-1` and every type size steps down (see the *_CARD_CLS constants in
 * pillarPresentation). Nothing is dropped — labels wrap instead. The `md:` prefixes do
 * this in CSS rather than through useBreakpoint so the first paint is already correct.
 */
import { ChevronDown } from 'lucide-react';
import { ELEMENT_ICONS, ELEMENT_EN, ELEMENT_COLOR } from '@/lib/elements';
import { type VoidStatus } from '@/types/baziLibraryTypes';
import { translations } from '@/lib/translations';
import {
  STEM_ELEMENT, BRANCH_ELEMENT, GAN_LABELS, GAN_LABELS_CH, ZHI_LABELS, ZHI_LABELS_CH,
  ROOTING_STYLES, VOID_CATEGORY_COLORS,
  SECTION_LABEL_CLS, GLYPH_CARD_CLS, CAPTION_CARD_CLS, ELEMENT_ICON_CARD_CLS,
  PillarDivider, TenGodCard,
} from './pillarPresentation';

/**
 * Rooting / void chip. 75% of the card at desktop, full width on a phone (75% of a 68px
 * card is 51px — nothing fits).
 *
 * The width used to be `w-3/5`, which is a pre-existing desktop bug unrelated to the
 * phone layout: at 1100px it left the chip 86.4px of content while 'Moderately Rooted'
 * needs 97px, so that one chip wrapped to two lines (32px) where 'No Root' and 'Deeply
 * Rooted' stayed at one (18px). Every row below it in that card then sat 14px high,
 * which is what opened the gap between the branch caption and the void chip.
 *
 * Why 75% and not a smaller fraction: the longest label needs a fixed 117px (97px of
 * text + 20px padding) while the card's inner width tracks the viewport, so the fraction
 * it demands slides from 100% at 816px through 73.3% at 1024px to 32.8% at 1920px. No
 * single percentage covers every width; 75% is the smallest round one that holds from
 * 1024px up, which is the real desktop range.
 *
 * `min-w-fit` covers what is left — the 816-1023px icon-rail band, where even 85% would
 * not be enough at 900px. There the box grows to its content instead of wrapping, so the
 * short chips stay at 75% and only a long one widens. `max-w-full` keeps it inside the
 * card, and below ~816px not even fit-content fits; the rooting chip adds
 * .pillar-rooting-chip for the reservation covering that (see styles/components.css).
 * The void chips deliberately do not — their labels are shorter, and they are the last
 * element in the card, so their height aligns nothing.
 */
const STATUS_CHIP_CLS = 'pillar-status-chip block w-full md:w-3/4 md:min-w-fit md:max-w-full text-[9px] md:text-[11px] italic text-center px-1 md:px-2.5 py-0.5 leading-tight';

/**
 * Below this width the longest pillar label no longer fits one line, so all four are
 * broken before their qualifier and read as a uniform block. Above it none of them wrap
 * and they stay on one line.
 *
 * Measured, not guessed: at 375px each card is 77.5px outer / 68.2px inner, and at the
 * label's italic 600 11px Noto Serif the four labels need 61.3 / 71.7 / 57.2 / 64.5px.
 * Only 'Month Pillar' overflows, which is why one column used to wrap alone. Solving
 * inner >= 71.7 puts the crossover at ~389px — and with no scrollbar 375px clears it by
 * 0.2px, close enough that font rendering could decide it either way. Forcing the break
 * below 390px takes that coin-flip out of the layout.
 *
 * Truly conditional behaviour ("break only if some column would wrap") cannot be done in
 * CSS: siblings cannot see each other's text metrics, and shorter text in an equal-width
 * box always wraps later. It would need a runtime measurement, which costs a layout pass
 * and a hydration flash for a cosmetic detail.
 */
const LABEL_STACK_CLS = 'max-[389px]:block';

/**
 * Below this width the element captions are broken after their first word on all four
 * cards, so they read as a uniform block ('Yin / Wood', 'Yang / Earth', 'Earth / Ox',
 * 'Earth / Dragon') rather than the two longest wrapping alone. Above it none of them
 * wrap and they stay on one line.
 *
 * Separate constant from LABEL_STACK_CLS because the strings are different lengths and
 * so is the crossover. Measured at 375px: the caption row is 68.2px wide, of which the
 * element icon plus its gap takes 14px, leaving 54.2px for text. At the caption's italic
 * 10px Noto Serif the labels run from 'Earth Ox' (41.9px) to 'Metal Monkey' (66.2px) —
 * so the long ones overflow and the short ones do not. The threshold uses the longest
 * label the tables can produce ('Metal Monkey' / 'Metal Rooster', 66.2px) rather than
 * whichever four this chart happens to have, so it does not shift per chart: text
 * available is cardOuter - 24, and cardOuter is (viewport - 64)/4, giving a crossover at
 * ~425px.
 *
 * No height reservation is needed alongside this. Breaking the text gives every card the
 * same line count at any width, which is what min-height was faking before — and faking
 * it left a one-line caption sitting in a two-line box.
 */
const CAPTION_STACK_CLS = 'max-[424px]:block';

/**
 * Element caption with the conditional break applied. Both label tables are two words
 * (polarity + element for stems, element + animal for branches), so splitting on the
 * first space puts one on each line. Chinese labels are a single 2-glyph word (阴木,
 * 土牛) with no space, so they fall through and stay on one line.
 */
function ElementCaptionText({ label }: { label: string }) {
  const spaceAt = label.indexOf(' ');
  if (spaceAt === -1) return <p className={CAPTION_CARD_CLS}>{label}</p>;
  return (
    <p className={CAPTION_CARD_CLS}>
      <span className={CAPTION_STACK_CLS}>{label.slice(0, spaceAt)}</span>{' '}
      <span className={CAPTION_STACK_CLS}>{label.slice(spaceAt + 1)}</span>
    </p>
  );
}

/* items-start so the element icon sits beside the caption's FIRST line once it breaks;
   at md+ the caption is always one line and the original centring applies. */
const CAPTION_ROW_CLS = 'flex justify-center gap-1 items-start md:items-center';

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
      /* The day master's border is 2px against the others' 1px, so its horizontal
         padding is 1px lighter to compensate: without that its content box is 2px
         narrower than its siblings', and at widths near a wrap threshold that is enough
         to break 'HEAVENLY STEM' onto two lines in this card alone (measured at 440px:
         its caption sat 15px lower than the other three). Both arms therefore resolve to
         the same inner width — outer - 10 on a phone, outer - 42 at md+. */
      className={`pillar-card relative w-full min-h-full rounded-xl pt-4 pb-8 md:pt-6 md:pb-9 flex flex-col items-center text-center cursor-pointer ${
        isDayMaster
          ? 'bg-gold-deep/4 border-2 border-gold-deep/30 px-[3px] md:px-[19px]'
          : 'bg-parchment border border-gold-deep/15 px-1 md:px-5'
      }`}
    >
      {/* Day Master Badge */}
      {isDayMaster && (
        <div className="day-master-badge absolute -top-4 left-1/2 -translate-x-1/2 text-white rounded-[20px] px-1.5 md:px-3.5 py-1 text-[8px] md:text-[11px] font-semibold uppercase tracking-[0.04em] md:tracking-[0.1em] whitespace-nowrap">
          {tr.dayMasterBadge[language]}
        </div>
      )}

      {/* Pillar Label. Under LABEL_STACK_CLS's threshold the qualifier drops to its own
          line on all four cards, so they read as one block ('Year / Month / Day / Hour'
          over a shared 'Pillar') instead of 'Month Pillar' wrapping by itself. Above it
          the spans are inline and the label is one line. No height reservation is needed
          either way: all four take the same number of lines at any given width.
          Whitespace between the spans is collapsed while they are blocks and only counts
          once they go inline. Chinese labels are one 2-glyph word (年柱) — nothing to
          split, so they fall through unchanged. */}
      <div className="mb-3">
        <p className="text-[11px] md:text-base font-semibold text-bronze-muted opacity-70 mt-1 mb-0 italic leading-tight">
          {(() => {
            const spaceAt = pillarLabel.indexOf(' ');
            if (spaceAt === -1) return pillarLabel;
            return (
              <>
                <span className={LABEL_STACK_CLS}>{pillarLabel.slice(0, spaceAt)}</span>{' '}
                <span className={LABEL_STACK_CLS}>{pillarLabel.slice(spaceAt + 1)}</span>
              </>
            );
          })()}
        </p>
      </div>

      {/* HEAVENLY STEM Section */}
      <div className="w-full">
        <label className={SECTION_LABEL_CLS}>{tr.heavenlyStem[language]}</label>
        <div className={`font-zh text-[34px] md:text-5xl font-semibold leading-none mt-1.5 mb-3 ${isDayMaster ? 'text-gold-deep' : 'text-bronze-muted'}`}>
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
                <div className={CAPTION_ROW_CLS}>
                  {Icon && (
                    <span className={ELEMENT_ICON_CARD_CLS}>
                      <Icon style={{ fontSize: 'inherit', color }} />
                    </span>
                  )}
                  <ElementCaptionText label={origLabel} />
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

            // flex-wrap: the old→new pair is four elements wide and does not fit 68px,
            // so on a phone it breaks onto a second line instead of overflowing.
            return (
              <div className="flex flex-wrap items-center justify-center gap-x-1 gap-y-0.5 text-[10px] md:text-[13px] text-bronze-muted italic leading-tight">
                <span className="inline-flex items-center gap-[3px] opacity-55">
                  {OldIcon && (
                    <span className={ELEMENT_ICON_CARD_CLS}>
                      <OldIcon style={{ fontSize: 'inherit', color: oldColor }} />
                    </span>
                  )}
                  <span>{origLabel}</span>
                </span>
                <span className="mx-0.5 opacity-45">→</span>
                <span className="inline-flex items-center gap-[3px]">
                  {NewIcon && (
                    <span className={ELEMENT_ICON_CARD_CLS}>
                      <NewIcon style={{ fontSize: 'inherit', color: newColor }} />
                    </span>
                  )}
                  <span>{combinedLabel}</span>
                </span>
              </div>
            );
          })()}
          {anyHeavenlyStemBadge && (
            <span
              className="inline-block text-[9px] md:text-xs font-zh-sans not-italic text-info-blue/85 bg-info-blue/8 border border-dashed border-info-blue/50 rounded-[20px] px-1 md:px-[7px] py-px whitespace-nowrap leading-[1.6]"
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
                <TenGodCard value={oldTenGod!} language={language} dimmed compact />
                <span className="opacity-45 text-[13px] text-bronze-muted">→</span>
                <TenGodCard value={pillar.天干.十神} language={language} compact />
              </div>
            );
          }

          return (
            <div className="mt-2">
              <TenGodCard value={pillar.天干.十神} language={language} compact />
            </div>
          );
        })()}
        {pillar?.天干?.根基强度 && (() => {
          const cfg = ROOTING_STYLES[pillar.天干.根基强度];
          if (!cfg) return null;
          return (
            <div className="w-full flex flex-col items-center mt-3">
              <span
                className={`${STATUS_CHIP_CLS} pillar-rooting-chip`}
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
        <div className={`${GLYPH_CARD_CLS} font-bold opacity-80 my-3`}>
          {earthlyChar}
        </div>
        {(() => {
          const branchElement = BRANCH_ELEMENT[earthlyChar];
          const ElemIcon = branchElement ? ELEMENT_ICONS[branchElement] : null;
          const elemColor = branchElement ? ELEMENT_COLOR[branchElement] : undefined;
          return (
            <div className={CAPTION_ROW_CLS}>
              {ElemIcon && (
                <span className={ELEMENT_ICON_CARD_CLS}>
                  <ElemIcon style={{ fontSize: 'inherit', color: elemColor }} />
                </span>
              )}
              <ElementCaptionText
                label={language === 'en' ? earthlyName : (ZHI_LABELS_CH[earthlyChar] ?? earthlyChar)}
              />
            </div>
          );
        })()}
        <div className="w-full flex flex-col items-center mt-2 gap-2">
          {Array.from({ length: maxVoidCount }).map((_, i) => {
            const c = voidStatus.conditions[i];
            // The placeholder reserves the same two lines as a real chip, or a card with
            // no void would come out shorter than one with 'Primary Void'.
            if (!c) {
              return (
                <span key={i} className={`${STATUS_CHIP_CLS} invisible`}>
                  –
                </span>
              );
            }
            const tone = VOID_CATEGORY_COLORS[c.category] ?? VOID_CATEGORY_COLORS.mutual;
            return (
              <span
                key={i}
                className={STATUS_CHIP_CLS}
                style={{ color: tone.color, borderLeft: `3px solid ${tone.color}`, background: tone.bg }}
              >
                {language === 'en' ? c.label.en : c.label.ch}
              </span>
            );
          })}
        </div>
      </div>

      {/* Expand affordance — mirrors the day-master ribbon on the opposite edge */}
      <span className="pillar-toggle-pill absolute -bottom-3.5 left-1/2 -translate-x-1/2 inline-flex items-center gap-1 rounded-[20px] px-1.5 md:px-2.5 py-1 text-[8px] md:text-[11px] font-semibold uppercase tracking-[0.04em] md:tracking-[0.1em] text-gold-deep/70">
        <span className="pillar-toggle-label">{tr.pillarDetails[language]}</span>
        <ChevronDown className="pillar-toggle-icon w-3.5 h-3.5 shrink-0" />
      </span>
    </button>
  );
}
