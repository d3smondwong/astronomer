'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import { type VoidStatus, type VoidCondition } from '@/types/baziLibraryTypes';
import { type ProfileRecord } from '@/types/profile';
import { toDisplayProfile } from '@/lib/profileDisplay';
// Shapes only — never lib/fastApiClient, which is server-only and reads the backend token.
import { type InsightsResponse, type StructuredSection } from '@/types/api';
import { Alert, Card, Tabs, Button, Popconfirm, Tooltip, Collapse } from 'antd';
import dayjs from 'dayjs';
import localizedFormat from 'dayjs/plugin/localizedFormat';
import { Calendar, Clock, MapPin, User, Trash2 } from 'lucide-react';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';
import { useAuth } from '@/lib/authContext';
import { reportClientError } from '@/lib/errorReporter';
import { deleteProfileAction } from '@/app/actions/profiles';
import { goldAlpha, palette } from '@/lib/theme';
import PillarCard from './PillarCard';
import PillarDetailPanel from './PillarDetailPanel';
import { type PillarKey, PILLAR_ORDER } from './pillarPresentation';
import FiveElementsCard from './FiveElementsCard';
import PillarInteractionsCard from './PillarInteractionsCard';
import DayMasterStrengthCard from './DayMasterStrengthCard';
import FavorableElementsCard from './FavorableElementsCard';
import InsightsLoading from './InsightsLoading';

dayjs.extend(localizedFormat);

/**
 * Tab keys, in display order. The Tabs component is controlled from `?tab=` so a view is
 * addressable: deep-linking to Insights works, reload holds the tab, and Back steps
 * between tabs instead of leaving the page. That matters most on a phone, where the tab
 * bar is the primary way around the chart and Android's back gesture is a system control.
 * 'pillars' is the default and is left out of the URL rather than written as ?tab=pillars.
 */
const TAB_KEYS = ['pillars', 'insights', 'cycles'] as const;
type TabKey = (typeof TAB_KEYS)[number];
const DEFAULT_TAB: TabKey = 'pillars';

const isTabKey = (value: string | null): value is TabKey =>
  value !== null && (TAB_KEYS as readonly string[]).includes(value);

// Ordered insight sections (matches the backend SECTION_REGISTRY) -> title translation key.
const INSIGHT_SECTIONS: { key: string; title: keyof typeof translations.profile }[] = [
  { key: 'personality', title: 'secPersonality' },
  { key: 'family', title: 'secFamily' },
  { key: 'romance', title: 'secRomance' },
  { key: 'career', title: 'secCareer' },
  { key: 'wealth', title: 'secWealth' },
];

// Narratives are plain paragraphs separated by blank lines — render each as a <p>.
const renderProse = (text: string) =>
  text
    .split(/\n{2,}/)
    .map((p) => p.trim())
    .filter(Boolean)
    .map((p, i) => (
      <p key={i} className="mb-3 text-bronze-muted/80 leading-relaxed">
        {p}
      </p>
    ));

type LabelKeyMap = Record<string, keyof typeof translations.profile>;

// Per-section group-key -> heading translation key. A section listed here renders
// as a structured object (labelled groups); everything else renders as prose.
const STRUCTURED_LABEL_KEYS: Record<string, LabelKeyMap> = {
  personality: {
    core: 'personalityCore',
    mind: 'personalityMind',
    drives: 'personalityDrives',
    strengths: 'personalityStrengths',
    weakness: 'personalityWeakness',
  },
  family: {
    roots: 'familyRoots',
    parents: 'familyParents',
    siblings: 'familySiblings',
  },
  romance: {
    partner: 'romancePartner',
    spouse: 'romanceSpouse',
    journey: 'romanceJourney',
    children: 'romanceChildren',
  },
  career: {
    path_to_success: 'careerPathToSuccess',
    highlights: 'careerHighlights',
    challenges: 'careerChallenges',
    advice: 'careerAdvice',
  },
  wealth: {
    sources: 'wealthSources',
    capacity: 'wealthCapacity',
    risks: 'wealthRisks',
    timing: 'wealthTiming',
    strategy: 'wealthStrategy',
  },
};

