import { apiFetch, apiFetchText } from "./http";

export interface ObservabilitySummary {
  service_name: string;
  metrics_enabled: boolean;
  prometheus_metrics_path: string;
  otlp_tracing_configured: boolean;
  otlp_endpoint: string | null;
  trace_ui_url: string | null;
  log_tail_enabled: boolean;
  log_file_path: string | null;
}

export interface LogTailResponse {
  path: string;
  lines: string[];
}

export async function getObservabilitySummary(): Promise<ObservabilitySummary> {
  return apiFetch<ObservabilitySummary>("/observability/summary");
}

export async function getObservabilityLogTail(lines = 200): Promise<LogTailResponse> {
  return apiFetch<LogTailResponse>(`/observability/logs/tail?lines=${lines}`);
}

/** Prometheus text exposition (same process as ``GET /metrics``). */
export async function getObservabilityMetricsText(): Promise<string> {
  return apiFetchText("/observability/metrics-text");
}
