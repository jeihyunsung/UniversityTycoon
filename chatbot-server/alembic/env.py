from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import application models so Alembic autogenerate can detect schema changes.
from app.models.db_models import Base
from app.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the ORM metadata so autogenerate reflects the current model definitions.
target_metadata = Base.metadata

# Override the sqlalchemy.url with the value from application settings when the
# .ini file still contains the placeholder value. For migrations, Alembic uses a
# synchronous engine, so we strip async driver prefixes (e.g. +asyncpg, +aiosqlite).
_ini_url = config.get_main_option("sqlalchemy.url") or ""
if not _ini_url or _ini_url == "driver://user:pass@localhost/dbname":
    _sync_url = (
        settings.database_url
        .replace("sqlite+aiosqlite://", "sqlite://")
        .replace("postgresql+asyncpg://", "postgresql://")
    )
    config.set_main_option("sqlalchemy.url", _sync_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
