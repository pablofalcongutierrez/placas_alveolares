"""Aceros pasivos definidos por el Código Estructural.

Los tipos y sus valores característicos proceden de la Tabla 34.2.a del
artículo 34 del Código Estructural (UNE 36065 y UNE 36068). Se adoptan los
mínimos garantizados de la tabla como valores característicos de cálculo.

El alargamiento característico ``eps_uk`` se toma del **alargamiento total bajo
carga máxima** ``εmáx`` (``A_gt``), que es la magnitud que usa la familia
eurocódigo como ``εuk``. El alargamiento de rotura ``εu,5`` de la tabla no se
usa porque se mide sobre una base de 5 diámetros y no interviene en el diagrama
de cálculo. El alcance actual considera únicamente acero suministrado en barra;
el suministro en rollo no se modela.

Las relaciones ``fs/fy`` y ``fy,real/fy,nominal`` son criterios de recepción
del producto, no datos de entrada del cálculo, por lo que no se modelan.
"""

from __future__ import annotations

from dataclasses import dataclass

from placas_alveolares.domain.model.materiales import AceroArmadura
from placas_alveolares.norms.errores import CasoFueraDeAlcance

_MODULO_ELASTICIDAD_ACERO = 200_000.0
"""Módulo de elasticidad del acero pasivo ``Es`` (MPa), CE art. 34."""


@dataclass(frozen=True, slots=True)
class PropiedadesAceroPasivo:
    """Valores característicos mínimos de un acero de la Tabla 34.2.a.

    Los valores adoptados corresponden al suministro en barra.

    Attributes:
        fyk: Límite elástico característico (MPa).
        ftk: Carga unitaria característica de rotura (MPa).
        eps_uk: Alargamiento total mínimo bajo carga máxima para suministro
            en barra (tanto por uno).
    """

    fyk: float
    ftk: float
    eps_uk: float


ACEROS_PASIVOS_CE: dict[str, PropiedadesAceroPasivo] = {
    "B 400 S": PropiedadesAceroPasivo(
        fyk=400.0,
        ftk=440.0,
        eps_uk=0.050,
    ),
    "B 500 S": PropiedadesAceroPasivo(
        fyk=500.0,
        ftk=550.0,
        eps_uk=0.050,
    ),
    "B 400 SD": PropiedadesAceroPasivo(
        fyk=400.0,
        ftk=480.0,
        eps_uk=0.075,
    ),
    "B 500 SD": PropiedadesAceroPasivo(
        fyk=500.0,
        ftk=575.0,
        eps_uk=0.075,
    ),
}
"""Tabla 34.2.a del Código Estructural, para suministro en barra."""


def tipos_acero_pasivo() -> tuple[str, ...]:
    """Nombres de los aceros pasivos disponibles en el Código Estructural.

    Returns:
        Las designaciones de la tabla, en el orden en que se declaran.
    """
    return tuple(ACEROS_PASIVOS_CE)


def acero_pasivo(nombre: str) -> AceroArmadura:
    """Construye el acero pasivo de un tipo de la Tabla 34.2.a.

    Args:
        nombre: Designación del acero (p. ej. ``"B 500 S"``).

    Returns:
        El material con ``fyk``, ``ftk``, ``Es`` y ``eps_uk`` característicos
        mínimos para suministro en barra.

    Raises:
        CasoFueraDeAlcance: Si la designación no figura en la Tabla 34.2.a.
    """
    try:
        propiedades = ACEROS_PASIVOS_CE[nombre]
    except KeyError as error:
        raise CasoFueraDeAlcance(
            f"El acero pasivo '{nombre}' no figura en la Tabla 34.2.a del "
            f"Código Estructural. Disponibles: {', '.join(ACEROS_PASIVOS_CE)}."
        ) from error

    return AceroArmadura(
        fyk=propiedades.fyk,
        ftk=propiedades.ftk,
        es=_MODULO_ELASTICIDAD_ACERO,
        eps_uk=propiedades.eps_uk,
    )
