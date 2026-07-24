import type { ReactNode } from 'react';
export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`card-hover rounded-[1.7rem] border border-brand-100/80 bg-white/92 p-5 shadow-soft backdrop-blur dark:border-white/10 dark:bg-white/[.055] ${className}`}>{children}</div>;
}
