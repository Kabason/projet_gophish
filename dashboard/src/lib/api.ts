// API client for the FastAPI inference service (ai-engine/api/main.py).
// Base URL comes from NEXT_PUBLIC_API_URL, defaulting to local dev.

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type FeatureContribution = {
  term: string;
  weight: number;
  direction: "phishing" | "legitimate";
};

export type ModelVote = {
  model: string;
  prediction: "phishing" | "legitimate";
  confidence: number;
};

export type PredictResponse = {
  prediction: "phishing" | "legitimate";
  confidence: number;
  model_used: string;
  top_features: FeatureContribution[];
  model_comparison: ModelVote[];
};

export type ModelMetrics = {
  best_params: Record<string, number | string | null>;
  precision: number;
  recall: number;
  f1: number;
};

export type ModelResults = {
  best_model: string;
  results: Record<string, ModelMetrics>;
};

export type AccuracyEntry = { accuracy: number; n: number };

export type Robustness = {
  best_model: string;
  accuracy_by_type: Record<string, Record<string, AccuracyEntry>>;
  accuracy_by_language: Record<string, Record<string, AccuracyEntry>>;
    detection_rate_by_tactic: Record<string, { rate: number; n: number }>;
};

export type MetricsResponse = {
  model_results: ModelResults;
  robustness: Robustness;
};

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export function predictEmail(emailText: string): Promise<PredictResponse> {
  return apiFetch<PredictResponse>("/predict", {
    method: "POST",
    body: JSON.stringify({ email_text: emailText }),
  });
}

export function getMetrics(): Promise<MetricsResponse> {
  return apiFetch<MetricsResponse>("/metrics");
}
