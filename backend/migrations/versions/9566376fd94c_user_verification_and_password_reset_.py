"""user verification and password reset tokens

Revision ID: 9566376fd94c
Revises: 357336ff011c
Create Date: 2026-05-06 16:41:49.568600

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9566376fd94c"
down_revision: Union[str, Sequence[str], None] = "357336ff011c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("verification_token", sa.String(128), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("verification_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("password_reset_token", sa.String(128), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("password_reset_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_users_verification_token",
        "users",
        ["verification_token"],
        unique=True,
    )
    op.create_index(
        "ix_users_password_reset_token",
        "users",
        ["password_reset_token"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_users_password_reset_token", table_name="users")
    op.drop_index("ix_users_verification_token", table_name="users")
    op.drop_column("users", "password_reset_expires_at")
    op.drop_column("users", "password_reset_token")
    op.drop_column("users", "verification_expires_at")
    op.drop_column("users", "verification_token")
