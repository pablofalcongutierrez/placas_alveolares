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

from placas_alveolares.domain.errores import MaterialInvalido


def _exigir_positivo(propiedad: str, valor: float) -> None:
    """Valida que una propiedad física sea estrictamente positiva.

    Args:
        propiedad: Nombre de la propiedad, para el mensaje de error.
        valor: Valor de la propiedad.

    Raises:
        MaterialInvalido: Si ``valor`` no es estrictamente positivo.
    """
    if valor <= 0.0:
        raise MaterialInvalido(
            f"La propiedad {propiedad} del material debe ser positiva; "
            f"se recibió {valor}."
        )


@dataclass(frozen=True, slots=True)
class Hormigon:
    """Hormigón estructural (unidades N/mm²).

    Attributes:
        fck: Resistencia característica a compresión (MPa).
        fcm: Resistencia media a compresión (MPa).
        ecm: Módulo de deformación secante (MPa).

    Raises:
        MaterialInvalido: Si alguna propiedad no es estrictamente positiva.
    """

    fck: float
    fcm: float
    ecm: float

    def __post_init__(self) -> None:
        _exigir_positivo("fck", self.fck)
        _exigir_positivo("fcm", self.fcm)
        _exigir_positivo("ecm", self.ecm)


@dataclass(frozen=True, slots=True)
class AceroArmadura:
    """Acero de armadura pasiva (unidades N/mm²).

    Attributes:
        fyk: Límite elástico característico (MPa).
        es: Módulo de elasticidad (MPa).

    Raises:
        MaterialInvalido: Si alguna propiedad no es estrictamente positiva.
    """

    fyk: float
    es: float

    def __post_init__(self) -> None:
        _exigir_positivo("fyk", self.fyk)
        _exigir_positivo("es", self.es)


@dataclass(frozen=True, slots=True)
class AceroPretensado:
    """Acero de pretensado (unidades N/mm²).

    Attributes:
        fpk: Carga unitaria característica de rotura (MPa).
        ep: Módulo de elasticidad (MPa).

    Raises:
        MaterialInvalido: Si alguna propiedad no es estrictamente positiva.
    """

    fpk: float
    ep: float

    def __post_init__(self) -> None:
        _exigir_positivo("fpk", self.fpk)
        _exigir_positivo("ep", self.ep)


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
