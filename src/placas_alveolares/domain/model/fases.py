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

from placas_alveolares.domain.model.seccion import (
    ComponenteSeccion,
    CondicionAdherencia,
    Seccion,
)


@dataclass(frozen=True, slots=True)
class Fase:
    """Fase de construcción o puesta en carga.

    Attributes:
        indice: Orden de la fase en la secuencia constructiva (0, 1, 2…).
        nombre: Descripción legible de la fase. Por defecto vacío.
    """

    indice: int
    nombre: str = ""


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
