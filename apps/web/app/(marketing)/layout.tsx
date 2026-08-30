/**
 * Marketing layout — the logged-out front door's chrome, shared by every page in the group
 * (landing today; pricing and about next).
 *
 * This is the counterpart to (dashboard)/layout.tsx + DashboardShell: two genuinely different
 * chromes for two different contexts. Marketing gets a fixed top bar and a footer; the
 * dashboard gets a collapsible sidebar. They deliberately do NOT share a component — see the
 * variant note in Header.tsx — though they do share the `translations.header.*` copy.
 *
 * A Server Component: it holds no state, and Header brings its own 'use client'. The group
 * adds no URL segment, so the landing page is still "/".
 *
 * No error.tsx here on purpose. app/error.tsx sits above this and catches the whole group;
 * route groups don't block boundary inheritance. Add one here only if marketing ever needs
 * copy distinct from the root boundary's.
 */

import Header from './Header';
import Footer from './Footer';

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      {/* pt-32 clears the fixed header — it is out of flow, so nothing else reserves the space. */}
      <main className="flex-grow pt-32 pb-20">{children}</main>

      <Footer />
    </div>
  );
}
