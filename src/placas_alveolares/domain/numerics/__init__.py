"""Métodos numéricos genéricos, independientes de la física.

El paquete separa dos familias:

- **Ecuaciones no lineales** ``F(x) = 0``: :class:`SolverNoLineal` y, de
  momento, :class:`Newton`.
- **Continuación** ``F(u, λ) = 0`` con restricción de arco: contratos de
  :class:`SolverContinuacion`, restricciones esférica y cilíndrica, y tipos
  de trayectoria. La implementación concreta de arc-length se añadirá más
  adelante.

No importa mecánica, normas ni la capa de aplicación.
"""

from placas_alveolares.domain.numerics.base import SolverNoLineal
from placas_alveolares.domain.numerics.continuacion import (
    ArcoCilindrico,
    ArcoEsferico,
    EstadoContinuacion,
    MotivoParada,
    OpcionesContinuacion,
    PasoContinuacion,
    ProblemaContinuacion,
    RestriccionArco,
    ResultadoContinuacion,
    SolverContinuacion,
)
from placas_alveolares.domain.numerics.diferencias_finitas import (
    jacobiano_por_diferencias_finitas,
)
from placas_alveolares.domain.numerics.errores import (
    ErrorContinuacion,
    ErrorDimensionesInvalidas,
    ErrorEvaluacionNoFinita,
    ErrorJacobianoSingular,
    ErrorNoConvergencia,
    ErrorNoConvergenciaContinuacion,
    ErrorOpcionesInvalidas,
    ErrorProblemaIncompleto,
    ErrorSolver,
)
from placas_alveolares.domain.numerics.newton import Newton
from placas_alveolares.domain.numerics.opciones import (
    NormaVectorial,
    OpcionesNewton,
    OpcionesSolver,
)
from placas_alveolares.domain.numerics.problema import (
    Matriz,
    ProblemaNoLineal,
    ProblemaParametrizado,
    Vector,
)
from placas_alveolares.domain.numerics.resultado import (
    IteracionSolver,
    ResultadoSolver,
)

__all__ = [
    "ArcoCilindrico",
    "ArcoEsferico",
    "ErrorContinuacion",
    "ErrorDimensionesInvalidas",
    "ErrorEvaluacionNoFinita",
    "ErrorJacobianoSingular",
    "ErrorNoConvergencia",
    "ErrorNoConvergenciaContinuacion",
    "ErrorOpcionesInvalidas",
    "ErrorProblemaIncompleto",
    "ErrorSolver",
    "EstadoContinuacion",
    "IteracionSolver",
    "Matriz",
    "MotivoParada",
    "Newton",
    "NormaVectorial",
    "OpcionesContinuacion",
    "OpcionesNewton",
    "OpcionesSolver",
    "PasoContinuacion",
    "ProblemaContinuacion",
    "ProblemaNoLineal",
    "ProblemaParametrizado",
    "RestriccionArco",
    "ResultadoContinuacion",
    "ResultadoSolver",
    "SolverContinuacion",
    "SolverNoLineal",
    "Vector",
    "jacobiano_por_diferencias_finitas",
]
