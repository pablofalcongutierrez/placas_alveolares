"""Método de Newton para sistemas de ecuaciones no lineales.

El bucle es deliberadamente independiente de la física y de las normas. La
resolución del sistema lineal se delega en ``numpy.linalg.solve``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np

from placas_alveolares.domain.numerics.base import SolverNoLineal
from placas_alveolares.domain.numerics.diferencias_finitas import (
    jacobiano_por_diferencias_finitas,
)
from placas_alveolares.domain.numerics.errores import (
    ErrorDimensionesInvalidas,
    ErrorEvaluacionNoFinita,
    ErrorJacobianoSingular,
    ErrorNoConvergencia,
)
from placas_alveolares.domain.numerics.opciones import (
    NormaVectorial,
    OpcionesNewton,
    OpcionesSolver,
)
from placas_alveolares.domain.numerics.problema import (
    Matriz,
    ProblemaNoLineal,
    Vector,
)
from placas_alveolares.domain.numerics.resultado import (
    IteracionSolver,
    ResultadoSolver,
)


@dataclass(frozen=True, slots=True)
class Newton(SolverNoLineal):
    """Método de Newton-Raphson para ``F(x) = 0``.

    En cada iteración resuelve ``J(x)·Δx = −F(x)`` y actualiza
    ``x ← x + Δx``. Si el problema no aporta Jacobiano, lo aproxima por
    diferencias finitas.

    Attributes:
        opciones: Tolerancias, máximo de iteraciones, norma y paso de
            diferencias finitas.
    """

    opciones: OpcionesNewton = field(default_factory=OpcionesNewton)

    def resolver(
        self,
        problema: ProblemaNoLineal,
        x0: Sequence[float],
    ) -> ResultadoSolver:
        """Resuelve el sistema no lineal desde ``x0``.

        Args:
            problema: Sistema ``F(x) = 0``.
            x0: Punto inicial.

        Returns:
            El resultado con la solución y el historial de iteraciones.

        Raises:
            ErrorNoConvergencia: Si se agotan las iteraciones o el incremento
                se estanca sin reducir el residuo.
            ErrorJacobianoSingular: Si el Jacobiano es singular.
            ErrorDimensionesInvalidas: Si las dimensiones no son coherentes.
            ErrorEvaluacionNoFinita: Si aparecen NaN o infinitos.
        """
        x = _vector_inicial(x0)
        dimension = int(x.size)
        f = _evaluar_residuo(problema, x, dimension)
        norma_inicial = _norma(f, self.opciones.norma)

        if _converge_residuo(norma_inicial, norma_inicial, self.opciones):
            return _resultado(
                x=x,
                iteraciones=0,
                norma_residuo=norma_inicial,
                norma_residuo_inicial=norma_inicial,
                historial=(),
            )

        historial: list[IteracionSolver] = []
        norma_residuo = norma_inicial
        for numero in range(1, self.opciones.max_iteraciones + 1):
            jacobiano = _evaluar_jacobiano(problema, x, f, self.opciones)
            try:
                incremento = np.asarray(
                    np.linalg.solve(jacobiano, -f),
                    dtype=np.float64,
                )
            except np.linalg.LinAlgError as exc:
                raise ErrorJacobianoSingular(
                    iteracion=numero,
                    x=_tupla(x),
                    detalle=str(exc),
                ) from exc

            if not np.all(np.isfinite(incremento)):
                raise ErrorJacobianoSingular(
                    iteracion=numero,
                    x=_tupla(x),
                    detalle=(
                        "El sistema lineal devolvió un incremento no finito."
                    ),
                )

            norma_incremento = _norma(incremento, self.opciones.norma)
            x = x + incremento
            f = _evaluar_residuo(problema, x, dimension)
            norma_residuo = _norma(f, self.opciones.norma)
            historial.append(
                IteracionSolver(
                    numero=numero,
                    x=_tupla(x),
                    norma_residuo=norma_residuo,
                    norma_incremento=norma_incremento,
                )
            )

            if _converge_residuo(
                norma_residuo,
                norma_inicial,
                self.opciones,
            ):
                return _resultado(
                    x=x,
                    iteraciones=numero,
                    norma_residuo=norma_residuo,
                    norma_residuo_inicial=norma_inicial,
                    historial=tuple(historial),
                )

            if _estancado(x, norma_incremento, self.opciones):
                resultado = _resultado(
                    x=x,
                    iteraciones=numero,
                    norma_residuo=norma_residuo,
                    norma_residuo_inicial=norma_inicial,
                    historial=tuple(historial),
                )
                raise ErrorNoConvergencia(
                    resultado,
                    "El incremento es despreciable y el residuo no alcanza "
                    "la tolerancia.",
                )

        resultado = _resultado(
            x=x,
            iteraciones=self.opciones.max_iteraciones,
            norma_residuo=norma_residuo,
            norma_residuo_inicial=norma_inicial,
            historial=tuple(historial),
        )
        raise ErrorNoConvergencia(
            resultado,
            f"No se alcanzó la tolerancia en "
            f"{self.opciones.max_iteraciones} iteraciones.",
        )


def _vector_inicial(x0: Sequence[float]) -> Vector:
    """Convierte y valida el punto inicial."""
    vector = np.asarray(x0, dtype=np.float64)
    if vector.ndim != 1 or vector.size == 0:
        raise ErrorDimensionesInvalidas(
            "x0 debe ser un vector unidimensional no vacío."
        )
    if not np.all(np.isfinite(vector)):
        raise ErrorEvaluacionNoFinita("x0 contiene valores no finitos.")
    return vector


def _evaluar_residuo(
    problema: ProblemaNoLineal,
    x: Vector,
    dimension: int,
) -> Vector:
    """Evalúa y valida el residuo."""
    residuo = np.asarray(problema.residuo(x), dtype=np.float64)
    if residuo.shape != (dimension,):
        raise ErrorDimensionesInvalidas(
            "El residuo debe devolver un vector de dimensión "
            f"{dimension}; se obtuvo {residuo.shape}."
        )
    if not np.all(np.isfinite(residuo)):
        raise ErrorEvaluacionNoFinita("El residuo contiene valores no finitos.")
    return residuo


def _evaluar_jacobiano(
    problema: ProblemaNoLineal,
    x: Vector,
    f: Vector,
    opciones: OpcionesNewton,
) -> Matriz:
    """Evalúa el Jacobiano analítico o lo aproxima por diferencias finitas."""
    if problema.jacobiano is None:
        jacobiano = jacobiano_por_diferencias_finitas(
            problema.residuo,
            x,
            f,
            paso=opciones.paso_diferencias_finitas,
        )
    else:
        jacobiano = np.asarray(problema.jacobiano(x), dtype=np.float64)

    dimension = int(x.size)
    if jacobiano.shape != (dimension, dimension):
        raise ErrorDimensionesInvalidas(
            "El Jacobiano debe ser una matriz cuadrada de dimensión "
            f"{dimension}; se obtuvo {jacobiano.shape}."
        )
    if not np.all(np.isfinite(jacobiano)):
        raise ErrorEvaluacionNoFinita(
            "El Jacobiano contiene valores no finitos."
        )
    return jacobiano


def _norma(vector: Vector, norma: NormaVectorial) -> float:
    """Calcula la norma configurada de un vector."""
    if norma is NormaVectorial.EUCLIDEA:
        return float(np.linalg.norm(vector))
    return float(np.max(np.abs(vector)))


def _converge_residuo(
    norma_residuo: float,
    norma_inicial: float,
    opciones: OpcionesSolver,
) -> bool:
    """Comprueba el criterio absoluto y relativo del residuo."""
    return norma_residuo <= (
        opciones.tolerancia_residuo
        + opciones.tolerancia_residuo_relativa * norma_inicial
    )


def _estancado(
    x: Vector,
    norma_incremento: float,
    opciones: OpcionesSolver,
) -> bool:
    """Detecta un incremento despreciable respecto al estado actual."""
    escala = max(1.0, _norma(x, opciones.norma))
    return norma_incremento <= opciones.tolerancia_incremento * escala


def _tupla(vector: Vector) -> tuple[float, ...]:
    """Convierte un vector en una tupla inmutable de ``float``."""
    return tuple(float(valor) for valor in vector)


def _resultado(
    *,
    x: Vector,
    iteraciones: int,
    norma_residuo: float,
    norma_residuo_inicial: float,
    historial: tuple[IteracionSolver, ...],
) -> ResultadoSolver:
    """Construye un resultado inmutable."""
    return ResultadoSolver(
        x=_tupla(x),
        iteraciones=iteraciones,
        norma_residuo=norma_residuo,
        norma_residuo_inicial=norma_residuo_inicial,
        historial=historial,
    )
