from collections.abc import AsyncGenerator

from app.config import settings
from app.repositories.base import SaveRepository
from app.repositories.in_memory import save_repository as in_memory_repo


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
