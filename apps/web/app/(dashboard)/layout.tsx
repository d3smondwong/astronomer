'use client';

import { Fragment, useState, useEffect, useRef, useCallback, useSyncExternalStore } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { Divider, Layout, Popconfirm, Modal } from 'antd';
import { Plus, Users, MessageSquare, User, Trash2 } from 'lucide-react';
import BaziProfileForm, { type BaziProfileFormRef } from '@/components/BaziProfileForm';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';
import { useAuth } from '@/lib/authContext';

const { Sider, Content } = Layout;

const COLLAPSE_BREAKPOINT = 1024;

// The viewport is an external store. Reading it through useSyncExternalStore keeps the
// server render (never collapsed) and the hydrating client render in agreement, then
// re-reads the real width immediately after hydration — no isMounted flag, no setState
// inside an effect.
function subscribeToViewport(onStoreChange: () => void) {
  window.addEventListener('resize', onStoreChange);
  return () => window.removeEventListener('resize', onStoreChange);
}

function useIsCollapsed(): boolean {
  return useSyncExternalStore(
    subscribeToViewport,
    () => window.innerWidth < COLLAPSE_BREAKPOINT,
    () => false,
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [profiles, setProfiles] = useState<any[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  // profileId whose delete failed — shows an inline notice under that row.
  // Success needs no announcement: the row disappearing is the feedback.
  const [deleteErrorId, setDeleteErrorId] = useState<string | null>(null);
  const isCollapsed = useIsCollapsed();
  const { language, setLanguage } = useLanguage();
  const tr = translations.sidebar;
  const formRef = useRef<BaziProfileFormRef>(null);
  const { user, openAuthModal, signOut } = useAuth();

  const fetchProfiles = useCallback(async () => {
    // Every visitor is a Firebase user now (anonymous guests included), so list by UID.
    if (!user) return null; // auth not bootstrapped yet
    try {
      const idToken = await user.getIdToken();
      const res = await fetch('/api/profiles', {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (!res.ok) return null;
      return (await res.json()) as any[];
    } catch (error) {
      console.error('Error loading profiles:', error);
      return null;
    }
  }, [user]);

  const loadProfiles = useCallback(async () => {
    const loaded = await fetchProfiles();
    if (loaded) setProfiles(loaded);
  }, [fetchProfiles]);

  // Reload when the user signs in/out or navigates (the guest path changes).
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const loaded = await fetchProfiles();
      if (!cancelled && loaded) setProfiles(loaded);
    })();
    return () => {
      cancelled = true;
    };
  }, [fetchProfiles, pathname]);

  const handleAddProfile = () => {
    // A guest who already has their one free chart must sign up to add more. profiles is the
    // authoritative count for the current (anonymous) session.
    if (user?.isAnonymous && profiles.length >= 1) {
      openAuthModal({ reason: 'addChart' });
      return;
    }
    setIsModalOpen(true);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    formRef.current?.reset();
  };

  const handleFormSuccess = (profileId: string) => {
    setIsModalOpen(false);
    loadProfiles();
    router.push(`/profile/${profileId}`);
  };

  const handleDeleteProfile = async (profileId: string) => {
    setDeleteErrorId(null);
    try {
      const idToken = user ? await user.getIdToken() : null;
      const res = await fetch(`/api/profiles/${profileId}`, {
        method: 'DELETE',
        headers: idToken ? { Authorization: `Bearer ${idToken}` } : undefined,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const remaining = profiles.filter((p: any) => p.profileId !== profileId);
      setProfiles(remaining);

      if (pathname.includes(profileId)) {
        if (remaining.length > 0) {
        const deletedIndex = profiles.findIndex((p: any) => p.profileId === profileId);
        const next = remaining[deletedIndex] ?? remaining[deletedIndex - 1];
        router.push(`/profile/${next.profileId}`);
      } else {
        handleAddProfile();
      }
    }
    } catch (error) {
      console.error('Error deleting profile:', error);
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
        <Sider className="dashboard-sider sidebar-shell" width={isCollapsed ? 85 : "12%"}>
          <div className="flex flex-col h-full">
            {/* Logo */}
            <div className="py-3 px-5 border-b border-gold-deep/8 flex items-center justify-center">
              <Link href="/">
                {isCollapsed ? (
                  <Image
                    src="/short_huat_life_logo.svg"
                    alt="Huat Life"
                    width={40}
                    height={40}
                    priority
                  />
                ) : (
                  <Image
                    src="/straight_huat_life_logo_svg.svg"
                    alt="Huat Life"
                    width={180}
                    height={45}
                    className="w-auto h-14"
                    priority
                  />
                )}
              </Link>
            </div>

            {/* Nav Content */}
            <div className="sidebar-nav-content flex-1 px-3 py-4 overflow-y-auto">
              {/* Profiles Section */}
              <div className="mb-2">
                {!isCollapsed && (
                  <div className="flex items-center justify-between mb-1.5 px-1">
                    <h3 className="sidebar-section-label">
                      <span className="mr-[5px] text-sm align-middle leading-none">·</span>{tr.profiles[language]}
                    </h3>
                    <button className="sidebar-add-btn" onClick={handleAddProfile}>
                      <Plus className="w-3 h-3" />
                    </button>
                  </div>
                )}

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
                            className={`w-full flex items-center py-[7px] px-2.5 bg-transparent border-none cursor-pointer text-sm text-left text-inherit [font-weight:inherit] ${isCollapsed ? 'gap-1 justify-center' : 'gap-2 justify-start'}`}
                            title={profile.name}
                          >
                            <User className="w-3.5 h-3.5 sidebar-item-icon" />
                            {!isCollapsed && (
                              <span className="overflow-hidden text-ellipsis whitespace-nowrap">{profile.name}</span>
                            )}
                            {isCollapsed && (
                              <span className="text-xs font-medium">{profile.name.substring(0, 3)}</span>
                            )}
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
                      {deleteErrorId === profile.profileId && !isCollapsed && (
                        <p className="text-xs px-3 pb-1 m-0 text-danger">
                          {translations.profile.deleteError[language]}
                        </p>
                      )}
                      </Fragment>
                    ))
                  )}
                </div>
              </div>

              {!isCollapsed && <Divider className="sidebar-divider my-4 border-gold-deep/8" />}

              {/* Other Sections */}
              <div className="flex flex-col gap-0.5">
                {!isCollapsed && (
                  <div className="px-1 mb-1.5">
                    <h3 className="sidebar-section-label">
                      <span className="mr-[5px] text-sm align-middle leading-none">·</span>{tr.tools[language]}
                    </h3>
                  </div>
                )}

                <Link href="/compatibility" className="block">
                  <div
                    className="sidebar-item sidebar-nav-item flex items-center gap-[9px] cursor-pointer text-sm"
                    data-active={isActive('compatibility')}
                    title="Compatibility"
                  >
                    <Users className="w-4 h-4 sidebar-item-icon" />
                    {!isCollapsed && <span className="sidebar-nav-label">{tr.compatibility[language]}</span>}
                  </div>
                </Link>

                <Link href="/ai_oracle_chat" className="block">
                  <div
                    className="sidebar-item sidebar-nav-item flex items-center gap-[9px] cursor-pointer text-sm"
                    data-active={isActive('ai_oracle_chat')}
                    title="AI Oracle Chat"
                  >
                    <MessageSquare className="w-4 h-4 sidebar-item-icon" />
                    {!isCollapsed && <span className="sidebar-nav-label">{tr.aiOracleChat[language]}</span>}
                  </div>
                </Link>
              </div>
            </div>

            {/* User Profile — bottom of sidebar */}
            <div className="sidebar-user-profile flex items-center p-3 border-t border-gold-deep/8">
              <div className="sidebar-avatar">
                {user && !user.isAnonymous ? user.email?.[0]?.toUpperCase() : <User className="w-5 h-5 text-gold-deep" />}
              </div>
              <p className="text-xs font-medium text-bronze-muted m-0">
                {user && !user.isAnonymous ? user.email?.split('@')[0] : tr.guest[language]}
              </p>
              <button
                className="sidebar-login-btn"
                onClick={() => (user && !user.isAnonymous) ? signOut() : openAuthModal()}
              >
                {user && !user.isAnonymous ? translations.header.signOut[language] : translations.header.loginSignUp[language]}
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

        {/* Main Content — margin tracks the JS-driven sidebar width */}
        <Content
          className="dashboard-content bg-parchment"
          style={{ marginLeft: isCollapsed ? '85px' : '12%' }}
        >
          {children}
        </Content>
      </Layout>

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
