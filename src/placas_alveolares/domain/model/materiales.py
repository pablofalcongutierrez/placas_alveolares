"""Materiales físicos del modelo estructural.

Un material describe únicamente propiedades **físicas o características**
(resistencias, módulos de deformación). **No** contiene la ley constitutiva
tensión-deformación: esa ley es normativa y se inyecta en los motores
mecánicos desde el preparador de cada norma (véase
``docs/decisions/0001-frontera-mecanica-fisica-vs-normativa.md``). El tipo del
material es el gancho que permite a la norma elegir la familia de leyes
aplicable.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Hormigon:
    """Hormigón estructural (unidades N/mm²).

    Attributes:
        fck: Resistencia característica a compresión (MPa).
        fcm: Resistencia media a compresión (MPa).
        ecm: Módulo de deformación secante (MPa).
    """

    fck: float
    fcm: float
    ecm: float


@dataclass(frozen=True, slots=True)
class AceroArmadura:
    """Acero de armadura pasiva (unidades N/mm²).

    Attributes:
        fyk: Límite elástico característico (MPa).
        es: Módulo de elasticidad (MPa).
    """

    fyk: float
    es: float


@dataclass(frozen=True, slots=True)
class AceroPretensado:
    """Acero de pretensado (unidades N/mm²).

    Attributes:
        fpk: Carga unitaria característica de rotura (MPa).
        ep: Módulo de elasticidad (MPa).
    """

    fpk: float
    ep: float


type Material = Hormigon | AceroArmadura | AceroPretensado
"""Material físico de un componente de sección."""


def modulo_elastico(material: Material) -> float:
    """Devuelve el módulo de elasticidad de un material (MPa).

    Args:
        material: Material del que se quiere el módulo de elasticidad.

    Returns:
        El módulo ``ecm`` del hormigón, ``es`` del acero de armadura o ``ep``
        del acero de pretensado (MPa).
    """
    if isinstance(material, Hormigon):
        return material.ecm
    if isinstance(material, AceroArmadura):
        return material.es
    return material.ep
