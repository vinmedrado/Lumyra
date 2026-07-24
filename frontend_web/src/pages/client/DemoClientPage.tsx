import { Eye, FileText, MessageCircle, Table2 } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { DataTable } from '../../components/ui/DataTable';
import { MetricCard } from '../../components/ui/MetricCard';
import { PageHeader } from '../../components/ui/PageHeader';
import { ProgressBar } from '../../components/ui/ProgressBar';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { demoActions, getDemoStats, useDemoStore, type DemoDocument, type DemoExpense, type DemoGuest, type DemoTimelineItem } from '../../demo/demoStore';

export type ClientDemoModule = 'guests' | 'rsvp' | 'tables' | 'timeline' | 'documents' | 'financial' | 'messages';

const money = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });
const date = (value: string) => new Date(`${value}T12:00:00`).toLocaleDateString('pt-BR');
const rsvpLabel = { confirmed: 'Confirmado', pending: 'Aguardando', declined: 'Não irá' } as const;

function GuestsModule() {
  const state = useDemoStore();
  return <>
    <PageHeader eyebrow="Lista compartilhada" title="Seus convidados" subtitle="Uma visão simples da lista mantida pela assessoria." />
    <DataTable<DemoGuest> rows={state.guests} columns={[{ key: 'name', header: 'Nome' }, { key: 'group', header: 'Grupo' }, { key: 'category', header: 'Categoria' }, { key: 'status', header: 'Resposta', render: row => <StatusBadge status={row.status === 'confirmed' ? 'success' : row.status === 'pending' ? 'warning' : 'neutral'}>{rsvpLabel[row.status]}</StatusBadge> }]} />
  </>;
}

function RsvpModule() {
  const state = useDemoStore();
  const stats = getDemoStats(state);
  return <>
    <PageHeader eyebrow="Atualização em tempo real" title="Confirmações" subtitle="As respostas do convite digital aparecem aqui e na assessoria." />
    <div className="grid gap-4 md:grid-cols-3"><MetricCard metric={{ label: 'Confirmados', value: stats.confirmed, status: 'success' }} /><MetricCard metric={{ label: 'Aguardando', value: stats.pending, status: 'warning' }} /><MetricCard metric={{ label: 'Não irão', value: stats.declined, status: 'neutral' }} /></div>
    <Card className="mt-6"><ProgressBar value={stats.confirmationRate} label="Taxa de confirmação" /><div className="mt-5 grid gap-3">{state.guests.map(guest => <div key={guest.id} className="flex items-center justify-between rounded-2xl bg-slate-50 p-3 dark:bg-white/10"><div><p className="font-bold dark:text-white">{guest.name}</p><p className="text-xs text-slate-500">{guest.group}</p></div><StatusBadge status={guest.status === 'confirmed' ? 'success' : guest.status === 'pending' ? 'warning' : 'neutral'}>{rsvpLabel[guest.status]}</StatusBadge></div>)}</div></Card>
  </>;
}

function TablesModule() {
  const state = useDemoStore();
  return <>
    <PageHeader eyebrow="Organização do salão" title="Mapa de mesas" subtitle="A assessoria atualiza a distribuição e vocês acompanham o resultado." />
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{state.tables.map(table => {
      const guests = state.guests.filter(guest => guest.tableId === table.id && guest.status === 'confirmed');
      return <Card key={table.id}><div className="flex items-center justify-between"><Table2 className="text-brand-700" /><StatusBadge status="info">{guests.length}/{table.capacity}</StatusBadge></div><h3 className="mt-4 text-xl font-black dark:text-white">{table.name}</h3><p className="text-sm text-slate-500">{table.zone}</p><div className="mt-4 space-y-2">{guests.map(guest => <p key={guest.id} className="rounded-xl bg-brand-50 px-3 py-2 text-sm font-bold text-brand-900 dark:bg-white/10 dark:text-purple-50">{guest.name}</p>)}</div></Card>;
    })}</div>
  </>;
}

