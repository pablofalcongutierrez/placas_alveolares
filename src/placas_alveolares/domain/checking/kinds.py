"""Vocabulario cerrado de normas y tipos de comprobación.

Los identificadores de norma permiten etiquetar los datos normativos sin que la
capa de aplicación conozca las implementaciones concretas de cada norma.
"""

from __future__ import annotations

from enum import StrEnum


class NormId(StrEnum):
    """Identificadores de las normas soportadas."""

    CE = "ce"
    EC2 = "ec2"
    EN1168 = "en1168"