// Structured sections render as labelled groups of bulleted point/explanation items.
const renderStructured = (
  value: StructuredSection,
  labelKeys: LabelKeyMap,
  language: keyof typeof translations.profile.careerAdvice,
) =>
  Object.entries(value)
    .filter(([, items]) => Array.isArray(items) && items.length > 0)
    .map(([groupKey, items]) => {
      const labelKey = labelKeys[groupKey];
      return (
      <div key={groupKey} className="mb-5 last:mb-0">
        <h4 className="font-serif text-gold-deep mb-2 font-semibold">
          {labelKey ? translations.profile[labelKey][language] : groupKey}
        </h4>
        <ul className="list-disc pl-5 space-y-2">
          {items.map((it, i) => (
            <li key={i} className="text-bronze-muted/80 leading-relaxed">
              <span className="font-semibold">{it.point}</span>
              {it.explanation ? <> — {it.explanation}</> : null}
            </li>
          ))}
        </ul>
      </div>
      );
    });

/* ────────── Four-pillar derivations ──────────
   Pure, chart-shaped helpers at module scope: they used to be re-created inside a
   JSX IIFE on every render, which now matters because clicking a pillar re-renders
   the tab. */

const PILLAR_LABEL_KEY: Record<PillarKey, keyof typeof translations.profile> = {
  年柱: 'yearPillar', 月柱: 'monthPillar', 日柱: 'dayPillar', 时柱: 'hourPillar',
};

// Void condition metadata and supersession rules
const VOID_CONDITION_META: Record<string, { category: 'primary' | 'oneway' | 'mutual'; ch: string; en: string }> = {
  被日柱空:    { category: 'primary', ch: '空亡',    en: 'Primary Void'           },
  被年柱空:    { category: 'oneway',  ch: '被年空',  en: 'Void by Year'           },
  被月柱空:    { category: 'oneway',  ch: '被月空',  en: 'Void by Month'          },
  被时柱空:    { category: 'oneway',  ch: '被时空',  en: 'Void by Hour'           },
  年日互换空亡: { category: 'mutual',  ch: '年日互换', en: 'Mutual Void Year↔Day'  },
  月日互换空亡: { category: 'mutual',  ch: '月日互换', en: 'Mutual Void Month↔Day' },
  日时互换空亡: { category: 'mutual',  ch: '日时互换', en: 'Mutual Void Day↔Hour'  },
};
const SUPERSEDED_BY: Record<string, string[]> = {
  被日柱空: ['年日互换空亡', '月日互换空亡', '日时互换空亡'],
  被年柱空: ['年日互换空亡'],
  被月柱空: ['月日互换空亡'],
  被时柱空: ['日时互换空亡'],
};

const buildVoidStatus = (pillarData: any): VoidStatus => {
  const v = pillarData?.空亡 ?? {};
  const activeKeys = new Set<string>();
  for (const key of Object.keys(VOID_CONDITION_META)) {
    const val = v[key];
    const isActive = key === '被日柱空' ? val !== '无' : !!val;
    if (isActive) activeKeys.add(key);
  }
  const conditions: VoidCondition[] = [...activeKeys]
    .filter(key => !(SUPERSEDED_BY[key] ?? []).some(s => activeKeys.has(s)))
    .map(key => {
      const meta = VOID_CONDITION_META[key];
      return { category: meta.category, label: { ch: meta.ch, en: meta.en } };
    });
  return { conditions };
};

// Element from a naYin phrase (its last character carries the element).
const extractElementFromNaYin = (naYinPhrase: string): 'Metal' | 'Wood' | 'Water' | 'Fire' | 'Earth' => {
  const lastChar = naYinPhrase.charAt(naYinPhrase.length - 1);
  const elementMap: Record<string, 'Metal' | 'Wood' | 'Water' | 'Fire' | 'Earth'> = {
    '金': 'Metal', '木': 'Wood', '水': 'Water', '火': 'Fire', '土': 'Earth',
  };
  return elementMap[lastChar] ?? 'Metal';
};

