"""Representación temporal de las fases de cálculo.

El núcleo usa días como unidad interna. Las horas se admiten en la frontera
del modelo para fases de edad temprana y se convierten a días al comparar.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from placas_alveolares.domain.errores import FaseInvalida

_HORAS_POR_DIA = 24.0


class UnidadTiempo(StrEnum):
    """Unidad de entrada de un instante o intervalo."""

    DIAS = "dias"
    HORAS = "horas"


@dataclass(frozen=True, slots=True)
class Tiempo:
    """Instante o duración expresada en días o horas.

    Attributes:
        valor: Magnitud temporal. Debe ser finita y no negativa.
        unidad: Unidad de ``valor``. Por defecto, días.

    Raises:
        FaseInvalida: Si ``valor`` no es finito o es negativo.
    """

    valor: float
    unidad: UnidadTiempo = UnidadTiempo.DIAS

    def __post_init__(self) -> None:
        if not math.isfinite(self.valor) or self.valor < 0.0:
            raise FaseInvalida(
                "El tiempo debe ser finito y no negativo; se recibió "
                f"{self.valor} {self.unidad}."
            )

    @property
    def dias(self) -> float:
        """Valor temporal convertido a días."""
        if self.unidad is UnidadTiempo.HORAS:
            return self.valor / _HORAS_POR_DIA
        return self.valor
