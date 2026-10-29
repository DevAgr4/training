"""fix recipient department nullable

Revision ID: f89cc27ec3c2
Revises: e83938f2ede7
Create Date: 2026-09-30

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f89cc27ec3c2"
down_revision: Union[str, Sequence[str], None] = "e83938f2ede7"
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