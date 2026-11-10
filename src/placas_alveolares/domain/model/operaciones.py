"""Operaciones que modifican el estado de una sección en una fase.

Las operaciones son objetos puros: reciben el estado anterior y la definición
de la sección, y devuelven un estado nuevo. El contrato abierto permite añadir
nuevas operaciones sin modificar el bucle que ejecuta las fases.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from placas_alveolares.domain.errores import ErrorValidacion
from placas_alveolares.domain.state.plano_deformaciones import (
    PlanoDeformaciones,
)

if TYPE_CHECKING:
    from placas_alveolares.domain.model.seccion import Seccion
    from placas_alveolares.domain.state.estado_seccion import (
        EstadoSeccionFase,
    )


@dataclass(frozen=True, slots=True)
class PretensadoPorFuerza:
    """Pretensado inicial expresado como fuerza de tesado.

    Attributes:
        fuerza: Fuerza de tesado en N, positiva a tracción.
    """

    fuerza: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.fuerza) or self.fuerza < 0.0:
            raise ErrorValidacion(
                "La fuerza de tesado debe ser finita y no negativa; se "
                f"recibió {self.fuerza} N."
            )


@dataclass(frozen=True, slots=True)
class PretensadoPorTension:
    """Pretensado inicial expresado como tensión.

    Attributes:
        tension: Tensión inicial en MPa, positiva a tracción.
    """

    tension: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.tension) or self.tension < 0.0:
            raise ErrorValidacion(
                "La tensión de pretensado debe ser finita y no negativa; se "
                f"recibió {self.tension} MPa."
            )


@dataclass(frozen=True, slots=True)
class PretensadoPorPlano:
    """Pretensado inicial expresado como plano de deformaciones."""

    plano: PlanoDeformaciones


type PretensadoInicial = (
    PretensadoPorFuerza | PretensadoPorTension | PretensadoPorPlano
)


@dataclass(frozen=True, slots=True)
class PerdidaPorTension:
    """Pérdida de pretensado expresada como tensión.

    Attributes:
        tension: Pérdida de tensión en MPa, positiva.
    """

    tension: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.tension) or self.tension <= 0.0:
            raise ErrorValidacion(
                "La pérdida de tensión debe ser finita y positiva; se "
                f"recibió {self.tension} MPa."
            )


@dataclass(frozen=True, slots=True)
class PerdidaPorDeformacion:
    """Pérdida de pretensado expresada como deformación axial.

    Attributes:
        deformacion: Pérdida de deformación positiva, tanto por uno.
    """

    deformacion: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.deformacion) or self.deformacion <= 0.0:
            raise ErrorValidacion(
                "La pérdida de deformación debe ser finita y positiva; se "
                f"recibió {self.deformacion}."
            )


type PerdidaPretensado = PerdidaPorTension | PerdidaPorDeformacion


class OperacionFase(Protocol):
    """Operación pura aplicada al estado de una fase."""

    def aplicar(
        self,
        estado: EstadoSeccionFase,
        seccion: Seccion,
    ) -> EstadoSeccionFase:
        """Aplica la operación y devuelve un estado nuevo.

        Args:
            estado: Estado de la sección antes de la operación.
            seccion: Definición completa de la sección.

        Returns:
            El estado actualizado.

        Raises:
            ErrorValidacion: Si la operación no es aplicable al estado.
        """
        ...
