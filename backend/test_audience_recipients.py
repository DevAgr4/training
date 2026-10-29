import asyncio

from app.services.reminder_engine import get_active_reminder_recipients
from app.database.connection import AsyncSessionLocal
from app.models.training import Training
from sqlalchemy import select


async def main():
    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(Training).where(Training.id == 138)
        )

        training = result.scalar_one_or_none()

        if not training:
            print("Training 138 not found.")
            return

        print("\nTraining:")
        print("ID:", training.id)
        print("Name:", training.training_name)
        print("Audience ID:", training.audience_id)

        print("\nResolved recipients:")

        recipients = await get_active_reminder_recipients(training, db)

        print("\nRaw recipient objects:")

        for r in recipients:
            print(r)

        print("\nTotal recipients:", len(recipients))


asyncio.run(main())
