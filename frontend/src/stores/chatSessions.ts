/**
 * Briefing chat UI state: conversation list and messages from the API.
 */

import { defineStore } from "pinia";
import { ref } from "vue";

import type { AttendeeBriefing } from "@/api/chat";
import * as conversationsApi from "@/api/conversations";
import type { ConversationListItem } from "@/api/conversations";
import { ApiError } from "@/api/http";

export interface ChatMessage {
  id?: string;
  role: "user" | "assistant";
  content: string;
  /** Thumbs rating for assistant messages (from API after load). */
  feedback?: "up" | "down" | null;
}

function defaultDraftAttendees(): AttendeeBriefing[] {
  return [{ name: "", company: "" }];
}

function displayTitle(c: ConversationListItem): string {
  if (c.title && c.title.trim()) return c.title.trim();
  return `Briefing · ${c.id.slice(0, 8)}`;
}

export const useChatSessionsStore = defineStore("chatSessions", () => {
  const remoteList = ref<ConversationListItem[]>([]);
  const listLoading = ref(false);
  const listError = ref<string | null>(null);

  const activeConversationId = ref<string | null>(null);
  const activeMessages = ref<ChatMessage[]>([]);
  const messagesLoading = ref(false);
  const messagesError = ref<string | null>(null);

  const draftAttendees = ref<AttendeeBriefing[]>(defaultDraftAttendees());
  const draftGoal = ref("");

  async function fetchRemoteConversations(): Promise<void> {
    listLoading.value = true;
    listError.value = null;
    try {
      remoteList.value = await conversationsApi.listConversations(100);
    } catch (e) {
      listError.value = e instanceof ApiError ? e.message : "Could not load conversations.";
      remoteList.value = [];
    } finally {
      listLoading.value = false;
    }
  }

  async function loadMessagesForConversation(conversationId: string): Promise<void> {
    messagesLoading.value = true;
    messagesError.value = null;
    activeConversationId.value = conversationId;
    try {
      const res = await conversationsApi.getConversationMessages(conversationId);
      activeConversationId.value = res.conversation_id;
      activeMessages.value = res.messages
        .filter((m) => m.role === "user" || m.role === "assistant")
        .map((m) => ({
          id: m.id,
          role: m.role as "user" | "assistant",
          content: m.content,
          feedback: m.user_feedback ?? null,
        }));
    } catch (e) {
      messagesError.value = e instanceof ApiError ? e.message : "Could not load messages.";
      activeMessages.value = [];
    } finally {
      messagesLoading.value = false;
    }
  }

  async function selectConversation(id: string): Promise<void> {
    messagesError.value = null;
    await loadMessagesForConversation(id);
  }

  function startNewConversation(): void {
    activeConversationId.value = null;
    activeMessages.value = [];
    draftAttendees.value = defaultDraftAttendees();
    draftGoal.value = "";
    messagesError.value = null;
  }

  async function deleteRemoteConversation(id: string): Promise<void> {
    try {
      await conversationsApi.deleteConversation(id);
    } catch (e) {
      throw e instanceof ApiError ? e : new Error("Delete failed");
    }
    if (activeConversationId.value === id) {
      startNewConversation();
    }
    await fetchRemoteConversations();
  }

  /** After creating a thread or sending a message, refresh titles and order. */
  async function refreshAfterTurn(): Promise<void> {
    await fetchRemoteConversations();
    const id = activeConversationId.value;
    if (id) {
      await loadMessagesForConversation(id);
    }
  }

  function resetForLogout(): void {
    remoteList.value = [];
    listError.value = null;
    activeConversationId.value = null;
    activeMessages.value = [];
    messagesError.value = null;
    draftAttendees.value = defaultDraftAttendees();
    draftGoal.value = "";
  }

  return {
    remoteList,
    listLoading,
    listError,
    activeConversationId,
    activeMessages,
    messagesLoading,
    messagesError,
    draftAttendees,
    draftGoal,
    fetchRemoteConversations,
    loadMessagesForConversation,
    selectConversation,
    startNewConversation,
    deleteRemoteConversation,
    refreshAfterTurn,
    resetForLogout,
    displayTitle,
  };
});
