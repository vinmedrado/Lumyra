import type { Insight } from '../../types/domain';
import { StatusBadge } from './StatusBadge';
const map = { critical: 'danger', warning: 'warning', info: 'info' } as const;
export function InsightCard({ insight }: { insight: Insight }) { return <div className="rounded-2xl border border-slate-200 bg-white p-4"><div className="flex items-start justify-between gap-3"><div><h3 className="font-bold text-ink">{insight.title}</h3><p className="mt-1 text-sm text-slate-500">{insight.message}</p>{insight.action && <p className="mt-3 text-sm font-semibold text-brand-600">{insight.action}</p>}</div><StatusBadge status={map[insight.severity]}>{insight.count ?? insight.severity}</StatusBadge></div></div>; }
