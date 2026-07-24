import type { ReactNode } from 'react';
export function PageHeader({ title, subtitle, eyebrow, actions }: { title: string; subtitle?: string; eyebrow?: string; actions?: ReactNode }) {
  return <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between"><div>{eyebrow && <p className="mb-2 text-xs font-black uppercase tracking-[.22em] text-gold-600">{eyebrow}</p>}<h1 className="lumyra-display text-4xl font-black tracking-tight text-ink dark:text-white md:text-5xl">{title}</h1>{subtitle && <p className="mt-2 max-w-3xl leading-7 text-slate-500 dark:text-slate-300">{subtitle}</p>}</div>{actions && <div className="flex flex-wrap gap-2">{actions}</div>}</div>;
}
