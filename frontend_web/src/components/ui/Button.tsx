import type { ButtonHTMLAttributes } from 'react';
const variants = {
  primary: 'bg-brand-800 text-white shadow-glow hover:bg-brand-700 hover:shadow-gold',
  secondary: 'bg-white text-ink border border-brand-100 hover:bg-brand-50 dark:border-white/10 dark:bg-white/10 dark:text-ice dark:hover:bg-white/15',
  gold: 'bg-gold-500 text-ink shadow-gold hover:bg-gold-300',
  ghost: 'bg-transparent text-slate-700 hover:bg-brand-50 dark:text-slate-200 dark:hover:bg-white/10'
};
export function Button({ className = '', variant = 'primary', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: keyof typeof variants }) {
  return <button className={`lumyra-focus inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-extrabold transition duration-200 hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${className}`} {...props} />;
}