function TimelineModule() {
  const state = useDemoStore();
  return <>
    <PageHeader eyebrow="Caminho até o grande dia" title="Timeline" subtitle="Marque decisões concluídas; a atualização também entra no histórico da assessoria." />
    <Card><div className="relative border-l-2 border-brand-100 pl-6">{state.timeline.map((item: DemoTimelineItem) => <div key={item.id} className="relative mb-6 last:mb-0"><span className={`absolute -left-[31px] top-1 grid h-4 w-4 place-items-center rounded-full ${item.completed ? 'bg-emerald-500' : 'bg-brand-300'}`} /><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><p className={`font-black ${item.completed ? 'text-emerald-700 line-through' : 'text-ink dark:text-white'}`}>{item.title}</p><p className="text-sm text-slate-500">{date(item.date)} · {item.owner}</p></div>{item.title !== 'Casamento' && <Button variant="secondary" onClick={() => demoActions.toggleTimeline(item.id)}>{item.completed ? 'Reabrir' : 'Concluir'}</Button>}</div></div>)}</div></Card>
  </>;
}

function DocumentsModule() {
  const state = useDemoStore();
  return <>
    <PageHeader eyebrow="Arquivos compartilhados" title="Documentos" subtitle="Materiais importantes organizados sem depender de e-mails e conversas antigas." />
    <div className="grid gap-4 md:grid-cols-2">{state.documents.map((document: DemoDocument) => <Card key={document.id}><div className="flex items-start justify-between"><FileText className="text-brand-700" /><StatusBadge status={document.viewed ? 'success' : 'warning'}>{document.viewed ? 'Visto' : 'Novo'}</StatusBadge></div><h3 className="mt-4 font-black dark:text-white">{document.name}</h3><p className="mt-1 text-sm text-slate-500">{document.category} · atualizado {document.updatedAt}</p><Button variant="secondary" className="mt-4" onClick={() => demoActions.markDocumentViewed(document.id)}><Eye size={15} /> Visualizar</Button></Card>)}</div>
  </>;
}

function FinancialModule() {
  const state = useDemoStore();
  const stats = getDemoStats(state);
  return <>
    <PageHeader eyebrow="Resumo transparente" title="Financeiro" subtitle="Acompanhamento simplificado dos contratos e pagamentos do evento." />
    <div className="grid gap-4 md:grid-cols-3"><MetricCard metric={{ label: 'Investimento', value: money.format(stats.contracted), status: 'info' }} /><MetricCard metric={{ label: 'Já pago', value: money.format(stats.paid), status: 'success' }} /><MetricCard metric={{ label: 'A pagar', value: money.format(stats.contracted - stats.paid), status: 'warning' }} /></div>
    <Card className="mt-6"><ProgressBar value={stats.financialRate} label="Progresso financeiro" /></Card>
    <div className="mt-6"><DataTable<DemoExpense> rows={state.expenses} columns={[{ key: 'vendor', header: 'Fornecedor' }, { key: 'category', header: 'Categoria' }, { key: 'amount', header: 'Valor', render: row => money.format(row.amount) }, { key: 'paid', header: 'Situação', render: row => <StatusBadge status={row.paid ? 'success' : 'warning'}>{row.paid ? 'Pago' : `Vence ${date(row.dueDate)}`}</StatusBadge> }]} /></div>
  </>;
}

function MessagesModule() {
  const state = useDemoStore();
  return <>
    <PageHeader eyebrow="Comunicação com convidados" title="Mensagens" subtitle="Histórico resumido das campanhas conduzidas pela assessoria." />
    <div className="grid gap-4">{state.campaigns.map(campaign => <Card key={campaign.id}><div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div><h3 className="flex items-center gap-2 text-lg font-black dark:text-white"><MessageCircle size={18} /> {campaign.name}</h3><p className="mt-1 text-sm text-slate-500">{campaign.audience} · {campaign.scheduledAt}</p></div><div className="flex gap-4 text-center"><div><strong className="block text-xl dark:text-white">{campaign.delivered}</strong><span className="text-xs text-slate-400">entregues</span></div><div><strong className="block text-xl dark:text-white">{campaign.read}</strong><span className="text-xs text-slate-400">lidas</span></div><div><strong className="block text-xl dark:text-white">{campaign.replies}</strong><span className="text-xs text-slate-400">respostas</span></div></div></div></Card>)}</div>
  </>;
}

export function DemoClientPage({ module }: { module: ClientDemoModule }) {
  if (module === 'guests') return <GuestsModule />;
  if (module === 'rsvp') return <RsvpModule />;
  if (module === 'tables') return <TablesModule />;
  if (module === 'timeline') return <TimelineModule />;
  if (module === 'documents') return <DocumentsModule />;
  if (module === 'financial') return <FinancialModule />;
  return <MessagesModule />;
}
