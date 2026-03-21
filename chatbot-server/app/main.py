from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes.health import router as health_router
from app.api.routes.kakao import router as kakao_router
from app.config import settings
from app.services.game_engine import GameEngine
from app.services.image_service import KarloImageGenerator, NullImageGenerator

engine_db = None
async_session_factory = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine_db, async_session_factory
    if settings.use_db:
        engine_db = create_async_engine(settings.async_database_url)
        async_session_factory = async_sessionmaker(engine_db, expire_on_commit=False)

    if settings.image_generation_enabled and settings.karlo_api_key:
        image_gen = KarloImageGenerator(settings.karlo_api_key, settings.karlo_timeout)
    else:
        image_gen = NullImageGenerator()

    app.state.game_engine = GameEngine(image_generator=image_gen)

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
