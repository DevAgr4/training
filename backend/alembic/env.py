from logging.config import fileConfig
import asyncio

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import settings
from app.database.connection import Base

# Import all models that Alembic needs to detect.
# Keep this import even if User is not directly referenced below.
from app.models import (
    User,
    Department,
    HOD,
    LineManager,
    Employee,
    Training,
    TrainingAssignment,
    ReminderConfig,
    ReminderRecipient,
    Reminder,
    TrainingDocument,
)

# ---------------------------------------------------------
# Alembic Config
# ---------------------------------------------------------

config = context.config


# ---------------------------------------------------------
# Database URL
# ---------------------------------------------------------
# Alembic uses ConfigParser internally.
# ConfigParser treats "%" as interpolation syntax.
#
# Example:
# postgres password encoded as @
# %40
#
# Therefore we escape "%" as "%%" before giving the URL
# to Alembic.
# ---------------------------------------------------------

database_url = settings.DATABASE_URL.replace("%", "%%")

config.set_main_option(
    "sqlalchemy.url",
    database_url
)


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ---------------------------------------------------------
# SQLAlchemy Metadata
# ---------------------------------------------------------
# Alembic compares this metadata with the actual database
# and automatically generates migrations.
# ---------------------------------------------------------

target_metadata = Base.metadata


# ---------------------------------------------------------
# OFFLINE MIGRATIONS
# ---------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Run migrations without creating a database connection.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------
# ONLINE MIGRATIONS
# ---------------------------------------------------------

def do_run_migrations(connection: Connection) -> None:
    """
    Configure Alembic using an active database connection.
    """

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Create an async SQLAlchemy engine and run Alembic
    migrations using it.
    """

    connectable = async_engine_from_config(
        config.get_section(
            config.config_ini_section
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:

        await connection.run_sync(
            do_run_migrations
        )

    await connectable.dispose()


# ---------------------------------------------------------
# ONLINE MIGRATION ENTRY POINT
# ---------------------------------------------------------

def run_migrations_online() -> None:
    """
    Run asynchronous migrations.
    """

    asyncio.run(
        run_async_migrations()
    )


# ---------------------------------------------------------
# START MIGRATION
# ---------------------------------------------------------

if context.is_offline_mode():

    run_migrations_offline()

else:

    run_migrations_online()