"""Leyes constitutivas físicas, independientes de cualquier norma.

Permiten analizar y probar los motores mecánicos sin instalar ninguna norma
(véase ``docs/decisions/0001-frontera-mecanica-fisica-vs-normativa.md``). Las
leyes normativas viven en ``norms/*/laws.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LeyElastica:
    """Ley elástica lineal de Hooke: ``σ = E·ε``.

    Attributes:
        modulo_elasticidad: Módulo de elasticidad (MPa).
    """

    modulo_elasticidad: float

    def tension(self, deformacion: float) -> float:
        """Tensión elástica lineal.

        Args:
            deformacion: Deformación longitudinal (tanto por uno).

        Returns:
            La tensión ``E·ε`` (MPa).
        """
        return self.modulo_elasticidad * deformacion

    def modulo_tangente(self, deformacion: float) -> float:
        """Pendiente constante de la ley.

        Args:
            deformacion: Deformación longitudinal (tanto por uno); no influye.

        Returns:
            El módulo de elasticidad (MPa).
        """
        return self.modulo_elasticidad

    @property
    def deformacion_maxima_compresion(self) -> float:
        """La ley elástica no impone límite de compresión."""
        return -math.inf

    @property
    def deformacion_maxima_traccion(self) -> float:
        """La ley elástica no impone límite de tracción."""
        return math.inf


@dataclass(frozen=True, slots=True)
class LeyElastoplastica:
    """Ley elastoplástica perfecta con deformación última.

    Lineal hasta el límite elástico, constante hasta la deformación última y
    nula a partir de ella.

    Attributes:
        modulo_elasticidad: Módulo de elasticidad (MPa).
        limite_elastico: Tensión de plastificación (MPa, valor absoluto).
        deformacion_ultima: Deformación última (tanto por uno, valor absoluto).
    """

    modulo_elasticidad: float
    limite_elastico: float
    deformacion_ultima: float

    def tension(self, deformacion: float) -> float:
        """Tensión elastoplástica perfecta.

        Args:
            deformacion: Deformación longitudinal (tanto por uno).

        Returns:
            La tensión (MPa), positiva en tracción y negativa en compresión.
        """
        if abs(deformacion) > self.deformacion_ultima:
            return 0.0
        deformacion_fluencia = self.limite_elastico / self.modulo_elasticidad
        deformacion_efectiva = max(
            -deformacion_fluencia, min(deformacion_fluencia, deformacion)
        )
        return self.modulo_elasticidad * deformacion_efectiva

    def modulo_tangente(self, deformacion: float) -> float:
        """Pendiente de la ley en la rama correspondiente.

        Args:
            deformacion: Deformación longitudinal (tanto por uno).

        Returns:
            El módulo de elasticidad en la rama lineal y cero en la plástica o
            tras la deformación última (MPa).
        """
        if abs(deformacion) > self.deformacion_ultima:
            return 0.0
        if abs(deformacion) < self.limite_elastico / self.modulo_elasticidad:
            return self.modulo_elasticidad
        return 0.0

    @property
    def deformacion_maxima_compresion(self) -> float:
        """Deformación última de compresión (negativa)."""
        return -self.deformacion_ultima

    @property
    def deformacion_maxima_traccion(self) -> float:
        """Deformación última de tracción (positiva)."""
        return self.deformacion_ultima
