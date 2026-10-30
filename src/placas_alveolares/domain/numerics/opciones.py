"""Opciones de convergencia de los solvers no lineales."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from placas_alveolares.domain.numerics.errores import ErrorOpcionesInvalidas


class NormaVectorial(StrEnum):
    """Norma utilizada para medir residuos e incrementos."""

    MAXIMO = "maximo"
    EUCLIDEA = "euclidea"


@dataclass(frozen=True, slots=True)
class OpcionesSolver:
    """Opciones comunes de convergencia.

    La convergencia del residuo se comprueba con:

    ``‖F(x)‖ ≤ tolerancia_residuo + tolerancia_residuo_relativa·‖F(x0)‖``

    Attributes:
        tolerancia_residuo: Tolerancia absoluta del residuo.
        tolerancia_residuo_relativa: Tolerancia relativa respecto al residuo
            inicial.
        tolerancia_incremento: Tolerancia relativa del incremento para
            detectar estancamiento.
        max_iteraciones: Número máximo de iteraciones.
        norma: Norma vectorial empleada en los criterios.
    """

    tolerancia_residuo: float = 1e-9
    tolerancia_residuo_relativa: float = 1e-9
    tolerancia_incremento: float = 1e-12
    max_iteraciones: int = 50
    norma: NormaVectorial = NormaVectorial.MAXIMO

    def __post_init__(self) -> None:
        for nombre, valor in (
            ("tolerancia_residuo", self.tolerancia_residuo),
            (
                "tolerancia_residuo_relativa",
                self.tolerancia_residuo_relativa,
            ),
        ):
            if not math.isfinite(valor) or valor < 0.0:
                raise ErrorOpcionesInvalidas(
                    f"{nombre} debe ser un número finito no negativo."
                )
        if (
            self.tolerancia_residuo == 0.0
            and self.tolerancia_residuo_relativa == 0.0
        ):
            raise ErrorOpcionesInvalidas(
                "Debe definirse al menos una tolerancia de residuo positiva."
            )
        if (
            not math.isfinite(self.tolerancia_incremento)
            or self.tolerancia_incremento <= 0.0
        ):
            raise ErrorOpcionesInvalidas(
                "tolerancia_incremento debe ser un número finito positivo."
            )
        if self.max_iteraciones < 1:
            raise ErrorOpcionesInvalidas(
                "max_iteraciones debe ser al menos 1."
            )


@dataclass(frozen=True, slots=True)
class OpcionesNewton(OpcionesSolver):
    """Opciones específicas del método de Newton.

    Attributes:
        paso_diferencias_finitas: Paso absoluto para el Jacobiano numérico.
            Si es ``None``, se usa un paso relativo automático.
    """

    paso_diferencias_finitas: float | None = None

    def __post_init__(self) -> None:
        OpcionesSolver.__post_init__(self)
        if self.paso_diferencias_finitas is not None:
            if (
                not math.isfinite(self.paso_diferencias_finitas)
                or self.paso_diferencias_finitas <= 0.0
            ):
                raise ErrorOpcionesInvalidas(
                    "paso_diferencias_finitas debe ser un número finito "
                    "positivo o None."
                )
