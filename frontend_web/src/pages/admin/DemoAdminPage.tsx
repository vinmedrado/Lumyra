import { BarChart3, CalendarDays, FileText, Lightbulb, MessageCircle, Send, Settings, ShieldCheck, Table2, Wallet } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { DataTable } from '../../components/ui/DataTable';
import { MetricCard } from '../../components/ui/MetricCard';
import { PageHeader } from '../../components/ui/PageHeader';
import { ProgressBar } from '../../components/ui/ProgressBar';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { demoActions, getDemoStats, useDemoStore, type DemoCampaign, type DemoDocument, type DemoExpense, type DemoForm, type DemoMessage } from '../../demo/demoStore';

export type AdminDemoModule = 'events' | 'tables' | 'forms' | 'campaigns' | 'whatsapp' | 'financial' | 'documents' | 'insights' | 'audit' | 'settings';

const money = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });
const date = (value: string) => new Date(`${value}T12:00:00`).toLocaleDateString('pt-BR');

function statusTone(status: string) {
  if (['confirmed', 'sent', 'read', 'delivered', 'success'].includes(status)) return 'success' as const;
  if (['pending', 'scheduled', 'queued', 'warning'].includes(status)) return 'warning' as const;
  if (['failed'].includes(status)) return 'danger' as const;
  return 'neutral' as const;
}

function EventsModule() {
  const state = useDemoStore();
  const stats = getDemoStats(state);
  return <>
    <PageHeader eyebrow="Portfólio · operação realista" title="Eventos" subtitle="Visão central do evento, equipe, capacidade e marcos operacionais." actions={<Button><CalendarDays size={16} /> Novo evento</Button>} />
    <Card className="overflow-hidden bg-gradient-to-br from-brand-950 via-brand-800 to-ink text-white">
      <div className="grid gap-6 lg:grid-cols-[1.2fr_.8fr]">
        <div><StatusBadge status="success">{state.event.status}</StatusBadge><h2 className="lumyra-display mt-5 text-5xl font-black">{state.event.name}</h2><p className="mt-3 text-purple-100">{date(state.event.date)} · {state.event.ceremonyTime} · {state.event.location}</p></div>
        <div className="grid grid-cols-2 gap-3"><div className="rounded-3xl bg-white/10 p-4"><p className="text-xs uppercase tracking-widest text-purple-200">Convidados</p><strong className="mt-2 block text-4xl">{stats.total}</strong></div><div className="rounded-3xl bg-white/10 p-4"><p className="text-xs uppercase tracking-widest text-purple-200">Mesas</p><strong className="mt-2 block text-4xl">{state.tables.length}</strong></div><div className="rounded-3xl bg-white/10 p-4"><p className="text-xs uppercase tracking-widest text-purple-200">Fornecedores</p><strong className="mt-2 block text-4xl">{state.expenses.length}</strong></div><div className="rounded-3xl bg-white/10 p-4"><p className="text-xs uppercase tracking-widest text-purple-200">Etapas</p><strong className="mt-2 block text-4xl">{state.timeline.filter(item => item.completed).length}/{state.timeline.length}</strong></div></div>
      </div>
    </Card>
    <div className="mt-6 grid gap-4 md:grid-cols-3"><MetricCard metric={{ label: 'RSVP', value: `${stats.confirmationRate}%`, helper: `${stats.confirmed} confirmados`, status: 'success' }} /><MetricCard metric={{ label: 'Financeiro', value: `${stats.financialRate}%`, helper: `${money.format(stats.paid)} pagos`, status: 'info' }} /><MetricCard metric={{ label: 'Próximo marco', value: '30 jul', helper: 'Revisar convidados', status: 'warning' }} /></div>
  </>;
}

