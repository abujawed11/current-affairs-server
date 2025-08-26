from __future__ import annotations
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  # e.g. mysql+aiomysql://user:pass@127.0.0.1:3306/ca_quiz?charset=utf8mb4
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set. See .env.example")

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
