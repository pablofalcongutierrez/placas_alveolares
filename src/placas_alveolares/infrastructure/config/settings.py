"""Configuración de la aplicación (runtime).

Lee valores desde variables de entorno (prefijo ``PA_``) y, opcionalmente,
desde un fichero ``.env`` en la raíz del proyecto.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Ajustes(BaseSettings):
    """Ajustes de la aplicación, tipados y validados.

    Los nombres de campo están en español, pero los alias conservan las
    variables de entorno históricas (``PA_DATABASE_URL``, ``PA_LOG_LEVEL`` y
    ``PA_EXPORT_DIR``) para no romper despliegues existentes.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PA_",
        extra="ignore",
    )

    url_basedatos: str = Field(
        default="sqlite:///./placas.db",
        validation_alias="PA_DATABASE_URL",
    )
    nivel_log: str = Field(default="INFO", validation_alias="PA_LOG_LEVEL")
    directorio_export: Path = Field(
        default=Path("./exports"),
        validation_alias="PA_EXPORT_DIR",
    )


@lru_cache
def obtener_ajustes() -> Ajustes:
    """Devuelve una instancia única (cacheada) de :class:`Ajustes`."""
    return Ajustes()
