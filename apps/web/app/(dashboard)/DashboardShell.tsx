'use client';

/**
 * Interactive shell for the dashboard: sidebar chrome, the create-profile modal, delete
 * controls, sign-in/out, and the language toggle.
 *
 * The profile list arrives as a prop from the (server) dashboard layout — this component
 * deliberately keeps no copy of it. Mutations call Server Actions that revalidate the layout,
 * so the list re-renders from Firestore rather than from patched local state. That is what
 * removed the two-sources-of-truth bug; don't reintroduce a useState mirror here.
 *
 * Two chromes, one children tree, one breakpoint. Below 1024px the compact chrome (chip
 * strip + birth-record / account panels + bottom tab bar) is shown; at and above it the
 * sidebar. Both render unconditionally and CSS decides which is visible — branching in JS
 * would either render `children`, the whole chart tree, twice, or flash on hydration,
 * because the server snapshot cannot know the viewport.
 *
 * There used to be a third tier: an 85px icon rail from 768-1023px, driven by an
 * isCollapsed flag. It was strictly worse than the bottom nav it sat next to — no labels,
 * and its `!isCollapsed` guards hid the create-profile `+` while dashboard.css hid
 * `.sidebar-login-btn`, so a 1000px window could neither add a chart nor sign in or out.
 * Deleting it removed both bugs, the flag, the logo swap and a whole media-query block.
 * Hence no viewport hook here any more: the sidebar has exactly one shape.
 */

import { Fragment, useState, useRef } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { Divider, Layout, Popconfirm, Modal } from 'antd';
import { Plus, Users, MessageSquare, User, Trash2 } from 'lucide-react';
import BaziProfileForm, { type BaziProfileFormRef } from '@/components/BaziProfileForm';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';
import { useAuth } from '@/lib/authContext';
import { reportClientError } from '@/lib/errorReporter';
import { deleteProfileAction } from '@/app/actions/profiles';
import { type ProfileRecord } from '@/types/profile';
import MobileProfileStrip, { type MobilePanel } from './MobileProfileStrip';
import MobileBirthRecordPanel from './MobileBirthRecordPanel';
import MobileAccountPanel from './MobileAccountPanel';
import MobileBottomNav from './MobileBottomNav';

const { Sider, Content } = Layout;

/**
 * Sidebar width, in px, kept in sync with .dashboard-sider / .dashboard-content in
 * dashboard.css. antd's Sider writes inline min-width/max-width from this prop and
 * min-width beats a `width: … !important` from CSS, so the number has to be passed here
 * as well as declared there.
 *
 * A fixed width rather than the old `12%`: that had no clamp, so it resolved to 123px at
 * 1024px — too narrow for 'Compatibility', which truncated, and 'AI Oracle Chat', which
 * wrapped onto three lines. 210px fits the longest nav label at every viewport.
 */
const SIDEBAR_WIDTH = 210;

interface DashboardShellProps {
  /** Server-rendered, owner-scoped and newest-first. Re-rendered by revalidatePath on mutation. */
  profiles: ProfileRecord[];
  children: React.ReactNode;
}

