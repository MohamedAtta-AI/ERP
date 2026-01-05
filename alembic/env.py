from logging.config import fileConfig
import asyncio
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import all models to register them with SQLModel.metadata
# This must import all model classes, not just SQLModel
from sqlmodel import SQLModel
from server.config import config as app_config

# Import all models to ensure they're registered with SQLModel.metadata
from server.db.models import (  # noqa: F401
    Person,
    Attendance,
    Role,
    Location,
    Shift,
    Skill,
    PersonSkill,
    SkillLocationPrice,
    Assignment,
    Document,
    OvertimeRequest,
    SalaryComponent,
    EmployeeComponent,
    PayrollPeriod,
    PayrollRun,
    PayrollRunEmployee,
    PayrollRunLine,
    SalaryAdvance,
    Loan,
    PayrollGroup,
    Payslip,
    AuditLog,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
alembic_config = context.config

# Override sqlalchemy.url with our config
alembic_config.set_main_option("sqlalchemy.url", app_config.DB_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = SQLModel.metadata

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
    url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
