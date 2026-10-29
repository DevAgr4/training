from app.tasks.reminder_tasks import celery_engine
from sqlalchemy import text

with celery_engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT
            'HOD' AS recipient_type,
            id,
            name,
            email,
            whatsapp_number,
            audience_id
        FROM hods
        WHERE audience_id = 2

        UNION ALL

        SELECT
            'LINE_MANAGER' AS recipient_type,
            id,
            name,
            email,
            whatsapp_number,
            audience_id
        FROM line_managers
        WHERE audience_id = 2

        ORDER BY recipient_type, id
    """))

    print("\nRecipients assigned to Audience ID 2:\n")

    for row in rows:
        print(row)
