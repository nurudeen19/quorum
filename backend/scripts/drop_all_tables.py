"""Drop all ORM-managed tables (destructive)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Drop every table in :attr:`app.models.Base.metadata` after ``--yes``."""
    os.chdir(_BACKEND_ROOT)
    if str(_BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(_BACKEND_ROOT))

    parser = argparse.ArgumentParser(description="Drop all application database tables.")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Required. Refuses to run without this flag.",
    )
    args = parser.parse_args()
    if not args.yes:
        parser.error("Refusing to drop tables without --yes")

    from sqlalchemy import create_engine, pool

    from app.core.database import get_sync_database_url
    from app.models import Base

    url = get_sync_database_url()
    engine = create_engine(url, poolclass=pool.NullPool)
    try:
        Base.metadata.drop_all(engine)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
