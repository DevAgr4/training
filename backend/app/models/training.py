from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Training(Base):
    __tablename__ = "trainings"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    training_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    training_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"),
        nullable=False,
        index=True
    )

    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )

    scheduled_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="SCHEDULED",
        nullable=False,
        index=True
    )

    is_department_wise: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    attendance_required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    ojt_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Original date is retained when training is rescheduled.
    original_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    rescheduled_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    reschedule_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    not_conducted_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    trainer_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )