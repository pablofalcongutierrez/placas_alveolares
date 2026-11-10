"""Modelo estructural completo.

Agrupa la sección y la secuencia temporal de fases. Cada fase contiene sus
acciones, operaciones y tiempos. El campo ``fase_activa`` selecciona la fase
que se comprueba; no es un estado mutable de la sección. El historial de
estados calculados vive fuera del modelo, en :class:`HistorialSeccion`.
"""

from __future__ import annotations

from dataclasses import dataclass

from placas_alveolares.domain.errores import ModeloInvalido
from placas_alveolares.domain.model.fases import Fase
from placas_alveolares.domain.model.seccion import Seccion
from placas_alveolares.domain.model.tiempo import Tiempo

_FASE_INICIAL = Fase(
    indice=0,
    tiempo_inicio=Tiempo(0.0),
    tiempo_fin=Tiempo(0.0),
)
"""Fase instantánea inicial usada cuando el modelo no declara otras."""


@dataclass(frozen=True, slots=True)
class ModeloEstructural:
    """Modelo estructural de una pieza a comprobar.

    Attributes:
        seccion: Sección transversal completa.
        fases: Secuencia temporal de fases. Por defecto una única fase
            instantánea en ``t=0``.
        fase_activa: Fase que se comprueba. Por defecto ``0``.

    Raises:
        ModeloInvalido: Si hay índices de fase duplicados, si ``fase_activa`` no
            figura entre las fases, si las fases se solapan temporalmente o si
            algún componente referencia una fase inexistente.
    """

    seccion: Seccion
    fases: tuple[Fase, ...] = (_FASE_INICIAL,)
    fase_activa: int = 0

    def __post_init__(self) -> None:
        if not self.fases:
            raise ModeloInvalido("El modelo necesita al menos una fase.")

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

        for anterior, siguiente in zip(self.fases, self.fases[1:]):
            if siguiente.tiempo_inicio.dias < anterior.tiempo_fin.dias:
                raise ModeloInvalido(
                    "Las fases no pueden solaparse temporalmente: la fase "
                    f"{siguiente.indice} empieza en "
                    f"{siguiente.tiempo_inicio.dias} días, antes de que "
                    f"termine la fase {anterior.indice} en "
                    f"{anterior.tiempo_fin.dias} días."
                )

    def fase_por_indice(self, indice: int) -> Fase:
        """Devuelve la definición de una fase por su índice.

        Args:
            indice: Índice de la fase buscada.

        Returns:
            La fase correspondiente.

        Raises:
            ModeloInvalido: Si el índice no existe en el modelo.
        """
        for fase in self.fases:
            if fase.indice == indice:
                return fase
        raise ModeloInvalido(f"No existe la fase con índice {indice}.")
