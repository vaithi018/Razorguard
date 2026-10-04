'use client';

import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  Ban,
  CreditCard,
  Percent,
  Terminal,
  RefreshCw,
  Layers,
  ArrowRight,
  FileCheck2,
} from 'lucide-react';
import { Navbar } from '@/components/Navbar';
import { MetricCard } from '@/components/MetricCard';
import { RiskDistributionChart } from '@/components/RiskDistributionChart';
import { TransactionsTable } from '@/components/TransactionsTable';
import { TransactionDrawer } from '@/components/TransactionDrawer';
import { SimulatorTab } from '@/components/SimulatorTab';
import { ReconciliationTab } from '@/components/ReconciliationTab';
import { RulesConfigTab } from '@/components/RulesConfigTab';
import { DashboardMetrics, Transaction } from '@/types';
import { api } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loadingMetrics, setLoadingMetrics] = useState<boolean>(true);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  const fetchMetrics = async () => {
    setLoadingMetrics(true);
    try {
      const data = await api.getMetrics();
      setMetrics(data);
    } catch (err) {
      console.error('Failed to load metrics:', err);
    } finally {
      setLoadingMetrics(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, [refreshTrigger]);

  const triggerRefresh = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  const handleTransactionUpdated = (updated: Transaction) => {
    setSelectedTransaction(updated);
    triggerRefresh();
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <div className="space-y-8 animate-in fade-in duration-200">
            {/* Executive Welcome Hero Banner */}
            <div className="bg-white p-6 sm:p-7 rounded-2xl border border-slate-200/90 shadow-xs relative overflow-hidden">
              <div className="relative z-10 max-w-3xl space-y-3">
                <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold">
                  <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                  <span>Production-Grade Risk Architecture</span>
                </div>
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
                  Payment Risk & Reconciliation Control Center
                </h1>
                <p className="text-sm text-slate-600 leading-relaxed font-sans">
                  Real-time transaction decisioning powered by a deterministic, auditable rule engine. 
                  Enriched with asynchronous compliance narratives with zero latency degradation.
                </p>

                <div className="flex flex-wrap gap-3 pt-2">
                  <button
                    onClick={() => setActiveTab('simulator')}
                    className="px-4 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-white shadow-xs flex items-center space-x-2 transition-all cursor-pointer"
                  >
                    <Terminal className="w-4 h-4 text-teal-400" />
                    <span>Run Fraud Attack Simulator</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('reconciliation')}
                    className="px-4 py-2.5 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-xs font-semibold text-slate-700 shadow-xs flex items-center space-x-2 transition-all cursor-pointer"
                  >
                    <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
                    <span>Inspect Razorpay Recon</span>
                  </button>
                </div>
              </div>
            </div>

            {/* KPI Metric Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <MetricCard
                title="Total Volume"
                value={metrics ? formatCurrency(metrics.total_volume_inr) : '₹0.00'}
                subtext={`${metrics?.total_transactions || 0} Transactions`}
                icon={CreditCard}
                variant="default"
              />

              <MetricCard
                title="Approved"
                value={metrics?.approved_count || 0}
                subtext={`${metrics?.approval_rate_percent || 0}% Approval Rate`}
                icon={ShieldCheck}
                variant="success"
              />

              <MetricCard
                title="Under Review"
                value={metrics?.review_count || 0}
                subtext="Analyst Verification"
                icon={AlertTriangle}
                variant="warning"
              />

              <MetricCard
                title="Blocked"
                value={metrics?.blocked_count || 0}
                subtext="Fraud Averted"
                icon={Ban}
                variant="danger"
              />

              <MetricCard
                title="Avg Risk Score"
                value={`${metrics?.average_risk_score || 0}`}
                subtext="0-100 Bounded Scale"
                icon={Percent}
                variant="info"
              />

              <MetricCard
                title="Engine Status"
                value="ONLINE"
                subtext="Deterministic Truth"
                icon={FileCheck2}
                variant="success"
              />
            </div>

            {/* Middle Row: Risk Score Distribution & Top Triggered Rules */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {metrics && (
                <RiskDistributionChart
                  distribution={metrics.risk_distribution}
                  total={metrics.total_transactions}
                />
              )}

              {/* Top Triggered Rules Leaderboard */}
              <div className="bg-white p-5 rounded-xl border border-slate-200/90 shadow-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">
                        Top Triggered Risk Signals
                      </h3>
                      <p className="text-xs text-slate-500">
                        Most frequent violations detected by deterministic evaluators
                      </p>
                    </div>
                    <button
                      onClick={() => setActiveTab('rules')}
                      className="text-xs text-teal-700 hover:text-teal-800 font-semibold flex items-center space-x-1"
                    >
                      <span>Tune Rules</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="space-y-2.5">
                    {metrics?.top_triggered_rules && metrics.top_triggered_rules.length > 0 ? (
                      metrics.top_triggered_rules.map((rule, idx) => (
                        <div
                          key={rule.rule_id}
                          className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200/80"
                        >
                          <div className="flex items-center space-x-3">
                            <span className="font-mono text-xs font-bold text-slate-400 w-4">
                              0{idx + 1}
                            </span>
                            <div>
                              <div className="text-xs font-bold text-slate-900">
                                {rule.rule_name}
                              </div>
                              <div className="text-[10px] font-mono text-slate-500">
                                ID: {rule.rule_id}
                              </div>
                            </div>
                          </div>
                          <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                            {rule.count} hits
                          </span>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-10 text-xs text-slate-400 font-sans">
                        No rule violations recorded yet. Run simulation scenarios to view frequency.
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-200 text-[11px] text-slate-500 flex items-center justify-between font-sans">
                  <span>Deterministic engine controls 100% of decisions</span>
                  <span className="text-teal-700 font-semibold">AI Enrichment: Active</span>
                </div>
              </div>
            </div>

            {/* Live Ledger on Dashboard */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Live Transaction Feed</h3>
                  <p className="text-xs text-slate-500">
                    Real-time payment decisions, risk bands, and instant detail inspector
                  </p>
                </div>
                <button
                  onClick={() => setActiveTab('transactions')}
                  className="text-xs font-semibold text-teal-700 hover:text-teal-800 flex items-center space-x-1"
                >
                  <span>View Full Ledger</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>

              <TransactionsTable
                onSelectTransaction={(txn) => setSelectedTransaction(txn)}
                refreshTrigger={refreshTrigger}
              />
            </div>
          </div>
        )}

        {/* TRANSACTIONS TAB */}
        {activeTab === 'transactions' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            <div>
              <h2 className="text-xl font-bold tracking-tight text-slate-900 flex items-center space-x-2">
                <Layers className="w-5 h-5 text-teal-600" />
                <span>Transaction Risk Ledger & Audit Explorer</span>
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                Filter by risk decision, search customer identifiers, and inspect full rule evaluations.
              </p>
            </div>

            <TransactionsTable
              onSelectTransaction={(txn) => setSelectedTransaction(txn)}
              refreshTrigger={refreshTrigger}
            />
          </div>
        )}

        {/* SIMULATOR TAB */}
        {activeTab === 'simulator' && (
          <div className="animate-in fade-in duration-200">
            <SimulatorTab
              onTransactionSelected={(txn) => setSelectedTransaction(txn)}
              onRefreshMetrics={triggerRefresh}
            />
          </div>
        )}

        {/* RECONCILIATION TAB */}
        {activeTab === 'reconciliation' && (
          <div className="animate-in fade-in duration-200">
            <ReconciliationTab />
          </div>
        )}

        {/* RULES ENGINE TAB */}
        {activeTab === 'rules' && (
          <div className="animate-in fade-in duration-200">
            <RulesConfigTab />
          </div>
        )}
      </main>

      {/* Slide-over Transaction Detail Inspector */}
      {selectedTransaction && (
        <TransactionDrawer
          transaction={selectedTransaction}
          onClose={() => setSelectedTransaction(null)}
          onTransactionUpdated={handleTransactionUpdated}
        />
      )}
    </div>
  );
}
