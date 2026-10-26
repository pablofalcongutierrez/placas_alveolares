"""Aceros de pretensado (cordones) del Código Estructural.

La tabla recoge los cordones de siete alambres ``S7`` con su carga unitaria
característica de rotura ``fpk`` y el módulo de elasticidad ``Ep`` habitual.
Cuando el milestone de pretensado introduzca el resto de propiedades del
cordón (límite convencional ``fp0,1k``, alargamiento, área), se ampliará el
tipo del dominio y esta tabla.

Referencia de cláusula provisional: confirmar las designaciones y su
articulado contra la versión vigente del Código Estructural.
"""

from __future__ import annotations

from dataclasses import dataclass

from placas_alveolares.domain.model.materiales import AceroPretensado
from placas_alveolares.norms.errores import CasoFueraDeAlcance

_MODULO_ELASTICIDAD_CORDON = 195_000.0
"""Módulo de elasticidad ``Ep`` habitual de los cordones (MPa)."""


@dataclass(frozen=True, slots=True)
class PropiedadesAceroPretensado:
    """Valores característicos de un cordón de pretensado.

    Attributes:
        fpk: Carga unitaria característica de rotura (MPa).
        ep: Módulo de elasticidad (MPa).
    """

    fpk: float
    ep: float


ACEROS_PRETENSADOS_CE: dict[str, PropiedadesAceroPretensado] = {
    "Y 1670 S7": PropiedadesAceroPretensado(
        fpk=1_670.0, ep=_MODULO_ELASTICIDAD_CORDON
    ),
    "Y 1770 S7": PropiedadesAceroPretensado(
        fpk=1_770.0, ep=_MODULO_ELASTICIDAD_CORDON
    ),
    "Y 1860 S7": PropiedadesAceroPretensado(
        fpk=1_860.0, ep=_MODULO_ELASTICIDAD_CORDON
    ),
    "Y 1960 S7": PropiedadesAceroPretensado(
        fpk=1_960.0, ep=_MODULO_ELASTICIDAD_CORDON
    ),
}
"""Cordones de pretensado de siete alambres."""


def tipos_acero_pretensado() -> tuple[str, ...]:
    """Nombres de los cordones disponibles.

    Returns:
        Las designaciones de la tabla, en el orden en que se declaran.
    """
    return tuple(ACEROS_PRETENSADOS_CE)


def acero_pretensado(nombre: str) -> AceroPretensado:
    """Construye el acero de pretensado de un cordón de la tabla.

    Args:
        nombre: Designación del cordón (p. ej. ``"Y 1860 S7"``).

    Returns:
        El material con ``fpk`` y ``Ep``.

    Raises:
        CasoFueraDeAlcance: Si la designación no figura en la tabla.
    """
    try:
        propiedades = ACEROS_PRETENSADOS_CE[nombre]
    except KeyError as error:
        raise CasoFueraDeAlcance(
            f"El acero de pretensado '{nombre}' no figura en la tabla del "
            "Código Estructural. Disponibles: "
            f"{', '.join(ACEROS_PRETENSADOS_CE)}."
        ) from error

    return AceroPretensado(fpk=propiedades.fpk, ep=propiedades.ep)
