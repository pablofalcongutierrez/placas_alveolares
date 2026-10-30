"""Aproximación numérica del Jacobiano.

La fórmula de diferencias finitas es genérica y reutilizable por cualquier
solver que necesite una tangente aproximada. No se reimplementa álgebra
lineal: la resolución del sistema queda en ``numpy.linalg``.
"""

from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np

from placas_alveolares.domain.numerics.errores import (
    ErrorDimensionesInvalidas,
    ErrorEvaluacionNoFinita,
    ErrorOpcionesInvalidas,
)
from placas_alveolares.domain.numerics.problema import Matriz, Vector


def jacobiano_por_diferencias_finitas(
    funcion: Callable[[Vector], Vector],
    x: Vector,
    f0: Vector,
    *,
    paso: float | None = None,
) -> Matriz:
    """Aproxima el Jacobiano de ``funcion`` mediante diferencias hacia adelante.

    Args:
        funcion: Función vectorial ``F(x)``.
        x: Punto donde se evalúa el Jacobiano.
        f0: Valor ``F(x)`` ya calculado.
        paso: Paso absoluto. Si es ``None``, se usa
            ``sqrt(eps)·max(1, |x_k|)`` para cada componente.

    Returns:
        La matriz Jacobiana aproximada, de forma ``(n, n)``.

    Raises:
        ErrorDimensionesInvalidas: Si ``x`` o ``f0`` no son vectores
            coherentes o si la función devuelve otra dimensión.
        ErrorEvaluacionNoFinita: Si aparecen NaN o infinitos.
        ErrorOpcionesInvalidas: Si el paso no es finito y positivo.
    """
    if x.ndim != 1 or x.size == 0:
        raise ErrorDimensionesInvalidas(
            "El punto de evaluación del Jacobiano debe ser un vector "
            "unidimensional no vacío."
        )
    if not np.all(np.isfinite(x)):
        raise ErrorEvaluacionNoFinita(
            "El punto de evaluación del Jacobiano contiene valores no finitos."
        )
    dimension = int(x.size)
    if f0.shape != (dimension,):
        raise ErrorDimensionesInvalidas(
            "El valor F(x) debe tener la misma dimensión que x."
        )
    if not np.all(np.isfinite(f0)):
        raise ErrorEvaluacionNoFinita("F(x) contiene valores no finitos.")
    if paso is not None and (not math.isfinite(paso) or paso <= 0.0):
        raise ErrorOpcionesInvalidas(
            "El paso de diferencias finitas debe ser finito y positivo."
        )

    raiz_eps = math.sqrt(float(np.finfo(np.float64).eps))
    jacobiano = np.empty((dimension, dimension), dtype=np.float64)
    for columna in range(dimension):
        incremento = (
            paso
            if paso is not None
            else raiz_eps * max(1.0, abs(float(x[columna])))
        )
        x_desplazado = x.copy()
        x_desplazado[columna] += incremento
        f_desplazado = np.asarray(funcion(x_desplazado), dtype=np.float64)
        if f_desplazado.shape != (dimension,):
            raise ErrorDimensionesInvalidas(
                "La función debe devolver un vector de la misma dimensión "
                "que x."
            )
        if not np.all(np.isfinite(f_desplazado)):
            raise ErrorEvaluacionNoFinita(
                "F(x) contiene valores no finitos al perturbar el punto."
            )
        jacobiano[:, columna] = (f_desplazado - f0) / incremento
    return jacobiano
