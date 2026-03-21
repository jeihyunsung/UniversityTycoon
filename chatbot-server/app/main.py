from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes.health import router as health_router
from app.api.routes.kakao import router as kakao_router
from app.config import settings

engine_db = None
async_session_factory = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine_db, async_session_factory
    if settings.use_db:
        engine_db = create_async_engine(settings.async_database_url)
        async_session_factory = async_sessionmaker(engine_db, expire_on_commit=False)
    yield
    if engine_db:
        await engine_db.dispose()


app = FastAPI(
    title="University Tycoon Chatbot Server",
    version="0.1.0",
    description="Kakao chatbot skill server skeleton for University Tycoon.",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(kakao_router, prefix="/webhooks/kakao", tags=["kakao"])
