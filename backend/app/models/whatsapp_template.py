from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class WhatsAppTemplate(Base):
    __tablename__ = "whatsapp_templates"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # ---------------------------------------------------------
    # Template category
    # ---------------------------------------------------------

    template_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="TRAINING_REMINDER",
        index=True,
    )

    # ---------------------------------------------------------
    # Meta WhatsApp template
    # ---------------------------------------------------------

    meta_template_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    language_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="en_US",
    )

    # ---------------------------------------------------------
    # HR editable message / preview
    # ---------------------------------------------------------

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # ---------------------------------------------------------
    # Timestamps
    # ---------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )