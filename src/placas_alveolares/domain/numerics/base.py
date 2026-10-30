"""Contrato abstracto de los solvers de ecuaciones no lineales."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from placas_alveolares.domain.numerics.problema import ProblemaNoLineal
from placas_alveolares.domain.numerics.resultado import ResultadoSolver


class SolverNoLineal(ABC):
    """Solver de un sistema ``F(x) = 0``.

    Cada implementación concreta (Newton, Newton modificado, Newton
    amortiguado, Broyden…) es independiente. La configuración se inyecta en
    el constructor de la implementación concreta.
    """

    @abstractmethod
    def resolver(
        self,
        problema: ProblemaNoLineal,
        x0: Sequence[float],
    ) -> ResultadoSolver:
        """Resuelve ``F(x) = 0`` partiendo de ``x0``.

        Args:
            problema: Sistema de ecuaciones y, opcionalmente, su Jacobiano.
            x0: Punto inicial.

        Returns:
            El resultado con la solución y el historial de iteraciones.

        Raises:
            ErrorNoConvergencia: Si no se alcanza la tolerancia.
            ErrorJacobianoSingular: Si el sistema lineal es singular.
            ErrorDimensionesInvalidas: Si las dimensiones no son coherentes.
            ErrorEvaluacionNoFinita: Si aparecen NaN o infinitos.
        """
        ...
