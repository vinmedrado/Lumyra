import { Card } from '../../components/ui/Card';
import { MetricCard } from '../../components/ui/MetricCard';
import { PageHeader } from '../../components/ui/PageHeader';
import { ProgressBar } from '../../components/ui/ProgressBar';
import { getDemoStats, useDemoStore } from '../../demo/demoStore';

export function AnalyticsPage() {
  const state = useDemoStore();
  const stats = getDemoStats(state);
  const sent = state.campaigns.reduce((sum, campaign) => sum + campaign.sent, 0);
  const replies = state.campaigns.reduce((sum, campaign) => sum + campaign.replies, 0);
  const campaignRate = Math.round((replies / Math.max(sent, 1)) * 100);
  const costPerConfirmed = stats.contracted / Math.max(stats.confirmed, 1);

  return <><PageHeader eyebrow="Dados da demo integrada" title="Analytics" subtitle="Indicadores recalculados a cada RSVP, pagamento, campanha e alteração de mesa." /><div className="grid gap-4 md:grid-cols-3"><MetricCard metric={{ label: 'Taxa RSVP', value: `${stats.confirmationRate}%`, helper: `${stats.confirmed} de ${stats.total} confirmados`, status: 'success' }} /><MetricCard metric={{ label: 'Resposta campanha', value: `${campaignRate}%`, helper: `${replies} respostas recebidas`, status: 'info' }} /><MetricCard metric={{ label: 'Custo/confirmado', value: new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(costPerConfirmed), helper: 'estimativa dinâmica', status: 'neutral' }} /></div><Card className="mt-6"><h2 className="text-xl font-black text-ink dark:text-white">Saúde operacional</h2><div className="mt-5 space-y-5"><ProgressBar value={stats.confirmationRate} label="RSVP" /><ProgressBar value={stats.seatingRate} label="Confirmados com mesa" /><ProgressBar value={stats.financialRate} label="Financeiro quitado" /></div></Card></>;
}
