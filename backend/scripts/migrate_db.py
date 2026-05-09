"""Apply Alembic migrations to ``head``."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Run ``alembic upgrade head`` using ``alembic.ini`` next to this package."""
    os.chdir(_BACKEND_ROOT)
    if str(_BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(_BACKEND_ROOT))

    from alembic import command
    from alembic.config import Config

    ini = _BACKEND_ROOT / "alembic.ini"
    if not ini.is_file():
        raise SystemExit(f"Missing Alembic config: {ini}")

    cfg = Config(str(ini))
    command.upgrade(cfg, "head")


if __name__ == "__main__":
    main()
