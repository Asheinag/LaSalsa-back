import asyncio
import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.database import Base
from app.models import *  # noqa: F403

env_file = os.environ.get(
    "ENV_FILE", ".env.dev"
)  # например, передаётся через окружение
load_dotenv(dotenv_path=env_file, override=True)

config = context.config
# Load environment variables from the config
section = config.config_ini_section
config.set_section_option(section, "DB_HOST", os.getenv("DB_HOST", ""))
config.set_section_option(section, "DB_PORT", os.getenv("DB_PORT", ""))
config.set_section_option(section, "DB_USER", os.getenv("DB_USER", ""))
config.set_section_option(section, "DB_NAME", os.getenv("DB_NAME", ""))
config.set_section_option(section, "DB_PASS", os.getenv("DB_PASS", ""))
print(
    f"Using DB_HOST: {os.getenv('DB_HOST')}, DB_USER: {os.getenv('DB_USER')}, DB_NAME: {os.getenv('DB_NAME')}, DB_PORT: {os.getenv('DB_PORT')}, DB_PASS: {os.getenv('DB_PASS')}"
)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option(
        "sqlalchemy.url",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
    )
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = config.get_main_option(
        "sqlalchemy.url",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
    )
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