// lifeStageData is { 日干: "养", 自坐: "衰" }
const buildLifeStage = (lifeStageData: any) =>
  lifeStageData
    ? {
        xingYun: { chinese: lifeStageData.日干, english: '' },
        ziZuo: { chinese: lifeStageData.自坐, english: '' },
      }
    : null;
const buildNaYin = (naYinValue: any) =>
  naYinValue ? { chinese: naYinValue, english: '', element: extractElementFromNaYin(naYinValue) } : null;
const buildXunKong = (voidValue: any) =>
  voidValue && voidValue !== '无' ? { chinese: voidValue, english: '' } : null;

/**
 * Which other pillars a 化气格 pillar combined its stem with.
 *
 * 化气格信息 on the pillar itself is only { 类型, 原五行, 现五行 } — it does not name
 * the partner. The partner IS in 作用.柱位动态: the 天干合 item's 组合明细 maps every
 * participating pillar to its character. Returns {} when no such item exists, so the
 * panel falls back to a bare badge rather than inventing an attribution.
 */
const buildHuaPartners = (pillarDynamic: any[] | undefined) => {
  const out: Record<string, { pillar: string; char: string }[]> = {};
  for (const item of pillarDynamic ?? []) {
    if (item?.类型 !== '天干合') continue;
    const detail = (item.组合明细 ?? {}) as Record<string, string>;
    const members = Object.keys(detail).filter((k) => k in PILLAR_LABEL_KEY);
    for (const self of members) {
      const partners = members
        .filter((other) => other !== self)
        .map((other) => ({ pillar: other, char: detail[other] }));
      if (partners.length > 0) out[self] = [...(out[self] ?? []), ...partners];
    }
  }
  return out;
};

// A section is "ready" when prose has text, or a structured object has ≥1 item.
const sectionHasContent = (value: string | StructuredSection | undefined): boolean => {
  if (typeof value === 'string') return value.trim().length > 0;
  if (value && typeof value === 'object') {
    return Object.values(value).some((items) => Array.isArray(items) && items.length > 0);
  }
  return false;
};

interface ProfilePageClientProps {
  profileRecord: ProfileRecord;
  chartData: any;
  insights?: InsightsResponse | null;
  chartKey: string;
}

