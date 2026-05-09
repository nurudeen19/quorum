"""Single-line stdout messages during bootstrap (no structured log clutter)."""

from __future__ import annotations


def _title(module: str) -> str:
    """Human-readable label (e.g. ``briefing graph`` → ``Briefing graph``)."""
    return module.strip().title()


def starting(module: str) -> None:
    """Announce that a subsystem is starting."""
    print(f"Starting {_title(module)}...", flush=True)


def initialized(module: str) -> None:
    """Announce successful subsystem startup."""
    print(f"{_title(module)} initialized", flush=True)


def skipped(module: str, reason: str) -> None:
    """One line when a subsystem is intentionally not started."""
    r = reason.strip()
    suffix = f" — {r}" if r else ""
    print(f"{_title(module)} skipped{suffix}", flush=True)


def failed(module: str, detail: str = "") -> None:
    """Announce failure; keep ``detail`` short."""
    line = f"{_title(module)} failed"
    if detail.strip():
        line = f"{line} — {detail.strip()}"
    print(line, flush=True)
