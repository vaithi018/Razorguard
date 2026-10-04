'use client';

import React, { useState } from 'react';
import {
  Terminal,
  Zap,
  ShieldCheck,
  AlertTriangle,
  Ban,
  ArrowRight,
  Send,
  Sparkles,
} from 'lucide-react';
import { api } from '@/lib/api';
import { Transaction } from '@/types';
import { RiskScoreGauge } from '@/components/RiskScoreGauge';
import { formatCurrency } from '@/lib/utils';

interface SimulatorTabProps {
  onTransactionSelected: (txn: Transaction) => void;
  onRefreshMetrics: () => void;
}

export function SimulatorTab({
  onTransactionSelected,
  onRefreshMetrics,
}: SimulatorTabProps) {
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState<Transaction | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Custom form state
  const [customAmount, setCustomAmount] = useState<number>(75000);
  const [customEmail, setCustomEmail] = useState<string>('custom.shopper@retail.com');
  const [customIp, setCustomIp] = useState<string>('103.22.45.19');
  const [customMethod, setCustomMethod] = useState<string>('card');
  const [customCustomerId, setCustomCustomerId] = useState<string>('cust_interactive_01');

  const presets = [
    {
      key: 'clean',
      title: 'Standard Normal Purchase',
      desc: '₹2,500 UPI transaction with no previous anomalies.',
      badge: 'Expected: APPROVED',
      color: 'border-emerald-200 bg-emerald-50/40 hover:border-emerald-400',
      icon: ShieldCheck,
      iconColor: 'text-emerald-700',
    },
    {
      key: 'high_amount',
      title: 'High-Value Tier 2 Spike',
      desc: '₹125,000 single transaction exceeding standard limits.',
      badge: 'Expected: REVIEW',
      color: 'border-amber-200 bg-amber-50/40 hover:border-amber-400',
      icon: AlertTriangle,
      iconColor: 'text-amber-700',
    },
    {
      key: 'velocity',
      title: 'Velocity Cluster',
      desc: 'Multiple consecutive transaction attempts in short window.',
      badge: 'Expected: REVIEW / BLOCKED',
      color: 'border-orange-200 bg-orange-50/40 hover:border-orange-400',
      icon: Zap,
      iconColor: 'text-orange-700',
    },
    {
      key: 'card_testing',
      title: 'Automated Card Testing Bot',
      desc: '₹50 rapid repeated charge attempts (<30s spacing).',
      badge: 'Expected: BLOCKED',
      color: 'border-red-200 bg-red-50/40 hover:border-red-400',
      icon: Ban,
      iconColor: 'text-red-700',
    },
    {
      key: 'blocklist',
      title: 'Negative List Syndicate',
      desc: 'Flagged syndicate email & stolen card fingerprint.',
      badge: 'Expected: HARD BLOCK (100)',
      color: 'border-purple-200 bg-purple-50/40 hover:border-purple-400',
      icon: Ban,
      iconColor: 'text-purple-700',
    },
  ];

  const runPreset = async (key: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.simulateScenario(key);
      setLastResult(res);
      onRefreshMetrics();
    } catch (err: any) {
      setError(err.message || 'Simulation error');
    } finally {
      setLoading(false);
    }
  };

  const runCustom = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.createTransaction({
        amount: Number(customAmount),
        currency: 'INR',
        customer_id: customCustomerId,
        customer_email: customEmail,
        ip_address: customIp,
        payment_method: customMethod,
      });
      setLastResult(res);
      onRefreshMetrics();
    } catch (err: any) {
      setError(err.message || 'Simulation error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900 flex items-center space-x-2">
          <Terminal className="w-5 h-5 text-teal-600" />
          <span>Interactive Risk Sandbox & Attack Vector Simulator</span>
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Execute pre-built fraud vectors or custom payloads through the live deterministic rule engine and AI enrichment pipeline.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-800">
          {error}
        </div>
      )}

      {/* Preset Vectors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {presets.map((p) => {
          const Icon = p.icon;
          return (
            <div
              key={p.key}
              onClick={() => !loading && runPreset(p.key)}
              className={`p-5 rounded-xl border cursor-pointer transition-all duration-200 ${p.color} shadow-xs flex flex-col justify-between`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="p-2 rounded-lg bg-white border border-slate-200 shadow-xs">
                    <Icon className={`w-5 h-5 ${p.iconColor}`} />
                  </div>
                  <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-white text-slate-700 border border-slate-200">
                    {p.badge}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-900">{p.title}</h3>
                <p className="text-xs text-slate-600 mt-1 leading-relaxed">{p.desc}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-200/80 flex items-center justify-between text-xs font-semibold text-slate-700">
                <span>Run Vector</span>
                <ArrowRight className="w-4 h-4 text-teal-600" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Split section: Custom Transaction Injector + Live Simulation Result */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
        {/* Custom Form */}
        <div className="bg-white p-6 rounded-xl border border-slate-200/90 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900 mb-1 flex items-center space-x-2">
            <Zap className="w-4 h-4 text-teal-600" />
            <span>Custom Transaction Injector</span>
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            Test boundary amounts and custom attributes against the configured thresholds.
          </p>

          <form onSubmit={runCustom} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider block mb-1">
                  Amount (INR)
                </label>
                <input
                  type="number"
                  required
                  min={1}
                  step="0.01"
                  value={customAmount}
                  onChange={(e) => setCustomAmount(Number(e.target.value))}
                  className="w-full text-xs font-mono p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-teal-600"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider block mb-1">
                  Payment Method
                </label>
                <select
                  value={customMethod}
                  onChange={(e) => setCustomMethod(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-teal-600"
                >
                  <option value="card">Credit/Debit Card</option>
                  <option value="upi">UPI</option>
                  <option value="netbanking">Net Banking</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider block mb-1">
                Customer Email
              </label>
              <input
                type="email"
                required
                value={customEmail}
                onChange={(e) => setCustomEmail(e.target.value)}
                className="w-full text-xs font-mono p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-teal-600"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider block mb-1">
                  IP Address
                </label>
                <input
                  type="text"
                  required
                  value={customIp}
                  onChange={(e) => setCustomIp(e.target.value)}
                  className="w-full text-xs font-mono p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-teal-600"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider block mb-1">
                  Customer ID
                </label>
                <input
                  type="text"
                  required
                  value={customCustomerId}
                  onChange={(e) => setCustomCustomerId(e.target.value)}
                  className="w-full text-xs font-mono p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-teal-600"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-white shadow-xs flex items-center justify-center space-x-2 transition-all disabled:opacity-50 cursor-pointer"
            >
              <Send className="w-4 h-4 text-teal-400" />
              <span>{loading ? 'Evaluating Risk Pipeline...' : 'Inject & Evaluate Transaction'}</span>
            </button>
          </form>
        </div>

        {/* Live Result Card */}
        <div className="bg-white p-6 rounded-xl border border-slate-200/90 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-teal-600" />
                <span>Simulation Evaluation Result</span>
              </h3>
              {lastResult && (
                <span className="text-[11px] font-mono text-slate-500 font-medium">
                  {lastResult.transaction_ref}
                </span>
              )}
            </div>

            {lastResult ? (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-around">
                  <div className="text-left">
                    <span className="text-xs text-slate-500 font-medium">Evaluated Decision</span>
                    <div className="text-xl font-bold font-mono text-slate-900 mt-0.5">
                      {lastResult.decision}
                    </div>
                    <span className="text-xs text-slate-500">
                      Amount: {formatCurrency(lastResult.amount, lastResult.currency)}
                    </span>
                  </div>

                  <RiskScoreGauge
                    score={lastResult.risk_score}
                    decision={lastResult.decision}
                    size="sm"
                  />
                </div>

                {/* Triggered rules preview */}
                <div className="space-y-2">
                  <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Rules Triggered ({lastResult.evaluations?.filter((e) => e.triggered).length || 0})
                  </span>
                  <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                    {lastResult.evaluations
                      ?.filter((e) => e.triggered)
                      .map((r) => (
                        <div
                          key={r.rule_id}
                          className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-slate-50 border border-slate-200"
                        >
                          <span className="text-slate-800 font-medium">{r.rule_name}</span>
                          <span className="font-mono text-amber-800 font-bold bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                            +{r.score_impact} pts
                          </span>
                        </div>
                      ))}
                    {(!lastResult.evaluations ||
                      lastResult.evaluations.filter((e) => e.triggered).length === 0) && (
                      <p className="text-xs text-emerald-700 py-1 font-sans font-medium">
                        ✓ All rules evaluated clean. Baseline score 0/100.
                      </p>
                    )}
                  </div>
                </div>

                {/* AI Narrative preview */}
                {lastResult.ai_enrichment?.narrative && (
                  <div className="p-3 rounded-lg bg-teal-50 border border-teal-200 text-xs text-teal-900">
                    <span className="font-bold text-teal-800 block mb-1">
                      AI Explanation:
                    </span>
                    <p className="line-clamp-3 text-slate-700">{lastResult.ai_enrichment.narrative}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-16 text-xs text-slate-500 space-y-2">
                <Terminal className="w-8 h-8 mx-auto text-slate-400" />
                <p>Run any preset above or submit a custom transaction to inspect real-time outcomes.</p>
              </div>
            )}
          </div>

          {lastResult && (
            <div className="mt-4 pt-4 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => onTransactionSelected(lastResult)}
                className="px-4 py-2 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-xs font-semibold text-slate-800 flex items-center space-x-2 transition-all shadow-xs cursor-pointer"
              >
                <span>Open Full Audit Inspector</span>
                <ArrowRight className="w-4 h-4 text-teal-600" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
