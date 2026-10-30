"""Definición de problemas no lineales y parametrizados.

Un :class:`ProblemaNoLineal` representa ``F(x) = 0``. Un
:class:`ProblemaParametrizado` representa ``F(u, λ) = 0`` y conserva, además
del residuo, la matriz tangente ``∂F/∂u`` y la derivada respecto al parámetro
``∂F/∂λ``. Esta última es la que necesita un método de continuación como
arc-length.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

Vector = NDArray[np.float64]
"""Vector de números reales en doble precisión."""

Matriz = NDArray[np.float64]
"""Matriz de números reales en doble precisión."""


@dataclass(frozen=True, slots=True)
class ProblemaNoLineal:
    """Sistema de ecuaciones no lineales ``F(x) = 0``.

    Attributes:
        residuo: Función que evalúa ``F(x)``. Debe devolver un vector de la
            misma dimensión que ``x``.
        jacobiano: Función que evalúa ``∂F/∂x``. Si es ``None``, el solver
            puede aproximarla por diferencias finitas.
    """

    residuo: Callable[[Vector], Vector]
    jacobiano: Callable[[Vector], Matriz] | None = None


@dataclass(frozen=True, slots=True)
class ProblemaParametrizado:
    """Sistema de ecuaciones no lineales ``F(u, λ) = 0``.

    Attributes:
        residuo: Función que evalúa ``F(u, λ)``.
        jacobiano: Función que evalúa ``∂F/∂u``. Si es ``None``, el solver
            puede aproximarla por diferencias finitas.
        derivada_parametro: Función que evalúa ``∂F/∂λ``. Es necesaria para
            los métodos de continuación; para ``F(u, λ) = f(u) − λ·q`` vale
            ``−q``.
    """

    residuo: Callable[[Vector, float], Vector]
    jacobiano: Callable[[Vector, float], Matriz] | None = None
    derivada_parametro: Callable[[Vector, float], Vector] | None = None

    def con_parametro(self, parametro: float) -> ProblemaNoLineal:
        """Fija ``λ`` y devuelve un problema no lineal ordinario.

        Args:
            parametro: Valor del parámetro ``λ`` que se mantiene constante.

        Returns:
            Un :class:`ProblemaNoLineal` cuyo residuo y Jacobiano evalúan el
            sistema con ese valor de ``λ``.
        """
        residuo = self.residuo
        jacobiano = self.jacobiano
        if jacobiano is None:
            return ProblemaNoLineal(
                residuo=lambda x: residuo(x, parametro),
            )
        return ProblemaNoLineal(
            residuo=lambda x: residuo(x, parametro),
            jacobiano=lambda x: jacobiano(x, parametro),
        )
