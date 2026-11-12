"""Contrato portable para visualizar secciones, deformaciones y tensiones.

El contrato contiene magnitudes físicas —mm, tanto por uno y MPa— y ninguna
decisión de dibujo. Una UI de escritorio, una aplicación web o un exportador
pueden consumirlo sin conocer el modelo estructural ni las leyes constitutivas.

Todas las geometrías se expresan en el sistema alineado con la línea neutra:
``u`` es tangente a la línea neutra y ``v`` es normal, positiva hacia el aumento
de deformación. Así la línea neutra queda horizontal en ``v = 0``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

VERSION_FORMATO = 1
"""Versión del contrato de visualización."""


class TipoMaterialVista(StrEnum):
    """Familia de material empleada por el visualizador."""

    HORMIGON = "hormigon"
    ACERO_ARMADURA = "acero_armadura"
    ACERO_PRETENSADO = "acero_pretensado"


class AdherenciaVista(StrEnum):
    """Adherencia de un componente en la fase representada."""

    ADHERIDO = "adherido"
    ENFUNDADO = "enfundado"


@dataclass(frozen=True, slots=True)
class PuntoVista:
    """Punto del sistema alineado con la línea neutra.

    Attributes:
        u: Coordenada tangente (mm).
        v: Coordenada normal (mm), positiva hacia el aumento de deformación.
    """

    u: float
    v: float


@dataclass(frozen=True, slots=True)
class ContornoVista:
    """Contorno cerrado en el sistema alineado.

    Attributes:
        puntos: Vértices del contorno, en orden.
    """

    puntos: tuple[PuntoVista, ...]


@dataclass(frozen=True, slots=True)
class GeometriaVista:
    """Geometría efectiva de un componente, con sus huecos.

    Attributes:
        exterior: Contorno exterior.
        huecos: Huecos interiores descontados.
    """

    exterior: ContornoVista
    huecos: tuple[ContornoVista, ...]


@dataclass(frozen=True, slots=True)
class MuestraPerfilVista:
    """Muestra de un perfil vertical de un componente.

    Attributes:
        v: Cota alineada de la muestra (mm).
        deformacion: Deformación constitutiva (tanto por uno).
        tension: Tensión normal (MPa), positiva a tracción.
    """

    v: float
    deformacion: float
    tension: float


@dataclass(frozen=True, slots=True)
class TramoPerfilVista:
    """Tramo continuo de un perfil, sin atravesar huecos.

    Attributes:
        muestras: Muestras ordenadas de menor a mayor ``v``.
    """

    muestras: tuple[MuestraPerfilVista, ...]


@dataclass(frozen=True, slots=True)
class PerfilComponenteVista:
    """Perfil vertical de deformación y tensión de un componente.

    Attributes:
        u: Cota tangente de la vertical de muestreo (mm).
        tramos: Tramos continuos del perfil.
    """

    u: float
    tramos: tuple[TramoPerfilVista, ...]


@dataclass(frozen=True, slots=True)
class ComponenteVista:
    """Componente preparado para su representación.

    Attributes:
        componente_id: Identificador del componente.
        tipo_material: Familia del material.
        adherencia: Condición de adherencia en la fase.
        geometria: Geometría efectiva alineada.
        perfil: Perfil de deformación y tensión.
    """

    componente_id: str
    tipo_material: TipoMaterialVista
    adherencia: AdherenciaVista
    geometria: GeometriaVista
    perfil: PerfilComponenteVista


@dataclass(frozen=True, slots=True)
class MuestraDeformacionComunVista:
    """Muestra del plano común de deformaciones.

    Attributes:
        v: Cota alineada (mm).
        deformacion: Deformación común (tanto por uno).
    """

    v: float
    deformacion: float


@dataclass(frozen=True, slots=True)
class RangoVista:
    """Intervalo cerrado de una magnitud física.

    Attributes:
        minimo: Valor mínimo.
        maximo: Valor máximo.
    """

    minimo: float
    maximo: float

    @property
    def amplitud(self) -> float:
        """Diferencia entre el máximo y el mínimo."""
        return self.maximo - self.minimo


@dataclass(frozen=True, slots=True)
class LimitesFaseVista:
    """Rangos físicos de una fase alineada.

    Attributes:
        vertical: Rango de la coordenada ``v`` (mm).
        deformacion: Rango de deformaciones (tanto por uno).
        tension: Rango de tensiones (MPa).
    """

    vertical: RangoVista
    deformacion: RangoVista
    tension: RangoVista


@dataclass(frozen=True, slots=True)
class FaseAlineadaVista:
    """Estado alineado de una fase.

    Attributes:
        indice: Índice de la fase.
        nombre: Nombre legible de la fase.
        tiempo_inicio_dias: Instante inicial (días).
        tiempo_fin_dias: Instante final (días).
        equilibrio_resuelto: Indica si la fase resolvió equilibrio.
        linea_neutra_definida: Indica si existe línea neutra única.
        angulo_radianes: Giro aplicado a la sección (rad).
        curvatura: Módulo de la curvatura resultante (mm⁻¹).
        deformacion_comun: Muestras del plano común.
        componentes: Componentes activos, con su geometría y perfil.
        limites: Rangos físicos de la fase.
    """

    indice: int
    nombre: str
    tiempo_inicio_dias: float
    tiempo_fin_dias: float
    equilibrio_resuelto: bool
    linea_neutra_definida: bool
    angulo_radianes: float
    curvatura: float
    deformacion_comun: tuple[MuestraDeformacionComunVista, ...]
    componentes: tuple[ComponenteVista, ...]
    limites: LimitesFaseVista


@dataclass(frozen=True, slots=True)
class EvolucionAlineadaVista:
    """Evolución completa de una sección alineada por fases.

    Attributes:
        version_formato: Versión del contrato.
        unidad_longitud: Unidad de las coordenadas geométricas.
        unidad_deformacion: Unidad de las deformaciones.
        unidad_tension: Unidad de las tensiones.
        fases: Fases en orden de cálculo.
        limites_globales: Rangos que engloban todas las fases.
    """

    version_formato: int
    unidad_longitud: str
    unidad_deformacion: str
    unidad_tension: str
    fases: tuple[FaseAlineadaVista, ...]
    limites_globales: LimitesFaseVista
