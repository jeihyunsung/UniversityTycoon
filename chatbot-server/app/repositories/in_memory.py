from app.models.schemas import SaveState
from app.repositories.base import SaveRepository


class InMemorySaveRepository(SaveRepository):
    def __init__(self) -> None:
        self._saves: dict[str, SaveState] = {}

    async def get(self, user_key: str) -> SaveState | None:
        return self._saves.get(user_key)

    async def put(self, user_key: str, save: SaveState) -> SaveState:
        self._saves[user_key] = save
        return save


save_repository: InMemorySaveRepository = InMemorySaveRepository()
