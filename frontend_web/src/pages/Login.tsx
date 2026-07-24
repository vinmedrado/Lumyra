import { useState, type FormEvent } from 'react';
import { useLocation } from 'wouter';
import { Sparkles } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { FormInput } from '../components/ui/FormInput';
import { useAuth } from '../hooks/useAuth';
import type { Role } from '../types/domain';
import logo from '../assets/branding/lumyra-logo.svg';
export function Login() {
  const { login, demoLogin } = useAuth(); const [, navigate] = useLocation(); const [email, setEmail] = useState('admin@local'); const [password, setPassword] = useState('admin123'); const [error, setError] = useState(''); const [loading, setLoading] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault(); setError(''); setLoading(true);
    try {
      const user = await login(email, password);
      navigate(user.role === 'CLIENT' ? '/client/dashboard' : '/admin/dashboard');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Não foi possível entrar. Verifique e-mail e senha.');
    } finally {
      setLoading(false);
    }
  }
  function demo(role: Role) { demoLogin(role); navigate(role === 'CLIENT' ? '/client/dashboard' : '/admin/dashboard'); }
  return <div className="grid min-h-screen place-items-center bg-[radial-gradient(circle_at_20%_10%,rgba(139,92,246,.22),transparent_30%),linear-gradient(135deg,#F7F8FB,#F1ECFF)] p-4 dark:bg-[radial-gradient(circle_at_20%_10%,rgba(139,92,246,.24),transparent_30%),linear-gradient(135deg,#09060f,#181210)]"><Card className="w-full max-w-xl"><img src={logo} alt="Lumyra" className="mb-5 h-20 w-auto dark:brightness-200" /><p className="text-sm font-black uppercase tracking-widest text-gold-600">Acesso à plataforma</p><h1 className="lumyra-display mt-2 text-4xl font-black text-ink dark:text-white">Entre na experiência Lumyra</h1><p className="mt-2 text-slate-500 dark:text-slate-300">Use login real da FastAPI ou modo demo visual para apresentação de portfólio, cliente ou recrutador.</p><form onSubmit={submit} className="mt-6 space-y-4"><FormInput label="E-mail" value={email} onChange={e => setEmail(e.target.value)} /><FormInput label="Senha" type="password" value={password} onChange={e => setPassword(e.target.value)} />{error && <p className="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700">{error}</p>}<Button className="w-full" disabled={loading}>{loading ? 'Entrando...' : 'Entrar com API'}</Button></form><div className="mt-6 rounded-3xl bg-brand-50 p-4 dark:bg-white/10"><div className="mb-3 flex items-center gap-2 text-sm font-black text-brand-800 dark:text-gold-100"><Sparkles size={16} /> Demo Mode</div><div className="grid gap-3 sm:grid-cols-3"><Button variant="secondary" onClick={() => demo('ADMIN')}>Assessoria</Button><Button variant="secondary" onClick={() => demo('CLIENT')}>Noivos</Button><Button variant="gold" onClick={() => navigate('/guest/lumyra-demo-invitation-token')}>Convidado</Button></div></div></Card></div>;
}
