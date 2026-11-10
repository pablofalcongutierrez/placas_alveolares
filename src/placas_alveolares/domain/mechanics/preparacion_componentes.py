"""Preparación de mallas y leyes constitutivas para una fase."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from placas_alveolares.domain.mechanics.geometria_efectiva import (
    geometria_efectiva,
)
from placas_alveolares.domain.mechanics.laws import LeyTensionDeformacion
from placas_alveolares.domain.mechanics.mallado import Triangulo, mallar
from placas_alveolares.domain.model.fases import (
    Fase,
    componentes_activos,
)
from placas_alveolares.domain.model.seccion import (
    ComponenteId,
    ComponenteSeccion,
    Seccion,
)
from placas_alveolares.domain.state.estado_seccion import EstadoSeccionFase


class ProveedorLeyes(Protocol):
    """Proveedor de leyes constitutivas dependientes de la fase."""

    def ley_para(
        self,
        componente: ComponenteSeccion,
        fase: Fase,
    ) -> LeyTensionDeformacion:
        """Devuelve la ley constitutiva de un componente en una fase.

        Args:
            componente: Componente del modelo.
            fase: Fase para la que se prepara la ley.

        Returns:
            La ley tensión-deformación aplicable.
        """
        ...


@dataclass(frozen=True, slots=True)
class ComponenteCalculo:
    """Componente preparado para integrar tensiones en una fase.

    Attributes:
        componente_id: Identificador del componente del modelo.
        malla: Triángulos de su geometría efectiva.
        ley: Ley constitutiva aplicable en la fase.
    """

    componente_id: ComponenteId
    malla: tuple[Triangulo, ...]
    ley: LeyTensionDeformacion


def preparar_componentes(
    seccion: Seccion,
    fase: Fase,
    estado: EstadoSeccionFase,
    proveedor_leyes: ProveedorLeyes,
) -> tuple[ComponenteCalculo, ...]:
    """Prepara mallas y leyes de los componentes activos en una fase.

    Args:
        seccion: Definición completa de la sección.
        fase: Fase que se prepara.
        estado: Estado de la fase, usado para validar los componentes activos.
        proveedor_leyes: Fuente de leyes constitutivas por componente y fase.

    Returns:
        Los componentes activos listos para integrar tensiones.

    Raises:
        ErrorValidacion: Si un componente activo no tiene estado.
    """
    activos = componentes_activos(seccion, fase.indice)
    preparados: list[ComponenteCalculo] = []
    for componente in activos:
        estado.componente_requerido(componente.id)
        geometria = geometria_efectiva(componente, activos)
        preparados.append(
            ComponenteCalculo(
                componente_id=componente.id,
                malla=mallar(geometria),
                ley=proveedor_leyes.ley_para(componente, fase),
            )
        )
    return tuple(preparados)
