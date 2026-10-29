import asyncio
from app.database.connection import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT
                    column_name,
                    data_type,
                    is_nullable
                FROM information_schema.columns
                WHERE table_name = 'reminders'
                ORDER BY ordinal_position
            """)
        )

        print("\nREMINDERS TABLE:")
        for row in result:
            print(row)

asyncio.run(main())
