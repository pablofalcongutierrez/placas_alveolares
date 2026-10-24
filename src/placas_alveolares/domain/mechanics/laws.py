"""Contratos de las leyes constitutivas.

El dominio define la **forma** de las leyes tensión-deformación que los motores
mecánicos reciben por inyección, pero no su contenido: las leyes normativas
viven en ``norms/*/laws.py`` y las físicas genéricas en
``domain/mechanics/generic_laws.py``. El razonamiento está en
``docs/decisions/0001-frontera-mecanica-fisica-vs-normativa.md``.

Convención: deformaciones y tensiones positivas en tracción y negativas en
compresión; deformación adimensional (tanto por uno) y tensión en MPa.
"""

from __future__ import annotations

from typing import Protocol


class LeyTensionDeformacion(Protocol):
    """Ley constitutiva tensión-deformación uniaxial.

    La ley es una función **total**: fuera de su dominio de validez devuelve
    tensión nula porque el material está agotado. Comprobar que la deformación
    no supera el límite último es un criterio de la comprobación normativa, no
    de la ley.
    """

    def tension(self, deformacion: float) -> float:
        """Tensión asociada a una deformación.

        Args:
            deformacion: Deformación longitudinal (tanto por uno).

        Returns:
            La tensión (MPa), positiva en tracción y negativa en compresión.
        """
        ...

    def modulo_tangente(self, deformacion: float) -> float:
        """Pendiente de la ley tensión-deformación.

        Args:
            deformacion: Deformación longitudinal (tanto por uno).

        Returns:
            La pendiente ``dσ/dε`` (MPa) en la deformación dada.
        """
        ...

    @property
    def deformacion_maxima_compresion(self) -> float:
        """Deformación última de compresión (negativa o nula)."""
        ...

    @property
    def deformacion_maxima_traccion(self) -> float:
        """Deformación última de tracción (positiva o nula)."""
        ...
