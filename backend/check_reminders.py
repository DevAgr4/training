from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.reminder import Reminder

engine = create_engine(settings.SYNC_DATABASE_URL)

with Session(engine) as db:
    reminders = db.execute(
        select(Reminder).order_by(Reminder.id)
    ).scalars().all()

    print("\n========== REMINDERS ==========")

    for r in reminders:
        print(
            f"ID={r.id} | "
            f"status={r.status} | "
            f"channel={r.channel} | "
            f"scheduled={r.scheduled_at} | "
            f"recipient={r.recipient_type}:{r.recipient_id} | "
            f"failure={r.failure_reason}"
        )

    print("===============================\n")