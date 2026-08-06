import { ApiError } from "@/lib/api";

export type CostComponents = {
  tts: number;
  llm: number;
  compute: number;
  storage: number;
  platform: number;
};

export type CostBudget = {
  monthly_limit_usd: number | null;
  month_spent_usd: number;
  utilization: number | null;
  thresholds: number[];
  projected_month_usd: number;
};

export type CostTotals = {
  all_time_usd: number;
  month_usd: number;
  previous_month_usd: number;
  runs_all_time: number;
  runs_month: number;
  chars_month: number;
  audio_ms_month: number;
  avg_run_usd: number;
  usd_per_1k_chars: number;
  usd_per_audio_minute: number;
  retained_storage_usd_per_month: number;
  active_users_month: number;
};

export type CostMonth = {
  month: string;
  total_usd: number;
  components: CostComponents;
  runs: number;
  chars: number;
  audio_ms: number;
};

export type CostDay = {
  date: string;
  total_usd: number;
  runs: number;
};

export type CostVendor = {
  vendor: string;
  voice: string;
  total_usd: number;
  runs: number;
  chars: number;
};

export type CostUser = {
  user_ref: string;
  total_usd: number;
  runs: number;
};

export type CostRun = {
  reading_id: string;
  created_at: string;
  vendor: string;
  char_count: number;
  total_usd: number;
  components: CostComponents;
  usage: {
    chars_synthesized: number;
    chunks: number;
    audio_ms: number;
    stored_bytes: number;
    lambda_memory_mb: number;
    // Open map on purpose: the processor emits normalize/synthesize/merge plus
    // overhead, and legacy run records can carry an empty object.
    compute_ms_by_stage: Record<string, number>;
  };
};

export type CostLimits = {
  max_text_chars: number;
  max_run_cost_usd: number;
  monthly_budget_usd: number | null;
};

export type CostSummary = {
  currency: "USD";
  price_book_version: string;
  budget: CostBudget;
  totals: CostTotals;
  months: CostMonth[];
  days: CostDay[];
  components: CostComponents;
  vendors: CostVendor[];
  users: CostUser[];
  runs: CostRun[];
  limits: CostLimits;
};

export type CostEstimateRejection = {
  code: string;
  message: string;
};

export type CostEstimateVendor = {
  vendor: string;
  voice: string;
  estimated_audio_ms: number;
  allowed: boolean;
  rejection: CostEstimateRejection | null;
  cost: {
    total_usd: number;
    components: CostComponents;
  };
};

export type CostEstimate = {
  char_count: number;
  chunk_count: number;
  price_book_version: string;
  limits: {
    max_text_chars: number;
    max_run_cost_usd: number;
  };
  vendors: CostEstimateVendor[];
};

async function costsFetch(
  path: string,
  init: { method?: string; body?: string } = {},
) {
  const headers: Record<string, string> = {};
  if (init.body !== undefined) headers["Content-Type"] = "application/json";

  const res = await fetch(path, {
    method: init.method ?? "GET",
    body: init.body,
    headers,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new ApiError(res.status, text);
  }
  return res;
}

export async function estimateCost(
  originalText: string,
): Promise<CostEstimate> {
  const res = await costsFetch("/api/v1/costs/estimate", {
    method: "POST",
    body: JSON.stringify({ original_text: originalText }),
  });
  return res.json();
}
