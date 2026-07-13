const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ReasonCode {
  feature: string;
  impact: number;
  direction: string;
  description: string;
  code: string;
  category: string;
}

export interface PredictionResult {
  account_id: string;
  pd_score: number;
  pd_percent: number;
  rag_bucket: string;
  segment: string;
  rating_grade: string;
  rating_band: string;
  ifrs9_stage: string;
  ifrs9_basis: string;
  sma_category: string;
  sma_definition: string;
  explanation_method: "shap" | "perturbation_proxy";
  imputed_fields: string[];
  recommended_action: string;
  reason_codes: ReasonCode[];
  hazard_curve: { month: number; hazard: number; cumulative_pd: number }[];
  model_version: string;
  timestamp: string;
}

export interface PortfolioSummary {
  total_accounts: number;
  default_rate_actual: number;
  avg_pd: number;
  rag_breakdown: Record<string, number>;
  total_exposure: number;
  exposure_at_risk: number;
  exposure_by_rag: Record<string, number>;
  expected_loss: number;
  ifrs9_stage_breakdown: Record<string, number>;
  ecl_provision: number;
  sma_breakdown: Record<string, number>;
  ecl_method: string;
  sector_risk: { sector: string; avg_pd: number; count: number; exposure: number }[];
  high_risk_accounts: {
    account_id: string;
    sector: string;
    loan_type: string;
    predicted_pd: number;
    loan_amount: number;
    default_12m: number;
  }[];
  model_metrics: Record<string, number | string>;
}

export interface SkippedRow {
  row: number;
  account_id: string | null;
  errors: string[];
}

export interface BatchResult {
  predictions: PredictionResult[];
  total: number;
  skipped: SkippedRow[];
  imputed_columns: string[];
  warning: string | null;
}

export interface DecisionRecord {
  account_id: string;
  decision: "acknowledge" | "override" | "escalate";
  note: string;
  officer: string;
  model_pd: number;
  model_rag: string;
  timestamp: string;
}

export interface AccountRow {
  account_id: string;
  loan_type: string;
  sector: string;
  borrower_profile: string;
  enterprise_size: string;
  loan_amount: number;
  predicted_pd: number;
  rag: string;
  default_12m: number;
}

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { ...options?.headers },
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export function getPortfolioSummary(): Promise<PortfolioSummary> {
  return fetchApi<PortfolioSummary>("/portfolio/summary");
}

export function getAccounts(params?: {
  rag?: string;
  sector?: string;
  search?: string;
  sortBy?: string;
  sortDir?: string;
  limit?: number;
  offset?: number;
}): Promise<{ accounts: AccountRow[]; total: number }> {
  const q = new URLSearchParams();
  if (params?.rag) q.set("rag", params.rag);
  if (params?.sector) q.set("sector", params.sector);
  if (params?.search) q.set("search", params.search);
  if (params?.sortBy) q.set("sort_by", params.sortBy);
  if (params?.sortDir) q.set("sort_dir", params.sortDir);
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset !== undefined) q.set("offset", String(params.offset));
  return fetchApi(`/portfolio/accounts?${q}`);
}

export function formatINR(amount: number): string {
  // Indian digit grouping (lakh/crore comma style).
  const grp = (n: number, dp: number) =>
    n.toLocaleString("en-IN", { minimumFractionDigits: dp, maximumFractionDigits: dp });
  if (amount >= 1e12) return `\u20b9${grp(amount / 1e7, 0)} Cr`; // >= 1 lakh Cr
  if (amount >= 1e7) return `\u20b9${grp(amount / 1e7, 2)} Cr`;
  if (amount >= 1e5) return `\u20b9${grp(amount / 1e5, 2)} L`;
  if (amount >= 1e3) return `\u20b9${grp(amount / 1e3, 1)}K`;
  return `\u20b9${amount.toFixed(0)}`;
}

export function getAccountDetail(accountId: string): Promise<PredictionResult> {
  return fetchApi<PredictionResult>(`/explain/${accountId}`);
}

export async function uploadBatch(file: File): Promise<BatchResult> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/predict/batch`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

export function postDecision(payload: {
  account_id: string;
  decision: "acknowledge" | "override" | "escalate";
  note: string;
  officer: string;
}): Promise<DecisionRecord> {
  return fetchApi<DecisionRecord>("/decisions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getDecisions(accountId: string): Promise<DecisionRecord[]> {
  return fetchApi<DecisionRecord[]>(`/decisions/${accountId}`);
}

export function getHealth(): Promise<{ status: string; model_loaded: boolean }> {
  return fetchApi("/health");
}
