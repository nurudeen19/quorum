<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { RouterLink, useRouter } from "vue-router";

import type { AttendeeBriefing, BriefingContext } from "@/api/chat";
import { streamChat } from "@/api/chat";
import * as conversationsApi from "@/api/conversations";
import { ApiError } from "@/api/http";
import SafeMarkdown from "@/components/SafeMarkdown.vue";
import { derivePipelineStage } from "@/lib/briefingPipeline";
import { useAuthStore } from "@/stores/auth";
import { useChatSessionsStore } from "@/stores/chatSessions";

function extractAssistantReply(state: Record<string, unknown> | null): string {
  if (!state) return "No response received.";
  const fm = state["final_user_message"];
  const ve = state["validation_error"];
  const fromFinal = typeof fm === "string" ? fm.trim() : "";
  const fromErr = typeof ve === "string" ? ve.trim() : "";
  return fromFinal || fromErr || "No response received.";
}

const auth = useAuthStore();
const router = useRouter();
const sessions = useChatSessionsStore();
const {
  draftAttendees,
  draftGoal,
  activeMessages,
  activeConversationId,
  remoteList,
  listLoading,
  messagesLoading,
} = storeToRefs(sessions);

const followUp = ref("");
const loading = ref(false);
const error = ref("");
const pipelineStage = ref("Starting…");

const chatScrollArea = ref<HTMLElement | null>(null);
const followUpInput = ref<HTMLTextAreaElement | null>(null);

async function scrollChatToBottom(): Promise<void> {
  await nextTick();
  const el = chatScrollArea.value;
  if (el) {
    el.scrollTop = el.scrollHeight;
  }
}

async function focusFollowUpInput(): Promise<void> {
  await nextTick();
  requestAnimationFrame(() => {
    followUpInput.value?.focus({ preventScroll: true });
  });
}

const showBriefingForm = computed(
  () =>
    !activeConversationId.value &&
    !messagesLoading.value &&
    activeMessages.value.length === 0,
);

function shortTime(ts: string | number): string {
  try {
    const d = typeof ts === "number" ? new Date(ts) : new Date(ts);
    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(d);
  } catch {
    return "";
  }
}

function addAttendee() {
  draftAttendees.value.push({ name: "", company: "" });
}

function removeAttendee(i: number) {
  if (draftAttendees.value.length <= 1) return;
  draftAttendees.value.splice(i, 1);
}

function briefingPreview(ctx: BriefingContext): string {
  const lines = ["Attendees:"];
  for (const a of ctx.attendees) {
    const n = a.name.trim();
    const c = a.company?.trim();
    lines.push(c ? `- ${n} (${c})` : `- ${n}`);
  }
  lines.push("", "Goal:", ctx.goal.trim());
  return lines.join("\n");
}

function buildBriefingContext(): BriefingContext | null {
  const cleaned: AttendeeBriefing[] = [];
  for (const a of draftAttendees.value) {
    const n = a.name.trim();
    if (!n) continue;
    const c = a.company?.trim();
    cleaned.push({ name: n, company: c || null });
  }
  if (cleaned.length === 0) return null;
  const g = draftGoal.value.trim();
  if (!g) return null;
  return { attendees: cleaned, goal: g };
}

async function submitBriefing() {
  error.value = "";
  const ctx = buildBriefingContext();
  if (!ctx) {
    error.value = "Add at least one attendee with a name and a goal.";
    return;
  }

  loading.value = true;
  pipelineStage.value = derivePipelineStage(null);
  const userPreview = briefingPreview(ctx);
  activeMessages.value = [{ role: "user", content: userPreview }];

  let lastState: Record<string, unknown> | null = null;

  try {
    await streamChat(
      { briefing_context: ctx },
      {
        onMeta: (id) => {
          activeConversationId.value = id;
        },
        onState: (data: Record<string, unknown>) => {
          lastState = data;
          pipelineStage.value = derivePipelineStage(data);
        },
        onDone: () => {},
      },
    );

    const assistant = extractAssistantReply(lastState);
    activeMessages.value.push({ role: "assistant", content: assistant });
    await sessions.refreshAfterTurn();
    await scrollChatToBottom();
    await focusFollowUpInput();
  } catch (e) {
    activeMessages.value = [];
    if (e instanceof ApiError) {
      error.value = e.message;
    } else {
      error.value = e instanceof Error ? e.message : "Request failed";
    }
  } finally {
    loading.value = false;
  }
}