export default function DashboardShell({ profiles, children }: DashboardShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isModalOpen, setIsModalOpen] = useState(false);
  // profileId whose delete failed — shows an inline notice under that row.
  // Success needs no announcement: the row disappearing is the feedback.
  const [deleteErrorId, setDeleteErrorId] = useState<string | null>(null);
  // Which mobile drop-down panel is open (at most one), tagged with the route it was
  // opened on. Lives here rather than in the strip because the profile page reads it too
  // — its tab bar hides while a panel is up.
  //
  // Tapping an unselected chip is a plain <Link>, so there is nothing to intercept and
  // the panel has to close itself on navigation. Storing the path and comparing during
  // render does that by derivation; an effect calling setOpenPanel(null) would setState
  // during commit and cascade an extra render on every navigation.
  const [panelState, setPanelState] = useState<{ panel: MobilePanel; path: string }>({
    panel: null,
    path: pathname,
  });
  const openPanel: MobilePanel = panelState.path === pathname ? panelState.panel : null;
  const setOpenPanel = (panel: MobilePanel) => setPanelState({ panel, path: pathname });
  const { language, setLanguage } = useLanguage();
  const tr = translations.sidebar;
  const formRef = useRef<BaziProfileFormRef>(null);
  const { user, openAuthModal, signOut, setSpotlightCreateForm } = useAuth();

  const isSignedIn = Boolean(user && !user.isAnonymous);
  const accountName = isSignedIn ? user?.email?.split('@')[0] ?? null : null;

  // Exact segment match, unlike the sidebar's substring isActive(): the chip strip must
  // know precisely which profile is on screen to decide which chip discloses vs navigates.
  const activeProfileId = pathname.match(/^\/profile\/([^/]+)/)?.[1] ?? null;
  const activeProfile = profiles.find((p) => p.profileId === activeProfileId);

  const handleAddProfile = () => {
    // Either branch puts something else on screen; leaving a panel hanging under it
    // would cover the top of the modal.
    setOpenPanel(null);
    // A guest who already has their one free chart must sign up to add more. The server
    // enforces this too (/api/chart returns 409); this is the friendly path.
    if (user?.isAnonymous && profiles.length >= 1) {
      openAuthModal({ reason: 'addChart' });
      return;
    }
    setIsModalOpen(true);
  };

  const handleTogglePanel = (panel: Exclude<MobilePanel, null>) => {
    setOpenPanel(openPanel === panel ? null : panel);
  };

  const handleMobileAuthAction = () => {
    setOpenPanel(null);
    if (isSignedIn) signOut();
    else openAuthModal();
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    formRef.current?.reset();
  };

  const handleFormSuccess = (profileId: string) => {
    setIsModalOpen(false);
    // No list refetch: /api/chart revalidates the layout, so the sidebar re-renders on its own.
    router.push(`/profile/${profileId}`);
  };

  const handleDeleteProfile = async (profileId: string) => {
    setDeleteErrorId(null);
    try {
      const idToken = user ? await user.getIdToken() : null;
      if (!idToken) throw new Error('No auth token');
      const res = await deleteProfileAction(idToken, profileId);
      if (!res.ok) throw new Error(res.code);

      // The row disappears because the action revalidated this layout — no local filtering.
      // Navigate only when the deleted profile is the one on screen; deleting a background
      // profile now leaves the user exactly where they were.
      if (pathname.includes(profileId)) {
        // That was their last chart → spotlight the landing form so the next step is the only
        // lit thing on screen (same treatment a brand-new account gets after sign-up).
        if (res.remaining === 0) setSpotlightCreateForm(true);
        // replace(), not push(): the deleted profile must not stay in history. '/' picks the
        // destination — newest remaining chart, or the landing page if there is none.
        router.replace('/');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.error('Error deleting profile:', error);
      reportClientError({ context: 'profile_delete', profileId, uid: user?.uid, message });
      // Row stays in the list; show the failure right where the action happened.
      setDeleteErrorId(profileId);
    }
  };

  const isActive = (path: string) => {
    return pathname.includes(path);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Layout className="min-h-screen">
        {/* Left Sidebar — surface styles in components.css, layout math in dashboard.css */}
        <Sider className="dashboard-sider sidebar-shell" width={SIDEBAR_WIDTH}>
          <div className="flex flex-col h-full">
            {/* Logo */}
            <div className="py-3 px-5 border-b border-gold-deep/8 flex items-center justify-center">
              <Link href="/">
                <Image
                  src="/straight_huat_life_logo_svg.svg"
                  alt="Huat Life"
                  width={180}
                  height={45}
                  className="w-auto h-14"
                  priority
                />
              </Link>
            </div>

            {/* Nav Content */}
            <div className="sidebar-nav-content flex-1 px-3 py-4 overflow-y-auto">
              {/* Profiles Section */}
              <div className="mb-2">
                <div className="flex items-center justify-between mb-1.5 px-1">
                  <h3 className="sidebar-section-label">
                    <span className="mr-[5px] text-sm align-middle leading-none">·</span>{tr.profiles[language]}
                  </h3>
                  <button className="sidebar-add-btn" onClick={handleAddProfile}>
                    <Plus className="w-3 h-3" />
                  </button>
                </div>

                <div>
                  {profiles.length === 0 ? (
                    <p className="text-[13px] text-bronze-muted px-3 py-2 opacity-45 italic m-0">
                      {tr.noProfiles[language]}
                    </p>
                  ) : (
                    profiles.map((profile) => (
                      <Fragment key={profile.profileId}>
                      <div
                        className="sidebar-item group flex items-center justify-between mb-0.5"
                        data-active={isActive(profile.profileId)}
                      >
                        {/* text-inherit: keep the row's color — antd's reset paints bare anchors blue */}
                        <Link href={`/profile/${profile.profileId}`} className="flex-1 min-w-0 text-inherit">
                          <button
                            className="w-full flex items-center gap-2 justify-start py-[7px] px-2.5 bg-transparent border-none cursor-pointer text-sm text-left text-inherit [font-weight:inherit]"
                            title={profile.name}
                          >
                            <User className="w-3.5 h-3.5 sidebar-item-icon" />
                            <span className="overflow-hidden text-ellipsis whitespace-nowrap">{profile.name}</span>
                          </button>
                        </Link>

                        <Popconfirm
                          title={tr.deleteProfile[language]}
                          description={`Are you sure you want to delete "${profile.name}"? This action cannot be undone.`}
                          onConfirm={() => handleDeleteProfile(profile.profileId)}
                          okText={tr.deleteOk[language]}
                          cancelText={tr.deleteCancel[language]}
                        >
                          <button className="w-7 h-7 p-0 mr-1 border-none bg-transparent cursor-pointer text-danger rounded flex items-center justify-center transition-opacity opacity-0 group-hover:opacity-60 hover:opacity-100!">
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </Popconfirm>
                      </div>
                      {deleteErrorId === profile.profileId && (
                        <p className="text-xs px-3 pb-1 m-0 text-danger">
                          {translations.profile.deleteError[language]}
                        </p>
                      )}
                      </Fragment>
                    ))
                  )}
                </div>
              </div>

              <Divider className="sidebar-divider my-4 border-gold-deep/8" />

              {/* Other Sections */}
              <div className="flex flex-col gap-0.5">
                <div className="px-1 mb-1.5">
                  <h3 className="sidebar-section-label">
                    <span className="mr-[5px] text-sm align-middle leading-none">·</span>{tr.tools[language]}
                  </h3>
                </div>

                <Link href="/compatibility" className="block">
                  <div
                    className="sidebar-item sidebar-nav-item flex items-center gap-[9px] cursor-pointer text-sm"
                    data-active={isActive('compatibility')}
                    title="Compatibility"
                  >
                    <Users className="w-4 h-4 sidebar-item-icon" />
                    <span className="sidebar-nav-label">{tr.compatibility[language]}</span>
                  </div>
                </Link>

                <Link href="/ai_oracle_chat" className="block">
                  <div
                    className="sidebar-item sidebar-nav-item flex items-center gap-[9px] cursor-pointer text-sm"
                    data-active={isActive('ai_oracle_chat')}
                    title="AI Oracle Chat"
                  >
                    <MessageSquare className="w-4 h-4 sidebar-item-icon" />
                    <span className="sidebar-nav-label">{tr.aiOracleChat[language]}</span>
                  </div>
                </Link>
              </div>
            </div>

            {/* User Profile — bottom of sidebar */}
            <div className="sidebar-user-profile flex items-center p-3 border-t border-gold-deep/8">
              <div className="sidebar-avatar">
                {isSignedIn ? user?.email?.[0]?.toUpperCase() : <User className="w-5 h-5 text-gold-deep" />}
              </div>
              <p className="text-xs font-medium text-bronze-muted m-0">
                {isSignedIn ? accountName : tr.guest[language]}
              </p>
              <button
                className="sidebar-login-btn"
                onClick={() => (isSignedIn ? signOut() : openAuthModal())}
              >
                {isSignedIn ? translations.header.signOut[language] : translations.header.loginSignUp[language]}
              </button>
              {/* Language toggle */}
              <div className="lang-toggle">
                {(['en', 'ch'] as const).map((lang) => (
                  <button
                    key={lang}
                    className="lang-toggle-btn"
                    data-active={language === lang}
                    onClick={() => setLanguage(lang)}
                  >
                    {lang === 'en' ? 'EN' : '中文'}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Sider>

        {/* Main Content — the sidebar offset is now CSS-only (dashboard.css media
            queries). It used to be an inline style, which put the same two numbers in
            three places and meant any media query trying to zero the margin lost to
            the inline value. data-panel-open lets the profile page's tab bar hide
            while a mobile panel is up, without threading state through children. */}
        <Content
          className="dashboard-content bg-parchment"
          data-panel-open={openPanel !== null}
        >
          {/* Phone header. Hidden at md+; at most one panel is open beneath the strip. */}
          <div className="mobile-topbar">
            <MobileProfileStrip
              profiles={profiles}
              activeProfileId={activeProfileId}
              openPanel={openPanel}
              onTogglePanel={handleTogglePanel}
              onAddProfile={handleAddProfile}
              accountInitial={isSignedIn ? user?.email?.[0]?.toUpperCase() ?? null : null}
            />
            {openPanel === 'birth' && activeProfile && (
              <MobileBirthRecordPanel
                profile={activeProfile}
                onDelete={() => handleDeleteProfile(activeProfile.profileId)}
                deleteFailed={deleteErrorId === activeProfile.profileId}
              />
            )}
            {openPanel === 'account' && (
              <MobileAccountPanel
                accountName={accountName}
                onAuthAction={handleMobileAuthAction}
              />
            )}
          </div>

          {/* display:contents at md+, so the desktop layout is byte-identical; on a
              phone it becomes the scrolling flex row between strip and bottom bar. */}
          <div className="dashboard-main">{children}</div>
        </Content>
      </Layout>

      <MobileBottomNav
        activeProfileId={activeProfileId}
        fallbackProfileId={profiles[0]?.profileId ?? null}
      />

      {/* Add Profile Modal */}
      <Modal
        title={tr.modalTitle[language]}
        open={isModalOpen}
        onCancel={handleModalClose}
        footer={null}
        width={500}
      >
        <BaziProfileForm
          ref={formRef}
          onSuccess={handleFormSuccess}
          submitClassName="gold-gradient w-full h-10 text-white font-serif tracking-wide border-none mt-6"
        />
      </Modal>
    </div>
  );
}
