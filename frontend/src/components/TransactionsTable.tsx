'use client';

import React, { useState, useEffect } from 'react';
import { Search, RefreshCw, Eye } from 'lucide-react';
import { Transaction } from '@/types';
import { formatCurrency, formatDate, getDecisionBadgeProps, getRiskScoreColor } from '@/lib/utils';
import { api } from '@/lib/api';

interface TransactionsTableProps {
  onSelectTransaction: (txn: Transaction) => void;
  refreshTrigger?: number;
}

export function TransactionsTable({
  onSelectTransaction,
  refreshTrigger = 0,
}: TransactionsTableProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [decisionFilter, setDecisionFilter] = useState<string>('ALL');
  const [search, setSearch] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const data = await api.getTransactions(
        page,
        pageSize,
        decisionFilter,
        undefined,
        search.trim() || undefined
      );
      setTransactions(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to load transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, [page, decisionFilter, refreshTrigger]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchTransactions();
  };

  const handleRowClick = async (item: Transaction) => {
    try {
      const fullDetail = await api.getTransactionDetail(item.id);
      onSelectTransaction(fullDetail);
    } catch {
      onSelectTransaction(item);
    }
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="space-y-4">
      {/* Controls Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search ref, email, IP, customer..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full text-xs pl-9 pr-4 py-2 rounded-lg bg-slate-50 border border-slate-200 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:bg-white focus:border-teal-600 transition-all"
          />
        </form>

        {/* Filter Pills & Refresh */}
        <div className="flex items-center space-x-2 w-full md:w-auto justify-between md:justify-end">
          <div className="flex bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs">
            {['ALL', 'APPROVED', 'REVIEW', 'BLOCKED'].map((d) => (
              <button
                key={d}
                onClick={() => {
                  setDecisionFilter(d);
                  setPage(1);
                }}
                className={`px-3 py-1 rounded-md text-xs font-semibold transition-all ${
                  decisionFilter === d
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {d}
              </button>
            ))}
          </div>

          <button
            onClick={() => fetchTransactions()}
            disabled={loading}
            className="p-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 hover:text-slate-900 shadow-xs transition-colors"
            title="Refresh Ledger"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-teal-600' : ''}`} />
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold text-[11px] tracking-wide">
                <th className="py-3 px-4">Transaction Ref</th>
                <th className="py-3 px-4">Amount</th>
                <th className="py-3 px-4">Customer & IP</th>
                <th className="py-3 px-4">Method</th>
                <th className="py-3 px-4">Risk Score</th>
                <th className="py-3 px-4">Decision</th>
                <th className="py-3 px-4">Rules Hit</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {transactions.length > 0 ? (
                transactions.map((txn) => {
                  const badge = getDecisionBadgeProps(txn.decision);
                  const colors = getRiskScoreColor(txn.risk_score);
                  return (
                    <tr
                      key={txn.id}
                      onClick={() => handleRowClick(txn)}
                      className="hover:bg-slate-50/80 transition-colors cursor-pointer"
                    >
                      <td className="py-3 px-4 text-slate-900 font-bold font-mono">
                        {txn.transaction_ref}
                      </td>
                      <td className="py-3 px-4 text-slate-900 font-bold font-mono">
                        {formatCurrency(txn.amount, txn.currency)}
                      </td>
                      <td className="py-3 px-4">
                        <div className="truncate max-w-[160px] text-slate-800 font-medium">
                          {txn.customer_email}
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono">{txn.ip_address}</div>
                      </td>
                      <td className="py-3 px-4 uppercase text-[11px] text-slate-600 font-medium">
                        {txn.payment_method}
                      </td>
                      <td className="py-3 px-4">
                        <div className="inline-flex items-center space-x-1.5 font-bold font-mono">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              txn.risk_score >= 70
                                ? 'bg-red-600'
                                : txn.risk_score >= 40
                                ? 'bg-amber-500'
                                : 'bg-emerald-600'
                            }`}
                          />
                          <span className={colors.text}>{txn.risk_score} / 100</span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[11px] font-semibold border ${badge.bg}`}
                        >
                          {txn.decision}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-600 font-medium">
                        {txn.rules_triggered_count || 0} hits
                      </td>
                      <td className="py-3 px-4 text-slate-500 text-[11px]">
                        {formatDate(txn.created_at)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRowClick(txn);
                          }}
                          className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition-colors"
                          title="Inspect Details"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={9} className="text-center py-12 text-slate-500 font-sans">
                    {loading ? 'Fetching transactions...' : 'No transactions matching query.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-3.5 border-t border-slate-200 bg-white flex items-center justify-between text-xs text-slate-600 font-sans">
          <span>
            Showing <span className="font-semibold text-slate-900">{transactions.length}</span> of{' '}
            <span className="font-semibold text-slate-900">{total}</span> transactions
          </span>
          <div className="flex space-x-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-3 py-1 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold shadow-xs disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="py-1 px-2 text-slate-600 font-medium">
              Page {page} of {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold shadow-xs disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
