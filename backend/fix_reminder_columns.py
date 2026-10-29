import asyncio
from sqlalchemy import text
from app.database.connection import engine

async def main():
    async with engine.begin() as conn:
        await conn.execute(text("""
            ALTER TABLE public.reminders
            ADD COLUMN IF NOT EXISTS title VARCHAR(255)
        """))
        await conn.execute(text("""
            ALTER TABLE public.reminders
            ADD COLUMN IF NOT EXISTS custom_message TEXT
        """))

    print("Migration completed successfully.")
    await engine.dispose()

asyncio.run(main())
