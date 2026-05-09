"""Export the executive briefing LangGraph structure (Mermaid, optional PNG)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Write Mermaid (and optionally PNG) for the briefing workflow graph."""
    os.chdir(_BACKEND_ROOT)
    if str(_BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(_BACKEND_ROOT))

    parser = argparse.ArgumentParser(
        description="Generate Mermaid (and optional PNG) for the briefing LangGraph.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="-",
        metavar="PATH",
        help="Mermaid output path, or '-' for stdout (default: -).",
    )
    parser.add_argument(
        "--png",
        metavar="PATH",
        default=None,
        help="If set, also write a PNG diagram (needs Graphviz installed).",
    )
    args = parser.parse_args()

    from app.graph.briefing_graph import build_briefing_graph_for_diagram

    compiled = build_briefing_graph_for_diagram()
    graph = compiled.get_graph()
    mermaid = graph.draw_mermaid()

    if args.output == "-":
        print(mermaid)
    else:
        Path(args.output).write_text(mermaid, encoding="utf-8")

    if args.png:
        try:
            png_bytes = graph.draw_mermaid_png()
        except Exception as exc:  # noqa: BLE001 — surface graphviz / pillow issues
            raise SystemExit(f"PNG export failed: {exc}") from exc
        Path(args.png).write_bytes(png_bytes)


if __name__ == "__main__":
    main()
