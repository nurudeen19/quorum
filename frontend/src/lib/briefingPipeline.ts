/**
 * Map streamed briefing graph state to a short user-facing pipeline label.
 */

export function derivePipelineStage(state: Record<string, unknown> | null): string {
  if (!state) return "Connecting…";

  const st = state["status"];
  if (st === "guardrail_error") return "Validating your message…";
  if (st === "needs_clarification") return "Almost there — need a bit more detail…";

  const po = state["planner_output"];
  const hasPlanner =
    po !== null &&
    po !== undefined &&
    typeof po === "object" &&
    Object.keys(po as object).length > 0;

  if (!hasPlanner) return "Planning your briefing…";

  const ro = state["research_output"];
  let hasResearchBody = false;
  if (ro && typeof ro === "object") {
    const raw = (ro as { raw_report?: unknown }).raw_report;
    hasResearchBody = typeof raw === "string" && raw.trim().length > 0;
  }
  if (!hasResearchBody) return "Researching attendees & companies…";

  const so = state["synthesizer_output"];
  let hasMemo = false;
  if (so && typeof so === "object") {
    const md = (so as { executive_briefing_markdown?: unknown }).executive_briefing_markdown;
    hasMemo = typeof md === "string" && md.trim().length > 0;
  }
  if (!hasMemo) return "Drafting executive memo…";

  if (st === "completed") return "Finishing up…";
  return "Quality review…";
}

/** Best-effort assistant body while SSE state events arrive (before the final reply). */
export function extractStreamingPreview(state: Record<string, unknown> | null): string | null {
  if (!state) return null;

  const final = state["final_user_message"];
  if (typeof final === "string" && final.trim()) return final.trim();

  const validation = state["validation_error"];
  if (typeof validation === "string" && validation.trim()) return validation.trim();

  const synthesizer = state["synthesizer_output"];
  if (synthesizer && typeof synthesizer === "object") {
    const memo = (synthesizer as { executive_briefing_markdown?: unknown })
      .executive_briefing_markdown;
    if (typeof memo === "string" && memo.trim()) return memo.trim();
  }

  return null;
}
