import { Decision } from '@/types';

export function formatCurrency(amount: number, currency: string = 'INR'): string {
  try {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency || 'INR',
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `₹${amount.toFixed(2)}`;
  }
}

export function formatDate(dateStr: string): string {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    return d.toLocaleString('en-IN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    });
  } catch {
    return dateStr;
  }
}

export function getDecisionBadgeProps(decision: Decision | string) {
  switch (decision) {
    case 'APPROVED':
      return {
        bg: 'bg-emerald-50 text-emerald-800 border-emerald-200',
        dot: 'bg-emerald-600',
        label: 'APPROVED',
      };
    case 'REVIEW':
      return {
        bg: 'bg-amber-50 text-amber-800 border-amber-200',
        dot: 'bg-amber-600',
        label: 'REVIEW',
      };
    case 'BLOCKED':
      return {
        bg: 'bg-red-50 text-red-800 border-red-200',
        dot: 'bg-red-600',
        label: 'BLOCKED',
      };
    default:
      return {
        bg: 'bg-slate-100 text-slate-700 border-slate-200',
        dot: 'bg-slate-500',
        label: decision || 'UNKNOWN',
      };
  }
}

export function getRiskScoreColor(score: number): {
  text: string;
  bg: string;
  border: string;
  glow: string;
} {
  if (score >= 70) {
    return {
      text: 'text-red-700',
      bg: 'bg-red-50',
      border: 'border-red-200',
      glow: '',
    };
  }
  if (score >= 40) {
    return {
      text: 'text-amber-700',
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      glow: '',
    };
  }
  return {
    text: 'text-emerald-700',
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    glow: '',
  };
}
