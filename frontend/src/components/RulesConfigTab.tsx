'use client';

import React, { useEffect, useState } from 'react';
import { Sliders, Save, CheckCircle2, Shield, Settings2, RefreshCw } from 'lucide-react';
import { api } from '@/lib/api';
import { RulesConfig } from '@/types';

export function RulesConfigTab() {
  const [config, setConfig] = useState<RulesConfig | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchConfig = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getRulesConfig();
      setConfig(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load rule configuration');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!config) return;
    setSaving(true);
    setSavedSuccess(false);
    setError(null);
    try {
      const updated = await api.updateRulesConfig(config);
      setConfig(updated);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const updateThreshold = (key: 'review_min_score' | 'blocked_min_score', val: number) => {
    if (!config) return;
    setConfig({
      ...config,
      thresholds: {
        ...config.thresholds,
        [key]: val,
      },
    });
  };

  const updateRuleParam = (ruleId: string, paramKey: string, val: any) => {
    if (!config) return;
    setConfig({
      ...config,
      rules: {
        ...config.rules,
        [ruleId]: {
          ...(config.rules[ruleId] || {}),
          [paramKey]: val,
        },
      },
    });
  };

  if (loading) {
    return (
      <div className="py-20 text-center text-xs text-slate-500 flex items-center justify-center space-x-2">
        <RefreshCw className="w-4 h-4 animate-spin text-teal-600" />
        <span>Loading deterministic rule parameters...</span>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="p-6 text-center text-red-600 text-xs">
        {error || 'Unable to load rule configuration.'}
      </div>
    );
  }

  return (
    <form onSubmit={handleSave} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 flex items-center space-x-2">
            <Sliders className="w-5 h-5 text-teal-600" />
            <span>Deterministic Rules Configuration & Threshold Calibration</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Configure risk scores, velocity windows, and decision boundaries. All adjustments execute immediately across pipeline audits.
          </p>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-white shadow-xs flex items-center space-x-2 transition-all disabled:opacity-50 self-start"
        >
          {savedSuccess ? (
            <>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Saved & Activated</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4 text-teal-400" />
              <span>{saving ? 'Updating...' : 'Save & Publish Rules'}</span>
            </>
          )}
        </button>
      </div>

      {savedSuccess && (
        <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Rule configurations published and recorded to audit trail successfully.</span>
        </div>
      )}

      {error && (
        <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700">
          {error}
        </div>
      )}

      {/* Decision Thresholds Mapping */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-xs space-y-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
            <Shield className="w-4 h-4 text-teal-600" />
            <span>Decision Score Cutoffs (0–100 Scale)</span>
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Transactions scoring below Review Minimum are APPROVED. Scores reaching Blocked Minimum are immediately BLOCKED.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          <div className="p-4 rounded-xl bg-amber-50/40 border border-amber-200/80 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-amber-900">Review Threshold</span>
              <span className="font-mono text-slate-900 font-bold bg-white px-2 py-0.5 rounded border border-amber-200">
                {config.thresholds.review_min_score} / 100
              </span>
            </div>
            <input
              type="range"
              min={10}
              max={60}
              value={config.thresholds.review_min_score}
              onChange={(e) => updateThreshold('review_min_score', Number(e.target.value))}
              className="w-full accent-amber-600 cursor-pointer"
            />
            <p className="text-[11px] text-slate-600">
              Transactions with score &ge; {config.thresholds.review_min_score} enter manual REVIEW queue.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-red-50/40 border border-red-200/80 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-red-900">Blocked Threshold</span>
              <span className="font-mono text-slate-900 font-bold bg-white px-2 py-0.5 rounded border border-red-200">
                {config.thresholds.blocked_min_score} / 100
              </span>
            </div>
            <input
              type="range"
              min={60}
              max={95}
              value={config.thresholds.blocked_min_score}
              onChange={(e) => updateThreshold('blocked_min_score', Number(e.target.value))}
              className="w-full accent-red-600 cursor-pointer"
            />
            <p className="text-[11px] text-slate-600">
              Transactions with score &ge; {config.thresholds.blocked_min_score} are strictly BLOCKED.
            </p>
          </div>
        </div>
      </div>

      {/* High Amount Rule Config */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-xs space-y-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
            <Settings2 className="w-4 h-4 text-teal-600" />
            <span>High Amount Rule Parameters (HIGH_AMOUNT)</span>
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Tier thresholds defining stepped risk scoring for transaction ticket sizes.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
            <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider block">
              Tier 1 Amount (INR)
            </label>
            <input
              type="number"
              value={config.rules.HIGH_AMOUNT?.tier_1_threshold || 50000}
              onChange={(e) =>
                updateRuleParam('HIGH_AMOUNT', 'tier_1_threshold', Number(e.target.value))
              }
              className="w-full text-xs font-mono p-2 rounded-lg bg-white border border-slate-200 text-slate-900 focus:outline-none focus:border-teal-600 transition-colors"
            />
            <div className="flex justify-between text-[11px] text-slate-500 pt-1">
              <span>Score Impact:</span>
              <span className="font-mono text-amber-700 font-bold">
                +{config.rules.HIGH_AMOUNT?.tier_1_score || 25} pts
              </span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
            <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider block">
              Tier 2 Amount (INR)
            </label>
            <input
              type="number"
              value={config.rules.HIGH_AMOUNT?.tier_2_threshold || 100000}
              onChange={(e) =>
                updateRuleParam('HIGH_AMOUNT', 'tier_2_threshold', Number(e.target.value))
              }
              className="w-full text-xs font-mono p-2 rounded-lg bg-white border border-slate-200 text-slate-900 focus:outline-none focus:border-teal-600 transition-colors"
            />
            <div className="flex justify-between text-[11px] text-slate-500 pt-1">
              <span>Score Impact:</span>
              <span className="font-mono text-amber-700 font-bold">
                +{config.rules.HIGH_AMOUNT?.tier_2_score || 45} pts
              </span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
            <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider block">
              Extreme Amount (INR)
            </label>
            <input
              type="number"
              value={config.rules.HIGH_AMOUNT?.extreme_threshold || 300000}
              onChange={(e) =>
                updateRuleParam('HIGH_AMOUNT', 'extreme_threshold', Number(e.target.value))
              }
              className="w-full text-xs font-mono p-2 rounded-lg bg-white border border-slate-200 text-slate-900 focus:outline-none focus:border-teal-600 transition-colors"
            />
            <div className="flex justify-between text-[11px] text-slate-500 pt-1">
              <span>Score Impact:</span>
              <span className="font-mono text-red-700 font-bold">
                +{config.rules.HIGH_AMOUNT?.extreme_score || 75} pts
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Velocity and Frequency Rules */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-xs space-y-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
            <Settings2 className="w-4 h-4 text-teal-600" />
            <span>Velocity & Rate Anomaly Parameters</span>
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Card testing and high-frequency cluster thresholds.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex justify-between text-xs font-semibold text-slate-900">
              <span>10-Minute Velocity Window (VELOCITY_10M)</span>
              <span className="text-amber-700 font-mono font-bold">
                +{config.rules.VELOCITY_10M?.tier_1_score || 25} pts
              </span>
            </div>
            <div>
              <label className="text-[11px] font-medium text-slate-500 block mb-1">
                Max Allowed Transactions in 10 mins
              </label>
              <input
                type="number"
                value={config.rules.VELOCITY_10M?.tier_1_count || 3}
                onChange={(e) =>
                  updateRuleParam('VELOCITY_10M', 'tier_1_count', Number(e.target.value))
                }
                className="w-full text-xs font-mono p-2 rounded-lg bg-white border border-slate-200 text-slate-900 focus:outline-none focus:border-teal-600 transition-colors"
              />
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex justify-between text-xs font-semibold text-slate-900">
              <span>Rapid Succession / Card Testing (RAPID_SUCCESSION)</span>
              <span className="text-red-700 font-mono font-bold">
                +{config.rules.RAPID_SUCCESSION?.score_impact || 35} pts
              </span>
            </div>
            <div>
              <label className="text-[11px] font-medium text-slate-500 block mb-1">
                Threshold Window (Seconds between txns)
              </label>
              <input
                type="number"
                value={config.rules.RAPID_SUCCESSION?.seconds_threshold || 30}
                onChange={(e) =>
                  updateRuleParam('RAPID_SUCCESSION', 'seconds_threshold', Number(e.target.value))
                }
                className="w-full text-xs font-mono p-2 rounded-lg bg-white border border-slate-200 text-slate-900 focus:outline-none focus:border-teal-600 transition-colors"
              />
            </div>
          </div>
        </div>
      </div>
    </form>
  );
}
