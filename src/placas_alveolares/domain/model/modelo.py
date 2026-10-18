"""Modelo estructural completo.

Agrupa la sección, las acciones internas y la secuencia de fases. El campo
``fase_activa`` selecciona la fase que se está comprobando; no es un estado
mutable de la sección, sino el selector de la consulta de activación. Para
comprobar otra fase basta con construir un modelo con otro ``fase_activa``
(p. ej. ``dataclasses.replace(modelo, fase_activa=1)``).
"""

from __future__ import annotations

from dataclasses import dataclass

from placas_alveolares.domain.errores import ModeloInvalido
from placas_alveolares.domain.model.acciones import EsfuerzosInternos
from placas_alveolares.domain.model.fases import Fase
from placas_alveolares.domain.model.seccion import Seccion


@dataclass(frozen=True, slots=True)
class ModeloEstructural:
    """Modelo estructural de una pieza a comprobar.

    Attributes:
        seccion: Sección transversal completa.
        acciones: Esfuerzos internos de cálculo que se comprueban.
        fases: Secuencia de fases de construcción. Por defecto una única fase
            inicial (``Fase(0)``).
        fase_activa: Fase que se comprueba. Por defecto ``0``.

    Raises:
        ModeloInvalido: Si hay índices de fase duplicados, si ``fase_activa`` no
            figura entre las fases del modelo o si algún componente referencia
            una fase inexistente.
    """

    seccion: Seccion
    acciones: EsfuerzosInternos
    fases: tuple[Fase, ...] = (Fase(0),)
    fase_activa: int = 0

    def __post_init__(self) -> None:
        indices = [fase.indice for fase in self.fases]
        if len(set(indices)) != len(indices):
            duplicados = sorted({i for i in indices if indices.count(i) > 1})
            raise ModeloInvalido(
                f"Los índices de fase deben ser únicos; se repiten: {duplicados}."
            )

        definidos = set(indices)
        if self.fase_activa not in definidos:
            raise ModeloInvalido(
                f"La fase activa {self.fase_activa} no está definida entre las "
                f"fases del modelo: {sorted(definidos)}."
            )

        fases_componentes = {c.fase_incorporacion for c in self.seccion.componentes}
        inexistentes = sorted(fases_componentes - definidos)
        if inexistentes:
            raise ModeloInvalido(
                "Hay componentes que referencian fases inexistentes: "
                f"{inexistentes}; fases definidas: {sorted(definidos)}."
            )
