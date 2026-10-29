"""add whatsapp template type

Revision ID: a6a345c48387
Revises: d46cb41d55a1
Create Date: 2026-09-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a6a345c48387"
down_revision: Union[str, Sequence[str], None] = "d46cb41d55a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ---------------------------------------------------------
    # Add column temporarily as nullable
    # ---------------------------------------------------------

    op.add_column(
        "whatsapp_templates",
        sa.Column(
            "template_type",
            sa.String(length=50),
            nullable=True,
        ),
    )

    # ---------------------------------------------------------
    # Existing templates become Training Reminder templates
    # ---------------------------------------------------------

    op.execute(
        """
        UPDATE whatsapp_templates
        SET template_type = 'TRAINING_REMINDER'
        WHERE template_type IS NULL
        """
    )

    # ---------------------------------------------------------
    # Make column NOT NULL
    # ---------------------------------------------------------

    op.alter_column(
        "whatsapp_templates",
        "template_type",
        existing_type=sa.String(length=50),
        nullable=False,
    )

    # ---------------------------------------------------------
    # Add index
    # ---------------------------------------------------------

    op.create_index(
        "ix_whatsapp_templates_template_type",
        "whatsapp_templates",
        ["template_type"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        "ix_whatsapp_templates_template_type",
        table_name="whatsapp_templates",
    )

    op.drop_column(
        "whatsapp_templates",
        "template_type",
    )