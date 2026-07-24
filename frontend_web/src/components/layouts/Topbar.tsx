import { Link } from 'wouter';
import { Moon, Sun } from 'lucide-react';
import { Button } from '../ui/Button';
import { useAuth } from '../../hooks/useAuth';
import { useRealtime } from '../../hooks/useRealtime';
import { LiveIndicator } from '../realtime/LiveIndicator';
import { NotificationBell } from '../notifications/NotificationBell';
import { useTheme } from '../providers/ThemeProvider';
import mark from '../../assets/branding/lumyra-icon.svg';
export function Topbar() {
  const { user, logout } = useAuth();
  const { status, lastEvent } = useRealtime();
  const { theme, toggleTheme } = useTheme();
  return <header className="sticky top-0 z-20 border-b border-brand-100 bg-white/82 px-4 py-3 backdrop-blur-xl dark:border-white/10 dark:bg-[#09060f]/82 lg:px-8">
    <div className="flex items-center justify-between gap-3">
      <Link href="/" className="flex items-center gap-2 font-black text-ink dark:text-white lg:hidden"><img src={mark} className="h-8 w-8" alt="" />Lumyra</Link>
      <div className="hidden items-center gap-3 text-sm text-slate-500 dark:text-slate-300 lg:flex"><span>Evento ativo: <strong className="text-ink dark:text-white">Casamento Ana & João</strong></span><LiveIndicator status={status} /></div>
      <div className="flex items-center gap-3"><NotificationBell lastEvent={lastEvent} /><button onClick={toggleTheme} className="lumyra-focus rounded-2xl border border-brand-100 bg-white p-2 text-slate-700 shadow-sm transition hover:-translate-y-0.5 hover:bg-brand-50 dark:border-white/10 dark:bg-white/10 dark:text-slate-200 dark:hover:bg-white/15">{theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}</button><span className="hidden text-sm font-bold text-slate-600 dark:text-slate-300 sm:block">{user?.name}</span><Button variant="secondary" onClick={logout}>Sair</Button></div>
    </div>
  </header>;
}
