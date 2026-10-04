import React from 'react';
import { RiskScoreDistribution } from '@/types';

interface RiskDistributionChartProps {
  distribution: RiskScoreDistribution;
  total: number;
}

export function RiskDistributionChart({ distribution, total }: RiskDistributionChartProps) {
  const bands = [
    { label: '0–19', count: distribution.range_0_19, color: 'bg-emerald-600', desc: 'Low Risk' },
    { label: '20–39', count: distribution.range_20_39, color: 'bg-teal-600', desc: 'Acceptable' },
    { label: '40–59', count: distribution.range_40_59, color: 'bg-amber-500', desc: 'Review' },
    { label: '60–79', count: distribution.range_60_79, color: 'bg-orange-500', desc: 'Elevated' },
    { label: '80–100', count: distribution.range_80_100, color: 'bg-red-600', desc: 'High Risk' },
  ];

  return (
    <div className="bg-white p-5 rounded-xl border border-slate-200/90 shadow-xs">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900">Risk Score Distribution</h3>
          <p className="text-xs text-slate-500">Transaction counts grouped by deterministic score band</p>
        </div>
        <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
          N = {total}
        </span>
      </div>

      <div className="space-y-3">
        {bands.map((b) => {
          const percentage = total > 0 ? Math.round((b.count / total) * 100) : 0;
          return (
            <div key={b.label} className="space-y-1">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-700">
                  {b.label}{' '}
                  <span className="text-slate-500 text-[11px] font-sans">({b.desc})</span>
                </span>
                <span className="text-slate-600 font-semibold">
                  {b.count} <span className="text-slate-400 font-normal">({percentage}%)</span>
                </span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className={`h-full rounded-full ${b.color} transition-all duration-500`}
                  style={{ width: `${Math.max(percentage, b.count > 0 ? 3 : 0)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
