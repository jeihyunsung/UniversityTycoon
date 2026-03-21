from fastapi import APIRouter

from app.config import settings


router = APIRouter()


@router.get("/health")
async def health() -> dict:
    status: dict = {"status": "ok", "db": "disabled"}
    if settings.use_db:
        try:
            from sqlalchemy import text

            from app.main import engine_db

            async with engine_db.connect() as conn:
                await conn.execute(text("SELECT 1"))
            status["db"] = "connected"
        except Exception as e:
            status["db"] = f"error: {e}"
    return status
