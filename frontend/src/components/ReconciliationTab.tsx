'use client';

import React, { useEffect, useState } from 'react';
import {
  RefreshCw,
  AlertOctagon,
  CheckCircle2,
  ShieldAlert,
  CreditCard,
  ArrowUpRight,
  Search,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { api } from '@/lib/api';
import { ReconciliationRecord, Transaction } from '@/types';
import { formatDate, formatCurrency } from '@/lib/utils';
import { RiskScoreGauge } from '@/components/RiskScoreGauge';

interface ReconciliationTabProps {
  onSelectTransaction?: (txn: Transaction) => void;
}

export function ReconciliationTab({ onSelectTransaction }: ReconciliationTabProps) {
  const [records, setRecords] = useState<ReconciliationRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [simulating, setSimulating] = useState(false);

  // Form for simulated Razorpay payment
  const [testAmount, setTestAmount] = useState<number>(350000);
  const [testStatus, setTestStatus] = useState<string>('captured');
  const [testEmail, setTestEmail] = useState<string>('highrisk.buyer@phantom.com');

  // Form for fetching & analyzing Razorpay payment by ID
  const [searchPaymentId, setSearchPaymentId] = useState<string>('pay_test_whale_101');
  const [searching, setSearching] = useState<boolean>(false);
  const [fetchedPayment, setFetchedPayment] = useState<any | null>(null);
  const [analyzingPayment, setAnalyzingPayment] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<any | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  const loadReconciliation = async () => {
    setLoading(true);
    try {
      const res = await api.getReconciliationList(1, 30);
      setRecords(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReconciliation();
  }, []);

  const handleSimulatePayment = async (e: React.FormEvent) => {
    e.preventDefault();
    setSimulating(true);
    try {
      await api.simulateRazorpayPayment({
        amount: Number(testAmount),
        currency: 'INR',
        status: testStatus,
        customer_email: testEmail,
        method: 'card',
      });
      await loadReconciliation();
    } catch (err) {
      console.error(err);
    } finally {
      setSimulating(false);
    }
  };

  const handleFetchPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchPaymentId.trim()) return;
    setSearching(true);
    setSearchError(null);
    setFetchedPayment(null);
    setAnalysisResult(null);

    try {
      const res = await api.getRazorpayPayment(searchPaymentId.trim());
      setFetchedPayment(res);
    } catch (err: any) {
      setSearchError(err.message || 'Payment not found or credentials not configured');
    } finally {
      setSearching(false);
    }
  };

  const handleRunRiskAnalysis = async () => {
    if (!searchPaymentId.trim()) return;
    setAnalyzingPayment(true);
    setSearchError(null);

    try {
      const payload: any = { payment_id: searchPaymentId.trim() };
      // If payment was already fetched or custom entered, pass normalized hints
      if (fetchedPayment) {
        payload.amount_inr = fetchedPayment.amount_inr;
        payload.email = fetchedPayment.customer_email;
        payload.status = fetchedPayment.status;
        payload.method = fetchedPayment.method;
      }
      const res = await api.ingestRazorpayPayment(payload);
      setAnalysisResult(res);
      await loadReconciliation();
    } catch (err: any) {
      setSearchError(err.message || 'Failed to ingest and analyze payment');
    } finally {
      setAnalyzingPayment(false);
    }
  };

  const discrepantCount = records.filter((r) => r.is_discrepant).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 flex items-center space-x-2">
            <RefreshCw className="w-5 h-5 text-teal-600" />
            <span>Razorpay Test Mode Reconciliation & Settlement Guard</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Automated reconciliation agent matching Razorpay gateway events with deterministic risk decisions.
          </p>
        </div>

        <button
          onClick={loadReconciliation}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 shadow-xs flex items-center space-x-2 self-start transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${loading ? 'animate-spin' : ''}`} />
          <span>Sync Gateway Ledger</span>
        </button>
      </div>

      {/* Discrepancy KPI Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Reconciled Records</span>
          <div className="text-2xl font-bold font-mono text-slate-900 mt-1">{total}</div>
        </div>

        <div className="bg-red-50/60 p-4 rounded-xl border border-red-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-red-800">Gateway Discrepancies</span>
            <AlertOctagon className="w-4 h-4 text-red-600" />
          </div>
          <div className="text-2xl font-bold font-mono text-red-700 mt-1">{discrepantCount}</div>
          <p className="text-[11px] text-red-600 mt-1">
            Payments captured by gateway despite BLOCKED/REVIEW decision
          </p>
        </div>

        <div className="bg-emerald-50/60 p-4 rounded-xl border border-emerald-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-800">Clean Matches</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-700 mt-1">
            {Math.max(0, total - discrepantCount)}
          </div>
          <p className="text-[11px] text-emerald-600 mt-1">
            Settlement authorized in accordance with risk policy
          </p>
        </div>
      </div>

      {/* Razorpay Test Mode Payment Inspector & Ingestion Card */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
              <CreditCard className="w-4 h-4 text-teal-600" />
              <span>Razorpay Test Mode Payment Inspector & Risk Analysis</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Enter any Razorpay Test Mode Payment ID to retrieve payment data from the gateway and evaluate through the deterministic risk engine.
            </p>
          </div>
          <span className="text-[10px] font-mono font-medium px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
            TEST MODE ONLY
          </span>
        </div>

        <form onSubmit={handleFetchPayment} className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              required
              placeholder="e.g. pay_test_123456 or pay_test_whale_01"
              value={searchPaymentId}
              onChange={(e) => setSearchPaymentId(e.target.value)}
              className="w-full text-xs font-mono pl-9 pr-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:bg-white focus:border-teal-600 transition-colors"
            />
          </div>

          <div className="flex space-x-2 w-full sm:w-auto">
            <button
              type="submit"
              disabled={searching}
              className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-800 border border-slate-200 transition-all flex items-center justify-center space-x-1.5 disabled:opacity-50"
            >
              <Search className="w-3.5 h-3.5 text-slate-600" />
              <span>{searching ? 'Fetching...' : 'Fetch Payment'}</span>
            </button>

            <button
              type="button"
              onClick={handleRunRiskAnalysis}
              disabled={analyzingPayment}
              className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-white shadow-xs transition-all flex items-center justify-center space-x-1.5 disabled:opacity-50"
            >
              <Zap className="w-3.5 h-3.5 text-amber-300" />
              <span>{analyzingPayment ? 'Evaluating Risk...' : 'Run Risk Analysis'}</span>
            </button>
          </div>
        </form>

        {searchError && (
          <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700">
            {searchError}
          </div>
        )}

        {/* Live Result View */}
        {(fetchedPayment || analysisResult) && (
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
            <div className="space-y-2 text-xs">
              <div className="flex items-center space-x-2">
                <span className="font-bold text-slate-900">
                  {analysisResult?.payment_id || fetchedPayment?.payment_id}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600">
                  Status: {analysisResult?.normalized_summary?.status || fetchedPayment?.status || 'captured'}
                </span>
                {analysisResult?.already_processed && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-semibold">
                    IDEMPOTENT (CACHED)
                  </span>
                )}
              </div>

              <div className="text-slate-700">
                Amount:{' '}
                <span className="font-mono font-bold text-slate-900">
                  {formatCurrency(
                    analysisResult?.normalized_summary?.amount_inr ?? fetchedPayment?.amount_inr ?? 0
                  )}
                </span>{' '}
                via <span className="capitalize font-medium text-slate-800">{analysisResult?.normalized_summary?.method || fetchedPayment?.method}</span>
              </div>

              <div className="text-slate-500 truncate">
                Customer: {analysisResult?.normalized_summary?.email || fetchedPayment?.customer_email || 'shopper@test.com'}
              </div>
            </div>

            {/* Risk Decision Gauge */}
            {(analysisResult || (fetchedPayment?.is_ingested && fetchedPayment.internal_decision)) && (
              <div className="flex items-center justify-around p-3 rounded-xl bg-white border border-slate-200 shadow-xs">
                <div>
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">Deterministic Decision</span>
                  <span className="text-base font-bold font-mono text-slate-900">
                    {analysisResult?.decision || fetchedPayment?.internal_decision}
                  </span>
                  <span className="text-[10px] text-slate-500 block">
                    Score: {analysisResult?.risk_score ?? fetchedPayment?.risk_score} / 100
                  </span>
                </div>
                <RiskScoreGauge
                  score={analysisResult?.risk_score ?? fetchedPayment?.risk_score ?? 0}
                  decision={analysisResult?.decision || fetchedPayment?.internal_decision || 'REVIEW'}
                  size="sm"
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Test Mode Simulation Box */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-xs">
        <h3 className="text-sm font-bold text-slate-900 mb-1 flex items-center space-x-2">
          <CreditCard className="w-4 h-4 text-teal-600" />
          <span>Simulate Razorpay Test Payment Webhook / Ingestion</span>
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Test reconciliation logic by firing simulated Razorpay Test transactions into the pipeline.
        </p>

        <form onSubmit={handleSimulatePayment} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div>
            <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider block mb-1">
              Amount (INR)
            </label>
            <input
              type="number"
              value={testAmount}
              onChange={(e) => setTestAmount(Number(e.target.value))}
              className="w-full text-xs font-mono p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-900 focus:bg-white focus:outline-none focus:border-teal-600 transition-colors"
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider block mb-1">
              Razorpay Status
            </label>
            <select
              value={testStatus}
              onChange={(e) => setTestStatus(e.target.value)}
              className="w-full text-xs p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-900 focus:bg-white focus:outline-none focus:border-teal-600 transition-colors"
            >
              <option value="captured">captured (Success)</option>
              <option value="authorized">authorized (Held)</option>
              <option value="failed">failed (Declined)</option>
            </select>
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider block mb-1">
              Customer Email
            </label>
            <input
              type="email"
              value={testEmail}
              onChange={(e) => setTestEmail(e.target.value)}
              className="w-full text-xs font-mono p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-900 focus:bg-white focus:outline-none focus:border-teal-600 transition-colors"
            />
          </div>

          <button
            type="submit"
            disabled={simulating}
            className="w-full py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-white shadow-xs flex items-center justify-center space-x-2 transition-all disabled:opacity-50"
          >
            <ArrowUpRight className="w-4 h-4 text-teal-400" />
            <span>{simulating ? 'Processing...' : 'Simulate Payment'}</span>
          </button>
        </form>
      </div>

      {/* Ledger Table */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-700">Reconciliation Ledger</span>
          <span className="text-xs font-mono text-slate-500">Records: {records.length}</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/80 text-slate-500 font-mono text-[11px]">
                <th className="py-3 px-4">Payment ID</th>
                <th className="py-3 px-4">Razorpay Status</th>
                <th className="py-3 px-4">Internal Risk Decision</th>
                <th className="py-3 px-4">Reconciliation State</th>
                <th className="py-3 px-4">Action Required</th>
                <th className="py-3 px-4">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {records.length > 0 ? (
                records.map((r) => {
                  return (
                    <tr
                      key={r.id}
                      className={`hover:bg-slate-50/80 transition-colors ${
                        r.is_discrepant ? 'bg-red-50/30' : ''
                      }`}
                    >
                      <td className="py-3 px-4 text-slate-900 font-bold truncate max-w-[150px]">
                        {r.razorpay_payment_id}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${
                            r.razorpay_status === 'captured'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : r.razorpay_status === 'authorized'
                              ? 'bg-amber-50 text-amber-700 border-amber-200'
                              : 'bg-red-50 text-red-700 border-red-200'
                          }`}
                        >
                          {r.razorpay_status}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${
                            r.internal_decision === 'APPROVED'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : r.internal_decision === 'REVIEW'
                              ? 'bg-amber-50 text-amber-700 border-amber-200'
                              : 'bg-red-50 text-red-700 border-red-200'
                          }`}
                        >
                          {r.internal_decision || 'PENDING'}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {r.is_discrepant ? (
                          <div className="flex items-center space-x-1.5 text-red-600 font-semibold">
                            <ShieldAlert className="w-3.5 h-3.5" />
                            <span>{r.discrepancy_type || 'DISCREPANCY'}</span>
                          </div>
                        ) : (
                          <div className="flex items-center space-x-1.5 text-emerald-700 font-medium">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            <span>RECONCILED CLEAN</span>
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-700 font-sans text-xs">
                        {r.discrepancy_details?.recommended_action || 'No action needed'}
                      </td>
                      <td className="py-3 px-4 text-slate-500 text-[11px]">
                        {formatDate(r.checked_at)}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-slate-400 font-sans">
                    No reconciliation records recorded yet. Simulate a payment above to begin.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
