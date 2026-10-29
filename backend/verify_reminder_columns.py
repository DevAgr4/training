import asyncio
from sqlalchemy import text
from app.database.connection import engine

async def main():
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'reminders'
              AND column_name IN ('title', 'custom_message')
            ORDER BY column_name
        """))
        print("Verified columns:", result.fetchall())

    await engine.dispose()

asyncio.run(main())
