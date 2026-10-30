"""Contratos y tipos de los métodos de continuación.

Arc-length es un método de continuación, no un solver de ecuaciones
ordinario: el factor de carga ``λ`` es una incógnita y el resultado es una
trayectoria. Este paquete define los contratos; la implementación concreta de
arc-length se añadirá en un milestone posterior.
"""

from placas_alveolares.domain.numerics.continuacion.base import (
    SolverContinuacion,
)
from placas_alveolares.domain.numerics.continuacion.problema import (
    ProblemaContinuacion,
)
from placas_alveolares.domain.numerics.continuacion.restriccion import (
    ArcoCilindrico,
    ArcoEsferico,
    RestriccionArco,
)
from placas_alveolares.domain.numerics.continuacion.tipos import (
    EstadoContinuacion,
    MotivoParada,
    OpcionesContinuacion,
    PasoContinuacion,
    ResultadoContinuacion,
)

__all__ = [
    "ArcoCilindrico",
    "ArcoEsferico",
    "EstadoContinuacion",
    "MotivoParada",
    "OpcionesContinuacion",
    "PasoContinuacion",
    "ProblemaContinuacion",
    "RestriccionArco",
    "ResultadoContinuacion",
    "SolverContinuacion",
]
