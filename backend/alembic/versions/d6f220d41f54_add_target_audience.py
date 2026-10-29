"""add target audience

Revision ID: d6f220d41f54
Revises: a6a345c48387
Create Date: 2026-09-30 12:29:45.214233

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ---------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------

revision: str = "d6f220d41f54"

down_revision: Union[str, Sequence[str], None] = "a6a345c48387"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


# =========================================================
# UPGRADE
# =========================================================

def upgrade() -> None:
    """
    Create the Target Audience master table and connect
    Training, HOD and Line Manager records to it.
    """

    # -----------------------------------------------------
    # 1. Create target_audiences table
    # -----------------------------------------------------

    op.create_table(
        "target_audiences",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    # -----------------------------------------------------
    # 2. Target Audience indexes
    # -----------------------------------------------------

    op.create_index(
        "ix_target_audiences_id",
        "target_audiences",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_target_audiences_name",
        "target_audiences",
        ["name"],
        unique=True,
    )

    # -----------------------------------------------------
    # 3. Add audience_id to HOD
    # -----------------------------------------------------

    op.add_column(
        "hods",
        sa.Column(
            "audience_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_hods_audience_id",
        "hods",
        ["audience_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_hods_audience_id_target_audiences",
        "hods",
        "target_audiences",
        ["audience_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # -----------------------------------------------------
    # 4. Add audience_id to Line Manager
    # -----------------------------------------------------

    op.add_column(
        "line_managers",
        sa.Column(
            "audience_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_line_managers_audience_id",
        "line_managers",
        ["audience_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_line_managers_audience_id_target_audiences",
        "line_managers",
        "target_audiences",
        ["audience_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # -----------------------------------------------------
    # 5. Add audience_id to Training
    # -----------------------------------------------------

    op.add_column(
        "trainings",
        sa.Column(
            "audience_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_trainings_audience_id",
        "trainings",
        ["audience_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_trainings_audience_id_target_audiences",
        "trainings",
        "target_audiences",
        ["audience_id"],
        ["id"],
        ondelete="SET NULL",
    )


# =========================================================
# DOWNGRADE
# =========================================================

def downgrade() -> None:
    """
    Remove Target Audience relationships and table.
    """

    # -----------------------------------------------------
    # 1. Remove Training relationship
    # -----------------------------------------------------

    op.drop_constraint(
        "fk_trainings_audience_id_target_audiences",
        "trainings",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_trainings_audience_id",
        table_name="trainings",
    )

    op.drop_column(
        "trainings",
        "audience_id",
    )

    # -----------------------------------------------------
    # 2. Remove Line Manager relationship
    # -----------------------------------------------------

    op.drop_constraint(
        "fk_line_managers_audience_id_target_audiences",
        "line_managers",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_line_managers_audience_id",
        table_name="line_managers",
    )

    op.drop_column(
        "line_managers",
        "audience_id",
    )

    # -----------------------------------------------------
    # 3. Remove HOD relationship
    # -----------------------------------------------------

    op.drop_constraint(
        "fk_hods_audience_id_target_audiences",
        "hods",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_hods_audience_id",
        table_name="hods",
    )

    op.drop_column(
        "hods",
        "audience_id",
    )

    # -----------------------------------------------------
    # 4. Remove Target Audience indexes
    # -----------------------------------------------------

    op.drop_index(
        "ix_target_audiences_name",
        table_name="target_audiences",
    )

    op.drop_index(
        "ix_target_audiences_id",
        table_name="target_audiences",
    )

    # -----------------------------------------------------
    # 5. Remove Target Audience table
    # -----------------------------------------------------

    op.drop_table(
        "target_audiences"
    )