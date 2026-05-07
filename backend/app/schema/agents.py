"""Structured output schemas for agent responses (briefing graph)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Attendee(BaseModel):
    """Someone attending the meeting."""

    name: str = Field(description="Person name as given by the user")
    company: str = Field(description="Organization or affiliation")


class PlannerResponse(BaseModel):
    """Planner output: extracts meeting context and produces an executable research plan."""

    meeting_subject: str = Field(description="Meeting title or subject")
    attendees: list[Attendee] = Field(
        default_factory=list,
        description="People + companies to profile before the meeting",
    )
    briefing_goal: str = Field(
        description=(
            "What the user wants from the briefing (risks, angles, talking points, etc.)"
        ),
    )
    context_notes: str = Field(
        description=(
            "Short inferred context: relationships, seniority, why the meeting matters"
        ),
    )
    plan_steps: list[str] = Field(
        description="Ordered steps the research agent should execute",
    )
    research_queries: list[str] = Field(
        description="Concrete search queries or angles for live web research",
    )
    needs_user_clarification: bool = Field(
        description="True if critical details are missing and the user must answer first",
    )
    clarifying_questions: list[str] = Field(
        default_factory=list,
        description="Questions for the user when needs_user_clarification is True",
    )
    post_review_next_agent: Literal["research", "synthesizer"] | None = Field(
        default=None,
        description=(
            "After a failed review, send the next redo to research (more facts) "
            "or synthesizer (rewrite memo only). Omit on the first planning pass."
        ),
    )
    post_review_rationale: str | None = Field(
        default=None,
        description="Why that redo target was chosen (required when routing after review).",
    )

    @model_validator(mode="after")
    def clarification_consistency(self) -> PlannerResponse:
        if self.needs_user_clarification and not self.clarifying_questions:
            raise ValueError("clarifying_questions required when needs_user_clarification is True")
        return self


class ResearchResponse(BaseModel):
    """Structured output after web research."""

    raw_report: str = Field(
        description=(
            "Compiled evidence: per-person and per-company notes with dates and source cues"
        ),
    )
    source_summary: str = Field(
        description="Primary URLs, outlets, or document titles relied on",
    )
    caveats: str = Field(
        description="Gaps, stale items, uncertain claims, or conflicting sources",
    )


class ReviewerResponse(BaseModel):
    """Quality and safety gate before showing the user the briefing."""

    approved: bool = Field(description="True if the memo is ready for the user")
    issues: str = Field(
        description="Specific failures: accuracy, missing citations, tone, or safety",
    )
    tone_and_safety_ok: bool = Field(
        description="Whether language is professional and appropriate for executives",
    )


class SynthesizerResponse(BaseModel):
    """Final executive briefing memo."""

    memo_title: str = Field(description="Title for the one-page style briefing")
    executive_briefing_markdown: str = Field(
        description=(
            "Polished ~2-minute scan memo in Markdown: exec summary, attendees, "
            "news hooks, risks, suggested talking points"
        ),
    )
    key_takeaways: list[str] = Field(
        default_factory=list,
        description="3–7 bullets the reader should remember walking into the room",
    )