function TablesModule() {
  const state = useDemoStore();
  const confirmed = state.guests.filter(guest => guest.status === 'confirmed');
  return <>
    <PageHeader eyebrow="Mapa interativo" title="Mesas" subtitle="Distribuição de convidados confirmados. Altere uma mesa e confira a área dos noivos." />
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{state.tables.map(table => {
      const guests = confirmed.filter(guest => guest.tableId === table.id);
      const rate = Math.round((guests.length / table.capacity) * 100);
      return <Card key={table.id}><div className="flex items-center justify-between"><div className="grid h-11 w-11 place-items-center rounded-2xl bg-brand-50 text-brand-800"><Table2 /></div><StatusBadge status={rate >= 90 ? 'warning' : 'success'}>{guests.length}/{table.capacity}</StatusBadge></div><h3 className="mt-4 text-xl font-black text-ink dark:text-white">{table.name}</h3><p className="text-sm text-slate-500">{table.zone}</p><div className="mt-4"><ProgressBar value={rate} label="Ocupação" /></div><p className="mt-4 text-xs leading-5 text-slate-500">{guests.map(guest => guest.name).join(' · ') || 'Mesa disponível'}</p></Card>;
    })}</div>
    <Card className="mt-6"><h2 className="text-xl font-black text-ink dark:text-white">Alocação rápida</h2><div className="mt-4 grid gap-3">{confirmed.map(guest => <div key={guest.id} className="flex flex-col gap-2 rounded-2xl bg-slate-50 p-3 dark:bg-white/10 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-bold text-ink dark:text-white">{guest.name}</p><p className="text-xs text-slate-500">{guest.group}</p></div><select aria-label={`Mesa de ${guest.name}`} value={guest.tableId || ''} onChange={event => demoActions.assignGuestTable(guest.id, event.target.value ? Number(event.target.value) : null)} className="rounded-xl border border-brand-100 bg-white px-3 py-2 text-sm"><option value="">Sem mesa</option>{state.tables.map(table => <option key={table.id} value={table.id}>{table.name}</option>)}</select></div>)}</div></Card>
  </>;
}

function FormsModule() {
  const state = useDemoStore();
  return <>
    <PageHeader eyebrow="Respostas estruturadas" title="Formulários" subtitle="Campos dinâmicos conectam RSVP, transporte e necessidades dos convidados." actions={<Button><FileText size={16} /> Novo formulário</Button>} />
    <div className="grid gap-4 lg:grid-cols-3">{state.forms.map((form: DemoForm) => <Card key={form.id}><div className="flex items-center justify-between"><FileText className="text-brand-700" /><StatusBadge status={form.active ? 'success' : 'neutral'}>{form.active ? 'Ativo' : 'Rascunho'}</StatusBadge></div><h3 className="mt-4 text-lg font-black dark:text-white">{form.name}</h3><p className="mt-1 text-sm text-slate-500">{form.fields} campos · {form.responses} respostas</p><div className="mt-4"><ProgressBar value={Math.round((form.responses / Math.max(state.guests.length, 1)) * 100)} label="Cobertura" /></div></Card>)}</div>
    <Card className="mt-6"><h2 className="text-xl font-black dark:text-white">Resumo das respostas</h2><div className="mt-4 grid gap-4 md:grid-cols-3"><MetricCard metric={{ label: 'Precisam de transporte', value: state.guests.filter(guest => guest.needsBus).length, status: 'info' }} /><MetricCard metric={{ label: 'Restrições alimentares', value: state.guests.filter(guest => guest.dietary).length, status: 'warning' }} /><MetricCard metric={{ label: 'Famílias respondidas', value: new Set(state.guests.filter(guest => guest.status !== 'pending').map(guest => guest.group)).size, status: 'success' }} /></div></Card>
  </>;
}

