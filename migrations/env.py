"""Entorno de Alembic.

Usa `ajustes.url_basedatos` (pydantic-settings) como fuente de la URL, de
modo que cambiar de SQLite a PostgreSQL solo requiere cambiar el `.env`.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from placas_alveolares.infrastructure.config.settings import obtener_ajustes
from placas_alveolares.infrastructure.persistence.base import BaseDeclarativa

config = context.config
config.set_main_option("sqlalchemy.url", obtener_ajustes().url_basedatos)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = BaseDeclarativa.metadata


def run_migrations_offline() -> None:
    """Ejecuta las migraciones en modo 'offline'."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta las migraciones en modo 'online'."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
