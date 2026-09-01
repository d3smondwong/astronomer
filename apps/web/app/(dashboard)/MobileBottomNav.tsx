'use client';

/**
 * MobileBottomNav — the phone's primary navigation, replacing the sidebar's Tools
 * section. Fixed to the bottom edge and inset for the home indicator via
 * env(safe-area-inset-bottom) (see .mobile-bottom-nav in dashboard.css).
 *
 * Three destinations, matching the sidebar's three: the profile chart, Compatibility
 * and the Oracle. Rendered by DashboardShell and hidden at md+ via CSS.
 *
 * The Profiles tab needs a concrete profile to link to — the dashboard has no
 * /profile index route. It aims at the profile on screen, falls back to the newest
 * (the list arrives newest-first), and finally to '/', which the marketing route
 * resolves to the newest chart or the landing form.
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { User, Users, MessageSquare } from 'lucide-react';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';

interface MobileBottomNavProps {
  activeProfileId: string | null;
  /** Newest profile, used when no profile route is open. */
  fallbackProfileId: string | null;
}

export default function MobileBottomNav({
  activeProfileId,
  fallbackProfileId,
}: MobileBottomNavProps) {
  const pathname = usePathname();
  const { language } = useLanguage();
  const tr = translations.sidebar;

  const profileTarget = activeProfileId ?? fallbackProfileId;
  const items = [
    {
      key: 'profiles',
      href: profileTarget ? `/profile/${profileTarget}` : '/',
      label: tr.profiles[language],
      Icon: User,
      active: pathname.startsWith('/profile/'),
    },
    {
      key: 'compatibility',
      href: '/compatibility',
      label: tr.compatibility[language],
      Icon: Users,
      active: pathname.startsWith('/compatibility'),
    },
    {
      key: 'oracle',
      href: '/ai_oracle_chat',
      label: tr.navOracle[language],
      Icon: MessageSquare,
      active: pathname.startsWith('/ai_oracle_chat'),
    },
  ];

  return (
    <nav className="mobile-bottom-nav" aria-label={tr.tools[language]}>
      {items.map(({ key, href, label, Icon, active }) => (
        <Link
          key={key}
          href={href}
          className="bottom-nav-item"
          data-active={active}
          aria-current={active ? 'page' : undefined}
        >
          <Icon className="bottom-nav-icon w-[18px] h-[18px]" aria-hidden="true" />
          <span className="bottom-nav-label">{label}</span>
        </Link>
      ))}
    </nav>
  );
}
