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
:mod:`placas_alveolares.domain.model.fases`). Un componente de acero embebido
en hormigón declara su anfitrión; el hormigón se malla descontando el hueco
geométrico del componente (véase
``docs/decisions/0013-superposicion-geometrica-componentes.md``).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from placas_alveolares.domain.errores import SeccionInvalida
from placas_alveolares.domain.model.geometria import (
    GeometriaContorno,
    contorno_contiene,
    contornos_se_solapan,
)
from placas_alveolares.domain.model.materiales import (
    AceroArmadura,
    AceroPretensado,
    Hormigon,
    Material,
)

type ComponenteId = str
"""Identificador estable de un componente dentro de una sección."""


class CondicionAdherencia(StrEnum):
    """Condición de adherencia de un componente de acero de pretensado."""

    ADHERIDO = "adherido"
    ENFUNDADO = "enfundado"


@dataclass(frozen=True, slots=True)
class ComponenteSeccion:
    """Componente de una sección transversal.

    Attributes:
        id: Identificador estable y único dentro de la sección.
        geometria: Región material del componente (contorno, con sus huecos).
        material: Material físico del componente.
        fase_incorporacion: Índice de la fase en que entra en servicio. Por
            defecto ``0``.
        adherencia: Condición de adherencia inicial. Solo es relevante para
            componentes de :class:`AceroPretensado`; por defecto adherido.
        componente_anfitrion_id: Componente de hormigón del que se descuenta
            geométricamente este componente embebido. Por defecto ``None``.

    Raises:
        SeccionInvalida: Si el identificador está vacío, la fase es negativa o
            el anfitrión declarado no es válido para el material.
    """

    id: ComponenteId
    geometria: GeometriaContorno
    material: Material
    fase_incorporacion: int = 0
    adherencia: CondicionAdherencia = CondicionAdherencia.ADHERIDO
    componente_anfitrion_id: ComponenteId | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise SeccionInvalida(
                "El identificador del componente no puede estar vacío."
            )
        if self.fase_incorporacion < 0:
            raise SeccionInvalida(
                "La fase de incorporación no puede ser negativa; se recibió "
                f"{self.fase_incorporacion}."
            )
        if self.componente_anfitrion_id == self.id:
            raise SeccionInvalida(
                f"El componente '{self.id}' no puede ser su propio anfitrión."
            )
        if self.componente_anfitrion_id is not None and not isinstance(
            self.material, (AceroArmadura, AceroPretensado)
        ):
            raise SeccionInvalida(
                "Solo los componentes de acero pueden declarar un anfitrión "
                f"de hormigón; '{self.id}' es {type(self.material).__name__}."
            )


@dataclass(frozen=True, slots=True)
class Seccion:
    """Sección transversal completa, definida por sus componentes.

    Attributes:
        componentes: Todos los componentes que forman la sección, con
            independencia de la fase en que entren en servicio.

    Raises:
        SeccionInvalida: Si la sección no tiene componentes, hay identificadores
            repetidos o la geometría de los componentes es incoherente.
    """

    componentes: tuple[ComponenteSeccion, ...]

    def __post_init__(self) -> None:
        if not self.componentes:
            raise SeccionInvalida("Una sección necesita al menos un componente.")

        identificadores = [componente.id for componente in self.componentes]
        if len(set(identificadores)) != len(identificadores):
            repetidos = sorted(
                {
                    identificador
                    for identificador in identificadores
                    if identificadores.count(identificador) > 1
                }
            )
            raise SeccionInvalida(
                f"Los identificadores de componente deben ser únicos; "
                f"se repiten: {repetidos}."
            )

        por_id = {componente.id: componente for componente in self.componentes}
        for componente in self.componentes:
            self._validar_huecos(componente)
            anfitrion_id = componente.componente_anfitrion_id
            if anfitrion_id is None:
                continue
            anfitrion = por_id.get(anfitrion_id)
            if anfitrion is None:
                raise SeccionInvalida(
                    f"El anfitrión '{anfitrion_id}' del componente "
                    f"'{componente.id}' no existe en la sección."
                )
            if not isinstance(anfitrion.material, Hormigon):
                raise SeccionInvalida(
                    f"El anfitrión '{anfitrion_id}' debe ser de hormigón."
                )
            if not contorno_contiene(
                componente.geometria.exterior,
                anfitrion.geometria.exterior,
            ):
                raise SeccionInvalida(
                    f"El componente '{componente.id}' no está contenido "
                    f"íntegramente en su anfitrión '{anfitrion_id}'."
                )
            for hueco in anfitrion.geometria.huecos:
                if contornos_se_solapan(componente.geometria.exterior, hueco):
                    raise SeccionInvalida(
                        f"El componente '{componente.id}' ocupa un hueco del "
                        f"anfitrión '{anfitrion_id}'."
                    )

        for i, primero in enumerate(self.componentes):
            for segundo in self.componentes[i + 1 :]:
                if (
                    primero.componente_anfitrion_id == segundo.id
                    or segundo.componente_anfitrion_id == primero.id
                ):
                    continue
                if self._geometrias_se_solapan(primero, segundo):
                    raise SeccionInvalida(
                        "Los componentes "
                        f"'{primero.id}' y '{segundo.id}' se solapan sin una "
                        "relación de anfitrión declarada."
                    )

    @staticmethod
    def _validar_huecos(componente: ComponenteSeccion) -> None:
        """Valida contención y ausencia de solapes entre los huecos."""
        geometria = componente.geometria
        for hueco in geometria.huecos:
            if not contorno_contiene(hueco, geometria.exterior):
                raise SeccionInvalida(
                    f"Un hueco del componente '{componente.id}' queda fuera "
                    "de su contorno exterior."
                )
        for i, primero in enumerate(geometria.huecos):
            for segundo in geometria.huecos[i + 1 :]:
                if contornos_se_solapan(primero, segundo):
                    raise SeccionInvalida(
                        f"El componente '{componente.id}' tiene huecos "
                        "solapados."
                    )

    @staticmethod
    def _geometrias_se_solapan(
        primero: ComponenteSeccion,
        segundo: ComponenteSeccion,
    ) -> bool:
        """Comprueba el solape de todos los contornos de dos componentes."""
        contornos_primero = (
            primero.geometria.exterior,
            *primero.geometria.huecos,
        )
        contornos_segundo = (
            segundo.geometria.exterior,
            *segundo.geometria.huecos,
        )
        return any(
            contornos_se_solapan(a, b)
            for a in contornos_primero
            for b in contornos_segundo
        )

    def componente_por_id(self, componente_id: ComponenteId) -> ComponenteSeccion:
        """Devuelve un componente por su identificador.

        Args:
            componente_id: Identificador buscado.

        Returns:
            El componente correspondiente.

        Raises:
            SeccionInvalida: Si el identificador no existe.
        """
        for componente in self.componentes:
            if componente.id == componente_id:
                return componente
        raise SeccionInvalida(
            f"No existe un componente con identificador '{componente_id}'."
        )
