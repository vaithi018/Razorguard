import {
  Transaction,
  DashboardMetrics,
  ReconciliationRecord,
  RulesConfig,
  Decision
} from '@/types';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== 'undefined' ? '/api/v1' : 'http://127.0.0.1:8000/api/v1');


async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || errorBody.error || `HTTP error ${res.status}`);
  }

  const json = await res.json();
  return json.data;
}

export const api = {
  getHealth: () => fetchJson<any>(`${API_BASE}/health`),

  getMetrics: () => fetchJson<DashboardMetrics>(`${API_BASE}/analytics/metrics`),

  getTransactions: (
    page = 1,
    pageSize = 20,
    decision?: string,
    status?: string,
    search?: string
  ) => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (decision && decision !== 'ALL') params.append('decision', decision);
    if (status && status !== 'ALL') params.append('status', status);
    if (search) params.append('search', search);

    return fetchJson<{
      items: Transaction[];
      total: number;
      page: number;
      page_size: number;
      total_pages: number;
    }>(`${API_BASE}/transactions?${params.toString()}`);
  },

  getTransactionDetail: (id: string) =>
    fetchJson<Transaction>(`${API_BASE}/transactions/${id}`),

  submitManualReview: (
    id: string,
    action: 'FORCE_APPROVE' | 'CONFIRM_FRAUD',
    reason: string,
    analystId = 'analyst_01'
  ) =>
    fetchJson<Transaction>(`${API_BASE}/transactions/${id}/review-action`, {
      method: 'POST',
      headers: {
        'X-API-Key': process.env.NEXT_PUBLIC_ANALYST_API_KEY || 'rzg_demo_analyst_key_2026',
      },
      body: JSON.stringify({ action, reason, analyst_id: analystId }),
    }),

  simulateScenario: (scenarioKey: string) =>
    fetchJson<Transaction>(`${API_BASE}/transactions/simulate?scenario_key=${scenarioKey}`, {
      method: 'POST',
    }),

  createTransaction: (data: Partial<Transaction>) =>
    fetchJson<Transaction>(`${API_BASE}/transactions`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getReconciliationList: (page = 1, pageSize = 20) =>
    fetchJson<{
      items: ReconciliationRecord[];
      total: number;
      page: number;
      page_size: number;
    }>(`${API_BASE}/integrations/razorpay/reconciliation?page=${page}&page_size=${pageSize}`),

  simulateRazorpayPayment: (payload: {
    amount: number;
    currency?: string;
    status?: string;
    customer_email: string;
    method?: string;
  }) =>
    fetchJson<any>(`${API_BASE}/integrations/razorpay/simulate-test-payment`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getRulesConfig: () => fetchJson<RulesConfig>(`${API_BASE}/rules`),

  updateRulesConfig: (config: RulesConfig) =>
    fetchJson<RulesConfig>(`${API_BASE}/rules/config`, {
      method: 'PUT',
      headers: {
        'X-API-Key': process.env.NEXT_PUBLIC_ANALYST_API_KEY || 'rzg_demo_analyst_key_2026',
      },
      body: JSON.stringify(config),
    }),

  getRazorpayPayment: (paymentId: string) =>
    fetchJson<{
      payment_id: string;
      amount_inr: number;
      currency: string;
      status: string;
      method: string;
      customer_email?: string;
      customer_contact?: string;
      is_ingested: boolean;
      internal_decision?: string;
      risk_score?: number;
    }>(`${API_BASE}/integrations/razorpay/payments/${encodeURIComponent(paymentId)}`),

  ingestRazorpayPayment: (payload: {
    payment_id: string;
    amount?: number;
    amount_inr?: number;
    currency?: string;
    status?: string;
    email?: string;
    contact?: string;
    method?: string;
  }) =>
    fetchJson<{
      transaction: Transaction;
      already_processed: boolean;
      payment_id: string;
      decision: string;
      risk_score: number;
      normalized_summary: {
        amount_inr: number;
        status: string;
        method: string;
        email: string;
      };
    }>(`${API_BASE}/integrations/razorpay/payments`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
