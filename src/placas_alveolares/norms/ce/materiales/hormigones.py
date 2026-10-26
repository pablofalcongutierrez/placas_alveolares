"""Clases de hormigón estructural del Código Estructural.

La tabla recoge la resistencia característica ``fck`` de cada clase. Los
valores derivados ``fcm`` y ``Ecm`` se obtienen con las fórmulas de la Tabla
3.1 de EN 1992-1-1, que el Código Estructural adopta.

Referencia de cláusula provisional: confirmar las clases y su articulado
contra la versión vigente del Código Estructural.
"""

from __future__ import annotations

from placas_alveolares.domain.model.materiales import Hormigon
from placas_alveolares.norms.errores import CasoFueraDeAlcance
from placas_alveolares.norms.eurocode.laws import ecm_tabla_3_1, fcm_tabla_3_1

FCK_POR_CLASE_CE: dict[str, float] = {
    "HA-25": 25.0,
    "HA-30": 30.0,
    "HA-35": 35.0,
    "HA-40": 40.0,
    "HA-45": 45.0,
    "HA-50": 50.0,
    "HA-55": 55.0,
    "HA-60": 60.0,
}
"""Resistencia característica ``fck`` (MPa) de cada clase de hormigón."""


def tipos_hormigon() -> tuple[str, ...]:
    """Nombres de las clases de hormigón disponibles.

    Returns:
        Las designaciones de la tabla, en el orden en que se declaran.
    """
    return tuple(FCK_POR_CLASE_CE)


def hormigon(nombre: str) -> Hormigon:
    """Construye el hormigón de una clase del Código Estructural.

    Args:
        nombre: Designación de la clase (p. ej. ``"HA-30"``).

    Returns:
        El material con ``fck``, ``fcm = fck + 8`` y ``Ecm`` de la Tabla 3.1.

    Raises:
        CasoFueraDeAlcance: Si la clase no figura en la tabla.
    """
    try:
        fck = FCK_POR_CLASE_CE[nombre]
    except KeyError as error:
        raise CasoFueraDeAlcance(
            f"La clase de hormigón '{nombre}' no figura en la tabla del "
            f"Código Estructural. Disponibles: {', '.join(FCK_POR_CLASE_CE)}."
        ) from error

    fcm = fcm_tabla_3_1(fck)
    return Hormigon(fck=fck, fcm=fcm, ecm=ecm_tabla_3_1(fcm))
