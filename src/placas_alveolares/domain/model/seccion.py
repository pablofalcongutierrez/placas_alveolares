"""Sección transversal como conjunto de componentes.

Una :class:`Seccion` es la definición **completa e inmutable** de todos los
componentes que llegarán a existir. Cada :class:`ComponenteSeccion` es
independiente y aporta su propia geometría y material. Dos metadatos
ortogonales modulan su contribución:

- ``fase_incorporacion``: eje **temporal** (p. ej. la capa de compresión se
  hormigona en una fase posterior a la placa).
- ``adherencia``: eje de **adherencia** (un cordón enfundado existe pero no
  transmite en la sección analizada).

Ninguno de los dos es un estado mutable: la activación de un componente para
una fase concreta es una **consulta pura** (véase
:mod:`placas_alveolares.domain.model.fases`). Los componentes pueden
solaparse; la superposición la resuelve el motor de integración, no la
geometría (véase ``docs/decisions/0007-modelo-seccion-componentes-fases-adherencia.md``).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from placas_alveolares.domain.model.geometria import GeometriaContorno
from placas_alveolares.domain.model.materiales import Material


class CondicionAdherencia(StrEnum):
    """Condición de adherencia de un componente de acero de pretensado."""

    ADHERIDO = "adherido"
    ENFUNDADO = "enfundado"


@dataclass(frozen=True, slots=True)
class ComponenteSeccion:
    """Componente de una sección transversal.

    Attributes:
        geometria: Región material del componente (contorno, con sus huecos).
        material: Material físico del componente.
        fase_incorporacion: Índice de la fase en que entra en servicio. Por
            defecto ``0``.
        adherencia: Condición de adherencia. Solo es relevante para componentes
            de :class:`AceroPretensado`; por defecto adherido.
    """

    geometria: GeometriaContorno
    material: Material
    fase_incorporacion: int = 0
    adherencia: CondicionAdherencia = CondicionAdherencia.ADHERIDO


@dataclass(frozen=True, slots=True)
class Seccion:
    """Sección transversal completa, definida por sus componentes.

    Attributes:
        componentes: Todos los componentes que forman la sección, con
            independencia de la fase en que entren en servicio.

    Raises:
        ValueError: Si la sección no tiene ningún componente.
    """

    componentes: tuple[ComponenteSeccion, ...]

    def __post_init__(self) -> None:
        if not self.componentes:
            raise ValueError("Una sección necesita al menos un componente.")
