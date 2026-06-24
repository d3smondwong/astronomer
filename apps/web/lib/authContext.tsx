'use client';

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { type User, onAuthStateChanged, signOut as firebaseSignOut } from 'firebase/auth';
import { auth } from './firebaseClient';

interface ModalConfig {
  showSkip?: boolean;
  onSkip?: () => void;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthModalOpen: boolean;
  modalShowSkip: boolean;
  modalOnSkip?: () => void;
  openAuthModal: (config?: ModalConfig) => void;
  closeAuthModal: () => void;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  isAuthModalOpen: false,
  modalShowSkip: false,
  modalOnSkip: undefined,
  openAuthModal: () => {},
  closeAuthModal: () => {},
  signOut: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [modalConfig, setModalConfig] = useState<ModalConfig>({});

  useEffect(() => {
    return onAuthStateChanged(auth, (u) => {
      setUser(u);
      setLoading(false);
    });
  }, []);

  const openAuthModal = (config: ModalConfig = {}) => {
    setModalConfig(config);
    setIsAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    setIsAuthModalOpen(false);
    setModalConfig({});
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthModalOpen,
        modalShowSkip: modalConfig.showSkip ?? false,
        modalOnSkip: modalConfig.onSkip,
        openAuthModal,
        closeAuthModal,
        signOut: () => firebaseSignOut(auth),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  return useContext(AuthContext);
}
