import type { InputHTMLAttributes } from 'react';

type FormInputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  labelClassName?: string;
};

export function FormInput({ label, labelClassName = '', className = '', ...props }: FormInputProps) {
  return <label className="block"><span className={`mb-2 block text-sm font-semibold text-slate-700 ${labelClassName}`}>{label}</span><input className={`w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none ring-brand-500 transition placeholder:text-slate-400 focus:ring-2 ${className}`} {...props} /></label>;
}
