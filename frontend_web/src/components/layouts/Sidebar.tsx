import { Link, useLocation } from 'wouter';
import { Activity, BarChart3, Bell, CalendarDays, FileText, Heart, Home, Lightbulb, MessageCircle, Music2, Settings, ShieldCheck, Table2, Users, Wallet, Zap } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import logo from '../../assets/branding/lumyra-logo.svg';
import logoDark from '../../assets/branding/lumyra-logo-dark.svg';
import mark from '../../assets/branding/lumyra-icon.svg';

const adminGroups = [
  { title: 'Operação', items: [['Dashboard', '/admin/dashboard', Home], ['Eventos', '/admin/events', CalendarDays], ['Convidados', '/admin/guests', Users], ['Mesas', '/admin/tables', Table2], ['Formulários', '/admin/forms', FileText]] },
  { title: 'Comunicação', items: [['Campanhas', '/admin/campaigns', MessageCircle], ['WhatsApp', '/admin/whatsapp', MessageCircle], ['Playlist', '/admin/playlist', Music2], ['Notificações', '/admin/notifications', Bell]] },
  { title: 'Gestão', items: [['Financeiro', '/admin/financial', Wallet], ['Documentos', '/admin/documents', FileText]] },
  { title: 'Inteligência', items: [['Analytics', '/admin/analytics', BarChart3], ['Insights', '/admin/insights', Lightbulb], ['Command Center', '/admin/command-center', Zap], ['Activity Feed', '/admin/activity', Activity], ['Auditoria', '/admin/audit', ShieldCheck], ['Configurações', '/admin/settings', Settings]] }
] as const;
const clientItems = [['Início', '/client/dashboard', Heart], ['Convidados', '/client/guests', Users], ['RSVP', '/client/rsvp', MessageCircle], ['Mesas', '/client/tables', Table2], ['Timeline', '/client/timeline', CalendarDays], ['Documentos', '/client/documents', FileText], ['Financeiro', '/client/financial', Wallet], ['Mensagens', '/client/messages', MessageCircle], ['Playlist', '/client/playlist', Music2]] as const;
function LinkItem({ item }: { item: readonly [string, string, any] }) {
  const [label, to, Icon] = item;
  const [location] = useLocation();
  const isActive = location === to;
  return <Link href={to} className={`flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-bold transition ${isActive ? 'bg-brand-800 text-white shadow-glow' : 'text-slate-600 hover:bg-brand-50 hover:text-brand-800 dark:text-slate-300 dark:hover:bg-white/10 dark:hover:text-white'}`}><Icon size={18} />{label}</Link>;
}
export function Sidebar({ mode }: { mode: 'admin' | 'client' }) {
  const { user } = useAuth();
  return <aside className="hidden min-h-screen w-72 shrink-0 border-r border-brand-100 bg-ice/90 p-5 backdrop-blur dark:border-white/10 dark:bg-[#09060f]/95 lg:block">
    <div className="mb-7 rounded-[1.8rem] bg-white p-4 shadow-soft dark:bg-white/10">
      <img src={logo} alt="Lumyra" className="h-16 w-auto dark:hidden" />
      <img src={logoDark} alt="Lumyra" className="hidden h-16 w-auto dark:block" />
      <p className="mt-1 text-xs font-bold uppercase tracking-[.22em] text-slate-500 dark:text-slate-300">{mode === 'admin' ? 'Operação da assessoria' : 'Experiência dos noivos'}</p>
    </div>
    <div className="mb-5 rounded-3xl border border-brand-100 bg-white p-4 shadow-soft dark:border-white/10 dark:bg-white/10">
      <div className="flex items-center gap-3"><img src={mark} className="h-9 w-9" alt="" /><div><p className="text-xs uppercase tracking-widest text-slate-400">Perfil ativo</p><p className="font-extrabold text-ink dark:text-white">{user?.name || 'Demo Lumyra'}</p></div></div>
      <p className="mt-2 inline-flex rounded-full bg-brand-50 px-2.5 py-1 text-xs font-black text-brand-800 dark:bg-white/10 dark:text-gold-100">{user?.role || 'ADMIN'}</p>
    </div>
    {mode === 'admin' ? adminGroups.map(group => <div className="mb-5" key={group.title}><p className="mb-2 px-2 text-xs font-black uppercase tracking-widest text-gold-600">{group.title}</p><nav className="space-y-1">{group.items.map(item => <LinkItem key={item[1]} item={item} />)}</nav></div>) : <nav className="space-y-1">{clientItems.map(item => <LinkItem key={item[1]} item={item} />)}</nav>}
    <p className="mt-10 text-center text-xs text-slate-400">Lumyra v1.2 · Realtime Premium</p>
  </aside>;
}
