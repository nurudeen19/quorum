"""Add optional user_feedback on messages (thumbs up/down).

Revision ID: d4e5f6a1b2c3
Revises: b2c3d4e5f6a1
Create Date: 2026-05-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a1b2c3"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("user_feedback", sa.String(length=8), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("messages", "user_feedback")
