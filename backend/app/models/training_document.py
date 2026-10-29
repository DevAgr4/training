from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.database.connection import Base


class TrainingDocument(Base):

    __tablename__ = "training_documents"


    # ========================================================
    # ID
    # ========================================================

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )


    # ========================================================
    # TRAINING
    # ========================================================

    training_id: Mapped[int] = mapped_column(
        ForeignKey(
            "trainings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )


    # ========================================================
    # DOCUMENT TYPE
    # ========================================================

    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )


    # ========================================================
    # STATUS
    # ========================================================

    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        nullable=False,
    )


    # ========================================================
    # FILE
    # ========================================================

    file_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


    # ========================================================
    # RECEIVED VIA
    # ========================================================

    received_via: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )


    # ========================================================
    # RECEIVED AT
    # ========================================================

    received_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )


    # ========================================================
    # REMARKS
    # ========================================================

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


    # ========================================================
    # CREATED
    # ========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )