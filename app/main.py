from __future__ import annotations
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .db import engine
from .models import Base
from .routers.tests import router as tests_router
from .routers.attempts import router as attempts_router

load_dotenv()

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:8081, http://127.0.0.1:8081, exp://*, exp+android://*").split(",")]

app = FastAPI(title="Current Affairs Quiz API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    # Create tables if not present
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(tests_router)
app.include_router(attempts_router)

@app.get("/")
async def root():
    return {"ok": True, "service": "current-affairs-quiz"}
