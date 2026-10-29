from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class LineManager(Base):
    __tablename__ = "line_managers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    whatsapp_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )

    # --------------------------------------------------
    # DEPARTMENT
    # --------------------------------------------------
    # Kept for legacy/reporting purposes.
    # It is optional because recipients are now routed
    # primarily through Target Audience.
    # --------------------------------------------------

    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"),
        nullable=True,
        index=True
    )

    # --------------------------------------------------
    # TARGET AUDIENCE
    # --------------------------------------------------
    # Connects the Line Manager to the shared
    # target_audiences table.
    # --------------------------------------------------

    audience_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "target_audiences.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )