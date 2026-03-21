from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class GameSaveRow(Base):
    """ORM model representing one player's persisted game state."""

    __tablename__ = "game_saves"

    user_key: Mapped[str] = mapped_column(String(128), primary_key=True)

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    budget: Mapped[int] = mapped_column(Integer, nullable=False)

    reputation_arts: Mapped[int] = mapped_column(Integer, nullable=False)
    reputation_engineering: Mapped[int] = mapped_column(Integer, nullable=False)
    reputation_medical: Mapped[int] = mapped_column(Integer, nullable=False)
    reputation_humanities: Mapped[int] = mapped_column(Integer, nullable=False)

    enrolled_students: Mapped[int] = mapped_column(Integer, nullable=False)
    average_student_level: Mapped[float] = mapped_column(Float, nullable=False)

    admission_policy: Mapped[str] = mapped_column(String(16), nullable=False)

    # Stored as {"math": 5, "science": 5, "english": 5, "korean": 5}
    admission_criteria: Mapped[dict] = mapped_column(
        JSON, nullable=False, default={"math": 5, "science": 5, "english": 5, "korean": 5}
    )

    buildings: Mapped[dict] = mapped_column(JSON, nullable=False)
    departments: Mapped[list] = mapped_column(JSON, nullable=False)
    logs: Mapped[list] = mapped_column(JSON, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
