import asyncio
from sqlalchemy import text
from app.database.connection import engine

async def main():
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT current_database(), current_user,
                   inet_server_addr(), inet_server_port()
        """))
        print("CONNECTED DATABASE:", result.fetchone())

        result = await conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'reminders'
            ORDER BY ordinal_position
        """))
        print("REMINDERS TABLE COLUMNS:")
        for row in result.fetchall():
            print(row[0])

    await engine.dispose()

asyncio.run(main())
