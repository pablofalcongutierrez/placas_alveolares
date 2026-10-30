"""Contrato abstracto de los solvers de continuación."""

from __future__ import annotations

from abc import ABC, abstractmethod

from placas_alveolares.domain.numerics.continuacion.problema import (
    ProblemaContinuacion,
)
from placas_alveolares.domain.numerics.continuacion.tipos import (
    EstadoContinuacion,
    ResultadoContinuacion,
)


class SolverContinuacion(ABC):
    """Solver de una trayectoria ``F(u, λ) = 0`` con restricción de arco.

    La configuración (corrector, restricción, opciones de paso) se inyecta en
    el constructor de la implementación concreta. Cada implementación es
    independiente y puede reutilizar un :class:`SolverNoLineal` como
    corrector del sistema aumentado.
    """

    @abstractmethod
    def resolver(
        self,
        problema: ProblemaContinuacion,
        estado_inicial: EstadoContinuacion,
    ) -> ResultadoContinuacion:
        """Recorre la trayectoria desde ``estado_inicial``.

        Args:
            problema: Sistema parametrizado y restricción de arco.
            estado_inicial: Estado de equilibrio inicial ``(u0, λ0)``.

        Returns:
            La trayectoria de estados convergidos.

        Raises:
            ErrorNoConvergenciaContinuacion: Si un paso no converge.
            ErrorDimensionesInvalidas: Si las dimensiones no son coherentes.
            ErrorEvaluacionNoFinita: Si aparecen NaN o infinitos.
        """
        ...
