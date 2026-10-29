"""make recipient department nullable

Revision ID: ab5ba39edaa2
Revises: d6f220d41f54
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ab5ba39edaa2"
down_revision: Union[str, Sequence[str], None] = "d6f220d41f54"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "hods",
        "department_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    op.alter_column(
        "line_managers",
        "department_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "line_managers",
        "department_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "hods",
        "department_id",
        existing_type=sa.Integer(),
        nullable=False,
    )