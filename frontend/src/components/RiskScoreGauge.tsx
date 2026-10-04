import React from 'react';
import { getRiskScoreColor, getDecisionBadgeProps } from '@/lib/utils';
import { Decision } from '@/types';

interface RiskScoreGaugeProps {
  score: number;
  decision: Decision | string;
  size?: 'sm' | 'md' | 'lg';
}

export function RiskScoreGauge({ score, decision, size = 'md' }: RiskScoreGaugeProps) {
  const colors = getRiskScoreColor(score);
  const badge = getDecisionBadgeProps(decision);

  const radius = size === 'lg' ? 44 : size === 'md' ? 36 : 28;
  const strokeWidth = size === 'lg' ? 7 : size === 'md' ? 6 : 5;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const diameter = (radius + strokeWidth) * 2;

  return (
    <div className="flex flex-col items-center">
      <div className="relative flex items-center justify-center">
        <svg
          width={diameter}
          height={diameter}
          className="transform -rotate-90"
        >
          {/* Background circle */}
          <circle
            cx={diameter / 2}
            cy={diameter / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-slate-100"
            fill="transparent"
          />
          {/* Value circle */}
          <circle
            cx={diameter / 2}
            cy={diameter / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className={`${colors.text} transition-all duration-700 ease-out`}
            fill="transparent"
          />
        </svg>

        {/* Center score readout */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span
            className={`font-mono font-bold tracking-tight ${colors.text} ${
              size === 'lg' ? 'text-2xl' : size === 'md' ? 'text-xl' : 'text-sm'
            }`}
          >
            {score}
          </span>
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider">
            / 100
          </span>
        </div>
      </div>

      {/* Decision Pill */}
      <div
        className={`mt-2 inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full border text-xs font-semibold ${badge.bg}`}
      >
        <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`} />
        <span>{badge.label}</span>
      </div>
    </div>
  );
}
