export function LiveIndicator({ status }: { status: string }) {
  const live = status === 'connected';
  return <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-bold ${live ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' : 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-300'}`}>
    <span className={`h-2 w-2 rounded-full ${live ? 'animate-pulse bg-emerald-500' : 'bg-amber-500'}`} />
    {live ? 'Live' : 'Reconectando'}
  </span>;
}
