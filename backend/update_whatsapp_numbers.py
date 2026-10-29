from app.tasks.reminder_tasks import celery_engine
from sqlalchemy import text
from sqlalchemy.orm import Session

db = Session(celery_engine)

queries = [
    """
    UPDATE hods
    SET whatsapp_number =
        CASE
            WHEN whatsapp_number IS NOT NULL
                 AND length(regexp_replace(whatsapp_number, '[^0-9]', '', 'g')) = 10
            THEN '91' || regexp_replace(whatsapp_number, '[^0-9]', '', 'g')
            ELSE whatsapp_number
        END
    """,
    """
    UPDATE line_managers
    SET whatsapp_number =
        CASE
            WHEN whatsapp_number IS NOT NULL
                 AND length(regexp_replace(whatsapp_number, '[^0-9]', '', 'g')) = 10
            THEN '91' || regexp_replace(whatsapp_number, '[^0-9]', '', 'g')
            ELSE whatsapp_number
        END
    """
]

for query in queries:
    db.execute(text(query))

db.commit()

print("WhatsApp numbers updated with country code 91")

db.close()