export default function ProfilePageClient({ profileRecord, chartData, insights, chartKey }: ProfilePageClientProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  // Delete failure shown inline next to the delete control (success just navigates away).
  const [deleteError, setDeleteError] = useState(false);
  const [insightsData, setInsightsData] = useState<InsightsResponse | null>(insights ?? null);
  // Section keys whose LLM call is currently in flight (progressive loading).
  const [loadingSections, setLoadingSections] = useState<string[]>([]);
  // Section keys whose fetch failed — surfaced as an inline alert with Retry in the
  // Insights tab (sections that did succeed keep rendering normally).
  const [failedSections, setFailedSections] = useState<string[]>([]);
  // Which pillar's detail panel is open (accordion — at most one).
  const [openPillar, setOpenPillar] = useState<PillarKey | null>(null);
  const { language } = useLanguage();
  const tr = translations.profile;
  const trAuth = translations.auth;
  const { user, openAuthModal, setSpotlightCreateForm } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  // Ensures the auto insights generation fires at most once per mount.
  const insightsRequestedRef = useRef(false);

  const generating = loadingSections.length > 0;

  // Fetch one section and merge its prose into state; always clears its loading flag.
  // `requestId` correlates all 6 section calls of one generation across browser → Next → FastAPI.
  const fetchSection = async (idToken: string, key: string, force: boolean, requestId: string) => {
    setFailedSections((prev) => prev.filter((k) => k !== key));
    try {
      const res = await fetch('/api/insights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${idToken}` },
        body: JSON.stringify({ chartKey, section: key, force, requestId, profileId: profileRecord.profileId }),
      });
      if (res.ok) {
        const contentType = res.headers.get('content-type') ?? '';
        if (contentType.includes('text/event-stream') && res.body) {
          // Streaming path: merge each group-delta into the section as it arrives,
          // so the section's groups fill in progressively (renderStructured already
          // shows whichever groups have items).
          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';
          for (;;) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const events = buffer.split('\n\n');
            buffer = events.pop() ?? '';
            for (const evt of events) {
              const line = evt.split('\n').find((l) => l.startsWith('data:'));
              if (!line) continue;
              const payload = line.slice(5).trim();
              if (payload === '[DONE]') continue;
              let parsed: { delta?: Record<string, unknown>; error?: string };
              try { parsed = JSON.parse(payload); } catch { continue; }
              if (parsed.error) throw new Error(parsed.error);
              const delta = parsed.delta;
              if (!delta) continue;
              if (delta.__prose__ !== undefined) {
                const text = delta.__prose__ as string;
                setInsightsData((prev) => ({ sections: { ...(prev?.sections ?? {}), [key]: text } }));
              } else {
                setInsightsData((prev) => {
                  const existing = (prev?.sections?.[key] ?? {}) as StructuredSection;
                  return { sections: { ...(prev?.sections ?? {}), [key]: { ...existing, ...(delta as StructuredSection) } } };
                });
              }
            }
          }
        } else {
          // Cache hit: a single JSON response with the full section value.
          const data: InsightsResponse = await res.json();
          const value = data.sections?.[key] ?? '';
          setInsightsData((prev) => ({ sections: { ...(prev?.sections ?? {}), [key]: value } }));
        }
      } else {
        const detail = await res.text().catch(() => '');
        console.error(`Insights section '${key}' failed [req:${requestId}]:`, res.status, detail);
        reportClientError({
          context: 'insights_section', requestId, chartKey, profileId: profileRecord.profileId,
          uid: user?.uid, section: key, status: res.status, message: detail || `HTTP ${res.status}`,
        });
        setFailedSections((prev) => (prev.includes(key) ? prev : [...prev, key]));
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error(`Insights section '${key}' failed [req:${requestId}]:`, err);
      reportClientError({
        context: 'insights_section', requestId, chartKey, profileId: profileRecord.profileId,
        uid: user?.uid, section: key, message,
      });
      setFailedSections((prev) => (prev.includes(key) ? prev : [...prev, key]));
    } finally {
      setLoadingSections((prev) => prev.filter((k) => k !== key));
    }
  };

  // Progressive load: Core Personality first (renders immediately), then the
  // remaining sections in parallel. `force` (dev) bypasses the cache.
  const generateInsights = async (force = false): Promise<void> => {
    if (!user || user.isAnonymous) return; // insights require a permanent account
    const requestId = crypto.randomUUID();
    const keys = INSIGHT_SECTIONS.map((s) => s.key);
    setLoadingSections(keys);
    let idToken: string;
    try {
      idToken = await user.getIdToken();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error(`Failed to get auth token [req:${requestId}]:`, err);
      reportClientError({
        context: 'auth_token', requestId, profileId: profileRecord.profileId, uid: user?.uid, message,
      });
      setFailedSections(keys);
      setLoadingSections([]);
      return;
    }
    await fetchSection(idToken, keys[0], force, requestId); // personality first
    await Promise.all(keys.slice(1).map((k) => fetchSection(idToken, k, force, requestId)));
  };

  // Re-fetch only the failed sections (fresh token + requestId).
  const retryFailedSections = async (): Promise<void> => {
    if (!user || user.isAnonymous || failedSections.length === 0) return;
    const keys = [...failedSections];
    const requestId = crypto.randomUUID();
    setLoadingSections(keys);
    let idToken: string;
    try {
      idToken = await user.getIdToken();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error(`Failed to get auth token [req:${requestId}]:`, err);
      reportClientError({
        context: 'auth_token', requestId, profileId: profileRecord.profileId, uid: user?.uid, message,
      });
      setLoadingSections([]);
      return;
    }
    await Promise.all(keys.map((k) => fetchSection(idToken, k, false, requestId)));
  };

  // Auto-generate insights once we have a permanent (non-anonymous) owner and none are cached.
  // Covers a logged-in user landing on a freshly-created chart, and a guest who upgrades to an
  // account while viewing their chart. Ownership is already enforced server-side (SSR), and the
  // profile is owned at creation, so there is no "claim" step. Anonymous guests are gated.
  useEffect(() => {
    if (!user || user.isAnonymous) return;
    if (insightsData?.sections || insightsRequestedRef.current) return;
    insightsRequestedRef.current = true;
    void generateInsights();
  }, [user?.uid, user?.isAnonymous]); // eslint-disable-line react-hooks/exhaustive-deps

  // Storage shape -> display shape. Shared with the mobile birth-record panel so the
  // two surfaces cannot drift (lib/profileDisplay.ts).
  const profile = toDisplayProfile(profileRecord);

  const activeTab: TabKey = isTabKey(searchParams.get('tab')) ? (searchParams.get('tab') as TabKey) : DEFAULT_TAB;

  const handleTabChange = (key: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (key === DEFAULT_TAB) params.delete('tab');
    else params.set('tab', key);
    const query = params.toString();
    // push(), not replace(): a tab is a view the reader can back out of. On Android the
    // back gesture is a system control, so without a history entry it would leave the
    // chart entirely instead of returning to the previous tab.
    // scroll:false keeps the reader's place in a long chart.
    router.push(query ? `${pathname}?${query}` : pathname, { scroll: false });
  };

  const handleDeleteProfile = async () => {
    setIsDeleting(true);
    setDeleteError(false);
    try {
      const idToken = user ? await user.getIdToken() : null;
      if (!idToken) throw new Error('No auth token');
      const res = await deleteProfileAction(idToken, profileRecord.profileId);
      if (!res.ok) throw new Error(res.code);
      // That was their last chart → spotlight the landing form so the next step is the only
      // lit thing on screen (same treatment a brand-new account gets after sign-up).
      if (res.remaining === 0) setSpotlightCreateForm(true);
      // Success needs no announcement — navigating away from the deleted profile is the feedback.
      // Go to '/' and let the server component pick the destination: it redirects to the newest
      // remaining chart, or renders the landing page if that was the last one. Keeping that
      // choice in one place means this handler never needs the profile list.
      // replace(), not push(): the deleted profile must not stay in history, where Back would
      // land on a profile that no longer resolves.
      router.replace('/');
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.error('Error deleting profile:', error);
      reportClientError({ context: 'profile_delete', profileId: profileRecord.profileId, uid: user?.uid, message });
      setDeleteError(true);
      setIsDeleting(false);
    }
  };


  /* One row per pillar, feeding both the collapsed cards and the open detail panel.
     maxVoidCount and anyHeavenlyStemBadge are cross-pillar: they reserve space on
     every card so the four stay row-aligned when only some pillars carry a value. */
  const pillars = useMemo(() => {
    const siZhu = (chartData?.四柱实体 ?? {}) as Record<string, any>;
    const shenShaByPillar = (chartData?.神煞 ?? {}) as Record<string, any>;

    const tianGanHuaMap: Record<string, { 元素: string; 原五行: string; label: string }> = {};
    for (const pillarName of PILLAR_ORDER) {
      const hua = siZhu[pillarName]?.化气格信息;
      if (hua?.现五行) {
        tianGanHuaMap[pillarName] = { 元素: hua.现五行, 原五行: hua.原五行, label: `天干合·${hua.类型}` };
      }
    }
    const huaPartnerMap = buildHuaPartners(chartData?.作用?.柱位动态);

    const rows = PILLAR_ORDER.map((key, i) => ({
      key,
      columnIndex: i,
      pillarLabel: tr[PILLAR_LABEL_KEY[key]][language],
      isDayMaster: key === '日柱',
      pillar: siZhu[key],
      lifeStages: buildLifeStage(siZhu[key]?.十二长生),
      naYin: buildNaYin(siZhu[key]?.纳音),
      xunKong: buildXunKong(siZhu[key]?.空亡?.本柱旬空),
      voidStatus: buildVoidStatus(siZhu[key]),
      shenSha: shenShaByPillar[key],
      tianGanHua: tianGanHuaMap[key],
      huaPartners: huaPartnerMap[key],
    }));

    return {
      rows,
      maxVoidCount: Math.max(...rows.map((r) => r.voidStatus.conditions.length)),
      anyHeavenlyStemBadge: Object.keys(tianGanHuaMap).length > 0,
    };
  }, [chartData, language, tr]);

  const openRow = pillars.rows.find((r) => r.key === openPillar);


  // Small uppercase field label / value pair in the midnight header.
  const headerLabelCls = 'text-[10px] uppercase tracking-[0.08em] text-frost-label font-medium';
  const headerValueCls = 'flex items-center gap-1.5 text-sm text-frost-muted';

  return (
    <div className="h-full overflow-auto overflow-x-hidden">
      <div className="max-w-screen-2xl mx-auto px-4 py-6 space-y-6 overflow-x-hidden">
        {/* Profile Header — desktop only. On a phone the chip strip carries the name and
            its drop-down panel carries this birth record, so rendering both would say
            everything twice; the panel also replaces the TST tooltip below, which needs
            a hover the phone has no way to perform. */}
        <Card
          className="hidden md:block"
          style={{
            borderColor: goldAlpha(0.1),
            background: `linear-gradient(180deg, ${palette.inkNavyLight} 0%, ${palette.inkNavy} 100%)`,
            position: 'relative',
          }}
        >
          <div className="flex items-start justify-between">
            {/* Name + Info Grid */}
            <div className="flex-1 min-w-0">
              <h1 className="text-3xl font-semibold mb-3 font-serif text-frost">{profile.name}</h1>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {/* Date of Birth */}
                <div className="flex flex-col gap-0.5">
                  <span className={headerLabelCls}>{translations.sidebar.labelDob[language]}</span>
                  <span className={headerValueCls}>
                    <Calendar className="w-3.5 h-3.5 shrink-0" />
                    {dayjs(profile.birthDate).format('LL')}
                  </span>
                </div>

                {/* Birth Time */}
                <div className="flex flex-col gap-0.5">
                  <span className={headerLabelCls}>{translations.sidebar.labelTimeOfBirth[language]}</span>
                  <span className={headerValueCls}>
                    <Clock className="w-3.5 h-3.5 shrink-0" />
                    {profile.birthTime}
                    {profile.usedSolarTime && (
                      <Tooltip
                        title={tr.tstExplain[language]}
                        color={palette.parchment}
                        styles={{ root: { color: palette.bronzeMuted } }}
                      >
                        <span className="inline-block bg-frost-label text-ink-navy px-2 py-0.5 rounded-xl text-[10px] font-semibold cursor-help ml-1">
                          {tr.tst[language]}
                        </span>
                      </Tooltip>
                    )}
                  </span>
                </div>

                {/* Birth Location */}
                <div className="flex flex-col gap-0.5">
                  <span className={headerLabelCls}>{translations.sidebar.labelBirthLocation[language]}</span>
                  <span className={headerValueCls}>
                    <MapPin className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">{profile.birthLocation}</span>
                  </span>
                </div>

                {/* Gender */}
                <div className="flex flex-col gap-0.5">
                  <span className={headerLabelCls}>{translations.sidebar.labelGender[language]}</span>
                  <span className={headerValueCls}>
                    <User className="w-3.5 h-3.5 shrink-0" />
                    {profile.gender === 'male' ? tr.male[language] : tr.female[language]}
                  </span>
                </div>
              </div>
            </div>

          </div>

          {/* Delete Button - Top Right Corner */}
          <div className="absolute top-4 right-4">
            <Tooltip
              title={tr.deleteBtn[language]}
              color="#DC3545"
              styles={{ root: { color: '#FFFFFF' } }}
            >
              <Popconfirm
                title={tr.deleteTitle[language]}
                description={`Are you sure you want to delete "${profile.name}"? This action cannot be undone.`}
                onConfirm={handleDeleteProfile}
                okText={tr.deleteOk[language]}
                cancelText={tr.deleteCancel[language]}
                okButtonProps={{ danger: true }}
              >
                <Button
                  danger
                  type="text"
                  size="small"
                  className="profile-delete-btn"
                  icon={<Trash2 className="w-4 h-4" />}
                  loading={isDeleting}
                  disabled={isDeleting}
                  style={{ opacity: isDeleting ? 0.6 : 1 }}
                />
              </Popconfirm>
            </Tooltip>
            {deleteError && (
              <p className="text-xs m-0 mt-1 text-right text-[#f1aeb5]">
                {tr.deleteError[language]}
              </p>
            )}
          </div>
        </Card>

        {/* Tabs — controlled from ?tab= (see TAB_KEYS). Phone tab-bar styling and the
            hide-while-a-profile-panel-is-open rule live in styles/components.css. */}
        <Tabs
          activeKey={activeTab}
          onChange={handleTabChange}
          items={[
            {
              key: 'pillars',
              label: tr.tabFourPillars[language],
              children: (
                <div className="space-y-4" style={{ overflowX: 'hidden' }}>
                  {/* 4-up at every width. It used to wrap to 2×2 below lg, which put half
                      the chart below the fold on a phone — the four pillars are read as one
                      row. The width comes out of the cards' own padding and type sizes (see
                      PillarCard), not out of dropping any of them. */}
                  <div className="grid grid-cols-4 gap-1.5 md:gap-4 relative pt-5 min-w-0">
                    {pillars.rows.map((p) => (
                      <PillarCard
                        key={p.key}
                        pillarLabel={p.pillarLabel}
                        pillar={p.pillar}
                        isDayMaster={p.isDayMaster}
                        voidStatus={p.voidStatus}
                        maxVoidCount={pillars.maxVoidCount}
                        tianGanHua={p.tianGanHua}
                        language={language}
                        anyHeavenlyStemBadge={pillars.anyHeavenlyStemBadge}
                        isExpanded={openPillar === p.key}
                        onToggle={() => setOpenPillar((k) => (k === p.key ? null : p.key))}
                      />
                    ))}
                  </div>
                  {openRow && (
                    <PillarDetailPanel
                      pillarKey={openRow.key}
                      pillarLabel={openRow.pillarLabel}
                      pillar={openRow.pillar}
                      columnIndex={openRow.columnIndex}
                      lifeStages={openRow.lifeStages}
                      naYin={openRow.naYin}
                      xunKong={openRow.xunKong}
                      voidStatus={openRow.voidStatus}
                      shenSha={openRow.shenSha}
                      tianGanHua={openRow.tianGanHua}
                      huaPartners={openRow.huaPartners}
                      language={language}
                      onClose={() => setOpenPillar(null)}
                    />
                  )}
                  <DayMasterStrengthCard chartData={chartData} language={language} />
                  <FiveElementsCard chartData={chartData} language={language} />
                  <FavorableElementsCard chartData={chartData} language={language} />
                  <PillarInteractionsCard chartData={chartData} language={language} />
                </div>
              ),
            },
            {
              key: 'insights',
              label: tr.tabInsights[language],
              children: (
                <div className="space-y-4">
                  {/* Sections that failed to generate — inline alert with retry; sections
                      that did succeed keep rendering below. */}
                  {failedSections.length > 0 && !generating && (
                    <Alert
                      type="error"
                      showIcon
                      message={tr.errorInsights[language]}
                      action={
                        <Button size="small" danger onClick={() => void retryFailedSections()}>
                          {tr.retryInsights[language]}
                        </Button>
                      }
                    />
                  )}
                  {process.env.NODE_ENV !== 'production' && user && !user.isAnonymous && (
                    /* Dev-only: force-regenerate (bypass cache) to iterate on prompt/data edits */
                    <div className="flex justify-end">
                      <button
                        onClick={() => generateInsights(true)}
                        disabled={generating}
                        className={`px-3 py-1 border border-dashed border-gold-deep/40 rounded-md text-xs text-gold-deep bg-transparent ${
                          generating ? 'cursor-default opacity-50' : 'cursor-pointer'
                        }`}
                      >
                        ↻ Regenerate (dev)
                      </button>
                    </div>
                  )}
                  {(!user || user.isAnonymous) ? (
                    /* Guest gate card — anonymous users must create an account to unlock insights */
                    <Card style={{ borderColor: goldAlpha(0.15), background: 'rgba(251, 249, 244, 0.8)' }}>
                      <div className="flex flex-col items-center gap-4 py-4">
                        {/* Blurred placeholder rows */}
                        <div className="w-full blur-[4px] pointer-events-none opacity-40">
                          {[80, 60, 90, 70, 55].map((w, i) => (
                            <div
                              key={i}
                              className="h-3 rounded-md mb-2.5 bg-gradient-to-r from-gold-deep/25 to-gold-deep/10"
                              style={{ width: `${w}%` }}
                            />
                          ))}
                        </div>
                        <div className="w-10 h-px bg-gold-deep/20" />
                        <p className="font-serif text-center text-bronze-muted text-[15px] font-semibold">
                          {trAuth.unlockInsights[language]}
                        </p>
                        <button
                          className="indigo-cta font-serif"
                          onClick={() => openAuthModal({ reason: 'insights' })}
                        >
                          {trAuth.createFreeAccount[language]}
                        </button>
                      </div>
                    </Card>
                  ) : generating && !sectionHasContent(insightsData?.sections?.personality) ? (
                    /* Personality not ready yet — themed full loader */
                    <Card style={{ borderColor: goldAlpha(0.1) }}>
                      <InsightsLoading language={language} />
                    </Card>
                  ) : (insightsData?.sections && Object.values(insightsData.sections).some(sectionHasContent)) || generating ? (
                    (() => {
                      const sections = insightsData?.sections ?? {};
                      // Show a panel for each section that is ready OR still loading.
                      const panels = INSIGHT_SECTIONS.filter(
                        (s) => sectionHasContent(sections[s.key]) || loadingSections.includes(s.key),
                      );
                      const firstKey = panels[0]?.key;
                      return (
                        <Card style={{ borderColor: goldAlpha(0.1) }}>
                          <Collapse
                            accordion
                            defaultActiveKey={firstKey ? [firstKey] : []}
                            items={panels.map((s) => ({
                              key: s.key,
                              label: (
                                <span className="font-serif text-gold-deep font-semibold">
                                  {tr[s.title][language]}
                                </span>
                              ),
                              children: sectionHasContent(sections[s.key]) ? (
                                <div>
                                  {typeof sections[s.key] === 'string'
                                    ? renderProse(sections[s.key] as string)
                                    : renderStructured(
                                        sections[s.key] as StructuredSection,
                                        STRUCTURED_LABEL_KEYS[s.key] ?? {},
                                        language,
                                      )}
                                </div>
                              ) : (
                                <InsightsLoading language={language} compact />
                              ),
                            }))}
                          />
                        </Card>
                      );
                    })()
                  ) : (
                    /* Logged in but no insights yet — manual trigger */
                    <Card style={{ borderColor: goldAlpha(0.1) }}>
                      <div className="flex flex-col items-center gap-3 py-2">
                        <button className="indigo-cta font-serif" onClick={() => generateInsights()}>
                          {trAuth.generateInsights[language]}
                        </button>
                      </div>
                    </Card>
                  )}
                </div>
              ),
            },
            {
              key: 'cycles',
              label: tr.tabCycles[language],
              children: (
                <div className="space-y-4">
                  <Card style={{ borderColor: goldAlpha(0.1) }}>
                    <p className="text-center text-bronze-muted/70">Coming Soon</p>
                  </Card>
                </div>
              ),
            },
          ]}
        />
      </div>
    </div>
  );
}
