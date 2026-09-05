from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class TrainingDocument(Base):
    __tablename__ = "training_documents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    training_id: Mapped[int] = mapped_column(
        ForeignKey("trainings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        nullable=False
    )

    file_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    received_via: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    received_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )