/**
 * Briefing conversation labels for the sidebar list.
 */

import type { AttendeeBriefing, BriefingContext } from "@/api/chat";
import type { ConversationListItem } from "@/api/conversations";

const GENERIC_TITLE_PREFIXES = ["attendees:", "briefing ·"];

function formatBriefingDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    }).format(new Date(iso));
  } catch {
    return "";
  }
}

function firstName(name: string): string {
  const trimmed = name.trim();
  if (!trimmed) return "Briefing";
  return trimmed.split(/\s+/)[0] ?? "Briefing";
}

/** Match backend ``briefing_conversation_title`` for optimistic list labels. */
export function formatBriefingConversationTitle(
  ctx: BriefingContext,
  at: Date = new Date(),
): string {
  const attendee = ctx.attendees[0];
  if (!attendee) return "Briefing";
  const company = attendee.company?.trim();
  const label = company || firstName(attendee.name);
  const dateLabel = new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(at);
  return `${label} · ${dateLabel}`;
}

export function formatBriefingConversationTitleFromAttendees(
  attendees: AttendeeBriefing[],
  at: Date = new Date(),
): string | null {
  const cleaned = attendees
    .map((a) => ({
      name: a.name.trim(),
      company: a.company?.trim() || null,
    }))
    .filter((a) => a.name);
  if (cleaned.length === 0) return null;
  return formatBriefingConversationTitle({ attendees: cleaned, goal: "" }, at);
}

function isGenericStoredTitle(title: string): boolean {
  const normalized = title.trim().toLowerCase();
  return GENERIC_TITLE_PREFIXES.some((prefix) => normalized.startsWith(prefix));
}

export function displayConversationTitle(c: ConversationListItem): string {
  const stored = c.title?.trim();
  if (stored && !isGenericStoredTitle(stored)) return stored;
  const dateLabel = formatBriefingDate(c.created_at);
  if (dateLabel) return `Briefing · ${dateLabel}`;
  return `Briefing · ${c.id.slice(0, 8)}`;
}