async function submitFollowUp() {
  const cid = activeConversationId.value;
  const text = followUp.value.trim();
  if (!cid || !text) return;

  error.value = "";
  loading.value = true;
  pipelineStage.value = derivePipelineStage(null);
  activeMessages.value.push({ role: "user", content: text });
  followUp.value = "";

  let lastState: Record<string, unknown> | null = null;

  try {
    await streamChat(
      { conversation_id: cid, content: text },
      {
        onState: (data: Record<string, unknown>) => {
          lastState = data;
          pipelineStage.value = derivePipelineStage(data);
        },
      },
    );

    const assistant = extractAssistantReply(lastState);
    activeMessages.value.push({ role: "assistant", content: assistant });
    await sessions.refreshAfterTurn();
    await scrollChatToBottom();
    await focusFollowUpInput();
  } catch (e) {
    activeMessages.value.pop();
    followUp.value = text;
    if (e instanceof ApiError) {
      error.value = e.message;
    } else {
      error.value = e instanceof Error ? e.message : "Request failed";
    }
  } finally {
    loading.value = false;
  }
}

function newConversation() {
  sessions.startNewConversation();
  followUp.value = "";
  error.value = "";
}

async function pickConversation(id: string) {
  error.value = "";
  followUp.value = "";
  await sessions.selectConversation(id);
}

async function deleteConversation(id: string, ev: Event) {
  ev.preventDefault();
  ev.stopPropagation();
  error.value = "";
  try {
    await sessions.deleteRemoteConversation(id);
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Could not delete conversation.";
  }
  followUp.value = "";
}

async function logout() {
  await auth.logout();
  router.push({ name: "login" });
}

async function submitMessageFeedback(index: number, vote: "up" | "down") {
  const m = activeMessages.value[index];
  if (!m || m.role !== "assistant" || !m.id) return;
  const next = m.feedback === vote ? null : vote;
  error.value = "";
  try {
    await conversationsApi.patchMessageFeedback(m.id, { feedback: next });
    m.feedback = next === null ? undefined : next;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Could not save feedback.";
  }
}

onMounted(() => {
  void sessions.fetchRemoteConversations();
});

watch(
  () => auth.user?.id,
  () => {
    void sessions.fetchRemoteConversations();
  },
);

watch(
  () => [activeMessages.value.length, messagesLoading.value] as const,
  async () => {
    if (messagesLoading.value) return;
    await scrollChatToBottom();
  },
);

const inputClass =
  "w-full rounded-xl border border-slate-700/90 bg-slate-950/60 px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 shadow-inner shadow-black/20 transition focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20";
</script>

