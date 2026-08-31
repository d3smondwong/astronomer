'use client';

/**
 * PillarDetailPanel — the expanded reading for one pillar, opened by clicking its
 * PillarCard. Rendered full-width beneath the four-pillar grid as a vertical stack
 * of row cards: a fixed label gutter on the left, the values flowing on the right.
 *
 * The first card restates 天干 / 地支 horizontally (indigo-bordered, colour-matched
 * to the open card above) so the panel reads on its own, and so the rooting bar,
 * void chips and 化气格 badge get room the narrow grid card cannot give them. The
 * caret on its top edge points at the selected column — see .pillar-caret in
 * styles/components.css, which reads the two --pillar-col-* custom properties.
 *
 * Because exactly one pillar's panel exists at a time, none of the grid's
 * row-alignment placeholders are needed here: absent values render as a plain
 * em-dash and the 神煞 card is omitted outright.
 */
import { useEffect } from 'react';
import { X } from 'lucide-react';
import { ELEMENT_ICONS, ELEMENT_EN, ELEMENT_COLOR } from '@/lib/elements';
import { type LifeStageInfo, type NaYinInfo, type VoidInfo, type VoidStatus } from '@/types/baziLibraryTypes';
import { translations } from '@/lib/translations';
import {
  type PillarKey,
  STEM_ELEMENT, BRANCH_ELEMENT, GAN_LABELS, GAN_LABELS_CH, ZHI_LABELS, ZHI_LABELS_CH,
  ROOTING_STYLES, VOID_CATEGORY_COLORS, SHEN_SHA_LABELS,
  GUTTER_LABEL_CLS, SUB_LABEL_CLS, GLYPH_LG_CLS, GLYPH_MD_CLS, CAPTION_CLS,
  ElementCaption, TenGodCard, HiddenTenGodCard,
} from './pillarPresentation';

/**
 * One row: label gutter + flexing value area. Stacks the gutter above the values on
 * narrow screens. Rows carry their own vertical padding; the separators between them
 * are drawn by the parent's divide-y so the card has no trailing rule.
 */
function DetailRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col items-start gap-1.5 py-3.5 sm:flex-row sm:items-center sm:gap-5">
      <span className={`${GUTTER_LABEL_CLS} sm:w-24 sm:shrink-0`}>{label}</span>
      <div className="flex-1 min-w-0 w-full flex flex-wrap items-center gap-x-6 gap-y-3">
        {children}
      </div>
    </div>
  );
}

