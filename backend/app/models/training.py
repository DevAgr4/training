from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Training(Base):
    __tablename__ = "trainings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # --------------------------------------------------
    # Basic training information
    # --------------------------------------------------

    training_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    training_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # --------------------------------------------------
    # Legacy / reporting department relationship
    # --------------------------------------------------

    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"),
        nullable=True,
        index=True,
    )

    # --------------------------------------------------
    # Target Audience relationship
    # --------------------------------------------------

    audience_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "target_audiences.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # --------------------------------------------------
    # Training schedule
    # --------------------------------------------------

    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    training_to_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    scheduled_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    duration_hours: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    venue: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # --------------------------------------------------
    # Training status
    # --------------------------------------------------

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="SCHEDULED",
    )

    # --------------------------------------------------
    # Training configuration
    # --------------------------------------------------

    is_department_wise: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    attendance_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    ojt_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # --------------------------------------------------
    # Rescheduling / completion information
    # --------------------------------------------------

    original_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    rescheduled_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    reschedule_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    not_conducted_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # --------------------------------------------------
    # Trainer
    # --------------------------------------------------

    trainer_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # --------------------------------------------------
    # Timestamps
    # --------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )