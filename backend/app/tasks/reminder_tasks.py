from datetime import datetime

from celery import Task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.core.config import settings
from app.models.reminder import Reminder


# ============================================================
# SYNC DATABASE ENGINE FOR CELERY
# ============================================================

celery_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)


# ============================================================
# CELERY TASK
# ============================================================

@celery_app.task(
    name="app.tasks.reminder_tasks.process_due_reminders"
)
def process_due_reminders():

    now = datetime.now()

    with Session(celery_engine) as db:

        result = db.execute(
            select(Reminder)
            .where(
                Reminder.status == "PENDING",
                Reminder.scheduled_at <= now,
            )
            .order_by(Reminder.scheduled_at)
        )

        reminders = result.scalars().all()

        processed = 0

        for reminder in reminders:

            print(
                f"[REMINDER DUE] "
                f"id={reminder.id} "
                f"type={reminder.reminder_type} "
                f"channel={reminder.channel} "
                f"recipient="
                f"{reminder.recipient_type}:"
                f"{reminder.recipient_id}"
            )

            reminder.status = "PROCESSING"

            processed += 1

        db.commit()

        print(
            f"[REMINDER ENGINE] "
            f"Processed {processed} reminder(s)."
        )

        return {
            "processed": processed,
        }