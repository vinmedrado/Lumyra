import type { Status } from '../../types/domain';
const cls: Record<Status, string> = { success: 'bg-emerald-50 text-emerald-700 ring-emerald-200', warning: 'bg-amber-50 text-amber-700 ring-amber-200', danger: 'bg-rose-50 text-rose-700 ring-rose-200', info: 'bg-blue-50 text-blue-700 ring-blue-200', neutral: 'bg-slate-50 text-slate-700 ring-slate-200' };
export function StatusBadge({ status = 'neutral', children }: { status?: Status; children: React.ReactNode }) { return <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ${cls[status]}`}>{children}</span>; }
