'use client';

import React, { useState } from 'react';
import {
  X,
  ShieldAlert,
  Bot,
  History,
  CheckCircle2,
  AlertTriangle,
  CreditCard,
  User,
  Globe,
  Clock,
  Check,
  Ban,
} from 'lucide-react';
import { Transaction } from '@/types';
import { formatCurrency, formatDate, getDecisionBadgeProps, getRiskScoreColor } from '@/lib/utils';
import { RiskScoreGauge } from '@/components/RiskScoreGauge';
import { api } from '@/lib/api';

interface TransactionDrawerProps {
  transaction: Transaction | null;
  onClose: () => void;
  onTransactionUpdated: (updated: Transaction) => void;
}

export function TransactionDrawer({
  transaction,
  onClose,
  onTransactionUpdated,
}: TransactionDrawerProps) {
  const [activeTab, setActiveTab] = useState<'rules' | 'ai' | 'audit'>('rules');
  const [overrideAction, setOverrideAction] = useState<'FORCE_APPROVE' | 'CONFIRM_FRAUD' | null>(null);
  const [overrideReason, setOverrideReason] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [overrideError, setOverrideError] = useState<string | null>(null);

  if (!transaction) return null;

  const badgeProps = getDecisionBadgeProps(transaction.decision);

  const handleManualReview = async () => {
    if (!overrideAction || !overrideReason.trim()) {
      setOverrideError('Please enter an auditable reason for the manual override.');
      return;
    }
    setSubmitting(true);
    setOverrideError(null);
    try {
      const updated = await api.submitManualReview(
        transaction.id,
        overrideAction,
        overrideReason,
        'lead_analyst'
      );
      onTransactionUpdated(updated);
      setOverrideAction(null);
      setOverrideReason('');
    } catch (err: any) {
      setOverrideError(err.message || 'Failed to submit manual review action');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs flex justify-end animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-white border-l border-slate-200 shadow-2xl flex flex-col h-full overflow-hidden text-slate-900">
        {/* Header */}
        <div className="p-6 border-b border-slate-200 flex items-center justify-between bg-slate-50/70">
          <div>
            <div className="flex items-center space-x-3">
              <span className="font-mono text-base font-bold text-slate-900">
                {transaction.transaction_ref}
              </span>
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${badgeProps.bg}`}
              >
                {transaction.decision}
              </span>
              <span className="text-xs font-mono text-slate-500">
                Status: {transaction.status}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1 flex items-center space-x-1">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>Created {formatDate(transaction.created_at)}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Top Summary Banner */}
        <div className="p-6 bg-slate-50/40 border-b border-slate-200 grid grid-cols-3 gap-4 items-center">
          <div className="col-span-2 space-y-3">
            <div>
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Transaction Amount
              </span>
              <div className="text-2xl font-bold font-mono text-slate-900">
                {formatCurrency(transaction.amount, transaction.currency)}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center space-x-1.5 text-slate-700">
                <User className="w-3.5 h-3.5 text-slate-400" />
                <span className="truncate">{transaction.customer_email}</span>
              </div>
              <div className="flex items-center space-x-1.5 text-slate-700">
                <Globe className="w-3.5 h-3.5 text-slate-400" />
                <span className="font-mono">{transaction.ip_address}</span>
              </div>
              <div className="flex items-center space-x-1.5 text-slate-700">
                <CreditCard className="w-3.5 h-3.5 text-slate-400" />
                <span className="capitalize">{transaction.payment_method}</span>
                {transaction.card_last4 && (
                  <span className="font-mono text-slate-500">•••• {transaction.card_last4}</span>
                )}
              </div>
              {transaction.razorpay_payment_id && (
                <div className="flex items-center space-x-1.5 text-teal-700 font-mono text-[11px] font-semibold">
                  <span>RP ID: {transaction.razorpay_payment_id}</span>
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-center">
            <RiskScoreGauge
              score={transaction.risk_score}
              decision={transaction.decision}
              size="md"
            />
          </div>
        </div>

        {/* Tab Buttons */}
        <div className="flex border-b border-slate-200 px-6 bg-slate-50/50">
          <button
            onClick={() => setActiveTab('rules')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 flex items-center space-x-2 transition-colors ${
              activeTab === 'rules'
                ? 'border-teal-600 text-teal-800'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            <span>
              Deterministic Rules ({transaction.evaluations?.filter((e) => e.triggered).length || 0})
            </span>
          </button>
          <button
            onClick={() => setActiveTab('ai')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 flex items-center space-x-2 transition-colors ${
              activeTab === 'ai'
                ? 'border-teal-600 text-teal-800'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Bot className="w-4 h-4" />
            <span>AI Risk Intelligence</span>
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 flex items-center space-x-2 transition-colors ${
              activeTab === 'audit'
                ? 'border-teal-600 text-teal-800'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <History className="w-4 h-4" />
            <span>Audit Trail ({transaction.audit_logs?.length || 0})</span>
          </button>
        </div>

        {/* Scrollable Tab Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {activeTab === 'rules' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-500 pb-1">
                <span>Rules Evaluated by Source of Truth Engine</span>
                <span>Cumulative Impact</span>
              </div>

              {transaction.evaluations && transaction.evaluations.length > 0 ? (
                transaction.evaluations.map((evalItem) => {
                  return (
                    <div
                      key={evalItem.rule_id}
                      className={`p-4 rounded-xl border transition-all ${
                        evalItem.triggered
                          ? evalItem.is_hard_block
                            ? 'bg-red-50/70 border-red-200'
                            : 'bg-amber-50/70 border-amber-200'
                          : 'bg-slate-50/70 border-slate-200 opacity-75'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-3">
                          <div className="mt-0.5">
                            {evalItem.triggered ? (
                              <AlertTriangle
                                className={`w-4 h-4 ${
                                  evalItem.is_hard_block ? 'text-red-600' : 'text-amber-600'
                                }`}
                              />
                            ) : (
                              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                            )}
                          </div>
                          <div>
                            <div className="flex items-center space-x-2">
                              <span className="text-sm font-bold text-slate-900">
                                {evalItem.rule_name}
                              </span>
                              {evalItem.is_hard_block && (
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-100 text-red-800 font-mono font-bold">
                                  HARD BLOCK
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-slate-600 mt-1 font-sans">
                              {evalItem.details?.reason ||
                                (evalItem.triggered ? 'Rule triggered threshold' : 'Passed without breach')}
                            </p>
                          </div>
                        </div>

                        <div className="text-right">
                          <span
                            className={`font-mono text-xs font-bold px-2 py-0.5 rounded ${
                              evalItem.triggered
                                ? evalItem.is_hard_block
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-amber-100 text-amber-800'
                                : 'bg-slate-100 text-slate-600'
                            }`}
                          >
                            {evalItem.triggered ? `+${evalItem.score_impact} pts` : '0 pts'}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-center py-8 text-sm text-slate-500 font-sans">
                  No evaluation logs available.
                </div>
              )}
            </div>
          )}

          {activeTab === 'ai' && (
            <div className="space-y-4">
              {/* Notice */}
              <div className="p-3.5 rounded-xl bg-teal-50 border border-teal-200 text-xs text-teal-800 flex items-start space-x-2">
                <Bot className="w-4 h-4 text-teal-600 mt-0.5 shrink-0" />
                <span>
                  <strong>Strict Security Protocol:</strong> AI functions strictly as an observational intelligence layer. The decision ({transaction.decision}) was finalized prior to LLM analysis.
                </span>
              </div>

              {transaction.ai_enrichment ? (
                <div className="space-y-4">
                  {/* Primary Narrative */}
                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                        Executive Risk Narrative
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                        {transaction.ai_enrichment.model || 'OpenAI gpt-4o-mini'}
                      </span>
                    </div>
                    <p className="text-sm text-slate-700 leading-relaxed font-sans">
                      {transaction.ai_enrichment.narrative || 'No narrative provided.'}
                    </p>

                    {transaction.ai_enrichment.threat_vector && (
                      <div className="mt-3 inline-flex items-center space-x-2 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700">
                        <span className="text-slate-500 font-medium">Threat Vector:</span>
                        <span className="font-bold">
                          {transaction.ai_enrichment.threat_vector}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Signals */}
                  {transaction.ai_enrichment.contributing_signals?.length > 0 && (
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-2">
                      <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                        Contributing Risk Signals
                      </span>
                      <ul className="space-y-1.5 text-xs text-slate-600">
                        {transaction.ai_enrichment.contributing_signals.map((sig, i) => (
                          <li key={i} className="flex items-start space-x-2">
                            <span className="text-red-600 font-bold">•</span>
                            <span>{sig}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Investigation Checklist */}
                  {transaction.ai_enrichment.investigation_steps?.length > 0 && (
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-2">
                      <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                        Analyst Action Checklist
                      </span>
                      <ul className="space-y-1.5 text-xs text-slate-600">
                        {transaction.ai_enrichment.investigation_steps.map((step, i) => (
                          <li key={i} className="flex items-start space-x-2">
                            <span className="text-teal-600 font-bold">✓</span>
                            <span>{step}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-sm text-slate-500 font-sans">
                  AI Risk Narrative not generated for this transaction.
                </div>
              )}
            </div>
          )}

          {activeTab === 'audit' && (
            <div className="space-y-4">
              <div className="text-xs text-slate-500 pb-1">
                Immutable, append-only chronological log of all evaluation events and manual overrides.
              </div>

              {transaction.audit_logs && transaction.audit_logs.length > 0 ? (
                <div className="relative pl-6 space-y-5 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
                  {transaction.audit_logs.map((audit) => (
                    <div key={audit.id} className="relative">
                      <div className="absolute -left-[27px] top-1 w-3.5 h-3.5 rounded-full bg-white border-2 border-teal-600" />
                      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold font-mono text-slate-900">
                            {audit.action}
                          </span>
                          <span className="text-[11px] text-slate-500 font-mono">
                            {formatDate(audit.timestamp)}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 font-sans">
                          Actor: {audit.actor_type} ({audit.actor_id})
                        </p>
                        {audit.payload_snapshot && (
                          <pre className="mt-2 p-2 rounded bg-slate-50 text-[10px] font-mono text-slate-700 overflow-x-auto border border-slate-200">
                            {JSON.stringify(audit.payload_snapshot, null, 2)}
                          </pre>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-sm text-slate-500 font-sans">
                  No audit trail recorded.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer: Manual Review Override Action */}
        <div className="p-4 border-t border-slate-200 bg-slate-50/70">
          {overrideAction ? (
            <div className="space-y-3 p-4 rounded-xl bg-white border border-slate-300 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900">
                  Confirm Manual Override:{' '}
                  <span
                    className={
                      overrideAction === 'FORCE_APPROVE'
                        ? 'text-emerald-700'
                        : 'text-red-700'
                    }
                  >
                    {overrideAction === 'FORCE_APPROVE' ? 'FORCE APPROVE' : 'CONFIRM FRAUD'}
                  </span>
                </span>
                <button
                  onClick={() => {
                    setOverrideAction(null);
                    setOverrideError(null);
                  }}
                  className="text-xs text-slate-500 hover:text-slate-800 font-medium"
                >
                  Cancel
                </button>
              </div>

              <textarea
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                placeholder="Enter mandatory justification for compliance audit trail..."
                rows={2}
                className="w-full text-xs p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:bg-white focus:border-teal-600"
              />

              {overrideError && (
                <p className="text-xs text-red-600">{overrideError}</p>
              )}

              <button
                disabled={submitting}
                onClick={handleManualReview}
                className={`w-full py-2.5 rounded-lg text-xs font-semibold text-white transition-all ${
                  overrideAction === 'FORCE_APPROVE'
                    ? 'bg-emerald-600 hover:bg-emerald-700 shadow-xs'
                    : 'bg-red-600 hover:bg-red-700 shadow-xs'
                } disabled:opacity-50`}
              >
                {submitting ? 'Applying & Logging Event...' : 'Submit Override to Audit Trail'}
              </button>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500">Analyst Override Options:</span>
              <div className="flex space-x-2">
                <button
                  onClick={() => setOverrideAction('FORCE_APPROVE')}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold text-emerald-800 bg-emerald-50 border border-emerald-200 hover:bg-emerald-100 transition-all flex items-center space-x-1.5 shadow-xs"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Force Approve</span>
                </button>
                <button
                  onClick={() => setOverrideAction('CONFIRM_FRAUD')}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold text-red-800 bg-red-50 border border-red-200 hover:bg-red-100 transition-all flex items-center space-x-1.5 shadow-xs"
                >
                  <Ban className="w-3.5 h-3.5" />
                  <span>Confirm Fraud</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
