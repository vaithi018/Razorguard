import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon: LucideIcon;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
}

export function MetricCard({
  title,
  value,
  subtext,
  icon: Icon,
  variant = 'default',
}: MetricCardProps) {
  const variantStyles = {
    default: {
      border: 'border-slate-200/90',
      iconBg: 'bg-slate-100 text-slate-700',
      badge: 'text-slate-500',
    },
    success: {
      border: 'border-emerald-200/90',
      iconBg: 'bg-emerald-50 text-emerald-700 border border-emerald-200/60',
      badge: 'text-emerald-700 font-medium',
    },
    warning: {
      border: 'border-amber-200/90',
      iconBg: 'bg-amber-50 text-amber-700 border border-amber-200/60',
      badge: 'text-amber-700 font-medium',
    },
    danger: {
      border: 'border-red-200/90',
      iconBg: 'bg-red-50 text-red-700 border border-red-200/60',
      badge: 'text-red-700 font-medium',
    },
    info: {
      border: 'border-teal-200/90',
      iconBg: 'bg-teal-50 text-teal-700 border border-teal-200/60',
      badge: 'text-teal-700 font-medium',
    },
  };

  const style = variantStyles[variant];

  return (
    <div
      className={`bg-white p-5 rounded-xl border ${style.border} shadow-xs hover:border-slate-300 transition-all flex flex-col justify-between`}
    >
      <div className="flex items-center justify-between mb-2.5">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          {title}
        </span>
        <div className={`p-2 rounded-lg ${style.iconBg}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="flex items-baseline space-x-1.5">
        <span className="text-2xl font-bold tracking-tight text-slate-900 font-mono">
          {value}
        </span>
      </div>
      {subtext && (
        <p className={`mt-1.5 text-xs ${style.badge}`}>
          {subtext}
        </p>
      )}
    </div>
  );
}
