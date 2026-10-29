import asyncio

from app.database.connection import AsyncSessionLocal
from app.models.hod import HOD
from app.models.line_manager import LineManager
from sqlalchemy import select


async def main():
    async with AsyncSessionLocal() as db:

        print("\nACTIVE HODs - Audience 2")
        result = await db.execute(
            select(HOD).where(HOD.audience_id == 2).order_by(HOD.id)
        )

        for h in result.scalars():
            print(
                f"ID={h.id} | Name={h.name} | "
                f"Email={h.email} | WhatsApp={h.whatsapp_number}"
            )

        print("\nACTIVE LINE MANAGERS - Audience 2")
        result = await db.execute(
            select(LineManager)
            .where(LineManager.audience_id == 2)
            .order_by(LineManager.id)
        )

        for lm in result.scalars():
            print(
                f"ID={lm.id} | Name={lm.name} | "
                f"Email={lm.email} | WhatsApp={lm.whatsapp_number}"
            )


asyncio.run(main())
