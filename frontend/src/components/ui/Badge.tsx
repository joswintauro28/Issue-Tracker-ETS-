import type { ReactNode } from 'react';

export type BadgeTone = 'gray' | 'blue' | 'green' | 'amber' | 'red' | 'indigo';

const toneClasses: Record<BadgeTone, string> = {
  gray: 'bg-slate-100 text-slate-600 ring-slate-200',
  blue: 'bg-sky-50 text-sky-700 ring-sky-200',
  green: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  amber: 'bg-amber-50 text-amber-700 ring-amber-200',
  red: 'bg-red-50 text-red-700 ring-red-200',
  indigo: 'bg-indigo-50 text-indigo-700 ring-indigo-200',
};

export default function Badge({
  tone = 'gray',
  children,
}: {
  tone?: BadgeTone;
  children: ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${toneClasses[tone]}`}
    >
      {children}
    </span>
  );
}