function CampaignsModule() {
  const state = useDemoStore();
  return <>
    <PageHeader eyebrow="Automação de comunicação" title="Campanhas" subtitle="Segmentação, agendamento, entrega e respostas em um único fluxo." actions={<Button><MessageCircle size={16} /> Nova campanha</Button>} />
    <div className="grid gap-4">{state.campaigns.map((campaign: DemoCampaign) => <Card key={campaign.id}><div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between"><div><div className="flex items-center gap-2"><h3 className="text-xl font-black dark:text-white">{campaign.name}</h3><StatusBadge status={statusTone(campaign.status)}>{campaign.status}</StatusBadge></div><p className="mt-1 text-sm text-slate-500">{campaign.audience} · {campaign.scheduledAt}</p></div><div className="grid grid-cols-4 gap-4 text-center text-sm"><div><strong className="block text-xl dark:text-white">{campaign.sent}</strong><span className="text-slate-400">Enviadas</span></div><div><strong className="block text-xl dark:text-white">{campaign.delivered}</strong><span className="text-slate-400">Entregues</span></div><div><strong className="block text-xl dark:text-white">{campaign.read}</strong><span className="text-slate-400">Lidas</span></div><div><strong className="block text-xl dark:text-white">{campaign.replies}</strong><span className="text-slate-400">Respostas</span></div></div>{campaign.status !== 'sent' && <Button onClick={() => demoActions.sendCampaign(campaign.id)}><Send size={15} /> Enviar agora</Button>}</div></Card>)}</div>
  </>;
}

function WhatsAppModule() {
  const state = useDemoStore();
  const failures = state.messages.filter(item => item.status === 'failed').length;
  return <>
    <PageHeader eyebrow="Provider demonstrativo" title="WhatsApp" subtitle="Logs auditáveis de envio, leitura, fila e falhas por convidado." />
    <div className="mb-6 grid gap-4 md:grid-cols-3"><MetricCard metric={{ label: 'Entregues/lidas', value: state.messages.filter(item => ['delivered', 'read'].includes(item.status)).length, status: 'success' }} /><MetricCard metric={{ label: 'Na fila', value: state.messages.filter(item => item.status === 'queued').length, status: 'warning' }} /><MetricCard metric={{ label: 'Falhas', value: failures, status: failures ? 'danger' : 'success' }} /></div>
    <DataTable<DemoMessage> rows={state.messages} columns={[{ key: 'guest', header: 'Convidado' }, { key: 'template', header: 'Template' }, { key: 'channel', header: 'Canal' }, { key: 'status', header: 'Status', render: row => <StatusBadge status={statusTone(row.status)}>{row.status}</StatusBadge> }, { key: 'sentAt', header: 'Enviado em' }]} />
  </>;
}

function FinancialModule() {
  const state = useDemoStore();
  const stats = getDemoStats(state);
  return <>
    <PageHeader eyebrow="Controle financeiro" title="Financeiro" subtitle="Contratos, vencimentos e pagamentos refletidos também na visão dos noivos." actions={<Button><Wallet size={16} /> Nova despesa</Button>} />
    <div className="mb-6 grid gap-4 md:grid-cols-3"><MetricCard metric={{ label: 'Contratado', value: money.format(stats.contracted), status: 'info' }} /><MetricCard metric={{ label: 'Pago', value: money.format(stats.paid), status: 'success' }} /><MetricCard metric={{ label: 'Pendente', value: money.format(stats.contracted - stats.paid), status: 'warning' }} /></div>
    <DataTable<DemoExpense> rows={state.expenses} columns={[{ key: 'vendor', header: 'Fornecedor' }, { key: 'category', header: 'Categoria' }, { key: 'amount', header: 'Valor', render: row => money.format(row.amount) }, { key: 'dueDate', header: 'Vencimento', render: row => date(row.dueDate) }, { key: 'paid', header: 'Situação', render: row => <button onClick={() => demoActions.toggleExpensePaid(row.id)}><StatusBadge status={row.paid ? 'success' : 'warning'}>{row.paid ? 'Pago' : 'Marcar como pago'}</StatusBadge></button> }]} />
  </>;
}

function DocumentsModule() {
  const state = useDemoStore();
  return <>
    <PageHeader eyebrow="Central de arquivos" title="Documentos" subtitle="Contratos e materiais compartilhados, com confirmação de visualização pelos noivos." actions={<Button><FileText size={16} /> Enviar arquivo</Button>} />
    <div className="grid gap-4 md:grid-cols-2">{state.documents.map((document: DemoDocument) => <Card key={document.id}><div className="flex items-start justify-between gap-3"><div className="grid h-12 w-12 place-items-center rounded-2xl bg-brand-50 text-brand-800"><FileText /></div><StatusBadge status={document.viewed ? 'success' : 'warning'}>{document.viewed ? 'Visualizado' : 'Aguardando leitura'}</StatusBadge></div><h3 className="mt-4 font-black dark:text-white">{document.name}</h3><p className="mt-1 text-sm text-slate-500">{document.category} · por {document.owner} · {document.updatedAt}</p></Card>)}</div>
  </>;
}

function InsightsModule() {
  const state = useDemoStore();
  const stats = getDemoStats(state);
  const withoutTable = state.guests.filter(guest => guest.status === 'confirmed' && !guest.tableId).length;
  return <>
    <PageHeader eyebrow="Inteligência operacional" title="Insights" subtitle="Sinais calculados a partir do estado atual da demonstração." />
    <div className="grid gap-4 lg:grid-cols-3">
      <Card><Lightbulb className="text-amber-500" /><h3 className="mt-4 text-xl font-black dark:text-white">{stats.pending} RSVP pendentes</h3><p className="mt-2 text-sm text-slate-500">A campanha de lembrete pode ser enviada diretamente na aba Campanhas.</p></Card>
      <Card><Table2 className="text-brand-700" /><h3 className="mt-4 text-xl font-black dark:text-white">{withoutTable} confirmados sem mesa</h3><p className="mt-2 text-sm text-slate-500">Distribua essas pessoas antes do fechamento do layout.</p></Card>
      <Card><BarChart3 className="text-emerald-600" /><h3 className="mt-4 text-xl font-black dark:text-white">{stats.financialRate}% do financeiro pago</h3><p className="mt-2 text-sm text-slate-500">{money.format(stats.contracted - stats.paid)} ainda aguardam pagamento.</p></Card>
    </div>
  </>;
}

function AuditModule() {
  const state = useDemoStore();
  return <>
    <PageHeader eyebrow="Governança" title="Auditoria" subtitle="Registro das ações realizadas pelas personas e automações da demonstração." />
    <DataTable rows={state.audit} columns={[{ key: 'createdAt', header: 'Quando' }, { key: 'actor', header: 'Responsável' }, { key: 'action', header: 'Ação' }, { key: 'entity', header: 'Entidade' }, { key: 'result', header: 'Resultado', render: row => <StatusBadge status={row.result === 'success' ? 'success' : 'warning'}>{row.result}</StatusBadge> }]} />
  </>;
}

function SettingsModule() {
  const state = useDemoStore();
  const options: Array<{ key: keyof typeof state.settings; title: string; description: string }> = [
    { key: 'whatsappConnected', title: 'WhatsApp conectado', description: 'Habilita campanhas e logs do provider demonstrativo.' },
    { key: 'remindersEnabled', title: 'Lembretes automáticos', description: 'Agenda comunicações para convidados com RSVP pendente.' },
    { key: 'clientPortalEnabled', title: 'Portal dos noivos', description: 'Compartilha indicadores e arquivos com o casal.' },
  ];
  return <>
    <PageHeader eyebrow="Tenant Lumyra Demo" title="Configurações" subtitle="Preferências operacionais da assessoria e integrações do evento." />
    <div className="grid gap-4">{options.map(option => <Card key={option.key} className="flex items-center justify-between gap-5"><div><h3 className="flex items-center gap-2 font-black dark:text-white"><Settings size={17} /> {option.title}</h3><p className="mt-1 text-sm text-slate-500">{option.description}</p></div><button role="switch" aria-checked={state.settings[option.key]} onClick={() => demoActions.updateSetting(option.key, !state.settings[option.key])} className={`relative h-8 w-14 rounded-full transition ${state.settings[option.key] ? 'bg-brand-700' : 'bg-slate-300'}`}><span className={`absolute top-1 h-6 w-6 rounded-full bg-white transition ${state.settings[option.key] ? 'left-7' : 'left-1'}`} /></button></Card>)}</div>
    <Card className="mt-6"><div className="flex items-center gap-3"><ShieldCheck className="text-emerald-600" /><div><h3 className="font-black dark:text-white">Ambiente seguro de demonstração</h3><p className="text-sm text-slate-500">Todos os dados são fictícios e permanecem apenas neste navegador.</p></div></div></Card>
  </>;
}

export function DemoAdminPage({ module }: { module: AdminDemoModule }) {
  if (module === 'events') return <EventsModule />;
  if (module === 'tables') return <TablesModule />;
  if (module === 'forms') return <FormsModule />;
  if (module === 'campaigns') return <CampaignsModule />;
  if (module === 'whatsapp') return <WhatsAppModule />;
  if (module === 'financial') return <FinancialModule />;
  if (module === 'documents') return <DocumentsModule />;
  if (module === 'insights') return <InsightsModule />;
  if (module === 'audit') return <AuditModule />;
  return <SettingsModule />;
}
