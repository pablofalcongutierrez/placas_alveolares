"""Evaluación del campo tensional de un componente en un punto.

La deformación que ve la ley constitutiva de un componente no es la del plano
común, sino:

``ε = plano_común − plano_referencia + deformación_impuesta``

Por ello, la tensión de un cordón tesado puede ser no nula aunque el plano común
sea nulo, y su fibra de tensión nula puede no coincidir con la línea neutra
común. Este módulo concentra esa evaluación para que los visualizadores,
informes y futuras comprobaciones compartan la misma fórmula.
"""

from __future__ import annotations

from dataclasses import dataclass

from placas_alveolares.domain.mechanics.preparacion_componentes import (
    ComponenteCalculo,
)
from placas_alveolares.domain.model.geometria import Punto
from placas_alveolares.domain.state.estado_seccion import EstadoComponenteFase
from placas_alveolares.domain.state.plano_deformaciones import (
    PlanoDeformaciones,
)


@dataclass(frozen=True, slots=True)
class MuestraTension:
    """Deformación y tensión en una fibra de un componente.

    Attributes:
        punto: Punto de evaluación en coordenadas ``(y, z)`` (mm).
        deformacion: Deformación constitutiva (tanto por uno), positiva a
            tracción.
        tension: Tensión normal (MPa), positiva a tracción.
    """

    punto: Punto
    deformacion: float
    tension: float
    plano_constitutivo: PlanoDeformaciones


def evaluar_tension(
    componente: ComponenteCalculo,
    estado_componente: EstadoComponenteFase,
    plano_comun: PlanoDeformaciones,
    punto: Punto,
) -> MuestraTension:
    """Evalúa deformación constitutiva y tensión en una fibra.

    Args:
        componente: Componente con su malla y su ley constitutiva.
        estado_componente: Referencia, deformación impuesta y adherencia del
            componente en la fase.
        plano_comun: Plano cinemático común resuelto para la fase.
        punto: Punto de evaluación en coordenadas de la sección (mm).

    Returns:
        La muestra de deformación y tensión en el punto.
    """
    plano_constitutivo = estado_componente.deformacion_constitutiva(
        plano_comun
    )
    deformacion = plano_constitutivo.deformacion(punto.y, punto.z)
    return MuestraTension(
        punto=punto,
        deformacion=deformacion,
        tension=componente.ley.tension(deformacion),
        plano_constitutivo=plano_constitutivo,
    )
