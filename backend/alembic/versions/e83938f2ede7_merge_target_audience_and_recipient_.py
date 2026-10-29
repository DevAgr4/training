"""merge target audience and recipient department migrations

Revision ID: e83938f2ede7
Revises: 1396dc906f24, ab5ba39edaa2
Create Date: 2026-09-30 13:16:10.418606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e83938f2ede7'
down_revision: Union[str, Sequence[str], None] = ('1396dc906f24', 'ab5ba39edaa2')
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