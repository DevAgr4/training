from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.hod import HOD
from app.models.reminder import Reminder


engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)


with Session(engine) as db:

    # -----------------------------------------
    # 1. Add temporary WhatsApp number to HOD 1
    # -----------------------------------------

    hod = db.get(HOD, 1)

    if not hod:
        raise ValueError("HOD with ID 1 was not found")

    hod.whatsapp_number = "918299426750"

    print(
        f"HOD updated: {hod.name} | "
        f"WhatsApp={hod.whatsapp_number}"
    )

    # -----------------------------------------
    # 2. Create an immediate WhatsApp reminder
    # -----------------------------------------

    reminder = Reminder(
        training_id=1,
        reminder_type="BEFORE_TRAINING",
        recipient_type="HOD",
        recipient_id=1,
        channel="WHATSAPP",
        scheduled_at=datetime.now(),
        status="PENDING",
    )

    db.add(reminder)

    db.commit()
    db.refresh(reminder)

    print()
    print("======================================")
    print("WHATSAPP REMINDER CREATED")
    print("======================================")
    print(f"Reminder ID : {reminder.id}")
    print(f"Training ID : {reminder.training_id}")
    print(f"Recipient   : {hod.name}")
    print(f"WhatsApp    : {hod.whatsapp_number}")
    print(f"Channel     : {reminder.channel}")
    print(f"Status      : {reminder.status}")
    print(f"Scheduled   : {reminder.scheduled_at}")
    print("======================================")