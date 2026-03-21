from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.schemas import SaveState


class SaveRepository(ABC):
    """Abstract async repository for persisting game save states."""

    @abstractmethod
    async def get(self, user_key: str) -> SaveState | None:
        """Retrieve a save state by user key.

        Args:
            user_key: Unique identifier for the player.

        Returns:
            The saved game state, or None if no save exists.
        """

    @abstractmethod
    async def put(self, user_key: str, save: SaveState) -> SaveState:
        """Persist a save state for a user key.

        Args:
            user_key: Unique identifier for the player.
            save: The game state to persist.

        Returns:
            The persisted game state.
        """
