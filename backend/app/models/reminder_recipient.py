from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class ReminderRecipient(Base):
    __tablename__ = "reminder_recipients"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    reminder_config_id: Mapped[int] = mapped_column(
        ForeignKey(
            "reminder_configs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    recipient_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    recipient_id: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    channel: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )