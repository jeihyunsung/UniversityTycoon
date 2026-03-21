from app.models.schemas import SaveState


class InMemorySaveRepository:
    def __init__(self) -> None:
        self._saves: dict[str, SaveState] = {}

    def get(self, user_key: str) -> SaveState | None:
        return self._saves.get(user_key)

    def put(self, user_key: str, save: SaveState) -> SaveState:
        self._saves[user_key] = save
        return save


save_repository = InMemorySaveRepository()
