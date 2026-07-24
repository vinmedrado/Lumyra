import type { Metric } from '../../types/domain';
import { Card } from './Card';
const tone = { success: 'text-emerald-700 bg-emerald-50 dark:bg-emerald-500/15 dark:text-emerald-200', warning: 'text-amber-700 bg-amber-50 dark:bg-amber-500/15 dark:text-amber-200', danger: 'text-rose-700 bg-rose-50 dark:bg-rose-500/15 dark:text-rose-200', info: 'text-brand-800 bg-brand-50 dark:bg-brand-500/15 dark:text-brand-100', neutral: 'text-slate-700 bg-slate-50 dark:bg-white/10 dark:text-slate-200' };
export function MetricCard({ metric }: { metric: Metric }) {
  return <Card><p className="text-sm font-bold text-slate-500 dark:text-slate-300">{metric.label}</p><div className="mt-3 flex items-end justify-between gap-3"><strong className="text-4xl font-black text-ink dark:text-white">{metric.value}</strong><span className={`rounded-full px-3 py-1 text-xs font-black ${tone[metric.status || 'neutral']}`}>{metric.trend || metric.helper || 'Atual'}</span></div>{metric.helper && <p className="mt-3 text-sm text-slate-500 dark:text-slate-300">{metric.helper}</p>}</Card>;
}
