<script setup lang="ts">
import { computed, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";

import type { AttendeeBriefing, BriefingContext } from "@/api/chat";
import { streamChat } from "@/api/chat";
import { ApiError } from "@/api/http";
import { useAuthStore } from "@/stores/auth";

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

const conversationId = ref<string | null>(null);
const messages = ref<{ role: "user" | "assistant"; content: string }[]>([]);

const attendees = ref<AttendeeBriefing[]>([{ name: "", company: "" }]);
const goal = ref("");

const followUp = ref("");
const loading = ref(false);
const error = ref("");

const showBriefingForm = computed(() => conversationId.value === null);

function addAttendee() {
  attendees.value.push({ name: "", company: "" });
}

function removeAttendee(i: number) {
  if (attendees.value.length <= 1) return;
  attendees.value.splice(i, 1);
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
  for (const a of attendees.value) {
    const n = a.name.trim();
    if (!n) continue;
    const c = a.company?.trim();
    cleaned.push({ name: n, company: c || null });
  }
  if (cleaned.length === 0) return null;
  const g = goal.value.trim();
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
  const userPreview = briefingPreview(ctx);
  messages.value = [{ role: "user", content: userPreview }];

  let lastState: Record<string, unknown> | null = null;

  try {
    await streamChat(
      { briefing_context: ctx },
      {
        onMeta: (id) => {
          conversationId.value = id;
        },
        onState: (data: Record<string, unknown>) => {
          lastState = data;
        },
        onDone: () => {},
      },
    );

    const assistant = extractAssistantReply(lastState);
    messages.value.push({ role: "assistant", content: assistant });
  } catch (e) {
    messages.value = [];
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
  const cid = conversationId.value;
  const text = followUp.value.trim();
  if (!cid || !text) return;

  error.value = "";
  loading.value = true;
  messages.value.push({ role: "user", content: text });
  followUp.value = "";

  let lastState: Record<string, unknown> | null = null;

  try {
    await streamChat(
      { conversation_id: cid, content: text },
      {
        onState: (data: Record<string, unknown>) => {
          lastState = data;
        },
      },
    );

    const assistant = extractAssistantReply(lastState);
    messages.value.push({ role: "assistant", content: assistant });
  } catch (e) {
    messages.value.pop();
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
  conversationId.value = null;
  messages.value = [];
  attendees.value = [{ name: "", company: "" }];
  goal.value = "";
  followUp.value = "";
  error.value = "";
}

async function logout() {
  await auth.logout();
  router.push({ name: "login" });
}
</script>

<template>
  <div class="flex min-h-screen bg-gray-900 text-white">
    <aside class="w-56 shrink-0 bg-gray-800 border-r border-gray-700 flex flex-col">
      <div class="p-4 border-b border-gray-700">
        <RouterLink to="/dashboard" class="text-gray-400 hover:text-white text-sm">← Dashboard</RouterLink>
        <div class="text-xl font-bold mt-2">Briefing chat</div>
      </div>
      <div class="p-4 mt-auto border-t border-gray-700">
        <button type="button" class="text-gray-400 hover:text-white text-sm w-full text-left" @click="logout">
          Sign out
        </button>
      </div>
    </aside>

    <div class="flex flex-col flex-1 min-h-0">
      <header
        class="shrink-0 flex items-center justify-between gap-4 px-4 py-3 border-b border-gray-700 bg-gray-800"
      >
        <p class="text-sm text-gray-400">
          <template v-if="conversationId">Conversation: {{ conversationId.slice(0, 8) }}…</template>
          <template v-else>New conversation — structured first message</template>
        </p>
        <button
          v-if="conversationId"
          type="button"
          class="text-sm text-blue-400 hover:text-blue-300"
          :disabled="loading"
          @click="newConversation"
        >
          New conversation
        </button>
      </header>

      <div class="flex-1 overflow-y-auto p-4 space-y-4 max-w-3xl mx-auto w-full">
        <div
          v-if="showBriefingForm && messages.length === 0"
          class="bg-gray-800 border border-gray-700 rounded-lg p-6 space-y-4"
        >
          <h2 class="text-lg font-semibold">Who are you meeting, and what do you need?</h2>
          <p class="text-sm text-gray-400">
            Add one or more attendees (name and optional company), then your goal. After the first
            reply you can send free-form follow-ups in the thread.
          </p>

          <div v-for="(row, i) in attendees" :key="i" class="flex flex-wrap gap-2 items-end">
            <div class="flex-1 min-w-[140px]">
              <label class="block text-xs text-gray-400 mb-1">Name</label>
              <input
                v-model="row.name"
                type="text"
                class="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white text-sm"
                placeholder="Full name"
              />
            </div>
            <div class="flex-1 min-w-[140px]">
              <label class="block text-xs text-gray-400 mb-1">Company (optional)</label>
              <input
                v-model="row.company"
                type="text"
                class="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white text-sm"
                placeholder="Company"
              />
            </div>
            <button
              v-if="attendees.length > 1"
              type="button"
              class="text-sm text-red-400 hover:text-red-300 px-2"
              @click="removeAttendee(i)"
            >
              Remove
            </button>
          </div>
          <button
            type="button"
            class="text-sm text-blue-400 hover:text-blue-300"
            @click="addAttendee"
          >
            + Add attendee
          </button>

          <div>
            <label class="block text-xs text-gray-400 mb-1">Goal</label>
            <textarea
              v-model="goal"
              rows="4"
              class="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white text-sm"
              placeholder="What should the briefing help you achieve?"
            />
          </div>

          <p v-if="error" class="text-sm text-red-400">{{ error }}</p>

          <button
            type="button"
            class="w-full py-2 px-4 rounded-md bg-blue-600 hover:bg-blue-700 text-white font-medium disabled:opacity-50"
            :disabled="loading"
            @click="submitBriefing"
          >
            {{ loading ? "Starting…" : "Start briefing" }}
          </button>
        </div>

        <div
          v-for="(m, index) in messages"
          :key="'msg-' + index"
          class="rounded-lg px-4 py-3 text-sm whitespace-pre-wrap"
          :class="m.role === 'user' ? 'bg-gray-800 ml-8 border border-gray-700' : 'bg-gray-800/50 mr-8 border border-gray-600'"
        >
          <div class="text-xs text-gray-500 mb-1">{{ m.role === "user" ? "You" : "Assistant" }}</div>
          {{ m.content }}
        </div>

        <div v-if="!showBriefingForm" class="flex gap-2 items-end">
          <textarea
            v-model="followUp"
            rows="2"
            class="flex-1 px-3 py-2 rounded-md bg-gray-800 border border-gray-600 text-white text-sm"
            placeholder="Follow-up message…"
            :disabled="loading"
            @keydown.enter.exact.prevent="submitFollowUp"
          />
          <button
            type="button"
            class="shrink-0 py-2 px-4 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium disabled:opacity-50"
            :disabled="loading || !followUp.trim()"
            @click="submitFollowUp"
          >
            Send
          </button>
        </div>

        <p v-if="error && !showBriefingForm" class="text-sm text-red-400">{{ error }}</p>
      </div>
    </div>
  </div>
</template>
