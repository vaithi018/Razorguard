export type Decision = 'APPROVED' | 'REVIEW' | 'BLOCKED';

export interface RuleEvaluation {
  rule_id: string;
  rule_name: string;
  triggered: boolean;
  score_impact: number;
  is_hard_block: boolean;
  details: Record<string, any>;
}

export interface AIEnrichment {
  status: string;
  narrative?: string;
  threat_vector?: string;
  contributing_signals: string[];
  investigation_steps: string[];
  model?: string;
}

export interface AuditLogItem {
  id: string;
  action: string;
  actor_type: string;
  actor_id: string;
  payload_snapshot?: Record<string, any>;
  timestamp: string;
}

export interface Transaction {
  id: string;
  transaction_ref: string;
  amount: number;
  currency: string;
  customer_id: string;
  customer_email: string;
  customer_phone?: string;
  ip_address: string;
  payment_method: string;
  card_bin?: string;
  card_last4?: string;
  card_fingerprint?: string;
  decision: Decision;
  risk_score: number;
  status: string;
  razorpay_payment_id?: string;
  razorpay_order_id?: string;
  created_at: string;
  updated_at?: string;
  rules_triggered_count?: number;
  evaluations?: RuleEvaluation[];
  ai_enrichment?: AIEnrichment;
  audit_logs?: AuditLogItem[];
}

export interface RiskScoreDistribution {
  range_0_19: number;
  range_20_39: number;
  range_40_59: number;
  range_60_79: number;
  range_80_100: number;
}

export interface TopTriggeredRule {
  rule_id: string;
  rule_name: string;
  count: number;
}

export interface DashboardMetrics {
  total_transactions: number;
  approved_count: number;
  review_count: number;
  blocked_count: number;
  approval_rate_percent: number;
  average_risk_score: number;
  total_volume_inr: number;
  risk_distribution: RiskScoreDistribution;
  top_triggered_rules: TopTriggeredRule[];
}

export interface ReconciliationRecord {
  id: string;
  transaction_id?: string;
  razorpay_payment_id: string;
  razorpay_status: string;
  internal_decision?: Decision;
  is_discrepant: boolean;
  discrepancy_type?: string;
  discrepancy_details?: {
    severity?: string;
    message?: string;
    recommended_action?: string;
  };
  checked_at: string;
}

export interface RulesConfig {
  thresholds: {
    review_min_score: number;
    blocked_min_score: number;
  };
  rules: Record<string, any>;
}
