import asyncio
from app.db import engine
from app.models import Base

async def clear_all():
    async with engine.begin() as conn:
          # Drop all tables and recreate them
          await conn.run_sync(Base.metadata.drop_all)
          await conn.run_sync(Base.metadata.create_all)
    print("✅ All tables cleared and recreated!")

if __name__ == "__main__":
      asyncio.run(clear_all())