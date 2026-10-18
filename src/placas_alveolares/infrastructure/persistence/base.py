"""Base declarativa de SQLAlchemy.

Todos los modelos de persistencia deben heredar de :class:`BaseDeclarativa`.
Alembic usa `BaseDeclarativa.metadata` como `target_metadata`.
"""

from sqlalchemy.orm import DeclarativeBase


class BaseDeclarativa(DeclarativeBase):
    """Base declarativa común para los modelos ORM."""
