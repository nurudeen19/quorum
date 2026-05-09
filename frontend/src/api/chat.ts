/**
 * Chat stream (SSE) — POST /chat/stream.
 */

import { ApiError, parseDetail } from "@/api/http";

const baseURL = () =>
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "/api/v1";

export interface AttendeeBriefing {
  name: string;
  company?: string | null;
}

export interface BriefingContext {
  attendees: AttendeeBriefing[];
  goal: string;
}

/** New conversation (structured first turn). */
export interface ChatStreamNewConversation {
  briefing_context: BriefingContext;
  conversation_id?: undefined | null;
  content?: undefined | null;
}

/** Continue existing conversation. */
export interface ChatStreamContinue {
  conversation_id: string;
  content: string;
  briefing_context?: undefined | null;
}

export type ChatStreamRequestBody = ChatStreamNewConversation | ChatStreamContinue;

export type ChatStreamMetaEvent = { event: "meta"; conversation_id: string };

export type ChatStreamStateEvent = {
  event: "state";
  data: Record<string, unknown>;
};

export type ChatStreamDoneEvent = { event: "done" };

export type ChatStreamServerEvent = ChatStreamMetaEvent | ChatStreamStateEvent | ChatStreamDoneEvent;

function parseSseDataLine(line: string): unknown {
  const prefix = "data: ";
  if (!line.startsWith(prefix)) return null;
  const raw = line.slice(prefix.length).trim();
  if (!raw) return null;
  try {
    return JSON.parse(raw) as unknown;
  } catch {
    return null;
  }
}

export interface StreamChatHandlers {
  onMeta?: (conversationId: string) => void;
  onState?: (data: Record<string, unknown>) => void;
  onDone?: () => void;
}

/**
 * POST JSON body; read ``text/event-stream`` and invoke handlers per event.
 */
export async function streamChat(
  body: ChatStreamRequestBody,
  handlers: StreamChatHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const headers = new Headers({
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  });
  const access = localStorage.getItem("quorum_access_token");
  if (access) headers.set("Authorization", `Bearer ${access}`);

  const res = await fetch(`${baseURL()}/chat/stream`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
    signal,
  });

  if (!res.ok) {
    const text = await res.text();
    let json: unknown = undefined;
    if (text) {
      try {
        json = JSON.parse(text);
      } catch {
        json = text;
      }
    }
    throw new ApiError(parseDetail(json), res.status, json);
  }

  const reader = res.body?.getReader();
  if (!reader) {
    throw new Error("No response body");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      const trimmed = line.replace(/\r$/, "");
      if (!trimmed || trimmed.startsWith(":")) continue;
      const payload = parseSseDataLine(trimmed);
      if (!payload || typeof payload !== "object") continue;
      const ev = payload as Record<string, unknown>;
      const event = ev.event;
      if (event === "meta" && typeof ev.conversation_id === "string") {
        handlers.onMeta?.(ev.conversation_id);
      } else if (event === "state" && ev.data && typeof ev.data === "object") {
        handlers.onState?.(ev.data as Record<string, unknown>);
      } else if (event === "done") {
        handlers.onDone?.();
      }
    }
  }
}
