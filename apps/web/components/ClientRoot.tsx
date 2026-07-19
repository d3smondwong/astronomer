'use client';

import { type ReactNode } from 'react';
import { AuthProvider } from '@/lib/authContext';
import AuthModal from '@/components/AuthModal';

export function ClientRoot({
  children,
  /** Identity the server rendered this request for; see AuthProvider for why it matters. */
  serverIdentity,
}: {
  children: ReactNode;
  serverIdentity: string | null;
}) {
  return (
    <AuthProvider serverIdentity={serverIdentity}>
      {children}
      <AuthModal />
    </AuthProvider>
  );
}
