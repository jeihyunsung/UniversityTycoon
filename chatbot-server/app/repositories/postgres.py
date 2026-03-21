from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import GameSaveRow
from app.models.schemas import (
    AdmissionCriteria,
    BuildingState,
    ReputationState,
    SaveState,
    StudentState,
)
from app.repositories.base import SaveRepository


class PostgresSaveRepository(SaveRepository):
    """Async SQLAlchemy-backed repository for PostgreSQL (or any async engine)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_key: str) -> SaveState | None:
        """Fetch a save row and deserialize it into a SaveState.

        Args:
            user_key: Unique identifier for the player.

        Returns:
            A SaveState instance, or None if no row exists.
        """
        result = await self._session.execute(
            select(GameSaveRow).where(GameSaveRow.user_key == user_key)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._row_to_state(row)

    async def put(self, user_key: str, save: SaveState) -> SaveState:
        """Upsert a save state into the database.

        Args:
            user_key: Unique identifier for the player.
            save: The game state to persist.

        Returns:
            The persisted game state.
        """
        result = await self._session.execute(
            select(GameSaveRow).where(GameSaveRow.user_key == user_key)
        )
        row = result.scalar_one_or_none()

        criteria_dict = save.admission_criteria.model_dump()

        if row is None:
            row = GameSaveRow(user_key=user_key)
            self._session.add(row)

        row.year = save.year
        row.month = save.month
        row.budget = save.budget
        row.reputation_arts = save.reputation.arts
        row.reputation_engineering = save.reputation.engineering
        row.reputation_medical = save.reputation.medical
        row.reputation_humanities = save.reputation.humanities
        row.enrolled_students = save.students.enrolled
        row.average_student_level = save.students.average_level
        row.admission_policy = save.admission_policy
        row.admission_criteria = criteria_dict
        row.buildings = save.buildings.model_dump()
        row.departments = list(save.departments)
        row.logs = list(save.logs)
        row.pending_event = save.pending_event
        row.bonus_freshmen = save.bonus_freshmen
        row.updated_at = datetime.now(tz=timezone.utc)

        await self._session.flush()
        return save

    @staticmethod
    def _row_to_state(row: GameSaveRow) -> SaveState:
        """Convert a GameSaveRow ORM object to a SaveState Pydantic model.

        Args:
            row: The ORM row to convert.

        Returns:
            A fully populated SaveState.
        """
        criteria_data = row.admission_criteria or {"math": 5, "science": 5, "english": 5, "korean": 5}

        return SaveState.model_validate(
            {
                "userId": row.user_key,
                "year": row.year,
                "month": row.month,
                "budget": row.budget,
                "reputation": {
                    "arts": row.reputation_arts,
                    "engineering": row.reputation_engineering,
                    "medical": row.reputation_medical,
                    "humanities": row.reputation_humanities,
                },
                "students": {
                    "enrolled": row.enrolled_students,
                    "averageLevel": row.average_student_level,
                },
                "admissionPolicy": row.admission_policy,
                "admissionCriteria": criteria_data,
                "buildings": row.buildings,
                "departments": row.departments,
                "logs": row.logs,
                "pendingEvent": row.pending_event,
                "bonusFreshmen": row.bonus_freshmen,
            }
        )
