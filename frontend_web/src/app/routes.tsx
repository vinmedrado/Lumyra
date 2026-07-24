import type { ReactNode } from 'react';
import { Redirect } from 'wouter';
import type { Role } from '../types/domain';
import { useAuth } from '../hooks/useAuth';
import { LoadingState } from '../components/ui/LoadingState';

export function ProtectedRoute({ roles, children }: { roles?: Role[]; children: ReactNode }) {
  const { user, isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <LoadingState label="Restaurando sua sessão..." />;
  if (!isAuthenticated) return <Redirect to="/login" replace />;
  if (roles && user && !roles.includes(user.role)) return <Redirect to={user.role === 'CLIENT' ? '/client/dashboard' : '/admin/dashboard'} replace />;
  return <>{children}</>;
}
