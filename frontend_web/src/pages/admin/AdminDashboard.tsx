import { useCallback, useEffect, useState } from 'react';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { ErrorState } from '../../components/ui/ErrorState';
import { InsightCard } from '../../components/ui/InsightCard';
import { LoadingState } from '../../components/ui/LoadingState';
import { MetricCard } from '../../components/ui/MetricCard';
import { PageHeader } from '../../components/ui/PageHeader';
import { ProgressBar } from '../../components/ui/ProgressBar';
import { demoActions, getDemoStats, useDemoStore } from '../../demo/demoStore';
import { analyticsApi, eventsApi, hasStoredAccessToken, insightsApi } from '../../services/api';
import type { AnalyticsOverview, EventSummary, Insight, Metric } from '../../types/domain';

type DashboardState = {
  event: EventSummary;
  analytics: AnalyticsOverview;
  insights: Insight[];
};

export function AdminDashboard() {
  const isVisualDemo = !hasStoredAccessToken();
  const demo = useDemoStore();
  const demoStats = getDemoStats(demo);
  const [state, setState] = useState<DashboardState | null>(null);
  const [loading, setLoading] = useState(!isVisualDemo);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (isVisualDemo) return;
    setLoading(true);
    setError('');
    try {
      const events = await eventsApi.list();
      if (!events.length) throw new Error('Nenhum evento cadastrado');
      const event = events[0];
      const [analytics, insights] = await Promise.all([
        analyticsApi.overview(event.id),
        insightsApi.list(event.id),
      ]);
      setState({ event, analytics, insights });
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Não foi possível carregar o dashboard.');
    } finally {
      setLoading(false);
    }
  }, [isVisualDemo]);

  useEffect(() => { void load(); }, [load]);

  if (loading) return <LoadingState label="Carregando indicadores reais..." />;
  if (error) return <ErrorState description={error} onRetry={load} />;

  const analytics = state?.analytics;
  const metrics: Metric[] = isVisualDemo ? [
    { label: 'Convidados', value: demoStats.total, helper: 'Lista compartilhada', status: 'info' },
    { label: 'Confirmados', value: demoStats.confirmed, helper: `${demoStats.confirmationRate}% de confirmação`, status: 'success' },
    { label: 'Pendentes', value: demoStats.pending, helper: 'Precisam de contato', status: 'warning' },
    { label: 'Mensagens com erro', value: demo.messages.filter(item => item.status === 'failed').length, helper: 'Revisar telefone', status: 'danger' },
  ] : [
    { label: 'Convidados', value: analytics?.total_guests ?? 0, helper: 'Total cadastrado', status: 'info' },
    { label: 'Confirmados', value: analytics?.confirmed ?? 0, helper: `${analytics?.confirmation_rate ?? 0}% de confirmação`, status: 'success' },
    { label: 'Pendentes', value: analytics?.pending ?? 0, helper: 'Aguardando resposta', status: 'warning' },
    { label: 'Erros de mensagem', value: analytics?.message_errors ?? 0, helper: 'Exigem revisão', status: analytics?.message_errors ? 'danger' : 'success' },
  ];
  const insights: Insight[] = isVisualDemo ? [
    { severity: demoStats.pending ? 'warning' : 'info', title: 'RSVP pendente', message: `${demoStats.pending} convidados ainda não responderam.`, action: 'Enviar lembrete', count: demoStats.pending, related_page: '/admin/campaigns' },
    { severity: demoStats.confirmed - demoStats.seated ? 'critical' : 'info', title: 'Confirmados sem mesa', message: `${demoStats.confirmed - demoStats.seated} confirmados precisam de alocação.`, action: 'Revisar mesas', count: demoStats.confirmed - demoStats.seated, related_page: '/admin/tables' },
    { severity: 'info', title: 'Progresso financeiro', message: `${demoStats.financialRate}% do valor contratado já foi pago.`, action: 'Ver financeiro', count: demoStats.financialRate, related_page: '/admin/financial' },
  ] : state?.insights ?? [];
  const confirmationRate = isVisualDemo ? demoStats.confirmationRate : Math.round(analytics?.confirmation_rate ?? 0);
  const tableRate = isVisualDemo
    ? demoStats.seatingRate
    : Math.round(
      ((analytics?.table_occupancy.reduce((sum, table) => sum + table.occupied, 0) ?? 0)
        / Math.max(analytics?.total_guests ?? 0, 1)) * 100,
    );
  const financialRate = isVisualDemo
    ? demoStats.financialRate
    : Math.round(((analytics?.financial.paid ?? 0) / Math.max(analytics?.financial.contracted ?? 0, 1)) * 100);

  return <>
    <PageHeader
      eyebrow={isVisualDemo ? 'Operação · demonstração visual' : 'Operação · dados reais'}
      title={state?.event.name || demo.event.name}
      subtitle="Visão executiva do evento, pendências, comunicação e próximos passos."
      actions={<Button onClick={() => demoActions.sendCampaign(3)}>Enviar lembrete RSVP</Button>}
    />
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {metrics.map(metric => <MetricCard key={metric.label} metric={metric} />)}
    </div>
    <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_.9fr]">
      <Card>
        <h2 className="text-xl font-black text-ink dark:text-white">Progresso operacional</h2>
        <div className="mt-5 space-y-5">
          <ProgressBar value={confirmationRate} label="Confirmações" />
          <ProgressBar value={tableRate} label="Convidados com mesa" />
          <ProgressBar value={financialRate} label="Financeiro pago" />
        </div>
      </Card>
      <Card>
        <h2 className="text-xl font-black text-ink dark:text-white">Próximos passos</h2>
        <ol className="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-300">
          <li><strong>1.</strong> Revisar {demo.messages.filter(item => item.status === 'failed').length} mensagem(ns) com erro</li>
          <li><strong>2.</strong> Organizar {demoStats.confirmed - demoStats.seated} confirmado(s) sem mesa</li>
          <li><strong>3.</strong> Cobrar {demoStats.pending} RSVP pendente(s)</li>
          <li><strong>4.</strong> Conferir {demo.documents.filter(item => !item.viewed).length} documento(s) não visualizado(s)</li>
        </ol>
      </Card>
    </div>
    <section className="mt-6 grid gap-4 lg:grid-cols-3">
      {insights.slice(0, 6).map(insight => <InsightCard key={insight.title} insight={insight} />)}
    </section>
  </>;
}
