import { apiFetch } from "./http";

export interface ConversationListItem {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatMessageDto {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  user_feedback?: "up" | "down" | null;
  created_at: string;
}

export interface MessageFeedbackBody {
  feedback: "up" | "down" | null;
}

export interface ConversationMessagesResponse {
  conversation_id: string;
  messages: ChatMessageDto[];
}

export async function listConversations(limit = 50): Promise<ConversationListItem[]> {
  return apiFetch<ConversationListItem[]>(`/chat/conversations?limit=${limit}`);
}

export async function getConversationMessages(
  conversationId: string,
): Promise<ConversationMessagesResponse> {
  return apiFetch<ConversationMessagesResponse>(
    `/chat/conversations/${encodeURIComponent(conversationId)}/messages`,
  );
}

export async function deleteConversation(conversationId: string): Promise<void> {
  await apiFetch<void>(
    `/chat/conversations/${encodeURIComponent(conversationId)}`,
    { method: "DELETE" },
  );
}

export async function patchMessageFeedback(
  messageId: string,
  body: MessageFeedbackBody,
): Promise<ChatMessageDto> {
  return apiFetch<ChatMessageDto>(
    `/chat/messages/${encodeURIComponent(messageId)}/feedback`,
    { method: "PATCH", body: JSON.stringify(body) },
  );
}
