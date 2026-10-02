import type { ReactNode } from 'react';

interface CardProps {
  title?: string;
  className?: string;
  bodyClassName?: string;
  children: ReactNode;
}

export default function Card({ title, className = '', bodyClassName = 'p-5', children }: CardProps) {
  return (
    <section className={`rounded-lg bg-white shadow-sm ring-1 ring-slate-200 ${className}`}>
      {title && (
        <header className="border-b border-slate-200 px-5 py-3">
          <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
        </header>
      )}
      <div className={bodyClassName}>{children}</div>
    </section>
  );
}
