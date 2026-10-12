"""Base declarativa de SQLAlchemy.

Todos los modelos de persistencia deben heredar de :class:`Base`.
Alembic usa `Base.metadata` como `target_metadata`.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarativa común para los modelos ORM."""
