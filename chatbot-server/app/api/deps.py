from collections.abc import AsyncGenerator

from fastapi import Request

from app.config import settings
from app.repositories.base import SaveRepository
from app.repositories.in_memory import save_repository as in_memory_repo
from app.services.game_engine import GameEngine


def get_game_engine(request: Request) -> GameEngine:
    """Return the GameEngine instance stored in app state.

    The engine is created once during lifespan startup with the
    appropriate ImageGenerator wired in.
    """
    return request.app.state.game_engine


async def get_repository() -> AsyncGenerator[SaveRepository, None]:
    """Yield the appropriate SaveRepository for the current configuration.

    Uses the in-memory repository when DB is disabled, otherwise yields a
    per-request PostgresSaveRepository backed by an async SQLAlchemy session.
    """
    if not settings.use_db:
        yield in_memory_repo
        return

    from app.main import async_session_factory
    from app.repositories.postgres import PostgresSaveRepository

    async with async_session_factory() as session:
        yield PostgresSaveRepository(session)
