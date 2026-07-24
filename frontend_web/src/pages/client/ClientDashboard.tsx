import { useCallback, useEffect, useState } from 'react';
import { CalendarHeart, Heart, Sparkles } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { ErrorState } from '../../components/ui/ErrorState';
import { InsightCard } from '../../components/ui/InsightCard';
import { LoadingState } from '../../components/ui/LoadingState';
import { MetricCard } from '../../components/ui/MetricCard';
import { PageHeader } from '../../components/ui/PageHeader';
import { ProgressBar } from '../../components/ui/ProgressBar';
import { demoInsights } from '../../lib/demoData';
import { analyticsApi, eventsApi, hasStoredAccessToken, insightsApi } from '../../services/api';
import type { AnalyticsOverview, EventSummary, Insight, Metric } from '../../types/domain';

type ClientState = {
  event: EventSummary;
  analytics: AnalyticsOverview;
  insights: Insight[];
};

export function ClientDashboard() {
  const isVisualDemo = !hasStoredAccessToken();
  const [state, setState] = useState<ClientState | null>(null);
  const [loading, setLoading] = useState(!isVisualDemo);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (isVisualDemo) return;
    setLoading(true);
    setError('');
    try {
      const events = await eventsApi.list();
      if (!events.length) throw new Error('Nenhum evento disponível.');
      const event = events[0];
      const [analytics, insights] = await Promise.all([
        analyticsApi.overview(event.id),
        insightsApi.list(event.id),
      ]);
      setState({ event, analytics, insights });
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Não foi possível carregar o evento.');
    } finally {
      setLoading(false);
    }
  }, [isVisualDemo]);

  useEffect(() => { void load(); }, [load]);

  if (loading) return <LoadingState label="Preparando a visão do seu evento..." />;
  if (error) return <ErrorState description={error} onRetry={load} />;

  const analytics = state?.analytics;
  const confirmationRate = isVisualDemo ? 74 : Math.round(analytics?.confirmation_rate ?? 0);
  const metrics: Metric[] = [
    { label: 'Confirmados', value: isVisualDemo ? 184 : analytics?.confirmed ?? 0, helper: 'Presenças confirmadas', status: 'success' },
    { label: 'Pendentes', value: isVisualDemo ? 49 : analytics?.pending ?? 0, helper: 'Ainda aguardam resposta', status: 'warning' },
    { label: 'Não irão', value: isVisualDemo ? 15 : analytics?.declined ?? 0, helper: 'Respostas recusadas', status: 'info' },
  ];
  const insights = isVisualDemo ? demoInsights : state?.insights ?? [];

  return <>
    <PageHeader
      eyebrow={isVisualDemo ? 'Área dos noivos · demonstração' : 'Área dos noivos · dados reais'}
      title="Seu casamento está tomando forma"
      subtitle="Uma visão acolhedora para acompanhar confirmações e próximos passos."
    />
    <Card className="mb-6 overflow-hidden bg-gradient-to-br from-brand-900 via-brand-800 to-ink text-white">
      <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-3xl bg-white/15"><Heart /></div>
          <h2 className="lumyra-display text-4xl font-black">{state?.event.name || 'Ana & João'}</h2>
          <p className="mt-2 max-w-2xl text-purple-50">
            {state?.event.location ? `${state.event.location} · ${state.event.date || 'data em definição'}` : 'A Lumyra organiza o caminho até o grande dia.'}
          </p>
        </div>
        <div className="rounded-[1.7rem] border border-white/15 bg-white/15 p-5 text-center backdrop-blur">
          <p className="text-sm opacity-80">Confirmações</p>
          <strong className="text-5xl">{confirmationRate}%</strong>
          <p className="mt-1 text-xs text-gold-100">{isVisualDemo ? 'demonstração visual' : 'atualizado pela API'}</p>
        </div>
      </div>
    </Card>
    <div className="grid gap-4 md:grid-cols-3">{metrics.map(metric => <MetricCard key={metric.label} metric={metric} />)}</div>
    <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_.9fr]">
      <Card>
        <h2 className="flex items-center gap-2 text-xl font-black text-ink dark:text-white"><Sparkles className="text-gold-500" /> Resumo do evento</h2>
        <div className="mt-5 space-y-5">
          <ProgressBar value={confirmationRate} label="Confirmações recebidas" />
          <ProgressBar value={Math.max(0, 100 - Math.round(((analytics?.message_errors ?? 0) / Math.max(analytics?.total_guests ?? 1, 1)) * 100))} label="Comunicações sem erro" />
        </div>
      </Card>
      <Card>
        <h2 className="flex items-center gap-2 text-xl font-black text-ink dark:text-white"><CalendarHeart className="text-brand-700 dark:text-gold-100" /> Próximos passos</h2>
        <div className="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-300">
          {insights.slice(0, 4).map(item => <p key={item.title} className="rounded-2xl bg-brand-50 p-3 dark:bg-white/10">{item.action || item.message}</p>)}
        </div>
      </Card>
    </div>
    <section className="mt-6">
      <h2 className="mb-3 text-xl font-black text-ink dark:text-white">O que precisa de atenção</h2>
      <div className="grid gap-4 lg:grid-cols-3">{insights.slice(0, 3).map(item => <InsightCard key={item.title} insight={item} />)}</div>
    </section>
  </>;
}
