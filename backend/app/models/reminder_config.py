from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class ReminderConfig(Base):
    __tablename__ = "reminder_configs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    reminder_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    # Used for reminders such as:
    # 1 day before
    # 2 days before
    # 3 days before
    days_before: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    send_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
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