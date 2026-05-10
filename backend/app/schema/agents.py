"""Structured output schemas for agent responses (briefing graph)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Attendee(BaseModel):
    """Someone attending the meeting."""

    name: str = Field(description="Person name as given by the user")
    company: str = Field(
        description=(
            "Organization or affiliation for this person—use this to disambiguate from unrelated "
            "people with the same name"
        ),
    )


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
            "Short inferred context: relationships, seniority, why the meeting matters, and how "
            "each attendee is disambiguated from same-name ambiguity (role, geography, team, "
            "known email/URL fragment if provided)"
        ),
    )
    plan_steps: list[str] = Field(
        description=(
            "Ordered steps the research agent must execute; explicitly require scoping each "
            "person to the stated company/role/context and excluding unrelated homonyms"
        ),
    )
    research_queries: list[str] = Field(
        description=(
            "Concrete search queries that include disambiguation tokens (company, title, location, "
            "product, etc.)—never bare names alone when ambiguity is plausible"
        ),
    )
    needs_user_clarification: bool = Field(
        description="True if critical details are missing and the user must answer first",
    )
    clarifying_questions: list[str] = Field(
        default_factory=list,
        description=(
            "Specific questions when identity or scope is unclear (e.g. employer, role, city, "
            "LinkedIn URL, spelling)—required when needs_user_clarification is True"
        ),
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
            "Evidence scoped to planner attendees and companies: per-person sections with dated "
            "facts; each block should tie claims to identifiable context (employer, role, region). "
            "Include inline source cues (URL or outlet + headline) next to material claims"
        ),
    )
    source_summary: str = Field(
        description=(
            "Primary URLs, outlets, or document titles relied on—enough that a reader can verify "
            "provenance"
        ),
    )
    caveats: str = Field(
        description=(
            "Gaps, stale items, uncertain or conflicting sources, low confidence matches, and any "
            "same-name material deliberately excluded as likely the wrong person"
        ),
    )


class ReviewerResponse(BaseModel):
    """Quality and safety gate before showing the user the briefing."""

    approved: bool = Field(
        description=(
            "True only if the memo is accurate, on-scope vs the planner, properly sourced, and "
            "executive-ready"
        ),
    )
    issues: str = Field(
        description=(
            "If not approved: concrete failures (wrong or unverifiable claims, missing citations, "
            "off-scope or homonym content, tone/safety). If approved: brief confirmation or 'none'"
        ),
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
            "news hooks, risks, suggested talking points. Use inline reference markers [1], [2] "
            "for material facts where sources exist; omit markers only for purely structural text"
        ),
    )
    key_takeaways: list[str] = Field(
        default_factory=list,
        description="3–7 bullets the reader should remember walking into the room",
    )
    formatted_source_references: list[str] = Field(
        default_factory=list,
        description=(
            "Numbered or labeled lines matching inline memo markers, e.g. "
            "'[1] https://… — Outlet (date): headline' or '[1] Company press release (date): title'"
        ),
    )
