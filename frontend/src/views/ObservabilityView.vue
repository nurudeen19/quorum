<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import * as obsApi from "@/api/observability";
import type { LogTailResponse, ObservabilitySummary } from "@/api/observability";
import { ApiError } from "@/api/http";

const tab = ref<"summary" | "metrics" | "logs" | "traces">("summary");
const summary = ref<ObservabilitySummary | null>(null);
const metricsText = ref("");
const logs = ref<LogTailResponse | null>(null);
const error = ref("");
const loading = ref(false);

async function loadSummary() {
  loading.value = true;
  error.value = "";
  try {
    summary.value = await obsApi.getObservabilitySummary();
  } catch (e) {
    summary.value = null;
    error.value =
      e instanceof ApiError
        ? e.message
        : "Could not load observability summary (is OBSERVABILITY_DASHBOARD_ENABLED=true on the API?)";
  } finally {
    loading.value = false;
  }
}

async function loadMetrics() {
  error.value = "";
  try {
    metricsText.value = await obsApi.getObservabilityMetricsText();
  } catch (e) {
    metricsText.value = "";
    error.value = e instanceof ApiError ? e.message : "Could not load metrics.";
  }
}

async function loadLogs() {
  error.value = "";
  try {
    logs.value = await obsApi.getObservabilityLogTail(300);
  } catch (e) {
    logs.value = null;
    error.value = e instanceof ApiError ? e.message : "Could not load logs.";
  }
}

onMounted(() => {
  void loadSummary();
});

async function switchTab(t: typeof tab.value) {
  tab.value = t;
  if (t === "metrics" && !metricsText.value) await loadMetrics();
  if (t === "logs" && !logs.value) await loadLogs();
  if (t === "traces" && !summary.value) await loadSummary();
}
</script>

