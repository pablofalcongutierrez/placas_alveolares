"""Configuración de la aplicación (runtime).

Lee valores desde variables de entorno (prefijo ``PA_``) y, opcionalmente,
desde un fichero ``.env`` en la raíz del proyecto.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ajustes de la aplicación, tipados y validados."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PA_",
        extra="ignore",
    )

    database_url: str = "sqlite:///./placas.db"
    log_level: str = "INFO"
    export_dir: Path = Path("./exports")


@lru_cache
def get_settings() -> Settings:
    """Devuelve una instancia única (cacheada) de :class:`Settings`."""
    return Settings()
