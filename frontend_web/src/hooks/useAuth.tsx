import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { Role, User } from '../types/domain';
import { authApi, hasStoredAccessToken } from '../services/api';

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  demoLogin: (role: Role) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const demoUsers: Record<Role, User> = {
  ADMIN: { name: 'Assessoria Demo', email: 'admin@demo.local', role: 'ADMIN', tenant_id: 1 },
  CLIENT: { name: 'Ana & João', email: 'noivos@demo.local', role: 'CLIENT', tenant_id: 1 },
  STAFF: { name: 'Equipe Check-in', email: 'staff@demo.local', role: 'STAFF', tenant_id: 1 }
};

function readDemoUser(): User | null {
  try {
    const stored = localStorage.getItem('demo_user');
    return stored ? JSON.parse(stored) as User : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(readDemoUser);
  const [isLoading, setIsLoading] = useState(
    () => Boolean(!localStorage.getItem('demo_user') && hasStoredAccessToken()),
  );

  useEffect(() => {
    if (localStorage.getItem('demo_user') || !hasStoredAccessToken()) return;
    authApi.me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false));
  }, []);

  async function login(email: string, password: string) {
    await authApi.login(email, password);
    const current = await authApi.me();
    localStorage.removeItem('demo_user');
    setUser(current);
    return current;
  }

  async function logout() {
    try {
      if (hasStoredAccessToken()) await authApi.logout();
    } finally {
      localStorage.removeItem('demo_user');
      setUser(null);
    }
  }

  function demoLogin(role: Role) {
    const demo = demoUsers[role];
    localStorage.setItem('demo_user', JSON.stringify(demo));
    setUser(demo);
  }

  const value = useMemo(
    () => ({ user, isAuthenticated: Boolean(user), isLoading, login, logout, demoLogin }),
    [user, isLoading],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth precisa estar dentro de AuthProvider');
  return ctx;
}
