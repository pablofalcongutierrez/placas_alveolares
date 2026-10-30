"""Restricciones de arco para métodos de continuación.

La restricción define la ecuación adicional que convierte el problema
parametrizado ``F(u, λ) = 0`` en un sistema aumentado con solución única
local. Se incluyen las dos variantes habituales:

- esférica: ``‖u − u_previo‖² + ψ²(λ − λ_previo)² = Δs²``
- cilíndrica: ``‖u − u_previo‖² = Δs²``

El radio ``Δs`` se pasa en cada evaluación porque puede adaptarse entre
pasos. La implementación del bucle de arc-length no forma parte de este
módulo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from placas_alveolares.domain.numerics.continuacion.tipos import (
    EstadoContinuacion,
)
from placas_alveolares.domain.numerics.errores import (
    ErrorDimensionesInvalidas,
    ErrorEvaluacionNoFinita,
    ErrorOpcionesInvalidas,
)
from placas_alveolares.domain.numerics.problema import Vector


class RestriccionArco(Protocol):
    """Restricción que define el camino de continuación."""

    def residuo(
        self,
        u: Vector,
        parametro: float,
        estado_previo: EstadoContinuacion,
        radio: float,
    ) -> float:
        """Evalúa el residuo ``c(u, λ)`` de la restricción.

        Args:
            u: Vector de desplazamientos o deformaciones.
            parametro: Factor de carga ``λ``.
            estado_previo: Último estado convergido.
            radio: Radio de arco ``Δs``.

        Returns:
            El residuo escalar de la restricción.
        """
        ...

    def jacobiano(
        self,
        u: Vector,
        parametro: float,
        estado_previo: EstadoContinuacion,
        radio: float,
    ) -> tuple[Vector, float]:
        """Evalúa las derivadas de la restricción.

        Args:
            u: Vector de desplazamientos o deformaciones.
            parametro: Factor de carga ``λ``.
            estado_previo: Último estado convergido.
            radio: Radio de arco ``Δs``.

        Returns:
            La pareja ``(∂c/∂u, ∂c/∂λ)``.
        """
        ...


@dataclass(frozen=True, slots=True)
class ArcoEsferico:
    """Restricción esférica de arc-length.

    Attributes:
        peso_parametro: Peso ``ψ`` que escala la contribución de ``λ`` a la
            longitud de arco. Debe ser positivo.
    """

    peso_parametro: float = 1.0

    def __post_init__(self) -> None:
        if (
            not math.isfinite(self.peso_parametro)
            or self.peso_parametro <= 0.0
        ):
            raise ErrorOpcionesInvalidas(
                "peso_parametro debe ser un número finito positivo."
            )

    def residuo(
        self,
        u: Vector,
        parametro: float,
        estado_previo: EstadoContinuacion,
        radio: float,
    ) -> float:
        """Evalúa la restricción esférica.

        Args:
            u: Vector de desplazamientos o deformaciones.
            parametro: Factor de carga ``λ``.
            estado_previo: Último estado convergido.
            radio: Radio de arco ``Δs``.

        Returns:
            El residuo escalar ``c(u, λ)``.
        """
        _validar_radio(radio)
        desplazamiento = _desplazamiento(u, estado_previo)
        incremento_parametro = parametro - estado_previo.parametro
        return float(
            np.dot(desplazamiento, desplazamiento)
            + self.peso_parametro**2 * incremento_parametro**2
            - radio**2
        )

    def jacobiano(
        self,
        u: Vector,
        parametro: float,
        estado_previo: EstadoContinuacion,
        radio: float,
    ) -> tuple[Vector, float]:
        """Evalúa ``(∂c/∂u, ∂c/∂λ)`` de la restricción esférica.

        Args:
            u: Vector de desplazamientos o deformaciones.
            parametro: Factor de carga ``λ``.
            estado_previo: Último estado convergido.
            radio: Radio de arco ``Δs``.

        Returns:
            La pareja ``(∂c/∂u, ∂c/∂λ)``.
        """
        _validar_radio(radio)
        desplazamiento = _desplazamiento(u, estado_previo)
        incremento_parametro = parametro - estado_previo.parametro
        derivada_u = np.asarray(2.0 * desplazamiento, dtype=np.float64)
        derivada_parametro = (
            2.0 * self.peso_parametro**2 * incremento_parametro
        )
        return derivada_u, float(derivada_parametro)


@dataclass(frozen=True, slots=True)
class ArcoCilindrico:
    """Restricción cilíndrica de arc-length.

    La longitud de arco solo depende de ``u``; ``λ`` no contribuye a la
    restricción.
    """

    def residuo(
        self,
        u: Vector,
        parametro: float,
        estado_previo: EstadoContinuacion,
        radio: float,
    ) -> float:
        """Evalúa la restricción cilíndrica.

        Args:
            u: Vector de desplazamientos o deformaciones.
            parametro: Factor de carga ``λ``; no interviene en la restricción.
            estado_previo: Último estado convergido.
            radio: Radio de arco ``Δs``.

        Returns:
            El residuo escalar ``c(u)``.
        """
        _validar_radio(radio)
        desplazamiento = _desplazamiento(u, estado_previo)
        return float(
            np.dot(desplazamiento, desplazamiento) - radio**2
        )

    def jacobiano(
        self,
        u: Vector,
        parametro: float,
        estado_previo: EstadoContinuacion,
        radio: float,
    ) -> tuple[Vector, float]:
        """Evalúa ``(∂c/∂u, ∂c/∂λ)`` de la restricción cilíndrica.

        Args:
            u: Vector de desplazamientos o deformaciones.
            parametro: Factor de carga ``λ``; no interviene en la restricción.
            estado_previo: Último estado convergido.
            radio: Radio de arco ``Δs``; no interviene en la derivada.

        Returns:
            La pareja ``(∂c/∂u, 0)``.
        """
        _validar_radio(radio)
        desplazamiento = _desplazamiento(u, estado_previo)
        derivada_u = np.asarray(2.0 * desplazamiento, dtype=np.float64)
        return derivada_u, 0.0


def _validar_radio(radio: float) -> None:
    """Valida que el radio de arco sea finito y positivo."""
    if not math.isfinite(radio) or radio <= 0.0:
        raise ErrorOpcionesInvalidas(
            "El radio de arco debe ser un número finito positivo."
        )


def _desplazamiento(
    u: Vector,
    estado_previo: EstadoContinuacion,
) -> Vector:
    """Calcula ``u − u_previo`` y valida dimensiones y finitud."""
    if u.ndim != 1 or u.size == 0:
        raise ErrorDimensionesInvalidas(
            "u debe ser un vector unidimensional no vacío."
        )
    if not np.all(np.isfinite(u)):
        raise ErrorEvaluacionNoFinita("u contiene valores no finitos.")
    u_previo = np.asarray(estado_previo.u, dtype=np.float64)
    if u.shape != u_previo.shape:
        raise ErrorDimensionesInvalidas(
            "u y el estado previo deben tener la misma dimensión."
        )
    return np.asarray(u - u_previo, dtype=np.float64)