<template>
  <div
    class="app-shell relative flex h-dvh max-h-dvh min-h-0 overflow-hidden text-slate-100 bg-slate-950 selection:bg-cyan-500/30 selection:text-cyan-50"
  >
    <div class="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      <div
        class="absolute -top-1/2 left-1/3 h-[90%] w-[80%] -translate-x-1/2 rounded-full bg-[radial-gradient(ellipse_at_center,rgba(34,211,238,0.1),transparent_58%)]"
      />
      <div
        class="absolute bottom-0 right-0 h-[55%] w-[50%] rounded-full bg-[radial-gradient(ellipse_at_center,rgba(139,92,246,0.08),transparent_60%)]"
      />
    </div>

    <aside
      class="relative z-10 flex h-full min-h-0 w-72 shrink-0 flex-col border-r border-slate-800/90 bg-slate-950/80 backdrop-blur-md"
    >
      <div class="shrink-0 border-b border-slate-800/90 p-5">
        <RouterLink
          to="/dashboard"
          class="text-xs font-medium text-slate-500 transition hover:text-cyan-400"
        >
          ← Dashboard
        </RouterLink>
        <div class="app-display mt-2 text-xl font-bold tracking-tight text-white">Briefing chat</div>
        <p class="mt-1 text-xs text-slate-500">Pre-meeting intelligence</p>
      </div>

      <nav class="shrink-0 space-y-1 border-b border-slate-800/60 px-3 py-3">
        <RouterLink
          to="/dashboard"
          class="block rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-400 transition hover:bg-slate-800/60 hover:text-white"
        >
          Dashboard
        </RouterLink>
        <RouterLink
          to="/chat"
          class="app-display block rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-400 transition hover:bg-slate-800/60 hover:text-white"
          active-class="bg-gradient-to-r from-cyan-500/15 to-sky-500/10 !text-white shadow-inner shadow-cyan-500/10 ring-1 ring-cyan-500/25"
        >
          Briefing chat
        </RouterLink>
      </nav>

      <div class="flex min-h-0 flex-1 flex-col gap-2 px-3 py-3">
        <p class="px-1 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Conversations
        </p>
        <p v-if="listLoading" class="px-2 text-xs text-slate-500">Loading…</p>
        <button
          type="button"
          class="app-display w-full rounded-xl border px-3 py-2.5 text-left text-sm font-semibold transition"
          :class="
            activeConversationId === null
              ? 'border-cyan-500/40 bg-cyan-500/10 text-white ring-1 ring-cyan-500/25'
              : 'border-slate-700/80 bg-slate-900/40 text-slate-300 hover:border-slate-600 hover:text-white'
          "
          @click="newConversation"
        >
          + New briefing
        </button>

        <ul class="min-h-0 flex-1 space-y-1 overflow-y-auto pr-0.5">
          <li v-for="c in remoteList" :key="c.id">
            <div class="group flex items-stretch gap-0.5">
              <button
                type="button"
                class="app-display min-w-0 flex-1 rounded-xl border px-3 py-2 text-left text-sm transition"
                :class="
                  c.id === activeConversationId
                    ? 'border-cyan-500/35 bg-cyan-500/10 text-white ring-1 ring-cyan-500/20'
                    : 'border-transparent bg-slate-900/30 text-slate-300 hover:bg-slate-800/50 hover:text-white'
                "
                @click="pickConversation(c.id)"
              >
                <span class="block truncate font-medium">{{ sessions.displayTitle(c) }}</span>
                <span class="mt-0.5 block text-[11px] text-slate-500">{{ shortTime(c.updated_at) }}</span>
              </button>
              <button
                type="button"
                class="shrink-0 rounded-lg px-2 text-slate-600 opacity-0 transition hover:bg-red-500/15 hover:text-red-400 group-hover:opacity-100"
                title="Delete this conversation"
                aria-label="Delete conversation"
                @click="deleteConversation(c.id, $event)"
              >
                ×
              </button>
            </div>
          </li>
        </ul>
        <p v-if="!listLoading && remoteList.length === 0" class="px-2 text-xs text-slate-600">
          No briefing threads yet. Use "New briefing", or threads will show here after your first
          message.
        </p>
      </div>

      <div class="shrink-0 border-t border-slate-800/90 p-3">
        <button
          type="button"
          class="w-full rounded-xl px-4 py-2.5 text-left text-sm text-slate-500 transition hover:bg-slate-800/50 hover:text-slate-200"
          @click="logout"
        >
          Sign out
        </button>
      </div>
    </aside>

    <div class="relative z-10 flex h-full min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
      <header
        class="flex shrink-0 items-center justify-between gap-4 border-b border-slate-800/90 bg-slate-950/50 px-5 py-4 backdrop-blur-sm"
      >
        <div class="min-w-0">
          <p class="truncate text-sm text-slate-400">
            <template v-if="activeConversationId">
              <span class="font-mono text-xs text-cyan-500/90">{{ activeConversationId.slice(0, 8) }}…</span>
              <span class="text-slate-600"> · </span>
              <span>Active thread</span>
            </template>
            <template v-else>
              <span
                class="rounded-full bg-cyan-500/10 px-2 py-0.5 text-xs font-semibold text-cyan-300 ring-1 ring-cyan-500/25"
              >
                New
              </span>
              <span class="ml-2">Structured first message, then follow-ups</span>
            </template>
          </p>
        </div>
        <button
          v-if="activeConversationId || activeMessages.length > 0"
          type="button"
          class="shrink-0 rounded-full border border-slate-600 bg-slate-900/60 px-4 py-1.5 text-sm font-medium text-slate-200 transition hover:border-cyan-500/40 hover:text-white disabled:opacity-50"
          :disabled="loading"
          @click="newConversation"
        >
          New conversation
        </button>
      </header>

      <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
        <div
          ref="chatScrollArea"
          class="min-h-0 flex-1 overflow-y-auto overflow-x-hidden px-4 py-5 sm:px-6"
        >
          <div class="mx-auto flex w-full max-w-3xl flex-col gap-5">
            <p
              v-if="messagesLoading"
              class="py-16 text-center text-sm text-slate-500"
            >
              Loading messages…
            </p>
            <template v-else>
            <div
              v-if="showBriefingForm"
              class="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/55 p-6 shadow-xl shadow-black/25 ring-1 ring-white/5"
            >
              <div
                class="mb-5 h-1 w-16 rounded-full bg-gradient-to-r from-cyan-400 to-sky-500"
                aria-hidden="true"
              />
              <h2 class="app-display text-lg font-semibold text-white">
                Who are you meeting, and what do you need?
              </h2>
              <p class="mt-2 text-sm leading-relaxed text-slate-400">
                Add attendees (name and optional company), then your goal. After the first reply you
                can send free-form follow-ups in the thread.
              </p>

              <div class="mt-6 space-y-4">
                <div
                  v-for="(row, i) in draftAttendees"
                  :key="'att-' + i"
                  class="flex flex-wrap items-end gap-3 rounded-xl bg-slate-950/40 p-4 ring-1 ring-slate-800/80"
                >
                  <div class="min-w-[140px] flex-1">
                    <label class="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-500"
                      >Name</label
                    >
                    <input v-model="row.name" type="text" :class="inputClass" placeholder="Full name" />
                  </div>
                  <div class="min-w-[140px] flex-1">
                    <label class="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-500"
                      >Company (optional)</label
                    >
                    <input v-model="row.company" type="text" :class="inputClass" placeholder="Company" />
                  </div>
                  <button
                    v-if="draftAttendees.length > 1"
                    type="button"
                    class="rounded-lg px-3 py-2 text-sm font-medium text-red-400 transition hover:bg-red-500/10 hover:text-red-300"
                    @click="removeAttendee(i)"
                  >
                    Remove
                  </button>
                </div>
              </div>

              <button
                type="button"
                class="mt-2 text-sm font-semibold text-cyan-400 transition hover:text-cyan-300"
                @click="addAttendee"
              >
                + Add attendee
              </button>

              <div class="mt-5">
                <label class="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-500"
                  >Goal</label
                >
                <textarea
                  v-model="draftGoal"
                  rows="4"
                  :class="inputClass"
                  placeholder="What should the briefing help you achieve?"
                />
              </div>

              <p
                v-if="error"
                class="mt-4 rounded-lg border border-red-500/30 bg-red-950/40 px-3 py-2 text-sm text-red-200"
              >
                {{ error }}
              </p>

              <button
                type="button"
                class="app-display mt-6 w-full rounded-full bg-gradient-to-r from-cyan-400 to-sky-400 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-500/20 transition hover:from-cyan-300 hover:to-sky-300 disabled:opacity-50"
                :disabled="loading"
                @click="submitBriefing"
              >
                {{ loading ? "Starting…" : "Start briefing" }}
              </button>
            </div>

            <div
              v-for="(m, index) in activeMessages"
              :key="m.id ?? 'msg-' + index + '-' + (m.content?.length ?? 0)"
              class="flex w-full"
              :class="m.role === 'user' ? 'justify-end' : 'justify-start'"
            >
              <div
                class="max-w-[min(100%,42rem)] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-lg"
                :class="
                  m.role === 'user'
                    ? 'border border-cyan-500/25 bg-gradient-to-br from-cyan-950/80 to-slate-900/90 text-slate-100'
                    : 'border border-violet-500/20 bg-slate-900/80 text-slate-200 ring-1 ring-slate-800/90'
                "
              >
                <div
                  class="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide"
                  :class="m.role === 'user' ? 'text-cyan-400/90' : 'text-violet-300/90'"
                >
                  {{ m.role === "user" ? "You" : "Assistant" }}
                </div>
                <SafeMarkdown :source="m.content" />
                <div
                  v-if="m.role === 'assistant' && m.id"
                  class="mt-3 flex flex-wrap items-center gap-2 border-t border-slate-700/60 pt-3"
                >
                  <span class="text-[11px] font-medium uppercase tracking-wide text-slate-500">
                    Helpful?
                  </span>
                  <button
                    type="button"
                    class="inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition"
                    :class="
                      m.feedback === 'up'
                        ? 'border-emerald-500/50 bg-emerald-500/15 text-emerald-200'
                        : 'border-slate-600/80 bg-slate-800/50 text-slate-400 hover:border-emerald-500/35 hover:text-emerald-200'
                    "
                    :aria-pressed="m.feedback === 'up'"
                    title="Thumbs up"
                    @click="submitMessageFeedback(index, 'up')"
                  >
                    <span class="text-base leading-none" aria-hidden="true">👍</span>
                    Good
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition"
                    :class="
                      m.feedback === 'down'
                        ? 'border-amber-500/50 bg-amber-500/15 text-amber-100'
                        : 'border-slate-600/80 bg-slate-800/50 text-slate-400 hover:border-amber-500/35 hover:text-amber-100'
                    "
                    :aria-pressed="m.feedback === 'down'"
                    title="Thumbs down"
                    @click="submitMessageFeedback(index, 'down')"
                  >
                    <span class="text-base leading-none" aria-hidden="true">👎</span>
                    Needs work
                  </button>
                </div>
              </div>
            </div>

            <div v-if="loading && activeMessages.length > 0" class="flex justify-start">
              <div
                class="pipeline-card max-w-[min(100%,42rem)] overflow-hidden rounded-2xl border border-cyan-500/20 bg-slate-900/70 px-5 py-4 shadow-lg shadow-cyan-500/5 ring-1 ring-cyan-500/10"
              >
                <div class="flex items-start gap-3">
                  <div class="relative mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center">
                    <span
                      class="absolute h-8 w-8 rounded-full bg-cyan-400/25 blur-md pipeline-pulse"
                      aria-hidden="true"
                    />
                    <span
                      class="relative flex h-2.5 w-2.5 rounded-full bg-cyan-400 shadow-[0_0_12px_rgba(34,211,238,0.8)]"
                    >
                      <span
                        class="absolute inset-0 animate-ping rounded-full bg-cyan-400 opacity-40"
                      />
                    </span>
                  </div>
                  <div class="min-w-0 flex-1">
                    <p class="text-xs font-semibold uppercase tracking-wider text-cyan-400/90">
                      Briefing in progress
                    </p>
                    <p class="mt-1 text-sm font-medium text-slate-200">
                      {{ pipelineStage }}
                    </p>
                    <div class="mt-3 flex items-center gap-1" aria-hidden="true">
                      <span class="pipeline-dot h-1.5 w-1.5 rounded-full bg-cyan-400/90" />
                      <span class="pipeline-dot h-1.5 w-1.5 rounded-full bg-cyan-400/90" />
                      <span class="pipeline-dot h-1.5 w-1.5 rounded-full bg-cyan-400/90" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            </template>
          </div>
        </div>

        <div
          v-if="activeConversationId && !messagesLoading"
          class="shrink-0 border-t border-slate-800/90 bg-slate-950/85 px-4 py-4 backdrop-blur-md sm:px-6"
        >
          <div class="mx-auto flex w-full max-w-3xl flex-col gap-3">
            <p v-if="error" class="text-sm text-red-300">{{ error }}</p>
            <div class="flex gap-3">
              <textarea
                ref="followUpInput"
                v-model="followUp"
                rows="2"
                class="min-h-[3rem] flex-1 resize-y rounded-xl border border-slate-700/90 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-600 focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20"
                placeholder="Ask a follow-up…"
                :disabled="loading"
                @keydown.enter.exact.prevent="submitFollowUp"
              />
              <button
                type="button"
                class="app-display h-fit shrink-0 self-end rounded-full bg-gradient-to-r from-cyan-400 to-sky-400 px-6 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-500/15 transition hover:from-cyan-300 hover:to-sky-300 disabled:opacity-50"
                :disabled="loading || !followUp.trim()"
                @click="submitFollowUp"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-display {
  font-family: "Outfit", "DM Sans", system-ui, sans-serif;
}

.pipeline-card {
  background: linear-gradient(
    135deg,
    rgba(15, 23, 42, 0.95) 0%,
    rgba(17, 24, 39, 0.92) 40%,
    rgba(12, 74, 110, 0.12) 100%
  );
  background-size: 200% 200%;
  animation: pipeline-shimmer 3.5s ease infinite;
}

@keyframes pipeline-shimmer {
  0%,
  100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.pipeline-pulse {
  animation: pipeline-glow 2s ease-in-out infinite;
}

@keyframes pipeline-glow {
  0%,
  100% {
    opacity: 0.5;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.15);
  }
}

.pipeline-dot {
  animation: pipeline-bounce 1.2s ease-in-out infinite;
}

.pipeline-dot:nth-child(1) {
  animation-delay: 0ms;
}

.pipeline-dot:nth-child(2) {
  animation-delay: 160ms;
}

.pipeline-dot:nth-child(3) {
  animation-delay: 320ms;
}

@keyframes pipeline-bounce {
  0%,
  80%,
  100% {
    transform: translateY(0);
    opacity: 0.35;
  }
  40% {
    transform: translateY(-5px);
    opacity: 1;
  }
}
</style>
