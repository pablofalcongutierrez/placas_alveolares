"""Fases de construcción y consultas de activación.

Una :class:`Fase` representa un estado de la construcción (p. ej. placa
prefabricada sola, o placa más capa de compresión). Los componentes de una
sección no conocen las fases: solo anotan en qué fase entran en servicio
(``fase_incorporacion``). La activación es, por tanto, una consulta pura.

En este milestone la fase solo identifica el orden constructivo. La
información temporal (edad del hormigón, cargas que entran en cada fase) se
añadirá con la evolución temporal en un milestone posterior.
"""

from __future__ import annotations

from dataclasses import dataclass

from placas_alveolares.domain.errores import FaseInvalida
from placas_alveolares.domain.model.acciones import EsfuerzosInternos
from placas_alveolares.domain.model.operaciones import OperacionFase
from placas_alveolares.domain.model.seccion import (
    ComponenteSeccion,
    CondicionAdherencia,
    Seccion,
)
from placas_alveolares.domain.model.tiempo import Tiempo


@dataclass(frozen=True, slots=True)
class Fase:
    """Fase de construcción o puesta en carga.

    Attributes:
        indice: Orden de la fase en la secuencia constructiva (0, 1, 2…).
        tiempo_inicio: Instante inicial de la fase.
        tiempo_fin: Instante final. Si coincide con el inicial, la fase es
            instantánea.
        acciones: Acciones totales vigentes al final de la fase.
        operaciones: Operaciones aplicadas al final, en orden.
        resolver_equilibrio: Si es ``True``, se resuelve el equilibrio después
            de aplicar las operaciones. Por defecto ``True``.
        nombre: Descripción legible de la fase. Por defecto vacío.

    Raises:
        FaseInvalida: Si el índice es negativo, el intervalo temporal no es
            válido o una fase sin equilibrio declara acciones no nulas.
    """

    indice: int
    tiempo_inicio: Tiempo
    tiempo_fin: Tiempo
    acciones: EsfuerzosInternos = EsfuerzosInternos()
    operaciones: tuple[OperacionFase, ...] = ()
    resolver_equilibrio: bool = True
    nombre: str = ""

    def __post_init__(self) -> None:
        if self.indice < 0:
            raise FaseInvalida(
                f"El índice de fase no puede ser negativo; se recibió {self.indice}."
            )
        if self.tiempo_inicio.dias > self.tiempo_fin.dias:
            raise FaseInvalida(
                "El tiempo final de la fase no puede ser anterior al inicial; "
                f"se recibió [{self.tiempo_inicio.dias}, "
                f"{self.tiempo_fin.dias}] días."
            )
        if not self.resolver_equilibrio and not self.acciones.es_nulo:
            raise FaseInvalida(
                "Una fase sin resolución de equilibrio no puede contener "
                "acciones externas."
            )


def componentes_activos(
    seccion: Seccion, fase: int
) -> tuple[ComponenteSeccion, ...]:
    """Devuelve los componentes en servicio en una fase.

    Args:
        seccion: Sección completa con todos sus componentes.
        fase: Índice de la fase que se comprueba.

    Returns:
        Los componentes cuya ``fase_incorporacion`` es menor o igual que
        ``fase``, en el orden original de la sección.
    """
    return tuple(c for c in seccion.componentes if c.fase_incorporacion <= fase)


def componentes_adheridos(
    componentes: tuple[ComponenteSeccion, ...]
) -> tuple[ComponenteSeccion, ...]:
    """Filtra los componentes con adherencia efectiva.

    Los componentes enfundados existen físicamente pero no transmiten
    esfuerzos en la sección analizada, por lo que se excluyen.

    Args:
        componentes: Componentes a filtrar.

    Returns:
        Los componentes con :attr:`CondicionAdherencia.ADHERIDO`.
    """
    return tuple(c for c in componentes if c.adherencia is CondicionAdherencia.ADHERIDO)
