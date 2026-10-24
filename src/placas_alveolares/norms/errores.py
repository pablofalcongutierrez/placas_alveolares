"""Errores de la capa de normas.

Cada capa define su propia base heredando de
``placas_alveolares.domain.errores.ErrorDominio`` (ADR 0009).
"""

from __future__ import annotations

from placas_alveolares.domain.errores import ErrorDominio


class ErrorNorma(ErrorDominio):
    """Error de una implementación normativa."""


class CasoFueraDeAlcance(ErrorNorma):
    """El caso planteado queda fuera del alcance de la norma."""
