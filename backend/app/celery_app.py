from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "training_reminder",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.reminder_tasks",
    ],
)


celery_app.conf.update(
    timezone="Asia/Kolkata",
    enable_utc=False,

    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    task_track_started=True,

    beat_schedule={
        "process-due-reminders-every-minute": {
            "task": "app.tasks.reminder_tasks.process_due_reminders",
            "schedule": 60.0,
        },
    },
)