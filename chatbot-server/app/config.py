from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    use_db: bool = False
    openai_api_key: str = ""
    image_generation_enabled: bool = True
    image_timeout: int = 30
    model_config = {"env_prefix": "UT_", "env_file": ".env"}

    @property
    def async_database_url(self) -> str:
        """Return an async-compatible database URL.

        Converts a plain postgresql:// URL to the asyncpg driver scheme.
        """
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
