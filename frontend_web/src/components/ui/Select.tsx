import type { SelectHTMLAttributes } from 'react';

type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
  labelClassName?: string;
};

export function Select({ label, children, labelClassName = '', className = '', ...props }: SelectProps) {
  return <label className="block"><span className={`mb-2 block text-sm font-semibold text-slate-700 ${labelClassName}`}>{label}</span><select className={`w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none ring-brand-500 transition focus:ring-2 ${className}`} {...props}>{children}</select></label>;
}
