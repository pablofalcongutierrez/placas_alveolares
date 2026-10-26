"""Errores de la capa de aplicación.

Cada capa define su propia base heredando de
``placas_alveolares.domain.errores.ErrorDominio`` (ADR 0009).
"""

from __future__ import annotations

from placas_alveolares.domain.errores import ErrorDominio


class ErrorAplicacion(ErrorDominio):
    """Error de un caso de uso o de un servicio de aplicación."""


class EntradaProtegida(ErrorAplicacion):
    """Intento de modificar o eliminar una entrada normativa del catálogo."""


class EntradaCatalogoInvalida(ErrorAplicacion):
    """Entrada de catálogo con un nombre o metadatos incoherentes."""


class EntradaDuplicada(ErrorAplicacion):
    """Preset normativo registrado más de una vez con la misma clave."""
