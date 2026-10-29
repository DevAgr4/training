from app.tasks.reminder_tasks import celery_engine
from sqlalchemy import text

with celery_engine.connect() as conn:
    print("\nHODs:")
    rows = conn.execute(
        text("SELECT id, name, whatsapp_number FROM hods ORDER BY id")
    )

    for row in rows:
        print(row)

    print("\nLine Managers:")
    rows = conn.execute(
        text("SELECT id, name, whatsapp_number FROM line_managers ORDER BY id")
    )

    for row in rows:
        print(row)
