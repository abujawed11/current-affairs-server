# clear_db.py
import asyncio
from app.db import engine
from app.models import Base

async def clear_all():
    try:
        async with engine.begin() as conn:
            # Drop and recreate all tables
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        print("✅ All tables cleared and recreated!")
    finally:
        # ✨ ensure pool/transport is closed before loop shuts down
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(clear_all())
