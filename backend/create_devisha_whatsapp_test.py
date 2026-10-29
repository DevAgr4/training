import asyncio
from datetime import datetime, timedelta

from app.database.connection import AsyncSessionLocal
from sqlalchemy import text


async def main():
    async with AsyncSessionLocal() as db:

        result = await db.execute(text("""
            SELECT id, name, whatsapp_number, audience_id
            FROM line_managers
            WHERE id = 4
        """))

        recipient = result.fetchone()

        if not recipient:
            print("ERROR: Devisha Agrawal (LINE_MANAGER ID 4) not found.")
            return

        print("Testing recipient:")
        print(recipient)

        scheduled_at = datetime.now() + timedelta(minutes=1)

        result = await db.execute(text("""
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
                'LINE_MANAGER',
                4,
                'WHATSAPP',
                :scheduled_at,
                'PENDING',
                NULL,
                NULL,
                NOW(),
                NULL
            )
            RETURNING
                id,
                training_id,
                reminder_type,
                recipient_type,
                recipient_id,
                channel,
                scheduled_at,
                status
        """), {
            "scheduled_at": scheduled_at
        })

        reminder = result.fetchone()

        await db.commit()

        print("\nTEST REMINDER CREATED:")
        print(reminder)


asyncio.run(main())