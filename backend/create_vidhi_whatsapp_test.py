import asyncio
from datetime import datetime, timedelta

from app.database.connection import AsyncSessionLocal
from sqlalchemy import text


async def main():
    async with AsyncSessionLocal() as db:

        # Confirm Vidhi is still the intended recipient
        result = await db.execute(
            text("""
                SELECT id, name, whatsapp_number, audience_id
                FROM hods
                WHERE id = 7
            """)
        )

        vidhi = result.fetchone()

        if not vidhi:
            print("ERROR: Vidhi (HOD ID 7) not found.")
            return

        print("Testing recipient:")
        print(vidhi)

        scheduled_at = datetime.now() + timedelta(minutes=1)

        result = await db.execute(
            text("""
                INSERT INTO reminders (
                    training_id,
                    reminder_type,
                    recipient_type,
                    recipient_id,
                    channel,
                    scheduled_at,
                    status,
                    sent_at,
                    failure_reason,
                    created_at,
                    whatsapp_message_id
                )
                VALUES (
                    138,
                    'BEFORE_TRAINING',
                    'HOD',
                    7,
                    'WHATSAPP',
                    :scheduled_at,
                    'PENDING',
                    NULL,
                    NULL,
                    NOW(),
                    NULL
                )
                RETURNING id, training_id, reminder_type,
                          recipient_type, recipient_id,
                          channel, scheduled_at, status
            """),
            {"scheduled_at": scheduled_at}
        )

        reminder = result.fetchone()

        await db.commit()

        print("\nTEST REMINDER CREATED:")
        print(reminder)


asyncio.run(main())
