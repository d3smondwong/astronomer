'use client';

import { type ReactNode } from 'react';
import { AuthProvider } from '@/lib/authContext';
import AuthModal from '@/components/AuthModal';

export function ClientRoot({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      {children}
      <AuthModal />
    </AuthProvider>
  );
}
