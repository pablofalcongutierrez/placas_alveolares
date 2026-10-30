"""Resultados de los solvers no lineales.

Los resultados son inmutables y devuelven tuplas de ``float`` en lugar de
arrays para evitar aliasing. El historial permite reconstruir la traza de
cálculo en capas superiores sin acoplar el solver al sistema de trazas.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IteracionSolver:
    """Estado registrado al final de una iteración.

    Attributes:
        numero: Número de iteración, empezando en 1.
        x: Estado alcanzado al final de la iteración.
        norma_residuo: Norma del residuo en ese estado.
        norma_incremento: Norma del incremento aplicado en la iteración.
    """

    numero: int
    x: tuple[float, ...]
    norma_residuo: float
    norma_incremento: float


@dataclass(frozen=True, slots=True)
class ResultadoSolver:
    """Resultado de un solver de ecuaciones no lineales.

    Attributes:
        x: Solución aproximada.
        iteraciones: Número de iteraciones realizadas. Vale 0 si el punto
            inicial ya satisfacía la tolerancia.
        norma_residuo: Norma del residuo final.
        norma_residuo_inicial: Norma del residuo en el punto inicial.
        historial: Iteraciones realizadas, en orden.
    """

    x: tuple[float, ...]
    iteraciones: int
    norma_residuo: float
    norma_residuo_inicial: float
    historial: tuple[IteracionSolver, ...] = ()
