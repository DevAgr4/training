import asyncio
from app.database.connection import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT id, name, email, whatsapp_number, audience_id
                FROM hods
                WHERE id = 7
            """)
        )

        row = result.fetchone()

        print("\nVidhi recipient:")
        print(row)

asyncio.run(main())
