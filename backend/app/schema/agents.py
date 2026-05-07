"""Structured output schemas for agent responses."""

from pydantic import BaseModel, Field


class PlannerResponse(BaseModel):
    """Structured output for planning."""

    objective: str = Field(description="Goal the user wants to achieve")
    steps: list[str] = Field(description="Ordered steps to execute")


class ResearchResponse(BaseModel):
    """Structured output for research."""

    findings: str = Field(description="Key findings, sources, and caveats")


class ReviewerResponse(BaseModel):
    """Structured output for reviewing work quality."""

    approved: bool = Field(description="Whether the output is acceptable")
    notes: str = Field(description="Feedback and required fixes")


class SynthesizerResponse(BaseModel):
    """Structured output for the final answer."""

    summary: str = Field(description="Final user-facing response")