export default function PillarDetailPanel({
  pillarLabel,
  pillar,
  columnIndex,
  lifeStages,
  naYin,
  xunKong,
  voidStatus,
  shenSha,
  tianGanHua,
  huaPartners,
  language,
  onClose,
}: {
  pillarKey: PillarKey;
  pillarLabel: string;
  pillar: any;
  columnIndex: number;
  lifeStages?: { xingYun: LifeStageInfo | null; ziZuo: LifeStageInfo | null } | null;
  naYin?: NaYinInfo | null;
  xunKong?: VoidInfo | null;
  voidStatus: VoidStatus;
  shenSha?: { 名称: string; 来源: string; 解读?: string }[];
  tianGanHua?: { 元素: string; 原五行: string; label: string };
  huaPartners?: { pillar: string; char: string }[];
  language: 'en' | 'ch';
  onClose: () => void;
}) {
  const tr = translations.profile;

  // Escape closes the panel — the card keeps focus, so the listener sits on the document.
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  const heavenlyChar = pillar?.天干?.天干;
  const earthlyChar = pillar?.地支?.地支;
  const stemElement = STEM_ELEMENT[heavenlyChar];
  const branchElement = BRANCH_ELEMENT[earthlyChar];

  const stemLabel = language === 'en'
    ? (GAN_LABELS[heavenlyChar] ?? heavenlyChar)
    : (GAN_LABELS_CH[heavenlyChar] ?? heavenlyChar);
  const branchLabel = language === 'en'
    ? (ZHI_LABELS[earthlyChar] ?? earthlyChar)
    : (ZHI_LABELS_CH[earthlyChar] ?? earthlyChar);

  const 化气格变化 = pillar?.化气格变化;
  const hiddenStemPairs = [
    { stem: pillar?.藏干?.本气?.天干, tenGod: pillar?.藏干?.本气?.十神, oldTenGod: 化气格变化?.原藏干十神?.本气 },
    { stem: pillar?.藏干?.中气?.天干, tenGod: pillar?.藏干?.中气?.十神, oldTenGod: 化气格变化?.原藏干十神?.中气 },
    { stem: pillar?.藏干?.余气?.天干, tenGod: pillar?.藏干?.余气?.十神, oldTenGod: 化气格变化?.原藏干十神?.余气 },
  ].filter((pair) => pair.stem != null && pair.stem !== '无') as { stem: string; tenGod: string | null; oldTenGod?: string }[];

  const QI_LABELS = [tr.primaryQi[language], tr.middleQi[language], tr.residualQi[language]];

  const rootingCfg = pillar?.天干?.根基强度 ? ROOTING_STYLES[pillar.天干.根基强度] : undefined;
  const oldStemTenGod = 化气格变化?.原天干十神;
  const stemTenGodChanged =
    oldStemTenGod != null && oldStemTenGod !== '' && oldStemTenGod !== pillar?.天干?.十神;

  const uniqueShenSha = (shenSha ?? []).filter(
    (star, idx, arr) => arr.findIndex((s) => s.名称 === star.名称) === idx,
  );

  return (
    <section
      id="pillar-detail-panel"
      role="region"
      aria-label={`${pillarLabel} — ${tr.pillarDetails[language]}`}
      className="pillar-detail-panel relative mt-3 rounded-xl border border-ink-indigo/35 bg-parchment px-5 py-1.5 pr-10"
    >
      <span
        className="pillar-caret"
        style={{
          '--pillar-col-4': columnIndex,
          '--pillar-col-2': columnIndex % 2,
        } as React.CSSProperties}
      />
      <button
        type="button"
        onClick={onClose}
        aria-label={tr.closeDetails[language]}
        className="absolute top-2.5 right-2.5 inline-flex items-center justify-center rounded-md p-1 text-gold-deep/50 hover:text-gold-deep hover:bg-gold-deep/8 cursor-pointer"
      >
        <X className="w-4 h-4" />
      </button>

      <div className="divide-y divide-gold-deep/12">
        {/* HEAVENLY STEM */}
        <DetailRow label={tr.heavenlyStem[language]}>
          {/* Glyph, element caption, ten god and rooting stack vertically, mirroring
              the collapsed card's arrangement. */}
          <span className="inline-flex flex-col items-center gap-2">
            <span className={GLYPH_LG_CLS}>{heavenlyChar}</span>
            {tianGanHua ? (() => {
              const OldIcon = tianGanHua.原五行 ? ELEMENT_ICONS[tianGanHua.原五行] : null;
              const NewIcon = tianGanHua.元素 ? ELEMENT_ICONS[tianGanHua.元素] : null;
              const combinedLabel = language === 'en'
                ? `${stemLabel.split(' ')[0]} ${ELEMENT_EN[tianGanHua.元素] ?? tianGanHua.元素}`
                : `${stemLabel[0]}${tianGanHua.元素}`;
              return (
                <span className="flex items-center gap-1 text-[13px] text-bronze-muted italic">
                  <span className="inline-flex items-center gap-[3px] opacity-55">
                    {OldIcon && <OldIcon style={{ fontSize: 13, color: ELEMENT_COLOR[tianGanHua.原五行] }} />}
                    <span>{stemLabel}</span>
                  </span>
                  <span className="mx-0.5 opacity-45">→</span>
                  <span className="inline-flex items-center gap-[3px]">
                    {NewIcon && <NewIcon style={{ fontSize: 13, color: ELEMENT_COLOR[tianGanHua.元素] }} />}
                    <span>{combinedLabel}</span>
                  </span>
                </span>
              );
            })() : (
              <ElementCaption element={stemElement} label={stemLabel} />
            )}

            {pillar?.天干?.十神 && (
              stemTenGodChanged ? (
                <span className="inline-flex items-center gap-1.5">
                  <TenGodCard value={oldStemTenGod!} language={language} dimmed />
                  <span className="opacity-45 text-[13px] text-bronze-muted">→</span>
                  <TenGodCard value={pillar.天干.十神} language={language} />
                </span>
              ) : (
                <TenGodCard value={pillar.天干.十神} language={language} />
              )
            )}

            {rootingCfg && (
              <span
                className="inline-block text-[11px] italic px-2.5 py-0.5"
                style={{ color: rootingCfg.color, borderLeft: `3px solid ${rootingCfg.color}`, background: rootingCfg.bg }}
              >
                {language === 'en' ? tr[rootingCfg.trKey][language] : pillar.天干.根基强度}
              </span>
            )}
          </span>
        </DetailRow>

        {/* EARTHLY BRANCH — glyph, element caption, then any 空亡 conditions, stacked */}
        <DetailRow label={tr.earthlyBranch[language]}>
          <span className="inline-flex flex-col items-center gap-2">
            <span className={`${GLYPH_LG_CLS} font-bold opacity-80`}>{earthlyChar}</span>
            <ElementCaption element={branchElement} label={branchLabel} />
            {voidStatus.conditions.map((c, i) => {
              const tone = VOID_CATEGORY_COLORS[c.category] ?? VOID_CATEGORY_COLORS.mutual;
              return (
                <span
                  key={i}
                  className="inline-block text-[11px] italic px-2.5 py-0.5"
                  style={{ color: tone.color, borderLeft: `3px solid ${tone.color}`, background: tone.bg }}
                >
                  {language === 'en' ? c.label.en : c.label.ch}
                </span>
              );
            })}
          </span>
        </DetailRow>

        {/* 化气格 — the stem combination that relabelled this pillar */}
        {tianGanHua && (
          <DetailRow label={tr.stemCombination[language]}>
            <span className="inline-block text-xs font-zh-sans not-italic text-info-blue/85 bg-info-blue/8 border border-dashed border-info-blue/50 rounded-[20px] px-2 py-px whitespace-nowrap leading-[1.6]">
              {tianGanHua.label}
            </span>
            {(huaPartners ?? []).map((p) => (
              <span key={p.pillar} className="inline-flex items-center gap-1.5 text-[13px] text-bronze-muted/75 italic">
                <span>{p.pillar}</span>
                <span className="font-zh text-lg not-italic text-bronze-muted">{p.char}</span>
              </span>
            ))}
          </DetailRow>
        )}

        {/* ── HIDDEN STEMS ── */}
        <DetailRow label={tr.hiddenStems[language]}>
          {hiddenStemPairs.length > 0 ? (
            hiddenStemPairs.map(({ stem, tenGod, oldTenGod }, idx) => {
              const hiddenChanged = oldTenGod != null && oldTenGod !== '' && oldTenGod !== tenGod;
              return (
                <div key={idx} className="flex flex-col items-center gap-2">
                  <span className={SUB_LABEL_CLS}>{QI_LABELS[idx]}</span>
                  <span className={GLYPH_MD_CLS}>{stem}</span>
                  <ElementCaption
                    element={STEM_ELEMENT[stem]}
                    label={language === 'en' ? (GAN_LABELS[stem] || stem) : (GAN_LABELS_CH[stem] || stem)}
                    size="sm"
                  />
                  {tenGod && (
                    hiddenChanged ? (
                      <span className="inline-flex items-center gap-1">
                        <HiddenTenGodCard value={oldTenGod!} language={language} dimmed />
                        <span className="opacity-45 text-[13px] text-bronze-muted">→</span>
                        <HiddenTenGodCard value={tenGod} language={language} />
                      </span>
                    ) : (
                      <HiddenTenGodCard value={tenGod} language={language} />
                    )
                  )}
                </div>
              );
            })
          ) : (
            <p className="text-xs text-bronze-muted opacity-45 m-0">{tr.noneLabel[language]}</p>
          )}
        </DetailRow>

        {/* ── VOID BRANCH PAIRS ── */}
        <DetailRow label={tr.voidBranchPairs[language]}>
          {xunKong ? (
            <>
              <span className={GLYPH_MD_CLS}>{xunKong.chinese}</span>
              {language === 'en' && xunKong.english && <p className={CAPTION_CLS}>{xunKong.english}</p>}
            </>
          ) : (
            <p className="text-xl font-bold text-bronze-muted opacity-45 m-0">—</p>
          )}
        </DetailRow>

        {/* ── 12 LIFE STAGES ── */}
        <DetailRow label={tr.twelveLifeStages[language]}>
          <div className="flex items-center gap-3">
            <span className={SUB_LABEL_CLS}>{tr.dayMasterRef[language]}</span>
            {lifeStages?.xingYun ? (
              <>
                <span className={GLYPH_MD_CLS}>{lifeStages.xingYun.chinese}</span>
                {language === 'en' && lifeStages.xingYun.english && (
                  <p className={CAPTION_CLS}>{lifeStages.xingYun.english}</p>
                )}
              </>
            ) : (
              <span className="text-xl font-bold text-bronze-muted opacity-45">—</span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <span className={SUB_LABEL_CLS}>{tr.pillarStemRef[language]}</span>
            {lifeStages?.ziZuo ? (
              <>
                <span className={GLYPH_MD_CLS}>{lifeStages.ziZuo.chinese}</span>
                {language === 'en' && lifeStages.ziZuo.english && (
                  <p className={CAPTION_CLS}>{lifeStages.ziZuo.english}</p>
                )}
              </>
            ) : (
              <span className="text-xl font-bold text-bronze-muted opacity-45">—</span>
            )}
          </div>
        </DetailRow>

        {/* ── NA YIN ── */}
        <DetailRow label={tr.naYin[language]}>
          {naYin ? (
            <>
              <span className={GLYPH_MD_CLS}>{naYin.chinese}</span>
              {language === 'en' && naYin.english && <p className={CAPTION_CLS}>{naYin.english}</p>}
            </>
          ) : (
            <p className="text-xl font-bold text-bronze-muted opacity-45 m-0">—</p>
          )}
        </DetailRow>

        {/* ── SHEN SHA — omitted entirely when this pillar carries none ── */}
        {uniqueShenSha.length > 0 && (
          <DetailRow label={tr.shenSha[language]}>
            {uniqueShenSha.map((star, idx) => (
              <div
                key={idx}
                className="flex flex-col items-center bg-info-blue/7 border border-info-blue/28 rounded-lg px-2.5 py-1 whitespace-nowrap"
              >
                <span className="font-zh text-2xl font-normal text-bronze-muted leading-[1.4]">
                  {star.名称}
                </span>
                {language === 'en' && SHEN_SHA_LABELS[star.名称] && (
                  <span className="text-[13px] text-bronze-muted/55 leading-snug mt-1">
                    {SHEN_SHA_LABELS[star.名称]}
                  </span>
                )}
              </div>
            ))}
          </DetailRow>
          )}
      </div>
    </section>
  );
}
