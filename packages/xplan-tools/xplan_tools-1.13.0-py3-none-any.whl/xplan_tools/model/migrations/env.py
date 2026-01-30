from alembic import context
from sqlalchemy import engine_from_config, pool

from xplan_tools.model.orm import Base
from xplan_tools.settings import get_settings

config = context.config

target_metadata = Base.metadata

settings = get_settings()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        dialect_name=context.get_x_argument(as_dictionary=True).get(
            "dialect", "postgresql"
        ),
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
    cfg_section = config.get_section(config.config_ini_section, {}) or {}
    x_args = context.get_x_argument(as_dictionary=True)
    if "sqlalchemy.url" in x_args:
        cfg_section["sqlalchemy.url"] = x_args["sqlalchemy.url"]
    elif "url" in x_args:
        cfg_section["sqlalchemy.url"] = x_args["url"]

    connectable = engine_from_config(
        cfg_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=settings.db_schema,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
