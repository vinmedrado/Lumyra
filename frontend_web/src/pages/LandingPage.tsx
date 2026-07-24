import { Link } from 'wouter';
import { ArrowRight, BarChart3, BellRing, HeartHandshake, MessageCircle, Sparkles, Users, Zap } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import logoDark from '../assets/branding/lumyra-logo-dark.svg';
import mark from '../assets/branding/lumyra-icon.svg';
const modules = [
  ['Gestão operacional', 'Eventos, convidados, mesas, tarefas e documentos em uma operação integrada.', Users],
  ['Experiência dos noivos', 'Painel simples, emocional e premium para acompanhar o grande dia.', HeartHandshake],
  ['Portal dos convidados', 'Confirmação mobile-first com RSVP, transporte e respostas dinâmicas.', Sparkles],
  ['WhatsApp e automação', 'Campanhas, retries, logs, alertas e workflows conectados.', MessageCircle],
  ['Analytics', 'Tendências de RSVP, mensagens, financeiro e ocupação de mesas.', BarChart3],
  ['Realtime collaboration', 'Notificações, presença online, feed de atividade e command center.', Zap]
] as const;
export function LandingPage() {
  return <div className="min-h-screen overflow-hidden bg-ice text-ink dark:bg-[#09060f] dark:text-ice">
    <section className="lumyra-hero relative text-white">
      <div className="absolute inset-0 opacity-30 [background-image:radial-gradient(circle_at_1px_1px,rgba(255,255,255,.25)_1px,transparent_0)] [background-size:28px_28px]" />
      <header className="relative mx-auto flex max-w-7xl items-center justify-between p-6">
        <img src={logoDark} alt="Lumyra" className="h-16 w-auto" />
        <div className="flex gap-3"><Link href="/guest/lumyra-demo-invitation-token" className="hidden sm:block"><Button variant="secondary">Portal convidado</Button></Link><Link href="/login"><Button variant="gold">Explore Demo</Button></Link></div>
      </header>
      <main className="relative mx-auto grid max-w-7xl items-center gap-10 px-6 pb-24 pt-10 lg:grid-cols-[1.06fr_.94fr]">
        <div className="animate-fadeUp"><p className="mb-4 text-sm font-black uppercase tracking-[.28em] text-gold-100">Modern Event Operations Platform</p><h1 className="lumyra-display max-w-5xl text-5xl font-black leading-[.96] md:text-7xl">A operação de eventos com aparência, inteligência e fluidez de SaaS premium.</h1><p className="mt-6 max-w-2xl text-lg leading-8 text-purple-50">Lumyra conecta assessoria, noivos e convidados em uma experiência moderna com WhatsApp, RSVP, financeiro, documentos, analytics e colaboração em tempo real.</p><div className="mt-8 flex flex-wrap gap-3"><Link href="/login"><Button variant="gold">Explore Demo <ArrowRight size={17} /></Button></Link><Link href="/guest/lumyra-demo-invitation-token"><Button variant="secondary">Abrir convite digital</Button></Link></div></div>
        <Card className="animate-fadeUp border-white/20 bg-white/95 text-ink shadow-glow dark:bg-white/10 dark:text-white"><div className="flex items-center justify-between"><div><p className="text-sm font-black uppercase tracking-widest text-brand-700 dark:text-gold-100">Command Center</p><h2 className="mt-2 text-3xl font-black">74% confirmado</h2></div><span className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-xs font-black text-emerald-700"><span className="live-dot h-2 w-2 rounded-full bg-emerald-500" />Live</span></div><div className="mt-5 h-3 rounded-full bg-brand-50 dark:bg-white/10"><div className="h-3 w-[74%] rounded-full bg-gradient-to-r from-brand-800 to-gold-500" /></div><div className="mt-6 grid grid-cols-2 gap-3 text-sm"><div className="rounded-3xl bg-brand-50 p-4 dark:bg-white/10"><strong className="text-2xl">248</strong><p>convidados</p></div><div className="rounded-3xl bg-gold-50 p-4 dark:bg-white/10"><strong className="text-2xl">18</strong><p>sem mesa</p></div><div className="rounded-3xl bg-rose-50 p-4 dark:bg-white/10"><strong className="text-2xl">6</strong><p>alertas críticos</p></div><div className="rounded-3xl bg-emerald-50 p-4 dark:bg-white/10"><strong className="text-2xl">R$ 82k</strong><p>contratado</p></div></div></Card>
      </main>
    </section>
    <section className="mx-auto max-w-7xl px-6 py-20"><div className="mb-10 flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><p className="text-sm font-black uppercase tracking-[.24em] text-gold-600">Uma plataforma, três experiências</p><h2 className="lumyra-display mt-3 text-4xl font-black md:text-5xl">Assessoria, noivos e convidados com a mesma identidade premium.</h2></div><img src={mark} className="h-16 w-16" alt="Lumyra mark" /></div><div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">{modules.map(([title, text, Icon]) => <Card key={title} className="min-h-44"><div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-800 dark:bg-white/10 dark:text-gold-100"><Icon /></div><h3 className="text-xl font-black">{title}</h3><p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{text}</p></Card>)}</div></section>
    <section className="mx-auto max-w-7xl px-6 pb-20"><div className="rounded-[2rem] bg-gradient-to-br from-brand-900 to-ink p-8 text-white shadow-glow md:p-12"><BellRing className="mb-4 text-gold-100" /><h2 className="lumyra-display text-4xl font-black">Pronta para apresentação, venda e evolução SaaS.</h2><p className="mt-3 max-w-3xl text-purple-50">A identidade Lumyra foi aplicada em landing, login, áreas autenticadas, portal público, dark mode, componentes, favicon e documentação visual.</p><Link href="/login" className="mt-6 inline-block"><Button variant="gold">Entrar agora</Button></Link></div></section>
  </div>;
}