<template>
  <div
    class="app-shell relative flex min-h-screen text-slate-100 bg-slate-950 selection:bg-cyan-500/30 selection:text-cyan-50"
  >
    <div class="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      <div
        class="absolute -top-1/2 right-1/4 h-[80%] w-[70%] rounded-full bg-[radial-gradient(ellipse_at_center,rgba(34,211,238,0.1),transparent_55%)]"
      />
    </div>

    <aside
      class="relative z-10 w-64 shrink-0 border-r border-slate-800/90 bg-slate-950/80 backdrop-blur-md"
    >
      <div class="border-b border-slate-800/90 p-5">
        <RouterLink
          to="/dashboard"
          class="text-xs font-medium text-slate-500 transition hover:text-cyan-400"
        >
          ← Dashboard
        </RouterLink>
        <div class="app-display mt-2 text-xl font-bold tracking-tight text-white">Observability</div>
        <p class="mt-1 text-xs text-slate-500">Metrics, traces, logs</p>
      </div>
      <nav class="flex flex-col gap-1 p-3">
        <button
          type="button"
          class="rounded-xl px-4 py-2.5 text-left text-sm font-semibold transition"
          :class="
            tab === 'summary'
              ? 'bg-cyan-500/15 text-white ring-1 ring-cyan-500/25'
              : 'text-slate-400 hover:bg-slate-800/60 hover:text-white'
          "
          @click="switchTab('summary')"
        >
          Summary
        </button>
        <button
          type="button"
          class="rounded-xl px-4 py-2.5 text-left text-sm font-semibold transition"
          :class="
            tab === 'metrics'
              ? 'bg-cyan-500/15 text-white ring-1 ring-cyan-500/25'
              : 'text-slate-400 hover:bg-slate-800/60 hover:text-white'
          "
          @click="switchTab('metrics')"
        >
          Metrics
        </button>
        <button
          type="button"
          class="rounded-xl px-4 py-2.5 text-left text-sm font-semibold transition"
          :class="
            tab === 'logs'
              ? 'bg-cyan-500/15 text-white ring-1 ring-cyan-500/25'
              : 'text-slate-400 hover:bg-slate-800/60 hover:text-white'
          "
          @click="switchTab('logs')"
        >
          Logs
        </button>
        <button
          type="button"
          class="rounded-xl px-4 py-2.5 text-left text-sm font-semibold transition"
          :class="
            tab === 'traces'
              ? 'bg-cyan-500/15 text-white ring-1 ring-cyan-500/25'
              : 'text-slate-400 hover:bg-slate-800/60 hover:text-white'
          "
          @click="switchTab('traces')"
        >
          Traces
        </button>
      </nav>
    </aside>

    <main class="relative z-10 flex-1 overflow-y-auto p-6">
      <div class="mx-auto max-w-5xl">
        <p v-if="loading && tab === 'summary'" class="text-sm text-slate-400">Loading…</p>
        <p v-if="error" class="mb-4 rounded-lg border border-red-500/30 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {{ error }}
        </p>

        <div v-if="tab === 'summary' && summary" class="space-y-4">
          <section class="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
            <h2 class="app-display text-lg font-semibold text-white">Service</h2>
            <dl class="mt-4 grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt class="text-slate-500">Service name (OTel)</dt>
                <dd class="mt-1 font-mono text-slate-200">{{ summary.service_name }}</dd>
              </div>
              <div>
                <dt class="text-slate-500">Prometheus metrics</dt>
                <dd class="mt-1 text-slate-200">
                  {{ summary.metrics_enabled ? "Enabled" : "Disabled" }} — scrape path
                  <code class="rounded bg-slate-950 px-1.5 py-0.5 text-cyan-300">{{
                    summary.prometheus_metrics_path
                  }}</code>
                  on the API host (dev: also proxied at <code class="text-cyan-300">/metrics</code> from Vite).
                </dd>
              </div>
              <div>
                <dt class="text-slate-500">OTLP tracing</dt>
                <dd class="mt-1 text-slate-200">
                  {{ summary.otlp_tracing_configured ? "Endpoint configured" : "Console / default exporter" }}
                  <span v-if="summary.otlp_endpoint" class="mt-1 block truncate font-mono text-xs text-slate-400">{{
                    summary.otlp_endpoint
                  }}</span>
                </dd>
              </div>
              <div>
                <dt class="text-slate-500">Log tail API</dt>
                <dd class="mt-1 text-slate-200">
                  {{ summary.log_tail_enabled ? "Enabled" : "Disabled" }}
                  <span v-if="summary.log_file_path" class="mt-1 block truncate text-xs text-slate-400">{{
                    summary.log_file_path
                  }}</span>
                </dd>
              </div>
            </dl>
          </section>
        </div>

        <div v-if="tab === 'metrics'" class="space-y-3">
          <p class="text-sm text-slate-400">
            Prometheus text format from this API process. Use the Metrics tab refresh by switching tabs
            or reload the page.
          </p>
          <pre
            class="max-h-[70vh] overflow-auto rounded-xl border border-slate-800 bg-slate-950/80 p-4 text-xs leading-relaxed text-slate-300"
          >{{ metricsText || "—" }}</pre>
        </div>

        <div v-if="tab === 'logs'" class="space-y-3">
          <p v-if="logs" class="text-xs text-slate-500">File: {{ logs.path }}</p>
          <pre
            class="max-h-[70vh] overflow-auto rounded-xl border border-slate-800 bg-slate-950/80 p-4 text-xs leading-relaxed text-slate-300 whitespace-pre-wrap font-mono"
          >{{ logs ? logs.lines.join("\n") : "—" }}</pre>
        </div>

        <div v-if="tab === 'traces'" class="space-y-4 text-sm text-slate-300">
          <p>
            Spans are exported via OpenTelemetry (OTLP when configured, otherwise console in dev). Use
            your trace UI (Jaeger, Grafana Tempo, Honeycomb, etc.) to explore latency and dependencies.
          </p>
          <p v-if="summary?.trace_ui_url">
            <a
              :href="summary.trace_ui_url"
              class="font-semibold text-cyan-400 underline hover:text-cyan-300"
              target="_blank"
              rel="noopener noreferrer"
              >Open trace UI</a
            >
          </p>
          <p v-else class="text-slate-500">
            Set <code class="rounded bg-slate-900 px-1.5 py-0.5 text-cyan-200">OBSERVABILITY_TRACE_UI_URL</code>
            on the API to show a link here (for example your Jaeger base URL).
          </p>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-display {
  font-family: "Outfit", "DM Sans", system-ui, sans-serif;
}
</style>
